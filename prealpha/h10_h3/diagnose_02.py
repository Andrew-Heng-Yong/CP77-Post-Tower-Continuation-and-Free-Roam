"""Capture the now-flushed H2 session and its new AutoSave-14, read-only."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_02'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');B=W/'recovery/h10_h3_diagnosis_02'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def copy(p,d):
 h=sha(p);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);assert sha(p)==sha(d)==h;return h
O.mkdir(exist_ok=False);B.mkdir(exist_ok=False)
receipt={str(p):{'backup':str(B/'AutoSave-14'/p.name),'sha256':copy(p,B/'AutoSave-14'/p.name)} for p in (S/'AutoSave-14').iterdir() if p.is_file()}
(B/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
logs={rel:copy(G/rel,O/Path(rel).name) for rel in ['red4ext/logs/red4ext-2026-10-24-18-17-21.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','bin/x64/plugins/cyber_engine_tweaks/cyber_engine_tweaks.log']}
prior=json.loads((C/'diagnosis_01/inputs.json').read_text())['saves'];current={str(p):sha(p) for p in S.rglob('*') if p.is_file()}
changed={p:{'before':h,'after':current.get(p)} for p,h in prior.items() if current.get(p)!=h}
assert list(changed)==[str(S/'user.gls')],changed
added={p:h for p,h in current.items() if p not in prior};assert len(added)==3 and all(Path(p).parent.name=='AutoSave-14' for p in added),added
report={'changed_since_first_live_capture':changed,'new_user_autosave_files':added,'saves':current,'logs':logs,'normal_shutdown':'18:26:41','live_h2_door_resolved':'18:20:20; signed interior distance=-9.245326','purchase_offer_log_present':False,'assistant_game_writes_so_far':0}
(O/'inputs.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'normal_shutdown':report['normal_shutdown'],'new_autosave_files':len(added),'changed_existing_files':list(changed),'protected_files':len(current)}))
