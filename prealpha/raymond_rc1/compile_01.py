"""Compile the 51-file RC1 successor against the currently installed public stack."""
import hashlib, json, shutil, subprocess
from pathlib import Path

H=Path(__file__).resolve().parent
W=H.parent.parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
O=H/'compile_01'
assert not O.exists(), O
O.mkdir()
S=O/'scripts'
C=O/'cache'
C.mkdir()
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()
pins={}
for name,root in [('game',G/'r6/scripts'),('Codeware',G/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',G/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',G/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',G/'red4ext/plugins/mod_settings')]:
    for p in root.rglob('*.reds'):
        pins[str(p)]=sha(p)
        dest=S/name/p.relative_to(root)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
target=S/'game/PTFR_Consolidated/PTFR_SideJobsS29.reds'
old=target.read_text(encoding='utf-8')
new=(H/'candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds').read_text(encoding='utf-8')
needle='public static func FactMax5() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }'
replacement='public static func FactMax5() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }'
needle=next(line for line in old.splitlines() if 'public static func FactMax5()' in line)
assert needle.count('0')==14 and old.count(needle)==1
replacement=needle.replace('return [0,','return [1,',1)
assert new==old.replace(needle,replacement)
shutil.copyfile(H/'candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds',target)
for name in ('final.redscripts','final.redscripts.ts'):
    shutil.copyfile(G/'r6/cache'/name,C/name)
paths=O/'compile_paths.txt'
paths.write_text('',encoding='utf-8')
command=[G/'engine/tools/scc.exe','-compile',S,'-compilePathsFile',paths,'-customCacheDir',C,'-outputCacheFile',C/'compiled.redscripts',C/'final.redscripts']
r=subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=240)
log=r.stdout+r.stderr
(O/'scc.log').write_text(log,encoding='utf-8')
for p,digest in pins.items():
    assert sha(Path(p))==digest,p
proof={'status':'PASS' if r.returncode==0 and 'Compilation complete' in log else 'FAIL','source_count':len(list(S.rglob('*.reds'))),'exit_code':r.returncode,'tail':log[-2000:],'scc_sha256':sha(C/'compiled.redscripts') if (C/'compiled.redscripts').exists() else None,'game_writes':0,'save_writes':0}
(O/'result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
assert proof['status']=='PASS'
