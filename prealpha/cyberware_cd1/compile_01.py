"""Compile the shipped alpha plus CD1 and local dependencies in the workspace."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,zipfile
from prepare_01 import ROOT,OUT,ZIP,EQUIP,COVER

GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DEST=OUT/(sys.argv[1] if len(sys.argv)>1 else 'compile_01')
DEST.mkdir(exist_ok=False)
SCRIPTS=DEST/'scripts';CACHE=DEST/'cache';CACHE.mkdir()
inputs={};deferred=[]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def copy(src,dst):
    inputs[str(src)]=digest(src);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)

for name,folder in [('game',GAME/'r6/scripts'),('Codeware',GAME/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',GAME/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',GAME/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',GAME/'red4ext/plugins/mod_settings')]:
    for src in folder.rglob('*.reds'):
        relative=src.relative_to(folder)
        if name=='game' and (relative.parts[0]=='PTFR_PreAlpha' or relative.parts[0].startswith('TowerContinued_')):continue
        dest=SCRIPTS/name/relative
        if 'EquipmentEx' in src.parts:deferred.append((src,dest));continue
        copy(src,dest)

with zipfile.ZipFile(ZIP) as z:
    for name in z.namelist():
        if not name.startswith('r6/scripts/') or not name.endswith('.reds'):continue
        dest=SCRIPTS/'game'/Path(name).relative_to('r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(z.read(name))
for src in (OUT/'package/r6/scripts').rglob('*.reds'):
    copy(src,SCRIPTS/'game'/src.relative_to(OUT/'package/r6/scripts'))
for name in ['final.redscripts','final.redscripts.ts']:copy(GAME/'r6/cache'/name,CACHE/name)
CLI=ROOT/'diagnostics/mod_updates_20261023_01/downloads/redscript-cli.exe'

def run(args,label):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=240)
    log=result.stdout+result.stderr;(DEST/(label+'.log')).write_text(log,encoding='utf-8')
    assert result.returncode==0 and not re.search(r'(?m)^\[?ERROR\b',log),log[-12000:]
    assert 'Output successfully saved' in log,log[-2000:]
    return log

run([CLI,'compile','-s',SCRIPTS,'-b',CACHE/'final.redscripts','-o',CACHE/'cli.redscripts'],'cli')
print('CLI preflight passed.',flush=True)
for src,dest in deferred:copy(src,dest)
paths=DEST/'compile_paths.txt';paths.write_text('')
log=run([GAME/'engine/tools/scc.exe','-compile',SCRIPTS,'-compilePathsFile',paths,'-customCacheDir',CACHE,'-outputCacheFile',CACHE/'compiled.redscripts',CACHE/'final.redscripts'],'scc')
assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
run([CLI,'decompile','-i',CACHE/'compiled.redscripts','-o',DEST/'compiled.script'],'decompile')
text=(DEST/'compiled.script').read_text(encoding='utf-8-sig')
for marker in ['CyberwareDiagnosticsCD1','FAIL item_or_quantity','FAIL part_count','FAIL part_identity_or_slot','Body/profile/cyberware fault:','Cyberware item-preservation check failed.','EquipmentEx.OutfitSystem.GetInstance']:
    assert marker in text,marker
for path,expected in inputs.items():assert digest(Path(path))==expected,path
report={'status':'PASS_FULL_SCC_NOT_LIVE','sources':len(list(SCRIPTS.rglob('*.reds'))),'base':'shipped v0.1.1 alpha scripts, not H5 development scripts','full_scc_equipmentex':True,'compiled_sha256':digest(CACHE/'compiled.redscripts'),'input_hashes':inputs,'game_writes':False}
(DEST/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'}),flush=True)
