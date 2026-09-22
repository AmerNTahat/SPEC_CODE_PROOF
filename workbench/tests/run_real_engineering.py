"""Actual HAMR/Logika positive, counterexample and zero-obligation checks."""
import json
from pathlib import Path
import re
import shutil
import uuid
from inspecta_scp.config import resolve
from inspecta_scp.controller import Controller
from inspecta_scp.storage import sha_file


def main():
    repo=Path.cwd();profile_path=repo/'workbench/profiles/producer-consumer.engineering.check.json'
    profile=json.loads(profile_path.read_text());config=resolve(profile,base_dir=profile_path.parent)['config']
    original_hashes={rel:sha_file(Path(config['project'])/rel) for rel in config['input_files']}
    root=repo/'.scp-workbench/engineering-tests'/uuid.uuid4().hex
    project=root/'project';project.mkdir(parents=True)
    for rel in config['input_files']:
        target=project/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(Path(config['project'])/rel,target)
    source=project/config['model_file'];original=source.read_text()
    profile['project']=str(project)
    controller=Controller(root/'state');cases=[]
    try:
        def run(name,expected):
            started=controller.create(profile,base_dir=profile_path.parent)
            finished=controller.execute(started['id'])
            cases.append({'case':name,'run':finished,'events':controller.store.events(started['id'])})
            print(name,finished['state'],flush=True)
            assert finished['state']==expected,finished
            assert not finished['result']['engineering_accepted']
        run('real_generation_and_nonempty_integration','CHECKED')
        profile['required_gates']=['parse_type','integration_constraints']
        bad=original.replace('(input.payload <= 100 [i32])','(input.payload <= 10 [i32])')
        assert bad != original
        source.write_text(bad)
        run('incompatible_receiver_contract','FAILED')
        empty,n=re.subn(r'integration\s+assume Payload_Range:.*?;', '',original,flags=re.S)
        assert n==1
        source.write_text(empty)
        run('no_receiver_obligations','BLOCKED')
        source.write_text(original)
        assert original_hashes=={rel:sha_file(Path(config['project'])/rel) for rel in config['input_files']}
        evidence=repo/'reports/build/engineering-evidence';evidence.mkdir(exist_ok=True)
        for path in (root/'state/objects').glob('*.json'):
            target=evidence/path.name
            if target.exists():assert target.read_bytes()==path.read_bytes()
            else:shutil.copy2(path,target)
        report={'scope':'Real offline code generation and connection integration; no implementation proof or live demonstration',
                'model_calls':0,'original_sources_unchanged':True,'state_directory':str(root/'state'),
                'cases':cases,'evidence_directory':str(evidence.relative_to(repo))}
        (repo/'reports/build/real-engineering-integration.json').write_text(json.dumps(report,indent=2)+'\n')
    finally:controller.close()


if __name__=='__main__':main()
