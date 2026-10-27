"""Compile the full candidate/current framework stack entirely in workspace."""
import shutil,subprocess
from common import *
O=HERE/'compile_01';assert not O.exists();O.mkdir()
S=O/'scripts';C=O/'cache';C.mkdir();pins={}
for name,root in [('game',GAME/'r6/scripts'),('Codeware',GAME/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',GAME/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',GAME/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',GAME/'red4ext/plugins/mod_settings')]:
    for p in root.rglob('*.reds'):
        pins[str(p)]=sha(p)
        dest=S/name/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (CANDIDATE/'package/r6/scripts').rglob('*.reds'):
    dest=S/'game'/p.relative_to(CANDIDATE/'package/r6/scripts')
    assert dest.is_file(),dest
    shutil.copyfile(p,dest)
for name in ('final.redscripts','final.redscripts.ts'):shutil.copyfile(GAME/'r6/cache'/name,C/name)
paths=O/'compile_paths.txt';paths.write_text('',encoding='utf-8')
command=[GAME/'engine/tools/scc.exe','-compile',S,'-compilePathsFile',paths,'-customCacheDir',C,'-outputCacheFile',C/'compiled.redscripts',C/'final.redscripts']
r=subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=240)
log=r.stdout+r.stderr;(O/'scc.log').write_text(log,encoding='utf-8')
for p,digest in pins.items():assert sha(Path(p))==digest,p
proof={'status':'PASS' if r.returncode==0 and 'Compilation complete' in log else 'FAIL','source_count':len(list(S.rglob('*.reds'))),'exit_code':r.returncode,'tail':log[-3500:],'compiled_sha256':sha(C/'compiled.redscripts'),'installed_source_pins':pins,'game_writes':0,'save_writes':0}
write_new(O/'result.json',proof)
print(json.dumps({k:v for k,v in proof.items() if k!='installed_source_pins'}))
assert proof['status']=='PASS'
