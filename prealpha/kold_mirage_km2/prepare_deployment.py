"""Seal the verified KM2 Core51 package and exact one-archive PE1 transaction."""
from pathlib import Path
import copy
import hashlib
import zipfile
from prepare import HERE, BASE, OUT, PREDECESSOR, ARCHIVE, read, sha, write

SOURCE_PACKAGE = BASE/'package'
TRANSACTION = 'core_manifest_01.json'
ALLOWED = [ARCHIVE]


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
    compilation = read(HERE/'compile_inventory.json')
    assert verification['status'] == 'PASS_KM2_COOKED_ACTOR_SUPPRESSION_FLOW_AND_COMPLETE_DELTA'
    assert verification['plan_sha256'] == sha(HERE/'input_02/plan.json')
    assert archive['status'] == 'PASS_ALL_KM2_ARCHIVE_MEMBERS'
    assert compilation['status'] == 'PASS_UNCHANGED_CURRENT_SOURCES_MATCH_PE1_COMPLETE_COMPILE'
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert len(members) == len({r['key'] for r in archive['resources']}) == 1581
    assert set(members) == set(baseline['source_resources'])
    changed = sorted(d for d,h in members.items() if h != baseline['source_resources'][d])
    assert changed == sorted(e['depot'] for e in plan['edits'])
    for depot, digest in members.items():
        checked(OUT/'archive_source'/depot, digest)
    game = Path(installed['game_root'])
    files = {p.relative_to(OUT/'package').as_posix(): p for p in (OUT/'package').rglob('*') if p.is_file()}
    old_files = {r['path']: r for r in installed['core_files']}
    assert set(files) == set(old_files) and len(files) == 51
    rows = []
    for rel, old in sorted(old_files.items()):
        checked(game/rel, old['sha256'])
        p = files[rel]
        rows.append({'path': rel, 'before': old['sha256'], 'before_bytes': old['bytes'], 'after': sha(p), 'after_bytes': p.stat().st_size})
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    assert next(r['after'] for r in rows if r['path'] == ARCHIVE) == archive['archive_sha256']
    for row in installed['required_files']:
        checked(game/row['path'], row['sha256'])
    write(OUT/'package_manifest.json', {'status': 'STAGED_KM2_READBACK_VERIFIED', 'epoch': 'KM2', 'predecessor': 'PE1', 'files': [{'path':r['path'], 'sha256':r['after'], 'bytes':r['after_bytes']} for r in rows], 'source_resources': members, 'changed_paths': ALLOWED, 'changed_depots': changed, 'archive_payloads': 1581, 'retained_archive_members': 1578, 'installed': False, 'gameplay_validation': 'PENDING_USER_PRE_OPEN_TEST'})
    zip_path = HERE/'KM2_Core51_01.zip'
    assert not zip_path.exists()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for rel, p in sorted(files.items()):
            z.write(p, rel)
    with zipfile.ZipFile(zip_path) as z:
        assert set(z.namelist()) == set(files) and z.testzip() is None
        for row in rows:
            assert hashlib.sha256(z.read(row['path'])).hexdigest().upper() == row['after']
    old = read(PREDECESSOR/TRANSACTION)
    for row in old['protected_saves'] + old['working_save_files']:
        checked(Path(old['save_root'])/row['path'], row['sha256'])
    assert all(sha(path) == digest for path,digest in compilation['input_pins'].items())
    proofs = [HERE/'input_02/plan.json', HERE/'source_01/manifest.json', HERE/'readback_01/manifest.json', HERE/'verification.json', HERE/'compile_inventory.json', HERE/'archive_readback.json', OUT/'package_manifest.json']
    transaction = copy.deepcopy(old)
    transaction.update(schema='PTFR_KM2_CORE_V1', source_epoch='KM2', predecessor_epoch='PE1', package_root=str(OUT/'package'), zip=str(zip_path), zip_sha256=sha(zip_path), files=rows, changing_paths=ALLOWED, compile_inputs=compilation['input_pins'], compile_coverage={'mode':'UNCHANGED_CURRENT_REDS_MATCH_PE1_COMPILED_INPUTS', 'sources':148, 'input_pins':151, 'compiled_sha256':compilation['compiled_sha256'], 'new_compile_run':False, 'scripts_changed':0, 'timestamp_sidecar':compilation['timestamp_sidecar']}, proofs=[{'path':str(p), 'sha256':sha(p)} for p in proofs], scope='User-requested KOLD MIRAGE Johnny actor/effect/objective removal and native Open -> scan -> Take -> Nix flow; pre-first-opening transition only. Only the existing consolidated archive is replaced.', rollback_policy='Restore the exact PE1 archive from this transaction recovery. File rollback does not undo saved gameplay.')
    write(HERE/TRANSACTION, transaction)
    review = read(PREDECESSOR/'installer_review.json')
    source = checked(PREDECESSOR/'deploy_core.ps1', review['installer_sha256']).read_text(encoding='utf-8-sig')
    old_allowlist = '$wanted=@(' + ','.join("'"+p+"'" for p in old['changing_paths']) + ')'
    changes = {
        '# PE1 deployment. User requested the marker/encounter setup policy across restored content.': '# KM2 deployment. User requested the KOLD MIRAGE actor-free interaction sequence.',
        '# Derived from the reviewed KM1 transaction. Only the consolidated archive and six listed scripts may change.': '# Derived from the reviewed PE1 transaction. Only the consolidated archive may change.',
        '# The seven-file replacement is journaled, with per-file atomic replacement; Windows': '# The one-archive replacement is journaled, with per-file atomic replacement; Windows',
        "$PinnedCoreManifestSHA='"+sha(PREDECESSOR/TRANSACTION)+"'": "$PinnedCoreManifestSHA='"+sha(HERE/TRANSACTION)+"'",
        'PTFR_PE1_JOURNAL_V1': 'PTFR_KM2_JOURNAL_V1',
        "'PTFR_PE1_CORE_V1'": "'PTFR_KM2_CORE_V1'",
        "$manifest.source_epoch -cne 'PE1' -or $manifest.predecessor_epoch -cne 'KM1'": "$manifest.source_epoch -cne 'KM2' -or $manifest.predecessor_epoch -cne 'PE1'",
        "('recovery/core_pe1_01')": "('recovery/core_km2_01')",
        old_allowlist: "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')",
        '$changes.Count -ne 7': '$changes.Count -ne 1',
        "'Core51/seven-existing-file scope drift'": "'Core51/one-existing-archive scope drift'",
    }
    for before, after in changes.items():
        assert source.count(before) == (2 if before == 'PTFR_PE1_JOURNAL_V1' else 1), before
        source = source.replace(before, after)
    (HERE/'deploy_core.ps1').write_text(source, encoding='utf-8')
    write(HERE/'installer_review.json', {'status':'PASS_KM2_ONE_ARCHIVE_TRANSACTION_LITERAL_DELTA', 'predecessor_installer_sha256':review['installer_sha256'], 'installer_sha256':sha(HERE/'deploy_core.ps1'), 'manifest_sha256':sha(HERE/TRANSACTION), 'allowed_replacements':ALLOWED, 'reviewed_literal_changes':changes, 'transaction_functions':'Inherited unchanged apart from exact one-archive allowlist and epoch/pin/recovery namespace.', 'package_member_count':51, 'archive_member_count':1581, 'unchanged_payloads':1578})
    fixture = (PREDECESSOR/'test_deployment.py').read_text(encoding='utf-8-sig')
    for before,after in [('PE1 seven-file', 'KM2 one-archive'), ('PASS_PE1_SEVEN_FILE_DEPLOYMENT_FIXTURES', 'PASS_KM2_ONE_ARCHIVE_DEPLOYMENT_FIXTURES'), ('"AfterFirstReplace", "AfterSecondReplace", "BeforeReceipt", "CrashAfterFirstReplace", "CrashAfterSecondReplace", "CrashBeforeReceipt"', '"AfterFirstReplace", "BeforeReceipt", "CrashAfterFirstReplace", "CrashBeforeReceipt"'), ('ten isolated fixtures','eight isolated fixtures')]:
        assert fixture.count(before) == 1, before
        fixture = fixture.replace(before, after)
    with (HERE/'test_deployment.py').open('x', encoding='utf-8', newline='\n') as f:
        f.write(fixture)
    print('Sealed KM2 Core51, full ZIP readback and exact one-archive transaction. Not installed.')


if __name__ == '__main__':
    main()
