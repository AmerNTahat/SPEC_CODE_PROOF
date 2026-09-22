"""Known-answer arithmetic and real service provenance boundary tests."""
import tempfile
import json
import unittest
from pathlib import Path
from inspecta_scp.config import PolicyError,digest
from inspecta_scp.controller import Controller
from inspecta_scp.metrics import Metrics,calculate


class MetricsTests(unittest.TestCase):
    def test_formal_evidence_requires_bound_objects_not_pass_labels(self):
        # Synthetic evidence tests the rejection boundary, not a formal adapter.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir()
            (source/'Model.sysml').write_text('package Test {}')
            c=Controller(root/'state')
            try:
                run=c.create({'project':str(source),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only'})
                metrics=Metrics(c);unit={'id':'u','formal_element_ids':['g']}
                manifest=json.loads((c.store.root/'runs'/run['id']/'input-workspace-manifest.json').read_text())
                binding={'run_id':run['id'],'config_sha256':run['config_hash'],'input_manifest_sha256':digest(manifest)}
                obligation={**binding,'element_id':'g','unit_id':'u','gate':'configured_formal_verification','status':'PASS'}
                def gate(record, outer=None):
                    return {'status':'PASS','evidence':c.store.object({**(binding if outer is None else outer),'unit_checks':{'u':[record]}})}
                valid={'element_id':'g','status':'PASS','evidence_ref':c.store.object(obligation)}
                self.assertTrue(metrics._formal_unit_verified(run,gate(valid),unit))
                for record in [{**valid,'evidence_ref':'looks-valid'},
                               {**valid,'evidence_ref':{'sha256':'0'*64}},
                               {**valid,'evidence_ref':c.store.object({**obligation,'config_sha256':'stale'})},
                               {**valid,'evidence_ref':c.store.object({**obligation,'element_id':'other'})}]:
                    self.assertFalse(metrics._formal_unit_verified(run,gate(record),unit))
                self.assertFalse(metrics._formal_unit_verified(run,gate(valid,{**binding,'run_id':'other'}),unit))
                path=c.store.root/valid['evidence_ref']['path'];path.write_text('{}')
                self.assertFalse(metrics._formal_unit_verified(run,gate(valid),unit))
            finally:c.close()

    def test_known_answer(self):
        result=calculate(['a','b','c'],['a','b'],['a'],120,1000,2)
        self.assertEqual(result['coverage'],2/3);self.assertEqual(result['verified_per_minute'],1)
        self.assertEqual(result['tokens_per_verified_unit'],500);self.assertEqual(result['dollars_per_verified_unit'],1)

    def test_zero_verified_and_unknown_denominator(self):
        result=calculate(['a'],[],[],60,100,None)
        self.assertEqual(result['coverage'],0);self.assertIsNone(result['tokens_per_verified_unit'])
        self.assertIsNone(result['dollars_per_verified_unit'])
        self.assertIsNone(calculate(None,[],[],None,None,None)['coverage'])

    def test_duplicate_unregistered_and_nonfinite_rejected(self):
        for args in [(['a','a'],[],[],60,0,None),(['a'],['b'],[],60,0,None),(['a'],[],['a'],60,0,None),(['a'],[],[],float('nan'),0,None)]:
            with self.assertRaises(PolicyError):calculate(*args)

    def test_unregistered_real_run_does_not_invent_units_or_cost(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir();(source/'Model.sysml').write_text('package Test {}')
            c=Controller(root/'state')
            try:
                run=c.create({'project':str(source),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only'})
                report=Metrics(c).report(run['id'])
                self.assertIsNone(report['registered_count']);self.assertEqual(report['verified_count'],0)
                self.assertIsNone(report['cost_usd']);self.assertEqual(report['total_tokens'],0)
                c.store.db.execute('UPDATE runs SET usage_unknown=1 WHERE id=?',(run['id'],))
                self.assertIsNone(Metrics(c).report(run['id'])['total_tokens'])
                exported=Metrics(c).export(run['id'],root/'report',plots=False)
                self.assertEqual(exported['report']['registered_count'],None)
                with self.assertRaises(PolicyError):Metrics(c).export(run['id'],root/'report',plots=False)
            finally:c.close()


if __name__=='__main__':unittest.main()
