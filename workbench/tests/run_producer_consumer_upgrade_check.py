from pathlib import Path
import json,hashlib,shutil
from inspecta_scp.controller import Controller
root=Path.cwd();c=Controller(root/'.scp-workbench/app');prior=c.status('7643a50c7bdc4609a2a1557a76e25fb6');config=dict(prior['config']);config.pop('resolved_operation',None);home=root/'.scp-workbench/tools/sireum-4.20260810.80aad0c2/Sireum';project=root/'.scp-workbench/upgrade-compatibility/producer-consumer-120ms';project.mkdir(parents=True,exist_ok=True)
for rel in config['input_files']:
 target=project/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'.scp-workbench/app/runs'/prior['id']/'candidate'/rel,target)
config.update(integration_solver='cvc5',project=str(project),sireum=str(home/'bin/sireum'),sireum_sha256=hashlib.sha256((home/'bin/sireum').read_bytes()).hexdigest(),required_gates=['parse_type','architecture_capture','hamr_codegen','integration_constraints'],hamr_platform='Microkit',budget={'wall_seconds':300})
run=c.create(config);run=c.execute(run['id']);Path('reports/demo/tool-upgrade/producer-consumer-compatibility.json').write_text(json.dumps({'prior_source_run_id':prior['id'],'scope':'New-tool compatibility for previously approved120ms allocation; no new requirement or implementation change','run':run,'model_calls':0},indent=2)+'\n');print(run['id'],run['state']);print([(g['gate'],g['status'],g.get('reason')) for g in run.get('result',{}).get('gates',[])]);c.close()
