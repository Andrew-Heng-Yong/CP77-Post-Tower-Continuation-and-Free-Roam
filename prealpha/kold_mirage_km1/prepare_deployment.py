"""Seal KM1 Core51 and derive its exact two-file JP1 successor transaction."""
from pathlib import Path
import copy
import hashlib
import zipfile
from prepare import HERE, WS, JP1, BASE, OUT, ENTRY, SCRIPT, ARCHIVE, read, sha, write

ALLOWED=[ARCHIVE,SCRIPT]
SOURCE_PACKAGE=BASE/'package'
TRANSACTION='core_manifest_01.json'


def checked(path,digest):
    path=Path(path);assert sha(path)==digest,path
    return path


def main():
    assert not (HERE/TRANSACTION).exists() and not (HERE/'deploy_core.ps1').exists()
    plan=read(HERE/'input_01/plan.json')
    installed=read(checked(plan['installed_baseline'],plan['installed_baseline_sha256']))
    baseline=read(checked(plan['baseline_package'],plan['baseline_package_sha256']))
    verification=read(HERE/'verification.json')
    archive=read(HERE/'archive_readback.json')
    compilation=read(HERE/'compile_01/result.json')
    assert verification['status']=='PASS_KM1_TYPED_GUARDS_AND_COMPLETE_DELTA'
    assert archive['status']=='PASS_ALL_KM1_ARCHIVE_MEMBERS'
    assert compilation['status']=='PASS_CURRENT_REGISTERED_SOURCE_COMPILE'
    members={r['depot']:r['sha256'] for r in archive['resources']}
    assert len(members)==len({r['key'] for r in archive['resources']})==1581
    assert set(members)==set(baseline['source_resources'])
    assert [d for d,h in members.items() if h!=baseline['source_resources'][d]]==[ENTRY]
    game=Path(installed['game_root'])
    files={p.relative_to(OUT/'package').as_posix():p for p in (OUT/'package').rglob('*') if p.is_file()}
    originals={r['path']:r for r in installed['core_files']}
    assert set(files)==set(originals) and len(files)==51
    rows=[]
    for rel,old in sorted(originals.items()):
        checked(game/rel,old['sha256'])
        p=files[rel]
        rows.append({'path':rel,'before':old['sha256'],'before_bytes':old['bytes'],'after':sha(p),'after_bytes':p.stat().st_size})
    assert [r['path'] for r in rows if r['before']!=r['after']]==ALLOWED
    assert next(r['after'] for r in rows if r['path']==ARCHIVE)==archive['archive_sha256']
    for r in installed['required_files']:
        checked(game/r['path'],r['sha256'])
    manifest={'status':'STAGED_KM1_READBACK_VERIFIED','epoch':'KM1','predecessor':'JP1','files':[{'path':r['path'],'sha256':r['after'],'bytes':r['after_bytes']} for r in rows],'source_resources':members,'changed_paths':ALLOWED,'changed_depots':[ENTRY],'retained_archive_members':1580,'archive_payloads':1581,'installed':False,'gameplay_validation':'PENDING_USER_TEST'}
    write(OUT/'package_manifest.json',manifest)
    zip_path=HERE/'KM1_Core51_01.zip';assert not zip_path.exists()
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for rel,p in sorted(files.items()):z.write(p,rel)
    with zipfile.ZipFile(zip_path) as z:
        assert set(z.namelist())==set(files) and z.testzip() is None
        for r in rows:assert hashlib.sha256(z.read(r['path'])).hexdigest().upper()==r['after']
    old=read(JP1/TRANSACTION)
    # Preserve master/working save pins. Any legitimate new working-slot change
    # needs separate reconciliation rather than silently replacing a receipt.
    for r in old['protected_saves']+old['working_save_files']:
        checked(Path(old['save_root'])/r['path'],r['sha256'])
    compile_inputs=compilation['input_pins']
    assert all(sha(p)==s for p,s in compile_inputs.items())
    proofs=[HERE/'input_01/plan.json',HERE/'analysis_01.json',HERE/'source_01/providers.json',HERE/'readback_01/manifest.json',HERE/'verification.json',HERE/'archive_readback.json',HERE/'compile_01/result.json',OUT/'package_manifest.json']
    transaction=copy.deepcopy(old)
    transaction.update(schema='PTFR_KM1_CORE_V1',source_epoch='KM1',predecessor_epoch='JP1',package_root=str(OUT/'package'),zip=str(zip_path),zip_sha256=sha(zip_path),files=rows,changing_paths=ALLOWED,compile_inputs=compile_inputs,compile_coverage={'mode':'FRESH_COMPLETE_REGISTERED_SOURCE_COMPILE','sources':compilation['source_count'],'input_pins':len(compile_inputs),'compiled_sha256':compilation['compiled_sha256']},proofs=[{'path':str(p),'sha256':sha(p)} for p in proofs],scope='User-requested KOLD MIRAGE undiscovered marker and encounter repair: allow mq016_active=0 or 1 while preserving all other gates and the installed JP1 dialogue removals.',rollback_policy='Restore the exact JP1 archive and S29 script from this transaction recovery. File rollback does not undo saves.')
    write(HERE/TRANSACTION,transaction)
    source_path=JP1/'deploy_core.ps1'
    old_review=read(JP1/'installer_review.json')
    source=checked(source_path,old_review['installer_sha256']).read_text(encoding='utf-8-sig')
    changes={
      '# JP1 deployment. User requested implementation for their in-game pilot test. Fixtures stay under this task.':'# KM1 deployment. User requested the KOLD MIRAGE marker/encounter fix and active=0-or-1 admission.',
      '# Derived from the reviewed HH1 transaction. Only the consolidated archive may change.':'# Derived from the reviewed JP1 transaction. Only the consolidated archive and S29 script may change.',
      "$PinnedCoreManifestSHA='"+sha(JP1/TRANSACTION)+"'":"$PinnedCoreManifestSHA='"+sha(HERE/TRANSACTION)+"'",
      'PTFR_JP1_JOURNAL_V1':'PTFR_KM1_JOURNAL_V1',
      "'PTFR_JP1_CORE_V1'":"'PTFR_KM1_CORE_V1'",
      "$manifest.source_epoch -cne 'JP1' -or $manifest.predecessor_epoch -cne 'HH1'":"$manifest.source_epoch -cne 'KM1' -or $manifest.predecessor_epoch -cne 'JP1'",
      "('recovery/core_jp1_01')":"('recovery/core_km1_01')",
      "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')":"$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')",
      '$changes.Count -ne 1':'$changes.Count -ne 2',
      "'Core51/one-existing-archive scope drift'":"'Core51/two-existing-file scope drift'"
    }
    for old_text,new_text in changes.items():
        assert source.count(old_text)==(2 if old_text=='PTFR_JP1_JOURNAL_V1' else 1),old_text
        source=source.replace(old_text,new_text)
    (HERE/'deploy_core.ps1').write_text(source,encoding='utf-8')
    write(HERE/'installer_review.json',{'status':'PASS_KM1_TWO_FILE_TRANSACTION_LITERAL_DELTA','predecessor_installer_sha256':old_review['installer_sha256'],'installer_sha256':sha(HERE/'deploy_core.ps1'),'manifest_sha256':sha(HERE/TRANSACTION),'allowed_replacements':ALLOWED,'reviewed_literal_changes':changes,'transaction_functions':'Inherited unchanged apart from the exact two-file allowlist and epoch/pin/recovery namespace.','package_member_count':51,'archive_member_count':1581,'unchanged_payloads':1580})
    print('Sealed KM1 Core51, ZIP readback and exact two-file transaction. Not installed.')


if __name__=='__main__':
    main()
