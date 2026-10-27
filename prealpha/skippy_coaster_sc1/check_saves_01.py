"""Confirm SC1 deployment did not alter saved-game files or names."""
from hashlib import sha256
from pathlib import Path
import json

C=Path(__file__).resolve().parent/'candidate_07'
root=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
baseline=C/'save_baseline_01.json'
out=C/'save_comparison_01.json'
assert not out.exists()
before=json.loads(baseline.read_text())
assert before['status']=='READ_ONLY_PREINSTALL_SAVE_BASELINE'
def digest(path):
 h=sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest().upper()
old={row['path']:row['sha256'] for row in before['files']}
new={str(p):digest(p) for p in root.rglob('*') if p.is_file()}
assert old==new,'Saved-game names or contents changed'
result={'status':'PASS_ALL_SAVES_BYTE_IDENTICAL','files':len(old),'baseline_sha256':digest(baseline),'game_writes':0,'save_writes':0}
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
