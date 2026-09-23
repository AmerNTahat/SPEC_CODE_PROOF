import tempfile
import unittest
from unittest.mock import patch
from inspecta_scp.controller import Controller

class TypeDiagnosticTests(unittest.TestCase):
    def test_zero_exit_with_real_error_format_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            c=Controller(d)
            try:
                diagnostic="* file:///work/Model.sysml\n  - [34, 38] TypeChecker Error: Could not resolve id 'Periodic'.\n"
                for stdout,stderr in [(diagnostic,''),('Well-formed!',diagnostic)]:
                    with patch.object(c,'_run_tool',return_value=({'stdout':stdout,'stderr':stderr,'exit_code':0},None,None)):
                        gate,interrupted=c._parse_type('synthetic',{},None)
                        self.assertEqual(gate['status'],'FAIL')
                        self.assertIsNone(interrupted)
            finally:c.close()
