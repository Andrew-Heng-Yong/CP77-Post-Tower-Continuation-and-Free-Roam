"""Record one human getter result using a bounded existing-log read.

Writes only this fresh workspace evidence folder and QR15's mutable queue/checkpoint.
No Game API, process control, save parser/writer, build or installer is invoked.
"""
from pathlib import Path
import datetime, hashlib, json, re

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
WORK = BASE.parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
REPORT = '[JF02] ABSOLUTE_CAR_UNRESOLVED'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def fresh(p, value):
    assert not p.exists(), 'Fresh evidence required: ' + str(p)
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def pin(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p)}


def main():
    for name in ['result.json', 'completion.json', 'verification.json', 'scripting_tail.log', 'human_report.txt']:
        assert not (HERE/name).exists(), 'Fresh evidence required'
    readiness = read(BASE/'next_step_01/readiness.json')
    assert sha(readiness['command']['path']) == readiness['command']['sha256']
    assert sha(readiness['independent_review']['path']) == readiness['independent_review']['sha256']
    command = Path(readiness['command']['path']).read_text()
    # This literal return precedes every wrapper field/list call. Reuse the
    # prior nil-fixture evidence; do not rerun all unchanged controls.
    refusal = 'if not s then print("[JF02] ABSOLUTE_CAR_UNRESOLVED") return end'
    assert refusal in command and command.index(refusal) < command.index('s:IsInitialized()')
    fixture = read(BASE/'runtime_probe_02/validation_01.json')
    assert any(c['name'] == 'unresolved_not_reported_as_zero_inactive_or_missing_actor' and c['pass'] for c in fixture['checks'])

    source = GAME/'bin/x64/plugins/cyber_engine_tweaks/scripting.log'
    # Capture only a bounded tail from the existing log. No waiting/recording.
    before = source.stat()
    offset = max(0, before.st_size - 131072)
    with source.open('rb') as stream:
        stream.seek(offset)
        data = stream.read(131072)
    after = source.stat()
    lines = data.decode('utf-8', errors='replace').splitlines()
    if offset:
        lines = lines[1:]  # first line may begin before the captured byte range
    matches = [line for line in lines if re.search(r'\[JF02\]\s+ABSOLUTE_CAR_UNRESOLVED\s*$', line)]
    assert matches, 'Human report retained, but this exact log corroboration requires a fresh assessment if not present'
    assert not any('local ref' in line or 'pcall(function' in line for line in matches)
    (HERE/'scripting_tail.log').write_bytes(data)
    (HERE/'human_report.txt').write_text(REPORT+'\n', encoding='utf-8')

    baseline = read(BASE/'baseline.json')
    preservation = {}
    for category in ['installed', 'original_saves']:
        rows = [{'path': r['path'], 'expected': r['sha256'], 'actual': sha(r['path'])} for r in baseline[category]]
        assert all(r['expected'] == r['actual'] for r in rows), category
        preservation[category] = rows
    active = read(WORK/'prealpha/general_gig_probe_gg1/active.json')
    assert active['state'] == 'STOPPED'
    implementation = WORK/'research/framework_pr63_01/codeware/src/App/World/WorldStateSystem.cpp'
    text = implementation.read_text()
    body = text.split('App::WorldStateSystem::GetPopulationSpawner(',1)[1].split('void App::WorldStateSystem::ActivatePopulationSpawner',1)[0]
    assert all(x in body for x in ['if (!m_communitySystem)', 'if (!spawnerID)', 'if (!spawner)', 'spawnerWeak.Lock()'])

    prior_checkpoint = pin(BASE/'checkpoint.json')
    prior_queue = pin(BASE/'development_queue.json')
    result = {
        'status': 'HUMAN_AND_LOG_CONFIRMED_ABSOLUTE_LOOKUP_UNRESOLVED_CAR_STATE_UNKNOWN',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'human_report': REPORT, 'human_report_origin': 'Current user message transcribed verbatim; original native bytes are retained separately in the bounded log tail.',
        'log_matches': matches, 'log_source': str(source), 'source_bytes_before': before.st_size,
        'source_mtime_before_ns': before.st_mtime_ns, 'source_bytes_after': after.st_size, 'source_mtime_after_ns': after.st_mtime_ns,
        'source_stable_during_read': before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
        'captured_offset': offset, 'captured_bytes': len(data), 'captured_sha256': sha(HERE/'scripting_tail.log'),
        'copy_scope': 'At most128KiB existing log tail; earlier prefix excluded. Command echo is not counted as native output.',
        'command': readiness['command'], 'prepared_independent_review': readiness['independent_review'],
        'current_loaded_save_slot': None, 'same_body_as_JF01': None, 'same_body_as_offline_AutoSave8': None,
        'obtained_spawner_wrapper': False, 'initialized': None, 'active': None,
        'spawned_list_size': None, 'restored_list_size': None, 'reserved_list_size': None,
        'native_wrapper_getter_fields_observed': False,
        'source_failure_boundary': {
            'implementation': pin(implementation),
            'explicit_null_return_sites': ['Missing community-system pointer', 'ResolveNodeRef returned zero', 'GetSpawner weak-pointer lookup/lock yielded no strong object'],
            'exact_site_executed': 'UNKNOWN',
            'limits': 'Matching local source is corroboration, not a native instruction trace or an exhaustive proof of every allocation/error mechanism.'
        },
        'not_proven': ['Car absent or inactive', 'No spawned/restored/reserved entity', 'Prefab lease absent or fully released', 'Original graph currently executing or retired', 'VehicleSpawned predicate status', 'Visual destruction or door setup completion', 'A restoration repair is safe'],
        'assessment': 'The absolute-reference attempt did not produce a wrapper. A short-alias-only explanation is not established by this result; the underlying failure site remains unknown. This is neither a quest FAIL nor proof of a missing car.',
        'preservation': preservation, 'recorder_state': active['state'],
        'automated_game_calls': 0, 'runtime_installation_changes': 0, 'save_or_fact_writes': 0, 'runtime_fix_implemented': False,
        'next_human_test': None, 'next': 'No repeat JF01/JF02 or general scalar snapshot. Remaining repair work is the source-supported car/prefab lifecycle and full startup disposition; no runtime bypass is justified.',
        'prior_checkpoint': prior_checkpoint, 'prior_queue': prior_queue,
    }
    fresh(HERE/'result.json', result)
    completion = {
        'status': 'JF02_ASSESSED_NO_READY_MANUAL_TEST_REPAIR_UNIMPLEMENTED',
        'result': pin(HERE/'result.json'), 'report': pin(HERE/'REPORT.md'), 'handoff': pin(HERE/'HANDOFF.md'),
        'preserved_installed_hashes': len(preservation['installed']), 'preserved_original_save_hashes': len(preservation['original_saves']),
        'ready_human_tests': [], 'runtime_candidate': None, 'runtime_changes': 0,
        'restoration_complete': False, 'next': result['next'],
    }
    fresh(HERE/'completion.json', completion)
    checkpoint = read(BASE/'checkpoint.json')
    checkpoint['status'] = completion['status']
    checkpoint['next'] = result['next']
    checkpoint['latest_JF02_observation'] = {'result': pin(HERE/'result.json'), 'completion': pin(HERE/'completion.json'), 'handoff': str((HERE/'HANDOFF.md').resolve())}
    (BASE/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    queue = read(BASE/'development_queue.json')
    queue['status'] = 'JF02_ASSESSED_NO_READY_MANUAL_TEST_SAFE_ADAPTER_NOT_ESTABLISHED'
    queue['ready_human_tests'] = []
    queue['latest_evidence'] = pin(HERE/'completion.json')
    for name in ['JF01 short-reference/world snapshot', 'JF02 absolute-car lookup']:
        if name not in queue['closed_do_not_repeat']: queue['closed_do_not_repeat'].append(name)
    queue['items'][0]['status'] = 'ABSOLUTE_CAR_LOOKUP_UNRESOLVED_EXTERNAL_WORLD_TRANSITION_UNKNOWN'
    queue['items'][0]['required'] = 'Source-supported preservation/reacquisition and pending-car transition; getter failure site remains unknown. More generic scalar or repeated-reference queries do not prove these contracts.'
    queue['no_new_gameplay_request'] = True
    (BASE/'development_queue.json').write_text(json.dumps(queue,indent=2)+'\n',encoding='utf-8')

    # Read back the evidence and deliberate mutable-pointer updates.
    assert sha(HERE/'result.json') == completion['result']['sha256']
    assert read(BASE/'checkpoint.json')['latest_JF02_observation']['completion']['sha256'] == sha(HERE/'completion.json')
    assert read(BASE/'development_queue.json')['ready_human_tests'] == []
    fresh(HERE/'verification.json', {
        'status': 'OBSERVATION_AND_POINTER_READBACK_PASS', 'completion': pin(HERE/'completion.json'),
        'checkpoint': pin(BASE/'checkpoint.json'), 'queue': pin(BASE/'development_queue.json'),
        'log_corroboration': True, 'command_echo_counted': False, 'unobserved_getter_values_remain_null': True,
        'installed_hashes_preserved': len(preservation['installed']), 'protected_original_save_hashes_preserved': len(preservation['original_saves']),
        'runtime_changes': 0, 'repair_complete': False,
    })
    print(json.dumps({'status':completion['status'],'log_matches':len(matches),'ready_human_tests':0,'installed_hashes_preserved':len(preservation['installed']),'original_save_hashes_preserved':len(preservation['original_saves'])}))


if __name__ == '__main__':
    main()
