"""Actual KSU-generated system VCs in the reused pinned Verus worker; no model call."""
from pathlib import Path
import json,shutil,subprocess,time,hashlib
root=Path.cwd();out=root/'reports/demo/tool-upgrade/system-property-verus.json';source=json.loads((root/'reports/demo/tool-upgrade/system-property-codegen.json').read_text())['run'];src=next((root/'.scp-workbench/app/runs'/source['id']).glob('hamr_codegen-*/microkit'));work=root/'.scp-workbench/upgrade-system-property-proof'
if not work.exists():shutil.copytree(src,work)
image='jasonbelt/microkit_provers@sha256:bab407fd7f4aac24d7bee1234cd6bab9b6a29df380c2f0491af8e3ed1888a405'
report={'source_run_id':source['id'],'worker_image':image,'scope':'Actual generated system-composition VCs for official KSU fixture only; no Isolette behavioral or physical timing acceptance','model_calls':0,'checks':[],'source_rs_sha256':{p.relative_to(work).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*.rs')}}
container='scp-system-proof-'+str(int(time.time()))
base=['docker','run','--name',container,'--rm','--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--group-add','100','--mount','type=bind,src='+str(work)+',dst=/work','--mount','type=bind,src='+str(root/'.scp-workbench/ksu-container-validation/cargo')+',dst=/cache','-e','CARGO_HOME=/cache','-e','RUSTUP_HOME=/home/microkit/.rustup','-e','RUSTUP_TOOLCHAIN=1.92.0','-e','CARGO_NET_OFFLINE=true','-e','RUSTC_BOOTSTRAP=1','-e','PATH=/home/microkit/.cargo/bin:/home/microkit/provers/verus:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--entrypoint','/bin/sh',image,'-c']
for command in ['rustc --version && verus --version','make -C /work/crates/sys_nominal_proof all']:
 start=time.monotonic()
 try:
  p=subprocess.run(base+[command],capture_output=True,text=True,timeout=240);r={'command':base+[command],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 except subprocess.TimeoutExpired as e:
  subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=20)
  def text(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
  r={'command':base+[command],'exit_code':None,'status':'TIMEOUT','stdout':text(e.stdout),'stderr':text(e.stderr)}
 r['elapsed_seconds']=time.monotonic()-start;report['checks'].append(r);out.write_text(json.dumps(report,indent=2)+'\n');print(command,r['exit_code'],r['stdout'][-1400:],r['stderr'][-1400:],flush=True)
# Negative control: a separate crate copy, with one unconditional VC changed
# from true to false. The successful generated source remains unchanged.
negative=root/'.scp-workbench/upgrade-system-property-negative'
if not negative.exists():shutil.copytree(work,negative,ignore=shutil.ignore_patterns('target'))
probe=negative/'crates/sys_nominal_proof/src/gen_range_sanity/vc_sequential.rs'
original=probe.read_text();needle='true /* no assertions at out-places */'
assert needle in original
probe.write_text(original.replace(needle,'false /* deliberate negative control */',1))
args=[a.replace('src='+str(work)+',','src='+str(negative)+',') for a in base]
start=time.monotonic()
try:
 p=subprocess.run(args+['make -C /work/crates/sys_nominal_proof all'],capture_output=True,text=True,timeout=240)
 control={'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':time.monotonic()-start,
          'source_path':str(probe),'source_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),
          'expected':'Verus proof failure for deliberately false unconditional obligation',
          'expected_failure_observed':p.returncode!=0 and 'postcondition not satisfied' in (p.stdout+p.stderr)}
except subprocess.TimeoutExpired as e:
 subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=20)
 control={'exit_code':None,'status':'TIMEOUT','expected_failure_observed':False}
report['negative_control']=control;print('negative control',control.get('exit_code'),control['expected_failure_observed'],flush=True)
report['source_rs_preserved']=all(hashlib.sha256((work/p).read_bytes()).hexdigest()==sha for p,sha in report['source_rs_sha256'].items());report['whole_system_acceptance']=False;out.write_text(json.dumps(report,indent=2)+'\n')
