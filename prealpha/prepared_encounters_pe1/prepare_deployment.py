"""Seal PE1 Core51 and derive a guarded seven-file successor to installed KM1."""
from pathlib import Path
import copy
import hashlib
import zipfile
from prepare import HERE, WS, BASE, OUT, ARCHIVE, read, sha, write

PREDECESSOR = BASE.parent
SOURCE_PACKAGE = BASE/'package'
TRANSACTION = 'core_manifest_01.json'
ALLOWED = [ARCHIVE] + sorted(r['path'] for r in read(HERE/'input_02/plan.json')['scripts'])


def checked(path, digest):
    path = Path(path)
    assert sha(path) == digest, path
    return path


def main():
    assert not (HERE/TRANSACTION).exists() and not (HERE/'deploy_core.ps1').exists()
    plan = read(HERE/'input_02/plan.json')
    installed = read(checked(plan['installed_baseline'], plan['installed_baseline_sha256']))
    baseline = read(checked(plan['baseline_package'], plan['baseline_package_sha256']))
    verification = read(HERE/'verification.json')
    archive = read(HERE/'archive_readback.json')
    compilation = read(HERE/'compile_01/result.json')
    assert verification['status'] == 'PASS_PE1_COOKED_GUARDS_AND_COMPLETE_DELTA'
    assert verification['plan_sha256'] == sha(HERE/'input_02/plan.json')
    assert archive['status'] == 'PASS_ALL_PE1_ARCHIVE_MEMBERS'
    assert compilation['status'] == 'PASS_CURRENT_REGISTERED_SOURCE_COMPILE'
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert len(members) == len({r['key'] for r in archive['resources']}) == 1581
    assert set(members) == set(baseline['source_resources'])
    changed_depots = sorted(d for d, h in members.items() if h != baseline['source_resources'][d])
    assert changed_depots == sorted(r['depot'] for r in plan['resources'])
    for depot, digest in members.items():
        checked(OUT/'archive_source'/depot, digest)
    game = Path(installed['game_root'])
    files = {p.relative_to(OUT/'package').as_posix(): p for p in (OUT/'package').rglob('*') if p.is_file()}
    originals = {r['path']: r for r in installed['core_files']}
    assert set(files) == set(originals) and len(files) == 51
    rows = []
    for rel, old in sorted(originals.items()):
        checked(game/rel, old['sha256'])
        p = files[rel]
        rows.append({'path': rel, 'before': old['sha256'], 'before_bytes': old['bytes'], 'after': sha(p), 'after_bytes': p.stat().st_size})
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED and len(ALLOWED) == 7
    assert next(r['after'] for r in rows if r['path'] == ARCHIVE) == archive['archive_sha256']
    for r in installed['required_files']:
        checked(game/r['path'], r['sha256'])
    manifest = {'status': 'STAGED_PE1_READBACK_VERIFIED', 'epoch': 'PE1', 'predecessor': 'KM1', 'files': [{'path': r['path'], 'sha256': r['after'], 'bytes': r['after_bytes']} for r in rows], 'source_resources': members, 'changed_paths': ALLOWED, 'changed_depots': changed_depots, 'retained_archive_members': 1569, 'archive_payloads': 1581, 'installed': False, 'gameplay_validation': 'PENDING_USER_TEST'}
    write(OUT/'package_manifest.json', manifest)
    zip_path = HERE/'PE1_Core51_01.zip'
    assert not zip_path.exists()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for rel, p in sorted(files.items()):
            z.write(p, rel)
    with zipfile.ZipFile(zip_path) as z:
        assert set(z.namelist()) == set(files) and z.testzip() is None
        for r in rows:
            assert hashlib.sha256(z.read(r['path'])).hexdigest().upper() == r['after']
    old = read(PREDECESSOR/TRANSACTION)
    for r in old['protected_saves'] + old['working_save_files']:
        checked(Path(old['save_root'])/r['path'], r['sha256'])
    compile_inputs = compilation['input_pins']
    assert all(sha(p) == digest for p, digest in compile_inputs.items())
    proofs = [HERE/'input_02/plan.json', HERE/'decisions_01.json', HERE/'providers_01/manifest.json', HERE/'readback_01/manifest.json', HERE/'verification.json', HERE/'archive_readback.json', HERE/'compile_01/result.json', OUT/'package_manifest.json']
    transaction = copy.deepcopy(old)
    transaction.update(schema='PTFR_PE1_CORE_V1', source_epoch='PE1', predecessor_epoch='KM1', package_root=str(OUT/'package'), zip=str(zip_path), zip_sha256=sha(zip_path), files=rows, changing_paths=ALLOWED, compile_inputs=compile_inputs, compile_coverage={'mode': 'FRESH_COMPLETE_REGISTERED_SOURCE_COMPILE', 'sources': compilation['source_count'], 'input_pins': len(compile_inputs), 'compiled_sha256': compilation['compiled_sha256']}, proofs=[{'path': str(p), 'sha256': sha(p)} for p in proofs], scope='Source-qualified Boolean setup admission across all restored entry families: 17 additional entries, 20 setup fields, 25 private guard nodes. Preserve existing counters/progress/ownership, KM1, JP1 dialogue cuts and all unrelated payloads.', rollback_policy='Restore the exact KM1 archive and six scripts from this transaction recovery. File rollback does not undo saves.')
    write(HERE/TRANSACTION, transaction)
    source_path = PREDECESSOR/'deploy_core.ps1'
    old_review = read(PREDECESSOR/'installer_review.json')
    source = checked(source_path, old_review['installer_sha256']).read_text(encoding='utf-8-sig')
    wanted = '$wanted=@(' + ','.join("'"+rel+"'" for rel in ALLOWED) + ')'
    changes = {
        '# KM1 deployment. User requested the KOLD MIRAGE marker/encounter fix and active=0-or-1 admission.': '# PE1 deployment. User requested the marker/encounter setup policy across restored content.',
        '# Derived from the reviewed JP1 transaction. Only the consolidated archive and S29 script may change.': '# Derived from the reviewed KM1 transaction. Only the consolidated archive and six listed scripts may change.',
        '# The two-file replacement is journaled, with per-file atomic replacement; Windows': '# The seven-file replacement is journaled, with per-file atomic replacement; Windows',
        "$PinnedCoreManifestSHA='"+sha(PREDECESSOR/TRANSACTION)+"'": "$PinnedCoreManifestSHA='"+sha(HERE/TRANSACTION)+"'",
        'PTFR_KM1_JOURNAL_V1': 'PTFR_PE1_JOURNAL_V1',
        "'PTFR_KM1_CORE_V1'": "'PTFR_PE1_CORE_V1'",
        "$manifest.source_epoch -cne 'KM1' -or $manifest.predecessor_epoch -cne 'JP1'": "$manifest.source_epoch -cne 'PE1' -or $manifest.predecessor_epoch -cne 'KM1'",
        "('recovery/core_km1_01')": "('recovery/core_pe1_01')",
        "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')": wanted,
        '$changes.Count -ne 2': '$changes.Count -ne 7',
        "'Core51/two-existing-file scope drift'": "'Core51/seven-existing-file scope drift'",
    }
    for before, after in changes.items():
        assert source.count(before) == (2 if before == 'PTFR_KM1_JOURNAL_V1' else 1), before
        source = source.replace(before, after)
    (HERE/'deploy_core.ps1').write_text(source, encoding='utf-8')
    write(HERE/'installer_review.json', {'status': 'PASS_PE1_SEVEN_FILE_TRANSACTION_LITERAL_DELTA', 'predecessor_installer_sha256': old_review['installer_sha256'], 'installer_sha256': sha(HERE/'deploy_core.ps1'), 'manifest_sha256': sha(HERE/TRANSACTION), 'allowed_replacements': ALLOWED, 'reviewed_literal_changes': changes, 'transaction_functions': 'Inherited unchanged apart from the exact seven-file allowlist and epoch/pin/recovery namespace.', 'package_member_count': 51, 'archive_member_count': 1581, 'unchanged_payloads': 1569})
    # Adapt only the fixture's scope labels. Its transaction and preservation
    # assertions exercise all seven allowlisted paths through the actual installer.
    fixture_source = (PREDECESSOR/'test_deployment.py').read_text(encoding='utf-8-sig')
    for before, after in [('KM1 two-file', 'PE1 seven-file'), ('PASS_KM1_TWO_FILE_DEPLOYMENT_FIXTURES', 'PASS_PE1_SEVEN_FILE_DEPLOYMENT_FIXTURES')]:
        assert fixture_source.count(before) == 1
        fixture_source = fixture_source.replace(before, after)
    with (HERE/'test_deployment.py').open('x', encoding='utf-8', newline='\n') as f:
        f.write(fixture_source)
    print('Sealed PE1 Core51, complete ZIP readback and seven-file transaction. Not installed.')


if __name__ == '__main__':
    main()
