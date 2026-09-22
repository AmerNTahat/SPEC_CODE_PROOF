"""Independent local DSSE verifier: supplied trust and policy, no controller database."""
import argparse
import copy
import json
from pathlib import Path
from securesystemslib.dsse import Envelope
from securesystemslib.signer import Key

from .config import PolicyError, digest, relative_file
from .storage import safe_child, sha_file

STATEMENT_TYPE = 'https://in-toto.io/Statement/v1'
PREDICATE_TYPE = 'urn:inspecta-scp:validation-record:v1'
PAYLOAD_TYPE = 'application/vnd.in-toto+json'
ENGINEERING_GATES = {'parse_type', 'requirements_coverage', 'architecture', 'configured_build',
                     'configured_formal_verification', 'independent_requirements_tests', 'review'}


def verify(bundle, policy, trust):
    bundle = Path(bundle).absolute()
    if any(p.is_symlink() for p in [bundle, *bundle.parents]):
        raise PolicyError('Bundle root cannot use symlinks')
    envelope = Envelope.from_dict(copy.deepcopy(json.loads(safe_child(bundle,'envelope.json').read_text())))
    if envelope.payload_type != PAYLOAD_TYPE:
        raise PolicyError('Unexpected DSSE payload type')
    if not isinstance(trust, dict) or set(trust) != {'keys','threshold'} or type(trust['threshold']) is not int:
        raise PolicyError('External trust root requires keys and integer threshold')
    keys = [Key.from_dict(keyid, copy.deepcopy(value)) for keyid,value in trust['keys'].items()]
    accepted_signers = envelope.verify(keys, trust['threshold'])
    statement = json.loads(envelope.payload)
    if statement.get('_type') != STATEMENT_TYPE or statement.get('predicateType') != PREDICATE_TYPE:
        raise PolicyError('Unexpected attestation statement/predicate')
    predicate=statement['predicate']
    if predicate['policy_sha256'] != digest(policy):
        raise PolicyError('Signed policy differs from independently supplied policy')
    names={}
    for subject in statement['subject']:
        name=relative_file(subject['name'])
        if name=='envelope.json' or name in names or set(subject['digest'])!={'sha256'}:
            raise PolicyError('Duplicate, recursive or unsupported subject')
        path=safe_child(bundle,name)
        if not path.is_file() or sha_file(path)!=subject['digest']['sha256']:
            raise PolicyError('Subject missing or modified: '+name)
        names[name]=subject['digest']['sha256']
    actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file() and p!=bundle/'envelope.json'}
    if any(p.is_symlink() for p in bundle.rglob('*')) or actual!=set(names):
        raise PolicyError('Bundle contains unlisted or unsafe files')
    for required in ['run.json','events.json','input-manifest.json']:
        if required not in names:raise PolicyError('Missing required evidence subject: '+required)
    run=json.loads((bundle/'run.json').read_text())
    manifest=json.loads((bundle/'input-manifest.json').read_text())
    events=json.loads((bundle/'events.json').read_text())
    if run['id']!=policy['run_id'] or digest(run['config'])!=policy['config_sha256'] or run['config_hash']!=policy['config_sha256']:
        raise PolicyError('Wrong run/configuration identity')
    if digest(manifest)!=policy['input_manifest_sha256'] or digest(run['result'])!=policy['result_sha256']:
        raise PolicyError('Stale or substituted result/input manifest')
    if not events or events[-1]['id']!=policy['last_event_id']:
        raise PolicyError('Stale event sequence')
    if manifest['files']!=policy['source_hashes']:
        raise PolicyError('Source inventory differs from expected policy')
    source=Path(policy['source_root'])
    if any(p.is_symlink() for p in [source,*source.parents]):raise PolicyError('Unsafe external source root')
    for rel,expected in policy['source_hashes'].items():
        path=relative_file(rel)
        if names.get('inputs/'+path)!=expected or sha_file(safe_child(source,path))!=expected:
            raise PolicyError('Stale source dependency: '+path)
    for key in ('architecture_policy','requirement_ledger','rule_release','unit_registry','dataset_assignment','dataset_task'):
        if run['config'].get(key)!=policy.get(key):raise PolicyError('Policy/library/ledger/registry identity differs')
    gates=(run.get('result') or {}).get('gates',[])
    if len({g['gate'] for g in gates})!=len(gates):raise PolicyError('Duplicate gate result')
    by_gate={g['gate']:g for g in gates}
    missing=set(policy['mandatory_gates'])-set(by_gate)
    if missing:raise PolicyError('Mandatory gate records missing: '+','.join(sorted(missing)))
    def object_value(reference):
        path=reference['path']
        if names.get(path)!=reference['sha256']:raise PolicyError('Unbound evidence object')
        return json.loads(safe_child(bundle,path).read_text())
    def command_evidence(value):
        if 'capture_evidence' in value:return command_evidence(object_value(value['capture_evidence']))
        return value
    for gate in gates:
        if gate.get('evidence'):
            record=command_evidence(object_value(gate['evidence']))
            if 'config_sha256' in record and (record['config_sha256']!=policy['config_sha256'] or record['input_manifest_sha256']!=policy['input_manifest_sha256']):
                raise PolicyError('Tool evidence belongs to another artifact/configuration')
            if 'tool_identity' in record and record['tool_identity'] not in policy['tool_identities']:
                raise PolicyError('Unapproved tool identity')
    for dependency in policy.get('external_dependencies',[]):
        path=Path(dependency['path'])
        if any(p.is_symlink() for p in [path,*path.parents]) or sha_file(path)!=dependency['sha256']:
            raise PolicyError('External requirement/library dependency changed')
    expected_acceptance=bool(run.get('result') and run['result'].get('engineering_accepted'))
    if predicate['engineering_accepted'] != expected_acceptance:
        raise PolicyError('Acceptance claim differs from recorded result')
    complete = expected_acceptance and ENGINEERING_GATES<=set(by_gate) and all(by_gate[g]['status']=='PASS' and by_gate[g].get('evidence') for g in ENGINEERING_GATES)
    if expected_acceptance and not complete:raise PolicyError('Acceptance claimed without mandatory engineering gates')
    if policy['scope']=='engineering_acceptance' and not complete:raise PolicyError('Engineering acceptance is incomplete')
    if policy['scope'] not in {'record_integrity','engineering_acceptance'}:raise PolicyError('Unknown external verification scope')
    return {'status':'ACCEPTED' if complete else 'INCOMPLETE', 'integrity_valid':True, 'freshness_valid':True,
            'engineering_accepted':complete,'signers':sorted(accepted_signers), 'run_id':run['id'],
            'scope':'Local private-trust verification; no certification or SLSA level claim'}


def verify_files(bundle, policy_path, trust_path):
    root=Path(bundle).resolve()
    for path in (Path(policy_path).resolve(),Path(trust_path).resolve()):
        if path==root or root in path.parents:raise PolicyError('Policy and trust must be supplied outside the candidate bundle')
    from securesystemslib.exceptions import Error
    try:
        return verify(bundle,json.loads(Path(policy_path).read_text()),json.loads(Path(trust_path).read_text()))
    except Error as exc:
        raise PolicyError('Attestation signature/format rejected: ' + str(exc)) from exc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--policy',type=Path,required=True);parser.add_argument('--trust',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=verify_files(args.bundle,args.policy,args.trust);print(json.dumps(result,indent=2))
        return 0 if result['engineering_accepted'] else 3
    except Exception as exc:
        print(json.dumps({'status':'INVALID','error':str(exc)}));return 2


if __name__=='__main__':raise SystemExit(main())
