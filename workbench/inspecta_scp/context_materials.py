"""Explicit human-selected context; no implicit repository-wide agent ingestion."""
import base64
import hashlib
from pathlib import Path
from .config import PolicyError, relative_file
from .sources import Sources
from .storage import safe_child

FORMATS={'.pdf','.txt','.md','.json','.sysml','.aadl','.scala','.rs'}

class ContextMaterials:
    def __init__(self,store):self.store=store;self.sources=Sources(store)

    def inventory(self,directory):
        root=self.sources.register_root(directory,'learning')
        files=[];scanned=0;pending=[Path(root['path'])]
        while pending:
            folder=pending.pop()
            for path in sorted(folder.iterdir()):
                scanned+=1
                if scanned>10000:raise PolicyError('Context repository is too broad; select a smaller folder')
                if path.is_symlink() or path.name.startswith('.'):continue
                if path.is_dir():pending.append(path);continue
                if path.suffix.lower() in FORMATS:
                    rel=path.relative_to(root['path']).as_posix()
                    try:relative_file(rel)
                    except PolicyError:continue
                    files.append({'path':rel,'bytes':path.stat().st_size})
        return {**root,'files':files,'scope':'Inventory only. Select files explicitly before importing context.'}

    def select(self,root_id,files):
        root=self.store.read_record('source_root',root_id)
        if root['role']!='learning':raise PolicyError('Context import requires an explicit learning root')
        if not isinstance(files,list) or not files or len(files)>100:raise PolicyError('Select 1–100 context documents')
        entries=[]
        for relative in files:
            source=self.sources.register(root_id,relative)
            if any(s['role']=='evaluator' and s['sha256']==source['sha256'] for s in self.store.records('source')):
                raise PolicyError('Evaluator reference cannot be imported as learning context')
            entries.append(self.store.record('context_document',{'source_id':source['id'],'name':relative,
                'purpose':'learning_context','shared_with_validation':False,'status':'SELECTED_NOT_YET_SPLIT_APPROVED'}))
        return {'documents':entries}

    def upload(self,name,encoded):
        relative_file(name)
        if Path(name).name!=name or Path(name).suffix.lower() not in FORMATS:raise PolicyError('Upload a supported single document')
        try:data=base64.b64decode(encoded,validate=True)
        except (ValueError,TypeError):raise PolicyError('Invalid uploaded file encoding')
        if not data or len(data)>16*1024*1024:raise PolicyError('Upload must contain 1 byte–16 MiB')
        folder=safe_child(self.store.root,'uploads/'+hashlib.sha256(data).hexdigest());folder.mkdir(parents=True,exist_ok=True)
        target=safe_child(folder,name)
        if target.exists() and target.read_bytes()!=data:raise PolicyError('Uploaded snapshot changed')
        if not target.exists():
            with target.open('xb') as stream:stream.write(data)
        root=self.sources.register_root(folder,'learning')
        return self.select(root['id'],[name])
