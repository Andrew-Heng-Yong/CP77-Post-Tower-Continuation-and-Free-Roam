from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:f.write(s)
assert read(C/'package_proof_01.json')['status']=='PASS_PACKED_READBACK_AND_LOAD_ORDER'
assert read(C/'world_proof_01.json')['status']=='PASS_CURRENT_NATIVE_DOOR_REFERENCE_AND_INTERIOR_ANCHOR'
assert read(H/'native_02/tests_02.json')['status']=='PASS_OFFLINE_NOT_GAMEPLAY'
files=sorted(p.relative_to(C/'package').as_posix() for p in (C/'package').rglob('*') if p.is_file())
assert set(files)=={'archive/pc/mod/000000000_TowerContinued_JD1.archive','archive/pc/mod/000000000_TowerContinued_JD1.archive.xl','r6/scripts/TowerContinued_Housing_H1/JudyDoorJD1.reds','r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds'}
rows=[]
for rel in files:
 p=G/rel;old=sha(p) if p.exists() else None
 if old:
  dest=C/'before'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(dest)==old
 rows.append({'target':rel,'before':old,'after':sha(C/'package'/rel)})
assert sum(r['before'] is not None for r in rows)==1
s=(W/'prealpha/cyberware_cf1/deploy_01.ps1').read_text(encoding='utf-8-sig').replace('cyberware_cf1_01','judy_dennis_jd1_01').replace('CF1_INSTALLED','JD1_INSTALLED')
s=s.replace('-ne 1','-ne 4').replace('files=1','files=4').replace('replacements=0;additions=1','replacements=1;additions=3')
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
allowed=','.join("'"+f+"'" for f in files)
lines[i]=' if($f.target -cnotin @('+allowed+")){throw 'Unexpected target scope'}"
write(H/'deploy_01.ps1','\n'.join(lines)+'\n')
s=(W/'prealpha/cyberware_cf1/test_deploy_01.py').read_text(encoding='utf-8-sig');write(H/'test_deploy_01.py',s)
protected=[]
for folder in (G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ('.log','.jsonl','.dmp') and (not p.is_relative_to(G) or p.relative_to(G).as_posix() not in files):protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[H/n for n in ['JudyDoorJD1.reds','build_02.ps1','compile_01.py','test_03.py','package_01.ps1','verify_world_01.ps1','prepare_install_01.py','deploy_01.ps1','test_deploy_01.py','native_02/component.json','native_02/tests_02.json']]+[C/n for n in ['compile_04/result.json','world_proof_01.json','package_proof_01.json']]
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/judy_dennis_jd1_01'),'files':rows,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'NOT_INSTALLED_NOT_GAMEPLAY_TESTED','save_edits':0,'framework_changes':0,'compiled_sha256':read(C/'compile_04/result.json')['compiled_sha256']}
p=C/'install_manifest_01.json';write(p,json.dumps(m,indent=2)+'\n');write(Path(str(p)+'.sha256'),sha(p)+'\n')
print(json.dumps({'status':'PACKAGE_PINNED_NOT_INSTALLED','files':len(rows),'protected':len(protected),'saves':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(p)}))
