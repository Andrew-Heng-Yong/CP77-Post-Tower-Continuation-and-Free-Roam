"""Independent bounded QR14 transaction controls. Writes only own fixture domain."""
from pathlib import Path
import argparse, copy, hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
QR14 = HERE.parent
WS = QR14.parents[1]
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
INSTALLER = QR14 / 'deploy_core.ps1'
MANIFEST = QR14 / 'core_manifest_01.json'
TESTS = QR14 / 'test_deployment.py'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def put(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p)
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    args = ap.parse_args()
    assert args.run.startswith('review_01') and args.run.replace('_', '').isalnum()
    fixture_domain = QR14 / 'fixtures' / args.run
    assert not fixture_domain.exists()
    fixture_domain.mkdir(parents=True)
    source_pins = {str(p): sha(p) for p in [INSTALLER, MANIFEST, TESTS]}
    base = read(MANIFEST)
    checks, commands = [], []

    def ck(name, condition, evidence=None):
        checks.append({'name': name, 'pass': bool(condition), 'evidence': evidence})
        assert condition, name

    old = read(WS / 'prealpha/quest_restoration_qr9/worker_a/core_manifest_02.json')
    new = read(WS / 'prealpha/quest_restoration_qr13/candidate_01/package_manifest.json')
    compile_result = read(WS / 'prealpha/quest_restoration_qr13/verification/compile_01/result.json')
    observer = read(WS / 'prealpha/quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json')
    old_rows = {r['path']: (r['after'], r['after_bytes']) for r in old['files']}
    new_rows = {r['path']: (r['sha256'], r['bytes']) for r in new['files']}
    ck('all51 predecessor hashes and sizes match installed QR8 manifest',
       {r['path']: (r['before'], r['before_bytes']) for r in base['files']} == old_rows and len(old_rows) == 51)
    ck('all51 successor hashes and sizes match approved QR13 package',
       {r['path']: (r['after'], r['after_bytes']) for r in base['files']} == new_rows)
    ck('complete134 source/tool/cache pins equal successful fresh compile',
       base['compile_inputs'] == compile_result['input_pins'] and len(base['compile_inputs']) == 134)
    required = {r['path']: (r['sha256'], r['bytes']) for r in base['required_files']}
    diagnostic_paths = {r['path']: (r['after'], r['after_bytes']) for r in observer['files']}
    diagnostic_paths.update({r['path']: (r['sha256'], r['bytes']) for r in observer['required_files']
                             if '/PTFR_QR9_Diagnostics/' in r['path']})
    ck('current D00E watch and D01 code are protected exact dependencies',
       len(diagnostic_paths) == 2 and all(required[p] == x for p, x in diagnostic_paths.items()))
    ck('validated diagnostic files are outside Core mutation set',
       not set(diagnostic_paths).intersection(r['path'] for r in base['files']))
    ck('all proof pins exist and are exact', all(sha(r['path']) == r['sha256'] for r in base['proofs']))
    ck('all package bytes exact without running installer',
       all(sha(Path(base['package_root']) / r['path']) == r['after'] for r in base['files']))
    ck('all current compiler input pins exact without compiler execution',
       all(sha(p) == h for p, h in base['compile_inputs'].items()))

    def fixture(name):
        root = fixture_domain / name
        root.mkdir()
        m = copy.deepcopy(base)
        m.update(game_root=str(root / 'game'), save_root=str(root / 'saves'),
                 package_root=str(root / 'package'), zip='', zip_sha256=None)
        for r in m['files']:
            different = r['before'] != r['after']
            before = ('independent native before ' + r['path']).encode()
            after = ('independent approved after ' + r['path']).encode() if different else before
            put(root / 'game' / r['path'], before)
            put(root / 'package' / r['path'], after)
            r.update(before=sha(root / 'game' / r['path']), before_bytes=len(before),
                     after=sha(root / 'package' / r['path']), after_bytes=len(after))
        for r in m['required_files']:
            p = root / 'game' / r['path']
            data = ('independent dependency ' + r['path']).encode()
            put(p, data)
            r.update(sha256=sha(p), bytes=len(data))
        for r in m['protected_saves'] + m['working_save_files']:
            p = root / 'saves' / r['path']
            data = ('independent genuine unchanged fixture ' + r['path']).encode()
            put(p, data)
            r.update(sha256=sha(p), bytes=len(data))
        proof = root / 'proof.json'
        compiler_input = root / 'compiler_input.reds'
        put(proof, b'{"independent_proof":"pinned"}')
        put(compiler_input, b'// independently pinned compile input')
        m['proofs'] = [{'path': str(proof), 'sha256': sha(proof)}]
        m['compile_inputs'] = {str(compiler_input): sha(compiler_input)}
        (root / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n', encoding='utf-8')
        return root, m

    def call(root, action, extra=(), expected=True):
        command = [str(PS), '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                   '-FixtureRoot', str(root), '-FixtureManifest', str(root / 'manifest.json'),
                   '-FixtureManifestSHA', sha(root / 'manifest.json'), *extra]
        result = subprocess.run(command, capture_output=True, text=True, timeout=35,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        commands.append({'fixture': root.name, 'action': action, 'command': command,
                         'exit': result.returncode, 'stdout': result.stdout[-4000:], 'stderr': result.stderr[-5000:]})
        ck('expected action outcome ' + root.name + '/' + action,
           (result.returncode == 0) == expected)
        return result

    for kind, file in [('proof_drift', 'proof.json'), ('compile_input_drift', 'compiler_input.reds')]:
        root, m = fixture(kind)
        put(root / file, b'changed independent pinned input')
        before = snapshot(root / 'game'), snapshot(root / 'saves')
        call(root, 'Install', expected=False)
        ck(kind + ' refuses before recovery creation or managed/save changes',
           not (root / 'recovery').exists() and before == (snapshot(root / 'game'), snapshot(root / 'saves')))

    root, m = fixture('unchanged_core_drift')
    call(root, 'Install')
    same = next(r for r in m['files'] if r['before'] == r['after'])
    put(root / 'game' / same['path'], b'unknown changed unchanged-Core member')
    before = snapshot(root / 'game'), snapshot(root / 'saves')
    call(root, 'Verify', expected=False)
    call(root, 'Rollback', expected=False)
    ck('unchanged Core51 member drift blocks verification and rollback preserving unknown bytes',
       before == (snapshot(root / 'game'), snapshot(root / 'saves')))

    root, m = fixture('master_changes_after_install')
    call(root, 'Install')
    put(root / 'saves' / m['protected_saves'][0]['path'], b'externally modified protected master')
    before = snapshot(root / 'game'), snapshot(root / 'saves')
    call(root, 'Rollback', expected=False)
    ck('protected master drift after installation blocks rollback without restoring saves',
       before == (snapshot(root / 'game'), snapshot(root / 'saves')))

    root, m = fixture('linked_recovery_parent')
    target = root / 'same_domain_unknown'
    target.mkdir()
    put(target / 'unknown.txt', b'must remain')
    (root / 'recovery').symlink_to(target, target_is_directory=True)
    before = snapshot(root / 'game'), snapshot(root / 'saves'), snapshot(target)
    call(root, 'Install', expected=False)
    ck('recovery parent reparse refused before target or unknown destination writes',
       before == (snapshot(root / 'game'), snapshot(root / 'saves'), snapshot(target)) and not (target / 'core').exists())

    root, m = fixture('rollback_protection_current_working_history')
    call(root, 'Install')
    # The install fixture is pinned, while a later natural working history is allowed.
    put(root / 'saves' / m['working_save_files'][1]['path'], b'legitimate later working progression')
    put(root / 'saves/NewSlot/sav.dat', b'legitimate new slot')
    before = snapshot(root / 'saves')
    call(root, 'ValidateRollback')
    call(root, 'Rollback')
    ck('later working-slot bytes and new slots retained through actual rollback',
       before == snapshot(root / 'saves') and all(sha(root / 'game' / r['path']) == r['before'] for r in m['files']))

    ck('coordinator installer manifest and tests unchanged through independent controls',
       all(sha(p) == h for p, h in source_pins.items()))
    result = {'status': 'PASS_INDEPENDENT_QR14_DEPLOYMENT_CONTROLS',
              'source_pins': source_pins, 'checks': checks, 'command_count': len(commands),
              'commands': commands, 'fixture_domain': str(fixture_domain),
              'runtime_or_candidate_writes': 0, 'save_writes': 0, 'game_launches': 0,
              'limits': ['Synthetic transaction/save/dependency bytes for safety controls; actual manifests/package/compile/proof bytes read only.',
                         'No OS crash/power-loss or actual protected-directory replacement permission test.']}
    output = HERE / 'controls_result.json'
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'commands': len(commands), 'output': str(output)}))


if __name__ == '__main__':
    main()
