"""Build source stage review packets; never emit runtime admission rules.

Relations are directed local graph connectivity, not causal necessity, feasible
execution, earned player state or saved-owner liveness. Original records remain
immutable and every derived location resolves into the pinned source registry.
"""
import argparse
import json
import sqlite3
from collections import Counter, defaultdict, deque
from functools import lru_cache
from model import value
from prepare import HERE, read, sha, write


def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def closure(seed, adjacency):
    found = {seed}
    pending = [seed]
    while pending:
        for nxt in adjacency.get(pending.pop(), ()):
            if nxt not in found:
                found.add(nxt)
                pending.append(nxt)
    return found


def port_name(node, raw, direction):
    if node['type'] != 'scnQuestNode':
        return raw
    try:
        stamp = json.loads(raw)
        names = node['parameters'].get('isockMappings' if direction == 'input' else 'osockMappings', [])
        index = stamp.get('ordinal', 0)
        if stamp.get('name', 0) == 0 and 0 <= index < len(names):
            return str(value(names[index]))
    except (ValueError, TypeError):
        pass
    return None


class Contexts:
    def __init__(self, source, routes):
        self.db = source
        self.db.row_factory = sqlite3.Row
        self.routes = routes
        self.resources = {r['rid']: dict(r) for r in source.execute(
            'SELECT rid,depot,key,role,sha256,status,root_type FROM resources')}
        self.callers = defaultdict(list)
        for r in source.execute('SELECT * FROM calls'):
            self.callers[r['target'].lower().replace('/', '\\')].append(dict(r))
        self.graph_paths = {(r[0], r[1]) for r in source.execute('SELECT rid,path FROM graphs')}
        self.features = defaultdict(list)
        for r in source.execute('SELECT rid,graph,node,kind FROM features'):
            self.features[r['rid'], r['graph']].append({'node': r['node'], 'kind': r['kind']})

    @lru_cache(maxsize=128)
    def graph(self, rid, path):
        row = self.db.execute('SELECT * FROM graphs WHERE rid=? AND path=?', (rid, path)).fetchone()
        if row is None:
            return None
        nodes = {}
        for r in self.db.execute('SELECT id,type,parameters_json FROM nodes WHERE rid=? AND graph=?', (rid, path)):
            nodes[r['id']] = {'id': r['id'], 'type': r['type'], 'parameters': json.loads(r['parameters_json'])}
        edges = [dict(r) for r in self.db.execute('SELECT * FROM edges WHERE rid=? AND graph=?', (rid, path))]
        forward, reverse = defaultdict(set), defaultdict(set)
        for e in edges:
            if e['source_type'] == 'Output' and e['destination_type'] == 'Input':
                forward[e['source']].add(e['destination'])
                reverse[e['destination']].add(e['source'])
        inputs = json.loads(row['inputs_json'])
        journals = [dict(r) for r in self.db.execute('SELECT node,path,class,operation FROM journals WHERE rid=? AND graph=?', (rid, path))]
        return {'nodes': nodes, 'edges': edges, 'inputs': inputs, 'forward': forward, 'reverse': reverse,
                'kind': row['kind'], 'journals': journals}

    def parent_scopes(self, rid, graph):
        result = []
        if '/' in graph and not graph.startswith('embedded/'):
            parent, node = graph.rsplit('/', 1)
            if node.isdigit() and (rid, parent) in self.graph_paths:
                result.append({'rid': rid, 'graph': parent, 'node': int(node), 'kind': 'INLINE_PARENT'})
        if graph in ('root', 'scene'):
            resource = self.resources[rid]
            for call in self.callers[resource['depot']] + self.callers[resource['key']]:
                if self.resources[call['rid']]['role'] in ('STOCK', 'PTFR'):
                    result.append({**call, 'kind': 'RESOURCE_CALLER'})
        return result

    def stage_site(self, site):
        rid, graph, node = site['rid'], site['graph'], site['node']
        g = self.graph(rid, graph)
        before = closure(node, g['reverse'])
        after = closure(node, g['forward'])
        states, control = set(), []
        for edge in g['edges']:
            if edge['destination'] != node:
                continue
            name = port_name(g['nodes'][node], edge['destination_socket'], 'input')
            control.append({'source': edge['source'], 'source_socket': edge['source_socket'],
                            'raw_input': edge['destination_socket'], 'mapped_input': name,
                            'destination_type': edge['destination_type']})
            if edge['source_type'] == 'Output' and edge['destination_type'] == 'Input' and name is not None:
                states.add(name)
        relations = defaultdict(list)
        for f in self.features[rid, graph]:
            nid = f['node']
            relation = 'SAME_NODE' if nid == node else ('CYCLE' if nid in before & after else
                       'PREDECESSOR' if nid in before else 'SUCCESSOR' if nid in after else 'UNRELATED_LOCAL_BRANCH')
            relations[f['kind']].append({'node': nid, 'relation': relation})
        nearest = set()
        journal_nodes = {x['node'] for x in g['journals'] if x['operation'] == 'WRITE'}
        todo = list(g['reverse'].get(node, ())); seen = {node}
        while todo:
            n = todo.pop()
            if n in seen:
                continue
            seen.add(n)
            if n in journal_nodes:
                nearest.add(n)
            else:
                todo.extend(g['reverse'].get(n, ()))
        roots = sorted({r[0] for r in self.routes.execute(
            'SELECT root FROM reached WHERE rid=? AND graph=? AND node=?', (rid, graph, node))})
        return {'location': [rid, graph, node], 'operation': site['operation'],
                'incoming_controls': control, 'journal_write_inputs': sorted(states) if site['operation'] == 'WRITE' else [],
                'structurally_reaching_local_inputs': sorted(set(g['inputs']) & before),
                'nearest_predecessor_journal_sites': [x for x in g['journals'] if x['node'] in nearest],
                'feature_relations': dict(relations), 'registered_root_ordinals': roots,
                'optional_flags': site.get('optional_flags', []),
                'review_status': 'SOURCE_CONTEXT_ONLY_NOT_A_RESUME_CONTRACT'}

    def scope(self, rid, graph):
        g = self.graph(rid, graph)
        groups = defaultdict(list)
        for edge in g['edges']:
            if edge['source_type'] == 'Output' and edge['destination_type'] == 'Input':
                groups[edge['source'], edge['source_socket']].append(edge)
        fanouts = []
        for (node, socket), edges in groups.items():
            if len(edges) < 2:
                continue
            branches = []
            for edge in edges:
                reached = closure(edge['destination'], g['forward'])
                branches.append({'target': edge['destination'], 'input': edge['destination_socket'],
                                 'journal_writers': sorted({x['node'] for x in g['journals']
                                                           if x['operation'] == 'WRITE' and x['node'] in reached})})
            fanouts.append({'node': node, 'socket': socket, 'branches': branches,
                            'status': 'FANOUT_CANDIDATE_NOT_PROOF_OF_SIMULTANEOUS_OBJECTIVES'})
        return {'rid': rid, 'graph': graph, 'kind': g['kind'], 'input_nodes': g['inputs'],
                'source_provider': self.resources[rid], 'parent_scopes': self.parent_scopes(rid, graph),
                'root_support_source': {'table': 'resources', 'rid': rid, 'column': 'support_json'},
                'node_parameters_source': 'registry.sqlite3 nodes.parameters_json (includes nested instance prefabs and typed actor references)',
                'features': self.features[rid, graph], 'fanout_candidates': fanouts,
                'native_liveness': 'UNQUALIFIED', 'support_liveness': 'UNQUALIFIED'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--registry', default='registry_02'); ap.add_argument('--routes', default='routes_02')
    ap.add_argument('--output', default='contexts_01'); a = ap.parse_args()
    out = HERE / a.output
    assert out.parent == HERE and not out.exists(), 'Fresh contained output required'
    src = HERE / a.registry / 'registry.sqlite3'; route_path = HERE / a.routes / 'routes.sqlite3'
    db = sqlite3.connect(src.resolve().as_uri() + '?mode=ro', uri=True)
    routes = sqlite3.connect(route_path.resolve().as_uri() + '?mode=ro', uri=True)
    ctx = Contexts(db, routes)
    out.mkdir(); target = sqlite3.connect(out / 'contexts.sqlite3')
    target.executescript('''CREATE TABLE stages(quest_id TEXT,path TEXT,class TEXT,record_json TEXT,PRIMARY KEY(quest_id,path));
        CREATE TABLE sites(rid INT,graph TEXT,node INT,record_json TEXT,PRIMARY KEY(rid,graph,node));
        CREATE TABLE scopes(rid INT,graph TEXT,record_json TEXT,PRIMARY KEY(rid,graph));
        CREATE TABLE quests(id TEXT PRIMARY KEY,record_json TEXT);''')
    wanted_scopes, seen_sites = set(), set()
    counts = Counter(); selected_counts = Counter(); quest_rows = []
    for q in db.execute("SELECT id,title,selection,journal_root,record_json FROM quests WHERE selection!='EXCLUDE'"):
        quest = json.loads(q['record_json']); stage_counts = Counter()
        for s in db.execute('SELECT * FROM stages WHERE quest_id=?', (q['id'],)):
            row = json.loads(s['record_json']); sites = row['sites']
            relevant = [x for x in sites if ctx.resources[x['rid']]['role'] in ('STOCK', 'PTFR')]
            for site in relevant:
                key = site['rid'], site['graph'], site['node']
                wanted_scopes.add(key[:2])
                if key not in seen_sites:
                    seen_sites.add(key)
                    target.execute('INSERT INTO sites VALUES(?,?,?,?)', (*key, j(ctx.stage_site(site))))
            record = {'quest_id': q['id'], 'path': s['path'], 'class': s['class'],
                      'source_sites': [[x['rid'], x['graph'], x['node']] for x in relevant],
                      'definition_sources': row['journal_definitions'],
                      'has_native_write': any(x['operation'] == 'WRITE' and ctx.resources[x['rid']]['role'] == 'STOCK' for x in relevant),
                      'has_private_write': any(x['operation'] == 'WRITE' and ctx.resources[x['rid']]['role'] == 'PTFR' for x in relevant),
                      'prerequisites': 'Exact predicates and input controls are retained in source contexts; earned conjunction/alternatives are not inferred.',
                      'parallel_objectives': 'Review scope fanout candidates and journal transitions; no flattened linear stage order.',
                      'required_actors': 'Review root support and every parent scope; resource references alone do not establish required/live actors.',
                      'one_time_rewards': 'Review reward/inventory feature relations, fact writes and receipt ownership; never infer payment from local order.',
                      'resume_contract_status': 'NOT_QUALIFIED'}
            target.execute('INSERT INTO stages VALUES(?,?,?,?)', (q['id'], s['path'], s['class'], j(record)))
            stage_counts['paths'] += 1
            stage_counts['native_writer_paths'] += record['has_native_write']
            stage_counts['private_writer_paths'] += record['has_private_write']
            stage_counts['definition_only_paths'] += not relevant
        qr = {'id': q['id'], 'title': q['title'], 'selection': q['selection'], 'journal_root': q['journal_root'],
              'snapshot_index': quest['snapshot_index'], 'stage_counts': dict(stage_counts),
              'native_source_owners': quest['native_journal_resources'], 'private_source_owners': quest['private_journal_resources'],
              'registered_handlers': [r[0] for r in routes.execute('SELECT root FROM quest_routes WHERE quest_id=?', (q['id'],))],
              'source_contexts_status': 'INDEXED_WITH_EXPLICIT_BOUNDARIES', 'safe_resume_status': 'NOT_QUALIFIED'}
        target.execute('INSERT INTO quests VALUES(?,?)', (q['id'], j(qr))); quest_rows.append(qr)
        counts.update(stage_counts)
        if q['selection'] == 'INCLUDE': selected_counts.update(stage_counts)
        if len(quest_rows) % 25 == 0:
            target.commit(); print('Stage packets', len(quest_rows), flush=True)
    pending = list(wanted_scopes); seen_scopes = set()
    while pending:
        key = pending.pop()
        if key in seen_scopes:
            continue
        seen_scopes.add(key); row = ctx.scope(*key)
        target.execute('INSERT INTO scopes VALUES(?,?,?)', (*key, j(row)))
        for parent in row['parent_scopes']:
            pkey = parent['rid'], parent['graph']
            if pkey not in seen_scopes:
                pending.append(pkey)
    target.commit()
    assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    summary = {'status': 'SOURCE_STAGE_CONTEXTS_NOT_RESUME_RULES', 'quests': len(quest_rows),
               'selected_quests': sum(q['selection'] == 'INCLUDE' for q in quest_rows),
               'stage_counts': dict(counts), 'selected_stage_counts': dict(selected_counts),
               'unique_sites': len(seen_sites), 'owner_and_support_scopes': len(seen_scopes),
               'source_registry_sha256': sha(src), 'source_routes_sha256': sha(route_path),
               'limits': ['Local connectivity does not prove necessity, valid branch combinations or return feasibility.',
                          'No safe stage is certified; source owners are not saved executing owners.',
                          'The 15 separate scopes are inventoried without changing admission.',
                          'Additional installed activity families remain in report_01/coverage.json.',
                          'Base journal definitions remain opaque; pinned map-pin retries did not close coverage.']}
    target.close(); db.close(); routes.close()
    write(out / 'summary.json', summary); write(out / 'quests.json', quest_rows)
    write(out / 'manifest.json', {'files': {p.name: sha(p) for p in out.iterdir() if p.is_file()},
                                'tool_sha256': sha(__file__)})
    print(j(summary))


if __name__ == '__main__':
    main()
