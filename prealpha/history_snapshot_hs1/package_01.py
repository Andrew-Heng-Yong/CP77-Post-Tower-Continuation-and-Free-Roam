from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01';P=O/'package'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
changes=json.loads((O/'changes_01.json').read_text())
for x in changes:
 p=G/x['target'];assert (sha(p) if p.exists() else None)==x['before'],str(p)
 x['after']=sha(P/x['target'])
readback=json.loads((O/'readback_01.json').read_text())
assert all(sha(Path(p))==v for p,v in readback['sources'].items())
assert json.loads((O/'tests_02.json').read_text())['status']=='PASS_OFFLINE_NOT_LIVE'
assert json.loads((O/'native_check_01.json').read_text(encoding='utf-8-sig'))['status']=='PASS_CURRENT_NATIVE_TIMEOUT_BRANCH'
targets={str((G/x['target']).resolve()).lower() for x in changes};protected={}
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and str(p.resolve()).lower() not in targets:
   protected[str(p)]={'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'}
proofpaths=[H/f for f in ['SnapshotStateHS1.reds','init.lua','build_catalogue_01.py','integrate_01.py','compile_01.py','test_01.py','readback_01.py','native_check_01.ps1','deploy_01.ps1','package_01.py']]
proofpaths += [O/f for f in ['catalogue.json','tests_02.json','native_check_01.json','readback_01.json','compile_04/result.json','compile_04/cache/compiled.redscripts']]
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/history_snapshot_hs1_01'),'files':changes,'proofs':[{'path':str(p.resolve()),'sha256':sha(p)} for p in proofpaths],'protected':list(protected.values()),'live_status':'pending','archive_changes':0,'framework_changes':0}
path=O/'install_manifest_01.json';assert not path.exists();path.write_text(json.dumps(m,indent=2)+'\n')
Path(str(path)+'.sha256').write_text(sha(path)+'\n')
print(json.dumps({'files':len(changes),'protected':len(protected),'saves':sum(p['kind']=='save' for p in protected.values()),'manifest_sha256':sha(path)}))
