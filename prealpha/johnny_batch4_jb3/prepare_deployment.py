"""Bind the staged cumulative JB3 build to a fresh guarded JB1 upgrade."""

import importlib.util
from pathlib import Path

from prepare import ARCHIVE, HERE, INSTALLED, JB2, OUT, XL, inventory
from resources import read, sha, write

TRANSACTION = 'core_manifest_01.json'
SOURCE_PACKAGE = Path(read(INSTALLED)['source_candidate']) / 'package'
ALLOWED = [ARCHIVE, 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds',
           'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS25.reds']
DEPLOYMENT = HERE / 'deployment_01'

# Use only the predecessor's pure file and save readers. Its main function
# writes a pinned historical candidate and is never invoked here.
spec = importlib.util.spec_from_file_location('jb1_deploy_readers', INSTALLED.parents[1] / 'prepare_deployment.py')
jb1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jb1)
checked, save_inventory = jb1.checked, jb1.save_inventory


def derive_installer(manifest_path, previous_manifest, installer_path):
    source = installer_path.read_text(encoding='utf-8-sig')
    edits = {
        '# JB2 deployment. User approved Batch 3 and the Prophet entry exclusion.':
            '# JB3 deployment. User approved installation of the cumulative Johnny removal build.',
        "$PinnedCoreManifestSHA='" + sha(previous_manifest) + "'":
            "$PinnedCoreManifestSHA='" + sha(manifest_path) + "'",
        'PTFR_JB2_JOURNAL_V1': 'PTFR_JB3_JOURNAL_V1',
        'PTFR_JB2_CORE_V1': 'PTFR_JB3_CORE_V1',
        "$manifest.source_epoch -cne 'JB2'": "$manifest.source_epoch -cne 'JB3'",
        'recovery/core_jb2_01': 'recovery/core_jb3_01',
    }
    for old, new in edits.items():
        assert source.count(old) == (2 if old == 'PTFR_JB2_JOURNAL_V1' else 1), old
        source = source.replace(old, new)
    installer = HERE / 'deploy_core.ps1'
    with installer.open('x', encoding='utf-8', newline='\n') as f:
        f.write(source)
    write(HERE / 'installer_review.json', {
        'status': 'PASS_JB3_THREE_FILE_TRANSACTION_LITERAL_DELTA',
        'predecessor_installer_sha256': sha(installer_path),
        'installer_sha256': sha(installer),
        'manifest_sha256': sha(manifest_path),
        'allowed_replacements': ALLOWED,
        'substitutions': edits,
    })
    # Keep the same full-payload and interruption fixtures, with a fresh
    # manifest, installer and workspace fixture roots.
    fixture = (JB2 / 'test_deployment.py').read_text(encoding='utf-8-sig').replace('JB2', 'JB3')
    with (HERE / 'test_deployment.py').open('x', encoding='utf-8', newline='\n') as f:
        f.write(fixture)


