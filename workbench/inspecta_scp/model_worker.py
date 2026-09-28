"""Trusted proposal transport; never executes proposals as engineering checks."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import time

from .campaign import Campaign
from .config import PolicyError, digest
from .model_events import ModelEvents
from .storage import sha_file

CODEX_SHA = '0753dfe1d8b87a52436deb13eb1c549661ef4c84fee2c5aa688385eebeccb761'
BWRAP_SHA = '77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c'
DISABLED = ('shell_tool unified_exec apps browser_use browser_use_external browser_use_full_cdp_access '
            'computer_use code_mode code_mode_host plugins hooks multi_agent multi_agent_v2 '
            'skill_search skill_mcp_dependency_install workspace_dependencies view_image image_generation '
            'in_app_browser in_app_local_automation goals sleep_tool memories shell_snapshot '
            'unbounded_connection_retries').split()


def command(repo, work, credential_file=None):
    repo=Path(repo).resolve();work=Path(work).resolve()
    binary=repo/'codex-155';bwrap=repo/'tools/codex-runtime-v0.155.1/codex-resources/bwrap'
    if sha_file(binary)!=CODEX_SHA or sha_file(bwrap)!=BWRAP_SHA:
        raise PolicyError('Selected Codex/runtime identity changed')
    cmd=[str(bwrap),'--unshare-all','--share-net','--die-with-parent','--new-session']
    for directory in ['/usr','/bin','/lib','/lib64']:
        if Path(directory).exists():cmd+=['--ro-bind',directory,directory]
    cmd+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/etc','--dir','/home',
          '--dir','/home/worker','--dir','/home/worker/.codex','--dir','/runtime',
          '--ro-bind',str(binary),'/runtime/codex','--dir','/runtime/codex-resources',
          '--ro-bind',str(bwrap),'/runtime/codex-resources/bwrap','--ro-bind',str(work),'/work','--chdir','/work']
    for path in ['/etc/ssl','/etc/resolv.conf','/etc/hosts','/etc/nsswitch.conf']:
        if Path(path).exists():cmd+=['--ro-bind',path,path]
    if credential_file is not None:
        credential_file=Path(credential_file)
        if not credential_file.is_file() or credential_file.is_symlink():raise PolicyError('Selected saved CLI credentials are unavailable')
        cmd+=['--ro-bind',str(credential_file.resolve()),'/home/worker/.codex/auth.json']
    cmd+=['--clearenv','--setenv','PATH','/usr/bin:/bin','--setenv','HOME','/home/worker',
          '--setenv','CODEX_HOME','/home/worker/.codex','--setenv','LANG','C.UTF-8','--',
          '/runtime/codex','--strict-config','-a','never']
    for feature in DISABLED:cmd+=['--disable',feature]
    # Defense in depth: even accidentally surfaced filesystem tools cannot read authentication.
    for setting in ['web_search="disabled"','check_for_update_on_startup=false','tools.update_plan.enabled=false',
                    'default_permissions="proposal"',
                    'permissions.proposal.filesystem={"/"="read","/home/worker/.codex"="deny"}',
                    'permissions.proposal.network.enabled=false','agents.enabled=false']:
        cmd+=['-c',setting]
    return cmd


class ModelWorker:
    def __init__(self,store,repo):self.store=store;self.repo=Path(repo).resolve();self.campaign=Campaign(store)

    def propose(self,campaign_id,prompt,schema,credential_file,seconds=180,reservation=100000):
        if not isinstance(prompt,str) or len(prompt.encode())>256000:raise PolicyError('Bounded text prompt required')
        if type(seconds) is not int or not 1 <= seconds <= 600:raise PolicyError('Call deadline must be 1–600 seconds')
        if type(reservation) is not int or reservation<100000:raise PolicyError('Reserve at least 100,000 tokens per bounded call')
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)
        with tempfile.TemporaryDirectory(prefix='scp-model-') as temp:
            path=Path(temp);(path/'schema.json').write_text(json.dumps(schema))
            cmd=command(self.repo,path,credential_file)+['exec','--ignore-user-config','--ignore-rules',
                '--ephemeral','--skip-git-repo-check','--json','--color','never','-m','gpt-6-astra',
                '--output-schema','/work/schema.json','-']
            call=self.campaign.reserve(campaign_id,reservation)
            deadline=min(time.time()+seconds,self.campaign.status(campaign_id)['deadline'])
            parser=ModelEvents();events=[];reason=None;exit_code=None;process=None
            # Separate stderr is bounded and never published: it can contain account identifiers.
            stderr=bytearray();pending=bytearray();total=0;selector=None
            try:
                process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                         start_new_session=True,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
                selector=selectors.DefaultSelector()
                payload=prompt.encode();written=0
                os.set_blocking(process.stdin.fileno(),False)
                selector.register(process.stdin,selectors.EVENT_WRITE,'stdin')
                selector.register(process.stdout,selectors.EVENT_READ,'stdout');selector.register(process.stderr,selectors.EVENT_READ,'stderr')
                while selector.get_map():
                    if self.campaign.control_state(campaign_id)=='PAUSED':raise PolicyError('Campaign paused by user')
                    if time.time()>=deadline:raise PolicyError('Model call deadline reached')
                    for key,_ in selector.select(min(0.2,max(0,deadline-time.time()))):
                        if key.data=='stdin':
                            if written<len(payload):
                                try:written+=os.write(process.stdin.fileno(),payload[written:written+65536])
                                except BlockingIOError:continue
                            if written==len(payload):selector.unregister(process.stdin);process.stdin.close()
                            continue
                        data=os.read(key.fileobj.fileno(),65536)
                        if not data:selector.unregister(key.fileobj);continue
                        total+=len(data)
                        if total>4*1024*1024:raise PolicyError('Model stream output limit exceeded')
                        if key.data=='stderr':stderr.extend(data);continue
                        pending.extend(data)
                        while b'\n' in pending:
                            line,_,rest=pending.partition(b'\n');pending=bytearray(rest)
                            if line.strip():
                                event=json.loads(line)
                                # Retain protocol metadata on rejection without publishing tool arguments.
                                try:parser.feed(line.decode('utf-8'))
                                except PolicyError:
                                    events.append({'type':event.get('type'),'rejected':True,'item_type':event.get('item',{}).get('type')})
                                    raise
                                events.append(event)
                selector.close();exit_code=process.wait(timeout=max(0.01,deadline-time.time()))
                if pending.strip():parser.feed(pending.decode());events.append(json.loads(pending))
            except BaseException as exc:
                reason=type(exc).__name__+': '+str(exc)
                parser.failure=reason
            finally:
                if selector is not None:selector.close()
                if process is not None:
                    if process.poll() is None:
                        os.killpg(process.pid,signal.SIGKILL);process.wait()
                    exit_code=process.returncode
                    for stream in [process.stdin,process.stdout,process.stderr]:
                        if not stream.closed:stream.close()
            result=parser.result(exit_code)
            # A launch failure with no process cannot consume provider tokens.
            if process is None:result['usage_complete']=True
            state=self.campaign.settle(call,result['usage'],result['usage_complete'])
            if not result['usage_complete'] and state.get('failure_policy'):
                policy=state['failure_policy']
                state=self.campaign.reconcile_estimate(call,policy['debit_per_failure'],policy['consent'])
            if result['response'] is not None:
                errors=list(Draft202012Validator(schema).iter_errors(result['response']))
                if errors:result.update(status='BLOCKED',response=None,reason='Response failed output schema validation')
            return self.store.record('model_call',{'call_id':call,'campaign_id':campaign_id,'model':'gpt-6-astra',
                'codex_sha256':CODEX_SHA,'sandbox_sha256':BWRAP_SHA,'prompt_sha256':digest(prompt),
                'schema_sha256':digest(schema),'exit_code':exit_code,'events':events,'result':result,
                'stderr_bytes':len(stderr),'stderr_sha256':__import__('hashlib').sha256(stderr).hexdigest(),
                'campaign_used_tokens':state['used_tokens'],'campaign_usage_unknown':bool(state['usage_unknown']),
                'isolation':'allowlisted mounts; selected inputs via stdin; no evaluator mount; tool network disabled; credential path denied to tools'})
