import json,subprocess,time,shutil,os
from pathlib import Path
root=Path.cwd();out=root/'reports/build/ksu-container-clean-sdk141-runtime.json';work=root/'.scp-workbench/ksu-container-validation';work.mkdir(exist_ok=True)
image='jasonbelt/microkit_provers@sha256:bab407fd7f4aac24d7bee1234cd6bab9b6a29df380c2f0491af8e3ed1888a405'
name='scp-validation-'+str(int(time.time()));report={'image':image,'container':name,'scope':'Reused KSU runtime; actual generated Rust checks, no whole-system acceptance','model_calls':0,'checks':[]}
def run(args,seconds=180):
 deadline=json.loads((root/'reports/demo/CAMPAIGN_STATUS.json').read_text())['deadline'];seconds=min(seconds,max(1,deadline-time.time()-20));start=time.monotonic()
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=seconds);r={'command':args,'exit_code':p.returncode,'stdout':p.stdout[-40000:],'stderr':p.stderr[-40000:]}
 except subprocess.TimeoutExpired as e:
  def txt(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
  r={'command':args,'exit_code':None,'status':'TIMEOUT','stdout':txt(e.stdout)[-40000:],'stderr':txt(e.stderr)[-40000:]}
 r['elapsed_seconds']=time.monotonic()-start;report['checks'].append(r);out.write_text(json.dumps(report,indent=2)+'\n');print(args[-3:],r['exit_code'],flush=True);return r
src=next((root/'.scp-workbench/app/runs/7643a50c7bdc4609a2a1557a76e25fb6').glob('hamr_codegen-*/microkit'))
if not (work/'generated').exists():shutil.copytree(src,work/'generated')
positive='use vstd::prelude::*;\nverus! { fn plus_one(x: u64) -> (r: u64) requires x < u64::MAX, ensures r == x + 1, { x + 1 } }\nfn main() {}\n'
(work/'positive.rs').write_text(positive);(work/'negative.rs').write_text(positive.replace('{ x + 1 }','{ x }'))
args=['docker','run','-d','--name',name,'--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--group-add','100','--mount','type=bind,src='+str(work)+',dst=/work','-e','CARGO_HOME=/work/cargo','-e','RUSTUP_HOME=/home/microkit/.rustup','-e','RUSTUP_TOOLCHAIN=1.92.0','-e','RUSTC_BOOTSTRAP=1','-e','PATH=/home/microkit/.cargo/bin:/home/microkit/provers/verus:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--entrypoint','/bin/sleep',image,'1500']
if run(args,30)['exit_code']!=0:raise SystemExit(1)
try:
 build=work/'generated/build'
 if build.exists():build.rename(work/('mixed-sdk-build-'+str(int(time.time()))))
 built=run(['docker','exec','-e','CARGO_NET_OFFLINE=true','-e','MICROKIT_SDK=/home/microkit/provers/microkit-sdk-1.4.1',name,'make','-C','/work/generated','-j2'],180)
 if built['exit_code']!=0:raise SystemExit('Clean image build failed')
 run(['docker','exec','-e','CARGO_NET_OFFLINE=true','-e','MICROKIT_SDK=/home/microkit/provers/microkit-sdk-1.4.1',name,'make','-C','/work/generated','qemu'],20)

finally:
 run(['docker','rm','-f',name],30)
report['whole_system_acceptance']=False;out.write_text(json.dumps(report,indent=2)+'\n')
