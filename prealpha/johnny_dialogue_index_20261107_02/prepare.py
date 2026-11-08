"""Pin the verified parent, supplemental exports and current installed sources."""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from common import *


def main():
    out = TASK / 'evidence_01'
    if out.exists():
        raise SystemExit('Use a fresh preparation directory')
    receipt = read(COVERAGE / 'verification.json')
    assert receipt['status'] == 'PASS' and not receipt['step3_started']
    parent = read(PREVIOUS / 'index_02/database_manifest.json')
    assert sha(parent['path']) == parent['sha256']
    original = read(PREVIOUS / 'evidence_01/prepared.json')
    protected = []
    for row in original['checks']:
        actual = sha(row['path'])
        assert actual == row['expected'], row['path']
        protected.append({'path': row['path'], 'sha256': actual})
    rows = [__import__('json').loads(line) for line in
            (COVERAGE / 'evidence_05/exports.jsonl').read_text().splitlines()]
    assert len(rows) == 476
    pins = []
    for rel in ['verification.json', 'evidence_05/exports.jsonl', 'evidence_07/summary.json',
                'evidence_09/boundary_ledger.json', 'evidence_06/path_aliases.json']:
        path = COVERAGE / rel
        pins.append({'path': str(path), 'sha256': sha(path)})
    for rel in ['index_02/verification.json', 'index_02/cli_verification.json', 'search.py']:
        path = PREVIOUS / rel
        pins.append({'path': str(path), 'sha256': sha(path)})
    roles = {r['path'].casefold(): r['role'] for r in original['archives']}
    for row in rows:
        assert row['status'] == 'EXPORTED'
        assert sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256']
        row['resource_id'] = resource_id(row['archive'], row['key'])
        row['provider_role'] = roles[row['archive'].casefold()]
        row['scope'] = ('CURRENT_PTFR_PAYLOAD' if row['archive'].casefold().endswith('zzzz_ptfr_combined.archive')
                        else 'REFERENCE_CENSUS') if 'VOICESET_DISPATCH_GRAPH' in row['reasons'] else 'AUXILIARY_SOURCE'
    out.mkdir()
    write(out / 'prepared.json', {'schema': 1, 'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'parent': parent, 'parent_verification': str(PREVIOUS / 'index_02/verification.json'),
        'protected': protected, 'pins': pins, 'archives': original['archives'],
        'resources': rows, 'game_writes': 0, 'save_writes': 0, 'step3_started': False})
    print(encode({'supplemental_providers': len(rows),
        'reasons': dict(Counter(reason for r in rows for reason in r['reasons'])),
        'protected_files': len(protected), 'parent_sha256': parent['sha256']}))


if __name__ == '__main__':
    main()
