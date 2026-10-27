"""Read-only fresh save hash baseline immediately before S30 installation."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
root=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
out=H/'candidate_02/save_baseline_02.json';assert not out.exists()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest().upper()
files=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()]
out.write_text(json.dumps({'status':'PREINSTALL_READ_ONLY_SAVE_BASELINE','files':files},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'save_files':len(files),'bytes':sum(x['bytes'] for x in files)}))
