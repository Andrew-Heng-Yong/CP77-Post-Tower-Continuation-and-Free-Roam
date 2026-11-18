"""Compile all currently registered sources with the single safety-driver change."""
from pathlib import Path
import shutil,subprocess
from prepare import WORK,WS,SCRIPT,read,sha,write,plain,baseline

def main():
 b=baseline();game=Path(b['game_root']);pins=read(WORK/'inputs.json')
 sources={p for root in ('r6/scripts','red4ext/plugins') for p in (game/root).rglob('*.reds')}
 previous=read(WS/'prealpha/mid_quest_resume_retire_20261115_01/stage_06/compile/assessment.json')
 assert len(sources)==148 and {p.relative_to(game).as_posix() for p in sources}==set(previous['staged'])
 registry=None
 for path in sorted((game/'r6/logs').glob('redscript*.log'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
  txt=path.read_text(encoding='utf-8-sig',errors='replace')
  recorded={(game/'r6/scripts'/line.strip()).resolve() for line in txt.splitlines() if line.strip().lower().endswith('.reds')}
  if recorded==sources and 'Compilation complete' in txt:registry=path;break
 assert registry,'Current registered source inventory unavailable'
 compiler=game/'engine/tools/scc.exe';caches=[game/'r6/cache'/n for n in ('final.redscripts','final.redscripts.ts')]
 inputs={p:sha(p) for p in sorted(sources|{registry,compiler,*caches})}
 out=WORK/'compile_01';out.mkdir();(out/'cache').mkdir()
 for p in caches:shutil.copyfile(p,out/'cache'/p.name)
 staged={}
 for p in sorted(sources):
  plain(p);rel=p.relative_to(game).as_posix()
  assert sha(p)==previous['staged'][rel],f'Existing source drift: {rel}'
  src=Path(pins['script']['path']) if rel==SCRIPT else p
  if rel==SCRIPT:assert sha(src)==pins['script']['after']
  dst=out/'scripts'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);staged[rel]=sha(dst)
 paths=out/'compile_paths.txt';paths.write_bytes(b'')
 image=out/'cache/compiled.redscripts'
 command=[compiler,'-compile',out/'scripts','-compilePathsFile',paths,'-customCacheDir',out/'cache','-outputCacheFile',image,out/'cache/final.redscripts']
 result=subprocess.run(list(map(str,command)),capture_output=True,encoding='utf-8',errors='replace',timeout=140,creationflags=subprocess.CREATE_NO_WINDOW)
 log=result.stdout+result.stderr;(out/'scc.log').write_text(log,encoding='utf-8')
 assert result.returncode==0 and 'Compilation complete' in log and image.is_file(),log[-10000:]
 assert all(sha(p)==h for p,h in inputs.items()),'Compiler inputs changed'
 assert set(p for p in staged if staged[p]!=previous['staged'][p])=={SCRIPT}
 write(out/'assessment.json',dict(status='PASS',sources=148,staged=staged,input_pins={str(p):h for p,h in inputs.items()},compiled_sha256=sha(image),changed_sources=[SCRIPT],game_writes=0))
 print('PASS: all 148 registered REDscript sources compiled with the single world-safety driver change.')
if __name__=='__main__':main()
