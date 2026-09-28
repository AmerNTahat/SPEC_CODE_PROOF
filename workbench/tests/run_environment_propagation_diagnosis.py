"""Diagnostic transcription of FAA MRI8/9 allocation, not a system timing proof."""
from pathlib import Path
import json,subprocess,time,hashlib
root=Path.cwd();out=root/'reports/demo/isolette-rust';solver=root/'.scp-workbench/tools/sireum-4.20260810.80aad0c2/Sireum/bin/linux/cvc5'
text=(out/'FAA_MRI_PAGE_A17.txt').read_text();assert 'REQ-MRI-8' in text and 'REQ-MRI-9' in text and 'UNSPECIFIED' in text
base='''(set-logic QF_LIA)
(declare-const external_lower Int)
(declare-const external_upper Int)
(declare-const internal_lower Int)
(declare-const internal_upper Int)
(declare-const interface_failure Bool)
; Approved environmental ordering, assumed, not proved.
(assert (< external_lower external_upper))
; MRI8: a healthy interface forwards the same quantities.
(assert (=> (not interface_failure)
  (and (= internal_lower external_lower) (= internal_upper external_upper))))
; Internal TableA7 domains. MRI9 otherwise leaves the range unspecified.
(assert (and (<= 96 internal_lower) (<= internal_lower 101)))
(assert (and (<= 97 internal_upper) (<= internal_upper 102)))
'''
queries=[('healthy_copy_preserves_order','(assert (not interface_failure))\n(assert (not (< internal_lower internal_upper)))','unsat'),('failure_range_need_not_be_ordered','(assert interface_failure)\n(assert (= external_lower 97))\n(assert (= external_upper 100))\n(assert (= internal_lower 101))\n(assert (= internal_upper 97))','sat')]
report={'scope':'Manual SMT transcription of approved environmental premise plus MRI8/9 and TableA7. Establishes a contract-level distinction only; no runtime failure, scheduling reachability or whole-system proof is claimed.','model_calls':0,'checks':[],'pdf_page_sha256':hashlib.sha256((out/'FAA_MRI_PAGE_A17.txt').read_bytes()).hexdigest()}
for name,query,expected in queries:
 p=out/(name+'.smt2');p.write_text(base+query+'\n(check-sat)\n');start=time.monotonic();cmd=[str(solver),'--lang=smt2',str(p)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=20);report['checks'].append({'name':name,'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'expected':expected,'elapsed_seconds':time.monotonic()-start,'expected_observed':r.returncode==0 and r.stdout.strip()==expected})
(out/'ENVIRONMENT_PROPAGATION_DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n');assert all(c['expected_observed'] for c in report['checks']);print([(c['name'],c['stdout'].strip()) for c in report['checks']])
