"""Read PDF text with the existing local extractor inside an empty network namespace."""
from pathlib import Path
import subprocess
import tempfile
from .config import PolicyError
from .storage import sha_file


def extract_pdf(path):
    tool=Path('/usr/bin/pdftotext')
    sandbox=Path(__file__).resolve().parents[2]/'tools/codex-runtime-v0.155.1/codex-resources/bwrap'
    if not tool.is_file():raise PolicyError('PDF extraction requires pdftotext; select TXT or install the missing dependency')
    if sha_file(sandbox)!='77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c':raise PolicyError('PDF sandbox identity changed')
    with tempfile.TemporaryDirectory(prefix='scp-pdf-') as temp:
        cmd=[str(sandbox),'--unshare-all','--die-with-parent','--new-session']
        for directory in ['/usr','/bin','/lib','/lib64']:
            if Path(directory).exists():cmd+=['--ro-bind',directory,directory]
        cmd+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--bind',temp,'/out',
              '--ro-bind',str(Path(path).resolve()),'/input.pdf','--clearenv','--setenv','PATH','/usr/bin:/bin',
              '--','/bin/sh','-c','ulimit -f 8192; exec /usr/bin/pdftotext -layout /input.pdf /out/context.txt']
        try:result=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=20)
        except subprocess.TimeoutExpired as exc:raise PolicyError('PDF extraction exceeded 20 seconds') from exc
        output=Path(temp)/'context.txt'
        if result.returncode or not output.is_file():raise PolicyError('Isolated PDF extraction failed; retain the sandbox and inspect the PDF or host namespace permissions')
        if output.stat().st_size>4*1024*1024:raise PolicyError('Extracted text exceeds 4 MiB; select a smaller document')
        text=output.read_text()
        if not text.strip():raise PolicyError('PDF contains no extractable text; provide OCR text explicitly')
        return text,{'tool':str(tool),'sha256':sha_file(tool),'method':'pdftotext -layout','scope':'Text extraction only; not requirements interpretation'}
