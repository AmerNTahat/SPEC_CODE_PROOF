"""Control metadata isolation, not model semantic equivalence evidence."""
from pathlib import Path
import tempfile,unittest
from inspecta_scp.codegen_inputs import execution_view

class CodegenInputTests(unittest.TestCase):
    def test_explicit_options_win_without_editing_original_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/'source';src.mkdir()
            text='//@ HAMR: --platform Microkit --output-dir /unapproved\npackage Actual {\n // ordinary comment\n}\n'
            (src/'Model.sysml').write_text(text);out=root/'view'
            result=execution_view(src,out,['Model.sysml']);derived=(out/'Model.sysml').read_text()
            self.assertEqual((src/'Model.sysml').read_text(),text)
            self.assertEqual(derived.splitlines()[1:],text.splitlines()[1:])
            self.assertEqual(len(derived.splitlines()[0]),len(text.splitlines()[0]))
            self.assertNotIn('//@ HAMR:',derived);self.assertEqual(len(result['changes']),1)
            self.assertTrue((out/'.slang').is_dir())
