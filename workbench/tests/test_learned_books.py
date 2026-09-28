import tempfile
import unittest
from pathlib import Path
from inspecta_scp.storage import Store
from inspecta_scp.knowledge import Knowledge
from inspecta_scp.config import PolicyError

class LearnedBooksTests(unittest.TestCase):
    def test_snapshots_preserve_revisions_and_detect_modified_files(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d);knowledge=Knowledge(store)
            store.record('candidate_rule',{'record':{'id':'system-owner','revision':1,'principle':'Preserve ownership'}})
            first=knowledge.export_learned_books();old=Path(first['directory'])/'RULEBOOK.md';text=old.read_text()
            self.assertIn('DRAFT',text)
            self.assertEqual(first,knowledge.export_learned_books())
            self.assertEqual(knowledge.read_learned_book(first['id'])['text'],text)
            store.record('candidate_rule',{'record':{'id':'system-owner','revision':2,'principle':'Preserve ownership and bindings'}})
            second=knowledge.export_learned_books()
            self.assertNotEqual(first['snapshot_id'],second['snapshot_id'])
            self.assertEqual(old.read_text(),text)
            self.assertEqual(second['candidate_count'],2)
            Path(second['directory'],'RULEBOOK.md').write_text('unexpected edit')
            with self.assertRaisesRegex(PolicyError,'content changed'):knowledge.read_learned_book(second['id'])
            with self.assertRaisesRegex(PolicyError,'snapshot was modified'):knowledge.export_learned_books()
            store.close()
