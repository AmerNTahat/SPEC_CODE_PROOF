"""Actual sandboxed HAMR structural tests on disposable copies; no paid demonstration."""
import copy
import json
from pathlib import Path
import shutil
import uuid
from inspecta_scp.approvals import Approvals
from inspecta_scp.architecture import Architecture, differences
from inspecta_scp.config import resolve
from inspecta_scp.controller import Controller


def main():
    repo=Path.cwd()
    profile_path=repo/'workbench/profiles/producer-consumer.check.json'
    profile=json.loads(profile_path.read_text())
    config=resolve(profile,base_dir=profile_path.parent)['config']
    root=repo/'.scp-workbench/structure-tests'/uuid.uuid4().hex
    project=root/'project';project.mkdir(parents=True)
    for rel in config['input_files']:
        dest=project/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(Path(config['project'])/rel,dest)
    profile.update(project=str(project),required_gates=['architecture_capture'])
    profile['budget']['wall_seconds']=240
    source=project/profile['model_file'];original=source.read_text()
    controller=Controller(root/'state');architecture=Architecture(controller);approvals=Approvals(controller.store)
    results=[]
    def run(name,expected):
        started=controller.create(profile,base_dir=profile_path.parent)
        finished=controller.execute(started['id'])
        result={'case':name,'run':finished,'events':controller.store.events(started['id'])}
        results.append(result)
        print(name+': '+finished['state'],flush=True)
        assert finished['state']==expected,result
        return finished['result']['gates'][0]
    def approve(policy):
        request=architecture.request_review(policy['id'])
        approvals.decide(request['id'],request['subject_digest'],'APPROVED','Disposable structural integration test only')
    try:
        baseline_gate=run('real_capture','CHECKED')
        policy=architecture.propose(baseline_gate['snapshot_id']);approve(policy)
        profile.update(architecture_policy=policy['id'],required_gates=['architecture'])
        run('unchanged_real_architecture','CHECKED')
        source.write_text(original.replace('connection pc : PortConnection connect prod.output to cons.input;', ''))
        run('missing_connection','FAILED')
        source.write_text(original.replace('output.payload <= 90', 'output.payload < 90'))
        run('changed_contract_boundary','FAILED')
        # Consistent display/instance rename requires exact reviewed declaration
        # and resolved AIR deltas; the unchanged baseline must reject it first.
        source.write_text(original.replace('part prod: Prod_Process;', 'part producer: Prod_Process;')
            .replace('connect prod.output to cons.input', 'connect producer.output to cons.input')
            .replace('allocate prod to proc', 'allocate producer to proc'))
        renamed=run('unapproved_consistent_rename','FAILED')
        before=controller.store.load_object(controller.store.read_record('architecture_snapshot',baseline_gate['snapshot_id'])['normalized'])
        after=controller.store.load_object(controller.store.read_record('architecture_snapshot',renamed['snapshot_id'])['normalized'])
        delta=differences(before,after)
        assert delta and all('before' in change and 'after' in change for change in delta),delta
        changes=[{**change,'rationale':'Test-only exact consistent producer instance rename'} for change in delta]
        rename_policy=architecture.propose(baseline_gate['snapshot_id'],changes);approve(rename_policy)
        profile['architecture_policy']=rename_policy['id']
        run('explicitly_reviewed_consistent_rename','CHECKED')
        source.write_text(source.read_text().replace('output.payload <= 90', 'output.payload < 90'))
        run('extra_contract_change_not_covered_by_rename','FAILED')
        source.write_text(original)
        destination=repo/'reports/build/structural-evidence'
        destination.mkdir(parents=True,exist_ok=True)
        for file in (root/'state/objects').glob('*.json'):
            shutil.copy2(file,destination/file.name)
        report={'status':'PASS','scope':'Real HAMR captures/comparisons on disposable source copies; not proof or live learning/demo',
                'model_calls':0,'source_workspace':str(project.relative_to(repo)),
                'cases':results,'objects_directory':str(destination.relative_to(repo)),
                'policies':controller.store.records('architecture_policy'),
                'snapshots':controller.store.records('architecture_snapshot')}
        (repo/'reports/build/real-structure-integration.json').write_text(json.dumps(report,indent=2)+'\n')
    finally:controller.close()


if __name__=='__main__':main()
