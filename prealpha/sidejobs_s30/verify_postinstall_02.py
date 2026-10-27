"""Confirm the whole combined install, rollback backup, and saved games."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parent.parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
P=H/'candidate_02';B=W/'recovery/sidejobs_s30_02'
manifest=json.loads((P/'install_manifest_01.json').read_text(encoding='utf-8'))
package=json.loads((P/'manifest.json').read_text(encoding='utf-8'))
saves=json.loads((P/'save_baseline_02.json').read_text(encoding='utf-8'))['files']
def sha(p):
 if not p.is_file():return None
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest().upper()
assert len(package['files'])==51 and len(manifest['files'])==3
for row in package['files']:assert sha(G/row['path'])==row['sha256'],row['path']
for row in manifest['files']:assert sha(B/row['target'])==row['before'],row['target']
before={x['path'] for x in saves};after={str(p) for p in S.rglob('*') if p.is_file()}
assert before==after,('save file set changed',len(before),len(after))
for row in saves:assert sha(Path(row['path']))==row['sha256'],row['path']
assert not any((G/'archive/pc/mod').glob('*S30*.archive'))
receipt=json.loads((B/'receipt.json').read_text(encoding='utf-8-sig'))
assert receipt['status']=='S30_CONSOLIDATED_INSTALLED_LIVE_PENDING'
report={'status':'INSTALLED_STATIC_VERIFIED_LIVE_PENDING','combined_files':51,'replaced_files':3,'backup_files':3,'save_files_unchanged':len(saves),'extra_S30_archives':0,'game_launched':False,'live_quest_result':'pending'}
(P/'postinstall_02.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
