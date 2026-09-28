from pathlib import Path
import json,hashlib,time,shutil
from inspecta_scp.controller import Controller
root=Path.cwd();c=Controller(root/'.scp-workbench/app');new=root/'.scp-workbench/tools/sireum-4.20260810.80aad0c2/Sireum/bin/sireum';base=json.loads((root/'reports/demo/isolette-migrated-reference.profile.json').read_text());report={'tool':str(new),'scope':'Read-only compatibility checks of historical generated and reference files under a new tool identity; no model repair, source promotion or behavioral acceptance','checks':[],'model_calls':0}
for label,project in [('fresh_generated',root/'.scp-workbench/app/runs/7d406413c64a4219b7674ed71411eaee/candidate'),('approved_reference',Path(base['project']))]:
 folder=root/'.scp-workbench/upgrade-compatibility'/label;folder.mkdir(parents=True,exist_ok=True)
 for rel in base['input_files']:
  target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(project/rel,target)
 config={**base,'project':str(folder),'sireum':str(new),'sireum_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'required_gates':['parse_type','architecture_capture'],'task_operation':'verify-only','budget':{'wall_seconds':180}}
 run=c.create(config);run=c.execute(run['id']);report['checks'].append({'label':label,'run_id':run['id'],'state':run['state'],'result':run.get('result')});(root/'reports/demo/tool-upgrade/isolette-compatibility.json').write_text(json.dumps(report,indent=2)+'\n');print(label,run['state'],[(x['gate'],x['status'],x.get('reason')) for x in run.get('result',{}).get('gates',[])],flush=True)
c.close()
