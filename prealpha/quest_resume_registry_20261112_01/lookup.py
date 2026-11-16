"""Read-only lookup of the selected registry and stage review packets."""
import argparse
import json
import sqlite3
from prepare import HERE, read


def open_db(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('quest', help='Native ID or title substring')
    ap.add_argument('--stage', help='Journal path substring')
    ap.add_argument('--full', action='store_true', help='Include complete source stage/site packets')
    a = ap.parse_args()
    selected = read(HERE / 'checkpoint.json')
    db = open_db(HERE / selected['registry'] / 'registry.sqlite3')
    contexts = open_db(HERE / selected.get('contexts', 'contexts_01') / 'contexts.sqlite3')
    result = []
    for row in db.execute('SELECT id,title,selection FROM quests WHERE id=? OR instr(lower(title),lower(?))>0', (a.quest, a.quest)):
        q = contexts.execute('SELECT record_json FROM quests WHERE id=?', (row['id'],)).fetchone()
        if not q:
            result.append({**dict(row), 'status': 'Outside stage-context scope; original registry retains exclusion evidence.'})
            continue
        record = json.loads(q[0])
        if a.stage:
            record['matching_stages'] = []
            for s in contexts.execute('SELECT record_json FROM stages WHERE quest_id=? AND instr(lower(path),lower(?))>0', (row['id'], a.stage)):
                stage = json.loads(s[0]); sites = []
                for loc in stage['source_sites']:
                    site = json.loads(contexts.execute('SELECT record_json FROM sites WHERE rid=? AND graph=? AND node=?', loc).fetchone()[0])
                    if not a.full:
                        site = {k: site[k] for k in ['location', 'operation', 'journal_write_inputs',
                                'structurally_reaching_local_inputs', 'registered_root_ordinals', 'optional_flags']}
                    sites.append(site)
                record['matching_stages'].append({**stage, 'site_contexts': sites})
        result.append(record)
    if not result:
        raise SystemExit('Quest not found')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
