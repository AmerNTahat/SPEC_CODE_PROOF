import copy
import unittest
from inspecta_scp.graph_equivalence import isomorphic,compare_architectures,graph_from_air

class GraphEquivalenceTests(unittest.TestCase):
    def graph(self,n,edges):return {'nodes':{str(i):{'kind':'node'} for i in range(n)},'edges':[(str(a),str(b),'wire') for a,b in edges]}
    def test_names_and_order_do_not_matter_and_witness_is_bijective(self):
        a=self.graph(4,[(0,1),(1,2),(2,3)]);rename={'0':'z','1':'a','2':'q','3':'k'}
        b={'nodes':{rename[k]:v for k,v in reversed(list(a['nodes'].items()))},'edges':[(rename[x],rename[y],t) for x,y,t in reversed(a['edges'])]}
        r=isomorphic(a,b);self.assertEqual(r['status'],'PASS');self.assertEqual(len(set(r['mapping'].values())),4)
    def test_same_counts_and_degrees_not_enough(self):
        cycle=self.graph(6,[(i,(i+1)%6) for i in range(6)])
        two=self.graph(6,[(0,1),(1,2),(2,0),(3,4),(4,5),(5,3)])
        self.assertEqual(isomorphic(cycle,two)['status'],'FAIL')
    def test_direction_and_multiplicity_are_preserved(self):
        a=self.graph(3,[(0,1),(0,2)]);b=self.graph(3,[(1,0),(2,0)])
        self.assertEqual(isomorphic(a,b)['status'],'FAIL')
        a=self.graph(2,[(0,1),(0,1)]);b=self.graph(2,[(0,1),(1,0)])
        self.assertEqual(isomorphic(a,b)['status'],'FAIL')
    def test_role_properties_and_unknown_bound(self):
        a=self.graph(3,[(0,1),(1,2)]);b=copy.deepcopy(a);b['nodes']['0']['period']=60
        self.assertEqual(isomorphic(a,b)['status'],'FAIL')
        self.assertEqual(isomorphic(a,a,max_states=0)['status'],'UNKNOWN')
    def test_self_loops_checked(self):
        a=self.graph(2,[(0,0),(1,1)]);b=self.graph(2,[(0,1),(1,0)])
        self.assertEqual(isomorphic(a,b)['status'],'FAIL')
    def test_unsupported_air_fails_closed(self):
        self.assertEqual(compare_architectures({}, {})['status'],'UNKNOWN')
