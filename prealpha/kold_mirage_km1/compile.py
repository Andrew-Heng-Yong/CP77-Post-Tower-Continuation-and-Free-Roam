"""Compile the complete currently registered source inventory in isolation."""
from pathlib import Path
import shutil
import stat
import subprocess
from prepare import HERE, OUT, SCRIPT, read, sha, write


def safe(p):
    for q in (p,*p.parents):
        s=q.lstat()
        assert not stat.S_ISLNK(s.st_mode) and not s.st_file_attributes&0x400,q


def main():
    plan=read(HERE/'input_01/plan.json')
    game=Path(read(plan['installed_baseline'])['game_root'])
    out=HERE/'compile_01'
    assert not out.exists()
    log=game/'r6/logs/redscript_rCURRENT.log';safe(log)
    raw=log.read_bytes();log_sha=sha(log)
    registered=set()
    for line in raw.decode('utf-8-sig').splitlines():
        line=line.strip()
        if line.lower().endswith('.reds'):
            p=Path(line) if Path(line).is_absolute() else game/'r6/scripts'/line
            p=p.resolve();safe(p);assert p.is_relative_to(game)
            registered.add(p)
    roots=[('game',game/'r6/scripts'),('Codeware',game/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',game/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',game/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',game/'red4ext/plugins/mod_settings'),('LizziesBDs',game/'red4ext/plugins/LizziesBDs/Scripts')]
    found={p.resolve() for _,root in roots for p in root.rglob('*.reds')}
    all_sources={p.resolve() for parent in [game/'r6/scripts',game/'red4ext/plugins'] for p in parent.rglob('*.reds')}
    assert registered==found==all_sources,{'unregistered':list(map(str,found-registered)),'unknown_roots':list(map(str,all_sources-found))}
    out.mkdir();(out/'runtime_redscript.log').write_bytes(raw)
    scripts=out/'scripts';cache=out/'cache';cache.mkdir()
    pins={};origin={}
    for group,root in roots:
        safe(root)
        for p in sorted(root.rglob('*.reds')):
            safe(p);pins[str(p)]=sha(p)
            dest=scripts/group/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dest);assert sha(dest)==pins[str(p)];origin[str(p)]=str(dest)
    overlay=OUT/'package'/SCRIPT
    assert sha(overlay)==plan['script_after']
    dest=scripts/'game'/Path(SCRIPT).relative_to('r6/scripts')
    assert dest.exists() and sha(dest)==plan['script_before']
    shutil.copyfile(overlay,dest)
    for name in ['final.redscripts','final.redscripts.ts']:
        p=game/'r6/cache'/name;safe(p);pins[str(p)]=sha(p);shutil.copyfile(p,cache/name)
    exe=game/'engine/tools/scc.exe';safe(exe);pins[str(exe)]=sha(exe)
    paths=out/'compile_paths.txt';paths.write_text('',encoding='utf-8')
    command=list(map(str,[exe,'-compile',scripts,'-compilePathsFile',paths,'-customCacheDir',cache,'-outputCacheFile',cache/'compiled.redscripts',cache/'final.redscripts']))
    result=subprocess.run(command,capture_output=True,text=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    (out/'scc.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    assert all(sha(p)==s for p,s in pins.items()),'Installed compiler inputs changed'
    assert sha(log)==log_sha,'Runtime source registry changed'
    staged={str(p):sha(p) for p in scripts.rglob('*.reds')}
    good=result.returncode==0 and 'Compilation complete' in result.stdout+result.stderr and (cache/'compiled.redscripts').is_file()
    report={'status':'PASS_CURRENT_REGISTERED_SOURCE_COMPILE' if good else 'FAIL_COMPILE','command':command,'exit_code':result.returncode,'source_count':len(staged),'input_pins':pins,'runtime_log':{'path':str(log),'sha256':log_sha,'copy':str(out/'runtime_redscript.log')},'runtime_registered_sources':sorted(map(str,registered)),'source_origins':origin,'staged_sources':staged,'roots':[str(r) for _,r in roots],'overlay':{'path':SCRIPT,'sha256':sha(overlay)},'compiled_sha256':sha(cache/'compiled.redscripts') if good else None,'installed_inputs_unchanged':True,'game_writes':0,'save_writes':0}
    write(out/'result.json',report)
    print({'status':report['status'],'sources':len(staged),'compiler_inputs':len(pins),'compiled_sha256':report['compiled_sha256']})
    assert good,(result.stdout+result.stderr)[-4000:]


if __name__=='__main__':
    main()
