"""Synthetic boundary checks; these are not real engineering proof results."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from inspecta_scp.controller import Controller
from inspecta_scp.config import digest
from inspecta_scp.metrics import Metrics

class TypedUnitTests(unittest.TestCase):
    def test_structural_conformance_rejects_changed_missing_and_stale_elements(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);project=root/'source';project.mkdir();(project/'Model.sysml').write_text('package Test {}')
            c=Controller(root/'state')
            try:
                run=c.create({'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only'})
                manifest=json.loads((c.store.root/'runs'/run['id']/'input-workspace-manifest.json').read_text())
                elements={'owner::port':{'kind':'port','owner':'owner','sha256':'synthetic-port-content'}}
                base={'run_id':run['id'],'config_hash':run['config_hash'],'input_manifest_sha256':digest(manifest),'elements':elements}
                reference=c.store.record('architecture_snapshot',base)
                registry={'record':{'snapshot_id':reference['id']}}
                unit={'formal_element_ids':['owner::port']}
                def gate(snapshot):
                    return {'status':'PASS','snapshot_id':snapshot['id'],'evidence':c.store.object({'run_id':run['id'],'snapshot_id':snapshot['id']})}
                m=Metrics(c)
                with patch.object(c,'status',return_value={'evidence_current_for_source':True,'policy_current':True}):
                    self.assertTrue(m._structural_unit_conforms(run,gate(reference),unit,registry))
                    for changes in [{'elements':{}},{'elements':{'owner::port':{**elements['owner::port'],'sha256':'changed'}}},{'config_hash':'stale'},{'run_id':'other'}]:
                        candidate=c.store.record('architecture_snapshot',{**base,**changes})
                        self.assertFalse(m._structural_unit_conforms(run,gate(candidate),unit,registry))
                    self.assertFalse(m._structural_unit_conforms(run,{**gate(reference),'status':'NOT_RUN'},unit,registry))
                with patch.object(c,'status',return_value={'evidence_current_for_source':False,'policy_current':True}):
                    self.assertFalse(m._structural_unit_conforms(run,gate(reference),unit,registry))
            finally:c.close()

    def test_structural_counts_never_inflate_behavioral_verification(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);project=root/'source';project.mkdir();(project/'Model.sysml').write_text('package Test {}')
            c=Controller(root/'state')
            try:
                run=c.create({'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only'})
                run={**c.status(run['id']),'config':{**run['config'],'unit_registry':'reviewed'},'evidence_current_for_source':True,'policy_current':True}
                structural={'id':'s','unit_kind':'structural-conformance','formal_gate_ids':['architecture_capture'],'formal_element_ids':['port'],'obligation_ids':['req-s'],'implementation_files':['Model.sysml'],'assumption_element_ids':[]}
                behavioral={**structural,'id':'b','unit_kind':'behavioral-contract','formal_gate_ids':['configured_formal_verification'],'formal_element_ids':['guarantee'],'obligation_ids':['req-b']}
                m=Metrics(c)
                with patch.object(c,'status',return_value=run),patch.object(m,'approved',return_value={'record':{'units':[structural,behavioral]}}),patch.object(m,'_structural_unit_conforms',return_value=True),patch.object(m,'_formal_unit_verified',return_value=True):
                    report=m.report(run['id'])
                    self.assertEqual(report['structural_conforming_count'],1)
                    self.assertEqual(report['registered_count'],1)
                    self.assertEqual(report['requirement_registered_count'],2)
                    self.assertEqual(report['verified_count'],0)
                    self.assertEqual(report['accepted_count'],0)
                    self.assertIn('assumption-discharge',str(report['problems']))
            finally:c.close()
