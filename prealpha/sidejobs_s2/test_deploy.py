"""New S2 installer fixtures: isolated workspace paths, no game/save writes."""
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / 'fixtures' / datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%S%fZ')
RUN.mkdir(parents=True)
PWSH = shutil.which('pwsh')
assert PWSH
REVISION = sys.argv[1] if len(sys.argv) > 1 else 's2_02'
assert re.fullmatch(r's2_\d{2}', REVISION), 'Only an S2 build revision is accepted'
BASE = HERE / 'build' / REVISION
RELATIVES = [
    'archive/pc/mod/TowerContinued_SideJobs_S2.archive',
    'archive/pc/mod/TowerContinued_SideJobs_S2.archive.xl',
    'r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds',
]
EVIDENCE = ['build.json', 'tests.json', 'resource_check.json', 'compiler.json']
RESULT = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding='utf-8')


def fixture(name):
    p = RUN / name
    build, game, saves, rec = (p / n for n in ['build', 'game', 'saves', 'recovery'])
    build.mkdir(parents=True)
    saves.mkdir()
    for folder in ['archive/pc/mod', 'r6/cache', 'r6/scripts', 'r6/config', 'engine/config', 'red4ext/plugins', 'bin/x64/plugins']:
        (game / folder).mkdir(parents=True, exist_ok=True)
    for name in [Path(r).name for r in RELATIVES] + EVIDENCE:
        shutil.copy2(BASE / name, build / name)
    for relative, content in {
        'archive/pc/mod/keep.archive': b'fixture protected unrelated mod',
        'archive/pc/mod/TowerContinued_Races_R1.archive': b'fixture protected pinned R1',
        'r6/scripts/keep.reds': b'fixture protected unrelated script',
        'r6/cache/final.redscripts': b'fixture protected cache',
        'engine/config/settings.json': b'fixture protected settings',
        'r6/config/input.xml': b'fixture protected configuration',
        'red4ext/plugins/keep.dll': b'fixture protected plugin',
        'bin/x64/plugins/keep.dll': b'fixture protected CET',
    }.items():
        (game / relative).write_bytes(content)
    (saves / 'sav.dat').write_bytes(b'fixture protected save, not a real game save')
    return dict(p=p, build=build, game=game, saves=saves, recovery=rec)


def snapshot(f):
    return {
        str(p.relative_to(f['p'])): digest(p)
        for root in [f['p'] / 'game', f['p'] / 'saves']
        for p in root.rglob('*')
        if p.is_file() and not (p.is_relative_to(f['game']) and p.relative_to(f['game']).as_posix() in RELATIVES)
    }


