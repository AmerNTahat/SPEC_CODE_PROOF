"""Real DSSE cryptographic tests with ephemeral keys and synthetic recorded input."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
from securesystemslib.signer import CryptoSigner
from securesystemslib.exceptions import VerificationError
from inspecta_scp.attestation import Attestations
from inspecta_scp.config import PolicyError
from inspecta_scp.controller import Controller
from inspecta_scp.verify_attestation import verify,verify_files


class AttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.project=self.root/'source';self.project.mkdir();(self.project/'Model.sysml').write_text('package Synthetic {}')
        self.c=Controller(self.root/'state');self.service=Attestations(self.c)
        self.run=self.c.create({'project':str(self.project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only','required_gates':['parse_type']})
        self.c.store.change(self.run['id'],{'READY'},'CHECKING')
        # Explicit NOT_RUN is honest incomplete application evidence, never a simulated tool pass.
        self.c.store.finish(self.run['id'],{'task_status':'BLOCKED','gates':[{'gate':'parse_type','status':'NOT_RUN','reason':'Synthetic attestation fixture; no tool executed'}],'engineering_accepted':False})
        self.key=Ed25519PrivateKey.generate();self.key_path=self.root/'test-private.pem'
        self.key_path.write_bytes(self.key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption()));self.key_path.chmod(0o600)
        signer=CryptoSigner(self.key);self.trust={'keys':{signer.public_key.keyid:signer.public_key.to_dict()},'threshold':1}
        self.policy=self.service.policy(self.run['id']);self.bundle=self.root/'bundle'
        self.service.create(self.run['id'],self.key_path,self.policy,self.bundle)

    def tearDown(self):self.c.close();self.tmp.cleanup()

    def test_actual_signature_of_incomplete_record(self):
        result=verify(self.bundle,self.policy,self.trust)
        self.assertTrue(result['integrity_valid']);self.assertEqual(result['status'],'INCOMPLETE');self.assertFalse(result['engineering_accepted'])

    def test_modified_subject_rejected(self):
        (self.bundle/'inputs/Model.sysml').write_text('forged')
        with self.assertRaises(PolicyError):verify(self.bundle,self.policy,self.trust)

    def test_untrusted_key_rejected(self):
        other=CryptoSigner.generate_ed25519();trust={'keys':{other.public_key.keyid:other.public_key.to_dict()},'threshold':1}
        with self.assertRaises(VerificationError):verify(self.bundle,self.policy,trust)

    def test_changed_policy_and_stale_result_rejected(self):
        for field,value in [('result_sha256','0'*64),('last_event_id',-1),('mandatory_gates',[])]:
            changed={**self.policy,field:value}
            with self.assertRaises(PolicyError):verify(self.bundle,changed,self.trust)

    def test_current_source_change_rejected(self):
        (self.project/'Model.sysml').write_text('new user revision')
        with self.assertRaises(PolicyError):verify(self.bundle,self.policy,self.trust)

    def test_unlisted_file_and_symlink_rejected(self):
        path=self.bundle/'extra.txt';path.write_text('extra')
        with self.assertRaises(PolicyError):verify(self.bundle,self.policy,self.trust)
        path.unlink();path.symlink_to(self.project/'Model.sysml')
        with self.assertRaises(PolicyError):verify(self.bundle,self.policy,self.trust)

    def test_candidate_cannot_supply_own_trust(self):
        policy=self.bundle/'policy.json';policy.write_text(json.dumps(self.policy))
        trust=self.root/'trust.json';trust.write_text(json.dumps(self.trust))
        with self.assertRaises(PolicyError):verify_files(self.bundle,policy,trust)

    def test_incomplete_record_cannot_claim_engineering_acceptance(self):
        policy=self.service.policy(self.run['id'],'engineering_acceptance')
        with self.assertRaises(PolicyError):self.service.create(self.run['id'],self.key_path,policy,self.root/'accepted')
        self.assertFalse((self.root/'accepted').exists())

    def test_key_permission_and_source_zone_rejected(self):
        self.key_path.chmod(0o644)
        with self.assertRaises(PolicyError):self.service.create(self.run['id'],self.key_path,self.policy,self.root/'new')
        source_key=self.project/'key.pem';source_key.write_bytes(self.key_path.read_bytes());source_key.chmod(0o600)
        with self.assertRaises(PolicyError):self.service.create(self.run['id'],source_key,self.policy,self.root/'new')


if __name__=='__main__':unittest.main()
