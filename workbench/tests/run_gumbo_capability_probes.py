"""Pinned-tool syntax capability probes, not an Isolette repair or proof of correctness."""
from pathlib import Path
import json,shutil,time,hashlib,argparse
from inspecta_scp.controller import Controller
root=Path.cwd();profile=json.loads((root/'reports/demo/isolette-migrated-reference.profile.json').read_text());source=Path(profile['project']);base=root/'.scp-workbench/capability-probes'/str(int(time.time()));base.mkdir(parents=True);c=Controller(root/'.scp-workbench/app')
parser=argparse.ArgumentParser();parser.add_argument('--sireum',type=Path);parser.add_argument('--output',type=Path,default=root/'reports/demo/behavior-review/gumbo-capability-probes.json');args=parser.parse_args()
if args.sireum:
 profile.update(sireum=str(args.sireum.resolve()),sireum_sha256=hashlib.sha256(args.sireum.read_bytes()).hexdigest())
libs=[p for p in profile['input_files'] if p.startswith('sysml-aadl-libraries_1/')]
thread='''package Capability {
 private import AADL::*;
 part def Worker :> Thread {
  port elapsed_ms : DataPort { in :>> type : Base_Types::Integer_32; }
  port expired : DataPort { out :>> type : Base_Types::Boolean; }
  language "GUMBO" /*{
   state remembered_ms: Base_Types::Integer_32;
   initialize guarantee initial: remembered_ms == 0 [s32];
   compute
    guarantee timeout_condition: expired == (elapsed_ms > 1000 [s32]);
    guarantee remember: remembered_ms == elapsed_ms;
    guarantee old_value: In(remembered_ms) == In(remembered_ms);
    REPLACE_TEMPORAL
  }*/
 }
 part def WorkerProcess :> Process { part worker : Worker; }
 part def Root :> System {
  part process : WorkerProcess;
  REPLACE_SYSTEM
 }
}
'''
composition='''language "GUMBO" /*{
 composition nominal {
  components w = process.worker;
  ports expired = w.expired;
  schema { w }
  property BooleanOutput { after w : expired or not expired; }
 }
}*/'''
variants=[('state_elapsed_integer',thread.replace('REPLACE_TEMPORAL','').replace('REPLACE_SYSTEM','')),
 ('native_until_syntax',thread.replace('REPLACE_TEMPORAL','guarantee temporal: (not expired) until expired;').replace('REPLACE_SYSTEM','')),
 ('documented_system_composition',thread.replace('REPLACE_TEMPORAL','').replace('REPLACE_SYSTEM',composition))]
report={'scope':'Pinned Sireum parser/type checker probes only; passing syntax does not prove clock progress, contracts, system properties or deadlines','model_calls':0,'whole_system_acceptance':False,'checks':[],'sireum':profile['sireum'],'launcher_sha256':profile['sireum_sha256']}
for name,text in variants:
 folder=base/name;folder.mkdir()
 for rel in libs:
  target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,target)
 (folder/'Capability.sysml').write_text(text)
 config={**profile,'project':str(folder),'input_files':['Capability.sysml']+libs,'model_file':'Capability.sysml','required_gates':['parse_type'],'budget':{'wall_seconds':75},'task_operation':'verify-only'}
 run=c.create(config);start=time.monotonic();run=c.execute(run['id']);g=run['result']['gates'][0];e=c.store.load_object(g['evidence']) if g.get('evidence') else {}
 report['checks'].append({'name':name,'source':text,'run_id':run['id'],'status':g['status'],'reason':g.get('reason'),'stdout':e.get('stdout'),'stderr':e.get('stderr'),'elapsed_seconds':time.monotonic()-start})
 args.output.write_text(json.dumps(report,indent=2)+'\n');print(name,g['status'],flush=True)
c.close()
