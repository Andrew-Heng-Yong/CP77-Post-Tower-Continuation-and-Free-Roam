"""Current full script stack, workspace-only CLI preflight then SCC/readback."""
from pathlib import Path
import json,hashlib,re,shutil,subprocess,sys
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
O=C/sys.argv[1];O.mkdir(exist_ok=False);S=O/'scripts';cache=O/'cache';cache.mkdir()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
inputs={};deferred=[]
for name,root in [('game',G/'r6/scripts'),('Codeware',G/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',G/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',G/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',G/'red4ext/plugins/mod_settings')]:
 for p in root.rglob('*.reds'):
  inputs[str(p)]=sha(p);candidate=C/'package'/p.relative_to(G);src=candidate if candidate.exists() else p
  dest=S/name/p.relative_to(root)
  if 'EquipmentEx' in p.parts:deferred.append((src,dest));continue
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
for p in (C/'package/r6/scripts').rglob('*.reds'):
 dest=S/'game'/p.relative_to(C/'package/r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for p in (G/'r6/cache').iterdir():
 if p.is_file():inputs[str(p)]=sha(p)
for name in ['final.redscripts','final.redscripts.ts']:shutil.copyfile(G/'r6/cache'/name,cache/name)
cli=W/'diagnostics/mod_updates_20261023_01/downloads/redscript-cli.exe'
def run(args,label):
 r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=240)
 log=r.stdout+r.stderr;(O/(label+'.log')).write_text(log,encoding='utf-8')
 assert r.returncode==0 and not re.search(r'(?m)^\[?ERROR\b',log),log[-9000:]
 assert 'Output successfully saved' in log
 return log
run([cli,'compile','-s',S,'-b',cache/'final.redscripts','-o',cache/'cli.redscripts'],'cli')
print('CLI preflight passed.',flush=True)
for src,dst in deferred:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
paths=O/'compile_paths.txt';paths.write_text('')
log=run([G/'engine/tools/scc.exe','-compile',S,'-compilePathsFile',paths,'-customCacheDir',cache,'-outputCacheFile',cache/'compiled.redscripts',cache/'final.redscripts'],'scc')
assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
run([cli,'decompile','-i',cache/'compiled.redscripts','-o',O/'compiled.script'],'decompile')
text=(O/'compiled.script').read_text(encoding='utf-8-sig')
for name in ['PTFR.SideJobsS29.SideJobsS29','FreshS29','PTFR.HistorySnapshotHS1.SnapshotStateHS1','PTFR.HistorySnapshotHS1.SnapshotRecoveryHS1','PTFR.HistorySnapshotHS1.SnapshotDataHS1','EquipmentEx.OutfitSystem.GetInstance','PTFR.LoadingCoverLC1.StartupCoverLC1','PTFR.LoadingCoverLC1.SetupPopupLC1','PTFR.RestrictionsR1.CyberwareDiagnosticsCD1','PTFRCF1PreservesExactItem']:
 assert name in text,name
for p,h in inputs.items():assert sha(Path(p))==h,p
report={'status':'PASS_FULL_SCC_NOT_LIVE','sources':len(list(S.rglob('*.reds'))),'full_scc_equipmentex':True,'input_hashes':inputs,'compiled_sha256':sha(cache/'compiled.redscripts')}
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'}),flush=True)
