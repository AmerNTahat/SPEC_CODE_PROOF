import json
import tempfile
import unittest
from pathlib import Path
from inspecta_scp.api import Application
from inspecta_scp.config import PolicyError
from inspecta_scp.controller import Controller
from inspecta_scp.learning import Learning


class LearningTests(unittest.TestCase):
    def test_inspection_preserves_books_and_creates_no_model_work(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);project=root/'project';project.mkdir();books=root/'books';books.mkdir()
            model='package Test {}';book='# MR-LEARN-001\nPreserve this original.'
            (project/'Model.sysml').write_text(model);(books/'rules.md').write_text(book)
            profile={'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml'}
            path=root/'learning.json';path.write_text(json.dumps(profile))
            c=Controller(root/'state')
            try:
                result=Learning(c).inspect(profile,books,{'wall_seconds':600,'aggregate_model_tokens':10000},'interactive')
                self.assertEqual(result['status'],'MATERIALS_INSPECTED');self.assertEqual(result['document_count'],1)
                self.assertEqual(result['run']['config']['mode'],'learning');self.assertEqual(result['model_calls'],0)
                self.assertFalse(result['run']['config']['paid_runs_authorized'])
                self.assertEqual(result['run']['config']['assistance'],'interactive')
                self.assertEqual((project/'Model.sysml').read_text(),model);self.assertEqual((books/'rules.md').read_text(),book)
                catalog=Learning(c).catalog();self.assertEqual(len(catalog['sessions']),1)
                self.assertTrue(catalog['stages'][1]['available'])
                api=Application(root/'state',[path],[books])
                self.assertEqual(api.call('GET','/api/learning'),catalog)
                with self.assertRaises(PolicyError):api.call('POST','/api/learning/inspect',{'profile_id':'../../other','library_root_id':'0'})
            finally:c.close()
