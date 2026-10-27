"""Read-only preinstall save-file inventory."""
from hashlib import sha256
from pathlib import Path
import json

C=Path(__file__).resolve().parent/'candidate_01'
root=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
out=C/'save_baseline_01.json'
assert not out.exists()
def digest(path):
 h=sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest().upper()
files=[{'path':str(p),'sha256':digest(p)} for p in sorted(root.rglob('*')) if p.is_file()]
assert files
out.write_text(json.dumps({'status':'READ_ONLY_PREINSTALL_SAVE_BASELINE','files':files},indent=2)+'\n')
Path(str(out)+'.sha256').write_text(digest(out)+'\n')
print(json.dumps({'save_files':len(files),'save_writes':0}))
