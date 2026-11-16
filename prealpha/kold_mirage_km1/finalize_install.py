"""Record verified KM1 installation without changing the game or saves."""
from pathlib import Path
import copy
from prepare import HERE, JP1, OUT, ENTRY, SCRIPT, ARCHIVE, read, sha, write


def main():
    out=HERE/'deployment_01'
    assert not (out/'installed_manifest_01.json').exists()
    transaction=read(HERE/'core_manifest_01.json')
    install=read(out/'install.json')
    verified=read(out/'verify.json')
    rollback=read(out/'rollback_ready.json')
    assert install['status']=='INSTALLED_VERIFIED' and verified['status']=='VERIFIED_AFTER' and rollback['status']=='ROLLBACK_READY'
    game=Path(transaction['game_root'])
    for row in transaction['files']:
        assert sha(game/row['path'])==row['after']
    for row in transaction['required_files']:
        assert sha(game/row['path'])==row['sha256']
    a=install['journal']['protection_before'];b=install['journal']['protection_after']
    assert a['saves']==b['saves'] and a['unmanaged']==b['unmanaged'] and a['dependencies']==b['dependencies']
    saves=[r for r in a['saves']['files'] if r['kind']=='file']
    recovery=HERE/'recovery/core_km1_01'
    for row in transaction['files']:
        if row['path'] in transaction['changing_paths']:
            assert sha(recovery/'old'/row['path'])==row['before']
            assert sha(recovery/'new'/row['path'])==row['after']
    manifest=copy.deepcopy(read(JP1/'deployment_01/installed_manifest_01.json'))
    archive=next(r for r in transaction['files'] if r['path']==ARCHIVE)
    manifest.update(core_epoch='KM1',predecessor_epoch='JP1',authorization='User requested the missing KOLD MIRAGE marker/encounter repair and explicitly requested mq016_active=0 or 1.',archive_sha256=archive['after'],core_files=[{'path':r['path'],'bytes':r['after_bytes'],'sha256':r['after']} for r in transaction['files']],required_files=transaction['required_files'],core_transaction=str(HERE/'core_manifest_01.json'),core_transaction_sha256=sha(HERE/'core_manifest_01.json'),source_candidate=str(OUT),package_manifest_sha256=sha(OUT/'package_manifest.json'),save_files_preserved=len(saves),changed_paths=transaction['changing_paths'],unchanged_core_paths=49,compiled_source_changes=1,gameplay_status='PENDING_USER_POST_TOWER_TEST',save_transition_limit='Inactive KOLD MIRAGE quest and checked child entries only; active flag may be zero or one. Existing issued/progressed/completed/failed owners are not restarted. JP1 old-active-menu limitation remains.')
    write(out/'installed_manifest_01.json',manifest)
    proof={'status':'PASS_KM1_INSTALLED_BYTES_SAVES_DEPENDENCIES_AND_ROLLBACK','installed_manifest_sha256':sha(out/'installed_manifest_01.json'),'core_files_verified':51,'unchanged_core_files':49,'changed_paths':transaction['changing_paths'],'dependency_files_verified':len(transaction['required_files']),'save_files_preserved':len(saves),'save_snapshot_unchanged':True,'unmanaged_game_metadata_unchanged':True,'recovery_ready':True,'archive_sha256':archive['after'],'script_sha256':next(r['after'] for r in transaction['files'] if r['path']==SCRIPT),'archive_members_verified':1581,'unchanged_archive_members':1580,'native_resource_overrides':0,'new_depots':0,'new_ArchiveXL_phase_ids':0,'game_launches':0,'save_writes':0,'gameplay':'PENDING_USER_TEST'}
    write(out/'verification.json',proof)
    checkpoint={'schema':1,'status':'INSTALLED_VERIFIED_AWAITING_USER_POST_TOWER_TEST','authorization':manifest['authorization'],'candidate':'candidate_01','plan':'input_01/plan.json','source_review':'analysis_01.json','typed_verification':'verification.json','compile':'compile_01/result.json','archive_readback':'archive_readback.json','fixtures':'fixture_results.json','installed_manifest':'deployment_01/installed_manifest_01.json','preservation':'deployment_01/verification.json','test_card':'TEST_CARD.md','game_writes':2,'save_writes':0,'game_launches':0,'next_action':'User starts game normally, loads the original post-Tower working fixture and checks native undiscovered marker or immediate discovery, freezer Open/pickup and JP1 dialogue/progression. The accepted pre-ending approach test needs no repetition.'}
    write(HERE/'checkpoint.json',checkpoint)
    old_path=JP1/'checkpoint.json'
    old=read(old_path)
    old['current_successor_checkpoint']=str(HERE/'checkpoint.json')
    old['kold_mirage_test_status']='PRE_KM1_NO_START_REPAIRED_AWAITING_POST_KM1_USER_TEST'
    old['next_action']=checkpoint['next_action']
    old_path.write_text(__import__('json').dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=HERE/'REPORT.md'
    text=report.read_text(encoding='utf-8')
    text=text.replace('KM1 is a staged successor to the installed JP1 pilot.','KM1 is installed over the JP1 pilot.',1)
    text+='\n## Installed result\n\nThe closed-game transaction replaced exactly the archive and S29 script. Preflight, installation, post-install verification and rollback readiness passed. All 51 Core paths and 26 dependencies verified, with all '+str(len(saves))+' saved files and unmanaged game metadata preserved. The exact JP1 archive and script recovery copies are ready. Twenty-seven fixture actions across ten isolated roots covered full Core51 install/rollback, interrupted first and second replacements, recovery, game-running refusal and unknown-file refusal. No real rollback, save write or game launch occurred.\n\nCurrent archive SHA256: `'+archive['after']+'`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation verification](deployment_01/verification.json), [transaction fixtures](fixture_results.json) and [test card](TEST_CARD.md). Gameplay is pending.\n'
    report.write_text(text,encoding='utf-8')
    deployment_report='# KM1 installed result\n\nStatus: **INSTALLED_VERIFIED**, **VERIFIED_AFTER**, **ROLLBACK_READY**. Exactly two existing files changed: the combined archive and S29 script. All 51 Core paths and 26 dependency files verified; all '+str(len(saves))+' saved files and unmanaged game metadata were preserved. No game launch, runtime command, save edit or real rollback occurred.\n\nThe exact JP1 recovery payload is `../recovery/core_km1_01/old/`. File rollback does not undo saved progress. [Installed manifest](installed_manifest_01.json), [preservation result](verification.json), [component report](../REPORT.md) and [test card](../TEST_CARD.md). The native marker/encounter and JP1 dialogue removals still require the user post-Tower test.\n'
    with (out/'REPORT.md').open('x',encoding='utf-8') as f:f.write(deployment_report)
    print({'status':proof['status'],'saves':len(saves),'dependencies':len(transaction['required_files']),'archive_sha256':archive['after'],'changed_paths':transaction['changing_paths']})


if __name__=='__main__':
    main()
