"""Compile the complete installed script set plus S28 in workspace copies."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s21_compile', ROOT / 'prealpha/sidejobs_s21/compile.py')
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
sha, body, block, GAME = prior.sha, prior.body, prior.block, prior.GAME


def compact(s):
    # The decompiler escapes apostrophes inside double-quoted string literals.
    return prior.compact(re.sub(r'PTFR\.(?:SideJobsS28|RestrictionsR2|RestrictionsR3)\.', '', s).replace("\\'", "'"))


def verify(text, source):
    owner = block(text, r'\bpublic class PTFR\.SideJobsS28\.SideJobsS28 extends ScriptableSystem\s*\{', 'compiled S28')
    data = block(text, r'\bpublic abstract class PTFR\.SideJobsS28\.SideJobDataS28 extends IScriptable\s*\{', 'compiled data')
    srcowner = block(source, r'\bpublic class SideJobsS28 extends ScriptableSystem\s*\{', 'source S28')
    srcdata = block(source, r'\bpublic abstract class SideJobDataS28\s*\{', 'source data')
    checked = []
    def need(name, *tokens):
        actual = compact(body(owner, name))
        for token in tokens:
            assert compact(token) in actual, (name, token)
        checked.append(name)
    for name in ['Common', 'Safe', 'FreshOwner', 'Ready', 'Fact', 'Own']:
        a = re.findall(r'\breturn\s+([^;]+);', body(owner, name))
        b = re.findall(r'\breturn\s+([^;]+);', body(srcowner, name))
        assert [compact(v) for v in a] == [compact(v) for v in b], name
        checked.append(name)
    need('Permit', '!IsDefined(qs)||this.Own(i,"Issued")!=0', 'Tag(i)+"_Permit"', 'qs.SetFactStr(name,value)')
    need('Restored', 'this.epoch+=1', 'ArrayClear(this.previous)', 'this.warmup=3',
         'if this.Own(i,"Issued")==0', 'this.Permit(i,false)')
    need('Read', '!IsDefined(jm)||!IsDefined(qs)||jm.HasAnyDelayedStateChanges()',
         'GetEntryByString(paths[k],classes[k])', 'IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1',
         'state!=first[k]&&state!=second[k]', 'actual<minimum[k]||actual>maximum[k]', 'sample.valid=false',
         'SideJobDataS28.ItemNames(i)', '!IsDefined(players)||!IsDefined(transaction)',
         '!IsDefined(player)||player.IsReplacer()',
         'transaction.GetItemQuantity(player,ItemID.CreateQuery(TDBID.Create(items[k])))',
         'ArrayPush(sample.inventory,actual)', 'if actual!=0',
         'SideJobDataS28.VehicleNames(i)', '!IsDefined(vehicleSystem)',
         'unlocked=vehicleSystem.IsVehiclePlayerUnlocked(TDBID.Create(vehicles[k]))',
         'ArrayPush(sample.vehicles,unlocked)', 'if unlocked')
    assert body(owner, 'Read').count('jm.HasAnyDelayedStateChanges()') == 2
    need('Same', '!a.valid||!b.valid', 'ArraySize(a.states)!=ArraySize(b.states)',
         'ArraySize(a.facts)!=ArraySize(b.facts)', 'ArraySize(a.inventory)!=ArraySize(b.inventory)',
         'ArraySize(a.vehicles)!=ArraySize(b.vehicles)', 'a.states[i]!=b.states[i]',
         'a.facts[i]!=b.facts[i]', 'a.inventory[i]!=b.inventory[i]', 'a.vehicles[i]!=b.vehicles[i]')
    need('Poll', '!this.running||epoch!=this.epoch', 'this.Own(i,"Issued")==0',
         'this.Permit(i,this.Same(this.previous[i],current)&&this.Ready(i))',
         'this.previous[i]=current', 'this.Permit(i,false);this.previous[i]=empty')
    assert owner.count('.SetFactStr(') == 1
    for forbidden in ['ChangeEntryState', 'GiveReward', 'GiveItem', 'ModLog(', 'SetFact(',
                      'EnablePlayerVehicle', 'SetFactStr("mq', 'RestoreFresh', 'familyPreTower',
                      'PrepareSupport', 'MapPermit', 'PreparePermit']:
        assert forbidden not in owner
    count = int(re.search(r'return (\d+);', body(srcdata, 'Count')).group(1))
    assert count == 4, 'Exactly four S28 entries required'
    arrays = 0
    for stem in ['Paths', 'Classes', 'StatesA', 'StatesB', 'FactNames', 'FactMin', 'FactMax', 'ItemNames', 'VehicleNames']:
        for i in range(count):
            name = stem + str(i)
            original, actual = body(srcdata, name), body(data, name)
            expected = json.loads(re.search(r'return\s*(\[[^]]*\]);', original).group(1))
            resize = re.search(r'ArrayResize\((synthetic\$\d+),\s*(\d+)u\)', actual)
            assert resize and int(resize.group(2)) == len(expected), (name, 'size', actual)
            assignments = re.findall(re.escape(resize.group(1)) + r'\[(\d+)u\]\s*=\s*(n?"[^"\n]*"|-?\d+);', actual)
            parsed = [(int(k), json.loads(v.removeprefix('n').replace("\\'", "'"))) for k, v in assignments]
            assert parsed == list(enumerate(expected)), (name, 'data')
            branch = block(body(data, stem), r'if i == ' + str(i) + r'\s*\{', name + ' dispatch')
            assert compact(branch) == 'returnSideJobDataS28.' + name + '();'
            arrays += 1
    for name in ['Count', 'ID', 'Title', 'Tag', 'Index']:
        a = re.findall(r'\breturn\s+([^;]+);', body(data, name))
        b = re.findall(r'\breturn\s+([^;]+);', body(srcdata, name))
        assert [compact(v) for v in a] == [compact(v) for v in b], name
    return {'methods': checked, 'arrays': arrays, 'adapters': count,
            'owned_permit_only': True, 'typed_item_query_zero_and_stability_guards': True,
            'exact_vehicle_entitlement_and_stability_guards': True,
            'no_native_fact_journal_item_vehicle_writes': True}


def main(revision):
    build = HERE / 'build' / revision
    output = build / 'compile_result.json'
    assert not output.exists(), 'Immutable compiler receipt'
    stage = Path(tempfile.mkdtemp(prefix='compile_', dir=build))
    cache = stage / 'cache'; cache.mkdir()
    protected = {str(p): sha(p) for p in (GAME / 'r6/cache').iterdir() if p.is_file()}
    for name in ['final.redscripts', 'final.redscripts.ts']:
        shutil.copy2(GAME / 'r6/cache' / name, cache / name)
    dependencies = {}
    for p in (GAME / 'r6/scripts').rglob('*.reds'):
        dependencies[str(p)] = sha(p)
        target = stage / 'scripts' / p.relative_to(GAME / 'r6/scripts')
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, target)
    new = stage / 'scripts/TowerContinued_SideJobs_S28'; new.mkdir()
    shutil.copy2(build / 'SideJobsS28.reds', new / 'SideJobsS28.reds')
    config = ROOT / 'research/restriction_profiles/implementation_r1/compile_paths.txt'
    plugins = [v.strip() for v in config.read_text(encoding='utf-8-sig').splitlines()[2:] if v.strip()]
    script_roots = sorted({str((GAME / 'r6/scripts').resolve()), *(str(Path(p).resolve()) for p in plugins)})
    assert all(Path(p).is_dir() for p in script_roots)
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):
            dependencies[str(p)] = sha(p)
    cli = ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    compiler_inputs = {str(p.resolve()): sha(p) for p in [config, cli, GAME / 'engine/tools/scc.exe', GAME / 'engine/tools/scc_lib.dll']}
    def live_scripts():
        return sorted({str(p.resolve()) for root in script_roots for p in Path(root).rglob('*.reds')})
    assert live_scripts() == sorted(dependencies), 'Source identity set changed before compile'
    def run(args, name):
        result = subprocess.run(args, capture_output=True, text=True, timeout=180)
        log = result.stdout + result.stderr
        (stage / name).write_text(log, encoding='utf-8')
        assert result.returncode == 0 and 'Output successfully saved' in log and not re.search(r'(?m)^\[?ERROR\b', log), log[-12000:]
        return log
    args = [str(cli), 'compile']
    for p in [new, stage / 'scripts/PTFR_PreAlpha', GAME / 'red4ext/plugins/Codeware/Scripts']:
        args += ['-s', str(p)]
    args += ['-b', str(cache / 'final.redscripts'), '-o', str(stage / 'headless.redscripts')]
    run(args, 'headless.log')
    paths = stage / 'compile_paths.txt'; paths.write_text('\n'.join(plugins) + '\n')
    compiled = cache / 'compiled.redscripts'
    log = run([str(GAME / 'engine/tools/scc.exe'), '-compile', str(stage / 'scripts'), '-compilePathsFile', str(paths), '-customCacheDir', str(cache), '-outputCacheFile', str(compiled), str(cache / 'final.redscripts')], 'scc.log')
    assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
    flat = stage / 'compiled.script'
    run([str(cli), 'decompile', '-i', str(compiled), '-o', str(flat)], 'decompile.log')
    text = re.sub(r'\$local\$\d+', '', flat.read_text(encoding='utf-8-sig'))
    assert 'EquipmentEx.OutfitSystem.GetInstance' in text
    proof = verify(text, (build / 'SideJobsS28.reds').read_text(encoding='utf-8-sig'))
    for p, h in {**protected, **dependencies, **compiler_inputs}.items():
        assert sha(Path(p)) == h, p
    assert live_scripts() == sorted(dependencies), 'Source identity set changed during compile'
    report = {'status': 'PASS_NOT_LIVE', 'build_sha256': sha(build / 'build.json'),
              'compiler_sha256': sha(Path(__file__)), 'script_sha256': sha(build / 'SideJobsS28.reds'),
              'compiled_sha256': sha(compiled), 'stage': str(stage), 'combined_cli': True,
              'full_scc': True, 'equipmentex': True, 'body_readback': True, 'body_checks': proof,
              'protected': protected, 'dependencies': dependencies, 'live_files_unchanged': True,
              'script_roots': script_roots, 'compiler_inputs': compiler_inputs,
              'script_environment_complete': True}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['protected', 'dependencies']}, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
