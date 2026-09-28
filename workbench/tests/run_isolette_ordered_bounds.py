"""Human-approved strict ordering repair, isolated from original golden/source."""
from pathlib import Path
import json,shutil,difflib,time
from inspecta_scp.controller import Controller
root=Path.cwd();out=root/'reports/demo/isolette-rust';old=root/'.scp-workbench/isolette-rust/integer-clock';target=root/'.scp-workbench/isolette-rust/ordered-bounds'
if target.exists():raise SystemExit('Preserve existing experiment')
shutil.copytree(old,target)
p=target/'Regulate.sysml';before=p.read_text();needle='''            compute
                guarantee REQ_MHS_1:'''
assert before.count(needle)==1
after=before.replace(needle,'''            compute
                // Human-approved golden-defect repair: FAA EA-OI-6 ordering rationale.
                // Strict ordering is a local premise; producer/system discharge remains open.
                assume ORDERED_DESIRED_BOUNDS:
                    Lower_Desired_Temp.degrees < Upper_Desired_Temp.degrees;
                guarantee REQ_MHS_1:''')
p.write_text(after);(out/'ordered-bounds-ACCEPTED.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='before/Regulate.sysml',tofile='human-approved/Regulate.sysml')))
config=json.loads((out/'integer-clock-checks.json').read_text())['run']['config'];config.pop('resolved_operation',None);config['project']=str(target)
c=Controller(root/'.scp-workbench/app');start=time.monotonic()
try:
 run=c.execute(c.create(config)['id']);(out/'ordered-bounds-checks.json').write_text(json.dumps({'run':run,'elapsed_seconds':time.monotonic()-start,'model_calls':0},indent=2)+'\n');print(run['id'],run['state'],[(g['gate'],g['status']) for g in run.get('result',{}).get('gates',[])])
finally:c.close()
