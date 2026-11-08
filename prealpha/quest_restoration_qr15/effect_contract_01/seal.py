"""Verify named preservation and update only the mutable QR15 pointers."""
from pathlib import Path
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORK = HERE.parents[2]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def fresh(path, data):
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=2)+'\n')


def main():
    for name in ['preservation.json', 'completion.json', 'verification.json', 'evidence_manifest.json',
                 'checkpoint.before.json', 'development_queue.before.json', 'current-state.before.md']:
        assert not (HERE / name).exists(), 'Final output already exists: ' + name
    result = read(HERE / 'run_01/result.json')
    assert all(row['pass'] for row in result['checks'])
    for row in result['source_pins']:
        assert sha(row['path']) == row['sha256'], row['path']
    baseline = read(BASE / 'baseline.json')
    protected = {}
    for kind in ['installed', 'original_saves']:
        protected[kind] = []
        for row in baseline[kind]:
            actual = sha(row['path'])
            assert actual == row['sha256'], row['path']
            protected[kind].append({**row, 'actual_sha256': actual})
    epoch_path = WORK / 'prealpha/quest_restoration_qr13/source_epoch_02.json'
    assert sha(epoch_path) == 'A2EABC90B9A30E831703B1121BCD350D1AEA6C07C3453C696BBB5A0D56AED5F6'
    epoch = read(epoch_path)
    candidate = Path(epoch['candidate'])
    for depot, expected in epoch['source_resources'].items():
        assert sha(candidate / 'archive_source' / depot) == expected, depot
    for row in epoch['package_files']:
        assert sha(candidate / 'package' / row['path']) == row['sha256'], row['path']
    assert {str(p.relative_to(candidate/'archive_source')).casefold() for p in (candidate/'archive_source').rglob('*') if p.is_file()} == {str(Path(p)).casefold() for p in epoch['source_resources']}
    assert {str(p.relative_to(candidate/'package')).casefold() for p in (candidate/'package').rglob('*') if p.is_file()} == {str(Path(r['path'])).casefold() for r in epoch['package_files']}
    assert sha(epoch['zip']) == epoch['zip_sha256']
    previous = read(BASE / 'event_stage_01/evidence_manifest_01.json')
    for row in previous['files']:
        assert sha(row['path']) == row['sha256'], row['path']
    assert read(WORK / 'prealpha/general_gig_probe_gg1/active.json')['state'] == 'STOPPED'
    helpers = [BASE/'saved_graph_state_01/inspect_native.py', WORK/'tools/parity_audit/common.py', WORK/'tools/parity_audit/model.py']
    fresh(HERE / 'preservation.json', {
        'status': 'NAMED_RUNTIME_ORIGINAL_SAVES_CANDIDATE_AND_PRIOR_EVIDENCE_UNCHANGED',
        'protected': protected, 'source_epoch': pin(epoch_path),
        'candidate_resource_count': len(epoch['source_resources']), 'package_file_count': len(epoch['package_files']),
        'source_and_package_inventory_match': True, 'zip_match': True,
        'prior_event_stage_manifest': pin(BASE/'event_stage_01/evidence_manifest_01.json'),
        'prior_evidence_files_verified': len(previous['files']), 'analysis_helpers': [pin(p) for p in helpers],
        'recorder': 'STOPPED', 'runtime_changes': 0, 'save_or_fact_writes': 0,
        'limit': 'Named protected originals only, not every save or an executing-owner observation. Hash reads do not parse or load a save.'
    })
    state_path = WORK/'docs/knowledge/current-state.md'
    for source, target in [(BASE/'checkpoint.json', HERE/'checkpoint.before.json'),
                           (BASE/'development_queue.json', HERE/'development_queue.before.json'),
                           (state_path, HERE/'current-state.before.md')]:
        with target.open('xb') as f:
            f.write(source.read_bytes())
    checkpoint = read(BASE/'checkpoint.json')
    predecessor = checkpoint['latest_event_stage']['completion']
    assert sha(predecessor['path']) == predecessor['sha256']
    files = [pin(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    fresh(HERE/'evidence_manifest.json', {'files': files, 'runtime_artifact': False})
    completion = {
        'status': result['status'], 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'report': pin(HERE/'REPORT.md'), 'handoff': pin(HERE/'HANDOFF.md'),
        'result': pin(HERE/'run_01/result.json'), 'evidence': pin(HERE/'evidence_manifest.json'),
        'preservation': pin(HERE/'preservation.json'), 'previous_step': predecessor,
        'checks': len(result['checks']), 'checks_scope': 'Static source, graph and byte controls; no gameplay or repair pass',
        'actual_startup_branches': result['startup']['actual_fanout_count'],
        'restoration_complete': False, 'confirmed_runtime_defect': False, 'runtime_candidate': None,
        'runtime_changes': 0, 'save_or_fact_writes': 0, 'ready_human_tests': [],
        'source_closed': result['closed'], 'remaining': result['remaining'],
        'next': 'Use the full branch matrix to establish a state-preserving support/approach continuation. Actual setup application, consumed waits and shared courier history remain unproved. Do not repeat rejected scalar/key/path probes or restart native setup.'
    }
    fresh(HERE/'completion.json', completion)
    checkpoint['status'] = completion['status']
    checkpoint['next'] = completion['next']
    checkpoint['latest_effect_contract'] = {'completion': pin(HERE/'completion.json'), 'handoff': str(HERE/'HANDOFF.md')}
    (BASE/'checkpoint.json').write_text(json.dumps(checkpoint, indent=2)+'\n', encoding='utf-8')
    queue = read(BASE/'development_queue.json')
    queue['status'] = completion['status']
    queue['latest_evidence'] = pin(HERE/'completion.json')
    queue['items'][0]['status'] = 'ALL_STARTUP_BRANCHES_MAPPED_EXACT_EFFECTS_PARTIAL_ADAPTER_DEFERRED'
    queue['items'][0]['required'] = completion['next']
    for finding in result['closed']:
        if finding not in queue['source_closed']:
            queue['source_closed'].append(finding)
    (BASE/'development_queue.json').write_text(json.dumps(queue, indent=2)+'\n', encoding='utf-8')
    state = state_path.read_text(encoding='utf-8-sig')
    old = next(line for line in state.splitlines() if line.startswith('| Latest targeted continuation investigation |'))
    new = ('| Latest targeted continuation investigation | [QR15 startup-effect result, 5 November](../../prealpha/quest_restoration_qr15/effect_contract_01/REPORT.md) maps all16native startup branches and binds the actual vehicle setter. False-accumulate replaces grid values and queues a typed change event; unchanged scalar idempotence does not prove full history/event preservation. Resolved prevention enables are Boolean assignments, with explicit unresolved-target limits. [Prior saved-stage evidence](../../prealpha/quest_restoration_qr15/event_stage_01/REPORT.md) and filtering limits remain valid. No safe prepared-entry adapter, candidate or ready manual test. Core, diagnostics, protected originals and consolidated source/package remain unchanged; closed tests stay closed. |')
    state_path.write_text(state.replace(old, new, 1), encoding='utf-8')
    for row in files:
        assert sha(row['path']) == row['sha256'], row['path']
    fresh(HERE/'verification.json', {
        'status': 'PASS_SOURCE_PRESERVATION_AND_FINAL_READBACK_NO_REPAIR',
        'completion': pin(HERE/'completion.json'), 'checkpoint': pin(BASE/'checkpoint.json'),
        'queue': pin(BASE/'development_queue.json'), 'current_state': pin(state_path),
        'ready_human_tests': [], 'runtime_changes': 0,
    })
    print(json.dumps({'status': completion['status'], 'installed_pins_preserved': len(protected['installed']),
        'original_save_files_preserved': len(protected['original_saves']), 'candidate_resources': len(epoch['source_resources']),
        'package_files': len(epoch['package_files']), 'prior_evidence_files': len(previous['files']), 'runtime_changes': 0}))


if __name__ == '__main__':
    main()
