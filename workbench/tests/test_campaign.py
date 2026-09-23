import tempfile
import unittest
from inspecta_scp.campaign import Campaign
from inspecta_scp.config import PolicyError
from inspecta_scp.storage import Store


class CampaignTests(unittest.TestCase):
    def test_aggregate_restart_unknown_and_no_reset(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(100,60,'TEST ONLY explicit best-effort consent')
            self.assertIsNone(grant['deadline'])
            call=campaign.reserve(grant['id'],80)
            with self.assertRaises(PolicyError):campaign.reserve(grant['id'],1)
            state=campaign.settle(call,{'input_tokens':50,'cached_input_tokens':40,'output_tokens':10},True)
            self.assertEqual(state['remaining_tokens'],40)
            deadline=state['deadline'];store.close()
            store=Store(path);campaign=Campaign(store)
            self.assertEqual(campaign.authorize(100,60,'TEST ONLY explicit best-effort consent')['deadline'],deadline)
            with self.assertRaises(PolicyError):campaign.reserve(grant['id'],41)
            call=campaign.reserve(grant['id'],40)
            state=campaign.settle(call,{'input_tokens':5,'cached_input_tokens':0,'output_tokens':0},False)
            self.assertEqual(state['used_tokens'],65);self.assertIsNone(state['remaining_tokens'])
            with self.assertRaises(PolicyError):campaign.reserve(grant['id'],1)
            store.close()

    def test_estimated_reconciliation_preserves_measured_usage_and_clock(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(200,60,'TEST ONLY best effort')
            call=campaign.reserve(grant['id'],50)
            state=campaign.settle(call,{'input_tokens':5,'cached_input_tokens':0,'output_tokens':2},False)
            deadline=state['deadline']
            state=campaign.reconcile_estimate(call,100,'TEST ONLY explicitly approved estimate')
            self.assertEqual(state['used_tokens'],7);self.assertEqual(state['estimated_debit_tokens'],100)
            self.assertEqual(state['remaining_tokens'],93);self.assertEqual(state['deadline'],deadline)
            with self.assertRaises(PolicyError):campaign.reconcile_estimate(call,100,'repeat')
            call=campaign.reserve(grant['id'],90)
            state=campaign.settle(call,{'input_tokens':10,'cached_input_tokens':0,'output_tokens':3},True)
            self.assertEqual(state['remaining_tokens'],80)
            with self.assertRaises(PolicyError):campaign.reconcile_estimate(call,100,'replace measured')
            store.close()

    def test_explicit_time_extension_preserves_usage_and_rejects_replay(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(200,60,'TEST ONLY best effort')
            call=campaign.reserve(grant['id'],50)
            pending=campaign.status(grant['id'])
            with self.assertRaises(PolicyError):campaign.extend_time(grant['id'],60,pending['deadline'],'TEST consent')
            state=campaign.settle(call,{'input_tokens':5,'cached_input_tokens':0,'output_tokens':2},False)
            state=campaign.reconcile_estimate(call,100,'TEST estimated debit')
            extended=campaign.extend_time(grant['id'],3600,state['deadline'],'TEST explicit 60-minute extension')
            self.assertEqual(extended['started'],state['started'])
            self.assertEqual(extended['deadline'],state['deadline']+3600)
            self.assertEqual(extended['used_tokens'],7)
            self.assertEqual(extended['estimated_debit_tokens'],100)
            self.assertEqual(extended['remaining_tokens'],93)
            self.assertEqual(extended['authorization'],state['authorization'])
            with self.assertRaises(PolicyError):campaign.extend_time(grant['id'],3600,state['deadline'],'replayed consent')
            store.close()
