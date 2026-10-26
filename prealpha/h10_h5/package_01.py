from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
t=read(C/'tests_01.json');assert t['status']=='PASS_H5_OFFLINE_LIVE_PENDING'
for p,h in t['sources'].items():assert sha(Path(p))==h
changes=read(C/'script_changes_01.json')+read(C/'native_01.json')['files']
assert len(changes)==5 and sum(x['before'] is None for x in changes)==3
for x in changes:
 p=G/x['target'];assert (sha(p) if p.exists() else None)==x['before']
 assert sha(C/'package'/x['target'])==x['after']
s=(W/'prealpha/h10_h4/deploy_01.ps1').read_text(encoding='utf-8-sig')
s=s.replace('h10_h4_01','h10_h5_01').replace('H4_INSTALLED','H5_INSTALLED').replace('-ne 1','-ne 5').replace('files=1','files=5').replace('replacements=1;additions=0','replacements=2;additions=3')
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cnotin @("+','.join("'"+x['target']+"'" for x in changes)+")){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x',encoding='utf-8') as out:out.write('\n'.join(lines)+'\n')
s=(W/'prealpha/h10_h4/test_deploy_01.py').read_text(encoding='utf-8-sig').replace("'-TestFailAfter','1'","'-TestFailAfter','4'")
with (H/'test_deploy_01.py').open('x',encoding='utf-8') as out:out.write(s)
targets={(G/x['target']).resolve() for x in changes};protected=[]
for root in (G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S):
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ('.log','.jsonl','.dmp') and p.resolve() not in targets:
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=set(H.glob('*.*'))|{Path(p) for p in t['sources']}|{C/'tests_01.json',C/'h10_purchase.scene.json'}
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/h10_h5_01'),'files':changes,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in sorted(proofs)],'live_status':'pending','new_archive_resources':2,'existing_archive_changes':0,'framework_changes':0,'save_edits':0}
p=C/'install_manifest_01.json'
with p.open('x',encoding='utf-8') as out:json.dump(m,out,indent=2);out.write('\n')
Path(str(p)+'.sha256').write_text(sha(p)+'\n')
print(json.dumps({'status':'H5_PACKAGE_PINNED','files':5,'protected':len(protected),'saves':sum(x['kind']=='save' for x in protected),'manifest_sha256':sha(p)}))
