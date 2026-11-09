"""Actual HAMR component Verus/GUMBOX checks, bounded by existing campaign time."""
from pathlib import Path
import json,shutil,subprocess,time,hashlib,argparse
from inspecta_scp.controller import Controller
from inspecta_scp.campaign import Campaign
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='baseline');parser.add_argument('--components',nargs='*');args=parser.parse_args()
root=Path.cwd();out=root/'reports/demo/isolette-rust'/('verification-'+args.revision+'.json');model=json.loads((root/'reports/demo/isolette-rust/integer-clock-checks.json').read_text())['run'];src=next((root/'.scp-workbench/app/runs'/model['id']).glob('hamr_codegen-*/microkit'));work=root/'.scp-workbench/isolette-rust'/('rust-'+args.revision)
if not work.exists():shutil.copytree(src,work)
worker='jasonbelt/microkit_provers@sha256:bab407fd7f4aac24d7bee1234cd6bab9b6a29df380c2f0491af8e3ed1888a405'
report={'source_run_id':model['id'],'source_model_project':model['config']['project'],'worker_image':worker,'scope':'Actual component implementation checks of isolated integer-clock candidate; no physical timing, system acceptance or golden-scope approval. GUMBOX tests are component contract tests.','model_calls':0,'checks':[],'source_rs_sha256':{p.relative_to(work).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*.rs')}}
crates=[p.parent.parent.parent.name for p in work.glob('crates/*/src/component/*_app.rs')];crates=sorted(crates,key=lambda n:(not n.startswith('thermostat_rt_'),n))
if args.components:crates=[n for n in crates if n in args.components]
c=Controller(root/'.scp-workbench/app');campaign=Campaign(c.store)
try:
 for crate in crates:
  for kind,command in [('verus','make -C /work/crates/'+crate+' verus'),('gumbo_tests','cargo test --offline --manifest-path /work/crates/'+crate+'/Cargo.toml -- --nocapture')]:
   remaining=campaign.status('3f16ff4ef866d414cedb448a3ade2dfc4c5b5807162e6aea7522abc218fb49d8')['remaining_seconds']
   if remaining<80:
    report['stopped']='Authorized wall-clock reserve reached';break
   name='scp-isolette-'+str(int(time.time()*1000))
   base=['docker','run','--name',name,'--rm','--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--group-add','100','--mount','type=bind,src='+str(work)+',dst=/work','--mount','type=bind,src='+str(root/'.scp-workbench/ksu-container-validation/cargo')+',dst=/cache','-e','CARGO_HOME=/cache','-e','RUSTUP_HOME=/home/microkit/.rustup','-e','RUSTUP_TOOLCHAIN=1.92.0','-e','CARGO_NET_OFFLINE=true','-e','RUSTC_BOOTSTRAP=1','-e','PATH=/home/microkit/.cargo/bin:/home/microkit/provers/verus:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--entrypoint','/bin/sh',worker,'-c',command]
   start=time.monotonic()
   try:
    p=subprocess.run(base,capture_output=True,text=True,timeout=min(120,remaining-60));check={'crate':crate,'kind':kind,'command':base,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
   except subprocess.TimeoutExpired as e:
    subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
    def txt(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
    check={'crate':crate,'kind':kind,'command':base,'exit_code':None,'status':'TIMEOUT','stdout':txt(e.stdout),'stderr':txt(e.stderr)}
   check['elapsed_seconds']=time.monotonic()-start;report['checks'].append(check);out.write_text(json.dumps(report,indent=2)+'\n');print(crate,kind,check['exit_code'],flush=True)
  if report.get('stopped'):break
 report['source_rs_preserved']=all(hashlib.sha256((work/p).read_bytes()).hexdigest()==h for p,h in report['source_rs_sha256'].items());report['whole_system_acceptance']=False;out.write_text(json.dumps(report,indent=2)+'\n')
finally:c.close()
