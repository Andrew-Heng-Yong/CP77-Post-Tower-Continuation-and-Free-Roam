"""Seal the exact JB2 package and derive its three-file guarded transaction."""

import hashlib
import importlib.util
from pathlib import Path
import zipfile

from prepare import ARCHIVE, BASE, HERE, INPUT, INSTALLED, OUT, read, sha, write

TRANSACTION = 'core_manifest_01.json'
SOURCE_PACKAGE = BASE / 'package'
ALLOWED = [ARCHIVE, 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds',
           'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS25.reds']

# Reuse the predecessor's read-only save census and byte verifier. Its main
# function targets the pinned JB1 outputs and is never invoked here.
spec = importlib.util.spec_from_file_location('jb1_seal_helpers', BASE.parent / 'prepare_deployment.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
checked, save_inventory = previous.checked, previous.save_inventory


def seal(plan, rb):
    baseline = read(checked(plan['baseline_package'], plan['baseline_package_sha256']))
    installed = read(checked(INSTALLED, plan['installed_baseline_sha256']))
    game = Path(installed['game_root'])
    resources = {r['depot']: r['sha256'] for r in rb['resources']}
    prior = baseline['source_resources']
    new = set(resources) - set(prior)
    assert set(prior) <= set(resources)
    changed = {p for p, h in resources.items() if p in prior and h != prior[p]}
    assert new == {r['depot'] for r in plan['edits'] if r['is_new']}
    assert changed == {r['depot'] for r in plan['edits'] if not r['is_new']}
    assert len(resources) == len({r['key'] for r in rb['resources']}) == 1603
    assert len(prior) == 1581 and len(changed) == 11 and len(new) == 22
    cooked = read(HERE / 'readback_02/manifest.json')
    assert {r['depot']: r['sha256'] for r in cooked['resources']} == {
        p: resources[p] for p in new | changed}

    pkg = OUT / 'package'
    files = {p.relative_to(pkg).as_posix(): p for p in pkg.rglob('*') if p.is_file()}
    old = {r['path']: r for r in installed['core_files']}
    assert set(files) == set(old) and len(files) == 51
    rows = []
    for rel, path in sorted(files.items()):
        checked(game / rel, old[rel]['sha256'])
        rows.append({'path': rel, 'before': old[rel]['sha256'], 'before_bytes': old[rel]['bytes'],
                     'after': sha(path), 'after_bytes': path.stat().st_size})
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    checked(pkg / ARCHIVE, rb['archive_sha256'])
    assert len(installed['required_files']) == 26
    for row in installed['required_files']:
        checked(game / row['path'], row['sha256'])
    manifest = OUT / 'package_manifest.json'
    write(manifest, {'status': 'STAGED_JB2_READBACK_VERIFIED', 'epoch': 'JB2', 'predecessor': 'JB1',
          'files': [{'path': r['path'], 'sha256': r['after'], 'bytes': r['after_bytes']} for r in rows],
          'archive_payloads': len(resources), 'source_resources': resources,
          'new_depots': sorted(new), 'changed_depots': sorted(changed), 'changed_paths': ALLOWED,
          'retained_archive_members': len(prior) - len(changed), 'new_xl_registrations': 0,
          'installed': False, 'gameplay_validation': 'PENDING_GENUINE_PRE_SCENE_FIXTURES'})
    zip_path = HERE / 'JB2_Core51_02.zip'
    with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for rel, path in sorted(files.items()):
            bundle.write(path, rel)
    with zipfile.ZipFile(zip_path) as bundle:
        assert set(bundle.namelist()) == set(files) and bundle.testzip() is None
        for row in rows:
            assert hashlib.sha256(bundle.read(row['path'])).hexdigest().upper() == row['after']
    return rows, manifest, zip_path


def prepare_installer(rows, manifest, zip_path, compilation):
    jb1 = BASE.parent
    before = jb1 / TRANSACTION
    review = read(jb1 / 'installer_review.json')
    transaction = read(checked(before, review['manifest_sha256']))
    source_path = checked(jb1 / 'deploy_core.ps1', review['installer_sha256'])
    saves = save_inventory(transaction['save_root'])
    master = {r['path']: r for r in transaction['protected_saves']}
    current = {r['path']: r for r in saves}
    assert all(current[p] == row for p, row in master.items())
    for p, digest in compilation['input_pins'].items():
        checked(p, digest)
    inventory = HERE / 'save_inventory_preparation_02.json'
    write(inventory, {'status': 'READ_ONLY_CURRENT_SAVE_INVENTORY', 'save_root': transaction['save_root'],
          'files': saves, 'file_count': len(saves), 'game_writes': 0, 'save_writes': 0})
    proofs = [INPUT / 'plan.json', HERE / 'readback_02/manifest.json', HERE / 'verification_02.json',
              HERE / 'archive_readback_02.json', HERE / 'compile_01/result.json', inventory, manifest]
    transaction.update(
        schema='PTFR_JB2_CORE_V1', source_epoch='JB2', predecessor_epoch='JB1',
        package_root=str(OUT / 'package'), zip=str(zip_path), zip_sha256=sha(zip_path), files=rows,
        changing_paths=ALLOWED, compile_inputs=compilation['input_pins'],
        working_save_files=[r for r in saves if r['path'] not in master],
        compile_coverage={'mode': 'COMPLETE_REGISTERED_SOURCE_COMPILE', 'sources': 148,
                          'compiled_sha256': compilation['compiled_sha256'], 'new_compile_run': True,
                          'scripts_changed': 2},
        proofs=[{'path': str(p), 'sha256': sha(p)} for p in proofs],
        scope='Batch 3 dialogue and Johnny presentation cleanup with approved local rewires, plus prospective S23 and S25 Prophet entry exclusion.',
        rollback_policy='Restore the exact JB1 archive and two REDscript files from this transaction recovery.')
    target = HERE / TRANSACTION
    write(target, transaction)
    source = source_path.read_text(encoding='utf-8-sig')
    substitutions = {
        '# JB1 deployment. User approved the five-quest Johnny removal and native skips.':
            '# JB2 deployment. User approved Batch 3 and the Prophet entry exclusion.',
        '# Derived from the reviewed SD1 transaction. Only the consolidated archive may change.':
            '# Derived from JB1. The consolidated archive and the two listed scripts may change.',
        '# The one-archive replacement is journaled, with per-file atomic replacement; Windows':
            '# The three-file replacement is journaled, with per-file atomic replacement; Windows',
        "$PinnedCoreManifestSHA='" + sha(before) + "'":
            "$PinnedCoreManifestSHA='" + sha(target) + "'",
        'PTFR_JB1_JOURNAL_V1': 'PTFR_JB2_JOURNAL_V1',
        "'PTFR_JB1_CORE_V1'": "'PTFR_JB2_CORE_V1'",
        "$manifest.source_epoch -cne 'JB1' -or $manifest.predecessor_epoch -cne 'SD1'":
            "$manifest.source_epoch -cne 'JB2' -or $manifest.predecessor_epoch -cne 'JB1'",
        "('recovery/core_jb1_01')": "('recovery/core_jb2_01')",
        f"$wanted=@('{ARCHIVE}')": '$wanted=@(' + ','.join(f"'{p}'" for p in ALLOWED) + ')',
        '$changes.Count -ne 1': '$changes.Count -ne 3',
        'Core51/one-existing-archive scope drift': 'Core51/three-existing-file scope drift',
    }
    for old, new in substitutions.items():
        assert source.count(old) == (2 if old == 'PTFR_JB1_JOURNAL_V1' else 1), old
        source = source.replace(old, new)
    installer = HERE / 'deploy_core.ps1'
    with installer.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)
    write(HERE / 'installer_review.json', {
        'status': 'PASS_JB2_THREE_FILE_TRANSACTION_LITERAL_DELTA',
        'predecessor_installer_sha256': review['installer_sha256'], 'installer_sha256': sha(installer),
        'manifest_sha256': sha(target), 'allowed_replacements': ALLOWED, 'substitutions': substitutions})
    fixture = (jb1 / 'test_deployment.py').read_text(encoding='utf-8-sig')
    changes = {
        'JB1 one-archive': 'JB2 three-file',
        'PASS_JB1_ONE_ARCHIVE_DEPLOYMENT_FIXTURES': 'PASS_JB2_THREE_FILE_DEPLOYMENT_FIXTURES',
        '("AfterFirstReplace", "BeforeReceipt", "CrashAfterFirstReplace", "CrashBeforeReceipt")':
            '("AfterFirstReplace", "AfterSecondReplace", "CrashAfterSecondReplace", "CrashBeforeReceipt")',
    }
    for old, new in changes.items():
        assert fixture.count(old) == 1, old
        fixture = fixture.replace(old, new)
    with (HERE / 'test_deployment.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(fixture)


def main():
    assert not (HERE / TRANSACTION).exists() and not (HERE / 'deploy_core.ps1').exists()
    plan_path = INPUT / 'plan.json'
    plan = read(plan_path)
    proof = read(HERE / 'verification_02.json')
    archive = read(HERE / 'archive_readback_02.json')
    compilation = read(HERE / 'compile_01/result.json')
    assert proof['status'] == 'PASS_JB2_COOKED_AND_BOUNDED_FLOW'
    assert archive['status'] == 'PASS_JB2_ARCHIVE_AND_PROVIDERS'
    assert proof['plan_sha256'] == archive['plan_sha256'] == sha(plan_path)
    assert compilation['status'] == 'PASS_JB2_COMPLETE_SOURCE_COMPILE'
    assert compilation['overlays'] == plan['scripts']
    rows, manifest, zip_path = seal(plan, archive)
    prepare_installer(rows, manifest, zip_path, compilation)
    print('Sealed and verified the JB2 Core51 ZIP and three-file transaction.')


if __name__ == '__main__':
    main()
