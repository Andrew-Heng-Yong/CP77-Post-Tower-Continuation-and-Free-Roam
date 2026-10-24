"""Bind the failed live attempt and retain AutoSave-15 without editing originals."""
from pathlib import Path
import hashlib,json,shutil,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');B=W/'recovery/h10_h4_diagnosis_01'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def copy(p,d):
 h=sha(p);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);assert sha(p)==sha(d)==h;return h
O.mkdir(exist_ok=False);B.mkdir(exist_ok=False)
receipt={str(p):{'backup':str(B/'AutoSave-15'/p.name),'sha256':copy(p,B/'AutoSave-15'/p.name)} for p in (S/'AutoSave-15').iterdir() if p.is_file()}
(B/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
log=G/'bin/x64/plugins/cyber_engine_tweaks/gamelog.log';lh=copy(log,O/'gamelog.log');lines=(O/'gamelog.log').read_text(encoding='utf-8-sig',errors='replace').splitlines()
rows=[x for x in lines if 'PTFR_HousingH3' in x]
assert any('entrance=true released=true nativeUI=true popup=false' in x and 'high=1 tier=1 scene=true dialogue=false combat=false' in x for x in rows)
assert any('map=purchasable H10 icon' in x for x in rows)
assert not any('purchase confirmation requested' in x for x in rows)
report={'log_sha256':lh,'diagnostic_rows':rows,'diagnosis':'The player reached the exact door while the cover was released and native UI ready. SafeActor denied purchase on scenes.IsEntityInScene=true despite HighLevel=1, SceneTier=1, dialogue=false and combat=false. Other guard terms remain unproven until live retest.','saves':{str(p):sha(p) for p in S.rglob('*') if p.is_file()},'backed_up_autosave_files':receipt,'game_edits':0,'save_edits':0}
(O/'inputs.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'log_sha256':lh,'guard_rows':len(rows),'saves':len(report['saves']),'backup_files':len(receipt)}))
