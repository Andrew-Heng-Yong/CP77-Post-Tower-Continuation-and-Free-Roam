from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(C/'tests_01.json')['status']=='PASS_HS2_OFFLINE_LIVE_PENDING'
files=read(C/'changes_01.json');assert len(files)==2
for f in files:assert sha(C/'before'/f['target'])==sha(G/f['target'])==f['before'] and sha(C/'package'/f['target'])==f['after']
s=(W/'prealpha/h10_h4/deploy_01.ps1').read_text(encoding='utf-8-sig').replace('h10_h4_01','snapshot_reload_hs2_01').replace('H4_INSTALLED','HS2_INSTALLED').replace('-ne 1','-ne 2').replace('files=1','files=2').replace('replacements=1','replacements=2')
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cnotin @("+','.join("'"+f['target']+"'" for f in files)+")){throw 'Unexpected target scope'}"
(H/'deploy_01.ps1').write_text('\n'.join(lines)+'\n')
(H/'test_deploy_01.py').write_text((W/'prealpha/h10_h4/test_deploy_01.py').read_text(encoding='utf-8-sig'))
targets={(G/f['target']).resolve() for f in files};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and p.resolve() not in targets:protected.append(dict(path=str(p),sha256=sha(p),kind='save' if p.is_relative_to(S) else 'game'))
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'compile_01/result.json',C/'compile_01/cache/compiled.redscripts']
m=dict(schema=1,game_root=str(G),backup_root=str(W/'recovery/snapshot_reload_hs2_01'),files=files,protected=protected,proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],live_status='pending',archive_changes=0,framework_changes=0,save_edits=0)
p=C/'install_manifest_01.json'
with p.open('x') as f:json.dump(m,f,indent=2);f.write('\n')
Path(str(p)+'.sha256').write_text(sha(p)+'\n')
print(json.dumps(dict(files=2,protected=len(protected),saves=sum(x['kind']=='save' for x in protected),manifest_sha256=sha(p))))
