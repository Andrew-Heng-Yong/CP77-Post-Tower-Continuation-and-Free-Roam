"""Generate additive capture definitions without changing legacy row indices."""
import json
import re
import sqlite3
import hashlib
from collections import defaultdict
from common import HERE, REGISTRY, MANIFEST, RED, baseline, read, sha, write, walk, value


def main():
    out = HERE / 'evidence_01'
    assert not out.exists(), 'Fresh evidence required'
    m, game = baseline()
    checkpoint = read(REGISTRY / 'checkpoint.json')
    source = REGISTRY / checkpoint['registry'] / 'registry.sqlite3'
    assert sha(source) == read(REGISTRY / 'report_01/manifest.json')['files']['registry_02\\registry.sqlite3']
    db = sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True); db.row_factory = sqlite3.Row
    text = (game / RED).read_text(encoding='utf-8')
    legacy = {}
    for idx, escaped in re.findall(r'func MetadataJSON(\d+)\(\) -> String \{ return "((?:\\.|[^"\\])*)"; \}', text):
        legacy[int(idx)] = json.loads(json.loads('"' + escaped + '"'))
    assert sorted(legacy) == list(range(158))
    journals, facts, items = set(), set(), set()
    owners = defaultdict(set)
    for i, row in legacy.items():
        journals.update(tuple(v) for v in row['journals']); facts.update(row['fact_names'])
        for path, cls in row['journals']: owners[path, cls].add(row['id'])
    quests = [dict(r) for r in db.execute("SELECT id,title,selection,journal_root FROM quests WHERE selection!='EXCLUDE'")]
    for r in read(REGISTRY / checkpoint['activities'] / 'registry.json')['rows']:
        quests.append({'id': r['journal_root'].rsplit('/',1)[1], 'title': r['journal_root'].rsplit('/',1)[1],
                       'selection': r['family'], 'journal_root': r['journal_root']})
    resources = set()
    for q in quests:
        jp = q['journal_root']
        journals.add((jp, 'gameJournalQuest')); owners[jp, 'gameJournalQuest'].add(q['id'])
        for r in db.execute('SELECT * FROM journals WHERE path=? OR (path>=? AND path<?)', (jp, jp+'/', jp+'0')):
            journals.add((r['path'], r['class'])); owners[r['path'], r['class']].add(q['id'])
            if db.execute('SELECT role FROM resources WHERE rid=?', (r['rid'],)).fetchone()[0] in ('STOCK', 'PTFR'):
                resources.add(r['rid'])
        for r in db.execute('SELECT path,class FROM journal_definitions WHERE path=? OR (path>=? AND path<?)', (jp, jp+'/', jp+'0')):
            if r['class'] in ('gameJournalQuest', 'gameJournalQuestPhase', 'gameJournalQuestObjective'):
                journals.add(tuple(r)); owners[tuple(r)].add(q['id'])
        resources.update(r[0] for r in db.execute('SELECT rid FROM quest_resources WHERE quest_id=?', (q['id'],)))
    # Follow every native/private phase or scene body from these source owners.
    providers = defaultdict(set)
    for r in db.execute("SELECT rid,depot,key FROM resources WHERE role IN ('STOCK','PTFR')"):
        providers[r['depot']].add(r['rid']); providers[r['key']].add(r['rid'])
    children = defaultdict(set)
    for r in db.execute('SELECT rid,target FROM calls'):
        children[r['rid']].update(providers[r['target'].lower().replace('/', '\\')])
    pending = list(resources)
    while pending:
        rid = pending.pop()
        for child in children[rid] - resources:
            resources.add(child); pending.append(child)
    fact_sources, item_sources = defaultdict(set), defaultdict(set)
    for rid in sorted(resources):
        for r in db.execute('SELECT graph,id,parameters_json FROM nodes WHERE rid=?', (rid,)):
            for obj in walk(json.loads(r['parameters_json'])):
                for key, val in obj.items():
                    if key.lower().startswith('fact') and isinstance(value(val), str):
                        name = value(val)
                        if name and name.lower() not in ('none', '0'):
                            facts.add(name); fact_sources[name].add((rid, r['graph'], r['id'], key))
                if obj.get('$type') == 'TweakDBID' and isinstance(value(obj), str) and value(obj).startswith('Items.'):
                    items.add(value(obj)); item_sources[value(obj)].add((rid, r['graph'], r['id']))
    # Native cutoff evidence remains observation, never rewritten to pre-cutoff zero.
    facts.update(['q115_point_of_no_return', 'q307_point_of_no_return', 'q307_active', 'q307_2079',
                  'q307_main_game_killed', 'q307_ep1_killed', 'q307_done', 'q307_finished'])
    data = {'schema': 3, 'quests': quests,
            'journals': [{'path': p, 'class': c, 'quest_ids': sorted(owners[p,c])} for p,c in sorted(journals)],
            'facts': sorted(facts), 'items': sorted(items),
            'limits': ['Source-derived fields include uncertain and conditional paths; missing runtime entries are recorded as unknown.',
                       'Item quantities are observations, not one-time reward receipts or item-instance restoration data.',
                       'No active graph stacks, dialogue cursor, actor state or remaining timers are reconstructed.']}
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    data['fingerprint'] = hashlib.sha256(canonical).hexdigest().upper()
    out.mkdir(); write(out / 'catalogue.json', data)
    write(out / 'catalogue_sources.json', {'registry_sha256': sha(source), 'legacy_source_sha256': sha(game / RED),
        'legacy_indices': {i: r['id'] for i,r in legacy.items()}, 'resources': sorted(resources),
        'facts': {k: sorted(v) for k,v in fact_sources.items()}, 'items': {k: sorted(v) for k,v in item_sources.items()}})
    gates = []
    for rid, graph, start, end, route in [(12674, 'root/10', 97, 169, 1), (1776, 'root/3/113', 97, 46, 2)]:
        resource = dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone())
        edges = [dict(r) for r in db.execute('SELECT * FROM edges WHERE rid=? AND graph=? AND source=? AND destination=?', (rid, graph, start, end))]
        assert len(edges) == 1 and edges[0]['source_socket'] == 'Out' and edges[0]['destination_socket'] == 'In'
        assert sha(resource['export_path']) == resource['export_sha256']
        assert not list(db.execute('SELECT 1 FROM nodes WHERE rid=? AND graph=? AND id BETWEEN 60000 AND 60010', (rid, graph)))
        gates.append({'rid': rid, 'graph': graph, 'from': start, 'to': end, 'route': route,
                      'depot': resource['depot'], 'archive': resource['archive'], 'key': resource['key'],
                      'sha256': resource['sha256'], 'export': resource['export_path'], 'export_sha256': resource['export_sha256']})
    write(out / 'plan.json', {'baseline_sha256': sha(MANIFEST), 'game_root': str(game), 'gates': gates,
                             'catalogue_sha256': sha(out / 'catalogue.json'), 'legacy_count': len(legacy),
                             'legacy_fields_and_indices_unchanged': True})
    print(json.dumps({'quests': len(quests), 'journals': len(journals), 'facts': len(facts), 'items': len(items), 'resources': len(resources)}))


if __name__ == '__main__': main()
