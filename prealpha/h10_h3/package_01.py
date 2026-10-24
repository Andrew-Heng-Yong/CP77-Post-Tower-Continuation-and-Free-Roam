from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
t=json.loads((C/'tests_01.json').read_text());assert t['status']=='PASS_H3_OFFLINE_NOT_LIVE'
for path,h in t['sources'].items():assert sha(Path(path))==h
changes=[]
for name in ['HousingPurchase.reds','HousingState.reds','HousingEntranceH3.reds']:
 rel='r6/scripts/TowerContinued_Housing_H1/'+name;p=C/'package'/rel;b=C/'before'/rel
 before=sha(b) if b.exists() else None
 assert (sha(G/rel) if (G/rel).exists() else None)==before
 changes.append({'target':rel,'before':before,'after':sha(p)})
assert len(changes)==3 and sum(x['before'] is None for x in changes)==1
script=(W/'prealpha/h10_h2/deploy_01.ps1').read_text(encoding='utf-8-sig')
script=script.replace('h10_h2_01','h10_h3_01').replace('H2_INSTALLED','H3_INSTALLED').replace('-ne 6','-ne 3').replace('files=6','files=3').replace('replacements=4;additions=2','replacements=2;additions=1')
lines=script.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cnotin @("+','.join("'"+x['target']+"'" for x in changes)+")){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
test=(W/'prealpha/h10_h2/test_deploy_01.py').read_text(encoding='utf-8-sig').replace("'-TestFailAfter','5'","'-TestFailAfter','2'")
with (H/'test_deploy_01.py').open('x',encoding='utf-8') as f:f.write(test)
targets={(G/x['target']).resolve() for x in changes};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and p.resolve() not in targets:protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'compile_04/result.json',C/'compile_04/cache/compiled.redscripts',C/'diagnosis_01/inputs.json',C/'diagnosis_02/inputs.json']
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/h10_h3_01'),'files':changes,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','framework_changes':0,'archive_changes':0,'save_edits':0}
out=C/'install_manifest_01.json'
with out.open('x') as f:json.dump(m,f,indent=2);f.write('\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':'H3_PACKAGE_PINNED','files':len(changes),'protected':len(protected),'save_files':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(out)}))
