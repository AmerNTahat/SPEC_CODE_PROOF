"""Replay the recorded supervised Isolette wrapper experiment; requires its local run ledger.
No model calls, original/golden edits or independent transfer claims.
"""
from pathlib import Path
import re,json,shutil,time,hashlib,difflib
from inspecta_scp.controller import Controller
from inspecta_scp.campaign import Campaign
from inspecta_scp.graph_equivalence import compare_architectures
from inspecta_scp.structural_patterns import structural_patterns
root=Path.cwd();c=Controller(root/'.scp-workbench/app');campaign='3f16ff4ef866d414cedb448a3ade2dfc4c5b5807162e6aea7522abc218fb49d8'
old=c.store.read_record('development_result','46099f1c2bc9e5ca7a4592b46d7333685886cad1e724f4fd456201994e23ab17');run=c.status(old['generated_run_id']);src=Path(run['config']['project']);destination=root/'.scp-workbench/structural-experiments'/('isolette-'+str(int(time.time())));shutil.copytree(src,destination)
p=destination/'Regulate.sysml';original=p.read_text();text=original
thread_names=['Manage_Regulator_Interface_i','Manage_Regulator_Mode_i','Manage_Heat_Source_i','Detect_Regulator_Failure_i'];wrappers=[]
# Extract only the existing generated port declarations; do not copy golden behavior.
for domain,name in enumerate(thread_names,3):
 pattern=r'part def '+re.escape(name)+r' :> AADL::Thread \{'
 start=re.search(pattern,text).end();tail=text[start:];stop=tail.index('language "GUMBO"');header=tail[:stop]
 ports=list(re.finditer(r'port\s+(\w+)\s*:\s*AADL::DataPort\s*\{\s*(in|out)\s*:>>\s*type\s*:\s*([^;]+);\s*\}',header))
 assert len(ports)=={3:9,4:4,5:5,6:1}[domain],(name,len(ports))
 body=['    part def '+name+'_Process :> AADL::Process {','        part worker : '+name+';','        attribute Domain : CASE_Scheduling::Domain = '+str(domain)+';']
 for m in ports:
  port,direction,payload=m.groups();body.append('        '+m.group())
  endpoints=(port,'worker.'+port) if direction=='in' else ('worker.'+port,port)
  body.append('        connection forward_'+port+' : AADL::FeatureConnection connect '+endpoints[0]+' to '+endpoints[1]+';')
 body.append('    }');wrappers.append('\n'.join(body))
 properties='\n        // Human-approved supervised architecture profile; FAA timing remains an open obligation.\n        attribute :>> Dispatch_Protocol = AADL_Project::Supported_Dispatch_Protocols::Periodic;\n        attribute :>> Period = 1000 [HAMR_Time_Units::ms];\n        attribute Domain : CASE_Scheduling::Domain = '+str(domain)+';\n'
 text=text[:start]+properties+text[start:]
 text=re.sub(r'(part\s+\w+\s*:\s*)'+re.escape(name)+r'\s*;',lambda m:m.group(1)+name+'_Process;',text)
text=text.replace('part def Regulate_Temperature_i :> AADL::Process','part def Regulate_Temperature_i :> AADL::System')
# Preserve original behavioral and obligation text as historical commentary, with explicit supersession of old design diagnosis.
text=text.replace('requirement Scheduling_Integration {','requirement Scheduling_Integration {\n            doc /* HUMAN-APPROVED REVISION: explicit reference-derived Periodic1000ms/domains3..6 supersede the old missing-deployment diagnosis below. This does not meet or relax FAA response deadlines; timing remains unresolved. */')
text=text.replace('requirement Architecture_Review {','requirement Architecture_Review {\n            doc /* HUMAN-APPROVED REVISION: the former four-thread Process is now a System with four single-thread Process wrappers. The following diagnostic is retained as historical context, not the current architecture claim. */')
text=text.replace('    alias Regulate_i for Regulate_Temperature_i;','\n\n'.join(wrappers)+'\n\n    alias Regulate_i for Regulate_Temperature_i;')
assert len(re.findall(r'language "GUMBO" /\*\{[\s\S]*?\}\*/',original))==4
assert re.findall(r'language "GUMBO" /\*\{[\s\S]*?\}\*/',text)==re.findall(r'language "GUMBO" /\*\{[\s\S]*?\}\*/',original)
p.write_text(text);patch=''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='generated-before/Regulate.sysml',tofile='supervised-structural-experiment/Regulate.sysml'));(root/'reports/demo/isolette-supervised-structure.patch').write_text(patch)
remaining=Campaign(c.store).status(campaign)['remaining_seconds'];config={**run['config'],'project':str(destination),'required_gates':['parse_type','architecture_capture'],'budget':{**run['config']['budget'],'wall_seconds':min(240,max(1,int(remaining-20)))}};config.pop('resolved_operation',None)
r=c.create(config);report={'scope':'Offline supervised mechanical structural repair; not fresh model generation or independent rule validation','user_authorization':'One Thread per Process; follow approved example deployment abstraction','parent_generated_run':run['id'],'reference_run':old['reference_run_id'],'run_id':r['id'],'project':str(destination),'model_calls':0,'gumbo_contracts_byte_identical':True,'whole_system_acceptance':False};out=root/'reports/demo/ISOLETTE_SUPERVISED_STRUCTURAL_EXPERIMENT.json';out.write_text(json.dumps(report,indent=2)+'\n');print('Run',r['id'],flush=True)
checked=c.execute(r['id']);report['state']=checked['state'];report['gates']=checked.get('result');gate=next((g for g in (checked.get('result') or {}).get('gates',[]) if g['gate']=='architecture_capture' and g.get('snapshot_id') and g['status']=='PASS'),None)
if gate:
 ref=c.status(old['reference_run_id']);rg=next(g for g in ref['result']['gates'] if g.get('snapshot_id'))
 values=[c.store.load_object(c.store.read_record('architecture_snapshot',g['snapshot_id'])['normalized']) for g in [rg,gate]]
 report['directed_graph']=compare_architectures(*values);report['structural_profile']=structural_patterns(values[1])
 report['reference_evidence_current']=bool(ref.get('evidence_current_for_source') and ref.get('policy_current'))
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['structural_profile','directed_graph']},indent=2),flush=True);c.close()
