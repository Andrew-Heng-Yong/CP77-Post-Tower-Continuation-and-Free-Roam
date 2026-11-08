"""Fresh complete-input offline SCC for an approved QR13 staged successor."""
from pathlib import Path
import hashlib,json,shutil,stat,subprocess
H=Path(__file__).resolve().parent
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def safe(p):
 for v in(p,*p.parents):
  s=v.lstat();assert not stat.S_ISLNK(s.st_mode)and not(getattr(s,'st_file_attributes',0)&0x400)
def main():
 c=H/'candidate_01';approval=read(c/'promotion.json');assert approval['status']=='SOURCE_CHANGES_APPROVED_PENDING_PACKAGE'
 o=H/'verification/compile_01';assert not o.exists();scripts=o/'scripts';cache=o/'cache';cache.mkdir(parents=True)
 roots=[('game',GAME/'r6/scripts'),('Codeware',GAME/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',GAME/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',GAME/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',GAME/'red4ext/plugins/mod_settings')]
 pins={};staged={}
 for group,root in roots:
  safe(root);assert root.is_dir()
  for p in sorted(root.rglob('*.reds')):
   safe(p);pins[str(p)]=sha(p);dest=scripts/group/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(dest)==pins[str(p)]
 for p in sorted((c/'package/r6/scripts').rglob('*.reds')):
  rel=p.relative_to(c/'package/r6/scripts');dest=scripts/'game'/rel;assert dest.exists(),'Candidate missing installed source identity'
  shutil.copyfile(p,dest);assert sha(dest)==sha(p)
 for name in ['final.redscripts','final.redscripts.ts']:
  p=GAME/'r6/cache'/name;safe(p);pins[str(p)]=sha(p);shutil.copyfile(p,cache/name)
 exe=GAME/'engine/tools/scc.exe';pins[str(exe)]=sha(exe);paths=o/'compile_paths.txt';paths.write_text('',encoding='utf-8')
 cmd=list(map(str,[exe,'-compile',scripts,'-compilePathsFile',paths,'-customCacheDir',cache,'-outputCacheFile',cache/'compiled.redscripts',cache/'final.redscripts']))
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=300);log=result.stdout+result.stderr;(o/'scc.log').write_text(log,encoding='utf-8')
 unchanged=all(sha(p)==v for p,v in pins.items());assert unchanged,'Installed compiler inputs changed'
 staged={str(p):sha(p)for p in scripts.rglob('*.reds')}
 good=result.returncode==0 and'Compilation complete'in log and(cache/'compiled.redscripts').exists()
 report={'status':'PASS_COMPLETE_INPUT_OFFLINE_COMPILE'if good else'FAIL_OFFLINE_COMPILE','command':cmd,'exit_code':result.returncode,'input_pins':pins,'staged_sources':staged,'source_count':len(staged),
   'candidate_managed_source_count':len(list((c/'package/r6/scripts').rglob('*.reds'))),'compiled_sha256':sha(cache/'compiled.redscripts')if(cache/'compiled.redscripts').exists()else None,
   'installed_inputs_unchanged':unchanged,'game_writes':0,'save_writes':0,'promotion_sha256':sha(c/'promotion.json')}
 (o/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');assert good,log[-5000:]
 print({'status':report['status'],'sources':len(staged),'managed':report['candidate_managed_source_count'],'compiled_sha256':report['compiled_sha256']})
if __name__=='__main__':main()
