import json,tempfile,unittest
from pathlib import Path
from inspecta_scp.application_results import recorded_checks
from inspecta_scp.storage import sha_file

class ApplicationResultsTests(unittest.TestCase):
    def test_receipt_binding_prevents_changed_log_credit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'reports/build').mkdir(parents=True);(root/'.scp-workbench').mkdir()
            log=root/'reports/build/application-tests.log';log.write_text('Ran 7 tests in 0.1s\n\nOK\n')
            browser=root/'reports/build/browser-smoke.json';browser.write_text(json.dumps({'status':'PASS','checks':['synthetic']}))
            (root/'.scp-workbench/BUILD_RESULT.json').write_text(json.dumps({'evidence':[{'path':str(p.relative_to(root)),'sha256':sha_file(p)} for p in [log,browser]]}))
            r=recorded_checks(root)['checks'];self.assertEqual(r[0]['passed'],7);self.assertEqual(r[1]['passed'],1)
            log.write_text('Ran 700 tests in 0.1s\n\nOK\n');r=recorded_checks(root)['checks'][0];self.assertEqual(r['status'],'STALE_OR_UNBOUND');self.assertIsNone(r['passed'])
    def test_absent_receipt_cannot_grant_credit(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(all(x['passed'] is None for x in recorded_checks(d)['checks']))
