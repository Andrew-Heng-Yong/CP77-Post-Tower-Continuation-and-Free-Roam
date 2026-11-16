"""Seal SD1 Core51 and derive the guarded one-archive KM2 -> SD1 transaction."""
from pathlib import Path
import copy
import hashlib
import zipfile
from prepare import HERE, BASE, OUT, KM2, ARCHIVE, read, sha, write

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
    verification, archive, compilation = [read(HERE/name) for name in ['verification.json','archive_readback.json','compile_inventory.json']]
    assert verification['status'] == 'PASS_SD1_COOKED_PRESENTATION_AND_COMPLETION_CONTRACTS'
    assert verification['plan_sha256'] == sha(HERE/'input_02/plan.json')
    assert archive['status'] == 'PASS_ALL_SD1_ARCHIVE_MEMBERS'
    assert compilation['status'] == 'PASS_UNCHANGED_CURRENT_SOURCES_MATCH_PE1_COMPLETE_COMPILE'
    members = {r['depot']:r['sha256'] for r in archive['resources']}
    assert len(members) == len({r['key'] for r in archive['resources']}) == 1581
    assert set(members) == set(baseline['source_resources'])
    changed = sorted(d for d,h in members.items() if h != baseline['source_resources'][d])
    assert changed == sorted(e['depot'] for e in plan['edits']) and len(changed) == 2
    for depot,digest in members.items():
        checked(OUT/'archive_source'/depot,digest)
    game = Path(installed['game_root'])
    files = {p.relative_to(OUT/'package').as_posix():p for p in (OUT/'package').rglob('*') if p.is_file()}
    old_files = {r['path']:r for r in installed['core_files']}
    assert set(files) == set(old_files) and len(files) == 51
    rows = []
    for rel,old in sorted(old_files.items()):
        checked(game/rel,old['sha256'])
        p=files[rel]
        rows.append({'path':rel,'before':old['sha256'],'before_bytes':old['bytes'],'after':sha(p),'after_bytes':p.stat().st_size})
    assert [r['path'] for r in rows if r['before'] != r['after']] == ALLOWED
    assert next(r['after'] for r in rows if r['path'] == ARCHIVE) == archive['archive_sha256']
    for row in installed['required_files']:
        checked(game/row['path'],row['sha256'])
    write(OUT/'package_manifest.json', {'status':'STAGED_SD1_READBACK_VERIFIED','epoch':'SD1','predecessor':'KM2',
          'files':[{'path':r['path'],'sha256':r['after'],'bytes':r['after_bytes']} for r in rows],
          'source_resources':members,'changed_paths':ALLOWED,'changed_depots':changed,'archive_payloads':1581,
          'retained_archive_members':1579,'installed':False,'gameplay_validation':'PENDING_SUPPORTED_UNSTARTED_FIXTURE'})
    zip_path=HERE/'SD1_Core51_01.zip'
    assert not zip_path.exists()
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for rel,p in sorted(files.items()):
            z.write(p,rel)
    with zipfile.ZipFile(zip_path) as z:
        assert set(z.namelist()) == set(files) and z.testzip() is None
        for row in rows:
            assert hashlib.sha256(z.read(row['path'])).hexdigest().upper() == row['after']
    old=read(KM2/TRANSACTION)
    for row in old['protected_saves']+old['working_save_files']:
        checked(Path(old['save_root'])/row['path'],row['sha256'])
    assert all(sha(p) == h for p,h in compilation['input_pins'].items())
    proofs=[HERE/'input_02/plan.json',HERE/'source_01/manifest.json',HERE/'readback_01/manifest.json',HERE/'verification.json',
            HERE/'compile_inventory.json',HERE/'archive_readback.json',OUT/'package_manifest.json']
    transaction=copy.deepcopy(old)
    transaction.update(schema='PTFR_SD1_CORE_V1',source_epoch='SD1',predecessor_epoch='KM2',package_root=str(OUT/'package'),
        zip=str(zip_path),zip_sha256=sha(zip_path),files=rows,changing_paths=ALLOWED,compile_inputs=compilation['input_pins'],
        compile_coverage={'mode':'UNCHANGED_CURRENT_REDS_MATCH_PE1_COMPILED_INPUTS','sources':148,'input_pins':151,
                         'compiled_sha256':compilation['compiled_sha256'],'new_compile_run':False,'scripts_changed':0,'timestamp_sidecar':compilation['timestamp_sidecar']},
        proofs=[{'path':str(p),'sha256':sha(p)} for p in proofs],
        scope='Authorized Sweet Dreams Johnny actor/presentation cleanup only. Preserve gameplay sequence, timings, gear, journals and outcomes. Only existing consolidated archive is replaced. No completed-quest reset or saved-owner migration.',
        rollback_policy='Restore exact KM2 archive from this transaction recovery. File rollback does not undo gameplay saves.')
    write(HERE/TRANSACTION,transaction)
    review=read(KM2/'installer_review.json')
    source=checked(KM2/'deploy_core.ps1',review['installer_sha256']).read_text(encoding='utf-8-sig')
    changes={
        '# KM2 deployment. User requested the KOLD MIRAGE actor-free interaction sequence.':'# SD1 deployment. User requested Sweet Dreams Johnny presentation cleanup.',
        '# Derived from the reviewed PE1 transaction. Only the consolidated archive may change.':'# Derived from the reviewed KM2 transaction. Only the consolidated archive may change.',
        "$PinnedCoreManifestSHA='"+sha(KM2/TRANSACTION)+"'":"$PinnedCoreManifestSHA='"+sha(HERE/TRANSACTION)+"'",
        'PTFR_KM2_JOURNAL_V1':'PTFR_SD1_JOURNAL_V1',
        "'PTFR_KM2_CORE_V1'":"'PTFR_SD1_CORE_V1'",
        "$manifest.source_epoch -cne 'KM2' -or $manifest.predecessor_epoch -cne 'PE1'":"$manifest.source_epoch -cne 'SD1' -or $manifest.predecessor_epoch -cne 'KM2'",
        "('recovery/core_km2_01')":"('recovery/core_sd1_01')",
    }
    for before,after in changes.items():
        assert source.count(before) == (2 if before == 'PTFR_KM2_JOURNAL_V1' else 1),before
        source=source.replace(before,after)
    with (HERE/'deploy_core.ps1').open('x',encoding='utf-8',newline='\n') as f:
        f.write(source)
    write(HERE/'installer_review.json', {'status':'PASS_SD1_ONE_ARCHIVE_TRANSACTION_LITERAL_DELTA',
          'predecessor_installer_sha256':review['installer_sha256'],'installer_sha256':sha(HERE/'deploy_core.ps1'),
          'manifest_sha256':sha(HERE/TRANSACTION),'allowed_replacements':ALLOWED,'reviewed_literal_changes':changes,
          'transaction_functions':'Inherited unchanged; only epoch, pin, recovery namespace and scope comments differ.',
          'package_member_count':51,'archive_member_count':1581,'unchanged_payloads':1579})
    fixture=(KM2/'test_deployment.py').read_text(encoding='utf-8-sig')
    for before,after in [('KM2 one-archive','SD1 one-archive'),('PASS_KM2_ONE_ARCHIVE_DEPLOYMENT_FIXTURES','PASS_SD1_ONE_ARCHIVE_DEPLOYMENT_FIXTURES')]:
        assert fixture.count(before) == 1,before
        fixture=fixture.replace(before,after)
    with (HERE/'test_deployment.py').open('x',encoding='utf-8',newline='\n') as f:
        f.write(fixture)
    print('Sealed SD1 Core51, full ZIP readback and exact one-archive transaction. Not installed.')


if __name__ == '__main__':
    main()
