"""Combined U9 packaging/interlock/compile checks. Never writes the game tree.

Component source/graph tests are separate evidence. This validator integrates
their immutable outputs and compiles against the actual installed mod set.
"""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/gig_restoration/gig_batch_u9'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
COMPONENTS = ('gig_phone_u9', 'native_gigs_u9', 'special_gigs_u9')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def crc(text):
    result = 65535
    for byte in text.encode('utf-8'):
        result ^= byte << 8
        for _ in range(8):
            result = ((result << 1) ^ (0x1021 if result & 32768 else 0)) & 65535
    return result


def interlocks():
    source = ROOT / 'redscript/PTFR_GigBatchU9/EntryInterlocks.reds'
    lua = ROOT / 'diagnostics/PTFR_GigBatchU9/init.lua'
    report_path = OUT / 'interlock_tests.json'
    report = read(report_path)
    assert report['status'].startswith('PASS'), 'Interlock tests failed'
    test = ROOT / 'tools/test_gig_batch_interlocks_u9.py'
    assert report['test_sha256'].upper() == sha(test), 'Interlock tests stale'
    assert report['target_count'] == 11 and report['actual_luajit']
    assert report['no_mutator_probes'] and report['default_false_helper']
    for path, digest in report['source_pins'].items():
        assert sha(ROOT / path) == digest.upper(), 'Interlock source drift: ' + path
    # Old module-qualified REDscript methods cannot be wrapped by this compiler;
    # the additive CET hooks have their own executable Lua test suite.
    assert '@wrapMethod' not in source.read_text()
    assert 'Probe' in source.read_text() and 'return false' in source.read_text()
    assert all(x not in lua.read_text() for x in ('SetFact(', 'GiveReward(', 'ChangeEntryState('))
    return source, lua, report, report_path, test


def run(args, timeout, log):
    p = subprocess.run(list(map(str, args)), capture_output=True, text=True, timeout=timeout)
    text = p.stdout + p.stderr
    (OUT / log).write_text(text, encoding='utf-8')
    assert p.returncode == 0 and '[ERROR' not in text and 'ERROR [' not in text, text[-6000:]
    return text


