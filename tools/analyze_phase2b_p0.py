"""Read-only runtime collection; write reports only into this workspace.

Run when the user says 'test complete'. No game APIs, recovery, or save writes.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DEFAULT_LOG = GAME / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Phase2B_P0/ptfr_runtime.jsonl'
U = 'UNKNOWN'
STAGES = ['DR03', 'DR01', 'DR02', 'DR04', 'DR05', 'DR06', 'DR07', 'DR08', 'DR09', 'DR10'] + [f'DR11_{i}' for i in range(1, 7)] + ['DR12', 'DR13']


def parse(text):
    rows, errors = [], []
    for number, line in enumerate(text.splitlines(), 1):
        pos = line.find('[PTFR] ')
        if pos < 0:
            continue
        try:
            row = json.loads(line[pos + 7:])
            if row.get('schema') != 1 or row.get('probe') != 'Phase2B-P0':
                raise ValueError('wrong schema/probe')
            if not isinstance(row.get('seq'), int) or not row.get('event') or not row.get('run_id'):
                raise ValueError('missing sequence/event/run')
            row['_line'] = number
            rows.append(row)
        except (ValueError, TypeError) as exc:
            errors.append({'line': number, 'error': str(exc)})
    return rows, errors


def analyze(rows, parse_errors=()):
    if not rows:
        return {'status': 'NO_VALID_TRACE', 'same_session': U, 'parse_errors': list(parse_errors)}
    # Preserve observed file order. Never sort by DR label or pretend sampled facts have write timestamps.
    run = rows[-1]['run_id']
    rows = [r for r in rows if r['run_id'] == run]
    sequence_ok = all(b['seq'] == a['seq'] + 1 for a, b in zip(rows, rows[1:])) and rows[0]['seq'] == 1
    seen = {}
    for r in rows:
        if r['event'] in STAGES and r.get('detail', {}).get('value', 1) == 1:
            seen.setdefault(r['event'], r)
    arm = seen.get('DR02')
    done = seen.get('DR13')
    post = next((r for r in rows if r['event'] == 'DR14' and done and r['seq'] >= done['seq']), None)
    start = arm['seq'] if arm else 0
    end = post['seq'] if post else rows[-1]['seq']
    window = [r for r in rows if start <= r['seq'] <= end]
    late = [r for r in rows if r['seq'] > end]
    front = [r for r in window if r['event'] == 'DR16']
    loads = [r for r in window if r['event'] == 'DR17']
    detach = [r for r in window if r['event'] == 'PLAYER_DETACH']
    stale = any(r['event'] == 'PREEXISTING_MARKER' for r in rows)
    before = arm.get('state', {}) if arm else {}
    after = post.get('state', {}) if post else (done.get('state', {}) if done else {})
    required = ('q307_active', 'q307_done', 'q307_finished', 'q307_2079')
    facts_intact = all(before.get('facts', {}).get(f) == after.get('facts', {}).get(f) and
                       isinstance(after.get('facts', {}).get(f), int) and
                       (after['facts'][f] == 0 if f == 'q307_active' else after['facts'][f] >= 1) for f in required)
    close_row = next((r for r in window if r['event'] == 'CLOSE_REQUEST'), None)
    close = close_row is not None
    idle_row = next((r for r in window if close_row and r['event'] == 'IDLE_ENTER' and
                     r['seq'] > close_row['seq']), None)
    idle = idle_row is not None
    clear_row = next((r for r in window if close_row and r['seq'] >= close_row['seq'] and
                      all(r.get('state', {}).get('credits', {}).get(f) is False
                          for f in ('CredditsScrolling', 'FinalBoardsOpened'))), None)
    teardown_row = next((r for r in window if close_row and r['seq'] >= close_row['seq'] and
                         r['event'] in ('CREDITS_UNINITIALIZE', 'FINALBOARDS_LEAVE')), None)
    credits_teardown_evidence = ('CONFIRMED_BLACKBOARD_FALSE' if clear_row else
                                 'INFERRED_UI_CLOSE_UNINITIALIZE_IDLE' if teardown_row and idle else U)
    clear = credits_teardown_evidence != U
    identity = before.get('player_entity', U)
    continuity = (identity != U and identity == after.get('player_entity') and
                  before.get('attach_count') is not None and before.get('attach_count') == after.get('attach_count') and
                  before.get('detach_count') is not None and before.get('detach_count') == after.get('detach_count') and
                  after.get('player_exists') is True)
    explicit_loss = bool(front or loads or detach)
    same = U
    if arm and explicit_loss:
        same = 'NOT_RETAINED_OR_TRANSITION_OBSERVED'
    elif arm and post and continuity and facts_intact and close and idle and clear and sequence_ok and not stale:
        same = 'INFERRED_RETAINED: matching player ID/lifecycle counters and Tower facts, close/Idle observed; exact native session identity unavailable'
    restrictions = after.get('restrictions', {})
    effective_clear = len(restrictions) == 6 and all(v is False for v in restrictions.values())
    core_ok = (same.startswith('INFERRED_RETAINED') and after.get('tier') == 1 and
               after.get('player_visible') is True and after.get('finalboards_blocked') is False and effective_clear)
    status = 'CORE_STATE_SUPPORTED_MOVEMENT_NEEDS_HUMAN_OBSERVATION' if core_ok else 'INCOMPLETE_OR_FAILED_PROBE'
    if not sequence_ok or stale:
        status = 'INVALID_OR_STALE_TRACE'
    early = [r['seq'] for r in rows if r['event'] in ('DR07', 'DR08', 'DR09', 'DR10', 'DR13') and
             (r.get('state', {}).get('credits', {}).get('CredditsScrolling') is True or
              r.get('state', {}).get('credits', {}).get('FinalBoardsOpened') is True)]
    if early:
        status = 'REJECT_GATE_PRESENTATION_STILL_ACTIVE'
    if parse_errors:
        status = 'INCOMPLETE_TRACE_PARSE_ERRORS'
        if not explicit_loss:
            same = U
    compared = {key: {'before': before.get(key, U), 'after': after.get(key, U)} for key in
                ('tier', 'player_exists', 'player_visible', 'player_entity', 'position', 'facts', 'credits',
                 'credits_board_status', 'fact_listener_count', 'credit_listener_count',
                 'restrictions', 'content_blocked', 'finalboards_blocked', 'saving_locked', 'scenario',
                 'map_available', 'inventory_available', 'phone_available', 'vehicle_available', 'world_ai_simulation',
                 'ep1_root_state', 'base_root_state', 'dogtown_availability')}
    return {'status': status, 'run_id': run, 'sequence_complete': sequence_ok, 'parse_errors': list(parse_errors),
            'same_session': same, 'tower_facts_intact': facts_intact if arm and after else U,
            'frontend_request': 'OBSERVED_EXPOSED_REQUEST' if any(r.get('node') == 'GotoMainMenu' for r in front) else 'NOT_OBSERVED (not proof of absence)',
            'frontend_entry': 'OBSERVED' if any(r.get('node') == 'OnEnterScenario' for r in front) else 'NOT_OBSERVED',
            'load_request': 'OBSERVED_SAVE_OR_CHECKPOINT_REQUEST; PONR attribution UNKNOWN' if loads else
                            'NOT_OBSERVED; native PONR/load absence not conclusively established',
            'route_false_observed': any(r.get('state', {}).get('credits', {}).get('LoadPonRSave') is False for r in window),
            'route_false_graph_return_observed': 'DR02' in seen,
            'credits_teardown_evidence': credits_teardown_evidence,
            'last_graph_stage': next((e for e in reversed(STAGES) if e in seen), U),
            'missing_stages': [e for e in STAGES if e not in seen], 'early_teardown_observations': early,
            'poll_recovered_stages': [e for e, r in seen.items() if r.get('detail', {}).get('evidence', '').startswith('poll')],
            'before_after': compared, 'analysis_window_seq': [start, end],
            'later_frontend_or_load_events': [r['seq'] for r in late if r['event'] in ('DR16', 'DR17')],
            'logger_errors': [r for r in rows if r['event'] == 'LOGGER_ERROR'],
            'read_errors': rows[-1].get('read_errors', {}),
            'timeline': [{'seq': r['seq'], 'time': r.get('elapsed_s', U), 'event': r['event'],
                          'resource': r.get('resource', U), 'node': r.get('node', U), 'detail': r.get('detail', {})}
                         for r in rows if r['event'] not in ('STATE', 'DR14', 'DR15')],
            'limitations': ['Listener timestamps are delivery times; polling cannot establish sub-sample order.',
                            'No native destination detour: missing exposed load/menu callbacks cannot prove no native request.',
                            'Session continuity is inferred from several observations, not a native session GUID.',
                            'Visibility getter is player visibility-component enabled state, not final rendered pixels.',
                            'Effective status effects do not enumerate all restriction source owners.',
                            'UI_CreditsScreen is not exposed through GetAllBlackboardDefs in the observed CET session; UNKNOWN fields are not interpreted as false.',
                            'When credits fields are unavailable, close/uninitialize/Idle supports only inferred UI teardown.',
                            'Read errors are UNKNOWN, never false or success.']}


def markdown(result):
    lines = ['# Phase 2B-P0 runtime analysis', '', f"Status: **{result['status']}**", '',
             f"Same session: {result['same_session']}", '']
    for key in ('run_id', 'last_graph_stage', 'route_false_observed', 'route_false_graph_return_observed',
                'credits_teardown_evidence', 'tower_facts_intact', 'frontend_request', 'load_request', 'missing_stages'):
        lines += [f"- {key}: {result.get(key, U)}"]
    lines += ['', '## Before / after', '', '```json', json.dumps(result.get('before_after', {}), indent=2), '```', '',
              '## Event delivery order', '']
    for r in result.get('timeline', []):
        lines.append(f"- {r['seq']} / {r['time']}: {r['event']} — {r['resource']} / {r['node']}")
    lines += ['', '## Interpretation limits', ''] + [f'- {s}' for s in result.get('limitations', [])]
    return '\n'.join(lines) + '\n'


def readiness_failures(rows, age_seconds):
    failures = []
    if not rows or age_seconds > 120:
        return ['no logger output from the last two minutes']
    latest = [r for r in rows if r['run_id'] == rows[-1]['run_id']]
    state = latest[-1].get('state', {})
    facts = state.get('facts', {})
    if state.get('player_exists') is not True:
        failures.append('player is not present')
    if state.get('archive_present') is not True:
        failures.append('Phase 2B-P0 archive is not detected')
    if state.get('tier', U) == U or not isinstance(state.get('player_visible'), bool):
        failures.append('player tier/visibility read unavailable')
    restrictions = state.get('restrictions', {})
    if len(restrictions) != 6 or not all(isinstance(v, bool) for v in restrictions.values()):
        failures.append('one or more restriction reads unavailable')
    if not isinstance(state.get('finalboards_blocked'), bool):
        failures.append('finalboards content-token read unavailable')
    if not all(isinstance(facts.get(f), int) for f in ('q307_active', 'q307_done', 'q307_finished', 'q307_2079')):
        failures.append('one or more q307 fact reads unavailable')
    if facts.get('q307_active') != 1 or facts.get('q307_2079', 0) < 1:
        failures.append('save is not in the expected active q307 / 2079 state')
    fact_count = len(facts)
    expected_facts = fact_count if fact_count else 0
    listener_events = [r for r in latest if r['event'] == 'FACT_LISTENERS_READY']
    listener = listener_events[-1] if listener_events else None
    if not listener or listener['detail'].get('registered') != listener['detail'].get('expected') or \
            listener['detail'].get('expected') != state.get('fact_listener_count') or \
            state.get('fact_listener_count') != expected_facts:
        failures.append('fact listeners are incomplete for the current save')
    board_status = state.get('credits_board_status')
    credit_count = state.get('credit_listener_count')
    if board_status == 'AVAILABLE':
        if credit_count != 6 or not all(isinstance(state.get('credits', {}).get(f), bool)
                for f in ('CredditsScrolling', 'FinalBoardsOpened', 'LoadPonRSave')):
            failures.append('credits board exists but its reads/listeners are incomplete')
    elif board_status in ('NOT_CREATED', 'DEFINITION_UNEXPOSED'):
        if credit_count != 0:
            failures.append('credits listeners are present without a current credits board')
        read_errors = latest[-1].get('read_errors', {})
        # CET's JSON encoder represents an empty Lua table as [] on this host.
        # A nonempty array is malformed and must not silently pass readiness.
        if read_errors == []:
            read_errors = {}
        if not isinstance(read_errors, dict):
            failures.append('recorder read-error payload is malformed')
            read_errors = {}
        if read_errors.get('credits_board'):
            failures.append('credits blackboard API raised an error')
        if board_status == 'DEFINITION_UNEXPOSED':
            init = next((r for r in latest if r['event'] == 'DR00'), None)
            attempts = init.get('detail', {}).get('hook_attempts', {}) if init else {}
            required_hooks = ('MenuScenario_FinalBoards.OnEnterScenario',
                              'MenuScenario_FinalBoards.OnCloseFinalBoardsRequest',
                              'CreditsGameController.OnUninitialize',
                              'MenuScenario_Idle.OnEnterScenario')
            if not all(attempts.get(h) == 'registration_requested_not_runtime_verified' for h in required_hooks):
                failures.append('credits blackboard is unexposed and required UI observer registration failed')
    else:
        failures.append('credits board availability is unknown')
    if any(r['event'] == 'PREEXISTING_MARKER' for r in latest) or \
            any(v != 0 for k, v in facts.items() if k.startswith('PTFRP0_') or k == 'PostTowerFreeRoamActive'):
        failures.append('probe markers already exist in this save')
    if any(r['event'] == 'LOGGER_ERROR' for r in latest):
        failures.append('recorder emitted a logger error')
    return failures


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log', type=Path, default=DEFAULT_LOG)
    ap.add_argument('--out', type=Path, default=ROOT / 'research/phase2b_p0/runtime')
    ap.add_argument('--check-ready', action='store_true', help='Cheap recorder check after loading the disposable q307 save; no game writes')
    args = ap.parse_args()
    # No save reading or game-side writes. Preserve raw input in original location.
    if not args.log.is_file():
        raise SystemExit('NOT READY: logger file is missing. Do not start the ending.')
    rows, errors = parse(args.log.read_text(encoding='utf-8-sig', errors='replace'))
    if args.check_ready:
        import time
        problems = list(errors)
        problems.extend(readiness_failures(rows, time.time() - args.log.stat().st_mtime))
        if problems:
            raise SystemExit('NOT READY: ' + '; '.join(str(p) for p in problems) + '. Do not start the ending.')
        board_status = rows[-1]['state']['credits_board_status']
        if board_status == 'NOT_CREATED':
            print('READY (credits board deferred): archive, fresh facts, player state and fact listeners pass. Credits listeners will attach when final boards create their UI blackboard. Proceed with ONE watched-credit run.')
        elif board_status == 'DEFINITION_UNEXPOSED':
            print('READY (UI blackboard unexposed): archive, fresh facts, player state, fact listeners and UI observer registration pass. Credits-field values remain UNKNOWN; quest markers and UI lifecycle will be recorded. Proceed with ONE watched-credit run.')
        else:
            print('READY: archive, fresh facts, player state and all listeners pass. Proceed with ONE watched-credit run.')
        return
    result = analyze(rows, errors)
    if not args.out.resolve().is_relative_to(ROOT):
        ap.error('Output must remain inside the workspace')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'analysis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (args.out / 'analysis.md').write_text(markdown(result), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('timeline', 'before_after')}, indent=2))


if __name__ == '__main__':
    main()
