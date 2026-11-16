"""Seal JB1 Core51 and prepare a guarded SD1 -> JB1 archive transaction.

Preparation and isolated fixtures do not authorize a real deployment.
"""
from pathlib import Path
import copy
import hashlib
import os
import zipfile
from prepare import HERE, WS, BASE, OUT, ARCHIVE, read, sha, write

SD1 = WS / 'prealpha/sweet_dreams_sd1'
SOURCE_PACKAGE = BASE / 'package'
TRANSACTION = 'core_manifest_01.json'
ALLOWED = [ARCHIVE]


def checked(path, digest):
    path = Path(path)
    assert sha(path) == digest, path
    return path


def save_inventory(root):
    root = Path(root)
    assert root.is_dir()
    for ancestor in [root, *root.parents]:
        assert not (ancestor.stat().st_file_attributes & 0x400), ancestor
    rows = []
    for directory, subdirs, files in os.walk(root, followlinks=False):
        for name in subdirs + files:
            p = Path(directory) / name
            assert not (p.stat(follow_symlinks=False).st_file_attributes & 0x400), p
        for name in files:
            p = Path(directory) / name
            rows.append({'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    return sorted(rows, key=lambda x: x['path'])


def main():
    assert not (HERE / TRANSACTION).exists() and not (HERE / 'deploy_core.ps1').exists()
    plan = read(HERE / 'input_04/plan.json')
    installed = read(checked(plan['installed_baseline'], plan['installed_baseline_sha256']))
    baseline = read(checked(plan['baseline_package'], plan['baseline_package_sha256']))
    verification = read(HERE / 'verification_04.json')
    flows = read(HERE / 'flow_fixtures_04.json')
    archive = read(HERE / 'archive_readback_04.json')
    compilation = read(HERE / 'compile_inventory_04.json')
    assert verification['status'] == 'PASS_JB1_COOKED_DIALOGUE_PRESENTATION_AND_WIRING_CONSTRAINTS'
    assert flows['status'] == 'PASS_JB1_BOUNDED_FLOW_AND_NATIVE_GUARD_FIXTURES'
    assert verification['plan_sha256'] == flows['plan_sha256'] == sha(HERE / 'input_04/plan.json')
    assert archive['status'] == 'PASS_ALL_JB1_ARCHIVE_MEMBERS'
    assert compilation['status'] == 'PASS_UNCHANGED_CURRENT_SOURCES_MATCH_PE1_COMPLETE_COMPILE'
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert len(members) == len({r['key'] for r in archive['resources']}) == 1581
    assert set(members) == set(baseline['source_resources'])
    changed = sorted(d for d, h in members.items() if h != baseline['source_resources'][d])
    assert changed == sorted(e['depot'] for e in plan['edits']) and len(changed) == 13
    for depot, digest in members.items():
        checked(OUT / 'archive_source' / depot, digest)
    game = Path(installed['game_root'])
    files = {p.relative_to(OUT / 'package').as_posix(): p for p in (OUT / 'package').rglob('*') if p.is_file()}
    old_files = {r['path']: r for r in installed['core_files']}
    assert set(files) == set(old_files) and len(files) == 51
    rows = []
    for rel, old in sorted(old_files.items()):
        checked(game / rel, old['sha256'])
        p = files[rel]
        rows.append({'path': rel, 'before': old['sha256'], 'before_bytes': old['bytes'],
                     'after': sha(p), 'after_bytes': p.stat().st_size})
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    assert next(r['after'] for r in rows if r['path'] == ARCHIVE) == archive['archive_sha256']
    for row in installed['required_files']:
        checked(game / row['path'], row['sha256'])
    write(OUT / 'package_manifest.json', {'status': 'STAGED_JB1_READBACK_VERIFIED', 'epoch': 'JB1', 'predecessor': 'SD1',
          'files': [{'path': r['path'], 'sha256': r['after'], 'bytes': r['after_bytes']} for r in rows],
          'source_resources': members, 'changed_paths': ALLOWED, 'changed_depots': changed,
          'archive_payloads': 1581, 'retained_archive_members': 1568, 'installed': False,
          'gameplay_validation': 'PENDING_SUPPORTED_PRE_SCENE_FIXTURES'})
    zip_path = HERE / 'JB1_Core51_04.zip'
    assert not zip_path.exists()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for rel, path in sorted(files.items()):
            z.write(path, rel)
    with zipfile.ZipFile(zip_path) as z:
        assert set(z.namelist()) == set(files) and z.testzip() is None
        for row in rows:
            assert hashlib.sha256(z.read(row['path'])).hexdigest().upper() == row['after']
    old = read(SD1 / TRANSACTION)
    # Immutable master pins retain their previous identity. Current working saves
    # are inventoried afresh; natural human progress is never restored/reset.
    protected = {r['path']: r for r in old['protected_saves']}
    for row in protected.values():
        checked(Path(old['save_root']) / row['path'], row['sha256'])
    saves = save_inventory(old['save_root'])
    assert set(protected) <= {r['path'] for r in saves}
    write(HERE / 'save_inventory_preparation_04.json', {'status': 'READ_ONLY_CURRENT_SAVE_INVENTORY',
          'save_root': old['save_root'], 'files': saves, 'file_count': len(saves),
          'limits': 'Preparation-time inventory. Actual deployment must take a fresh snapshot and preserve natural human progress.',
          'game_writes': 0, 'save_writes': 0})
    assert all(sha(p) == h for p, h in compilation['input_pins'].items())
    proofs = [HERE / name for name in ['input_04/plan.json', 'source_01/manifest.json', 'readback_04/manifest.json',
              'verification_04.json', 'flow_fixtures_04.json', 'compile_inventory_04.json', 'archive_readback_04.json',
              'save_inventory_preparation_04.json']] + [OUT / 'package_manifest.json']
    transaction = copy.deepcopy(old)
    transaction.update(schema='PTFR_JB1_CORE_V1', source_epoch='JB1', predecessor_epoch='SD1',
        package_root=str(OUT / 'package'), zip=str(zip_path), zip_sha256=sha(zip_path), files=rows,
        changing_paths=ALLOWED, compile_inputs=compilation['input_pins'],
        working_save_files=[r for r in saves if r['path'] not in protected],
        compile_coverage={'mode': 'UNCHANGED_CURRENT_REDS_MATCH_PE1_COMPILED_INPUTS', 'sources': 148, 'input_pins': 151,
                         'compiled_sha256': compilation['compiled_sha256'], 'new_compile_run': False,
                         'scripts_changed': 0, 'timestamp_sidecar': compilation['timestamp_sidecar']},
        proofs=[{'path': str(p), 'sha256': sha(p)} for p in proofs],
        scope='User-approved five-quest Johnny dialogue, V reaction, menu and presentation removal plus reviewed native skips. Twelve private scenes and one Small Man cleanup wait. Only the existing combined archive changes. No quest reset, saved-owner restart or admission change.',
        rollback_policy='Restore the exact SD1 archive from this transaction recovery. File rollback does not undo gameplay saves.')
    write(HERE / TRANSACTION, transaction)
    review = read(SD1 / 'installer_review.json')
    source = checked(SD1 / 'deploy_core.ps1', review['installer_sha256']).read_text(encoding='utf-8-sig')
    changes = {
        '# SD1 deployment. User requested Sweet Dreams Johnny presentation cleanup.': '# JB1 deployment. User approved the five-quest Johnny removal and native skips.',
        '# Derived from the reviewed KM2 transaction. Only the consolidated archive may change.': '# Derived from the reviewed SD1 transaction. Only the consolidated archive may change.',
        "$PinnedCoreManifestSHA='" + sha(SD1 / TRANSACTION) + "'": "$PinnedCoreManifestSHA='" + sha(HERE / TRANSACTION) + "'",
        'PTFR_SD1_JOURNAL_V1': 'PTFR_JB1_JOURNAL_V1',
        "'PTFR_SD1_CORE_V1'": "'PTFR_JB1_CORE_V1'",
        "$manifest.source_epoch -cne 'SD1' -or $manifest.predecessor_epoch -cne 'KM2'": "$manifest.source_epoch -cne 'JB1' -or $manifest.predecessor_epoch -cne 'SD1'",
        "('recovery/core_sd1_01')": "('recovery/core_jb1_01')",
    }
    for before, after in changes.items():
        assert source.count(before) == (2 if before == 'PTFR_SD1_JOURNAL_V1' else 1), before
        source = source.replace(before, after)
    with (HERE / 'deploy_core.ps1').open('x', encoding='utf-8', newline='\n') as f:
        f.write(source)
    write(HERE / 'installer_review.json', {'status': 'PASS_JB1_ONE_ARCHIVE_TRANSACTION_LITERAL_DELTA',
          'predecessor_installer_sha256': review['installer_sha256'], 'installer_sha256': sha(HERE / 'deploy_core.ps1'),
          'manifest_sha256': sha(HERE / TRANSACTION), 'allowed_replacements': ALLOWED, 'reviewed_literal_changes': changes,
          'transaction_functions': 'Inherited unchanged; only epoch, manifest pin, recovery namespace and scope comments differ.',
          'package_member_count': 51, 'archive_member_count': 1581, 'unchanged_payloads': 1568})
    fixture = (SD1 / 'test_deployment.py').read_text(encoding='utf-8-sig')
    for before, after in [('SD1 one-archive', 'JB1 one-archive'), ('PASS_SD1_ONE_ARCHIVE_DEPLOYMENT_FIXTURES', 'PASS_JB1_ONE_ARCHIVE_DEPLOYMENT_FIXTURES')]:
        assert fixture.count(before) == 1
        fixture = fixture.replace(before, after)
    with (HERE / 'test_deployment.py').open('x', encoding='utf-8', newline='\n') as f:
        f.write(fixture)
    print('Sealed JB1 Core51, full ZIP readback and guarded one-archive transaction. Not installed.')


if __name__ == '__main__':
    main()
