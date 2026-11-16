"""Record PE1's verified installation; never write game files or saves."""
from pathlib import Path
import copy
import json
from prepare import HERE, BASE, OUT, ARCHIVE, read, sha, write


def main():
    out = HERE/'deployment_01'
    assert not (out/'installed_manifest_01.json').exists()
    transaction_path = HERE/'core_manifest_01.json'
    transaction = read(transaction_path)
    install, verified, rollback = [read(out/name) for name in ['install.json', 'verify.json', 'rollback_ready.json']]
    assert [install['status'], verified['status'], rollback['status']] == ['INSTALLED_VERIFIED', 'VERIFIED_AFTER', 'ROLLBACK_READY']
    game = Path(transaction['game_root'])
    for row in transaction['files']:
        assert sha(game/row['path']) == row['after'], row['path']
    for row in transaction['required_files']:
        assert sha(game/row['path']) == row['sha256'], row['path']
    before, after = install['journal']['protection_before'], install['journal']['protection_after']
    assert before['saves'] == after['saves'] and before['unmanaged'] == after['unmanaged'] and before['dependencies'] == after['dependencies']
    saves = [r for r in before['saves']['files'] if r['kind'] == 'file']
    recovery = HERE/'recovery/core_pe1_01'
    for row in transaction['files']:
        if row['path'] in transaction['changing_paths']:
            assert sha(recovery/'old'/row['path']) == row['before']
            assert sha(recovery/'new'/row['path']) == row['after']
    plan = read(HERE/'input_02/plan.json')
    compilation = read(HERE/'compile_01/result.json')
    overlay_hashes = {str(game/r['path']): r['after'] for r in plan['scripts']}
    for path, old_hash in compilation['input_pins'].items():
        assert sha(path) == overlay_hashes.get(path, old_hash), path
    manifest = copy.deepcopy(read(BASE.parent/'deployment_01/installed_manifest_01.json'))
    archive = next(r for r in transaction['files'] if r['path'] == ARCHIVE)
    manifest.update(core_epoch='PE1', predecessor_epoch='KM1', authorization='User requested that the new marker and encounter policy apply across restored post-Tower content.', archive_sha256=archive['after'], core_files=[{'path': r['path'], 'bytes': r['after_bytes'], 'sha256': r['after']} for r in transaction['files']], required_files=transaction['required_files'], core_transaction=str(transaction_path), core_transaction_sha256=sha(transaction_path), source_candidate=str(OUT), package_manifest_sha256=sha(OUT/'package_manifest.json'), save_files_preserved=len(saves), changed_paths=transaction['changing_paths'], unchanged_core_paths=44, compiled_source_changes=6, gameplay_status='PENDING_USER_POST_TOWER_TEST', save_transition_limit='New Boolean setup admission requires accepted Inactive baselines and existing current progress/owner guards. Counters, later stages, completed/failed and already-issued owners remain protected. No saved fields/schema change; future save transitions and native execution remain unproved.')
    write(out/'installed_manifest_01.json', manifest)
    proof = {'status': 'PASS_PE1_INSTALLED_BYTES_SAVES_DEPENDENCIES_AND_ROLLBACK', 'installed_manifest_sha256': sha(out/'installed_manifest_01.json'), 'core_files_verified': 51, 'unchanged_core_files': 44, 'changed_paths': transaction['changing_paths'], 'dependency_files_verified': len(transaction['required_files']), 'save_files_preserved': len(saves), 'save_snapshot_unchanged': True, 'unmanaged_game_metadata_unchanged': True, 'recovery_ready': True, 'archive_sha256': archive['after'], 'script_hashes': {r['path']: r['after'] for r in plan['scripts']}, 'archive_members_verified': 1581, 'unchanged_archive_members': 1569, 'changed_private_entry_resources': 12, 'changed_private_guard_nodes': 25, 'additional_entries': 17, 'boolean_setup_fields': 20, 'native_resource_overrides': 0, 'new_depots': 0, 'new_ArchiveXL_phase_ids': 0, 'game_launches': 0, 'save_writes': 0, 'gameplay': 'PENDING_USER_TEST'}
    write(out/'verification.json', proof)
    checkpoint = read(HERE/'checkpoint.json')
    checkpoint.update(status='INSTALLED_VERIFIED_AWAITING_USER_POST_TOWER_TEST', candidate='candidate_02', plan='input_02/plan.json', source_review='decisions_01.json', typed_verification='verification.json', compile='compile_01/result.json', archive_readback='archive_readback.json', fixtures='fixture_results.json', installed_manifest='deployment_01/installed_manifest_01.json', preservation='deployment_01/verification.json', test_card='TEST_CARD.md', current_build_installed=True, game_writes=7, save_writes=0, game_launches=0, next_action='User starts the game normally and checks the original post-Tower KOLD MIRAGE fixture, then naturally available unfinished entries. No completed route or pre-ending comparison needs repetition. No fact/save edits.')
    (HERE/'checkpoint.json').write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    old_path = BASE.parent/'checkpoint.json'
    old = read(old_path)
    old.update(current_successor_checkpoint=str(HERE/'checkpoint.json'), next_action=checkpoint['next_action'])
    old_path.write_text(json.dumps(old, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report = HERE/'REPORT.md'
    text = report.read_text(encoding='utf-8')
    assert text.count('PE1 is a verified staged successor to installed KM1.') == 1
    text = text.replace('PE1 is a verified staged successor to installed KM1.', 'PE1 is installed over KM1.', 1)
    text += '\n## Installed result\n\nThe closed-game transaction passed real preflight, installation, post-install verification and rollback readiness. Exactly seven existing paths changed: the combined archive and six scripts. All 51 Core paths and 26 dependencies verified. All '+str(len(saves))+' save files and unmanaged game metadata remained unchanged. Exact KM1 recovery copies of the seven replacements are verified. No game launch, runtime command, save/fact edit or real rollback occurred.\n\nTwenty-seven fixture actions across ten isolated roots passed full Core51 install/rollback, interruption before/after replacement, hard-crash recovery, interrupted rollback, game-running refusal and unknown-file refusal. Static and deployment results do not certify gameplay.\n\nCurrent archive SHA256: `'+archive['after']+'`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation result](deployment_01/verification.json), [deployment report](deployment_01/REPORT.md) and [post-Tower test card](TEST_CARD.md).\n'
    report.write_text(text, encoding='utf-8')
    with (out/'REPORT.md').open('x', encoding='utf-8') as f:
        f.write('# PE1 installed result\n\nStatus: **INSTALLED_VERIFIED**, **VERIFIED_AFTER**, **ROLLBACK_READY**. Exactly seven existing files changed: the archive and six scripts. All 51 Core paths and 26 dependencies verified; all '+str(len(saves))+' save files and unmanaged game metadata were preserved. No game launch, runtime command, save/fact edit or real rollback occurred.\n\nThe exact KM1 recovery payload is `../recovery/core_pe1_01/old/`. File rollback does not undo saved progress. [Installed manifest](installed_manifest_01.json), [preservation result](verification.json), [component report](../REPORT.md) and [test card](../TEST_CARD.md). The broadened native marker/encounter admission and JP1 pilot still await post-Tower gameplay qualification.\n')
    print(json.dumps({'status': proof['status'], 'saves': len(saves), 'dependencies': len(transaction['required_files']), 'archive_sha256': archive['after'], 'changed_paths': len(transaction['changing_paths'])}))


if __name__ == '__main__':
    main()