def main():
    manifest = HERE / TRANSACTION
    assert all(not p.exists() for p in (
        manifest, HERE / 'deploy_core.ps1', HERE / 'readiness.json',
        DEPLOYMENT / 'save_inventory_preparation.json', HERE / 'recovery/core_jb3_01'))
    checkpoint_path = HERE / 'checkpoint.json'
    checkpoint = read(checkpoint_path)
    assert checkpoint['status'] == 'JB3_BATCH4_STAGED_OFFLINE'
    assert checkpoint['installed_epoch'] == 'JB1'
    assert checkpoint['changes_relative_to_installed'] == ALLOWED
    assert checkpoint['package_manifest_sha256'] == '2CCDB16A29B7EBE3AC43193D360839BF5543EC34677179D9B7921DD91C7CEBDF'
    package_manifest = checked(HERE / checkpoint['package_manifest'], checkpoint['package_manifest_sha256'])
    package = read(package_manifest)
    assert package['status'] == 'STAGED_JB3_READBACK_VERIFIED' and package['epoch'] == 'JB3'
    assert package['archive_payloads'] == checkpoint['archive_payloads'] == 1636
    installed = read(checked(INSTALLED, checkpoint['installed_manifest_sha256']))
    game = Path(installed['game_root'])
    assert installed['core_epoch'] == 'JB1'
    bundle = checked(HERE / checkpoint['package'], checkpoint['package_sha256'])
    proofs = [checked(HERE / p, digest) for p, digest in checkpoint['proofs'].items()]
    rb = read(HERE / 'archive_readback_01.json')
    validation = read(HERE / 'verification_01.json')
    assert rb['status'] == 'PASS_JB3_ARCHIVE_AND_PROVIDERS'
    assert rb['archive_sha256'] == checkpoint['archive_sha256']
    assert package['source_resources'] == {r['depot']: r['sha256'] for r in rb['resources']}
    assert len({r['key'] for r in rb['resources']}) == 1636
    assert validation['status'] == 'PASS_JB3_COOKED_AND_BOUNDED_FLOW'
    assert validation['fixture_count'] == checkpoint['fixture_count'] == 41

    provider_path = DEPLOYMENT / 'provider_preflight.json'
    provider = read(provider_path)
    assert provider['status'] == 'PASS_JB3_CUMULATIVE_DEPOT_PROVIDERS'
    assert provider['new_xl_registrations'] == 0
    assert provider['unoccupied_alias_count'] == 55
    assert provider['provider_key_count'] == len(provider['keys'])
    assert provider['archive_count'] == len(provider['archives'])

    old = {row['path']: row for row in installed['core_files']}
    new = {row['path']: row for row in package['files']}
    assert len(old) == len(new) == 51 and old.keys() == new.keys()
    pkg = OUT / 'package'
    assert inventory(pkg) == {p: r['sha256'] for p, r in new.items()}
    assert old[XL]['sha256'] == new[XL]['sha256'] == provider['archivexl_sha256']
    assert new[ARCHIVE]['sha256'] == rb['archive_sha256']
    files = []
    for rel in sorted(new):
        before, after = old[rel], new[rel]
        checked(game / rel, before['sha256'])
        assert (game / rel).stat().st_size == before['bytes']
        assert (pkg / rel).stat().st_size == after['bytes']
        files.append({'path': rel, 'before': before['sha256'], 'before_bytes': before['bytes'],
                      'after': after['sha256'], 'after_bytes': after['bytes']})
    assert [r['path'] for r in files if r['before'] != r['after']] == ALLOWED

    review = read(JB2 / 'installer_review.json')
    assert review['status'] == 'PASS_JB2_THREE_FILE_TRANSACTION_LITERAL_DELTA'
    prior_path = checked(JB2 / TRANSACTION, '6F56198224824B69F5073CC95A7D7708A9F08262707C48C61CE6A61593F9F1F4')
    assert sha(prior_path) == review['manifest_sha256']
    installer_path = checked(JB2 / 'deploy_core.ps1', 'BDE3D32F47AC7D98FBDCFDED0FC477335B33B2F7C0F2E83F2ABFBB2198A83767')
    assert sha(installer_path) == review['installer_sha256']
    transaction = read(prior_path)
    assert transaction['game_root'] == installed['game_root'] and transaction['save_root'] == installed['save_root']
    assert transaction['predecessor_epoch'] == installed['core_epoch']
    dependencies = {r['path']: (r['sha256'], r['bytes']) for r in transaction['required_files']}
    assert len(dependencies) == 26
    assert dependencies == {r['path']: (r['sha256'], r['bytes']) for r in installed['required_files']}
    for rel, (digest, size) in dependencies.items():
        checked(game / rel, digest)
        assert (game / rel).stat().st_size == size
    c_path = checked(JB2 / 'compile_01/result.json', validation['compile_identity']['sha256'])
    compilation = read(c_path)
    assert compilation['status'] == 'PASS_JB2_COMPLETE_SOURCE_COMPILE' and compilation['exit_code'] == 0
    assert compilation['source_count'] == len(compilation['sources']) == 148
    assert transaction['compile_inputs'] == compilation['input_pins']
    for p, digest in compilation['input_pins'].items():
        checked(p, digest)
    for p, row in compilation['sources'].items():
        rel = Path(p).relative_to(game).as_posix()
        digest = new[rel]['sha256'] if rel in new else compilation['input_pins'][p]
        assert digest == row['sha256'], rel

    saves = save_inventory(installed['save_root'])
    master = {r['path']: r for r in transaction['protected_saves']}
    current = {r['path']: r for r in saves}
    assert len(master) == 3 and all(current[p] == r for p, r in master.items())
    save_path = DEPLOYMENT / 'save_inventory_preparation.json'
    write(save_path, {'status': 'READ_ONLY_CURRENT_SAVE_INVENTORY', 'files': saves,
                      'file_count': len(saves), 'game_writes': 0, 'save_writes': 0})
    proofs += [checkpoint_path, package_manifest, INSTALLED, c_path, provider_path, save_path]
    transaction.update(
        schema='PTFR_JB3_CORE_V1', source_epoch='JB3', predecessor_epoch='JB1',
        package_root=str(pkg), zip=str(bundle), zip_sha256=sha(bundle),
        files=files, changing_paths=ALLOWED,
        working_save_files=[r for r in saves if r['path'] not in master],
        compile_coverage={'mode': 'COMPLETE_JB2_COMPILE_SAME_CANDIDATE_SOURCE_BYTES',
                          'sources': 148, 'compiled_sha256': compilation['compiled_sha256'],
                          'new_compile_run': False, 'scripts_changed': 2},
        proofs=[{'path': str(p), 'sha256': sha(p)} for p in proofs],
        scope='Cumulative approved Johnny removal through Batch 4 and the staged R6.3 Prophet entry exclusion.',
        rollback_policy='Restore the exact JB1 combined archive and two REDscript files from this transaction recovery.',
    )
    write(manifest, transaction)
    derive_installer(manifest, prior_path, installer_path)
    print(f'Prepared exact three-file JB3 transaction with {len(saves)} current save-file pins.')


if __name__ == '__main__':
    main()
