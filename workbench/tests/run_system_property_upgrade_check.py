"""Real official KSU system-property fixture under the isolated new tool; no model call."""
from pathlib import Path
import json,hashlib
from inspecta_scp.controller import Controller
root=Path.cwd();home=root/'.scp-workbench/tools/sireum-4.20260810.80aad0c2/Sireum';project=root/'.scp-workbench/upgrade-system-property-example/sysmlv2';c=Controller(root/'.scp-workbench/app')
config={'project':str(project),'model_file':'struct-split/SysPropStructSplit.sysml','input_files':sorted(p.relative_to(project).as_posix() for p in project.rglob('*.sysml')),'sireum':str(home/'bin/sireum'),'sireum_sha256':hashlib.sha256((home/'bin/sireum').read_bytes()).hexdigest(),'hamr_platform':'Microkit','task_operation':'verify-only','required_gates':['parse_type','hamr_codegen'],'budget':{'wall_seconds':150}}
run=c.create(config);run=c.execute(run['id']);out={'scope':'Official KSU capability fixture, not a trained-rule benchmark or Isolette acceptance','model_calls':0,'run':run};(root/'reports/demo/tool-upgrade/system-property-codegen.json').write_text(json.dumps(out,indent=2)+'\n')
print(run['id'],run['state'])
for g in run.get('result',{}).get('gates',[]):
 print(g['gate'],g['status'],g.get('reason'))
 if g.get('evidence'):
  e=c.store.load_object(g['evidence']);print(e.get('stdout','')[-1800:],e.get('stderr','')[-1800:])
c.close()
