"""Package only the installed S25 archive; retain rollback and protected saves."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_02'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
b=read(C/'build_01.json');t=read(C/'tests_01.json');assert t['status']=='PASS_FS1_OFFLINE_LIVE_PENDING'
for p,h in t['sources'].items():assert sha(Path(p))==h
f={k:b[k] for k in ('target','before','after')}
assert sha(G/f['target'])==sha(C/'before'/f['target'])==f['before']
assert sha(C/'package'/f['target'])==f['after']
src=(W/'prealpha/h10_h4/deploy_01.ps1').read_text(encoding='utf-8-sig')
src=src.replace('h10_h4_01','fred_scene_fs1_01').replace('H4_INSTALLED','FS1_INSTALLED').replace('candidate_01','candidate_02')
src=src.replace('r6/scripts/TowerContinued_Housing_H1/HousingState.reds',f['target'])
with (H/'deploy_01.ps1').open('x',encoding='utf-8') as out:out.write(src)
src=(W/'prealpha/h10_h4/test_deploy_01.py').read_text(encoding='utf-8-sig').replace('candidate_01','candidate_02')
with (H/'test_deploy_01.py').open('x',encoding='utf-8') as out:out.write(src)
target=(G/f['target']).resolve();protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ('.log','.jsonl','.dmp') and p.resolve()!=target:
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'build_01.json',C/'fred_before.questphase.json',C/'fred_after.questphase.json',W/'diagnostics/scene_membership_20261025_01/assessment_01.json']
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/fred_scene_fs1_01'),'files':[f],'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','archive_resources_changed':1,'unchanged_resources':25,'framework_changes':0,'script_changes':0,'save_edits':0}
p=C/'install_manifest_01.json'
with p.open('x',encoding='utf-8') as out:json.dump(m,out,indent=2);out.write('\n')
Path(str(p)+'.sha256').write_text(sha(p)+'\n')
print(json.dumps({'status':'FS1_PACKAGE_PINNED','files':1,'protected':len(protected),'saves':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(p)}))
