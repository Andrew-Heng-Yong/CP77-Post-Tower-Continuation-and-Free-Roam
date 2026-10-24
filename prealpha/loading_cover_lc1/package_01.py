"""Freeze tested LC1 sources and a closed-game installation manifest."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_04';P=C/'package'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
changes=json.loads((C/'changes_01.json').read_text())
n=json.loads((H/'candidate_02/native_01.json').read_text(encoding='utf-8-sig'))
changes.append({k:n[k] for k in ['target','before','after']})
assert len(changes)==17
tests=json.loads((C/'tests_01.json').read_text());assert tests['status']=='PASS_OFFLINE_COMPILED_NATIVE_NOT_LIVE'
assert all(sha(Path(p))==v for p,v in tests['sources'].items())
for f in changes:
 f['after']=sha(P/f['target']);p=G/f['target'];assert (sha(p) if p.exists() else None)==f['before']
# Derived, scoped successor of the already exercised HS1 installer.
deployer=(W/'prealpha/history_snapshot_hs1/deploy_01.ps1').read_text()
deployer=deployer.replace("'candidate_01'","'candidate_04'").replace('history_snapshot_hs1_01','loading_cover_lc1_01').replace('HS1_INSTALLED_LIVE_PENDING','LC1_INSTALLED_LIVE_PENDING')
deployer=deployer.replace('-ne 13','-ne 17').replace('files=13','files=17').replace('replacements=10;additions=3','replacements=15;additions=2')
lines=deployer.splitlines()
allow=','.join("'"+f['target']+"'" for f in changes)
idx=next(i for i,l in enumerate(lines) if "Unexpected target scope" in l)
lines[idx]=" if($f.target -cnotin @("+allow+")){throw 'Unexpected target scope'}"
dest=H/'deploy_01.ps1';assert not dest.exists();dest.write_text('\n'.join(lines)+'\n')
fixture=(W/'prealpha/history_snapshot_hs1/test_deploy_01.py').read_text().replace("O=H/'candidate_01'","O=H/'candidate_04'")
fixture=fixture.replace("bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/snapshot_hs1_user.json","r6/scripts/TowerContinued_Loading_LC1/user_note.txt").replace("'-TestFailAfter','11'","'-TestFailAfter','15'")
fixture=fixture.replace('runtime_snapshot_preserved_on_rollback','unrelated_user_file_preserved_on_rollback')
dest=H/'test_deploy_01.py';assert not dest.exists();dest.write_text(fixture)
targets={str((G/f['target']).resolve()).lower() for f in changes};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and str(p.resolve()).lower() not in targets:
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]
proofs += [C/'tests_01.json',C/'compile_02/result.json',C/'compile_02/cache/compiled.redscripts',H/'candidate_02/native_01.json',H/'candidate_02/native_phase.json']
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/loading_cover_lc1_01'),'files':changes,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','archive_resources_changed':1,'framework_changes':0,'save_edits':0}
out=C/'install_manifest_01.json';assert not out.exists();out.write_text(json.dumps(m,indent=2)+'\n');Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':'PACKAGE_PINNED','files':len(changes),'protected':len(protected),'saves':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(out)}))
