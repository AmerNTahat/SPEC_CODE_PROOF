"""Real isolated Rust/Verus checks on saved generated artifacts; no acceptance claim."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/'.scp-workbench/tools'
RUST=TOOLS/'rust'
VERUS=TOOLS/'verus-0.2026.01.23.1650a05/verus-x86-linux'
OUT=ROOT/'reports/build'
ENV={'PATH':str(VERUS)+':'+str(RUST/'cargo/bin')+':/usr/bin:/bin','CARGO_HOME':str(RUST/'cargo'),
     'RUSTUP_HOME':str(RUST/'rustup'),'RUSTUP_TOOLCHAIN':'1.92.0','LANG':'C.UTF-8','RUSTC_BOOTSTRAP':'1'}

def invoke(args,cwd,seconds=60,env=ENV):
    start=time.monotonic()
    deadline=json.loads((ROOT/'reports/demo/CAMPAIGN_STATUS.json').read_text())['deadline']
    seconds=min(seconds,max(0,deadline-time.time()-20))
    if seconds<2:return {'command':args,'exit_code':None,'status':'BUDGET_EXHAUSTED','elapsed_seconds':0}
    try:
        p=subprocess.run(args,cwd=cwd,env=env,text=True,capture_output=True,timeout=seconds)
        return {'command':args,'cwd':str(cwd),'exit_code':p.returncode,'stdout':p.stdout[-48000:],'stderr':p.stderr[-48000:],'elapsed_seconds':time.monotonic()-start}
    except subprocess.TimeoutExpired as e:
        def text(x):return x.decode(errors='replace') if isinstance(x,bytes) else x or ''
        return {'command':args,'cwd':str(cwd),'exit_code':None,'status':'TIMEOUT','stdout':text(e.stdout)[-48000:],'stderr':text(e.stderr)[-48000:],'elapsed_seconds':time.monotonic()-start}

def sandbox(work,command,network=False):
    bwrap=ROOT/'tools/codex-runtime-v0.155.1/codex-resources/bwrap'
    assert hashlib.sha256(bwrap.read_bytes()).hexdigest()=='77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c'
    cmd=[str(bwrap),'--unshare-all','--die-with-parent','--new-session']
    if network:cmd+=['--share-net']
    for name in ['/usr','/bin','/lib','/lib64']:
        if Path(name).exists():cmd+=['--ro-bind',name,name]
    cmd+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/etc']
    for name in ['/etc/ssl/certs','/etc/resolv.conf','/etc/ld.so.cache','/etc/nsswitch.conf','/etc/hosts']:
        if Path(name).exists():cmd+=['--ro-bind',name,name]
    cmd+=['--ro-bind',str(TOOLS),str(TOOLS),'--bind',str(RUST/'cargo'),str(RUST/'cargo'),
          '--bind',str(work),str(work),'--chdir',str(work),'--clearenv']
    for key,value in ENV.items():cmd+=['--setenv',key,value]
    return cmd+command

def main():
    report={'scope':'Actual tool installation and generated component checks; not a completed whole-system demonstration','checks':[],'model_calls':0}
    path=OUT/'rust-verus-checks.json'
    def save():path.write_text(json.dumps(report,indent=2)+'\n')
    for args in [['rustc','--version'],['cargo','--version'],['verus','--version'],['cargo-verus','--help']]:
        r=invoke(args,ROOT);report['checks'].append(r);save();print(args[0],r['exit_code'],flush=True)
        if r['exit_code']!=0:return
    work=ROOT/'.scp-workbench/rust-validation';work.mkdir(exist_ok=True)
    positive='use vstd::prelude::*;\nverus! { fn plus_one(x: u64) -> (r: u64) requires x < u64::MAX, ensures r == x + 1, { x + 1 } }\nfn main() {}\n'
    for name,code,expected in [('positive',positive,0),('negative',positive.replace('{ x + 1 }','{ x }'),1)]:
        p=work/(name+'.rs');p.write_text(code)
        r=invoke(sandbox(work,['verus',str(p)]),work);r['case']=name;r['expected_pass']=expected==0;report['checks'].append(r);save();print(name,r['exit_code'],flush=True)
        if (r['exit_code']==0)!=(expected==0):return
    timing=json.loads((ROOT/'reports/demo/KSU_HUMAN_TIMING_OVERRIDE_RANGE.json').read_text())
    run=timing['run']['id'];original=next((ROOT/'.scp-workbench/app/runs'/run).glob('hamr_codegen-*/microkit'))
    generated=work/'generated'
    if not generated.exists():shutil.copytree(original,generated)
    report['generated_run_id']=run;report['build_copy']=str(generated);report['source_evidence_preserved']=True;save()
    for component in ['prod_prod','cons_cons']:
        crate=generated/'crates'/component
        for operation,args,network in [('fetch',['cargo','fetch','--manifest-path',str(crate/'Cargo.toml')],True),
                                       ('test',['cargo','test','--offline','--manifest-path',str(crate/'Cargo.toml')],False),
                                       ('verify',['cargo-verus','verify','--offline','--manifest-path',str(crate/'Cargo.toml')],False)]:
            r=invoke(sandbox(work,args,network),crate,180);r.update(component=component,operation=operation,network_enabled=network)
            report['checks'].append(r);save();print(component,operation,r['exit_code'],flush=True)
            if operation=='fetch' and r['exit_code']!=0:break
    report['whole_system_acceptance']=False;save()

if __name__=='__main__':main()
