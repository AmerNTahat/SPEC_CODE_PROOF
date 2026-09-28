from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

lex=load('local_compare'); integrity=load('verify_package'); preflight=load('preflight')

class LexicalTests(unittest.TestCase):
    def test_identity(self): self.assertAlmostEqual(lex.compare_text('x <= 3','x <= 3')['cosine_similarity'],1.0)
    def test_whitespace(self): self.assertEqual(lex.compare_text('x<=3','x <= 3')['sequence_deleted_plus_inserted'],0)
    def test_both_empty(self):
        r=lex.compare_text('',' '); self.assertIsNone(r['cosine_similarity']); self.assertEqual(r['acceptance'],'NOT_ASSESSED')
    def test_one_empty(self): self.assertIsNone(lex.compare_text('','hello')['cosine_similarity'])
    def test_delete_everything(self): self.assertEqual(lex.sequence_edits(['a','b','c'],[]),3)
    def test_insert_everything(self): self.assertEqual(lex.sequence_edits([],['a','b']),2)
    def test_replace(self): self.assertEqual(lex.sequence_edits(['x'],['y']),2)
    def test_operator_distinction(self):
        self.assertNotEqual(lex.tokenize('x < 4'),lex.tokenize('x <= 4'))
        self.assertLess(lex.compare_text('x < 4','x <= 4')['cosine_similarity'],1)
    def test_negation_preserved(self): self.assertIn('not',lex.tokenize('not alarm'))
    def test_order_limitation_explicit(self):
        r=lex.compare_text('a -> b','b -> a')
        self.assertAlmostEqual(r['cosine_similarity'],1.0)
        self.assertGreater(r['sequence_deleted_plus_inserted'],0)
        self.assertEqual(r['semantic_equivalence'],'NOT_ESTABLISHED')
    def test_numeric_units(self): self.assertNotEqual(lex.tokenize('1 ms'),lex.tokenize('1 s'))
    def test_case_preserved(self): self.assertNotEqual(lex.tokenize('Port'),lex.tokenize('port'))
    def test_unicode(self): self.assertTrue(lex.tokenize('Δ <= 3'))
    def test_file_output_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a'; b=Path(d)/'b'; out=Path(d)/'out'
            a.write_text('a'); b.write_text('b'); out.write_text('keep')
            self.assertEqual(lex.main([str(a),str(b),'--output',str(out)]),2)
            self.assertEqual(out.read_text(),'keep')

class IntegrityTests(unittest.TestCase):
    def make(self,d):
        root=Path(d); (root/'a.txt').write_text('hello')
        digest=hashlib.sha256(b'hello').hexdigest()
        (root/'SHA256SUMS').write_text(f'{digest}  a.txt\n'); return root
    def test_valid(self):
        with tempfile.TemporaryDirectory() as d: self.assertTrue(integrity.verify(self.make(d))['ok'])
    def test_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.make(d); (root/'a.txt').write_text('changed'); self.assertFalse(integrity.verify(root)['ok'])
    def test_extra(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.make(d); (root/'extra').write_text('x'); self.assertFalse(integrity.verify(root)['ok'])
    def test_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.make(d); (root/'SHA256SUMS').write_text('0'*64+'  ../outside\n')
            self.assertFalse(integrity.verify(root)['ok'])
    def test_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.make(d); p=root/'SHA256SUMS'; p.write_text(p.read_text()*2); self.assertFalse(integrity.verify(root)['ok'])

class PreflightTests(unittest.TestCase):
    def test_no_model_or_install(self):
        result=preflight.inventory(False)
        self.assertEqual(result['model_calls'],0); self.assertFalse(result['installations_performed'])
        self.assertTrue(all(item['probe']=='NOT_RUN' for item in result['tools'].values()))
    def test_no_credentials(self):
        result=preflight.inventory(False); self.assertNotIn('OPENAI_API_KEY',json.dumps(result))

if __name__=='__main__': unittest.main()
