"""Freeze the five-file LC2 repair and a guarded, reversible installer."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';P=C/'package'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
changes=json.loads((C/'changes_01.json').read_text());assert len(changes)==5
tests=json.loads((C/'tests_01.json').read_text());assert tests['status']=='PASS_OFFLINE_COMPILED_NATIVE_NOT_LIVE'
for p,h in tests['sources'].items():assert sha(Path(p))==h
for f in changes:
 f['after']=sha(P/f['target']);assert sha(G/f['target'])==f['before'];assert sha(C/'before'/f['target'])==f['before']
s=(W/'prealpha/loading_cover_lc1/deploy_01.ps1').read_text().replace("'candidate_04'","'candidate_01'").replace('loading_cover_lc1_01','loading_cover_lc2_01').replace('LC1_INSTALLED','LC2_INSTALLED')
s=s.replace('-ne 17','-ne 5').replace('files=17','files=5').replace('replacements=15;additions=2','replacements=5;additions=0')
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cnotin @("+','.join("'"+f['target']+"'" for f in changes)+")){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x') as f:f.write('\n'.join(lines)+'\n')
s=(W/'prealpha/loading_cover_lc1/test_deploy_01.py').read_text().replace("O=H/'candidate_04'","O=H/'candidate_01'").replace("'-TestFailAfter','15'","'-TestFailAfter','2'").replace('interrupted_after_addition','interrupted_after_replacement')
with (H/'test_deploy_01.py').open('x') as f:f.write(s)
targets={str((G/f['target']).resolve()).lower() for f in changes};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and str(p.resolve()).lower() not in targets:
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'compile_02/result.json',C/'compile_02/cache/compiled.redscripts',C/'native_01.json',C/'native_phase.json',C/'catalogue_binding_01.json']+list((C/'diagnosis_01').iterdir())
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/loading_cover_lc2_01'),'files':changes,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','archive_resources_changed':1,'framework_changes':0,'save_edits':0}
out=C/'install_manifest_01.json'
with out.open('x') as f:json.dump(m,f,indent=2);f.write('\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':'PACKAGE_PINNED','files':5,'protected':len(protected),'saves':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(out)}))
