"""Final QR14 review: actual integration evidence plus populated inventory fixtures."""
from pathlib import Path
import argparse, copy, json, stat, subprocess
from independent_controls import sha, read, put, snapshot, HERE, QR14, WS, PS, INSTALLER

MANIFEST = QR14 / 'core_manifest_02.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    args = ap.parse_args()
    assert args.run.startswith('review_01') and args.run.replace('_', '').isalnum()
    domain = QR14 / 'fixtures' / args.run
    assert not domain.exists()
    domain.mkdir(parents=True)
    output = HERE / 'final_controls_03_result.json'
    assert not output.exists()
    checked_files = [INSTALLER, MANIFEST, QR14 / 'test_deployment.py', QR14 / 'compile_integration.py',
                     Path(__file__), HERE / 'independent_controls.py', QR14 / 'verification/compile_01/result.json']
    pins = {str(p): sha(p) for p in checked_files}
    base = read(MANIFEST)
    cr = read(QR14 / 'verification/compile_01/result.json')
    checks, commands = [], []

    def ck(name, condition, evidence=None):
        checks.append({'name': name, 'pass': bool(condition), 'evidence': evidence})
        assert condition, name

    previous = read(QR14 / 'core_manifest_01.json')
    ck('Core51 and three-leaf change set unchanged from reviewed manifest01',
       base['files'] == previous['files'] and base['changing_paths'] == previous['changing_paths'])
    # Only the compile inventory/pin selection changed; the transaction is exact.
    old_engine = (QR14 / 'engine_01/deploy_core.ps1').read_text(encoding='utf-8-sig')
    new_engine = INSTALLER.read_text(encoding='utf-8-sig')
    start = new_engine.index('function CheckCompileInventory {')
    end = new_engine.index('function CheckPackage {', start)
    residual = new_engine[:start] + new_engine[end:]
    residual = residual.replace(' CheckCompileInventory\n', '', 1)
    residual = residual.replace(sha(MANIFEST), sha(QR14 / 'core_manifest_01.json'))
    residual = residual.replace("'core_manifest_02.json'", "'core_manifest_01.json'")
    ck('all original transaction cleanup lock and recovery code exact after guard-only delta', residual == old_engine)
    ck('revised manifest binds every current integration input pin',
       base['compile_inputs'] == cr['input_pins'] and len(cr['input_pins']) == 151)
    game = Path(base['game_root'])
    actual_sources = set()
    for root in [game / 'r6/scripts', game / 'red4ext/plugins']:
        for p in [root, *root.rglob('*')]:
            info = p.lstat()
            if p.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                assert not getattr(info, 'st_file_attributes', 0) & 16 and p.suffix.lower() != '.reds', p
                continue  # Non-source file links are recorded, never followed.
            if p.is_file() and p.suffix.lower() == '.reds':
                actual_sources.add(str(p))
    source_pins = {p: h for p, h in cr['input_pins'].items() if Path(p).suffix.lower() == '.reds'}
    log_copy = Path(cr['runtime_log']['copy'])
    logged_sources = set()
    for line in log_copy.read_text(encoding='utf-8-sig').splitlines():
        text = line.strip()
        if text.lower().endswith('.reds'):
            p = Path(text) if Path(text).is_absolute() else game / 'r6/scripts' / text
            logged_sources.add(str(p))
    ck('all148 enclosing-tree sources equal logged registrations and actual compiler origins',
       actual_sources == logged_sources == set(cr['runtime_registered_sources']) == set(cr['source_origins']) == set(source_pins)
       and len(actual_sources) == 148)
    ck('runtime log exact and same historical source listing independently captured',
       sha(log_copy) == cr['runtime_log']['sha256'] == read(HERE / 'compile_boundary_01.json')['log_sha256'])
    ck('all151 current installed source compiler and cache inputs retain exact bytes',
       all(sha(p) == h for p, h in cr['input_pins'].items()))
    extra = read(HERE / 'compile_boundary_01.json')['omitted_registered_sources']
    ck('all17 previously omitted LBD inputs are now included and protected dependencies',
       set(cr['additional_sources_vs_QR13']) == {r['path'] for r in extra}
       and all(source_pins[r['path']] == r['sha256'] for r in extra)
       and all(any(str(game / dep['path']) == r['path'] and dep['sha256'] == r['sha256']
                   and dep['bytes'] == r['bytes'] for dep in base['required_files']) for r in extra))
    package_scripts = {str(game / r['path']): r['after'] for r in base['files'] if r['path'].endswith('.reds')}
    staged_expected = {cr['source_origins'][origin]: package_scripts.get(origin, digest)
                       for origin, digest in source_pins.items()}
    ck('full148 staged bytes exactly current sources plus46 candidate managed overlays',
       len(package_scripts) == 46 and cr['staged_sources'] == staged_expected
       and all(sha(p) == h for p, h in staged_expected.items()))
    ck('exactly two staged script byte changes match authorized QR13 script leaves',
       {p for p in source_pins if staged_expected[cr['source_origins'][p]] != source_pins[p]}
       == {str(game / r['path']) for r in base['files'] if r['path'].endswith('.reds') and r['before'] != r['after']})
    command = cr['command']
    compiled = Path(command[command.index('-outputCacheFile') + 1])
    ck('fresh actual148-source compiler success and compiled binary pinned',
       cr['status'] == 'PASS_RUNTIME_REGISTERED148_INTEGRATION_COMPILE' and cr['exit_code'] == 0
       and cr['source_count'] == 148 and sha(compiled) == cr['compiled_sha256']
       and 'Compilation complete' in (QR14 / 'verification/compile_01/scc.log').read_text(encoding='utf-8-sig'))
    ck('exact current Core51 predecessor and26 external diagnostic dependency bytes',
       all(sha(game / r['path']) == r['before'] for r in base['files'])
       and len(base['required_files']) == 26 and all(sha(game / r['path']) == r['sha256'] for r in base['required_files']))
    ck('all bound proofs package and zip unchanged',
       all(sha(r['path']) == r['sha256'] for r in base['proofs'])
       and all(sha(Path(base['package_root']) / r['path']) == r['after'] for r in base['files'])
       and sha(base['zip']) == base['zip_sha256'])

    def fixture(name, actual=False):
        root = domain / name
        root.mkdir()
        m = copy.deepcopy(base)
        m.update(game_root=str(root / 'game'), save_root=str(root / 'saves'),
                 package_root=str(root / 'package'), zip='', zip_sha256=None)
        for r in m['files']:
            changed = r['before'] != r['after']
            old = (WS / 'prealpha/quest_restoration_qr8/candidate_01/package' / r['path']).read_bytes() if actual else ('native original ' + r['path']).encode()
            new = (Path(base['package_root']) / r['path']).read_bytes() if actual else (('approved successor ' + r['path']).encode() if changed else old)
            put(root / 'game' / r['path'], old)
            put(root / 'package' / r['path'], new)
            r.update(before=sha(root / 'game' / r['path']), before_bytes=len(old),
                     after=sha(root / 'package' / r['path']), after_bytes=len(new))
        for r in m['required_files']:
            p = root / 'game' / r['path']
            data = ('independent dependency ' + r['path']).encode()
            put(p, data)
            r.update(sha256=sha(p), bytes=len(data))
        for r in m['protected_saves'] + m['working_save_files']:
            p = root / 'saves' / r['path']
            data = ('untouched genuine fixture ' + r['path']).encode()
            put(p, data)
            r.update(sha256=sha(p), bytes=len(data))
        for relative in ['r6/scripts/OtherScript/External.reds', 'red4ext/plugins/Codeware/Scripts/code.reds',
                         'red4ext/plugins/ArchiveXL/Scripts/archive.reds', 'red4ext/plugins/TweakXL/Scripts/tweak.reds',
                         'red4ext/plugins/mod_settings/packed.reds']:
            put(root / 'game' / relative, ('pinned framework ' + relative).encode())
        log_target = root / 'logs/ArchiveXL.log'
        put(log_target, b'benign external log target must not be touched')
        (root / 'game/red4ext/plugins/ArchiveXL/ArchiveXL.log').symlink_to(log_target)
        m['compile_inputs'] = {str(p): sha(p) for folder in ['r6/scripts', 'red4ext/plugins']
                               for p in (root / 'game' / folder).rglob('*.reds')}
        expected_source_count = len({r['path'] for r in m['files'] + m['required_files'] if r['path'].endswith('.reds')}) + 5
        assert len(m['compile_inputs']) == expected_source_count == 69  # Includes the external Atelier script.
        proof = root / 'proof.json'
        put(proof, b'{"independent_proof":"exact"}')
        m['proofs'] = [{'path': str(proof), 'sha256': sha(proof)}]
        (root / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n', encoding='utf-8')
        return root, m

    def call(root, action, extra=(), expected=True):
        command = [str(PS), '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                   '-FixtureRoot', str(root), '-FixtureManifest', str(root / 'manifest.json'),
                   '-FixtureManifestSHA', sha(root / 'manifest.json'), *extra]
        r = subprocess.run(command, capture_output=True, text=True, timeout=35, creationflags=subprocess.CREATE_NO_WINDOW)
        commands.append({'fixture': root.name, 'action': action, 'command': command, 'exit': r.returncode,
                         'stdout': r.stdout[-4000:], 'stderr': r.stderr[-5000:]})
        ck('expected populated-inventory outcome ' + root.name + '/' + action, (r.returncode == 0) == expected)
        return r

    root, m = fixture('valid_populated_inventory')
    before = snapshot(root / 'saves')
    call(root, 'Preflight')
    call(root, 'Install')
    call(root, 'Verify')
    call(root, 'ValidateRollback')
    call(root, 'Rollback')
    call(root, 'Verify', ['-ExpectedState', 'Before'])
    ck('populated69 source inventory permits actual guarded install and full rollback',
       before == snapshot(root / 'saves') and all(sha(root / 'game' / r['path']) == r['before'] for r in m['files']))
    ck('non-source framework log link accepted without following or changing its target',
       (root / 'game/red4ext/plugins/ArchiveXL/ArchiveXL.log').is_symlink()
       and (root / 'logs/ArchiveXL.log').read_bytes() == b'benign external log target must not be touched')

    for kind in ['added_r6_script', 'added_unknown_plugin', 'removed_source', 'renamed_source',
                 'linked_source', 'linked_plugin_directory', 'input_hash_drift', 'proof_hash_drift']:
        root, m = fixture(kind)
        known = root / 'game/r6/scripts/OtherScript/External.reds'
        if kind == 'added_r6_script':
            put(root / 'game/r6/scripts/NewSource/added.reds', b'new uncompiled source')
        elif kind == 'added_unknown_plugin':
            put(root / 'game/red4ext/plugins/UnregisteredNewPlugin/Scripts/added.reds', b'new plugin source')
        elif kind == 'removed_source':
            assert known.resolve().is_relative_to(domain.resolve())
            known.unlink()
        elif kind == 'renamed_source':
            known.rename(known.with_name('Renamed.reds'))
        elif kind == 'linked_source':
            target = root / 'same_bytes.txt'
            put(target, known.read_bytes())
            assert known.resolve().is_relative_to(domain.resolve())
            known.unlink()
            known.symlink_to(target)
        elif kind == 'linked_plugin_directory':
            target = root / 'alias_target'
            target.mkdir()
            (root / 'game/red4ext/plugins/LinkedPlugin').symlink_to(target, target_is_directory=True)
        elif kind == 'input_hash_drift':
            put(known, b'drift at known original path')
        else:
            put(root / 'proof.json', b'drifted proof')
        before = snapshot(root / 'game'), snapshot(root / 'saves')
        result = call(root, 'Install', expected=False)
        ck(kind + ' refuses before recovery creation or game/save writes',
           not (root / 'recovery').exists() and before == (snapshot(root / 'game'), snapshot(root / 'saves')))
        if kind not in ['input_hash_drift', 'proof_hash_drift']:
            ck(kind + ' fails specifically on inventory or reparse guard',
               'source inventory drift' in result.stderr or 'compiler inventory entry refused' in result.stderr
               or 'Linked path refused' in result.stderr)

    root, m = fixture('hard_interruption_populated_inventory')
    before = snapshot(root / 'saves')
    call(root, 'Install', ['-FailurePoint', 'CrashAfterSecondReplace'], expected=False)
    call(root, 'Recover')
    call(root, 'Verify', ['-ExpectedState', 'Before'])
    ck('new inventory guard preserves interrupted transaction recovery protocol',
       before == snapshot(root / 'saves') and all(sha(root / 'game' / r['path']) == r['before'] for r in m['files']))
    root, m = fixture('actual_Core51_final_engine', actual=True)
    before = snapshot(root / 'saves')
    call(root, 'Preflight')
    call(root, 'Install')
    call(root, 'Verify')
    call(root, 'ValidateRollback')
    ck('actual final Core51 package installed exactly on final engine',
       all(sha(root / 'game' / r['path']) == r['after'] for r in m['files']))
    call(root, 'Rollback')
    call(root, 'Verify', ['-ExpectedState', 'Before'])
    ck('actual Core51 final engine rollback restores QR8 and preserves saves and log target',
       before == snapshot(root / 'saves') and all(sha(root / 'game' / r['path']) == r['before'] for r in m['files'])
       and (root / 'logs/ArchiveXL.log').read_bytes() == b'benign external log target must not be touched')
    ck('all reviewed final coordinator inputs unchanged throughout independent controls', all(sha(p) == h for p, h in pins.items()))
    result = {'status': 'PASS_INDEPENDENT_FINAL_QR14_POPULATED_INVENTORY_AND_148_SOURCE_INTEGRATION',
              'source_pins': pins, 'checks': checks, 'command_count': len(commands), 'commands': commands,
              'fixture_domain': str(domain), 'real_game_or_candidate_writes': 0, 'real_save_writes': 0,
              'game_launches': 0, 'compiled_sha256': cr['compiled_sha256'],
              'limits': ['No real installation or protected-directory write permission test.',
                         'Offline integration and transaction fixtures do not establish gameplay or executing saved owner compatibility.']}
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'commands': len(commands), 'out': str(output)}))


if __name__ == '__main__':
    main()
