"""Compile workspace R3 with both compilers, without touching installed caches."""
import hashlib, json, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
OUT = ROOT / 'research/restriction_profiles/profile_r3'
SOURCES = [ROOT / f'redscript/PTFR_Restrictions_R{i}' for i in (1, 2, 3)]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def compile_all():
    OUT.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='compile_', dir=OUT))
    cache = stage / 'cache'; cache.mkdir()
    protected = {str(p): sha(p) for p in (GAME / 'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts', 'final.redscripts.ts'):
        shutil.copy2(GAME / 'r6/cache' / name, cache / name)
    dependencies = {}
    for p in (GAME / 'r6/scripts').rglob('*.reds'):
        rel = p.relative_to(GAME / 'r6/scripts')
        if rel.parts[0] in [s.name for s in SOURCES]: continue
        target = stage / 'scripts' / rel; target.parent.mkdir(parents=True, exist_ok=True)
        dependencies[str(p)] = sha(p); shutil.copy2(p, target)
    plugins = (ROOT / 'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for directory in plugins:
        for p in Path(directory).rglob('*.reds'): dependencies[str(p)] = sha(p)
    cli = ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args = [str(cli), 'compile']
    for s in SOURCES + [GAME / 'red4ext/plugins/Codeware/Scripts']: args += ['-s', str(s)]
    args += ['-b', str(cache / 'final.redscripts'), '-o', str(stage / 'headless.redscripts')]
    run = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=90)
    log = run.stdout + run.stderr; (OUT / 'headless_compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Output successfully saved' in log and 'ERROR' not in log, log[-18000:]
    paths = stage / 'compile_paths.txt'
    paths.write_text('\n'.join(map(str, SOURCES + [stage / 'scripts'] + list(map(Path, plugins)))) + '\n', encoding='utf-8')
    compiled = cache / 'compiled.redscripts'
    run = subprocess.run([str(GAME / 'engine/tools/scc.exe'), '-compile', str(SOURCES[-1]), '-compilePathsFile', str(paths),
                          '-customCacheDir', str(cache), '-outputCacheFile', str(compiled), str(cache / 'final.redscripts')],
                         cwd=ROOT, capture_output=True, text=True, timeout=90)
    log = run.stdout + run.stderr; (OUT / 'compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log, log[-18000:]
    assert 'EquipmentEx.reds' in log
    flat = OUT / 'compiled_flat.script'
    run = subprocess.run([str(cli), 'decompile', '-i', str(compiled), '-o', str(flat)], capture_output=True, text=True, timeout=60)
    assert 'Output successfully saved' in run.stdout + run.stderr
    text = flat.read_text(encoding='utf-8-sig')
    for symbol in ('func PTFRR3SellPerk(', 'func FullNerf(', 'func PTFRR3MoveTattooToFirst(', 'EquipmentEx.OutfitSystem.GetInstance',
                   'class PTFR.RestrictionsR3.ProfilePhysical', 'func PTFRR3StartBodyRelic('): assert symbol in text, symbol
    for p, digest in {**protected, **dependencies}.items(): assert sha(p) == digest, p
    result = dict(status='PASS_COMPILE_ONLY_NOT_RUNTIME', compiled_sha256=sha(compiled), compiled_path=str(compiled),
                  flat_sha256=sha(flat), dependency_hashes=dependencies, protected_inputs=protected,
                  dependency_roots=[str(GAME / 'r6/scripts')] + plugins, equipmentex_full_compile=True,
                  checked_sources={str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for s in SOURCES for p in s.glob('*.reds')})
    (OUT / 'compile_result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','compiled_path','compiled_sha256')}, indent=2))
    return result
if __name__ == '__main__': compile_all()
