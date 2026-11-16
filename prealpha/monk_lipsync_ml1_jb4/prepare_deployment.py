"""Prepare a guarded single-archive transaction from JB4."""

from pathlib import Path

from stage import ARCHIVE, BASE, BUNDLE, HERE, INSTALLED, JB4, OUT, PLAN, PROOF, baseline, checked, inventory, plain, read, sha, write

TRANSACTION = 'core_manifest_01.json'
SOURCE_PACKAGE = BASE / 'package'
ALLOWED = [ARCHIVE]


def compile_equivalence(game):
    result = checked(JB4 / 'compile_01/result.json',
                     'E0D04853D2E9F1ABAFC1BAC53DCA487B37A14183D1B15B91189D5CD74208F02B')
    proof = read(result)
    assert proof['status'] == 'PASS_JB4_COMPLETE_SOURCE_COMPILE'
    sources = {Path(p) for p in proof['sources']}
    assert len(sources) == 148
    assert sources == {p for root in ('r6/scripts', 'red4ext/plugins') for p in (game / root).rglob('*.reds')}
    pins = {}
    for path, row in proof['sources'].items():
        checked(path, row['sha256'])
        checked(row['staged'], row['sha256'])
        pins[path] = row['sha256']
    timestamps = []
    for path, digest in proof['input_pins'].items():
        if path in pins:
            continue
        if Path(path) == game / 'r6/cache/final.redscripts.ts':
            plain(Path(path))
            assert Path(path).stat().st_size == 16
            current = sha(path)
            timestamps.append({'path': path, 'compiled_input_sha256': digest, 'current_sha256': current, 'bytes': 16})
            pins[path] = current
        else:
            pins[path] = sha(checked(path, digest))
    assert len(pins) == 151 and len(timestamps) == 1
    return pins, {
        'mode': 'UNCHANGED_REDS_MATCH_COMPLETE_JB4_COMPILE', 'sources': 148, 'scripts_changed': 0,
        'new_compile_run': False, 'compile_result': str(result), 'compile_result_sha256': sha(result),
        'compiled_sha256': proof['compiled_sha256'], 'timestamp_sidecar': timestamps,
    }


def write_new(path, source):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)


def main():
    destination = HERE / TRANSACTION
    installer = HERE / 'deploy_core.ps1'
    assert not destination.exists() and not installer.exists()
    installed, _ = baseline()
    pkg_manifest = OUT / 'package_manifest.json'
    package = read(pkg_manifest)
    assert package['status'] == 'STAGED_ML1_JB4_READBACK_VERIFIED'
    assert package['before_installed_manifest_sha256'] == sha(INSTALLED)
    assert package['archive_readback_sha256'] == sha(PROOF)
    checked(BUNDLE, package['zip_sha256'])
    package_root = OUT / 'package'
    assert inventory(package_root) == {row['path']: row['sha256'] for row in package['files']}
    pins, coverage = compile_equivalence(Path(installed['game_root']))
    previous = checked(JB4 / TRANSACTION, installed['core_transaction_sha256'])
    tx = read(previous)
    assert tx['source_epoch'] == 'JB4' and tx['required_files'] == installed['required_files']
    for row in tx['protected_saves']:
        path = checked(Path(installed['save_root']) / row['path'], row['sha256'])
        assert path.stat().st_size == row['bytes']
    before = {row['path']: row for row in installed['core_files']}
    assert before.keys() == {row['path'] for row in package['files']}
    rows = [{'path': row['path'], 'before': before[row['path']]['sha256'],
             'before_bytes': before[row['path']]['bytes'], 'after': row['sha256'],
             'after_bytes': row['bytes']} for row in package['files']]
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    proofs = [INSTALLED, pkg_manifest, PLAN, PROOF, Path(coverage['compile_result'])]
    old_write_set = ','.join("'" + name + "'" for name in tx['changing_paths'])
    tx.update(
        schema='PTFR_ML1_JB4_CORE_V1', source_epoch='ML1', predecessor_epoch='JB4',
        package_root=str(package_root), zip=str(BUNDLE), zip_sha256=sha(BUNDLE),
        files=rows, changing_paths=ALLOWED, compile_inputs=pins, compile_coverage=coverage,
        working_save_files=[],
        proofs=[{'path': str(p), 'sha256': sha(p)} for p in proofs],
        scope='Apply the first monk’s two English lip-sync entries to the current JB4 archive.',
        rollback_policy='Restore the exact JB4 archive from this transaction recovery.',
    )
    write(destination, tx)

    source = checked(JB4 / 'deploy_core.ps1',
                     '8865BFF2E268DBD551D841E84F6A7D3EC195B84B1E9EE3C3762543B738D00A72')
    body = source.read_text(encoding='utf-8-sig')
    substitutions = {
        '# JB4 deployment. User approved the combined dialogue and setup update.':
            '# ML1 deployment over JB4. The requested monk fix changes one lip map.',
        '# The consolidated archive and the three reviewed setup scripts may change.':
            '# Only the combined archive is in the write set.',
        '# The four-file replacement is journaled, with per-file atomic replacement. Windows\n'
        '# does not provide a globally atomic set here. An interrupted journal needs Recover.':
            '# The archive replacement is atomic and journaled. An interrupted journal needs Recover.',
        "$PinnedCoreManifestSHA='" + sha(previous) + "'":
            "$PinnedCoreManifestSHA='" + sha(destination) + "'",
        'PTFR_JB4_CORE_V1': 'PTFR_ML1_JB4_CORE_V1',
        'PTFR_JB4_JOURNAL_V1': 'PTFR_ML1_JB4_JOURNAL_V1',
        "$manifest.source_epoch -cne 'JB4' -or $manifest.predecessor_epoch -cne 'JB3'":
            "$manifest.source_epoch -cne 'ML1' -or $manifest.predecessor_epoch -cne 'JB4'",
        'recovery/core_jb4_01': 'recovery/core_ml1_jb4_01',
        '$wanted=@(' + old_write_set + ')': "$wanted=@('" + ARCHIVE + "')",
        '$changes.Count -ne 4': '$changes.Count -ne 1',
        'Core51/four-existing-file scope drift': 'Core51/one-archive scope drift',
    }
    for old, new in substitutions.items():
        assert body.count(old) == (2 if old == 'PTFR_JB4_JOURNAL_V1' else 1), old
        body = body.replace(old, new)
    write_new(installer, body)
    write(HERE / 'installer_review.json', {
        'status': 'PASS_ML1_JB4_ONE_ARCHIVE_LITERAL_DELTA', 'predecessor_installer_sha256': sha(source),
        'installer_sha256': sha(installer), 'manifest_sha256': sha(destination), 'substitutions': substitutions,
    })
    template = checked(HERE.parent / 'sweet_dreams_sd1/test_deployment.py',
                       '3867C30FB41898D47903C9AB2CADCAA885E190D2FEB89916E550F8807D9EB97A')
    write_new(HERE / 'test_deployment.py', template.read_text(encoding='utf-8-sig').replace('SD1', 'ML1_JB4'))
    print('Prepared the one-archive transaction with the complete JB4 source inventory.')


if __name__ == '__main__':
    main()
