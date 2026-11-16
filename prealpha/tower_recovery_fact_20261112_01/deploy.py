"""Prepare and record the one-script recovery day counter transaction."""

import argparse
from datetime import datetime
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

from build import (BASELINE, BASELINE_SHA, CHANGES, EPOCH, HERE, PRE, PREVIOUS, R3,
                   TEMPLATE, TEMPLATE_MANIFEST_SHA, TEMPLATE_SHA, one, read, sha, write)


SCHEMA = 'PTFR_TOWER_RECOVERY_FACT_CORE_V1'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
JOURNAL = HERE / 'recovery/core_tower_recovery_fact_01/journal.json'


def prepare(attempt):
    assert not MANIFEST.exists() and not INSTALLER.exists()
    assert sha(BASELINE) == BASELINE_SHA and sha(TEMPLATE) == TEMPLATE_SHA
    predecessor = read(BASELINE)
    assert predecessor['core_epoch'] == PREVIOUS
    candidate = HERE / f'candidate_{attempt:02}'
    package = candidate / 'package'
    compile_path = HERE / f'compile_{attempt:02}/result.json'
    source_check = candidate / 'verification.json'
    compiled, checked = read(compile_path), read(source_check)
    assert compiled['status'] == checked['compile'] == 'PASS'
    assert checked['baseline_sha256'] == BASELINE_SHA
    game = Path(predecessor['game_root'])
    files = []
    for row in predecessor['core_files']:
        rel = row['path']
        src, dest = game / rel, package / rel
        assert sha(src) == row['sha256']
        after = sha(dest)
        if rel == R3:
            assert after == compiled['staged_hashes'][rel] == checked['script_hashes'][rel]
        else:
            assert after == row['sha256']
        files.append({'path': rel, 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': after, 'after_bytes': dest.stat().st_size})
    assert len(files) == 51 and {row['path'] for row in files if row['before'] != row['after']} == CHANGES
    assert set(compiled['staged_hashes']) == {rel for rel in compiled['input_pins'] if rel.endswith('.reds')}
    assert {rel for rel, pin in compiled['staged_hashes'].items() if compiled['input_pins'][rel] != pin} == CHANGES

    template_manifest = TEMPLATE.parent / 'core_manifest_01.json'
    assert sha(template_manifest) == TEMPLATE_MANIFEST_SHA
    proofs = [BASELINE, compile_path, source_check, candidate / 'source.patch']
    manifest = {
        'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': PREVIOUS,
        'scope': 'Drive post-Tower recovery from a capped 11:55 quest fact with saved checkpoint tracking.',
        'game_root': str(game), 'save_root': predecessor['save_root'], 'package_root': str(package),
        'process_names': read(template_manifest)['process_names'], 'files': files, 'changing_paths': [R3],
        'required_files': predecessor['required_files'], 'protected_saves': [], 'working_save_files': [],
        'proofs': [{'path': str(path), 'sha256': sha(path)} for path in proofs],
        'compile_inputs': {str(game / rel): pin for rel, pin in compiled['input_pins'].items()},
        'zip': '', 'zip_sha256': None,
    }
    write(MANIFEST, manifest)
    script = TEMPLATE.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# The Johnny presentation REDscript is the only game write for this load repair.',
         '# The installed profile REDscript is the only game write for this recovery counter update.'),
        (TEMPLATE_MANIFEST_SHA, sha(MANIFEST)),
        ('PTFR_JOHNNY_LOAD_REPAIR_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'QP2_JOHNNY_LOAD_REPAIR'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2_REED_CRASH_AND_JOHNNY_WORLD'", f"$manifest.predecessor_epoch -cne '{PREVIOUS}'"),
        ('recovery/core_johnny_load_01', 'recovery/core_tower_recovery_fact_01'),
        ("$wanted=@('r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds')", f"$wanted=@('{R3}')"),
        ('Core51/one-file Johnny presentation scope drift', 'Core51/one-file recovery counter scope drift'),
    ):
        script = one(script, old, new)
    with INSTALLER.open('x', encoding='utf-8', newline='\n') as out:
        out.write(script)

    # Run the reviewed fixture harness with this worker's manifest and installer.
    harness_path = PRE / 'tower_recovery_profile_hold_20261111_01/deploy.py'
    assert sha(harness_path) == '05F0A78C9951F20788B318D1EF348B53BEA882C235E178843AF0B38396A832DB'
    spec = importlib.util.spec_from_file_location('core_fixture_harness', harness_path)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    assert harness.INSTALLER == INSTALLER and harness.CHANGES == CHANGES
    assert harness.FIXTURES == HERE / 'fixtures/deployment_01'
    actions = harness.run_fixtures(manifest)
    fixture_result = HERE / 'fixture_results.json'
    scope = HERE / 'scope_review.json'
    write(fixture_result, {'status': 'PASS', 'installer_sha256': sha(INSTALLER), 'actions': actions})
    write(scope, {'changed_paths': [R3], 'core_paths': 51, 'source_checks': checked['checks'],
                  'manifest_sha256': sha(MANIFEST)})
    write(HERE / 'readiness.json', {
        'status': 'READY_NOT_INSTALLED', 'manifest_sha256': sha(MANIFEST), 'installer_sha256': sha(INSTALLER),
        'fixture_result': fixture_result.name, 'fixture_result_sha256': sha(fixture_result),
        'scope_review': scope.name, 'scope_review_sha256': sha(scope),
    })
    print(f'Prepared the one-script repair. {len(actions)} transaction fixture actions passed.')


def record(attempt):
    previous, manifest, receipt = read(BASELINE), read(MANIFEST), read(JOURNAL)
    journal_text = receipt['payload_json']
    assert sha256(journal_text.encode()).hexdigest().upper() == receipt['payload_sha256']
    journal = json.loads(journal_text)
    assert journal['manifest_sha256'] == sha(MANIFEST) and journal['state'] == 'INSTALLED_VERIFIED'
    assert set(journal['completed_paths']) == CHANGES
    verify = DEPLOYMENT / 'verify.json'
    rollback = DEPLOYMENT / 'rollback_readiness.json'
    assert read(verify)['status'] == 'VERIFIED_AFTER' and read(rollback)['status'] == 'ROLLBACK_READY'
    before, after = journal['protection_before'], journal['protection_after']
    assert before['saves']['tree_sha256'] == after['saves']['tree_sha256']
    assert before['unmanaged']['tree_sha256'] == after['unmanaged']['tree_sha256']
    assert before['dependencies'] == after['dependencies']
    assert journal['save_writes'] == journal['game_launches'] == 0
    files = [{'path': row['path'], 'bytes': row['after_bytes'], 'sha256': row['after']} for row in manifest['files']]
    game = Path(manifest['game_root'])
    assert all(sha(game / row['path']) == row['sha256'] for row in files + manifest['required_files'])
    compile_path = HERE / f'compile_{attempt:02}/result.json'
    path = DEPLOYMENT / 'installed_manifest_01.json'
    assert not path.exists()
    save_count = sum(row['kind'] == 'file' for row in after['saves']['files'])
    write(path, {
        'schema': 1, 'recorded_date': datetime.fromisoformat(journal['updated_utc']).astimezone().date().isoformat(),
        'core_epoch': EPOCH, 'predecessor_epoch': PREVIOUS,
        'authorization': 'Apply the requested quest fact and daily checkpoint to the installed Tower recovery system.',
        'archive_payloads': previous['archive_payloads'], 'archive_sha256': previous['archive_sha256'],
        'core_files': files, 'required_files': manifest['required_files'],
        'game_root': manifest['game_root'], 'save_root': manifest['save_root'],
        'source_candidate': str(Path(manifest['package_root']).parent), 'archive_source': previous['archive_source'],
        'predecessor_manifest': str(BASELINE), 'predecessor_manifest_sha256': BASELINE_SHA,
        'core_transaction': str(MANIFEST), 'core_transaction_sha256': sha(MANIFEST),
        'installed_receipt': str(JOURNAL), 'installed_receipt_sha256': sha(JOURNAL),
        'post_install_verification': str(verify), 'rollback_readiness': str(rollback),
        'compile_result': str(compile_path), 'compile_sources': read(compile_path)['source_count'],
        'changed_paths': [R3], 'unchanged_core_paths': 50,
        'save_files_preserved': save_count, 'save_tree_sha256': after['saves']['tree_sha256'],
        'gameplay': 'UNVERIFIED',
    })
    print(f'Verified installed repair and {save_count} preserved save files.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'record'))
    parser.add_argument('--attempt', default=1, type=int)
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else record)(args.attempt)
