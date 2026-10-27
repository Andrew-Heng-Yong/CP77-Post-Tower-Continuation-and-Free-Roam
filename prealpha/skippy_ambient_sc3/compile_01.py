"""Compile SC3's one changed S23 source against installed public Codeware."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess

H=Path(__file__).resolve().parent
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
OUT=H/'candidate_01/compile_01'
assert not OUT.exists()
S,C=OUT/'scripts',OUT/'cache'
C.mkdir(parents=True)
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
pins={}
for name,root in (('game',GAME/'r6/scripts'),('Codeware',GAME/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',GAME/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',GAME/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',GAME/'red4ext/plugins/mod_settings')):
 for path in root.rglob('*.reds'):
  pins[str(path)]=digest(path)
  target=S/name/path.relative_to(root)
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(path,target)
candidate=H/'candidate_01/script_source/PTFR_SideJobsS23.reds'
target=S/'game/PTFR_Consolidated/PTFR_SideJobsS23.reds'
assert target.exists()
replaced=digest(target)
shutil.copyfile(candidate,target)
for name in ('final.redscripts','final.redscripts.ts'):shutil.copyfile(GAME/'r6/cache'/name,C/name)
paths=OUT/'compile_paths.txt';paths.write_text('')
cmd=[GAME/'engine/tools/scc.exe','-compile',S,'-compilePathsFile',paths,'-customCacheDir',C,'-outputCacheFile',C/'compiled.redscripts',C/'final.redscripts']
r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=300)
log=r.stdout+r.stderr
(OUT/'scc.log').write_text(log)
assert all(digest(Path(p))==h for p,h in pins.items())
proof={'status':'PASS' if r.returncode==0 and 'Compilation complete' in log else 'FAIL','exit_code':r.returncode,'source_count':len(list(S.rglob('*.reds'))),'candidate_sha256':digest(candidate),'replaced_sha256':replaced,'installed_source_hashes_unchanged':True,'game_writes':0,'save_writes':0,'log_tail':log[-3000:]}
(OUT/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({k:proof[k] for k in ('status','exit_code','source_count','candidate_sha256')}))
assert proof['status']=='PASS'
