"""Read-only save baseline immediately before W2 installation."""
import hashlib,json
from pathlib import Path

H=Path(__file__).resolve().parent
P=H/'candidate_02'
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
out=P/'save_baseline_01.json'
assert not out.exists(),out
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest().upper()
files=[{'path':str(p),'sha256':sha(p)} for p in sorted(S.rglob('*')) if p.is_file()]
assert files
out.write_text(json.dumps({'status':'READ_ONLY_PREINSTALL_SAVE_BASELINE','files':files},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'save_files':len(files),'save_writes':0}))
