"""Candidate Rust compatibility repair; sampled-ms abstraction requires review."""
from pathlib import Path
import json,shutil,difflib,hashlib,time
from inspecta_scp.controller import Controller
root=Path.cwd();out=root/'reports/demo/isolette-rust';old=root/'.scp-workbench/isolette-rust/model';target=root/'.scp-workbench/isolette-rust/integer-clock'
if target.exists():raise SystemExit('Preserve existing experiment')
shutil.copytree(old,target)
p=target/'Regulate.sysml';before=p.read_text();after=before.replace('Duration_INMODE : Base_Types::Float_64','Duration_INMODE : Base_Types::Integer_64').replace('Duration_INMODE == 0.0','Duration_INMODE == 0[s64]').replace('Duration_INMODE >= 0.0','Duration_INMODE >= 0[s64]').replace('In(Duration_INMODE) > 1.0','In(Duration_INMODE) > 1000[s64]').replace('In(Duration_INMODE) <= 1.0','In(Duration_INMODE) <= 1000[s64]').replace('Duration_INMODE denotes elapsed residence time in seconds.','Duration_INMODE denotes sampled elapsed residence time in integer milliseconds. This candidate requires reviewed clock abstraction, progress and overflow handling; it does not establish physical-time equivalence.')
p.write_text(after);(out/'integer-clock-candidate.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='rust-float/Regulate.sysml',tofile='candidate-integer-ms/Regulate.sysml')))
(out/'integer-clock-selection.json').write_text(json.dumps({'status':'CANDIDATE_NOT_ACCEPTED','before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'rationale':'Observed Rust codegen crash atFloat64 literal0.0. Integer milliseconds are an alternative sampled representation; preserving strict>1000 boundary does not prove clock progress, overflow safety or equivalence to arbitrary real-time semantics. No guard priority or requirement deletion.'},indent=2)+'\n')
config=json.loads((out/'checks.json').read_text())['run']['config'];config.pop('resolved_operation',None);config['project']=str(target)
c=Controller(root/'.scp-workbench/app');start=time.monotonic()
try:
 run=c.execute(c.create(config)['id']);(out/'integer-clock-checks.json').write_text(json.dumps({'run':run,'elapsed_seconds':time.monotonic()-start,'model_calls':0},indent=2)+'\n');print(run['id'],run['state']);print([(g['gate'],g['status'],g.get('reason')) for g in run.get('result',{}).get('gates',[])])
finally:c.close()