def compile_all(files):
    stage = Path(tempfile.mkdtemp(prefix='compile_', dir=OUT))
    cache = stage / 'cache'
    cache.mkdir()
    protected = {str(p): sha(p) for p in (GAME / 'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts', 'final.redscripts.ts'):
        shutil.copy2(GAME / 'r6/cache' / name, cache / name)
    deps = {}
    for p in (GAME / 'r6/scripts').rglob('*.reds'):
        deps[str(p)] = sha(p)
        dest = stage / 'scripts' / p.relative_to(GAME / 'r6/scripts')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    for f in files:
        if f['relative'].endswith('.reds'):
            dest = stage / 'scripts' / Path(f['relative']).relative_to('r6/scripts')
            assert not dest.exists(), 'U9 must be additive: ' + str(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f['source'], dest)
    plugins = (ROOT / 'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):
            deps[str(p)] = sha(p)
    cli = ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args = [cli, 'compile']
    # Standalone CLI and game SCC do not accept exactly the same third-party
    # syntax. CLI covers the new and dependent PTFR modules; full SCC below
    # covers every installed mod including EquipmentEx.
    names = ('PTFR_GigBatchU9', 'PTFR_NativeGigsU9', 'PTFR_GigPhoneU9',
             'PTFR_NativeHeywoodU8', 'PTFR_NativeSupportU7', 'PTFR_NativePadreU6',
             'PTFR_NativeJeopardyU4', 'PTFR_NativeReuseU1',
             'PTFR_Restrictions_R1', 'PTFR_Restrictions_R2', 'PTFR_Restrictions_R3',
             'PTFR_GigPilotR1', 'PTFR_SideJobPilotS1', 'PTFR_RiteG2', 'PTFR_MinefieldG3',
             'PTFR_JohnnyVoiceJV1', 'PTFR_FreshGigsB5', 'PTFR_FreshGigsB6',
             'PTFR_GigMarkersM6', 'PTFR_GigFamilyB7', 'PTFR_ActivityStateR3')
    for name in names:
        args += ['-s', stage / 'scripts' / name]
    args += ['-s', GAME / 'red4ext/plugins/Codeware/Scripts']
    args += ['-b', cache / 'final.redscripts', '-o', stage / 'headless.redscripts']
    log = run(args, 180, 'headless_compile.log')
    assert 'Output successfully saved' in log
    paths = stage / 'compile_paths.txt'
    paths.write_text('\n'.join(plugins) + '\n', encoding='utf-8')
    compiled = cache / 'compiled.redscripts'
    log = run([GAME / 'engine/tools/scc.exe', '-compile', stage / 'scripts',
               '-compilePathsFile', paths, '-customCacheDir', cache,
               '-outputCacheFile', compiled, cache / 'final.redscripts'], 180, 'compile.log')
    assert 'Compilation complete' in log and 'Output successfully saved' in log
    assert 'EquipmentEx.reds' in log
    flat = stage / 'compiled_flat.script'
    decomp = subprocess.run(list(map(str, [cli, 'decompile', '-i', compiled, '-o', flat])),
                            capture_output=True, text=True, timeout=120)
    decomp_log = decomp.stdout + decomp.stderr
    (OUT / 'decompile.log').write_text(decomp_log, encoding='utf-8')
    assert decomp.returncode == 0 and 'Output successfully saved' in decomp_log
    content = flat.read_text(encoding='utf-8-sig')
    # The old ActivityDefinition.FactNames method exceeds this decompiler's
    # code-cursor range. Do not hide arbitrary failures or treat that old body
    # as a new U9 verification. Bytecode decoding and every U9 body must pass.
    errors = [line for line in decomp_log.splitlines() if line.startswith('ERROR ')]
    if errors:
        assert len(errors) == 1 and re.search(r'Method decompilation \d+ failed .*invalid instruction offset:', errors[0]), errors
        old = content.split('class PTFR.ActivityStateR3.ActivityDefinition ', 1)[1].split('\npublic ', 1)[0]
        assert re.search(r'func FactNames\([^\n]+\{\s*public static func RootIndex', old)
    bytecode = stage / 'compiled_bytecode.txt'
    run([cli, 'decompile', '-i', compiled, '-o', bytecode, '-m', 'bytecode'], 120, 'bytecode.log')
    for symbol in ('class PTFR.ActivityStateR3.GigPhoneU9',
                   'class PTFR.ActivityStateR3.NativeGigsU9',
                   'class GigBatchLockU9', 'TemporaryHide(true);'):
        assert symbol in content, symbol
    for cls in ('GigBatchLockU9', 'PTFR.ActivityStateR3.GigPhoneU9',
                'PTFR.ActivityStateR3.NativeGigsU9', 'PTFR.ActivityStateR3.NativeGigDataU9',
                'PTFR.ActivityStateR3.GigPhoneDataU9'):
        body = content.split('class ' + cls + ' ', 1)[1].split('\npublic ', 1)[0]
        assert not re.search(r'func [^\n]+\{\s*(?:public|private|protected) ', body), cls
        assert body.count('{') == body.count('}'), cls
    assert sha(GAME / 'r6/scripts/PTFR_Restrictions_R3/ProfilePhysical.reds') == 'BD574FC510FB75969314E64388E0D609DE2B01CDBBD90C2EBF552ACF2C342F12'
    for p, digest in {**deps, **protected}.items():
        assert sha(p) == digest, p
    return {'cli': True, 'full_scc': True, 'equipmentex': True,
            'compiled_readback': True, 'compiled_sha256': sha(compiled),
            'unchanged_predecessor_decompiler_gaps': errors,
            'all_u9_bodies_readback': True, 'bytecode_readback': True,
            'dependencies': deps, 'protected': protected}


def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT / 'install_receipt.json').exists(), 'Installed evidence pinned'
    files, components, pins, boots = [], {}, {}, []
    for name in COMPONENTS:
        folder = ROOT / 'research/gig_restoration' / name
        mpath, tpath = folder / 'manifest.json', folder / 'tests.json'
        m, t = read(mpath), read(tpath)
        assert t['status'].startswith('PASS'), (name, t['status'])
        assert t['manifest_sha256'].upper() == sha(mpath), name + ' tests stale'
        if 'plan_sha256' in m:
            assert m['plan_sha256'].upper() == sha(folder / 'build_plan.json'), name + ' plan stale'
        components[name] = {'manifest': str(mpath.relative_to(ROOT)).replace('\\', '/'),
                            'manifest_sha256': sha(mpath), 'tests': str(tpath.relative_to(ROOT)).replace('\\', '/'),
                            'tests_sha256': sha(tpath), 'status': t['status']}
        pins[components[name]['manifest']] = sha(mpath)
        pins[components[name]['tests']] = sha(tpath)
        for kind, report, field, suffix in (
            ('build', m, 'builder_sha256', '.ps1'),
            ('test', t, 'test_sha256', '.py'),
        ):
            code = 'tools/' + kind + '_' + name + suffix
            assert report[field].upper() == sha(ROOT / code), code + ' changed after tests'
            pins[code] = sha(ROOT / code)
        for pinset in ('source_pins', 'native_pins'):
            for p, h in m.get(pinset, {}).items():
                assert sha(ROOT / p) == h.upper(), p
                pins[p] = h.upper()
        for f in m['files']:
            assert not f.get('predecessor'), 'No old script replacements in this batch'
            assert sha(ROOT / f['source']) == f['sha256'].upper(), f['source']
            files.append(f)
        boots += m.get('boots', [m['depot']] if 'depot' in m else [])
    peer_path = ROOT / 'research/gig_restoration/special_gigs_u9/integration_tests.json'
    peer = read(peer_path)
    assert peer['status'] == 'PASS_SPECIAL_U9_PEER_INTEGRATION_NOT_ENGINE_PROOF'
    assert peer['manifest_sha256'] == components['special_gigs_u9']['manifest_sha256']
    assert peer['native_manifest_sha256'] == components['native_gigs_u9']['manifest_sha256']
    for path, digest in (
        ('tools/test_special_gigs_u9_integration.py', peer['test_sha256']),
        ('tools/test_special_gigs_u9_retaliation.py', peer['retaliation']['test_sha256']),
    ):
        assert sha(ROOT / path) == digest.upper(), path + ' peer tests stale'
        pins[path] = digest.upper()
    assert peer['retaliation']['shared_cancel_cannot_clear_unissued_gang_pending']
    assert peer['matching_gang_required_in_writer_entry'] == 13
    pins[str(peer_path.relative_to(ROOT)).replace('\\', '/')] = sha(peer_path)
    source, lua, lock_checks, lock_report, lock_test = interlocks()
    files.append({'source': str(source.relative_to(ROOT)).replace('\\', '/'),
                  'relative': 'r6/scripts/PTFR_GigBatchU9/EntryInterlocks.reds',
                  'sha256': sha(source), 'predecessor': None})
    files.append({'source': str(lua.relative_to(ROOT)).replace('\\', '/'),
                  'relative': 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigBatchU9/init.lua',
                  'sha256': sha(lua), 'predecessor': None})
    for path in (lock_report, lock_test):
        pins[str(path.relative_to(ROOT)).replace('\\', '/')] = sha(path)
    assert len({f['relative'].lower() for f in files}) == len(files)
    for f in files:
        pins[f['source']] = sha(ROOT / f['source'])
    assert len(set(boots)) == len(boots)
    node_ids = [crc(p + ':1') for p in boots]
    assert len(set(node_ids)) == len(node_ids), 'Cross-package XL collision'
    native = read(ROOT / 'research/q307_extracted/json/ep1/quest/ep1.quest.json')
    reserved = {n['Data']['id'] for n in native['Data']['RootChunk']['graph']['Data']['nodes']}
    assert not reserved.intersection(node_ids), 'Native-root XL collision'
    # Exact cast whitelist correspondence is checked again at integration.
    whitelist_path = ROOT / 'research/gig_restoration/lore_whitelists_v4_cast.json'
    whitelist = read(whitelist_path)['ignore_two_year_gap']['gigs']
    assert len(whitelist) == 72 and len(set(whitelist)) == 72
    plan_path = ROOT / 'research/gig_restoration/native_gigs_u9/build_plan.json'
    plan = read(plan_path)
    assert len(plan['jobs']) == 72
    assert {j['title'] for j in plan['jobs']} == set(whitelist), 'Cast whitelist coverage mismatch'
    assert len({j['id'] for j in plan['jobs']}) == 72
    pins[str(plan_path.relative_to(ROOT)).replace('\\', '/')] = sha(plan_path)
    pins[str(whitelist_path.relative_to(ROOT)).replace('\\', '/')] = sha(whitelist_path)
    result = compile_all(files)
    # Verify source files did not change during compilation.
    for p, h in pins.items():
        assert sha(ROOT / p) == h, p
    manifest = {'status': 'BUILT_U9_GIG_ONLY_BATCH_LIVE_PENDING', 'files': files,
                'components': components, 'source_pins': pins, 'boots': boots,
                'collisions': [{'depot': p, 'node_id': crc(p + ':1')} for p in boots],
                'scope': 'Whitelisted gigs only; no side-job or world-activity restoration.',
                'production_auto': False, 'development_save_migration': False,
                'gig_count': 72, 'coverage': [{'id': j['id'], 'title': j['title'],
                    'region': j['region'], 'live_status': 'UNTESTED_U9'} for j in plan['jobs']],
                'additions': len(files), 'replacements': 0}
    write('manifest.json', manifest)
    write('tests.json', {'status': 'PASS_U9_COMBINED_OFFLINE_LIVE_PENDING',
                        'manifest_sha256': sha(OUT / 'manifest.json'),
                        'validator_sha256': sha(__file__), 'components': components,
                        'interlocks': lock_checks, 'cross_package_collisions': True,
                        'special_peer_integration': peer,
                        'game_scripts_and_cache_unchanged': True, **result})
    print(json.dumps({'status': 'PASS_U9_COMBINED_OFFLINE_LIVE_PENDING',
                      'files': len(files), 'boots': len(boots), 'interlocks': lock_checks}))


if __name__ == '__main__':
    main()
