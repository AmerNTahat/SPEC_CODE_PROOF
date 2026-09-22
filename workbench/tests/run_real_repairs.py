"""Real isolated repair checks reusing a completed disposable structural test workspace."""
import hashlib
import json
from pathlib import Path
import shutil
from inspecta_scp.controller import Controller
from inspecta_scp.repairs import Repairs


def main():
    repo=Path.cwd();structural=json.loads((repo/'reports/build/real-structure-integration.json').read_text())
    project=repo/structural['source_workspace'];state=project.parent/'state'
    profile_path=repo/'workbench/profiles/producer-consumer.check.json'
    profile=json.loads(profile_path.read_text())
    policy=next(p for p in structural['policies'] if p['mode']=='equivalence')
    profile.update(project=str(project),required_gates=['architecture'],architecture_policy=policy['id'],repair_allowed_files=[profile['model_file']])
    profile['budget']['wall_seconds']=240
    source=project/profile['model_file'];original=source.read_text()
    damaged=original.replace('connection pc : PortConnection connect prod.output to cons.input;','')
    c=Controller(state);repairs=Repairs(c)
    try:
        run=c.create(profile,base_dir=profile_path.parent)
        def patch(before,after):return {profile['model_file']:{'expected_sha256':hashlib.sha256(before.encode()).hexdigest(),'text':after}}
        failed=repairs.stage(run['id'],'missing-connection-test',patch(original,damaged))
        failure=repairs.validate(failed['id']);assert failure['status']=='FAILED',failure
        print('Real missing-connection repair rejected; original retained',flush=True)
        corrected=repairs.stage(run['id'],'missing-connection-test',patch(damaged,original),failed['id'])
        success=repairs.validate(corrected['id']);assert success['status']=='CHECKED_PROVISIONAL',success
        after=c.status(run['id'])
        assert after['deadline']==run['deadline'] and after['used_tokens']==run['used_tokens']
        assert after['result']==run['result'] and source.read_text()==original
        assert success['engineering_accepted'] is False
        print('Corrected child revision checked provisionally; original result/deadline preserved',flush=True)
        destination=repo/'reports/build/structural-evidence'
        for file in (state/'objects').glob('*.json'):shutil.copy2(file,destination/file.name)
        report={'status':'PASS','scope':'Real isolated HAMR provisional repair tests; no source promotion or live model demonstration',
            'model_calls':0,'run_id':run['id'],'deadline_before':run['deadline'],'deadline_after':after['deadline'],
            'source_files_modified':0,'failed_validation':failure,'corrected_validation':success,
            'events':c.store.events(run['id']),'candidates':[failed,corrected],
            'objects_directory':'reports/build/structural-evidence'}
        (repo/'reports/build/real-repair-integration.json').write_text(json.dumps(report,indent=2)+'\n')
    finally:c.close()


if __name__=='__main__':main()
