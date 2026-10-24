from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
t=read(C/'tests_02.json');assert t['status']=='PASS_H2_OFFLINE_NOT_LIVE'
for path,h in t['sources'].items():assert sha(path)==h
changes=read(C/'changes_02.json');n=read(C/'native_02.json');changes.append({k:n[k] for k in ['target','before','after']})
for f in changes:
 if f['before']:assert sha(G/f['target'])==sha(C/'before'/f['target'])==f['before']
 else:assert not (G/f['target']).exists()
 # Earlier change manifests deliberately remain intermediate evidence. The
 # final package binds the exact last tested source bytes, including lock undo.
 f['after']=sha(C/'package'/f['target']);assert t['sources'][str(C/'package'/f['target'])]==f['after']
assert len(changes)==6 and sum(f['before'] is None for f in changes)==2
s=(W/'prealpha/loading_cover_lc3/deploy_01.ps1').read_text().replace('loading_cover_lc3_01','h10_h2_01').replace('LC3_INSTALLED','H2_INSTALLED')
s=s.replace('-ne 3','-ne 6').replace('files=3','files=6').replace('replacements=3;additions=0','replacements=4;additions=2')
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l);lines[i]=" if($f.target -cnotin @("+','.join("'"+f['target']+"'" for f in changes)+")){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x',encoding='utf-8') as out:out.write('\n'.join(lines)+'\n')
s=(W/'prealpha/loading_cover_lc3/test_deploy_01.py').read_text().replace("'-TestFailAfter','2'","'-TestFailAfter','5'")
with (H/'test_deploy_01.py').open('x',encoding='utf-8') as out:out.write(s)
targets={(G/f['target']).resolve() for f in changes};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and p.resolve() not in targets:protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_02.json',C/'native_02.json',C/'anchor_01.json',C/'compile_04/result.json',C/'compile_04/cache/compiled.redscripts',C/'diagnosis_01/inputs.json',C/'native_readback_02/mq011.questphase.json']
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/h10_h2_01'),'files':changes,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','unchanged_s23_resources':33,'framework_changes':0,'save_edits':0}
out=C/'install_manifest_01.json'
with out.open('x') as f:json.dump(m,f,indent=2);f.write('\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':'H2_PACKAGE_PINNED','files':6,'protected':len(protected),'save_files':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(out)}))
