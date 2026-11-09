import json,subprocess,time,shutil,os
from pathlib import Path
root=Path.cwd();out=root/'reports/build/ksu-container-engineering.json';work=root/'.scp-workbench/ksu-container-validation';work.mkdir(exist_ok=True)
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
 run(['docker','exec',name,'/bin/sh','-c','mkdir -p /work/cargo; cp -R /home/microkit/.cargo/registry /work/cargo/'],60)
 for command in [['rustc','--version'],['cargo','--version'],['verus','--version'],['verus','/work/positive.rs'],['verus','/work/negative.rs']]:run(['docker','exec',name]+command,60)
 for component in ['prod_prod','cons_cons']:
  manifest='/work/generated/crates/'+component+'/Cargo.toml'
  run(['docker','network','disconnect','none',name],20);run(['docker','network','connect','bridge',name],20)
  run(['docker','exec',name,'cargo','fetch','-Z','build-std=core,alloc,compiler_builtins','--target','aarch64-unknown-none','--manifest-path',manifest],100)
  run(['docker','network','disconnect','bridge',name],20);run(['docker','network','connect','none',name],20)
  run(['docker','exec','-e','CARGO_NET_OFFLINE=true',name,'make','-C','/work/generated/crates/'+component,'verus'],100)
 # The user-owned generated tests file calls a helper absent from the generated utility.
 # Replace that helper invocation with the same full i32 strategy; do not edit generator-owned utilities.
 p=work/'generated/crates/cons_cons/src/test/tests.rs';before=p.read_text()
 if 'generators::i32_strategy_default()' in before:
  import difflib
  after=before.replace('generators::i32_strategy_default()','proptest::prelude::any::<i32>()');p.write_text(after)
  (root/'reports/demo/consumer-test-helper-repair.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='before/tests.rs',tofile='after/tests.rs')))
 run(['docker','exec',name,'cargo','test','--offline','--manifest-path','/work/generated/crates/cons_cons/Cargo.toml'],100)
 run(['docker','exec','-e','CARGO_NET_OFFLINE=true','-e','MICROKIT_SDK=/home/microkit/provers/microkit-sdk-2.1.0',name,'make','-C','/work/generated','-j2'],100)

finally:
 run(['docker','rm','-f',name],30)
report['whole_system_acceptance']=False;out.write_text(json.dumps(report,indent=2)+'\n')
