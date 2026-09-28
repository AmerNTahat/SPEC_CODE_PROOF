"""Synthetic scope policy checks; not tool capability or requirement evidence."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.capability_scope import CapabilityScope
from inspecta_scp.approvals import Approvals
from inspecta_scp.config import digest,PolicyError

class CapabilityScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.c=Controller(Path(self.tmp.name)/'state');self.s=CapabilityScope(self.c)
        self.prep=self.c.store.record('prepared_requirements',{'english':'R1: retain a missing capability. R2: repair an incorrect implementation.','english_sha256':digest('source')})
        self.identity={'home':'synthetic','files':{'bin/sireum':'synthetic'},'identity_digest':'one'}
        self.mock=patch.object(self.s,'tool',return_value=self.identity);self.mock.start()
    def tearDown(self):self.mock.stop();self.c.close();self.tmp.cleanup()
    def item(self,key,status):return {'requirement_id':key,'source_excerpt':'R1: retain a missing capability.' if key=='R1' else 'R2: repair an incorrect implementation.', 'status':status,'reason':'Synthetic capability review','evidence_run_ids':['synthetic-run'],'alternative_encoding_review':'Synthetic alternative review; not real evidence','revisit_condition':'After changing the tool version'}
    def test_only_reviewed_unsupported_is_deferred_never_passed(self):
        r=self.s.propose(self.prep['id'],'synthetic-run',[self.item('R1','NOT_SUPPORTED_TOOL_VERSION'),self.item('R2','IMPLEMENTATION_FAILURE')])
        pending=self.s.inspect(r['id']);self.assertEqual(pending['mandatory_targets'],2)
        a=r['approval'];Approvals(self.c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic reviewer')
        result=self.s.inspect(r['id']);self.assertEqual(result['mandatory_targets'],1);self.assertEqual(result['deferred_targets'],1);self.assertEqual(result['total_targets'],2)
        self.assertEqual(result['verified_targets'],0);self.assertFalse(result['whole_system_acceptance']);self.assertEqual(result['targets'][1]['result'],'NOT_VERIFIED')
        config={'sireum':'synthetic/bin/sireum','sireum_sha256':'synthetic'}
        self.assertEqual(self.s.bind(r['id'],self.prep['id'],config)['id'],r['id'])
        with self.assertRaisesRegex(PolicyError,'different English'):self.s.bind(r['id'],'other',config)
        with self.assertRaisesRegex(PolicyError,'different selected tool'):
            self.s.bind(r['id'],self.prep['id'],{**config,'sireum':'upgraded/bin/sireum'})
        self.assertEqual(self.c.store.read_record('prepared_requirements',self.prep['id'])['english'],self.prep['english'])
    def test_version_change_invalidates_exclusion(self):
        r=self.s.propose(self.prep['id'],'synthetic-run',[self.item('R1','NOT_SUPPORTED_TOOL_VERSION')]);a=r['approval'];Approvals(self.c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic reviewer')
        with patch.object(self.s,'tool',return_value={**self.identity,'identity_digest':'new-version'}):
            result=self.s.inspect(r['id']);self.assertFalse(result['effective']);self.assertEqual(result['deferred_targets'],0);self.assertEqual(result['mandatory_targets'],1)
    def test_missing_or_mismatched_evidence_and_source_rejected(self):
        item=self.item('R1','NOT_SUPPORTED_TOOL_VERSION')
        for bad in [{**item,'source_excerpt':'invented English'},{**item,'evidence_run_ids':[]},{**item,'alternative_encoding_review':''},{**item,'status':'PASS'}]:
            with self.assertRaises(PolicyError):self.s.propose(self.prep['id'],'synthetic-run',[bad])
        with patch.object(self.s,'tool',side_effect=[self.identity,{**self.identity,'identity_digest':'different'}]):
            with self.assertRaisesRegex(PolicyError,'different tool'):self.s.propose(self.prep['id'],'synthetic-run',[item])

    def test_reference_omission_is_a_separate_reviewed_exclusion(self):
        r=self.s.propose(self.prep['id'],'synthetic-run',[self.item('R1','OUT_OF_SCOPE_REFERENCE'),self.item('R2','IMPLEMENTATION_FAILURE')])
        pending=self.s.inspect(r['id']);self.assertEqual(pending['qualification_denominator'],2)
        a=r['approval'];Approvals(self.c.store).decide(a['id'],a['subject_digest'],'APPROVED','Synthetic reviewer')
        result=self.s.inspect(r['id'])
        self.assertEqual(result['qualification_denominator'],1)
        self.assertEqual(result['reference_excluded_targets'],1)
        self.assertEqual(result['deferred_targets'],0)
        self.assertEqual(result['targets'][0]['result'],'EXCLUDED_REFERENCE_SCOPE')
        self.assertEqual(result['total_targets'],2)
        self.assertFalse(result['excluded_targets_are_failures'])
        self.assertFalse(result['whole_system_acceptance'])
        self.assertEqual(result['verified_targets'],0)
