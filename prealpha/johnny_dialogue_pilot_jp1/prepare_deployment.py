"""Seal JP1 Core51 and derive a guarded one-archive HH1 successor transaction."""
import copy
import zipfile
from pathlib import Path
from prepare_changes import HERE, WS, HH1, ARCHIVE, read, sha, write, files

ALLOWED = [ARCHIVE]
TRANSACTION = 'core_manifest_01.json'
BASE_INSTALLER_SHA = '368EEC162431322C3C82A0DA9932D375ED030955BFB7B6FBB70D037F7D58C4A9'
SOURCE_PACKAGE = HH1 / 'candidate_01/package'


def checked(path, digest):
    assert sha(path) == digest, path
    return Path(path)


def main():
    assert not (HERE / TRANSACTION).exists() and not (HERE / 'deploy_core.ps1').exists()
    plan = read(HERE / 'input_03/plan.json')
    installed = read(checked(Path(plan['installed_baseline']), plan['installed_baseline_sha256']))
    before_package = read(checked(Path(plan['baseline_package']), plan['baseline_package_sha256']))
    candidate = Path(plan['candidate_directory'])
    package = candidate / 'package'
    game = Path(installed['game_root'])
    archive = read(HERE / 'validation_05/archive_readback.json')
    scenes = read(HERE / 'validation_05/scene_verification.json')
    providers = read(HERE / 'validation_05/provider_collisions.json')
    assert archive['status'] == 'PASS_ALL_JP1_ARCHIVE_MEMBERS'
    assert scenes['spoken_events_removed'] == 37 and scenes['options_bypassed_in_normal_entry_flow'] == 4
    assert providers['status'] == 'PASS_EXACT_PRIVATE_PROVIDERS_NO_NEW_NAMESPACES'
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert len(members) == len({r['key'] for r in archive['resources']}) == 1581
    old_members = before_package['source_resources']
    assert set(members) == set(old_members)
    changed_depots = sorted(k for k in members if members[k] != old_members[k])
    assert changed_depots == sorted(e['resource']['depot'] for e in plan['edits'])
    after_files = files(package)
    before_files = {r['path']: r for r in installed['core_files']}
    assert set(after_files) == set(before_files) and len(after_files) == 51
    rows = []
    for rel, old in sorted(before_files.items()):
        checked(game / rel, old['sha256'])
        after = after_files[rel]
        rows.append({'path': rel, 'before': old['sha256'], 'before_bytes': old['bytes'],
                     'after': sha(after), 'after_bytes': after.stat().st_size})
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    assert next(r for r in rows if r['path'] == ARCHIVE)['after'] == archive['archive_sha256']
    for row in installed['required_files']:
        checked(game / row['path'], row['sha256'])
    package_manifest = {'status': 'STAGED_JP1_READBACK_VERIFIED', 'epoch': 'JP1', 'predecessor': 'HH1',
                        'files': [{'path': r['path'], 'sha256': r['after'], 'bytes': r['after_bytes']} for r in rows],
                        'source_resources': members, 'changed_paths': ALLOWED, 'changed_depots': changed_depots,
                        'retained_archive_members': 1578, 'archive_payloads': 1581, 'installed': False,
                        'gameplay_validation': 'PENDING_USER_TEST'}
    write(candidate / 'package_manifest.json', package_manifest)
    zip_path = HERE / 'JP1_Core51_01.zip'
    assert not zip_path.exists()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for rel, path in sorted(after_files.items()):
            z.write(path, rel)
    with zipfile.ZipFile(zip_path) as z:
        assert set(z.namelist()) == set(after_files) and z.testzip() is None
        import hashlib
        for r in rows:
            assert hashlib.sha256(z.read(r['path'])).hexdigest().upper() == r['after']
    old = read(HH1 / TRANSACTION)
    compile_pins = dict(old['compile_inputs'])
    timestamp_updates = []
    for path, expected in list(compile_pins.items()):
        actual = sha(path)
        if actual != expected:
            assert Path(path) == game / 'r6/cache/final.redscripts.ts' and Path(path).stat().st_size == 16, path
            timestamp_updates.append({'path': path, 'old': expected, 'current': actual, 'reason': 'Normal 16-byte runtime cache timestamp refresh; source and compiled bytes remain pinned.'})
            compile_pins[path] = actual
    assert sum(Path(p).suffix.lower() == '.reds' for p in compile_pins) == 148
    proofs = [HERE / 'input_03/plan.json', HERE / 'readback_03/cooked.json',
              HERE / 'validation_05/scene_verification.json', HERE / 'validation_05/archive_readback.json',
              HERE / 'validation_05/provider_collisions.json', candidate / 'package_manifest.json']
    manifest = copy.deepcopy(old)
    manifest.update(schema='PTFR_JP1_CORE_V1', source_epoch='JP1', predecessor_epoch='HH1',
                    package_root=str(package), zip=str(zip_path), zip_sha256=sha(zip_path),
                    files=rows, changing_paths=ALLOWED, compile_inputs=compile_pins,
                    compile_coverage=old['compile_coverage'] | {'mode': 'UNCHANGED_REDS_CURRENT_HASHES_VERIFIED', 'timestamp_updates': timestamp_updates},
                    proofs=[{'path': str(p), 'sha256': sha(p)} for p in proofs],
                    scope='Install the user-requested two-quest Johnny/V dialogue pilot for their in-game test; replace only the existing consolidated archive.',
                    rollback_policy='Restore the exact HH1 archive from this transaction recovery. File rollback does not undo saves.')
    write(HERE / TRANSACTION, manifest)
    source = checked(HH1 / 'deploy_core.ps1', BASE_INSTALLER_SHA).read_text(encoding='utf-8-sig')
    changes = {
        '# HH1 deployment. User authorized installation. Fixtures stay under this task.': '# JP1 deployment. User requested implementation for their in-game pilot test. Fixtures stay under this task.',
        '# Derived from the QR19 transaction. Only the archive and XL may change.': '# Derived from the reviewed HH1 transaction. Only the consolidated archive may change.',
        "$PinnedCoreManifestSHA='067481C8B6D41FF456DBBD62406F8F2F9665766A88AD29F6575309737DADB2FC'": "$PinnedCoreManifestSHA='" + sha(HERE / TRANSACTION) + "'",
        'PTFR_HH1_JOURNAL_V1': 'PTFR_JP1_JOURNAL_V1',
        "'PTFR_HH1_CORE_V1'": "'PTFR_JP1_CORE_V1'",
        "$manifest.source_epoch -cne 'HH1' -or $manifest.predecessor_epoch -cne 'QR19'": "$manifest.source_epoch -cne 'JP1' -or $manifest.predecessor_epoch -cne 'HH1'",
        "('recovery/core_hh1_01')": "('recovery/core_jp1_01')",
        "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl')": "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')",
        '$changes.Count -ne 2': '$changes.Count -ne 1',
        "'Core51/two-existing-file scope drift'": "'Core51/one-existing-archive scope drift'",
    }
    for old_text, new_text in changes.items():
        assert source.count(old_text) == (2 if old_text == 'PTFR_HH1_JOURNAL_V1' else 1), old_text
        source = source.replace(old_text, new_text)
    (HERE / 'deploy_core.ps1').write_text(source, encoding='utf-8')
    write(HERE / 'installer_review.json', {'status': 'PASS_JP1_ONE_ARCHIVE_TRANSACTION_DELTA',
          'predecessor_installer_sha256': BASE_INSTALLER_SHA, 'installer_sha256': sha(HERE / 'deploy_core.ps1'),
          'manifest_sha256': sha(HERE / TRANSACTION), 'allowed_replacements': ALLOWED,
          'reviewed_literal_changes': changes, 'transaction_functions': 'Inherited unchanged except the exact one-file allowlist gate and epoch/pin/recovery namespace.',
          'package_member_count': 51, 'archive_member_count': 1581, 'unchanged_payloads': 1578})
    print('Sealed Core51 package, exact one-archive transaction and reviewed installer delta; not installed.')


if __name__ == '__main__':
    main()
