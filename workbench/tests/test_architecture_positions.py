import unittest
from inspecta_scp.architecture import normalize,differences

class PositionNormalizationTests(unittest.TestCase):
    def test_operator_locations_are_metadata_but_operations_remain_significant(self):
        a={'type':'org.sireum.lang.ast.Exp.Binary','op':'<=','left':{'value':0},'right':{'name':'x'},'opPosOpt':{'value':{'beginLine':1,'offset':2}}}
        b={**a,'opPosOpt':{'value':{'beginLine':90,'offset':999}}}
        self.assertEqual(differences(normalize(a),normalize(b)),[])
        self.assertNotEqual(differences(normalize(a),normalize({**b,'op':'<'})),[])
        self.assertNotEqual(normalize({'offset':1}),normalize({'offset':2}))
