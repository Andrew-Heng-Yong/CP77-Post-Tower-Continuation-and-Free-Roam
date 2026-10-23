"""Audit complete simple vendor owners/scenes before a bounded opt-in rollout.

Generated output is an evidence manifest, not permission to overwrite scenes.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

from audit_wilson_vendor_owner import graph_edges, walk
from report_scene_route import scalars, unwrap

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'research/b0_vendor_rollout'
OUT = ROOT / 'research/b0_ordinary_vendor_batch'
EXISTING = {
    'wat_lch_clothingshop_01': 'PTFRB0LCHV_',
    'wat_nid_gunsmith_01': 'PTFRB0NIDG_',
    'wat_nid_foodshop_01': 'PTFRB0NIDF_',
    'wat_nid_medicstore_02': 'PTFRB0NIDM_',
    'bls_ina_se5_junkshop_01': 'PTFRB0SE5J_',
    'bls_ina_se5_melee_01': 'PTFRB0SE5M_',
    'cct_dtn_ripdoc_01': 'PTFRB0RIPDTN_',
    'hey_rey_netrunner_01': 'PTFRB0NETREY_',
    'pac_cvi_techstore_01': 'PTFRB0NETCVI_',
    'pac_wwd_ripdoc_01': 'PTFRB0RIPWWD_',
    'std_arr_ripperdoc_01': 'PTFRB0RIPARR_',
    'std_rcr_ripperdoc_01': 'PTFRB0RIPRCR_',
    'wbr_hil_ripdoc_01': 'PTFRB0RIPHIL_',
    'wbr_jpn_ripdoc_01': 'PTFRB0RIPJPN_',
    'wbr_jpn_netrun_01': 'PTFRB0JPNNET1_',
}
DEFER = {
    'wat_kab_ripperdoc_03_ok': 'Charles outcome dialogue writes gig facts; retain complete dialogue for a separate outcome-aware owner.',
    'cct_cpz_food_01': 'Bar drinking and two declared actor roles require their complete local lifecycle.',
    'std_arr_foodshop_01': 'Bar drinking and two declared actor roles require their complete local lifecycle.',
    'wat_nid_foodshop_02': 'Bar drinking/workspot lifecycle has not been tested in vendor cohort.',
    'wbr_hil_foodshop_01': 'Bar drinking/workspot lifecycle has not been tested in vendor cohort.',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


@lru_cache(None)
def resource(source):
    return read(BASE / 'regional_sources/json' / (source.replace('\\', '/') + '.json'))['Data']['RootChunk']


def graph_at(root, route):
    g = root['graph']['Data']
    for part in route.split('/')[1:]:
        n = next(h['Data'] for h in g['nodes'] if h['Data']['id'] == int(part[4:]))
        g = n['phaseGraph']['Data']
    return g


def nm(g):
    return {h['Data']['id']: h['Data'] for h in g['nodes']}


def edge_set(g, handles):
    return sorted((e['source_node_id'], e['source_socket'], e['destination_node_id'], e['destination_socket'])
                  for e in graph_edges(g, 'audit', handles))


def single(values):
    values = list(values)
    assert len(values) == 1, values
    return values[0]


def dist(n):
    c = n.get('condition', {}).get('Data', {})
    if c.get('$type') != 'questDistanceCondition':
        return None
    t = c['type']['Data']
    return {'node': n['id'], 'comparison': t['comparisonType'],
            'radius': t['distanceDefinition2']['Data']['distanceValue'],
            'reference': t['distanceDefinition1']['Data']['nodeRef2']['reference']['$value']}


def spec(row, audit):
    key = Path(row['scene'].replace('\\', '/')).stem
    root = resource(row['source'])
    inner = graph_at(root, row['graph'])
    route = row['graph'].split('/')
    outer = graph_at(root, '/'.join(route[:-1]))
    phase = int(route[-1][4:])
    outer_id = int(route[-2][4:])
    inn, out = nm(inner), nm(outer)
    handles = {str(v['HandleId']): v['Data'] for v in walk(root) if 'HandleId' in v and 'Data' in v}
    ie, oe, re = edge_set(inner, handles), edge_set(outer, handles), edge_set(root['graph']['Data'], handles)
    scene = inn[row['scene_node']]
    inp = single(n['id'] for n in inn.values() if n['$type'] == 'questInputNodeDefinition')
    end = single(n['id'] for n in inn.values() if n['$type'] == 'questOutputNodeDefinition')
    outer_distance = single(dist(n) for n in out.values() if dist(n))
    close = single(dist(n) for n in inn.values() if dist(n) and dist(n)['comparison'] == 'Less')
    far = single(dist(n) for n in inn.values() if dist(n) and dist(n)['comparison'] == 'Greater')
    gate_node = single(n for n in out.values() if n.get('condition', {}).get('Data', {}).get('$type') == 'questFactsDBCondition')
    gate = gate_node['condition']['Data']['type']['Data']
    assert gate['comparisonType'] == 'Less' and gate['value'] == 1, (key, gate)
    activate, deactivate = row['spawn_activate'][0], row['spawn_deactivate'][0]
    scene_socket = single(e[3] for e in ie if e[2] == row['scene_node'])
    expected = sorted([(inp, 'Out', activate['node'], 'In'), (inp, 'Out', far['node'], 'In'),
                       (activate['node'], 'Out', close['node'], 'In'),
                       (close['node'], 'Out', row['scene_node'], scene_socket),
                       (far['node'], 'Out', deactivate['node'], 'In'),
                       (deactivate['node'], 'Out', end, 'In')])
    reasons = []
    if ie != expected:
        reasons.append('Original inner executable topology differs from tested six-edge loop')
    root_pred = [e for e in re if e[2] == outer_id]
    root_nodes = nm(root['graph']['Data'])
    def root_initializer(node_id):
        node = root_nodes[node_id]
        if node['$type'] == 'questInputNodeDefinition':
            return True
        t = node.get('type', {}).get('Data', {})
        starts = [e for e in re if e[2] == node_id]
        return (t.get('$type') == 'questSetVar_NodeType' and t.get('factName') == gate['factName']
                and t.get('value') == 1 and t.get('setExactValue') in (0, 1) and bool(starts)
                and all(root_nodes[e[0]]['$type'] == 'questInputNodeDefinition' for e in starts))
    direct_gate = False
    if len(root_pred) == 1:
        predecessor = root_nodes[root_pred[0][0]]
        c = predecessor.get('condition', {}).get('Data', {})
        t = c.get('type', {}).get('Data', {})
        upstream = [e for e in re if e[2] == predecessor['id']]
        direct_gate = (c.get('$type') == 'questFactsDBCondition'
                       and t.get('factName') == gate['factName']
                       and t.get('comparisonType') == 'Greater' and t.get('value') == 0
                       and any(root_initializer(e[0]) for e in upstream)
                       and all(root_initializer(e[0]) or e[0] == outer_id for e in upstream))
    if not direct_gate:
        reasons.append('Additional ancestor eligibility path needs explicit trace')
    if len(out) != 7 or outer_distance['comparison'] != 'Less' or far['radius'] != 50:
        reasons.append('Outer shape or departure threshold differs')
    if list(scalars(out[phase].get('phasePrefabs', []), 'prefabNodeRef')):
        reasons.append('Embedded prefab owner requires review')
    scene_group = single(group for group in ('regional_scene_sources', 'special_scene_sources')
                         if (BASE / group / 'json' / (row['scene'].replace('\\', '/') + '.json')).exists())
    p = BASE / scene_group / 'json' / (row['scene'].replace('\\', '/') + '.json')
    sr = read(p)['Data']['RootChunk']
    entry = single(e['nodeId']['id'] for e in sr['entryPoints'] if unwrap(e['name']) == scene_socket)
    scene_nodes = {h['Data']['nodeId']['id']: h['Data'] for h in sr['sceneGraph']['Data']['graph']}
    seen, queue = set(), [entry]
    while queue:
        n = queue.pop()
        if n in seen:
            continue
        seen.add(n)
        queue.extend(d['nodeId']['id'] for s in scene_nodes[n].get('outputSockets', []) for d in s.get('destinations', []))
    reachable = [scene_nodes[n] for n in sorted(seen)]
    writes = sorted({str(v['factName']) for n in reachable for v in walk(n) if v.get('$type') == 'questSetVar_NodeType'})
    qtypes = sorted({v['$type'] for n in reachable for v in walk(n) if str(v.get('$type', '')).startswith('quest')})
    panels = sorted({v for n in reachable for o in walk(n) for v in o.values() if isinstance(v, str) and v.startswith('Vendors.')})
    if not panels:
        reasons.append('No literal reachable vendor panel')
    if key in DEFER:
        reasons.append(DEFER[key])
    raw_scene = BASE / scene_group / 'raw' / row['scene'].replace('\\', '/')
    raw_owner = BASE / 'regional_sources/raw' / row['source'].replace('\\', '/')
    return dict(id=key, category=audit['category'], source=row['source'], graph=row['graph'],
                outer=outer_id, phase=phase, input=inp, output=end, scene=row['scene'], scene_node=row['scene_node'],
                scene_socket=scene_socket, scene_marker=row['scene_location'], outer_distance=outer_distance,
                close=close, far=far, gate=gate['factName'], spawn=activate, despawn=deactivate,
                inner_edges=ie, outer_edges=oe, root_predecessors=root_pred,
                scene_group=scene_group, scene_sha256=hashlib.sha256(raw_scene.read_bytes()).hexdigest().upper(),
                source_sha256=hashlib.sha256(raw_owner.read_bytes()).hexdigest().upper(),
                reachable_scene_nodes=len(seen), choice_nodes=sum(n['$type']=='scnChoiceNode' for n in reachable),
                scene_fact_reads=sorted(set(map(str, scalars(reachable, 'factName')))), scene_fact_writes=writes,
                quest_types=qtypes, panel_records=panels, actors=[a['actorName'] for a in sr.get('actors', [])],
                disposition='existing' if key in EXISTING else ('deferred' if reasons else 'review'),
                existing_prefix=EXISTING.get(key), reasons=reasons,
                dialogue_policy='Complete original scene, original entry socket/location and unchanged predicates; no dialogue or state reset')


def main():
    audit = {r['scene']: r for r in read(BASE / 'vendor_template_audit.json') if r['structural_candidate']}
    result = [spec(row, audit[row['scene']]) for row in read(BASE / 'regional_vendor_inventory.json') if row['scene'] in audit]
    OUT.mkdir(exist_ok=True)
    (OUT / 'owner_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    for r in result:
        print(r['disposition'], r['id'], 'gate='+r['gate'], 'choices='+str(r['choice_nodes']),
              'writes='+','.join(r['scene_fact_writes']), 'reason='+';'.join(r['reasons']))
    print(dict(Counter(r['disposition'] for r in result)))


if __name__ == '__main__':
    main()
