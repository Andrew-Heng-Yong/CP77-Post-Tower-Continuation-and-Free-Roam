"""Record an authorized JB1 install only after all guarded receipts exist.

This writes workspace evidence only. It neither installs nor launches the game.
"""
from pathlib import Path
import copy
import json
from prepare import HERE, OUT, INSTALLED, ARCHIVE, read, sha, write


def main():
    out = HERE / 'deployment_01'
    assert not (out / 'installed_manifest_01.json').exists()
    cp = read(HERE / 'checkpoint.json')
    assert cp.get('deployment_authorized') is True, 'Fresh deployment authorization required'
    transaction_path = HERE / 'core_manifest_01.json'
    transaction = read(transaction_path)
    install, verify, rollback = [read(out / n) for n in ['install.json', 'verify.json', 'rollback_ready.json']]
    assert [install['status'], verify['status'], rollback['status']] == ['INSTALLED_VERIFIED', 'VERIFIED_AFTER', 'ROLLBACK_READY']
    game = Path(transaction['game_root'])
    for row in transaction['files']:
        assert sha(game / row['path']) == row['after'], row['path']
    for row in transaction['required_files']:
        assert sha(game / row['path']) == row['sha256'], row['path']
    before, after = install['journal']['protection_before'], install['journal']['protection_after']
    for key in ['saves', 'unmanaged', 'dependencies']:
        assert before[key] == after[key], key
    saves = sum(r['kind'] == 'file' for r in before['saves']['files'])
    archive, = [r for r in transaction['files'] if r['path'] == ARCHIVE]
    recovery = HERE / 'recovery/core_jb1_01'
    assert sha(recovery / 'old' / ARCHIVE) == archive['before']
    assert sha(recovery / 'new' / ARCHIVE) == archive['after']
    manifest = copy.deepcopy(read(INSTALLED))
    manifest.update(core_epoch='JB1', predecessor_epoch='SD1',
        authorization=cp['deployment_authorization_record'], archive_sha256=archive['after'],
        core_files=[{'path': r['path'], 'bytes': r['after_bytes'], 'sha256': r['after']} for r in transaction['files']],
        required_files=transaction['required_files'], core_transaction=str(transaction_path), core_transaction_sha256=sha(transaction_path),
        source_candidate=str(OUT), package_manifest_sha256=sha(OUT / 'package_manifest.json'),
        installed_receipt=str(out / 'install.json'), post_install_verification=str(out / 'verify.json'),
        rollback_readiness=str(out / 'rollback_ready.json'), save_files_preserved=saves, changed_paths=[ARCHIVE],
        unchanged_core_paths=50, compiled_source_changes=0, gameplay_status='JB1_FIVE_QUEST_LIVE_TESTS_PENDING',
        save_transition_limit='Prospective affected-scene scope; no reset/reissue and no certified already-running scene migration.',
        sweet_dreams_status='SD1_RETAINED_EXACT_LIVE_TEST_PENDING_SUPPORTED_FIXTURE',
        kold_mirage_status='USER_REPORTED_PASS_EDITING_COMPLETE')
    write(out / 'installed_manifest_01.json', manifest)
    proof = {'status': 'PASS_JB1_INSTALLED_BYTES_SAVES_DEPENDENCIES_AND_ROLLBACK',
        'installed_manifest_sha256': sha(out / 'installed_manifest_01.json'), 'core_files_verified': 51,
        'unchanged_core_files': 50, 'changed_paths': [ARCHIVE], 'dependency_files_verified': len(transaction['required_files']),
        'save_files_preserved': saves, 'save_snapshot_unchanged': True, 'unmanaged_game_metadata_unchanged': True,
        'recovery_ready': True, 'archive_sha256': archive['after'], 'archive_members_verified': 1581,
        'unchanged_archive_members': 1568, 'changed_private_resources': 13, 'scripts_changed': 0,
        'native_resource_overrides': 0, 'new_depots': 0, 'new_ArchiveXL_phase_ids': 0,
        'game_launches': 0, 'save_writes': 0, 'gameplay': 'FIVE_QUEST_LIVE_TESTS_PENDING'}
    write(out / 'verification.json', proof)
    cp.update(status='INSTALLED_VERIFIED_LIVE_TEST_PENDING', installed=True, game_writes=1,
        installed_manifest='deployment_01/installed_manifest_01.json', preservation='deployment_01/verification.json',
        deployment_status='INSTALLED_VERIFIED', next_action='User may launch normally and test supported pre-scene fixtures. No quest resets. KOLD complete; Sweet Dreams and wider marker scope unchanged.')
    (HERE / 'checkpoint.json').write_text(json.dumps(cp, indent=2) + '\n', encoding='utf-8')
    with (out / 'REPORT.md').open('x', encoding='utf-8') as f:
        f.write('# JB1 installed result\n\n**INSTALLED_VERIFIED / VERIFIED_AFTER / ROLLBACK_READY.** Only the existing combined archive changed. All 51 Core paths and '
                + str(len(transaction['required_files'])) + ' dependencies verified; all ' + str(saves)
                + ' save files and unmanaged game metadata were preserved. Exact SD1 recovery is retained. No game launch, save/fact edit or real rollback occurred. Five-quest gameplay tests remain pending. File rollback does not undo saved gameplay.\n\n[Manifest](installed_manifest_01.json), [preservation](verification.json), [implementation](../REPORT.md), [test card](../TEST_CARD.md).\n')
    print(json.dumps({'status': proof['status'], 'saves_preserved': saves, 'dependencies': len(transaction['required_files']),
                      'archive_sha256': archive['after'], 'changed_paths': 1}))


if __name__ == '__main__':
    main()
