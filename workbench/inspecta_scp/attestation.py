"""Controller-side signed evidence packaging. Private keys stay outside the repo."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from securesystemslib.dsse import Envelope
from securesystemslib.signer import CryptoSigner

from .config import PolicyError,canonical,digest
from .storage import safe_child,sha_file
from .verify_attestation import STATEMENT_TYPE,PREDICATE_TYPE,PAYLOAD_TYPE,verify


class Attestations:
    def __init__(self,controller):self.controller=controller;self.store=controller.store

    def policy(self,run_id,scope='record_integrity'):
        run=self.controller.status(run_id)
        if run['state'] not in {'CHECKED','FAILED','BLOCKED','CANCELLED','BUDGET_EXHAUSTED'}:
            raise PolicyError('Attest only completed or blocked runs')
        if not run.get('evidence_current_for_source') or not run.get('policy_current',True):raise PolicyError('Cannot attest stale evidence')
        folder=self.store.root/'runs'/run_id
        manifest=json.loads((folder/'input-workspace-manifest.json').read_text())
        tools=[]
        for gate in (run.get('result') or {}).get('gates',[]):
            if gate.get('evidence'):
                record=self.store.load_object(gate['evidence'])
                if 'capture_evidence' in record:record=self.store.load_object(record['capture_evidence'])
                if 'tool_identity' in record and record['tool_identity'] not in tools:tools.append(record['tool_identity'])
        dependencies=[]
        if run['config'].get('requirement_ledger'):
            ledger=self.store.read_record('requirement_ledger',run['config']['requirement_ledger'])
            for source_id,sha in ledger['sources'].items():
                source=self.store.read_record('source',source_id);root=self.store.read_record('source_root',source['root_id'])
                dependencies.append({'path':str(safe_child(Path(root['path']),source['relative'])),'sha256':sha})
        if run['config'].get('dataset_assignment'):
            dataset=self.store.read_record('dataset',run['config']['dataset_assignment'])
            for task in dataset['proposal']['tasks']:
                for source_id in task['source_ids']+task['reference_ids']:
                    source=self.store.read_record('source',source_id);root=self.store.read_record('source_root',source['root_id'])
                    dependency={'path':str(safe_child(Path(root['path']),source['relative'])),'sha256':source['sha256']}
                    if dependency not in dependencies:dependencies.append(dependency)
        return {'schema_version':1,'scope':scope,'run_id':run_id,'config_sha256':run['config_hash'],
            'input_manifest_sha256':digest(manifest),'result_sha256':digest(run['result']),
            'last_event_id':self.store.events(run_id)[-1]['id'],'source_root':run['config']['project'],
            'source_hashes':manifest['files'],'mandatory_gates':run['config']['required_gates'],
            'architecture_policy':run['config'].get('architecture_policy'),'requirement_ledger':run['config'].get('requirement_ledger'),
            'rule_release':run['config']['rule_release'],'unit_registry':run['config'].get('unit_registry'),
            'dataset_assignment':run['config'].get('dataset_assignment'),'dataset_task':run['config'].get('dataset_task'),
            'tool_identities':tools,'external_dependencies':dependencies,
            'review_note':'Review this external policy and select the trusted key independently before verification.'}

    def create(self,run_id,key_path,policy,output):
        output=Path(output).absolute();key_path=Path(key_path).absolute()
        repo=Path(__file__).resolve().parents[2]
        if any(p.is_symlink() for p in [key_path,*key_path.parents]) or repo in key_path.parents or self.store.root in key_path.parents:
            raise PolicyError('Signing key must be outside repository, candidate and controller state')
        source=Path(self.store.get(run_id)['config']['project'])
        if source in key_path.parents or output in key_path.parents or key_path.stat().st_mode & 0o077:
            raise PolicyError('Signing key must be private and outside source/output workspaces')
        if self.policy(run_id,policy['scope'])!=policy:raise PolicyError('External policy is stale or differs from current evidence')
        if output.exists() or any(p.is_symlink() for p in [output,*output.parents]):raise PolicyError('Use a new safe bundle output directory')
        output.parent.mkdir(parents=True,exist_ok=True)
        temporary=Path(tempfile.mkdtemp(prefix='.attest-',dir=output.parent))
        try:
            signer=CryptoSigner(load_pem_private_key(key_path.read_bytes(),password=None))
            run=self.controller.status(run_id);folder=self.store.root/'runs'/run_id
            (temporary/'run.json').write_text(canonical(run))
            (temporary/'events.json').write_text(canonical(self.store.events(run_id)))
            shutil.copyfile(folder/'input-workspace-manifest.json',temporary/'input-manifest.json')
            for rel,sha in policy['source_hashes'].items():
                source_file=safe_child(folder/'candidate',rel)
                if sha_file(source_file)!=sha:raise PolicyError('Candidate changed before packaging')
                dest=safe_child(temporary,'inputs/'+rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_file,dest)
            visited=set()
            def objects(value):
                if isinstance(value,dict):
                    if set(value)=={'sha256','path'} and str(value['path']).startswith('objects/'):
                        if value['sha256'] in visited:return
                        visited.add(value['sha256']);payload=self.store.load_object(value)
                        dest=safe_child(temporary,value['path']);dest.parent.mkdir(parents=True,exist_ok=True)
                        dest.write_text(canonical(payload));objects(payload)
                    for child in value.values():objects(child)
                elif isinstance(value,list):
                    for child in value:objects(child)
            objects(run.get('result'))
            subjects=[{'name':p.relative_to(temporary).as_posix(),'digest':{'sha256':sha_file(p)}} for p in sorted(temporary.rglob('*')) if p.is_file()]
            statement={'_type':STATEMENT_TYPE,'subject':subjects,'predicateType':PREDICATE_TYPE,
                'predicate':{'policy_sha256':digest(policy),'engineering_accepted':bool(run.get('result') and run['result'].get('engineering_accepted')),
                             'scope':'Recorded Workbench validation evidence, including incomplete/failed outcomes'}}
            envelope=Envelope(canonical(statement).encode(),PAYLOAD_TYPE,{});envelope.sign(signer)
            (temporary/'envelope.json').write_text(canonical(envelope.to_dict()))
            trust={'keys':{signer.public_key.keyid:signer.public_key.to_dict()},'threshold':1}
            result=verify(temporary,policy,trust)
            if self.policy(run_id,policy['scope'])!=policy:raise PolicyError('Evidence changed while signing')
            temporary.rename(output)
            return {**result,'bundle':str(output),'policy_sha256':digest(policy),
                'key_id':signer.public_key.keyid,'envelope_sha256':sha_file(output/'envelope.json')}
        finally:
            if temporary.exists():shutil.rmtree(temporary)
