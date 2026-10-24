from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
tests=read(C/'tests_01.json');assert tests['status']=='PASS_LC3_COMPILED_NATIVE_FEEDBACK_NOT_LIVE'
for path,h in tests['sources'].items():assert sha(path)==h
changes=read(C/'changes_01.json');native=read(C/'native_01.json');changes.append({k:native[k] for k in ['target','before','after']});assert len(changes)==3
for f in changes:assert sha(G/f['target'])==sha(C/'before'/f['target'])==f['before'] and sha(C/'package'/f['target'])==f['after']
s=(W/'prealpha/startup_crash_sc1/deploy_01.ps1').read_text().replace('startup_crash_sc1_01','loading_cover_lc3_01').replace('SC1_INSTALLED','LC3_INSTALLED')
s=s.replace('-ne 1','-ne 3').replace('files=1','files=3').replace('replacements=1','replacements=3')
lines=s.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l);lines[i]=" if($f.target -cnotin @("+','.join("'"+f['target']+"'" for f in changes)+")){throw 'Unexpected target scope'}"
with (H/'deploy_01.ps1').open('x') as out:out.write('\n'.join(lines)+'\n')
s=(W/'prealpha/startup_crash_sc1/test_deploy_01.py').read_text().replace("'-TestFailAfter','1'","'-TestFailAfter','2'")
with (H/'test_deploy_01.py').open('x') as out:out.write(s)
targets={(G/f['target']).resolve() for f in changes};protected=[]
for root in [G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S]:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ['.log','.jsonl','.dmp'] and p.resolve() not in targets:protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'native_01.json',C/'prepared_native_01.json',C/'changes_01.json',C/'compile_01/result.json',C/'compile_01/cache/compiled.redscripts',C/'diagnosis_01/inputs.json',C/'diagnosis_01/assessment_01.json']
proofs+=list((C/'prepared_native_01').glob('*.json'))+list((C/'readback_01').glob('*.json'))
m={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/loading_cover_lc3_01'),'files':changes,'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'pending','changed_private_scenes':4,'unchanged_archive_resources':13,'framework_changes':0,'save_edits':0}
out=C/'install_manifest_01.json'
with out.open('x') as f:json.dump(m,f,indent=2);f.write('\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':'LC3_PACKAGE_PINNED','files':3,'protected':len(protected),'save_files':sum(p['kind']=='save' for p in protected),'manifest_sha256':sha(out)}))
