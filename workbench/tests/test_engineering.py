import unittest
from inspecta_scp.engineering import classify


class EngineeringTests(unittest.TestCase):
    def test_empty_success_is_not_integration_proof(self):
        record={'stdout':'', 'stderr':'', 'exit_code':0, 'interrupted':None}
        self.assertEqual(classify('integration_constraints',record,{})[0],'UNKNOWN')
        record['stdout']='Integration constraints verified!'
        self.assertEqual(classify('integration_constraints',record,{})[0],'UNKNOWN')
        record['stdout']='Checking connection a\nIntegration constraints verified!'
        self.assertEqual(classify('integration_constraints',record,{})[0],'UNKNOWN')
        record['integration_results']=[{'type':'IntegrationConstraintReporting.IntegrationConstraint',
            'srcPort':'a.out','dstPort':'b.in','claim':'synthetic fixture','smt2Query':'synthetic fixture',
            'smt2QueryResult':{'value':'Unsat'}}]
        self.assertEqual(classify('integration_constraints',record,{})[0],'PASS')
        record['interrupted']='CANCELLED'
        self.assertEqual(classify('integration_constraints',record,{})[0],'UNKNOWN')

    def test_codegen_requires_artifacts_and_clean_model(self):
        record={'stdout':'', 'stderr':'', 'exit_code':0, 'interrupted':None}
        self.assertEqual(classify('hamr_codegen',record,{})[0],'UNKNOWN')
        self.assertEqual(classify('hamr_codegen',record,{'generated/Main.scala':{}})[0],'PASS')
        record['stdout']='Instantiation Warning'
        self.assertEqual(classify('hamr_codegen',record,{'generated/Main.scala':{}})[0],'UNKNOWN')
        record['exit_code']=1
        self.assertEqual(classify('hamr_codegen',record,{})[0],'FAIL')

    def test_microkit_requires_rust_and_build_manifest(self):
        record={'stdout':'','stderr':'','exit_code':0,'interrupted':None}
        for artifacts in ({'Main.scala':{}},{'lib.rs':{}},{'Cargo.toml':{}}):
            self.assertEqual(classify('hamr_codegen',record,artifacts,'Microkit')[0],'UNKNOWN')
        status,scope=classify('hamr_codegen',record,{'lib.rs':{},'Cargo.toml':{}},'Microkit')
        self.assertEqual(status,'PASS');self.assertIn('separate',scope)


if __name__=='__main__': unittest.main()
