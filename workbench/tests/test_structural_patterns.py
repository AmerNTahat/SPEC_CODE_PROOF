import unittest
from inspecta_scp.structural_patterns import structural_patterns,source_outline

def component(category,children=None,name='arbitrary',annexes=None):
    return {'category':{'value':category},'identifier':{'name':[name]},'subComponents':children or [],'annexes':annexes or []}
def check(root):return structural_patterns({'models':{'test':{'components':[root]}}})['roots'][0]
class StructuralPatternTests(unittest.TestCase):
    def test_reference_abstraction_and_flattening(self):
        good=component('System',[component('Process',[component('Thread')]) for _ in range(4)])
        bad=component('Process',[component('Thread') for _ in range(4)])
        self.assertEqual(check(good)['one_thread_per_process']['status'],'PASS')
        self.assertEqual(check(bad)['one_thread_per_process']['status'],'FAIL')
        self.assertEqual(check(bad)['one_thread_per_process']['violations'][0]['direct_threads'],4)
    def test_missing_wrappers_unknown_and_contract_ownership(self):
        self.assertEqual(check(component('System',[component('Thread')]))['one_thread_per_process']['status'],'FAIL')
        annex={'name':'GUMBO','clause':{'type':'GclSubclause'}}
        r=check(component('Process',[component('Thread',annexes=[annex])]))
        self.assertEqual(r['gumbo_owner_categories'],{'Thread':1})
        self.assertEqual(check(component('System'))['one_thread_per_process']['status'],'UNKNOWN')
        self.assertEqual(check({'identifier':{'name':['missing']}})['one_thread_per_process']['status'],'UNKNOWN')
    def test_source_outline_ignores_comments_and_contract_text(self):
        r=source_outline('// part def fake :> Thread {}\npart def X :> AADL::System { language "GUMBO" /*{ part def fake :> Process {} }*/ }\npart def Y :> Process {}')
        self.assertEqual(r['category_order'],['System','Process'])
        self.assertEqual(r['status'],'ADVISORY')