def invoke(f, mode, success=True, extra=(), busy=False):
    args = [str(HERE / 'deploy.ps1'), '-Fixture', '-Mode', mode, '-Build', str(f['build']), '-GameRoot', str(f['game']), '-SaveRoot', str(f['saves']), '-RecoveryRoot', str(f['recovery']), *extra]
    before = snapshot(f)
    if busy:
        quoted = ' '.join("'" + a.replace("'", "''") + "'" if not a.startswith('-') else a for a in args)
        cmd = [PWSH, '-NoProfile', '-Command', 'function global:Get-Process { param($Name) return [pscustomobject]@{Id=999} }; & ' + quoted]
    else:
        cmd = [PWSH, '-NoProfile', '-File', *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    if ((result.returncode == 0) != success or snapshot(f) != before):
        write(RUN / 'failure.json', dict(status='FAIL_WORKSPACE_FIXTURE', case=f['p'].name, mode=mode, expected_success=success, exit=result.returncode, output=result.stdout + result.stderr, installer_sha256=digest(HERE / 'deploy.ps1'), tester_sha256=digest(Path(__file__)), build_sha256=digest(BASE / 'build.json')))
    assert (result.returncode == 0) == success, (f['p'].name, mode, result.stdout, result.stderr)
    assert snapshot(f) == before, ('protected data changed', f['p'].name)
    RESULT.append(dict(case=f['p'].name, mode=mode, expected_success=success, exit=result.returncode, output=result.stdout + result.stderr))


def repin(f):
    for name in EVIDENCE[1:]:
        path = f['build'] / name
        obj = read(path)
        obj['build_sha256'] = digest(f['build'] / 'build.json')
        write(path, obj)


def change(f, edit):
    path = f['build'] / 'build.json'
    obj = read(path)
    edit(obj)
    write(path, obj)
    repin(f)


def installed_exact(f):
    for entry in read(f['build'] / 'build.json')['files']:
        assert digest(f['game'] / entry['relative']) == entry['sha256']


def removed_exact(f, count):
    assert not any((f['game'] / r).exists() for r in RELATIVES)
    assert len(list(f['recovery'].glob('removed_*'))) == count
    for entry in read(f['build'] / 'build.json')['files'][:count]:
        assert digest(f['recovery'] / ('removed_' + Path(entry['relative']).name)) == entry['sha256']


f = fixture('normal')
invoke(f, 'Validate')
assert not (f['game'] / 'r6/scripts/TowerContinued_SideJobs_S2').exists()
invoke(f, 'Install')
installed_exact(f)
invoke(f, 'Install', False)
invoke(f, 'ValidateRollback')
invoke(f, 'Rollback')
removed_exact(f, 3)
invoke(f, 'Rollback', False)
f = fixture('partial')
invoke(f, 'Install', False, ['-FailAfterFirst'])
assert not (f['game'] / 'r6/scripts/TowerContinued_SideJobs_S2').exists()
invoke(f, 'ValidateRollback')
invoke(f, 'Rollback')
removed_exact(f, 1)
f = fixture('busy')
invoke(f, 'Install', False, busy=True)
assert not f['recovery'].exists()

for name, mutate in [
    ('extra_file', lambda m: m['files'].append(m['files'][0].copy())),
    ('missing_file', lambda m: m['files'].pop()),
    ('path_escape', lambda m: m['files'][0].update(relative='../outside.archive')),
    ('wrong_target', lambda m: m['files'][0].update(relative='r6/cache/final.redscripts')),
    ('wrong_script_target', lambda m: m['files'][2].update(relative='r6/scripts/keep.reds')),
    ('duplicate_target', lambda m: m['files'][1].update(relative=m['files'][0]['relative'])),
    ('wrong_status', lambda m: m.update(status='PASS')),
    ('native_override', lambda m: m.update(official_overrides=['base/unwanted.questphase'])),
    ('extra_script', lambda m: m.update(runtime_scripts_added=2)),
    ('no_script', lambda m: m.update(runtime_scripts_added=0)),
    ('no_readback', lambda m: m.update(packed_readback=False)),
    ('string_readback', lambda m: m.update(packed_readback='true')),
    ('scene_patch', lambda m: m.update(native_scenes_unchanged=False)),
    ('wrong_resource_count', lambda m: m['resources'].pop(next(iter(m['resources'])))),
    ('wrong_boot_count', lambda m: m['boots'].pop()),
    ('bad_hash', lambda m: m['files'][0].update(sha256='0' * 64)),
    ('bad_script_hash', lambda m: m['files'][2].update(sha256='0' * 64)),
    ('wrong_official_count', lambda m: m.update(official_resource_count=0)),
    ('no_sources', lambda m: m.update(source_pins={})),
    ('bad_source_hash', lambda m: m['source_pins'].update({next(iter(m['source_pins'])): '0' * 64})),
    ('source_escape', lambda m: m['source_pins'].update({'../outside': '0' * 64})),
]:
    f = fixture(name)
    change(f, mutate)
    invoke(f, 'Validate', False)

for name, file, mutate in [
    ('missing_tests', 'tests.json', None),
    ('missing_audit', 'resource_check.json', None),
    ('missing_compiler', 'compiler.json', None),
    ('unbound_tests', 'tests.json', lambda d: d.update(build_sha256='0' * 64)),
    ('unbound_audit', 'resource_check.json', lambda d: d.update(build_sha256='0' * 64)),
    ('audit_override', 'resource_check.json', lambda d: d.update(overrides=['unexpected'])),
    ('audit_official_override', 'resource_check.json', lambda d: d.update(official_overrides=['base/bad.questphase'])),
    ('audit_load_order', 'resource_check.json', lambda d: d.update(modlist_absent=False)),
    ('audit_missing_official', 'resource_check.json', lambda d: d['official'].pop()),
    ('audit_duplicate_official', 'resource_check.json', lambda d: d['official'].__setitem__(1, d['official'][0].copy())),
    ('wrong_test_source', 'tests.json', lambda d: d.update(tester_sha256='0' * 64)),
    ('wrong_audit_source', 'resource_check.json', lambda d: d.update(checker_sha256='0' * 64)),
    ('unbound_compiler', 'compiler.json', lambda d: d.update(build_sha256='0' * 64)),
    ('wrong_compiler_source', 'compiler.json', lambda d: d.update(compiler_sha256='0' * 64)),
    ('wrong_compiled_script', 'compiler.json', lambda d: d.update(script_sha256='0' * 64)),
    ('no_scc', 'compiler.json', lambda d: d.update(full_scc=False)),
    ('no_cli', 'compiler.json', lambda d: d.update(combined_cli=False)),
    ('no_body_readback', 'compiler.json', lambda d: d.update(body_readback=False)),
    ('no_equipmentex', 'compiler.json', lambda d: d.update(equipmentex=False)),
    ('compiler_live_drift', 'compiler.json', lambda d: d.update(live_files_unchanged=False)),
    ('compiler_string_pass', 'compiler.json', lambda d: d.update(full_scc='true')),
]:
    f = fixture(name)
    path = f['build'] / file
    if mutate is None:
        path.rename(path.with_suffix('.withheld'))
    else:
        obj = read(path)
        mutate(obj)
        write(path, obj)
    invoke(f, 'Validate', False)

for index, relative in enumerate(RELATIVES):
    f = fixture('existing_target_' + str(index))
    target = f['game'] / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'never overwrite user file')
    invoke(f, 'Install', False)
    assert target.read_bytes() == b'never overwrite user file'

