"""Inventory five selected quest graph closures; no game or save writes."""
import hashlib
import json
import sqlite3
from pathlib import Path

TASK = Path(__file__).resolve().parent
WS = TASK.parents[1]
QUESTS = [
    ('mq016_bartmoss', r'towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase'),
    ('mq017_streetkid', r'towercontinued\sidejobs_s29\entries\mq017_streetkid.questphase'),
    ('mq029_tourist', r'towercontinued\sidejobs_s28\vehicles\mq029_tourist_entry.questphase'),
    ('mq036_overload', r'towercontinued\sidejobs_s29\entries\mq036_overload.questphase'),
    ('mq042_nomad', r'towercontinued\sidejobs_s29\entries\mq042_nomad.questphase'),
]


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()


def main():
    out = TASK / 'evidence_01'
    assert not out.exists()
    out.mkdir()
    sources = {}
    for p in ['capture.json', 'capture_additions.json']:
        cap = load(WS / 'prealpha/johnny_dialogue_removal_20261107_01/step1_01' / p)
        for row in cap['resources']:
            key = row['depot'].lower()
            group = sources.setdefault(key, [])
            if not any(r['archive'] == row['archive'] and r['sha256'] == row['sha256'] for r in group):
                group.append(row)
    entry_sources = load(WS / 'prealpha/johnny_dialogue_removal_20261107_01/step1_01/entry_sources.json')
    registry_path = WS / 'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json'
    registry = load(registry_path)
    con = sqlite3.connect((WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3').as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    quests = []
    export = {}
    for qid, entry in QUESTS:
        selection = next(x for x in registry['decision_registry'] if x['id'] == qid)
        assert selection['decision'] == 'INCLUDE'
        binding = next(x for x in entry_sources['xl_phase_bindings'] if x['path'] == entry)
        xl_source = next(x for x in entry_sources['source_files'] if x['path'] == binding['file'])
        assert sha(xl_source['path']) == xl_source['sha256']
        todo = [entry]
        seen = set()
        rows = []
        boundaries = []
        while todo:
            depot = todo.pop()
            if depot.lower() in seen:
                continue
            seen.add(depot.lower())
            candidates = sources.get(depot.lower(), [])
            private = [x for x in candidates if x['archive'].lower().endswith('zzzz_ptfr_combined.archive')]
            candidates = private or candidates
            hashes = {x['sha256'] for x in candidates}
            if not candidates or len(hashes) != 1:
                boundaries.append({'depot': depot, 'status': 'MISSING' if not candidates else 'PROVIDER_REVIEW', 'candidates': candidates})
                continue
            row = candidates[0]
            assert sha(row['raw']) == row['sha256'], depot
            rows.append(row)
            if depot.lower().endswith('.scene'):
                indexed = [dict(r) for r in con.execute('select * from resources where depot=? collate nocase and raw_sha256=?', (depot, row['sha256']))]
                if len(indexed) != 1:
                    boundaries.append({'depot': depot, 'status': 'INDEX_PROVIDER_REVIEW', 'index_candidates': indexed})
                else:
                    row = dict(row)
                    row['indexed'] = indexed[0]
                    rows[-1] = row
            else:
                export[row['key'] + '_' + row['sha256'][:10]] = row
            for ref in row['imports']:
                if ref.lower().endswith(('.questphase', '.quest', '.scene')):
                    todo.append(ref)
        quests.append({'id': qid, 'title': selection['title'], 'entry': entry,
                       'registry': selection, 'registration': binding, 'registration_source': xl_source,
                       'resources': rows, 'source_boundaries': boundaries})
        print(qid, 'resources', len(rows), 'scenes', sum(r['depot'].lower().endswith('.scene') for r in rows), 'boundaries', len(boundaries))
    data = {'schema': 1, 'registry_path': str(registry_path), 'registry_sha256': sha(registry_path),
            'quests': quests, 'phase_exports': [{'export_key': k, **r} for k, r in export.items()],
            'scope': 'Five selected post-Tower quest source closures; caller graphs require separate qualification.',
            'game_writes': 0, 'save_writes': 0}
    (out / 'source_inventory.json').write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Phase exports requested:', len(export))


if __name__ == '__main__':
    main()
