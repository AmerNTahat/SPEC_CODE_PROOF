"""Live, artifact-bound component evidence; source lineage is explicit."""
import json
import re
import os
from pathlib import Path
from .config import PolicyError
from .storage import sha_file, safe_child


def implementation_manifest(workspace):
    """Inputs to the local Rust build/proof, excluding generated build outputs."""
    root=Path(workspace);result={}
    for base,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if d not in {'target','.git','build'}]
        for name in files:
            p=Path(base)/name
            if p.suffix in {'.rs','.toml','.lock','.mk'} or name in {'Makefile','rust-toolchain'}:
                result[p.relative_to(root).as_posix()]=sha_file(p)
    return result


class EngineeringProgress:
    def __init__(self,controller):self.controller=controller;self.store=controller.store

    def register(self,label,report,workspace,model_run_id):
        root=self.store.root.parent.parent
        path=Path(report).resolve();work=Path(workspace).resolve()
        if not path.is_relative_to(root/'reports/demo') or not work.is_relative_to(root/'.scp-workbench'):
            raise PolicyError('Engineering evidence must stay in the authorized demonstration workspace')
        self.controller.status(model_run_id)
        return self.store.record('engineering_execution_job',{'label':label,'report_path':str(path),'workspace':str(work),'model_run_id':model_run_id})

    def inspect(self,job):
        rows=[];blockers=[];report={};complete=False
        try:
            report=json.loads(Path(job['report_path']).read_text())
            if report['source_run_id']!=job['model_run_id'] or report.get('workspace')!=job['workspace']:
                raise PolicyError('Component report lineage does not match the registered candidate')
            model=self.controller.status(job['model_run_id'])
            if not model.get('evidence_current_for_source') or not model.get('policy_current'):raise PolicyError('Source model evidence changed')
            manifest=report.get('source_rs_sha256',{})
            if not manifest:raise PolicyError('No checked Rust source manifest')
            for name,expected in manifest.items():
                if sha_file(safe_child(job['workspace'],name))!=expected:raise PolicyError('Checked Rust changed: '+name)
            if report.get('implementation_manifest') is not None and implementation_manifest(job['workspace'])!=report['implementation_manifest']:
                raise PolicyError('Implementation source or build/proof configuration changed')
            complete=report.get('source_rs_preserved') is True and not report.get('stopped')
            groups={}
            for check in report.get('checks',[]):groups.setdefault(check['crate'],{})[check['kind']]=check
            expected=sorted({Path(name).parts[1] for name in manifest if name.startswith('crates/') and '/src/component/' in name and name.endswith('_app.rs')})
            for crate in expected:
                checks=groups.get(crate,{})
                proof=checks.get('verus',{});test=checks.get('gumbo_tests',{})
                summaries=re.findall(r'verification results:: (\d+) verified, (\d+) errors',proof.get('stdout','')+'\n'+proof.get('stderr',''))
                proof_pass=proof.get('exit_code')==0 and bool(summaries) and int(summaries[-1][0])>0 and all(int(e)==0 for _,e in summaries)
                testrows=[{'name':n,'status':s} for n,s in re.findall(r'^test (\S+) \.\.\. (ok|FAILED|ignored)',test.get('stdout',''),re.M)]
                gumbo=[x for x in testrows if 'gumbo' in x['name'].lower()]
                basic=[x for x in testrows if 'gumbo' not in x['name'].lower()]
                test_pass=test.get('exit_code')==0 and bool(testrows) and all(x['status']=='ok' for x in testrows)
                path=Path(job['workspace'])/'crates'/crate/'src/component'/(crate+'_app.rs')
                source=path.read_text()
                contracts=re.findall(r'// (?:guarantee|case) (\S+)',source)
                assumptions=re.findall(r'requires\s+(.*?)\s+ensures',source,re.S)
                rows.append({'component':crate,'verus_status':'PASS' if proof_pass else ('FAIL' if proof else 'NOT_RUN'),
                    'verus_units_verified':int(summaries[-1][0]) if summaries else None,'verus_units_errors':int(summaries[-1][1]) if summaries else None,
                    'dependency_summaries':summaries[:-1],'tests_status':'PASS' if test_pass else ('FAIL' if test else 'NOT_RUN'),
                    'gumbo_tests':{'passed':sum(x['status']=='ok' for x in gumbo),'total':len(gumbo),'cases':gumbo},
                    'other_tests':{'passed':sum(x['status']=='ok' for x in basic),'total':len(basic),'cases':basic},
                    'declared_contracts':contracts,'assumptions':assumptions,'application_sha256':sha_file(path),'contract_coverage_note':'Named generated postconditions in this component; proof is conditional on its requires clauses. These counts are not independent English requirement coverage.',
                    'checks':checks,'fully_checked':proof_pass and test_pass})
        except FileNotFoundError: blockers.append('Waiting for an executed result or a bound artifact is missing')
        except (OSError,ValueError,KeyError,PolicyError) as exc:blockers.append(str(exc))
        current=not blockers
        return {**job,'state':'COMPLETE' if complete and current else ('RUNNING_OR_INCOMPLETE' if current else 'EVIDENCE_UNAVAILABLE_OR_STALE'),
            'current':current,'blockers':blockers,'components':rows,
            'scores':{'components_passing_both':sum(r['fully_checked'] for r in rows) if current else 0,'components_total':len(rows),
                'verus_components_passed':sum(r['verus_status']=='PASS' for r in rows) if current else 0,
                'gumbo_passed':sum(r['gumbo_tests']['passed'] for r in rows) if current else 0,'gumbo_total':sum(r['gumbo_tests']['total'] for r in rows),
                'other_tests_passed':sum(r['other_tests']['passed'] for r in rows) if current else 0,'other_tests_total':sum(r['other_tests']['total'] for r in rows)},
            'source_model_project':report.get('source_model_project'),'worker_image':report.get('worker_image'),
            'whole_system_acceptance':False,'model_calls':report.get('model_calls',0),
            'scope':'Current isolated implementation candidate bound to the named HAMR model run. Does not attach component proof to an older generated model or establish timing/integration/transfer.'}

    def catalog(self):return [self.inspect(j) for j in self.store.records('engineering_execution_job')]

    def register_runtime(self,job_id,report):
        job=self.store.read_record('engineering_execution_job',job_id)
        path=Path(report).resolve()
        if not path.is_relative_to(self.store.root.parent.parent/'reports/demo'):
            raise PolicyError('Runtime report must be in the demonstration reports')
        record={'job_id':job['id'],'report_path':str(path),'report_sha256':sha_file(path)}
        self.runtime(record)
        return self.store.record('engineering_runtime_observation',record)

    def runtime(self,record):
        job=self.store.read_record('engineering_execution_job',record['job_id'])
        if sha_file(record['report_path'])!=record['report_sha256']:raise PolicyError('Runtime report changed')
        report=json.loads(Path(record['report_path']).read_text())
        if report.get('workspace')!=job['workspace'] or report.get('source_rs_preserved') is not True:
            raise PolicyError('Runtime workspace or source preservation mismatch')
        proof=self.inspect(job)
        if not proof['current'] or proof['state']!='COMPLETE':raise PolicyError('Runtime source model or component evidence is stale')
        manifest=report.get('source_rs_sha256',{})
        if not manifest:raise PolicyError('Runtime source manifest is empty')
        for name,expected in manifest.items():
            if sha_file(safe_child(job['workspace'],name))!=expected:raise PolicyError('Runtime source changed: '+name)
        return {**record,'current':True,'label':job['label'],'report':report,
            'scope':'Bounded console observation only; no R2U2 property coverage, payload correctness, or physical timing acceptance.'}

    def runtime_catalog(self):
        result=[]
        for record in self.store.records('engineering_runtime_observation'):
            try:result.append(self.runtime(record))
            except (OSError,ValueError,KeyError,PolicyError) as exc:result.append({**record,'current':False,'error':str(exc)})
        return result

    def register_system(self,label,report,workspace,model_run_id):
        root=self.store.root.parent.parent;path=Path(report).resolve();work=Path(workspace).resolve()
        if not path.is_relative_to(root/'reports/demo') or not work.is_relative_to(root/'.scp-workbench'):
            raise PolicyError('System evidence must stay in the demonstration workspace')
        self.controller.status(model_run_id)
        return self.store.record('system_verification_job',{'label':label,'report_path':str(path),'workspace':str(work),'model_run_id':model_run_id})

    def system_inspect(self,job):
        blockers=[];checks=[];report={}
        try:
            report=json.loads(Path(job['report_path']).read_text())
            if report.get('source_run_id')!=job['model_run_id'] or report.get('workspace')!=job['workspace']:
                raise PolicyError('System report lineage mismatch')
            model=self.controller.status(job['model_run_id'])
            if not model.get('evidence_current_for_source') or not model.get('policy_current'):
                raise PolicyError('System model evidence is stale')
            if not report.get('implementation_manifest') or implementation_manifest(job['workspace'])!=report['implementation_manifest']:
                raise PolicyError('Generated system proof or build configuration changed')
            for check in report.get('checks',[]):
                summaries=re.findall(r'verification results:: (\d+) verified, (\d+) errors',check.get('stdout','')+'\n'+check.get('stderr',''))
                verified,errors=map(int,summaries[-1]) if summaries else (0,0)
                compile_failure=bool(re.search(r'error\[E\d+\]',check.get('stderr','')))
                if compile_failure:verified,errors=0,0
                checks.append({**check,'verified_units':verified,'error_units':errors,
                    'unit':'generated verification conditions, not distinct English requirements',
                    'status':'COMPILE_FAILURE' if compile_failure else 'PASS' if check.get('exit_code')==0 and verified>0 and errors==0 else 'FAIL' if errors>0 else 'UNKNOWN',
                    'dependency_summaries':summaries if compile_failure else summaries[:-1]})
            if not report.get('complete'):blockers.append('System verification execution incomplete')
            if not checks:blockers.append('No nonempty executed system proof')
        except (OSError,ValueError,KeyError,PolicyError) as exc:blockers.append(str(exc))
        return {**job,'current':not blockers,'blockers':blockers,'checks':checks,
            'status':'STALE_OR_INCOMPLETE' if blockers else 'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL' if any(c['status']=='FAIL' for c in checks) else 'UNKNOWN',
            'verified_units':sum(c['verified_units'] for c in checks) if not blockers else 0,
            'error_units':sum(c['error_units'] for c in checks),'scope':report.get('scope'),
            'whole_system_acceptance':False}

    def system_catalog(self):return [self.system_inspect(j) for j in self.store.records('system_verification_job')]
