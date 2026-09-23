from pathlib import Path
import tempfile
import unittest
from inspecta_scp.approvals import Approvals
from inspecta_scp.config import PolicyError
from inspecta_scp.storage import Store
from inspecta_scp.unit_definitions import UnitDefinitions,FIELDS,ARRAYS

class DefinitionTests(unittest.TestCase):
    def test_edit_approval_and_revocation_bind_exact_definition(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d);service=UnitDefinitions(s)
            value={**{k:'Synthetic '+k for k in FIELDS},**{k:['Synthetic '+k] for k in ARRAYS},'granularity':'sysml_gumbo_obligation'}
            proposal=s.record('unit_definition_proposal',{'plan_id':'synthetic-test-only','model_call_id':'no-real-model','definition':value})
            draft=service.revise(proposal['id'],value)
            with self.assertRaises(PolicyError):service.approved(draft['id'])
            approval=draft['approval'];Approvals(s).decide(approval['id'],approval['subject_digest'],'APPROVED','Synthetic reviewer')
            self.assertEqual(service.approved(draft['id'])['verified_count'],0)
            revised=service.revise(proposal['id'],{**value,'definition':'Changed granularity description'})
            self.assertTrue(revised['human_modified'])
            with self.assertRaises(PolicyError):service.approved(revised['id'])
            Approvals(s).decide(approval['id'],approval['subject_digest'],'REVOKED','Synthetic reviewer')
            with self.assertRaises(PolicyError):service.approved(draft['id'])
            s.close()
