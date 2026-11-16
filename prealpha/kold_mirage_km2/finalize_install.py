"""Seal KM2's installed assessment without modifying game files or saves."""
from pathlib import Path
import copy
import json
from prepare import HERE, OUT, INSTALLED, ARCHIVE, read, sha, write


def main():
    out = HERE/'deployment_01'
    assert not (out/'installed_manifest_01.json').exists()
    transaction_path = HERE/'core_manifest_01.json'
    transaction = read(transaction_path)
    install, verify, rollback = [read(out/name) for name in ['install.json','verify.json','rollback_ready.json']]
    assert [install['status'],verify['status'],rollback['status']] == ['INSTALLED_VERIFIED','VERIFIED_AFTER','ROLLBACK_READY']
    game = Path(transaction['game_root'])
    for row in transaction['files']:
        assert sha(game/row['path']) == row['after'], row['path']
    for row in transaction['required_files']:
        assert sha(game/row['path']) == row['sha256'], row['path']
    before, after = install['journal']['protection_before'], install['journal']['protection_after']
    for key in ['saves','unmanaged','dependencies']:
        assert before[key] == after[key], key
    saves = sum(r['kind']=='file' for r in before['saves']['files'])
    archive, = [r for r in transaction['files'] if r['path'] == ARCHIVE]
    recovery = HERE/'recovery/core_km2_01'
    assert sha(recovery/'old'/ARCHIVE) == archive['before'] and sha(recovery/'new'/ARCHIVE) == archive['after']
    manifest = copy.deepcopy(read(INSTALLED))
    manifest.update(core_epoch='KM2', predecessor_epoch='PE1', authorization='User requested KOLD MIRAGE Johnny entity/effects/journal and interaction rewiring, selecting a save before the first fridge opening.', archive_sha256=archive['after'], core_files=[{'path':r['path'],'bytes':r['after_bytes'],'sha256':r['after']} for r in transaction['files']], required_files=transaction['required_files'], core_transaction=str(transaction_path), core_transaction_sha256=sha(transaction_path), source_candidate=str(OUT), package_manifest_sha256=sha(OUT/'package_manifest.json'), save_files_preserved=saves, changed_paths=[ARCHIVE], unchanged_core_paths=50, compiled_source_changes=0, gameplay_status='PENDING_USER_PRE_FIRST_OPEN_TEST', save_transition_limit='Selected update/test point is before the first fridge opening, including the existing private Open-choice scene. Resource/node/actor/option/retained-event IDs remain; no reset or reissue. Already post-Open scenes, actual actor absence and engine/save transitions remain unqualified.')
    write(out/'installed_manifest_01.json', manifest)
    proof = {'status':'PASS_KM2_INSTALLED_BYTES_SAVES_DEPENDENCIES_AND_ROLLBACK', 'installed_manifest_sha256':sha(out/'installed_manifest_01.json'), 'core_files_verified':51, 'unchanged_core_files':50, 'changed_paths':[ARCHIVE], 'dependency_files_verified':len(transaction['required_files']), 'save_files_preserved':saves, 'save_snapshot_unchanged':True, 'unmanaged_game_metadata_unchanged':True, 'recovery_ready':True, 'archive_sha256':archive['after'], 'archive_members_verified':1581, 'unchanged_archive_members':1578, 'changed_private_resources':3, 'scripts_changed':0, 'native_resource_overrides':0, 'new_depots':0, 'new_ArchiveXL_phase_ids':0, 'game_launches':0, 'save_writes':0, 'gameplay':'PENDING_USER_PRE_FIRST_OPEN_TEST'}
    write(out/'verification.json', proof)
    cp_path = HERE/'checkpoint.json'
    cp = read(cp_path)
    cp.update(status='INSTALLED_VERIFIED_AWAITING_USER_PRE_OPEN_TEST', current_build_installed=True, installed_manifest='deployment_01/installed_manifest_01.json', preservation='deployment_01/verification.json', verification='verification.json', source='source_01/manifest.json', compile_inventory='compile_inventory.json', archive_readback='archive_readback.json', fixtures='fixture_results.json', test_card='TEST_CARD.md', game_writes=1, save_writes=0, game_launches=0, next_action='User starts normally, loads the selected save before first fridge opening, and tests Open -> scan -> Take -> Nix with no Johnny actor/effects/name/scanner entry or conversation prompts. Keep broader marker-count investigation deferred.')
    cp_path.write_text(json.dumps(cp,indent=2)+'\n',encoding='utf-8')
    old_path = INSTALLED.parents[1]/'checkpoint.json'
    old = read(old_path)
    old.update(current_successor_checkpoint=str(cp_path), next_action=cp['next_action'])
    old_path.write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
    report = HERE/'REPORT.md'
    text = report.read_text(encoding='utf-8')
    assert text.count('KM2 is a verified staged successor to PE1.') == 1
    text = text.replace('KM2 is a verified staged successor to PE1.','KM2 is installed over PE1.',1)
    text += '\n## Installed result\n\nClosed-game preflight, installation, post-install verification and rollback readiness passed. Only the existing consolidated archive changed. All 51 Core files and 26 dependencies verified; all '+str(saves)+' save files and unmanaged game metadata were preserved. The exact PE1 archive recovery copy is verified. Twenty-two actions across eight isolated fixtures passed full Core51 install/rollback, interrupted replacement/receipt recovery, interrupted rollback, game-running refusal and unknown-file refusal. No game was launched and no save/fact edit or real rollback occurred.\n\nArchive SHA256: `'+archive['after']+'`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation verification](deployment_01/verification.json), [deployment report](deployment_01/REPORT.md) and [pre-Open test card](TEST_CARD.md). Gameplay remains pending.\n'
    report.write_text(text,encoding='utf-8')
    with (out/'REPORT.md').open('x',encoding='utf-8') as f:
        f.write('# KM2 installed result\n\n**INSTALLED_VERIFIED / VERIFIED_AFTER / ROLLBACK_READY.** Only the existing consolidated archive changed. All 51 Core files and 26 dependencies verified; all '+str(saves)+' save files and unmanaged game metadata were preserved. The exact PE1 archive is retained in `../recovery/core_km2_01/old/`. File rollback does not undo gameplay saves.\n\nNo game launch, save/fact edit or real rollback occurred. Actor/interaction presentation and the selected pre-first-opening saved-scene transition await the user test. [Manifest](installed_manifest_01.json), [preservation](verification.json), [implementation](../REPORT.md) and [test card](../TEST_CARD.md).\n')
    print(json.dumps({'status':proof['status'],'saves':saves,'dependencies':len(transaction['required_files']),'archive_sha256':archive['after'],'changed_paths':1}))


if __name__ == '__main__':
    main()
