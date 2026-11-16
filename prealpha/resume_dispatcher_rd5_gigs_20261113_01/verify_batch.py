"""Check six proposed gig entrances against source and real save evidence."""
from collections import Counter
from pathlib import Path
import json
import sqlite3
import struct
import sys

from capture import BASELINE_SHA, HERE, ROOT, baseline, read, sha, write

# Reuse the framed native-save reader and the repository graph normalizer.
sys.path.insert(0, str(ROOT / 'prealpha/handler_preservation_hp1_20261112_01'))
from analyze import framed, freezer, paths, phase_hash
from model import effects, load_export, normalize, reachable, value, walk

REGISTRY = ROOT / 'prealpha/quest_resume_registry_20261112_01'
SAVED = ROOT / 'prealpha/handler_preservation_hp1_20261112_01/saves_01'
RD4 = ROOT / 'prealpha/resume_dispatcher_rd4_20261113_01'
SNAPSHOTS = {
    'history': ('snapshot_hs1_20261112T193921Z_151_2.json',
                'C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE'),
    'live': ('snapshot_hs1_20261112T171055Z_161_1.json',
             '849751BD2A07EFA27D1BE09D5EB38403F59B7D7F07BDB1948CAF8C38A1BFEF6D'),
}


def readonly(relative):
    database = REGISTRY / relative
    db = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


def snapshot_rows(game, kind):
    name, digest = SNAPSHOTS[kind]
    file = game / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1' / name
    assert sha(file) == digest
    return {r['definition']['id']: r for r in read(file)['rows']}


def graph(source, path):
    g = next(g for g in source['graphs'] if g['path'] == path)
    assert not g['unresolved_connections']
    return {r['id']: r['parameters'] for r in g['nodes']}, [tuple(e) for e in g['edges']]


def ancestry(db, rid, scope='root', seen=frozenset()):
    marker = (rid, scope)
    if marker in seen:
        return []
    visited = seen | {marker}
    if scope != 'root':
        assert scope.startswith('root/')
        parent, node = scope.rsplit('/', 1)
        return [(*steps, (rid, parent, int(node))) for steps in ancestry(db, rid, parent, visited)]
    if rid in (9717, 13718):
        return [((rid, 'game', 0 if rid == 9717 else 1),)]
    callers = db.execute('''SELECT c.rid,c.graph,c.node FROM calls c JOIN resources src ON src.rid=c.rid
        WHERE c.target=(SELECT depot FROM resources WHERE rid=?) AND src.role='STOCK'
        AND c.field='phaseResource' ORDER BY c.rid,c.graph,c.node''', (rid,))
    return [(*steps, (parent, scope, node)) for parent, scope, node in callers
            for steps in ancestry(db, parent, scope, visited)]


def saved_records(directory):
    projection = read(directory / 'manifest.json')
    assert projection['root_gap_hex'] == '026B577A51814903CAE118A84B9942C8C4'
    data = {}
    for row in projection['nodes']:
        p = Path(row['path'])
        assert sha(p) == row['sha256']
        data[row['name']] = (p.read_bytes(), row['id'])
    catalogue = paths(*data['customArray'])
    hashes = Counter(phase_hash(path) for path in catalogue)
    events = [(h, n) for token, h, n in struct.iter_unpack(
        '<QII', framed(*data['eventManager'], 16)) if token and n != 0xFFFF]
    return projection, catalogue, hashes, events, freezer(*data['questPhaseFreezer'])


def registrations(prefix, saved):
    _, catalogue, hashes, events, frozen = saved
    matching = [p for p in catalogue if p[:len(prefix)] == prefix]
    keys = {phase_hash(p): p for p in matching}
    ancestors = [(phase_hash(prefix[:i]), prefix[i]) for i in range(1, len(prefix))]
    assert all(hashes[key] == 1 for key in keys)
    assert all(hashes[key] <= 1 for key, _ in ancestors)
    return {
        'cached_paths': len(matching),
        'descendant_nodes': [[list(keys[h]), n] for h, n in events if h in keys],
        'ancestor_nodes': [list(prefix[:i+2]) for i, edge in enumerate(ancestors) if edge in events],
        'freezer_groups': sum(group['owner'][0] in keys or tuple(group['owner']) in ancestors
                              or any(m['key'][0] in keys for m in group['members']) for group in frozen),
    }


