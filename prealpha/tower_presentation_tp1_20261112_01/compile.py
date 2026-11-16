"""Compile a candidate against the complete currently registered source inventory."""
import argparse
import shutil
import subprocess
from pathlib import Path
from capture import HERE,BASELINE,BASELINE_SHA,sha,plain,write,read

def baseline():
    assert sha(BASELINE)==BASELINE_SHA
    manifest=read(BASELINE);game=Path(manifest['game_root'])
    for row in manifest['core_files']+manifest['required_files']:
        plain(game/row['path']);assert sha(game/row['path'])==row['sha256']
    return manifest,game


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
    package=HERE/args.candidate/'package';out=HERE/args.out
    assert package.parent.parent==HERE and package.is_dir() and out.parent==HERE and not out.exists()
    manifest,game=baseline()
    sources={p.resolve() for rel in ('r6/scripts','red4ext/plugins') for p in (game/rel).rglob('*.reds')}
    registry=None
    for p in sorted((game/'r6/logs').glob('redscript*.log'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
        text=p.read_text(encoding='utf-8-sig',errors='replace')
        registered={(game/'r6/scripts'/x.strip()).resolve() for x in text.splitlines() if x.strip().lower().endswith('.reds')}
        if 'Compilation complete' in text and registered==sources:registry=p;break
    assert registry is not None,'Current successful compiler log does not match the full filesystem source inventory'
    compiler=game/'engine/tools/scc.exe';caches=[game/'r6/cache'/n for n in ('final.redscripts','final.redscripts.ts')]
    pins={}
    for p in sorted(sources|{compiler,*caches}):plain(p);pins[p.relative_to(game).as_posix()]=sha(p)
    registry_sha=sha(registry);(out/'cache').mkdir(parents=True)
    for p in caches:shutil.copyfile(p,out/'cache'/p.name)
    staged={}
    for p in sorted(sources):
        rel=p.relative_to(game).as_posix();src=package/rel if (package/rel).is_file() else p
        dest=out/'scripts'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);staged[rel]=sha(dest)
    assert {p.relative_to(package).as_posix() for p in package.rglob('*.reds')}<=set(staged)
    paths=out/'compile_paths.txt';paths.write_bytes(b'');target=out/'cache/compiled.redscripts'
    command=[compiler,'-compile',out/'scripts','-compilePathsFile',paths,'-customCacheDir',out/'cache','-outputCacheFile',target,out/'cache/final.redscripts']
    result=subprocess.run(list(map(str,command)),capture_output=True,encoding='utf-8',errors='replace',timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    log=result.stdout+result.stderr;(out/'scc.log').write_text(log,encoding='utf-8')
    assert sha(registry)==registry_sha and all(sha(game/p)==h for p,h in pins.items())
    passed=result.returncode==0 and 'Compilation complete' in log and target.is_file()
    write(out/'result.json',{'status':'PASS' if passed else 'FAIL','source_count':len(staged),'input_pins':pins,'staged_hashes':staged,
        'registry':str(registry),'registry_sha256':registry_sha,'candidate':args.candidate,'compiled_sha256':sha(target) if passed else None})
    print(f'Offline compile {"PASS" if passed else "FAIL"}: {len(staged)} registered sources; installed inputs unchanged.')
    if not passed:raise RuntimeError(log[-10000:])


if __name__=='__main__':main()
