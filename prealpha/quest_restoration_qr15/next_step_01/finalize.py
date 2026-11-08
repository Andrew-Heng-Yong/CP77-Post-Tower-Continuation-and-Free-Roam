"""Seal bounded offline evidence and update workspace-only continuation pointers.

Reads installed/source/save hashes. Never writes to the game, a candidate or saves.
Existing outputs refuse overwrite; QR15 checkpoint/queue are intentionally mutable.
"""
from pathlib import Path
import datetime, hashlib, json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORK = BASE.parents[1]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def fresh(p, data):
    p = Path(p)
    assert not p.exists(), str(p)
    p.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def pin(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p)}


def check_rows(rows, root):
    for r in rows:
        p = Path(r['path'])
        if not p.is_absolute():
            p = root / p
        assert sha(p) == r['sha256'], str(p)
    return len(rows)


def main():
    for name in ['preservation_assessment.json', 'readiness.json', 'completion.json', 'verification.json']:
        assert not (HERE / name).exists(), 'Fresh output required: ' + name
    raw = read(HERE / 'preservation.json')
    assert raw['installed_match'] and raw['original_saves_match'] and raw['recorder_state'] == 'STOPPED'
    changed = [r for r in raw['pins'] if r['expected'] != r['actual']]
    qr14_checkpoint = WORK / 'prealpha/quest_restoration_qr14/checkpoint.json'
    assert len(changed) == 1 and Path(changed[0]['path']) == qr14_checkpoint
    # This specific already-recorded continuation edit preceded this substage;
    # a different pointer hash/content is not silently accepted.
    assert changed[0]['actual'] == sha(qr14_checkpoint) == 'DC64453212E3B118432CCDEC5A5DF1015A37B6D4384D803FBF748B21E2FD08AE'
    old = read(qr14_checkpoint)
    assert old['state'] == 'QR13_02_INSTALLED_VERIFIED_ROLLBACK_READY'
    assert old['installed'] == 'QR13:02 Core + unchanged QR10D01/D00E'
    assert sha(old['completion']) == old['completion_sha256'] == 'DAFCC2C6A84F7013F6477832A80C3DB913A4A63F643A172820A6CC24140E09CE'

    epoch = read(WORK / 'prealpha/quest_restoration_qr13/source_epoch_02.json')
    candidate = Path(epoch['candidate'])
    source = candidate / 'archive_source'
    for depot, expected in epoch['source_resources'].items():
        p = source / depot
        assert p.resolve().is_relative_to(source.resolve()) and sha(p) == expected, str(p)
    check_rows(epoch['package_files'], candidate / 'package')
    assert sha(epoch['zip']) == epoch['zip_sha256']

    native = BASE / 'saved_graph_state_01/inspector_review_01'
    native_readback = check_rows(read(native / 'manifest_01.json')['files'], native)
    native_verification = read(native / 'verification_01.json')
    assert native_verification['checks_count'] == 18 and native_verification['live_inspector_readiness'] == 'BLOCKED_NOT_PREPARED'
    check_rows(native_verification['inputs'], WORK)
    car = BASE / 'runtime_probe_01/car_binding_review_01'
    car_checks = read(car / 'verification_01.json')
    car_readback = check_rows(car_checks['files'], car)

    probe = BASE / 'runtime_probe_02'
    primary = read(probe / 'validation_01.json')
    independent = read(probe / 'review_01/review.json')
    assert len(primary['checks']) == 21 and all(c['pass'] for c in primary['checks'])
    assert len(independent['checks']) == 23 and not independent['blocking_findings']
    check_rows(primary['inputs'], WORK)
    check_rows(independent['source_pins'], WORK)

    assessment = {
        'status': 'RUNTIME_SAVES_AND_CANDIDATE_PRESERVED_MUTABLE_POINTER_DRIFT_EXPLICITLY_REVIEWED',
        'raw_comparison': pin(HERE / 'preservation.json'),
        'installed_hashes_match': len(raw['installed']), 'original_save_hashes_match': len(raw['original_saves']),
        'immutable_baseline_document_pins_match': len(raw['pins']) - len(changed),
        'documented_mutable_pointer_change': changed[0],
        'disposition': 'QR14 checkpoint already contains the prior JF01/native-store continuation update. Installed selection and verified deployment completion are unchanged. Raw all-pins comparison remains a discrepancy; no immutable evidence was rewritten.',
        'qr13_source_hashes_match': len(epoch['source_resources']), 'qr13_package_hashes_match': len(epoch['package_files']),
        'qr13_zip_match': True, 'native_evidence_files_read_back': native_readback, 'car_evidence_files_read_back': car_readback,
        'runtime_installation_changes': 0, 'save_or_fact_writes': 0, 'native_plugin_selected': False,
    }
    fresh(HERE / 'preservation_assessment.json', assessment)
    readiness = {
        'status': 'JF02_READY_FOR_ONE_MANUAL_READ_ONLY_LOOKUP_NOT_A_QUEST_TEST',
        'test': 'JF02', 'card': pin(probe / 'TEST_CARD.md'), 'command': pin(probe / 'car.command.txt'),
        'primary_validation': pin(probe / 'validation_01.json'), 'independent_review': pin(probe / 'review_01/review.json'),
        'installation_required': False, 'logger_start_stop_required': False, 'recorder_state': 'STOPPED',
        'player_state': 'Current loaded working post-Tower playthrough; exact JF01 loaded-body identity remains unknown. Report save switch/reload and slot if known.',
        'human_output': 'Complete [JF02] line only; no quest replay or save/fact mutation.',
        'limits': 'Resolution and exposed stored-list sizes are not native VehicleSpawned, visual/door, unique live actor, executing-owner or released-lease proof.',
    }
    fresh(HERE / 'readiness.json', readiness)
    evidence_paths = [
        HERE/'REPORT.md', HERE/'HANDOFF.md', HERE/'preservation_assessment.json', HERE/'readiness.json',
        BASE/'root_saved_resource_array_01/extraction.json', BASE/'root_saved_resource_array_01/header.json',
        BASE/'root_binding_providers_01/manifest.json', BASE/'quest_compression_il_01.json',
        native/'manifest_01.json', native/'verification_01.json', car/'binding_evidence.json', car/'verification_01.json',
    ]
    completion = {
        'status': 'OFFLINE_BINDING_COMPLETE_JF02_AWAITING_HUMAN_REPAIR_UNIMPLEMENTED',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'evidence': [pin(p) for p in evidence_paths],
        'offline_feasibility_complete': True, 'restoration_complete': False, 'runtime_candidate': None,
        'native_plugin_selected': False, 'runtime_changes': 0, 'game_calls': 0, 'save_or_fact_writes': 0,
        'checks_separate_not_additive': {'native_static': 18, 'strict_array_decoder': 16, 'car_binding': 34, 'primary_lua_source': 21, 'independent_command_review': 23},
        'remaining': ['External world lease release completion', 'Complete16branch non-replaying startup disposition', 'Car visual/door/pending transition', 'Actual currently executing owner/stage beyond static cleanup and historical root binding'],
        'next': 'One source-bound absolute-car lookup from readiness.json; do not repeat JF01 or completed quests.',
    }
    fresh(HERE / 'completion.json', completion)
    checkpoint = read(BASE / 'checkpoint.json')
    checkpoint['status'] = completion['status']
    checkpoint['next'] = completion['next']
    checkpoint['latest_next_step'] = {'completion': pin(HERE/'completion.json'), 'readiness': pin(HERE/'readiness.json'), 'handoff': str((HERE/'HANDOFF.md').resolve())}
    (BASE / 'checkpoint.json').write_text(json.dumps(checkpoint, indent=2) + '\n', encoding='utf-8')
    queue = read(BASE / 'development_queue.json')
    queue['status'] = 'EVIDENCE_ADVANCED_JF02_LOOKUP_READY_REPAIR_DEFERRED'
    queue['ready_human_tests'] = [{'id': 'JF02', 'kind': 'ONE_SHOT_READ_ONLY_LOOKUP', 'readiness': pin(HERE/'readiness.json')}]
    queue['latest_evidence'] = pin(HERE/'completion.json')
    queue['source_closed'] = ['Actual cut graph-registration cleanup ordering', 'Historical body EP1 rootindex1/full Jason startup path', 'Exact typed car full world reference']
    queue['items'][0]['status'] = 'GRAPH_CUT_ORDER_AND_HISTORICAL_ROOT_BOUND_EXTERNAL_WORLD_TRANSITION_UNKNOWN'
    queue['items'][0]['required'] = 'Complete native startup/car/prefab-lease transition. JF02 can narrow actual car registration only; do not promote it to whole-owner proof.'
    (BASE / 'development_queue.json').write_text(json.dumps(queue, indent=2) + '\n', encoding='utf-8')
    for r in completion['evidence']:
        assert sha(r['path']) == r['sha256']
    fresh(HERE/'verification.json', {'status': 'SEALED_READBACK_AND_POINTERS_PASS', 'completion': pin(HERE/'completion.json'), 'checkpoint': pin(BASE/'checkpoint.json'), 'queue': pin(BASE/'development_queue.json'), 'repair_complete': False, 'native_plugin_built': False, 'new_gameplay_requested': False, 'manual_read_only_lookup_pending': 'JF02'})
    print(json.dumps({'status': completion['status'], 'installed_preserved': len(raw['installed']), 'original_saves_preserved': len(raw['original_saves']), 'source_resources_preserved': len(epoch['source_resources']), 'manual_command': str((probe/'car.command.txt').resolve())}))


if __name__ == '__main__':
    main()
