"""Package/verify/plot actual offline tool evidence with an ephemeral test signer.
The public test key is not a production trust root; no paid demonstration is run.
"""
import json
from pathlib import Path
import tempfile
import subprocess
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
from securesystemslib.signer import CryptoSigner
from inspecta_scp.attestation import Attestations
from inspecta_scp.controller import Controller
from inspecta_scp.metrics import Metrics


def main():
    repo=Path.cwd();record=json.loads((repo/'reports/build/architecture-producer-consumer.json').read_text())
    c=Controller(repo/'.scp-workbench/architecture-integration')
    try:
        service=Attestations(c);policy=service.policy(record['id'])
        policy_path=repo/'reports/build/architecture-attestation-policy.json';policy_path.write_text(json.dumps(policy,indent=2)+'\n')
        with tempfile.TemporaryDirectory(prefix='inspecta-ephemeral-signer-') as temp:
            key=Ed25519PrivateKey.generate();path=Path(temp)/'test-private.pem'
            path.write_bytes(key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption()));path.chmod(0o600)
            signer=CryptoSigner(key);trust={'keys':{signer.public_key.keyid:signer.public_key.to_dict()},'threshold':1}
            trust_path=repo/'reports/build/TEST_ONLY-attestation-trust.json';trust_path.write_text(json.dumps(trust,indent=2)+'\n')
            bundle=repo/'reports/build/architecture-attestation'
            result=service.create(record['id'],path,policy,bundle)
            assert result['integrity_valid'] and not result['engineering_accepted'] and result['status']=='INCOMPLETE'
        completed=subprocess.run([str(repo/'.venv/bin/python'),'-m','inspecta_scp.verify_attestation',
            '--bundle',str(bundle),'--policy',str(policy_path),'--trust',str(trust_path)],capture_output=True,text=True)
        assert completed.returncode==3,completed.stdout+completed.stderr
        independent=json.loads(completed.stdout)
        plots=Metrics(c).export(record['id'],repo/'reports/build/offline-metric-plots')
        assert plots['report']['registered_count'] is None and plots['report']['verified_count']==0
        summary={'status':'PASS','scope':'Reporting over real offline architecture check; ephemeral TEST ONLY signer, no engineering acceptance or live demo',
            'model_calls':0,'signing_result':result,'independent_verifier':independent,'verifier_exit_code':completed.returncode,
            'plot_count':len(plots['figures']),'metrics':plots['report'],'private_key_retained':False}
        (repo/'reports/build/real-reporting-integration.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary,indent=2))
    finally:c.close()


if __name__=='__main__':main()
