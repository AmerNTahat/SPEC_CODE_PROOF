"""Exact projection policy tests; not real architecture evidence."""
import copy,unittest
from unittest.mock import patch
from inspecta_scp.approved_comparison import compare
from inspecta_scp.config import PolicyError
class ApprovedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.prop={'name':{'name':['HAMR::Implementation_Language']},'propertyValues':[{'type':'ValueProp','value':'Rust'}]}
        self.left={'nodes':{'a':{'kind':'component','properties':[]}},'edges':[]}
        self.right=copy.deepcopy(self.left);self.right['nodes']['a']['properties']=[self.prop]
        self.proposal=[{'result_id':'result','exact_candidate_additions':[{'node':'a','property':self.prop}]}]
    def run_projection(self,right):
        with patch('inspecta_scp.approved_comparison.approved_scope',return_value=self.proposal),patch('inspecta_scp.approved_comparison.graph_from_air',side_effect=copy.deepcopy):
            return compare(None,{'id':'result'},[self.left,right],'approval')[0]
    def test_only_exact_approved_addition_is_removed(self):
        self.assertEqual(self.run_projection(self.right)['status'],'PASS')
        self.assertEqual(len(self.right['nodes']['a']['properties']),1)
    def test_unapproved_property_remains_failure(self):
        self.right['nodes']['a']['properties'].append({'unapproved':'change'})
        self.assertEqual(self.run_projection(self.right)['status'],'FAIL')
    def test_unapproved_edge_remains_failure(self):
        self.right['edges']=[('a','a','unapproved')]
        self.assertEqual(self.run_projection(self.right)['status'],'FAIL')
    def test_changed_approved_property_is_rejected(self):
        self.right['nodes']['a']['properties']=[]
        with self.assertRaises(PolicyError):self.run_projection(self.right)
    def test_other_result_is_not_covered(self):
        self.proposal[0]['result_id']='other'
        with self.assertRaises(PolicyError):self.run_projection(self.right)
