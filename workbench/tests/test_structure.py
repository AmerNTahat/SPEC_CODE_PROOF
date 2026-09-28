"""Synthetic structural/ledger negatives; distinct from real HAMR integration."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from inspecta_scp.approvals import Approvals
from inspecta_scp.architecture import Architecture, normalize, differences, apply_delta, element_index
from inspecta_scp.config import PolicyError
from inspecta_scp.controller import Controller
from inspecta_scp.requirements import Requirements
from inspecta_scp.sources import Sources


def model():
    return {'type': 'Aadl', 'components': [{'type': 'Component', 'identifier': {'name': ['System']},
        'category': {'value': 'System'}, 'classifier': {'value': {'name': 'SystemType'}},
        'features': [{'type': 'FeatureEnd', 'identifier': {'name': ['System', 'in']}, 'direction': 'In', 'category': 'DataPort'}],
        'subComponents': [], 'connections': [{'name': {'name': ['System', 'wire']}, 'src': 'producer', 'dst': 'consumer'}],
        'annexes': [{'type': 'GclGuarantee', 'id': 'G1', 'exp': {'op': '<=', 'limit': 90}}],
        'properties': [{'type': 'UnitProp', 'value': '1', 'unit': {'type': 'Some', 'value': 'ms'}}]}]}


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = Controller(self.root / 'state')
        self.a = Architecture(self.c)
        self.r = Requirements(self.c.store)
        self.raw = {'models': {'System': model()}, 'declarations': {'System': {'definition': 'SystemType'}}}
        self.snapshot = self.snapshot_of(self.raw)

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def snapshot_of(self, value):
        return self.c.store.record('architecture_snapshot', {'normalized': self.c.store.object(normalize(value)),
            'elements': element_index(value['models']), 'tool_identity': {'scope': 'synthetic unit fixture'},
            'normalization': 'hamr-position-free-time-ps-v1'})

    def approve(self, request):
        return Approvals(self.c.store).decide(request['id'], request['subject_digest'], 'APPROVED', 'synthetic-unit-test')

    def check(self, value, changes=None):
        policy = self.a.propose(self.snapshot['id'], changes)
        self.approve(self.a.request_review(policy['id']))
        candidate = self.snapshot_of(value)
        return self.a.check(policy['id'], {'status': 'PASS', 'snapshot_id': candidate['id'], 'evidence': self.c.store.object({'synthetic': True})})

    def test_equivalent_units_and_positions(self):
        changed = copy.deepcopy(self.raw)
        prop = changed['models']['System']['components'][0]['properties'][0]
        prop.update(value='1000',unit={'type':'Some','value':'us'},pos={'line':999})
        self.assertEqual(self.check(changed)['status'], 'PASS')

    def test_negative_wiring_owner_ports_contracts_and_period(self):
        mutations = [lambda c: c.update(connections=[]),
            lambda c: c['connections'][0].update(src='consumer',dst='producer'),
            lambda c: c['features'][0].update(category='EventPort'),
            lambda c: c['features'][0].update(direction='Out'),
            lambda c: c.update(annexes=[]),
            lambda c: c['annexes'][0]['exp'].update(op='<'),
            lambda c: c['properties'][0].update(value='2'),
            lambda c: c['classifier']['value'].update(name='OtherRole')]
        # Each policy subject is stable; approve once then compare all mutations.
        policy = self.a.propose(self.snapshot['id'])
        self.approve(self.a.request_review(policy['id']))
        for mutation in mutations:
            value=copy.deepcopy(self.raw);mutation(value['models']['System']['components'][0])
            snapshot=self.snapshot_of(value)
            result=self.a.check(policy['id'], {'status':'PASS','snapshot_id':snapshot['id'],'evidence':self.c.store.object({'synthetic':True})})
            self.assertEqual(result['status'],'FAIL')

    def test_exact_reviewed_delta_and_unrelated_change(self):
        value=copy.deepcopy(self.raw)
        value['declarations']['System']['definition']='ReviewedName'
        changes=[{'path':['declarations','System','definition'],'before':'SystemType','after':'ReviewedName','rationale':'Synthetic authorized name change'}]
        self.assertEqual(self.check(value,changes)['status'],'PASS')
        value['models']['System']['components'][0]['annexes']=[]
        # Direct comparison to reviewed expected form detects the extra deletion.
        self.assertTrue(differences(apply_delta(normalize(self.raw),changes),normalize(value)))

    def test_stale_delta_before_and_overlap_rejected(self):
        change={'path':['declarations','System','definition'],'before':'wrong','after':'x','rationale':'test'}
        with self.assertRaises(PolicyError):self.a.propose(self.snapshot['id'],[change])
        change['before']='SystemType'
        with self.assertRaises(PolicyError):self.a.propose(self.snapshot['id'],[change,change])

    def test_policy_revocation_and_tool_change(self):
        policy=self.a.propose(self.snapshot['id']);request=self.a.request_review(policy['id']);self.approve(request)
        altered=self.c.store.record('architecture_snapshot',{**self.snapshot,'tool_identity':{'version':'different'}})
        result=self.a.check(policy['id'],{'status':'PASS','snapshot_id':altered['id'],'evidence':self.c.store.object({})})
        self.assertEqual(result['status'],'UNKNOWN')
        Approvals(self.c.store).decide(request['id'],request['subject_digest'],'REVOKED','test')
        with self.assertRaises(PolicyError):self.a.approved(policy['id'])

    def ledger(self):
        folder=self.root/'requirements';folder.mkdir(exist_ok=True)
        path=folder/'source.txt';path.write_text('The test system shall bound the payload.\n')
        sources=Sources(self.c.store);root=sources.register_root(folder,'shared');source=sources.register(root['id'],'source.txt')
        return {'$schema':'requirements.schema.json','schema_version':'1.0','record_type':'requirement_ledger',
            'project_id':'SYNTHETIC-TEST','state':'DRAFT','source_manifest':None,'approval_reference':None,'notes':'test fixture',
            'obligations':[{'id':'TEST-1','parent_id':None,'source_reference':source['id'],
                'source_text':'The test system shall bound the payload.','obligation':'Bound the test payload.',
                'owner':'System','representation':'behavior_contract','required_gate_ids':['configured_formal_verification'],
                'mapped_elements':['System#G1'],'review_status':'DRAFT','approval_reference':None}]}

    def coverage(self, value):
        ledger=self.r.propose(value);self.approve(self.r.request_review(ledger['id']))
        return self.r.coverage(ledger['id'],{'status':'PASS','snapshot_id':self.snapshot['id']})

    def test_mapped_never_means_checked_or_semantically_accepted(self):
        result=self.coverage(self.ledger())
        self.assertEqual(result['status'],'PASS');self.assertEqual(result['mapped_obligations'],1)
        self.assertEqual(result['checked_obligations'],0)

    def test_missing_contract_wrong_owner_and_assumption_not_guarantee(self):
        for field,value in [('mapped_elements',['System#MISSING']),('owner','WrongOwner'),('mapped_elements',['System::in'])]:
            ledger=self.ledger();ledger['obligations'][0][field]=value
            self.assertEqual(self.coverage(ledger)['status'],'FAIL')

    def test_duplicate_cyclic_and_fabricated_citation_rejected(self):
        for mutation in ['duplicate','cycle','source']:
            ledger=self.ledger()
            if mutation=='duplicate':ledger['obligations']*=2
            if mutation=='cycle':ledger['obligations'][0]['parent_id']='TEST-1'
            if mutation=='source':ledger['obligations'][0]['source_text']='Invented requirement'
            with self.assertRaises(PolicyError):self.r.propose(ledger)

    def test_stale_source_invalidates_reviewed_ledger(self):
        ledger=self.r.propose(self.ledger());self.approve(self.r.request_review(ledger['id']))
        (self.root/'requirements/source.txt').write_text('User revision')
        with self.assertRaises(PolicyError):self.r.approved(ledger['id'])

    def test_ledger_cannot_omit_mandatory_gates(self):
        ledger=self.r.propose(self.ledger());self.approve(self.r.request_review(ledger['id']))
        with self.assertRaises(PolicyError):
            self.c._validate_policies({'requirement_ledger':ledger['id'],'required_gates':['parse_type']})


if __name__=='__main__':unittest.main()
