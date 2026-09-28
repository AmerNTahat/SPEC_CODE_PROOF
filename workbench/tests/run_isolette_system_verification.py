"""Execute generated Isolette composition VCs with the reused offline Verus worker."""
from pathlib import Path
import argparse,json,shutil,subprocess,time
from inspecta_scp.controller import Controller
from inspecta_scp.campaign import Campaign
from inspecta_scp.engineering_progress import implementation_manifest
p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--model-report',required=True);a=p.parse_args()
root=Path.cwd();out=root/'reports/demo/isolette-rust';model=json.loads((out/a.model_report).read_text())['run'];src=next((root/'.scp-workbench/app/runs'/model['id']).glob('hamr_codegen-*/microkit'));work=root/'.scp-workbench/isolette-rust'/('system-'+a.revision)
if not work.exists():shutil.copytree(src,work)
crates=sorted(work.glob('crates/sys_*_proof'));assert crates,'No generated system VCs: cannot claim a proof'
image='jasonbelt/microkit_provers@sha256:bab407fd7f4aac24d7bee1234cd6bab9b6a29df380c2f0491af8e3ed1888a405';c=Controller(root/'.scp-workbench/app');report={'workspace':str(work),'source_run_id':model['id'],'worker_image':image,'model_calls':0,'checks':[],'preparation':[],'scope':'Generated GUMBO composition VCs for the exact experimental Isolette model. Conditional on component contracts; not a physical timing or whole-system acceptance claim.'};dest=out/('system-verification-'+a.revision+'.json')
def run(command):
 remaining=Campaign(c.store).status('3f16ff4ef866d414cedb448a3ade2dfc4c5b5807162e6aea7522abc218fb49d8')['remaining_seconds'];assert remaining>90
 name='scp-sys-'+str(int(time.time()*1000));args=['docker','run','--name',name,'--rm','--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--group-add','100','--mount','type=bind,src='+str(work)+',dst=/work','--mount','type=bind,src='+str(root/'.scp-workbench/ksu-container-validation/cargo')+',dst=/cache','-e','CARGO_HOME=/cache','-e','RUSTUP_HOME=/home/microkit/.rustup','-e','RUSTUP_TOOLCHAIN=1.92.0','-e','CARGO_NET_OFFLINE=true','-e','RUSTC_BOOTSTRAP=1','-e','PATH=/home/microkit/.cargo/bin:/home/microkit/provers/verus:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--entrypoint','/bin/sh',image,'-c',command];start=time.monotonic()
 try:
  r=subprocess.run(args,capture_output=True,text=True,timeout=min(180,remaining-60));result={'command':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except subprocess.TimeoutExpired as e:
  subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
  def text(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
  result={'command':args,'exit_code':None,'status':'TIMEOUT','stdout':text(e.stdout),'stderr':text(e.stderr)}
 return {**result,'elapsed_seconds':time.monotonic()-start}
try:
 for crate in crates:
  r=run('cargo generate-lockfile --offline --manifest-path /work/crates/'+crate.name+'/Cargo.toml');report['preparation'].append(r);assert r['exit_code']==0,r['stderr'][-1500:]
 report['implementation_manifest']=implementation_manifest(work);dest.write_text(json.dumps(report,indent=2)+'\n')
 for crate in crates:
  check=run('make -C /work/crates/'+crate.name+' all');check['crate']=crate.name;report['checks'].append(check);dest.write_text(json.dumps(report,indent=2)+'\n');print(crate.name,check['exit_code'],check['stdout'][-500:],check['stderr'][-1200:],flush=True)
 report['complete']=True;report['source_preserved']=implementation_manifest(work)==report['implementation_manifest'];dest.write_text(json.dumps(report,indent=2)+'\n')
finally:c.close()
