"""Bind the single-archive SC1 replacement and guarded rollback to current files."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
build=read(C/'build_02.json');test=read(C/'tests_01.json');assert test['status']=='PASS_NATIVE_INDEX_REPAIR_NOT_LIVE'
for p,h in test['sources'].items():assert sha(p)==h
f={k:build[k] for k in ['target','before','after']};assert sha(G/f['target'])==sha(C/'before'/f['target'])==f['before'];assert sha(C/'package'/f['target'])==f['after']
src=(W/'prealpha/loading_cover_lc2/deploy_01.ps1').read_text().replace('loading_cover_lc2_01','startup_crash_sc1_01').replace('LC2_INSTALLED','SC1_INSTALLED')
src=src.replace('-ne 5','-ne 1').replace('files=5','files=1').replace('replacements=5','replacements=1')
lines=src.splitlines();idx=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l);lines[idx]=" if($f.target -cne '"+f['target']+"'){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x') as out:out.write('\n'.join(lines)+'\n')
src=(W/'prealpha/loading_cover_lc2/test_deploy_01.py').read_text().replace("'-TestFailAfter','2'","'-TestFailAfter','1'").replace("runtime=g/'r6/scripts/TowerContinued_Loading_LC1/user_note.txt'","runtime=g/'user_note.txt'")
with (H/'test_deploy_01.py').open('x') as out:out.write(src)
target=(G/f['target']).resolve();protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and p.resolve()!=target:
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=list(p for p in H.iterdir() if p.is_file())+[C/'tests_01.json',C/'build_02.json',C/'prepared_01.json',C/'scene_audit_01/audit.json',C/'diagnosis_01/cause_02.json',C/'diagnosis_01/inputs.json',C/'diagnosis_01/unwind_01.json']
proofs+=list((C/'readback_02').glob('*.json'))+list((C/'prepared_01').glob('*.json'))
manifest={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/startup_crash_sc1_01'),'files':[f],'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','archive_resources_changed':9,'unchanged_owner_resources':8,'framework_changes':0,'save_edits':0}
p=C/'install_manifest_01.json'
with p.open('x') as out:json.dump(manifest,out,indent=2);out.write('\n')
Path(str(p)+'.sha256').write_text(sha(p)+'\n')
print(json.dumps({'status':'SC1_PACKAGE_PINNED','files':1,'protected':len(protected),'save_files':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(p)}))
