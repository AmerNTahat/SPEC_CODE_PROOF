"""Actual KSU Simple Isolette syntax-migration experiment; provisional only."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid
from inspecta_scp.config import resolve
from inspecta_scp.controller import Controller
from inspecta_scp.repairs import Repairs


def main():
    repo=Path.cwd();profile_path=repo/'workbench/profiles/ksu-simple-isolette.check.json'
    profile=json.loads(profile_path.read_text());config=resolve(profile,base_dir=profile_path.parent)['config']
    root=repo/'.scp-workbench/isolette-migrations'/uuid.uuid4().hex;project=root/'project';project.mkdir(parents=True)
    for rel in config['input_files']:
        path=project/rel;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(Path(config['project'])/rel,path)
    patch={};matches=0
    pattern=re.compile(r'(?m)^(\s*)(in|out) port ([^\n{}]+)\{\s*:>> type : ([^\n{}]+)\}')
    for rel in config['input_files']:
        if not rel.startswith('isolette-simple/'):continue
        path=project/rel;before=path.read_text()
        after,count=pattern.subn(lambda m:m[1]+'port '+m[3]+'{ '+m[2]+' :>> type : '+m[4]+'}',before)
        if count:patch[rel]={'expected_sha256':hashlib.sha256(before.encode()).hexdigest(),'text':after};matches+=count
    assert matches==12,(matches,list(patch))
    profile.update(project=str(project),repair_allowed_files=sorted(patch));profile['budget']['wall_seconds']=240
    c=Controller(root/'state');service=Repairs(c)
    try:
        run=c.create(profile,base_dir=profile_path.parent)
        candidate=service.stage(run['id'],'KSU data-port direction syntax compatibility',patch)
        validation=service.validate(candidate['id'])
        for rel in patch:assert hashlib.sha256((project/rel).read_bytes()).hexdigest()==patch[rel]['expected_sha256']
        report={'scope':'Real disposable KSU Simple Isolette syntax migration; not approved design, formal verification or live demonstration',
            'model_calls':0,'source_files_modified':0,'port_declarations_rewritten':matches,
            'state_directory':str((root/'state').relative_to(repo)), 'run_id':run['id'],
            'candidate':candidate,'validation':validation,'diff':service.diff(candidate['id']),
            'hypothesis':'Preserve explicit in/out intent while moving it onto the feature type refinement supported by the existing HAMR instantiator',
            'engineering_accepted':False,'promotion':'NOT_REQUESTED'}
        destination=repo/'reports/build/isolette-migration-evidence';destination.mkdir(exist_ok=True)
        for file in (root/'state/objects').glob('*.json'):shutil.copy2(file,destination/file.name)
        (repo/'reports/build/ksu-isolette-migration.json').write_text(json.dumps(report,indent=2)+'\n')
        print(validation['status'],json.dumps(validation['gates']),flush=True)
        assert validation['status']=='CHECKED_PROVISIONAL',validation
    finally:c.close()


if __name__=='__main__':main()
