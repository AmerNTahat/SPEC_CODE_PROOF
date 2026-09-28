"""Recorded application checks, kept separate from engineering verification."""
import json,re
from pathlib import Path
from .storage import sha_file


def recorded_checks(root):
    root=Path(root)
    specs=[('Application tests','reports/build/application-tests.log'),('Firefox UI checks','reports/build/browser-smoke.json')]
    try:receipt=json.loads((root/'.scp-workbench/BUILD_RESULT.json').read_text());hashes={e['path']:e['sha256'] for e in receipt['evidence']}
    except (OSError,ValueError,KeyError,TypeError):hashes={}
    rows=[]
    for label,path in specs:
        row={'label':label,'path':path,'status':'NOT_RECORDED','passed':None,'total':None}
        try:
            file=root/path
            if path not in hashes or sha_file(file)!=hashes[path]:row['status']='STALE_OR_UNBOUND'
            elif path.endswith('.json'):
                report=json.loads(file.read_text());row.update(status=report.get('status','UNKNOWN'),total=len(report.get('checks',[])))
                row['passed']=row['total'] if row['status']=='PASS' else None
            else:
                text=file.read_text();match=re.search(r'Ran (\d+) tests? in ',text);count=int(match[1]) if match else None
                passed=count is not None and bool(re.search(r'^OK\s*$',text,re.M)) and not re.search(r'^FAILED\b',text,re.M)
                row.update(status='PASS' if passed else 'UNKNOWN',total=count,passed=count if passed else None)
        except (OSError,ValueError,TypeError):pass
        rows.append(row)
    return {'checks':rows,'scope':'Recorded application checks bound to the saved receipt. These are support-software checks, not system proofs or English-requirement coverage.'}
