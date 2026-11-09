"""Keep model-embedded command hints from overriding the controller's resolved options."""
import re
import shutil
from pathlib import Path
from .storage import safe_child,sha_file


def execution_view(candidate,destination,files):
    destination=Path(destination);destination.mkdir()
    changes=[]
    for name in files:
        source=safe_child(candidate,name);target=safe_child(destination,name);target.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix=='.sysml':
            text=source.read_bytes().decode("utf-8")
            # HAMR mines these comment directives as CLI options. Neutralize
            # that control metadata only, retaining bytes/positions elsewhere.
            pattern=r'(?m)^[ \t]*//@[ \t]*HAMR:[^\r\n]*'
            revised,n=re.subn(pattern,lambda m:'//'+' '*(len(m.group())-2),text)
            target.write_bytes(revised.encode("utf-8"))
            if n:changes.append({'path':name,'command_hint_lines_neutralized':n,'original_sha256':sha_file(source),'execution_sha256':sha_file(target)})
        else:shutil.copy2(source,target)
    (destination/'.slang').mkdir()
    return {'changes':changes,'files':{name:sha_file(safe_child(destination,name)) for name in files},
            'scope':'Separate execution copy; only HAMR CLI comment hints neutralized to enforce resolved controller options. Original snapshots preserved. No formal model clauses intentionally changed.'}
