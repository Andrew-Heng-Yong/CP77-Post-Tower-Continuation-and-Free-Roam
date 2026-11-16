"""Seal the merged candidate and prepare its scoped upgrade from ML1."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from prepare import ARCHIVE, BASE, BASELINE, HERE, INSTALLED, JB4, LIPMAP, OUT, PRE, XL, baseline, checked, inventory, read, sha, write
from finalize_provider_plan import ORIGINAL, PACK_PLAN
from verify_changes import COMPILE, VERIFY

TRANSACTION = 'core_manifest_01.json'
SOURCE_PACKAGE = BASE / 'package'
ALLOWED = [ARCHIVE, XL, *(r['path'] for r in read(BASELINE)['scripts'])]
PROOF = HERE / 'archive_readback.json'
BUNDLE = HERE / 'QP2_Core51_01.zip'


def write_new(path, source):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)


def seal(installed, base, compiled):
    manifest = OUT / 'package_manifest.json'
    assert not manifest.exists() and not BUNDLE.exists()
    plan, verification, archive = map(read, (PACK_PLAN, VERIFY, PROOF))
    assert plan['original_pack_plan_sha256'] == sha(ORIGINAL) and plan['members'] == read(ORIGINAL)['members']
    assert plan['verification_sha256'] == sha(VERIFY)
    assert verification['status'] == 'PASS_QP2_MERGED_RESOURCES_AND_SCRIPTS'
    assert verification['compile_sha256'] == sha(COMPILE) and verification['baseline_sha256'] == sha(BASELINE)
    assert archive['status'] == 'PASS_QP2_ARCHIVE_AND_PROVIDERS' and archive['plan_sha256'] == sha(PACK_PLAN)
    assert archive['provider_depots'] == len(plan['providers'])
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert members == plan['members'] == inventory(OUT / 'archive_source', '\\')
    assert len(members) == len(archive['resources']) == len({r['key'] for r in archive['resources']}) == 1729
    before = base['source_resources']
    expected = read(BASELINE)
    additions = sorted(members.keys() - before.keys())
    replacements = sorted(d for d in before if members[d] != before[d])
    assert additions == expected['new_depots'] and len(additions) == 6
    assert set(replacements) == (set(expected['copied_resources']) | {expected['entry']['depot']}) & before.keys()
    assert len(replacements) == 3 and members[LIPMAP] == before[LIPMAP]

    pkg = OUT / 'package'
    actual = inventory(pkg)
    previous = {r['path']: r['sha256'] for r in installed['core_files']}
    assert actual.keys() == previous.keys() and len(actual) == 51
    assert actual[ARCHIVE] == archive['archive_sha256']
    assert actual[XL] == verification['registration']['xl_sha256']
    assert sorted(p for p in actual if actual[p] != previous[p]) == ALLOWED and len(ALLOWED) == 8
    game = Path(installed['game_root'])
    for p, h in compiled['input_pins'].items():
        checked(p, h)
    for p, row in compiled['sources'].items():
        rel = Path(p).relative_to(game).as_posix()
        assert actual.get(rel, compiled['input_pins'][p]) == row['sha256']
        checked(row['staged'], row['sha256'])
    files = [{'path': p, 'sha256': h, 'bytes': (pkg / p).stat().st_size} for p, h in sorted(actual.items())]
    with ZipFile(BUNDLE, 'x', ZIP_DEFLATED) as z:
        for row in files:
            z.write(pkg / row['path'], row['path'])
    with ZipFile(BUNDLE) as z:
        assert len(z.namelist()) == len(actual) and set(z.namelist()) == actual.keys()
        assert all(z.read(p) == (pkg / p).read_bytes() for p in actual)
    write(manifest, {
        'status': 'STAGED_QP2_READBACK_VERIFIED', 'epoch': 'QP2', 'predecessor': 'ML1',
        'installed_predecessor_sha256': sha(INSTALLED), 'files': files,
        'source_resources': members, 'archive_sha256': actual[ARCHIVE], 'archive_payloads': len(members),
        'new_depots': additions, 'changed_depots': replacements, 'changed_paths': ALLOWED,
        'new_ArchiveXL_phase_id': verification['registration']['generated_node_id'],
        'proofs': {str(p.relative_to(HERE)): sha(p) for p in (VERIFY, PROOF, PACK_PLAN, COMPILE, BASELINE)},
        'zip_sha256': sha(BUNDLE), 'zip': str(BUNDLE), 'gameplay_validation': 'PENDING',
    })
    print(f'Sealed the 51-path package with {len(members)} verified archive payloads.')
    return manifest, files


def transaction(installed, compiled, manifest, files):
    before = {r['path']: r for r in installed['core_files']}
    rows = [{'path': r['path'], 'before': before[r['path']]['sha256'], 'before_bytes': before[r['path']]['bytes'],
             'after': r['sha256'], 'after_bytes': r['bytes']} for r in files]
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    old_tx = checked(installed['core_transaction'], installed['core_transaction_sha256'])
    old_worker = old_tx.parent
    tx = read(old_tx)
    assert tx['source_epoch'] == 'ML1' and tx['required_files'] == installed['required_files']
    for r in tx['protected_saves']:
        p = checked(Path(tx['save_root']) / r['path'], r['sha256'])
        assert p.stat().st_size == r['bytes']
    tx.update(
        schema='PTFR_QP2_CORE_V1', source_epoch='QP2', predecessor_epoch='ML1',
        package_root=str(OUT / 'package'), zip=str(BUNDLE), zip_sha256=sha(BUNDLE),
        files=rows, changing_paths=ALLOWED, working_save_files=[],
        compile_inputs=compiled['input_pins'],
        compile_coverage={'mode': 'COMPLETE_QP2_COMPILE', 'sources': 148, 'scripts_changed': 6,
                          'new_compile_run': True, 'compiled_sha256': compiled['compiled_sha256']},
        proofs=[{'path': str(p), 'sha256': sha(p)} for p in (manifest, INSTALLED, VERIFY, PROOF, PACK_PLAN, COMPILE, BASELINE)],
        scope='Apply the reviewed Small Man, Heavy Hearts, Bartmoss, Judy travel and Tower rooftop fixes over ML1.',
        rollback_policy='Restore the eight exact ML1 files from this transaction recovery.',
    )
    destination = HERE / TRANSACTION
    write(destination, tx)
    source = checked(old_worker / 'deploy_core.ps1', 'FCFB273272B4675CB2538E45E96417A520A9C99D196E5023A652A4280FC1FAB0')
    body = source.read_text(encoding='utf-8-sig')
    changes = {
        '# ML1 deployment over JB4. The requested monk fix changes one lip map.':
            '# QP2 deployment over ML1. The user authorized the combined repair install.',
        '# Only the combined archive is in the write set.':
            '# The archive, ArchiveXL configuration and six scripts are in the write set.',
        '# The archive replacement is atomic and journaled. An interrupted journal needs Recover.':
            '# The replacement set is journaled with per-file atomic replacement. An interrupted journal needs Recover.',
        "$PinnedCoreManifestSHA='" + sha(old_tx) + "'": "$PinnedCoreManifestSHA='" + sha(destination) + "'",
        'PTFR_ML1_JB4_CORE_V1': 'PTFR_QP2_CORE_V1',
        'PTFR_ML1_JB4_JOURNAL_V1': 'PTFR_QP2_JOURNAL_V1',
        "$manifest.source_epoch -cne 'ML1' -or $manifest.predecessor_epoch -cne 'JB4'":
            "$manifest.source_epoch -cne 'QP2' -or $manifest.predecessor_epoch -cne 'ML1'",
        'recovery/core_ml1_jb4_02': 'recovery/core_qp2_01',
        "$wanted=@('" + ARCHIVE + "')": "$wanted=@(" + ','.join("'" + p + "'" for p in ALLOWED) + ")",
        '$changes.Count -ne 1': '$changes.Count -ne 8',
        'Core51/one-archive scope drift': 'Core51/eight-existing-file scope drift',
    }
    for old, new in changes.items():
        assert body.count(old) == (2 if old == 'PTFR_ML1_JB4_JOURNAL_V1' else 1), old
        body = body.replace(old, new)
    installer = HERE / 'deploy_core.ps1'
    write_new(installer, body)
    write(HERE / 'installer_review.json', {
        'status': 'PASS_QP2_EIGHT_FILE_TRANSACTION_LITERAL_DELTA',
        'predecessor_installer_sha256': sha(source), 'installer_sha256': sha(installer),
        'manifest_sha256': sha(destination), 'substitutions': changes, 'allowed_replacements': ALLOWED,
    })
    template = checked(JB4 / 'test_deployment.py', '3BD9B67A4877F24B50AEB14AF94DC470DE17F62D5D8669F01EFC8590022985C5')
    tests = template.read_text(encoding='utf-8-sig').replace('JB4', 'QP2').replace('four-file', 'eight-file').replace('FOUR_FILE', 'EIGHT_FILE')
    write_new(HERE / 'test_deployment.py', tests)
    print('Prepared the guarded eight-file upgrade from ML1.')


def main():
    assert not (HERE / TRANSACTION).exists() and not (HERE / 'deploy_core.ps1').exists()
    installed, base = baseline()
    compiled = read(COMPILE)
    assert compiled['status'] == 'PASS_QP2_COMPLETE_SOURCE_COMPILE' and compiled['exit_code'] == 0
    assert len(compiled['sources']) == compiled['source_count'] == 148 and len(compiled['input_pins']) == 151
    manifest, files = seal(installed, base, compiled)
    transaction(installed, compiled, manifest, files)


if __name__ == '__main__':
    main()
