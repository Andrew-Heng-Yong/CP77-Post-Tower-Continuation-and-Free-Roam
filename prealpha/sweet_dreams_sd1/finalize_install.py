"""Record installed SD1 bytes/preservation after the guarded transaction."""
from pathlib import Path
import copy
import json
from prepare import HERE, OUT, INSTALLED, ARCHIVE, read, sha, write


def main():
    out=HERE/'deployment_01'
    assert not (out/'installed_manifest_01.json').exists()
    transaction_path=HERE/'core_manifest_01.json'; transaction=read(transaction_path)
    install,verify,rollback=[read(out/name) for name in ['install.json','verify.json','rollback_ready.json']]
    assert [install['status'],verify['status'],rollback['status']] == ['INSTALLED_VERIFIED','VERIFIED_AFTER','ROLLBACK_READY']
    game=Path(transaction['game_root'])
    for row in transaction['files']:
        assert sha(game/row['path']) == row['after'],row['path']
    for row in transaction['required_files']:
        assert sha(game/row['path']) == row['sha256'],row['path']
    before,after=install['journal']['protection_before'],install['journal']['protection_after']
    for key in ['saves','unmanaged','dependencies']:
        assert before[key] == after[key],key
    saves=sum(r['kind']=='file' for r in before['saves']['files'])
    archive,=[r for r in transaction['files'] if r['path'] == ARCHIVE]
    recovery=HERE/'recovery/core_sd1_01'
    assert sha(recovery/'old'/ARCHIVE) == archive['before'] and sha(recovery/'new'/ARCHIVE) == archive['after']
    manifest=copy.deepcopy(read(INSTALLED))
    manifest.update(core_epoch='SD1',predecessor_epoch='KM2',
        authorization='User requested Sweet Dreams Johnny presentation cleanup, clarified no gameplay sequence rewrite, and authorized closed-game installation.',
        archive_sha256=archive['after'],core_files=[{'path':r['path'],'bytes':r['after_bytes'],'sha256':r['after']} for r in transaction['files']],
        required_files=transaction['required_files'],core_transaction=str(transaction_path),core_transaction_sha256=sha(transaction_path),
        source_candidate=str(OUT),package_manifest_sha256=sha(OUT/'package_manifest.json'),save_files_preserved=saves,changed_paths=[ARCHIVE],
        unchanged_core_paths=50,compiled_source_changes=0,gameplay_status='PENDING_SUPPORTED_UNSTARTED_SWEET_DREAMS_FIXTURE',
        save_transition_limit='Completed current Sweet Dreams and recovered equipment remain preserved. No reset/reissue or saved mid-scene migration. Review scope begins before using Stefan braindance player on an intact genuine post-Tower fixture; fixture not yet qualified.',
        kold_mirage_status='USER_REPORTED_PASS_EDITING_COMPLETE',
        kold_mirage_acceptance=str(HERE.parent/'kold_mirage_km2/observations/user_acceptance_20261108_01/result.json'))
    write(out/'installed_manifest_01.json',manifest)
    proof={'status':'PASS_SD1_INSTALLED_BYTES_SAVES_DEPENDENCIES_AND_ROLLBACK','installed_manifest_sha256':sha(out/'installed_manifest_01.json'),
        'core_files_verified':51,'unchanged_core_files':50,'changed_paths':[ARCHIVE],'dependency_files_verified':len(transaction['required_files']),
        'save_files_preserved':saves,'save_snapshot_unchanged':True,'unmanaged_game_metadata_unchanged':True,'recovery_ready':True,
        'archive_sha256':archive['after'],'archive_members_verified':1581,'unchanged_archive_members':1579,'changed_private_resources':2,
        'scripts_changed':0,'native_resource_overrides':0,'new_depots':0,'new_ArchiveXL_phase_ids':0,'game_launches':0,'save_writes':0,
        'gameplay':'PENDING_SUPPORTED_UNSTARTED_SWEET_DREAMS_FIXTURE'}
    write(out/'verification.json',proof)
    cp_path=HERE/'checkpoint.json';cp=read(cp_path)
    cp.update(status='INSTALLED_VERIFIED_LIVE_TEST_PENDING_SUPPORTED_FIXTURE',candidate_built=True,installed=True,
        installed_manifest='deployment_01/installed_manifest_01.json',preservation='deployment_01/verification.json',verification='verification.json',
        compile_inventory='compile_inventory.json',archive_readback='archive_readback.json',fixtures='fixture_results.json',test_card='TEST_CARD.md',
        user_test_intent='Current screenshot: start=1, done=1, items_retrieved=1, cancel_bd=0. No reset command provided; earlier intact genuine post-Tower fixture not qualified.',
        game_writes=1,save_writes=0,game_launches=0,next_action='User may start normally. Preserve current completed Sweet Dreams; qualify an intact genuine post-Tower pre-braindance fixture before replay testing. KOLD accepted complete; broader marker-count work remains deferred.')
    cp_path.write_text(json.dumps(cp,indent=2)+'\n',encoding='utf-8')
    old_path=INSTALLED.parents[1]/'checkpoint.json';old=read(old_path)
    old.update(current_successor_checkpoint=str(cp_path),next_action=cp['next_action'])
    old_path.write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
    report=HERE/'REPORT.md';text=report.read_text(encoding='utf-8')
    assert text.count('SD1 is a verified staged successor to KM2.') == 1
    text=text.replace('SD1 is a verified staged successor to KM2.','SD1 is installed over KM2.',1)
    text+='\n## Installed result\n\nClosed-game preflight, installation, post-install verification and rollback readiness passed. Only the existing consolidated archive changed. All 51 Core files and '+str(len(transaction['required_files']))+' dependencies verified; all '+str(saves)+' save files and unmanaged game metadata were preserved. The exact KM2 archive recovery copy is verified. Twenty-two installer actions across eight isolated fixtures passed, including full Core51 install/rollback, interrupted replacement/receipt/rollback recovery and game-running/unknown-file refusal. No game launch, save/fact edit or real rollback occurred.\n\nArchive SHA256: `'+archive['after']+'`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation](deployment_01/verification.json), [deployment report](deployment_01/REPORT.md). Live Sweet Dreams testing remains pending a supported fixture; KOLD MIRAGE remains accepted complete.\n'
    report.write_text(text,encoding='utf-8')
    with (out/'REPORT.md').open('x',encoding='utf-8') as f:
        f.write('# SD1 installed result\n\n**INSTALLED_VERIFIED / VERIFIED_AFTER / ROLLBACK_READY.** Only the existing consolidated archive changed. All 51 Core paths and '+str(len(transaction['required_files']))+' dependencies verified; all '+str(saves)+' save files and unmanaged game metadata were preserved. The exact KM2 archive is retained under `../recovery/core_sd1_01/old/`. File rollback does not undo saved gameplay.\n\nNo game launch, save/fact edit or real rollback occurred. Sweet Dreams presentation remains pending live testing from a supported intact post-Tower fixture. The current reported completed quest is preserved; no reset/restart command has been issued. KOLD MIRAGE remains user-accepted complete. [Manifest](installed_manifest_01.json), [preservation](verification.json), [implementation](../REPORT.md), [test card](../TEST_CARD.md).\n')
    print(json.dumps({'status':proof['status'],'saves':saves,'dependencies':len(transaction['required_files']),
                      'archive_sha256':archive['after'],'changed_paths':1}))


if __name__ == '__main__':
    main()
