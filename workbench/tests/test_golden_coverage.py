"""Coverage disclosure must not certify rules or conceal a changed reference."""
from pathlib import Path
import hashlib,tempfile,unittest
from inspecta_scp.controller import Controller
from inspecta_scp.golden_coverage import coverage_catalog

class GoldenCoverageTests(unittest.TestCase):
    def test_note_never_qualifies_a_candidate_and_reference_changes_are_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ref=root/'Golden.sysml';ref.write_text('package Example {}')
            c=Controller(root/'state')
            try:
                c.store.record('golden_coverage_note',{'feature':'Synthetic uncovered requirement','reference_files':[{'path':str(ref),'sha256':hashlib.sha256(ref.read_bytes()).hexdigest()}]})
                c.store.record('candidate_rule',{'record':{'id':'SYNTHETIC'}})
                report=coverage_catalog(c.store)
                self.assertEqual(report['candidates_without_completed_review'],1)
                self.assertFalse(report['acceptance_from_coverage_notes'])
                self.assertFalse(report['notes'][0]['establishes_tool_limitation'])
                self.assertEqual(report['notes'][0]['verification_credit'],0)
                self.assertTrue(report['notes'][0]['reference_current'])
                ref.write_text('package Changed {}')
                self.assertEqual(coverage_catalog(c.store)['notes'][0]['scope_status'],'STALE_RECHECK_REFERENCE')
            finally:c.close()
