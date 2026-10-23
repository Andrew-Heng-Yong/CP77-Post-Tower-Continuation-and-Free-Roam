"""Compile only in workspace copies; installed scripts and caches stay untouched."""
import json,re,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import sha
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')

def main(revision):
 build=Path(__file__).resolve().parent/'build'/revision;dest=build/'compile_result.json'
 assert not dest.exists()
 stage=Path(tempfile.mkdtemp(prefix='compile_',dir=build));cache=stage/'cache';cache.mkdir()
 protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
 for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
 deps={}
 for p in (GAME/'r6/scripts').rglob('*.reds'):
  deps[str(p)]=sha(p);target=stage/'scripts'/p.relative_to(GAME/'r6/scripts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 source=stage/'scripts/TowerContinued_NCPD_N21';source.mkdir()
 shutil.copy2(build/'ScannerRepairN21.reds',source/'ScannerRepairN21.reds')
 plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
 for folder in plugins:
  for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
 cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
 def run(args,name):
  r=subprocess.run(args,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(stage/name).write_text(log,encoding='utf-8')
  assert r.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-10000:]
  return log
 args=[str(cli),'compile']
 for p in [source,stage/'scripts/PTFR_PreAlpha',stage/'scripts/TowerContinued_NCPD_N2',GAME/'red4ext/plugins/Codeware/Scripts']:args+=['-s',str(p)]
 args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
 run(args,'headless.log')
 paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n')
 compiled=cache/'compiled.redscripts'
 log=run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],'scc.log')
 assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
 flat=stage/'compiled.script';run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],'decompile.log')
 text=re.sub(r'\$local\$\d+','',flat.read_text(encoding='utf-8-sig'))
 for token in ['PTFR.NCPDRepairN21.ScannerRepairN21','this.Permit(i)','this.Activate(i)','this.Fact("PTFRN2_" + id + "_Issued") != 1','ScannerDataN21.Finish(i)','JournalNotifyOption.DoNotNotify','EquipmentEx.OutfitSystem.GetInstance']:
  assert token in text,token
 for p,h in {**protected,**deps}.items():assert sha(p)==h,p
 report={'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'compiler_sha256':sha(Path(__file__)),'script_sha256':sha(build/'ScannerRepairN21.reds'),'compiled_sha256':sha(compiled),'stage':str(stage),'combined_cli':True,'full_scc':True,'equipmentex':True,'body_readback':True,'protected':protected,'dependencies':deps,'live_files_unchanged':True}
 dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('protected','dependencies')},indent=2))

if __name__=='__main__':main(sys.argv[1])
