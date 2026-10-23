"""Exact Casius allowlist extension, preserving the installed R1 evidence."""
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

import test_restrictions_r1 as r1

OUT = r1.ROOT / 'research/restriction_profiles/tattoo_whitelist_r1_1'
OLD = 'return id == t"Items.AdvancedCasiusTattoo" ||'
NEW = 'return id == t"Items.CasiusTattoo" || id == t"Items.AdvancedCasiusTattoo" ||'


def verify(sources, installed):
    assert sources.keys() == installed.keys()
    core = sources['CyberwarePolicy.reds']
    assert core.count(NEW) == 1
    previous = dict(sources)
    previous['CyberwarePolicy.reds'] = core.replace(NEW, OLD)
    assert previous == installed, 'Only the exact allowlist extension may change'
    original, areas = r1.verify(previous)
    approved = re.findall(r't"(Items\.[^"]+)"', r1.function(core, 'Approved'))
    assert len(approved) == 13 and set(approved) == set(original) | {'Items.CasiusTattoo'}
    policy = json.loads(r1.read(r1.ROOT / 'research/restriction_profiles/whitelist.json'))
    tattoo = next(x for x in policy['approved_model_details'] if x['category'] == 'Hands')
    assert tattoo['records'] == ['Items.CasiusTattoo', 'Items.AdvancedCasiusTattoo']
    audit = json.loads(r1.read(r1.ROOT / 'research/restriction_profiles/tattoo_r1_diagnosis/parts_records.json'))
    records = {x['name']: x for x in audit['records']}
    for name in tattoo['records']:
        assert records[name]['type'] == 'gamedataItem_Record'
        assert records[name]['fields']['equipArea']['name'] == 'EquipmentArea.HandsCW'
    assert not {'Items.SilverhandTattoo', 'Items.AdvancedSilverhandTattoo',
                'Items.AdvancedYakuzaTattoo', 'Items.AdvancedSmartLinkLegendary',
                'Items.MaskCW', 'Items.MaskCWPlus', 'Items.MaskCWPlusPlus'} & set(approved)
    return approved, areas