def match(guard, history, live, past_counts, live_counts, past_facts, live_facts, owners):
    return (
        all(history.get(r['path']) == r['history'] and live.get(r['path']) == r['live']
            and ('counter' not in r or past_counts.get(r['path']) == live_counts.get(r['path']) == r['counter'])
            for r in guard['journals'])
        and all(past_facts.get(name) == live_facts.get(name) == v for name, v in guard['facts'].items())
        and all(owners.get(name) == 0 for name in guard['zero_receipts'])
    )


def evidence_gate(stage, previous, after, local_saves):
    definition = previous['definition']
    assert previous['stable'] and after['stable'] and definition == after['definition']
    journal = definition['journals']
    names = [j[0] for j in journal]
    history, live = (dict(zip(names, row['states'], strict=True)) for row in (previous, after))
    past_counts, live_counts = (dict(zip(names, row['counters'], strict=True)) for row in (previous, after))
    past_facts, live_facts = (dict(zip(definition['fact_names'], row['facts'], strict=True))
                             for row in (previous, after))
    states = []
    for path, kind, *_ in journal:
        label = path.rsplit('/', 1)[-1]
        active = kind in ('gameJournalQuest', 'gameJournalQuestPhase') or label in stage['active_objectives']
        completed = kind == 'gameJournalQuestObjective' and label in stage['completed_objectives']
        expected = 2 if active or kind == 'gameJournalQuestDescription' else 3 if completed else 1
        current = 4 if active else expected
        assert history[path] == expected and live[path] == current, path
        item = {'path': path, 'class': kind, 'history': expected, 'live': current}
        if kind == 'gameJournalQuestObjective':
            assert past_counts[path] == live_counts[path] == 0
            item['counter'] = 0
        states.append(item)
    assert past_facts == live_facts
    receipts = ['PTFRU9_' + stage['id'] + '_' + key for key in (
        'Request', 'ParentEntered', 'Started', 'MainFinished', 'OwnerFinished',
        'Fault', 'CreditEntered', 'CreditDone', 'FailureMonitorEntered',
    )]
    guard = {'journals': states, 'facts': past_facts, 'zero_receipts': receipts}
    # This predicate describes the bounded fixture. Deployment will need the
    # independently reviewed predicates and working native graph, including support.
    for save in local_saves:
        present = {j['path']: j['state_u32'] for j in save['journals']}
        assert all(present.get(r['path'], 1) == r['live'] for r in states)
        assert all((save['facts'][name] or 0) == v for name, v in live_facts.items())
        assert all(save['facts'][key] in (None, 0) for key in receipts)
    owners = dict.fromkeys(receipts, 0)
    assert match(guard, history, live, past_counts, live_counts, past_facts, live_facts, owners)
    rejected = 0
    for j in states:
        p = j['path']
        for bad in (1, 2, 3, 4, -1):
            if bad != j['history']:
                assert not match(guard, history | {p: bad}, live, past_counts, live_counts, past_facts, live_facts, owners)
                rejected += 1
            if bad != j['live']:
                assert not match(guard, history, live | {p: bad}, past_counts, live_counts, past_facts, live_facts, owners)
                rejected += 1
        if 'counter' in j:
            assert not match(guard, history, live, past_counts, live_counts | {p: 1}, past_facts, live_facts, owners)
            rejected += 1
    for key, v in past_facts.items():
        assert not match(guard, history, live, past_counts, live_counts, past_facts, live_facts | {key: v+1}, owners)
        rejected += 1
    for key in owners:
        assert not match(guard, history, live, past_counts, live_counts, past_facts, live_facts, owners | {key: 1})
        rejected += 1
    return guard, rejected