f = fixture('existing_script_folder')
(f['game'] / 'r6/scripts/TowerContinued_SideJobs_S2').mkdir()
(f['game'] / 'r6/scripts/TowerContinued_SideJobs_S2/user.keep').write_bytes(b'preserve unrelated same-folder file')
invoke(f, 'Install')
installed_exact(f)
invoke(f, 'Rollback')
removed_exact(f, 3)
f = fixture('script_parent_file')
(f['game'] / 'r6/scripts/TowerContinued_SideJobs_S2').write_bytes(b'not a directory')
invoke(f, 'Install', False)
f = fixture('changed_package')
(f['build'] / Path(RELATIVES[0]).name).write_bytes(b'changed')
invoke(f, 'Validate', False)
f = fixture('recovery_reuse')
f['recovery'].mkdir()
invoke(f, 'Install', False)
f = fixture('rollback_drift')
invoke(f, 'Install')
target = f['game'] / RELATIVES[2]
target.write_bytes(b'user modification')
invoke(f, 'Rollback', False)
assert target.read_bytes() == b'user modification'
f = fixture('receipt_tamper')
invoke(f, 'Install')
path = f['recovery'] / 'transaction.json'
obj = read(path)
obj['game_root'] = 'C:\\'
write(path, obj)
invoke(f, 'Rollback', False)
f = fixture('receipt_scope')
invoke(f, 'Install')
path = f['recovery'] / 'transaction.json'
obj = read(path)
obj['files'][0]['relative'] = 'r6/cache/final.redscripts'
write(path, obj)
(f['recovery'] / 'transaction.sha256').write_text(digest(path))
invoke(f, 'Rollback', False)
f = fixture('recovery_destination_exists')
invoke(f, 'Install')
(f['recovery'] / ('removed_' + Path(RELATIVES[0]).name)).write_bytes(b'preserve existing recovery data')
invoke(f, 'Rollback', False)
f = fixture('root_escape')
f['saves'] = RUN.parent.parent
invoke(f, 'Validate', False)
f = fixture('build_escape')
f['build'] = BASE
invoke(f, 'Validate', False)
f = fixture('recovery_escape')
f['recovery'] = HERE / 'not-a-fixture'
invoke(f, 'Install', False)

result = dict(status='PASS_WORKSPACE_FIXTURES_NOT_LIVE', cases=len({r['case'] for r in RESULT}), checks=len(RESULT), installer_sha256=digest(HERE / 'deploy.ps1'), tester_sha256=digest(Path(__file__)), build_sha256=digest(BASE / 'build.json'), results=RESULT)
assert result['cases'] >= 45 and result['checks'] >= 60
write(RUN / 'results.json', result)
print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))
print(RUN / 'results.json')
