"""Finish diagnosis_02 after identifying AutoSave-14 as a rotated existing slot."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_02'
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');B=W/'recovery/h10_h3_diagnosis_02'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
receipt=json.loads((B/'receipt.json').read_text())
for p,r in receipt.items():assert sha(Path(p))==sha(Path(r['backup']))==r['sha256']
prior=json.loads((C/'diagnosis_01/inputs.json').read_text())['saves'];current={str(p):sha(p) for p in S.rglob('*') if p.is_file()}
changed={p:{'before':h,'after':current.get(p)} for p,h in prior.items() if current.get(p)!=h}
assert set(changed)=={str(S/'user.gls'),*receipt},changed
assert set(current)==set(prior)
report={'changed_since_first_live_capture':changed,'saves':current,'logs':{str(p):sha(p) for p in O.glob('*.log')},'normal_shutdown':'18:26:41','live_h2_door_resolved':'18:20:20; signed interior distance=-9.245326','purchase_offer_log_present':False,'assistant_game_writes_so_far':0,'note':'User session rotated AutoSave-14 and user.gls after first capture; backed up final AutoSave-14. No other existing saves changed.'}
out=O/'inputs.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'protected_files':len(current),'user_changed_files_since_initial_capture':len(changed),'backed_up_files':len(receipt)}))
