"""Fresh full-input SCC compile; installed sources/cache are read-only inputs."""
import sys,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import *
b=read(H/'baseline.json');G=Path(b['game']);C=H/'candidate_01';O=C/'compile_01';assert not O.exists(),'Preserve compilation evidence'
S=O/'scripts';K=O/'cache';K.mkdir(parents=True);pins={};staged=[]
roots=[('game',G/'r6/scripts'),('Codeware',G/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',G/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',G/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',G/'red4ext/plugins/mod_settings')]
for name,root in roots:
 assert root.exists(),f'Missing dependency source root: {root}'
 for p in sorted(root.rglob('*.reds')):
  pins[str(p)]=sha(p);t=S/name/p.relative_to(root);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t);staged.append({'source':str(p),'staged':str(t),'sha256':sha(t)})
for r in b['package_files']:
 if r['path'].endswith('.reds'):
  target=S/'game'/Path(r['path']).relative_to('r6/scripts');assert target.exists();shutil.copyfile(C/'package'/r['path'],target)
for p in sorted(S.rglob('*.reds')):assert p.is_relative_to(O)
for name in ['final.redscripts','final.redscripts.ts']:
 p=G/'r6/cache'/name;pins[str(p)]=sha(p);shutil.copyfile(p,K/name)
exe=G/'engine/tools/scc.exe';pins[str(exe)]=sha(exe);paths=O/'compile_paths.txt';paths.write_text('',encoding='utf-8')
cmd=[exe,'-compile',S,'-compilePathsFile',paths,'-customCacheDir',K,'-outputCacheFile',K/'compiled.redscripts',K/'final.redscripts']
r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=300);log=r.stdout+r.stderr;(O/'scc.log').write_text(log,encoding='utf-8');unchanged=all(sha(p)==v for p,v in pins.items())
result={'status':'PASS' if r.returncode==0 and 'Compilation complete' in log and (K/'compiled.redscripts').exists() and unchanged else 'FAIL','exit_code':r.returncode,'source_count':len(staged),'installed_inputs_unchanged':unchanged,'compiled_sha256':sha(K/'compiled.redscripts') if (K/'compiled.redscripts').exists() else None,'command':list(map(str,cmd)),'input_pins':pins,'staged_sources':snapshot(S.rglob('*.reds')),'game_writes':0,'save_writes':0,'log_tail':log[-4500:]}
write(O/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('input_pins','staged_sources','command')},indent=2));assert result['status']=='PASS'
