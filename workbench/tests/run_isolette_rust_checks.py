"""Select the documented Rust backend in an isolated Isolette copy and check it."""
from pathlib import Path
import json,re,shutil,hashlib,time,difflib
from inspecta_scp.controller import Controller
root=Path.cwd();out=root/'reports/demo/isolette-rust';out.mkdir(exist_ok=True)
source=root/'.scp-workbench/upgrade-compatibility/fresh_generated';target=root/'.scp-workbench/isolette-rust/model'
config=json.loads((root/'workbench/profiles/isolette-upgraded.check.json').read_text());changes=[]
if target.exists():raise SystemExit('Preserve existing experiment; choose a new revision rather than overwrite')
for name in config['input_files']:
 src=source/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 if len(Path(name).parts)>1:continue
 before=src.read_text();after,n=re.subn(r'(part def\s+\w+\s*:>\s*)(?:AADL::)?Thread\s*\{',r'\1HAMR_AADL::Thread {\n        attribute :>> Implementation_Language = HAMR::Implementation_Languages::Rust;',before)
 if n:
  dst.write_text(after);changes.append({'file':name,'thread_definitions':n,'before_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
  with (out/'rust-backend.patch').open('a') as f:f.writelines(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/'+name,tofile='isolated/'+name))
(out/'selection.json').write_text(json.dumps({'changes':changes,'scope':'Backend selection only: HAMR_AADL Thread and Rust Implementation_Language. GUMBO contracts preserved; source/golden unchanged.','model_calls':0},indent=2)+'\n')
config.update(project=str(target),hamr_platform='Microkit',integration_solver='cvc5',required_gates=['parse_type','architecture_capture','integration_constraints','hamr_codegen'],budget={'wall_seconds':300})
c=Controller(root/'.scp-workbench/app');start=time.monotonic()
try:
 run=c.create(config);run=c.execute(run['id']);(out/'checks.json').write_text(json.dumps({'run':run,'elapsed_seconds':time.monotonic()-start,'model_calls':0},indent=2)+'\n');print(run['id'],run['state']);print([(g['gate'],g['status'],g.get('reason')) for g in run.get('result',{}).get('gates',[])])
finally:c.close()
