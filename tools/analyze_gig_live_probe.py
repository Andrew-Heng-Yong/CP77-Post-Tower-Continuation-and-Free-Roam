"""Read tagged CET diagnostic output only; never execute logged commands."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "PTFR_GIG_AUDIT"
LINE = re.compile(r'^\[[^\]]+\] \[\d+\] (\{.*\})$')
STATES = {0: 'Undefined', 1: 'Inactive', 2: 'Active', 3: 'Succeeded', 4: 'Failed'}


def valid_state(value):
    return type(value) is int and value in STATES


def world(row):
    facts = row.get('facts', {})
    names = ['PostTowerFreeRoamActive', 'q307_done', 'q307_finished', 'q307_2079', 'q307_main_game_killed']
    if all(facts.get(n) == 1 for n in names):
        return 'POST_TOWER_MARKERS'
    if all(facts.get(n) == 0 for n in names):
        return 'PRE_TOWER_MARKERS'
    return 'UNKNOWN_OR_MIXED_MARKERS'


def analyze(log_path, revision=None):
    raw = log_path.read_bytes()
    records = []
    incomplete_or_invalid = []
    for line_no, line in enumerate(raw.decode('utf-8-sig', errors='replace').splitlines(), 1):
        # A pasted command is not an observation. Incomplete buffered output is
        # retained as a diagnostic, never repaired into a synthetic snapshot.
        if TAG in line and re.match(r'^\[[^\]]+\] \[\d+\] \{', line):
            try:
                json.loads(line.split('] ', 2)[2])
            except json.JSONDecodeError:
                incomplete_or_invalid.append(line_no)
        match = LINE.match(line)
        if not match or TAG not in line:
            continue
        try:
            data = json.loads(match[1])
        except json.JSONDecodeError:
            continue
        if data.get('tag') != TAG:
            continue
        if revision is not None and data.get('probe_revision', 1) != revision:
            continue
        records.append({'line': line_no, 'classification': world(data), 'snapshot': data})
    assert records, 'No complete tagged JSON snapshots found; command history is not a result.'
    summary = []
    for record in records:
        data = record['snapshot']
        journal = data.get('journal', {})
        errors = data.get('errors', {})
        summary.append({
            'line': record['line'], 'utc': data.get('utc'), 'classification': record['classification'],
            'probe_revision': data.get('probe_revision', 1), 'user_label': data.get('user_label'),
            'journal_entries': len(journal),
            'resolved_entries': sum(e.get('present') is True for e in journal.values()),
            'numeric_states': sum(valid_state(e.get('state')) for e in journal.values()),
            'errors': len(errors), 'error_fields': list(errors),
            'facts': data.get('facts'),
            'same_player_during_read': data.get('player_before') == data.get('player_after'),
            'same_tracking_during_read': data.get('tracked_before') == data.get('tracked_after'),
            'delayed_before': data.get('delayed_before'), 'delayed_after': data.get('delayed_after'),
        })
    pair = None
    pair_reason = 'Require exactly one pre-Tower and one post-Tower observation from the same probe revision.'
    classifications = [r['classification'] for r in records]
    if (len(records) == 2 and sorted(classifications) == ['POST_TOWER_MARKERS', 'PRE_TOWER_MARKERS']
            and len({r['snapshot'].get('probe_revision', 1) for r in records}) == 1):
        pre, post = (next(r['snapshot'] for r in records if r['classification'] == c)
                     for c in ['PRE_TOWER_MARKERS', 'POST_TOWER_MARKERS'])
        all_paths = sorted(pre['journal'].keys() | post['journal'].keys())
        states = {}
        for path in all_paths:
            before = pre['journal'].get(path, {}).get('state')
            after = post['journal'].get(path, {}).get('state')
            available = valid_state(before) and valid_state(after)
            states[path] = {'pre': before, 'post': after,
                            'pre_name': STATES.get(before, 'UNKNOWN') if valid_state(before) else 'UNKNOWN',
                            'post_name': STATES.get(after, 'UNKNOWN') if valid_state(after) else 'UNKNOWN',
                            'comparable': available, 'changed': before != after if available else None}
        pair = {
            'capture_order': classifications,
            'classification_basis': 'Captured Tower facts, not user_label; no exact save-slot or ancestry detection.',
            'probe_revision': pre.get('probe_revision', 1),
            'pre_utc': pre.get('utc'), 'post_utc': post.get('utc'),
            'fact_differences': {n: [pre['facts'].get(n), post['facts'].get(n)] for n in sorted(pre['facts'].keys() | post['facts'].keys()) if pre['facts'].get(n) != post['facts'].get(n)},
            'journal_nonstate_differences': {
                p: {k: [pre['journal'][p].get(k), post['journal'][p].get(k)]
                    for k in ('present', 'id', 'hash', 'optional', 'tracked')
                    if pre['journal'][p].get(k) != post['journal'][p].get(k)}
                for p in pre['journal'].keys() & post['journal'].keys()
                if any(pre['journal'][p].get(k) != post['journal'][p].get(k) for k in ('present', 'id', 'hash', 'optional', 'tracked'))
            },
            'journal_states': states,
            'journal_state_differences': {p: s for p, s in states.items() if s['changed'] is True},
            'unavailable_state_comparisons': [p for p, s in states.items() if not s['comparable']],
            'journal_state_comparison': 'UNKNOWN if either state read failed; no inference from equal UNKNOWN values',
        }
        pair_reason = None
    return {'status': 'OBSERVED_DIAGNOSTIC_OUTPUT_NOT_RESTORATION_ADMISSION',
            'log': str(log_path), 'log_sha256_at_read': hashlib.sha256(raw).hexdigest().upper(),
            'requested_revision': revision, 'incomplete_or_invalid_result_lines': incomplete_or_invalid,
            'record_count': len(records), 'summary': summary, 'records': records, 'pair': pair,
            'pair_unavailable_reason': pair_reason,
            'limitations': [
                'User labels do not identify the loaded save; classification uses the captured Tower facts.',
                'UNKNOWN or failed getters remain unavailable, never decoded from offline byte patterns.',
                'Equal player/tracking before and after is a bounded consistency check, not an atomic snapshot guarantee.',
                'Zero local failure or completion flags do not prove full provenance, native owner state or payment history.'
            ], 'game_writes': 0, 'save_writes': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', type=int, help='Select exactly this probe revision; never mix v1 and v2.')
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.relative_to((ROOT / 'research/gig_restoration').resolve())
    assert destination.suffix == '.json' and not destination.exists(), 'Use a new research JSON output.'
    report = analyze(args.log, args.revision)
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'record_count': report['record_count'], 'summary': report['summary']}, indent=2))
