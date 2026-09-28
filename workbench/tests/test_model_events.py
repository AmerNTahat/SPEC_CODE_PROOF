"""Synthetic transport fixtures; not a paid model capability demonstration."""
import json
import unittest
from inspecta_scp.config import PolicyError
from inspecta_scp.model_events import ModelEvents


class ModelEventTests(unittest.TestCase):
    def feed(self, parser, value):parser.feed(json.dumps(value))

    def test_usage_counts_cached_input_once(self):
        p=ModelEvents();self.feed(p,{'type':'thread.started','thread_id':'fixture'})
        self.feed(p,{'type':'turn.started'})
        self.feed(p,{'type':'item.completed','item':{'type':'agent_message','text':'{"rules":[]}'}})
        self.feed(p,{'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':80,'output_tokens':10}})
        r=p.result(0);self.assertTrue(r['usage_complete']);self.assertEqual(r['status'],'RESPONSE_RECEIVED')
        self.assertEqual(r['usage']['input_tokens']+r['usage']['output_tokens'],110)

    def test_unreported_failure_retains_known_prior_usage(self):
        p=ModelEvents();self.feed(p,{'type':'turn.started'})
        self.feed(p,{'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':0,'output_tokens':10}})
        self.feed(p,{'type':'turn.started'})
        with self.assertRaises(PolicyError):self.feed(p,{'type':'turn.failed'})
        r=p.result(1);self.assertFalse(r['usage_complete']);self.assertEqual(r['usage']['input_tokens'],100)

    def test_tools_and_bad_events_rejected(self):
        for kind in ['command_execution','file_change','mcp_tool_call','web_search']:
            p=ModelEvents();self.feed(p,{'type':'turn.started'})
            with self.assertRaises(PolicyError):self.feed(p,{'type':'item.started','item':{'type':kind}})
            self.assertIsNone(p.result(0)['response'])
        p=ModelEvents()
        with self.assertRaises(PolicyError):p.feed('not-json')

    def test_missing_usage_and_truncation_are_unknown(self):
        p=ModelEvents();self.feed(p,{'type':'turn.started'})
        self.assertFalse(p.result(1)['usage_complete'])
        with self.assertRaises(PolicyError):self.feed(p,{'type':'turn.completed','usage':{'input_tokens':0}})

    def test_pre_turn_warning_is_not_a_model_turn(self):
        p=ModelEvents();self.feed(p,{'type':'thread.started','thread_id':'fixture'})
        self.feed(p,{'type':'item.completed','item':{'type':'error','message':'Synthetic startup warning'}})
        self.assertEqual(p.started,0)
        self.assertFalse(p.result(0)['usage_complete'])
        self.feed(p,{'type':'turn.started'})
        self.feed(p,{'type':'item.completed','item':{'type':'agent_message','text':'{"rules":[]}'}})
        self.feed(p,{'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':0,'output_tokens':10}})
        self.assertEqual(p.result(0)['status'],'RESPONSE_RECEIVED')
        self.assertEqual(len(p.result(0)['warnings']),1)
