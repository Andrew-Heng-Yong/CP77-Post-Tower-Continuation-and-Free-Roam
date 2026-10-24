from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
tests=read(C/'tests_01.json');assert tests['status']=='PASS_H4_OFFLINE_NOT_LIVE'
files=read(C/'changes_01.json');assert len(files)==1 and files[0]['before'] and files[0]['target']=='r6/scripts/TowerContinued_Housing_H1/HousingState.reds'
for f in files:assert sha(C/'before'/f['target'])==sha(G/f['target'])==f['before'] and sha(C/'package'/f['target'])==f['after']
script=(W/'prealpha/h10_h3/deploy_01.ps1').read_text(encoding='utf-8-sig')
script=script.replace('h10_h3_01','h10_h4_01').replace('H3_INSTALLED','H4_INSTALLED').replace('-ne 3','-ne 1').replace('files=3','files=1').replace('replacements=2;additions=1','replacements=1;additions=0')
lines=script.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cnotin @('"+files[0]['target']+"')){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x',encoding='utf-8') as out:out.write('\n'.join(lines)+'\n')
test=(W/'prealpha/h10_h3/test_deploy_01.py').read_text(encoding='utf-8-sig').replace("'-TestFailAfter','2'","'-TestFailAfter','1'")
with (H/'test_deploy_01.py').open('x',encoding='utf-8') as out:out.write(test)
targets={(G/f['target']).resolve() for f in files};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and p.resolve() not in targets:
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'compile_01/result.json',C/'compile_01/cache/compiled.redscripts',C/'diagnosis_01/inputs.json']
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/h10_h4_01'),'files':files,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','archive_changes':0,'framework_changes':0,'save_edits':0}
out=C/'install_manifest_01.json'
with out.open('x') as h:json.dump(m,h,indent=2);h.write('\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':'H4_PACKAGE_PINNED','files':len(files),'protected':len(protected),'save_files':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(out)}))