def review(stage, db, routes, sources, members, saves, prior, after):
    qid = stage['id']
    records = {}
    for rid in (stage['wrapper'], stage['main'], stage['stage_body'], stage['native_main'],
                *stage['native_companions'], stage['reward'][0]):
        row = dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone())
        assert sha(row['export_path']) == row['export_sha256']
        if row['role'] == 'PTFR':
            assert members[row['depot']] == row['sha256'], row['depot']
        records[rid] = row
        if rid not in sources:
            sources[rid] = normalize(load_export(row['export_path']))
    wrap = records[stage['wrapper']]
    xl = routes.execute('SELECT binding_json FROM roots WHERE depot=?', (wrap['depot'],)).fetchall()
    assert len(xl) == 1
    binding = json.loads(xl[0][0])
    owner, owner_edges = graph(sources[stage['wrapper']], stage.get('wrapper_graph', 'root'))
    main, socket = stage['main_input']
    assert value(owner[main]['phaseResource']['DepotPath']) == records[stage['main']]['depot']
    assert (65004, 'Out', 'Output', main, socket, 'Input') in owner_edges

    body = sources[stage['stage_body']]
    nodes, edges = graph(body, stage['stage_graph'])
    candidates = reachable(stage['stage_seeds'], [(a,b) for a,_,x,b,_,y in edges if x=='Output' and y=='Input'])
    assert set(stage['stage_seeds']) <= nodes.keys()
    assert set(stage['consumed_nodes']) <= nodes.keys() and not set(stage['consumed_nodes']) & candidates
    writers = []
    for label, *address in stage['activation_writers']:
        scope, node = address if len(address) == 2 else (stage['stage_graph'], address[0])
        writers_nodes, writers_edges = graph(body, scope)
        assert writers_nodes[node]['type']['path']['realPath'].endswith('/' + label)
        assert any(e[3] == node and e[4] == 'Active' for e in writers_edges)
        if scope == stage['stage_graph']:
            assert node in candidates
        else:
            assert scope.startswith(stage['stage_graph'] + '/')
            assert int(scope.rsplit('/', 1)[-1]) in candidates
        writers.append([scope, node])
    assert {label for label, *_ in stage['activation_writers']} == set(stage['active_objectives'])
    reward_rid, scope, node, name = stage['reward']
    reward, _ = graph(sources[reward_rid], scope)
    assert [value(r) for r in reward[node]['type']['rewards']] == [name]
    if reward_rid == stage['stage_body'] and scope == stage['stage_graph']:
        assert node not in stage['stage_seeds']
    paths_seen = []
    for rid in (stage['native_main'], *stage['native_companions']):
        callers = ancestry(db, rid)
        assert callers
        for steps in callers:
            prefix = tuple(s[2] for s in steps)
            rows = {label: registrations(prefix, saved) for label, saved in saves.items()}
            paths_seen.append({'resource': rid, 'source_path': steps, 'controls': rows})
    guard, count = evidence_gate(stage, prior[qid], after[qid], [saves[slot][0] for slot in ('AutoSave-3','AutoSave-5')])
    return {
        'id': qid, 'title': stage['title'], 'status': 'DEFER_SUPPORT_AND_OWNER_REVIEW',
        'blocker': stage['blocker'], 'wrapper_registration': binding, 'source_resources': list(records.values()),
        'proposed_stage_graph': stage['stage_graph'], 'proposed_stage_seeds': stage['stage_seeds'],
        'proposed_activation_writers': writers, 'excluded_consumed_nodes': stage['consumed_nodes'],
        'local_structural_reach': len(candidates),
        'local_effect_sites': [i for i in sorted(candidates) if effects(nodes[i])],
        'reward': stage['reward'], 'source_owner_paths': paths_seen, 'fixture_guard': guard,
        'rejected_fixture_mutations': count,
    }


def main():
    _, game = baseline()
    stages = read(HERE / 'stages.json')
    previous = snapshot_rows(game, 'history')
    after = snapshot_rows(game, 'live')
    saves = {directory.name: saved_records(directory) for directory in (
        SAVED/'ManualSave-26', SAVED/'AutoSave-10', SAVED/'AutoSave-11',
        HERE/'saves_01/AutoSave-3', HERE/'saves_01/AutoSave-5',
    )}
    members = {r['depot']: r['sha256'] for r in read(RD4/'archive_01/readback.json')['members']}
    assert len(members) == 1742
    sources = {}
    with readonly('registry_02/registry.sqlite3') as db, readonly('routes_02/routes.sqlite3') as routes:
        results = [review(s, db, routes, sources, members, saves, previous, after) for s in stages]
    controls = sum(r['rejected_fixture_mutations'] for r in results)
    write(HERE/'evidence_01/batch_assessment.json', {
        'status': 'PASS_OFFLINE_STAGE_PREFLIGHT', 'installed_manifest_sha256': BASELINE_SHA,
        'stage_input_sha256': sha(HERE/'stages.json'), 'stages': results,
        'fixture_count': len(saves), 'rejected_fixture_mutations': controls,
        'qualified_runtime_entrances': 0, 'save_writes': 0, 'game_writes': 0,
    })
    print(f'Checked {len(results)} proposed gig stages against {len(saves)} saved controls. '
          f'{controls} guard mutations rejected. Runtime entries remain deferred.')


if __name__ == '__main__':
    main()