def main():
    OUT.mkdir(exist_ok=True)
    receipt_path = r1.OUT / 'install_receipt.json'
    receipt = json.loads(r1.read(receipt_path))
    installed = {}
    protected = {str(receipt_path): r1.sha(receipt_path), str(r1.OUT / 'tests.json'): r1.sha(r1.OUT / 'tests.json')}
    for entry in receipt['files']:
        path = r1.GAME / entry['relative']
        assert r1.sha(path) == entry['sha256'], 'Installed R1 has changed'
        installed[path.name] = r1.read(path)
        protected[str(path)] = r1.sha(path)
    sources = {p.name: r1.read(p) for p in r1.SRC.glob('*.reds')}
    approved, areas = verify(sources, installed)
    mutants = [NEW.replace('Items.CasiusTattoo', name) for name in
               ('Items.SilverhandTattoo', 'Items.AdvancedCasiusTattoo', 'Items.AdvancedYakuzaTattoo')]
    mutants.append(OLD)
    for replacement in mutants:
        mutant = dict(sources)
        mutant['CyberwarePolicy.reds'] = mutant['CyberwarePolicy.reds'].replace(NEW, replacement)
        try:
            verify(mutant, installed)
        except AssertionError:
            pass
        else:
            raise AssertionError('Accepted wrong/absent tattoo exemption')
    base = r1.GAME / 'r6/cache/final.redscripts'
    for name in ('final.redscripts', 'final.redscripts.ts'):
        path = r1.GAME / 'r6/cache' / name
        protected[str(path)] = r1.sha(path)
    assert r1.sha(base) == '2119046F3F3466206D8A16A4803B0EF0F3C90926AB689F9ABBD5B8E42E28EE86'
    cli = r1.ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    quick = subprocess.run([str(cli), 'compile', '-s', str(r1.SRC), '-s', str(r1.GAME / 'red4ext/plugins/Codeware/Scripts'),
                            '-b', str(base), '-o', str(OUT / 'compile.redscripts')], capture_output=True, text=True, timeout=30)
    quick_log = quick.stdout + quick.stderr
    assert 'Output successfully saved' in quick_log and 'ERROR' not in quick_log, quick_log
    # Stage installed scripts without the old policy to avoid duplicate classes.
    # A fresh directory prevents stale source files from entering repeat builds.
    stage = r1.Path(tempfile.mkdtemp(prefix='compile_', dir=OUT))
    dependencies = {}
    for path in (r1.GAME / 'r6/scripts').rglob('*.reds'):
        relative = path.relative_to(r1.GAME / 'r6/scripts')
        if relative.parts[0] == 'PTFR_Restrictions_R1':
            continue
        target = stage / 'scripts' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        dependencies[str(path)] = r1.sha(path)
        shutil.copy2(path, target)
        assert r1.sha(target) == dependencies[str(path)]
    plugin_paths = r1.read(r1.OUT / 'compile_paths.txt').splitlines()[2:]
    for directory in plugin_paths:
        for path in r1.Path(directory).rglob('*.reds'):
            dependencies[str(path)] = r1.sha(path)
    paths_file = stage / 'compile_paths.txt'
    paths_file.write_text('\n'.join([str(r1.SRC), str(stage / 'scripts')] + plugin_paths) + '\n', encoding='utf-8')
    cache = stage / 'cache'
    cache.mkdir()
    for name in ('final.redscripts', 'final.redscripts.ts'):
        shutil.copy2(r1.GAME / 'r6/cache' / name, cache / name)
    scc = r1.GAME / 'engine/tools/scc.exe'
    run = subprocess.run([str(scc), '-compile', str(r1.SRC), '-compilePathsFile', str(paths_file),
                          '-customCacheDir', str(cache), '-outputCacheFile', str(cache / 'compiled.redscripts'),
                          str(cache / 'final.redscripts')], cwd=r1.ROOT, capture_output=True, text=True, timeout=90)
    log = run.stdout + run.stderr
    (OUT / 'compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log, log[-6000:]
    assert 'EquipmentEx.reds' in log and 'CyberwarePolicy.reds' in log
    flat = OUT / 'compiled_flat.script'
    decompile = subprocess.run([str(cli), 'decompile', '-i', str(cache / 'compiled.redscripts'), '-o', str(flat)],
                               capture_output=True, text=True, timeout=30)
    assert 'Output successfully saved' in decompile.stdout + decompile.stderr
    compiled = r1.read(flat)
    # Function bodies are inspected from the actual compiled/decompiled output.
    assert set(re.findall(r't"(Items\.[^"]+)"', r1.function(compiled, 'Approved'))) == set(approved)
    for symbol in ('func PTFRR1Remove(', 'func OnPTFRR1BuyClosed(', 'EquipmentEx.OutfitSystem.GetInstance'):
        assert symbol in compiled
    for path, expected in {**protected, **dependencies}.items():
        assert r1.sha(r1.Path(path)) == expected, 'Read-only input changed: ' + path
    result = dict(status='PASS_CASIUS_WHITELIST_WORKSPACE_ONLY', utc=datetime.now(timezone.utc).isoformat(),
                  approved_records=approved, restricted_areas=areas, exact_one_line_runtime_delta=True,
                  source_mutants_rejected=len(mutants), r1_invariants_unchanged=True,
                  equipmentex_full_compile=True, compiled_allowlist_readback=True,
                  candidate_sha256=r1.sha(r1.SRC / 'CyberwarePolicy.reds'),
                  compiled_sha256=r1.sha(cache / 'compiled.redscripts'),
                  preserved_inputs=protected, dependency_hashes=dependencies,
                  installed=False, live_tested=False, game_writes=0, save_writes=0)
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('preserved_inputs', 'dependency_hashes')}, indent=2))


if __name__ == '__main__':
    main()
