"""Synthetic policy tests; these are not Isolette verification evidence."""
import json,tempfile,unittest
from pathlib import Path
from inspecta_scp.controller import Controller
from inspecta_scp.golden_defects import GoldenDefects
from inspecta_scp.storage import sha_file
from inspecta_scp.config import PolicyError

class GoldenDefectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.c=Controller(self.root/'state');self.service=GoldenDefects(self.c)
        self.source=self.root/'app.rs';self.source.write_text('synthetic proof source')
        self.model=self.root/'model.json';self.model.write_text(json.dumps({'run':{'id':'model','result':{'gates':[{'gate':g,'status':'PASS'} for g in ['parse_type','hamr_codegen']]}}}))
        self.proof=self.root/'proof.json';self.proof.write_text(json.dumps({'workspace':str(self.root),'source_run_id':'model','source_rs_sha256':{'app.rs':sha_file(self.source)},'source_rs_preserved':True,'checks':[{'crate':'heat','kind':'verus','exit_code':0,'stdout':'verification results:: 10 verified, 0 errors'},{'crate':'heat','kind':'gumbo_tests','exit_code':0,'stdout':'test result: ok. 5 passed; 0 failed'}]}))
        self.diagnosis=self.root/'diagnosis.json';self.diagnosis.write_text(json.dumps({'checks':[{'name':name,'exit_code':0,'stdout':out} for name,out in [('overlap_within_desired_range','sat'),('same_witness_both_guarantees','unsat')]]}))
        self.args=dict(title='Synthetic golden defect',target='synthetic heat',requirement_ids=['R1','R2'],comment='Contradictory guards, ordered premise approved',consent='Human approves scoped repair',citations=['Synthetic English and golden clauses'],artifacts=[str(self.source)],model_report=str(self.model),verification_report=str(self.proof),contradiction_report=str(self.diagnosis),component='heat',open_obligations=['Producer must establish ordering'])
    def tearDown(self):self.c.close();self.tmp.cleanup()
    def test_human_repair_count_is_scoped_and_stale_evidence_revokes_it(self):
        record=self.service.register(**self.args);r=self.service.inspect(record)
        self.assertEqual(r['status'],'REPAIRED_GOLDEN_DEFECT_ACCEPTED_BY_HUMAN')
        self.assertFalse(r['whole_system_acceptance']);self.assertFalse(r['unchanged_golden_pass']);self.assertFalse(r['rule_transfer_accepted'])
        self.assertEqual(r['open_obligations'],['Producer must establish ordering'])
        self.service.register(**self.args)
        self.assertEqual(self.service.catalog()['accepted_repair_cases'],1)
        self.source.write_text('modified after proof')
        self.assertFalse(self.service.inspect(record)['counts_as_accepted_repair_case'])
    def test_consent_and_contradiction_are_required(self):
        with self.assertRaises(PolicyError):self.service.register(**{**self.args,'consent':''})
        self.diagnosis.write_text(json.dumps({'checks':[]}))
        r=self.service.inspect(self.service.register(**self.args))
        self.assertFalse(r['counts_as_accepted_repair_case'])
    def test_external_premise_is_retained_without_claiming_internal_proof(self):
        assumption={'id':'EA-1','boundary':'System inputs','predicate':'lower < upper',
            'source_citation':'Reviewed guidebook','human_consent':'Approved external premise',
            'allocation':'Component requires receives this premise','mapping_status':'DECLARED_NOT_PROVED'}
        record=self.service.register(**self.args,environmental_assumptions=[assumption])
        review=self.service.inspect(record)
        self.assertTrue(review['counts_as_accepted_repair_case'])
        self.assertEqual(review['environmental_assumptions'],[assumption])
        self.assertFalse(review['whole_system_acceptance'])
        with self.assertRaisesRegex(PolicyError,'propagation proof'):
            self.service.register(**self.args,environmental_assumptions=[{**assumption,'mapping_status':'PROVED'}])
        with self.assertRaises(PolicyError):
            self.service.register(**self.args,environmental_assumptions=[{**assumption,'human_consent':''}])

    def test_dependency_proof_cannot_substitute_for_component_proof(self):
        proof=json.loads(self.proof.read_text())
        proof['checks'][0]['stdout']='verification results:: 1190 verified, 0 errors\nverification results:: 0 verified, 0 errors'
        self.proof.write_text(json.dumps(proof))
        self.assertFalse(self.service.inspect(self.service.register(**self.args))['counts_as_accepted_repair_case'])

    def test_wrong_model_or_failed_proof_cannot_be_accepted(self):
        proof=json.loads(self.proof.read_text());proof['source_run_id']='different';proof['checks'][0]['exit_code']=1
        self.proof.write_text(json.dumps(proof))
        r=self.service.inspect(self.service.register(**self.args))
        self.assertFalse(r['counts_as_accepted_repair_case'])
        self.assertIn('Proof belongs to another model',r['blockers'])
        self.assertTrue(any('verus' in b for b in r['blockers']))

if __name__=='__main__':unittest.main()
