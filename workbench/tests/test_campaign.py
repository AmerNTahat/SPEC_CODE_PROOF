import tempfile
import unittest
from inspecta_scp.campaign import Campaign
from inspecta_scp.config import PolicyError
from inspecta_scp.storage import Store


class CampaignTests(unittest.TestCase):
    def test_explicit_resume_grants_new_window_without_resetting_usage(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            with patch('inspecta_scp.campaign.time.time',return_value=1000):
                grant=campaign.authorize(1000,60,'TEST ONLY')
                call=campaign.reserve(grant['id'],20)
                old=campaign.settle(call,{'input_tokens':10,'cached_input_tokens':0,'output_tokens':5},True)
            with patch('inspecta_scp.campaign.time.time',return_value=1200):
                new=campaign.extend_time(grant['id'],1800,old['deadline'],'Explicit user authorization of30 more minutes',resume_after_expiry=True)
            self.assertEqual(new['deadline'],3000)
            self.assertEqual(new['remaining_seconds'],1800)
            self.assertEqual(new['authorized_wall_seconds'],1860)
            self.assertEqual(new['used_tokens'],15)
            self.assertEqual(new['started'],old['started'])
            with self.assertRaises(PolicyError):campaign.extend_time(grant['id'],1800,old['deadline'],'Replay',True)
            store.close()

    def test_continuation_allowance_preserves_aggregate_and_charges_usage(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(1000,60,'TEST ONLY')
            store.record('campaign_continuation_allowance',{'campaign_id':grant['id'],
                'baseline_charged_tokens':0,'additional_charged_tokens':100})
            call=campaign.reserve(grant['id'],80)
            state=campaign.settle(call,{'input_tokens':60,'cached_input_tokens':0,'output_tokens':20},True)
            self.assertEqual(state['token_ceiling'],1000)
            self.assertEqual(state['remaining_tokens'],920)
            self.assertEqual(state['continuation_remaining_tokens'],20)
            with self.assertRaises(PolicyError):campaign.reserve(grant['id'],21)
            store.close()

    def test_continuation_extension_retains_aggregate_and_all_debits(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(1000,60,'TEST ONLY')
            store.record('campaign_continuation_allowance',{'campaign_id':grant['id'],'baseline_charged_tokens':0,'additional_charged_tokens':100})
            call=campaign.reserve(grant['id'],80)
            with self.assertRaises(PolicyError):campaign.extend_continuation(grant['id'],50,20,'Active call')
            state=campaign.settle(call,{'input_tokens':60,'cached_input_tokens':0,'output_tokens':20},True)
            extended=campaign.extend_continuation(grant['id'],50,20,'Explicit additional50 within cap')
            self.assertEqual(extended['continuation_remaining_tokens'],70)
            self.assertEqual(extended['token_ceiling'],1000)
            self.assertEqual(extended['used_tokens'],80)
            self.assertEqual(extended['deadline'],state['deadline'])
            with self.assertRaises(PolicyError):campaign.extend_continuation(grant['id'],50,20,'Replay')
            with self.assertRaises(PolicyError):campaign.reserve(grant['id'],71)
            store.close()

    def test_token_extension_preserves_deadline_debits_and_rejects_replay(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(200,60,'TEST ONLY best effort')
            call=campaign.reserve(grant['id'],50)
            state=campaign.settle(call,{'input_tokens':5,'cached_input_tokens':0,'output_tokens':2},True)
            result=campaign.extend_tokens(grant['id'],100,200,'TEST additional allowance')
            self.assertEqual(result['token_ceiling'],300)
            self.assertEqual(result['remaining_tokens'],293)
            self.assertEqual(result['deadline'],state['deadline'])
            self.assertEqual(result['authorization']['aggregate_tokens'],200)
            with self.assertRaises(PolicyError):campaign.extend_tokens(grant['id'],100,200,'replayed consent')
            store.close()

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

    def test_pause_and_resume_never_restore_time_or_tokens(self):
        with tempfile.TemporaryDirectory() as path:
            store=Store(path);campaign=Campaign(store)
            grant=campaign.authorize(200,60,'TEST ONLY best effort')
            call=campaign.reserve(grant['id'],50)
            paused=campaign.control(grant['id'],'pause')
            self.assertEqual(paused['control_state'],'PAUSED')
            with self.assertRaises(PolicyError):campaign.reserve(grant['id'],1)
            with self.assertRaises(PolicyError):campaign.control(grant['id'],'resume')
            campaign.settle(call,{'input_tokens':5,'cached_input_tokens':0,'output_tokens':2},True)
            resumed=campaign.control(grant['id'],'resume')
            self.assertEqual(resumed['deadline'],paused['deadline'])
            self.assertEqual(resumed['used_tokens'],7)
            self.assertEqual(resumed['remaining_tokens'],193)
            self.assertEqual(resumed['control_state'],'ACTIVE')
            store.close()
