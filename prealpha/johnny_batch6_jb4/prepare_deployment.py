"""Bind the combined build to a guarded four-file upgrade from JB3."""

from pathlib import Path

from baseline import ARCHIVE, BASE, HERE, INSTALLED, JB3, OUT, installed_baseline, inventory, plain, read, sha, write
from package_core import BUNDLE

TRANSACTION = 'core_manifest_01.json'
SOURCE_PACKAGE = BASE / 'package'
ALLOWED = [ARCHIVE, *(r['path'] for r in read(HERE / 'baseline.json')['scripts'])]


def checked(path, digest):
    path = Path(path)
    plain(path)
    assert sha(path) == digest, path
    return path


def saves_at(root):
    root = Path(root)
    return [{'path': rel, 'sha256': digest, 'bytes': (root / rel).stat().st_size}
            for rel, digest in sorted(inventory(root).items())]


def write_new(path, source):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)


def main():
    manifest_path = HERE / TRANSACTION
    installer = HERE / 'deploy_core.ps1'
    deployment = HERE / 'deployment_01'
    assert not manifest_path.exists() and not installer.exists() and not deployment.exists()
    installed = installed_baseline()
    old_tx = checked(JB3 / TRANSACTION, installed['core_transaction_sha256'])
    old_installer = checked(JB3 / 'deploy_core.ps1',
                            '85A849C1BDF5C1943514D4211235DD9A3AD26F357DC9D8B459D81BF69DF5FCDB')
    transaction = read(old_tx)
    assert transaction['source_epoch'] == 'JB3'
    assert transaction['required_files'] == installed['required_files']
    package_manifest = OUT / 'package_manifest.json'
    package = read(package_manifest)
    assert package['status'] == 'STAGED_JB4_READBACK_VERIFIED'
    checked(BUNDLE, package['zip_sha256'])
    proofs = [checked(HERE / p, h) for p, h in package['proofs'].items()]
    compile_proof = read(HERE / 'compile_01/result.json')
    assert compile_proof['source_count'] == 148 and len(compile_proof['input_pins']) == 151
    for p, digest in compile_proof['input_pins'].items():
        checked(p, digest)

    previous = {r['path']: r for r in installed['core_files']}
    candidate = {r['path']: r for r in package['files']}
    assert previous.keys() == candidate.keys() and len(candidate) == 51
    pkg = OUT / 'package'
    assert inventory(pkg) == {p: r['sha256'] for p, r in candidate.items()}
    files = [{'path': p, 'before': previous[p]['sha256'], 'before_bytes': previous[p]['bytes'],
              'after': candidate[p]['sha256'], 'after_bytes': candidate[p]['bytes']} for p in sorted(candidate)]
    assert [r['path'] for r in files if r['before'] != r['after']] == ALLOWED
    saves = saves_at(installed['save_root'])
    protected = {r['path']: r for r in transaction['protected_saves']}
    current = {r['path']: r for r in saves}
    assert len(protected) == 3 and all(current[p] == r for p, r in protected.items())
    deployment.mkdir()
    save_path = deployment / 'save_inventory_preparation.json'
    write(save_path, {'status': 'CURRENT_SAVE_INVENTORY', 'files': saves, 'file_count': len(saves)})
    transaction.update(
        schema='PTFR_JB4_CORE_V1', source_epoch='JB4', predecessor_epoch='JB3',
        package_root=str(pkg), zip=str(BUNDLE), zip_sha256=sha(BUNDLE),
        files=files, changing_paths=ALLOWED,
        working_save_files=[r for r in saves if r['path'] not in protected],
        compile_inputs=compile_proof['input_pins'],
        compile_coverage={'mode': 'COMPLETE_JB4_COMPILE', 'sources': 148, 'scripts_changed': 3,
                          'new_compile_run': True, 'compiled_sha256': compile_proof['compiled_sha256']},
        proofs=[{'path': str(p), 'sha256': sha(p)} for p in [*proofs, package_manifest, INSTALLED, save_path]],
        scope='Cumulative Johnny removal through Batch 6 and the three reviewed profile setup fixes.',
        rollback_policy='Restore the exact JB3 archive and the three scripts from this transaction recovery.',
    )
    write(manifest_path, transaction)
    source = old_installer.read_text(encoding='utf-8-sig')
    edits = {
        '# JB3 deployment. User approved installation of the cumulative Johnny removal build.':
            '# JB4 deployment. User approved the combined dialogue and setup update.',
        '# Derived from JB1. The consolidated archive and the two listed scripts may change.':
            '# The consolidated archive and the three reviewed setup scripts may change.',
        '# The three-file replacement is journaled, with per-file atomic replacement; Windows':
            '# The four-file replacement is journaled, with per-file atomic replacement. Windows',
        "$PinnedCoreManifestSHA='" + sha(old_tx) + "'": "$PinnedCoreManifestSHA='" + sha(manifest_path) + "'",
        'PTFR_JB3_JOURNAL_V1': 'PTFR_JB4_JOURNAL_V1',
        'PTFR_JB3_CORE_V1': 'PTFR_JB4_CORE_V1',
        "$manifest.source_epoch -cne 'JB3'": "$manifest.source_epoch -cne 'JB4'",
        "$manifest.predecessor_epoch -cne 'JB1'": "$manifest.predecessor_epoch -cne 'JB3'",
        'recovery/core_jb3_01': 'recovery/core_jb4_01',
        "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS25.reds')":
            "$wanted=@(" + ','.join("'" + p + "'" for p in ALLOWED) + ")",
        '$changes.Count -ne 3': '$changes.Count -ne 4',
        'Core51/three-existing-file scope drift': 'Core51/four-existing-file scope drift',
    }
    for old, new in edits.items():
        assert source.count(old) == (2 if old == 'PTFR_JB3_JOURNAL_V1' else 1), old
        source = source.replace(old, new)
    write_new(installer, source)
    write(HERE / 'installer_review.json', {
        'status': 'PASS_JB4_FOUR_FILE_TRANSACTION_LITERAL_DELTA',
        'predecessor_installer_sha256': sha(old_installer),
        'installer_sha256': sha(installer), 'manifest_sha256': sha(manifest_path),
        'allowed_replacements': ALLOWED, 'substitutions': edits,
    })
    tests = (JB3 / 'test_deployment.py').read_text(encoding='utf-8-sig')
    tests = tests.replace('JB3', 'JB4').replace('three-file', 'four-file').replace('THREE_FILE', 'FOUR_FILE')
    write_new(HERE / 'test_deployment.py', tests)
    print(f'Prepared the exact four-file transaction with {len(saves)} save-file pins.')


if __name__ == '__main__':
    main()
