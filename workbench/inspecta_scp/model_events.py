"""Conservative Codex JSONL accounting for a structured, proposal-only call.

This parser is not a sandbox or a hard token cap. Tool execution must be disabled
and isolated before launching a worker; forbidden events require termination.
"""
import json
import re
from .config import PolicyError


class ModelEvents:
    def __init__(self):
        self.usage = {'input_tokens': 0, 'output_tokens': 0, 'cached_input_tokens': 0}
        self.started = 0
        self.completed = 0
        self.active = False
        self.final_text = None
        self.failure = None
        self.events = 0
        self.warnings = []
        self.thread_seen = False

    def feed(self, line):
        if self.failure:
            raise PolicyError('Model stream already rejected')
        try:
            if not isinstance(line, str) or len(line.encode()) > 1024 * 1024 or self.events >= 10000:
                raise PolicyError('Model event stream limit exceeded')
            event = json.loads(line)
            if not isinstance(event, dict):raise PolicyError('Expected a model event object')
            self.events += 1
            kind = event.get('type')
            if kind == 'thread.started':
                if self.thread_seen or self.started:raise PolicyError('Unexpected thread restart')
                self.thread_seen = True
            elif kind == 'turn.started':
                if self.active:raise PolicyError('Overlapping model turns')
                self.started += 1; self.active = True
            elif kind == 'turn.completed':
                if not self.active:raise PolicyError('Completion has no active turn')
                usage = event.get('usage', {})
                for field in self.usage:
                    if type(usage.get(field)) is not int or usage[field] < 0:
                        raise PolicyError('Missing or invalid model usage')
                if usage['cached_input_tokens'] > usage['input_tokens']:
                    raise PolicyError('Cached input exceeds total input')
                for field in self.usage:self.usage[field] += usage[field]
                self.completed += 1; self.active = False
            elif kind in {'item.started', 'item.updated', 'item.completed'}:
                item = event.get('item', {})
                # Codex emits nonfatal startup warnings as error items before turn.started.
                if item.get('type') == 'error' and kind == 'item.completed':
                    if not isinstance(item.get('message'), str):raise PolicyError('Invalid warning item')
                    self.warnings.append(item['message'])
                    return
                if not self.active:raise PolicyError('Model item has no active turn')
                if item.get('type') not in {'agent_message', 'reasoning'}:
                    raise PolicyError('Proposal-only worker attempted a tool or unsupported event')
                if kind == 'item.completed' and item['type'] == 'agent_message':
                    if not isinstance(item.get('text'), str):raise PolicyError('Missing final message text')
                    self.final_text = item['text']
            elif kind in {'turn.failed', 'error'}:
                message=event.get('message') or event.get('error',{}).get('message') or 'Unspecified provider error'
                message=re.sub(r'(?:sk-[A-Za-z0-9_-]+|Bearer\s+\S+|eyJ[A-Za-z0-9_.-]{30,})','[REDACTED]',str(message))[:8000]
                raise PolicyError('Model turn reported failure; usage may be incomplete: '+message)
            else:
                raise PolicyError('Unknown model event type')
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            self.failure = str(exc)
            raise PolicyError(self.failure) from exc

    def result(self, exit_code):
        complete = (exit_code == 0 and not self.failure and not self.active
                    and self.completed > 0 and self.started == self.completed)
        value = None
        if complete:
            try:
                value = json.loads(self.final_text)
                if not isinstance(value, dict):raise ValueError('Expected structured object')
            except (ValueError, TypeError):
                complete = False
        return {'usage': dict(self.usage), 'usage_complete': not self.failure and not self.active
                and self.completed > 0 and self.started == self.completed,
                'status': 'RESPONSE_RECEIVED' if complete else 'BLOCKED',
                'response': value if complete else None, 'warnings': self.warnings,
                'reason': self.failure or (None if complete else 'Incomplete or invalid structured response'),
                'scope': 'Metered response only; no truth, validation or acceptance claim'}
