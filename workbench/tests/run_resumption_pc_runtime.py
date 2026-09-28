"""Current Producer/Consumer build + bounded QEMU log observation; no payload proof."""
from pathlib import Path
import json,subprocess,time,hashlib
from inspecta_scp.controller import Controller
from inspecta_scp.campaign import Campaign
root=Path.cwd();work=root/'.scp-workbench/ksu-container-validation/producer-consumer-resumption';out=root/'reports/demo/isolette-rust/producer-consumer-resumption-runtime.json'
image='jasonbelt/microkit_provers@sha256:bab407fd7f4aac24d7bee1234cd6bab9b6a29df380c2f0491af8e3ed1888a405';name='scp-pc-resumption-'+str(int(time.time()))
c=Controller(root/'.scp-workbench/app');campaign=Campaign(c.store);key='3f16ff4ef866d414cedb448a3ade2dfc4c5b5807162e6aea7522abc218fb49d8'
report={'workspace':str(work),'image':image,'sdk':'1.4.1','model_calls':0,'checks':[],
 'source_rs_sha256':{p.relative_to(work).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*.rs') if 'target' not in p.parts},
 'scope':'Real build and 20-second wall-clock QEMU console observation of the current generated candidate. No R2U2 instrumentation, no simulated-time coverage, no payload/physical timing acceptance.'}
def run(args,limit):
 remaining=campaign.status(key)['remaining_seconds'];timeout=min(limit,max(1,remaining-30));start=time.monotonic()
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);record={'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 except subprocess.TimeoutExpired as e:
  def text(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
  record={'command':args,'exit_code':None,'status':'TIMEOUT','stdout':text(e.stdout),'stderr':text(e.stderr)}
 record['elapsed_seconds']=time.monotonic()-start;report['checks'].append(record);out.write_text(json.dumps(report,indent=2)+'\n');print(record.get('exit_code'),args[-3:],flush=True);return record
args=['docker','run','-d','--name',name,'--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--group-add','100','--mount',f'type=bind,src={work},dst=/work','--mount',f'type=bind,src={root/".scp-workbench/ksu-container-validation/cargo"},dst=/cache','-e','CARGO_HOME=/cache','-e','RUSTUP_HOME=/home/microkit/.rustup','-e','RUSTUP_TOOLCHAIN=1.92.0','-e','RUSTC_BOOTSTRAP=1','-e','CARGO_NET_OFFLINE=true','-e','MICROKIT_SDK=/home/microkit/provers/microkit-sdk-1.4.1','-e','MICROKIT_BOARD=qemu_virt_aarch64','-e','PATH=/home/microkit/.cargo/bin:/home/microkit/provers/verus:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--entrypoint','/bin/sleep',image,'500']
try:
 if run(args,30)['exit_code']!=0:raise SystemExit('Container startup failed')
 build=run(['docker','exec',name,'make','-C','/work','-j2'],240)
 if build['exit_code']==0:
  observation=run(['docker','exec',name,'make','-C','/work','qemu'],20)
  output=observation.get('stdout','')+'\n'+observation.get('stderr','')
  anomalies=[line for line in output.splitlines() if any(x in line.lower() for x in ['panic','fault','invalid channel','error:'])]
  report['observation']={'clock':'wall','requested_seconds':20,'elapsed_seconds':observation['elapsed_seconds'],
   'producer_compute_observed':'prod_prod' in output and 'compute entrypoint invoked' in output,
   'consumer_compute_observed':'cons_cons' in output and 'compute entrypoint invoked' in output,
   'anomalies':anomalies,'monitor':'Console diagnostic scan only; no R2U2 temporal property monitor',
   'status':'BOUNDED_LOG_OBSERVATION_NO_MATCHING_ANOMALY' if observation.get('status')=='TIMEOUT' and not anomalies else 'REVIEW_REQUIRED'}
finally:
 run(['docker','rm','-f',name],20)
 report['source_rs_preserved']=all(hashlib.sha256((work/p).read_bytes()).hexdigest()==sha for p,sha in report['source_rs_sha256'].items());out.write_text(json.dumps(report,indent=2)+'\n');c.close()
