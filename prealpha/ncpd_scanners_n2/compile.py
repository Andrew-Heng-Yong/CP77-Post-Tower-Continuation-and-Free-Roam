"""Compile the added admission reader with the installed scripts, in workspace caches."""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import sha
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def main(revision):
 build=ROOT/'prealpha/ncpd_scanners_n2/build'/revision
 dest=build/'compile_result.json';assert not dest.exists()
 stage=Path(tempfile.mkdtemp(prefix='compile_',dir=build));cache=stage/'cache';cache.mkdir()
 protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
 for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
 source=stage/'scripts/TowerContinued_NCPD_N2';source.mkdir(parents=True);shutil.copy2(build/'ScannerAdmissionN2.reds',source/'ScannerAdmissionN2.reds')
 deps={}
 for p in (GAME/'r6/scripts').rglob('*.reds'):
  deps[str(p)]=sha(p);target=stage/'scripts'/p.relative_to(GAME/'r6/scripts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
 for folder in plugins:
  for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
 cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
 # The bundled CLI predates an EquipmentEx temporary-value expression. Use
 # the same PTFR+Codeware CLI scope as PA6; SCC below includes EVERY mod.
 args=[str(cli),'compile','-s',str(source),'-s',str(stage/'scripts/PTFR_PreAlpha'),'-s',str(GAME/'red4ext/plugins/Codeware/Scripts')]
 args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
 def run(args,name,seconds=120):
  r=subprocess.run(args,capture_output=True,text=True,timeout=seconds);log=r.stdout+r.stderr;(stage/name).write_text(log,encoding='utf-8')
  assert r.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:]
  return log
 run(args,'headless.log')
 paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n')
 compiled=cache/'compiled.redscripts'
 log=run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],'scc.log')
 assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
 flat=stage/'compiled.script';run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],'decompile.log')
 text=re.sub(r'\$local\$\d+','',flat.read_text(encoding='utf-8-sig'))
 for token in ('PTFR.NCPDScannersN2.ScannerAdmissionN2','GetPointOfInterestMappinSavedState(Cast<Uint32>(jm.GetEntryHash(entry))','this.Check("ma_cct_cpz_16")','this.Check("ma_wbr_nok_05")','EquipmentEx.OutfitSystem.GetInstance'):
  assert token in text,token
 for p,h in {**protected,**deps}.items():assert sha(p)==h,p
 report={'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'compiler_sha256':sha(Path(__file__)),'script_sha256':sha(build/'ScannerAdmissionN2.reds'),'compiled_sha256':sha(compiled),'stage':str(stage),'combined_cli':True,'full_scc':True,'equipmentex':True,'body_readback':True,'protected':protected,'dependencies':deps,'live_files_unchanged':True}
 dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('protected','dependencies')},indent=2))
if __name__=='__main__':main(sys.argv[1])
