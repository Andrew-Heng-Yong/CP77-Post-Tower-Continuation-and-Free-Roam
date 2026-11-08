"""Pin a fresh, read-only continuation of the Step 1 source inventory."""

import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
STEP1 = WORKSPACE / 'prealpha/johnny_dialogue_removal_20261107_01/step1_01'
STEP2 = WORKSPACE / 'prealpha/johnny_dialogue_index_20261107_01'
OUT = TASK / 'evidence_01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def write(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main():
    if OUT.exists():
        raise SystemExit('A fresh evidence directory is required')
    old_summary = read(STEP1 / 'summary.json')
    for name, key in [('capture.json', 'bulk_capture_sha256'),
                      ('capture_additions.json', 'supplemental_capture_sha256')]:
        assert sha(STEP1 / name) == old_summary[key], name
    capture = read(STEP1 / 'capture.json')
    additions = read(STEP1 / 'capture_additions.json')
    entries = read(STEP1 / 'entry_sources.json')
    baseline = read(STEP1 / 'baseline.json')
    resources = capture['resources'] + additions['resources']
    pins = []
    for path in [STEP1 / name for name in ['summary.json', 'capture.json',
            'capture_additions.json', 'entry_sources.json', 'unresolved.json',
            'baseline.json', 'refinement.json', 'registrations_structured.json',
            'scene_census_outside_closure.json']]:
        pins.append({'path': str(path), 'sha256': sha(path)})
    for name in ['summary.json', 'index_02/database_manifest.json',
                 'index_02/verification.json', 'index_02/cli_verification.json',
                 'evidence_01/prepared.json', 'evidence_01/exports.jsonl']:
        path = STEP2 / name
        pins.append({'path': str(path), 'sha256': sha(path)})
    checks = []
    for row in read(STEP2 / 'evidence_01/prepared.json')['checks']:
        actual = sha(row['path'])
        checks.append({'path': row['path'], 'expected': row['expected'], 'actual': actual})
    assert all(row['actual'] == row['expected'] for row in checks), 'Baseline changed'
    db = STEP2 / 'index_02/dialogue.sqlite3'
    db_manifest = read(STEP2 / 'index_02/database_manifest.json')
    db_hash = sha(db)
    expected_db = read(STEP2 / 'summary.json')['database']['sha256']
    assert db_hash == expected_db, 'Database changed'
    pins.append({'path': str(db), 'sha256': db_hash})
    conn = sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    providers = defaultdict(list)
    for row in resources:
        providers[row['depot']].append(row)
    by_depot = defaultdict(list)
    for row in conn.execute('SELECT * FROM resources'):
        by_depot[row['depot']].append(dict(row))
    conversation_targets = sorted({row[0] for row in conn.execute(
        'SELECT DISTINCT target_depot FROM aux_links')})
    support = defaultdict(set)
    for row in resources:
        for target in row['imports']:
            if Path(target).suffix.lower() in {'.scenerid', '.workspot', '.animgraph'}:
                support[target].add(row['depot'])
    queries = defaultdict(set)
    for target in support:
        queries[target].add('REFERENCED_SUPPORT')
    for target in conversation_targets:
        if target not in by_depot:
            queries[target].add('CONVERSATION_TARGET_MISSING_FROM_INDEX')
    unresolved = read(STEP1 / 'unresolved.json')
    for row in unresolved['missing_candidates']:
        queries[row['depot']].add('STEP1_MISSING_CANDIDATE')
    OUT.mkdir()
    write(OUT / 'prepared.json', {
        'schema': 1, 'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Step 1 source coverage reconciliation, then Step 2 readiness assessment. No Step 3 exchange review.',
        'game_root': baseline['game_root'], 'protected_checks': checks, 'pins': pins,
        'archives': capture['archives'], 'graph_provider_census': capture['graph_provider_census'],
        'table_requests': [{'depot': target, 'reasons': sorted(reasons)}
                           for target, reasons in sorted(queries.items())],
        'opaque_resources': [row for row in resources if row['status'] == 'OPAQUE'],
        'captured_graph_providers': [{'depot': row['depot'], 'archive': row['archive'],
             'key': row['key'], 'sha256': row['sha256']}
             for row in resources if Path(row['depot']).suffix in {'.scene', '.questphase', '.quest', '.gamedef'}],
        'support_reference_sources': {target: sorted(sources) for target, sources in support.items()},
        'conversation_targets': conversation_targets,
        'database': {'path': str(db), 'sha256': db_hash},
        'game_writes': 0, 'save_writes': 0,
    })
    print(json.dumps({'protected_checks': len(checks), 'pins': len(pins),
        'support_unique': dict(Counter(Path(t).suffix for t in support)),
        'table_requests': len(queries), 'conversation_targets': len(conversation_targets),
        'captured_graph_providers': sum(Path(r['depot']).suffix in {'.scene', '.questphase', '.quest', '.gamedef'} for r in resources)}, indent=2))


if __name__ == '__main__':
    main()
