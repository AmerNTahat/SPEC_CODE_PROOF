import unittest
from inspecta_scp.contract_similarity import compare_contract_features

class ContractSimilarityTests(unittest.TestCase):
    def model(self,op='<',kind='GclGuarantee'):
        return {'models':{'instance':{'contract':{'type':kind,'id':'label','exp':{'op':op,'value':90,'attr':{'line':4}}}}}}
    def test_only_after_graph_and_no_acceptance_inferred(self):
        a=self.model()
        self.assertEqual(compare_contract_features(a,a,{'status':'FAIL'})['status'],'NOT_RUN')
        same=compare_contract_features(a,a,{'status':'PASS'})
        self.assertAlmostEqual(same['cosine_similarity'],1)
        self.assertFalse(same['threshold_applied'])
        changed=compare_contract_features(a,self.model('>'),{'status':'PASS'})
        self.assertLess(changed['cosine_similarity'],1)
        swapped=compare_contract_features(a,self.model(kind='GclAssume'),{'status':'PASS'})
        self.assertLess(swapped['cosine_similarity'],1)
    def test_empty_is_undefined_not_perfect(self):
        empty={'models':{}}
        self.assertEqual(compare_contract_features(empty,empty,{'status':'PASS'})['status'],'UNDEFINED')
