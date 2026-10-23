"""Reproducible local population-selection audit; never writes game resources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_wilson_vendor_owner import compact_node, graph_edges, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/afterlife_world'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def value(x):
    return x.get('$value', x) if isinstance(x, dict) else x


def graph(root, label):
    handles = {str(v['HandleId']): v['Data'] for v in walk(root)
               if 'HandleId' in v and 'Data' in v}
    g = root['graph']['Data']
    return {'nodes': [compact_node(n['Data']) for n in g['nodes']],
            'edges': graph_edges(g, label, handles)}


def main():
    source_paths = [OUT/'patron_vanilla_master_phase.json', OUT/'patron_vanilla_registry.json',
                    OUT/'population_rules_records.json', OUT/'manifest.json',
                    OUT/'patrons_manifest.json', OUT/'population_phase.json',
                    OUT/'patrons_registry.streamingsector.json']
    phase_path = OUT/'patrons_sources/json/base/quest/main_quests/prologue/q005/afterlife/phases/q005_afterlife_phase.questphase.json'
    scene_path = OUT/'patrons_sources/json/base/quest/main_quests/prologue/q005/afterlife/scenes/00_afterlife_global_scene.scene.json'
    area_path = ROOT/'research/misty_viktor_world/r7_showworld_sources/json/base/worlds/03_night_city/_compiled/default/exterior_-12_8_0_1.streamingsector.json'
    regional_path = ROOT/'research/phase2b_p4/vendor_owner/json/base/open_world/community/watson/little_china/wat_lch_phase.questphase.json'
    source_paths += [phase_path, scene_path, area_path, regional_path]
    embedded = read(regional_path)['Data']['EmbeddedFiles']
    master = next(e['Content'] for e in embedded if value(e['FileName']).endswith('afterlife_master_phase.questphase'))
    assert master == read(source_paths[0])['Content']
    owner = graph(master, 'afterlife_master/root')
    edges = {(e['source_node_id'], e['source_socket'], e['destination_node_id'], e['destination_socket'])
             for e in owner['edges']}
    required = [(0,'Out',58,'In'), (58,'Out',60,'In'), (60,'Out',61,'In'),
                (61,'Out',7,'Afterlife_In'), (60,'CutSource',4,'CutDestination'),
                (2,'Out',34,'In'), (34,'Out',33,'In'), (33,'Out',50,'In'),
                (50,'Out',4,'Afterlife_103_In')]
    assert all(e in edges for e in required)
    master_nodes = {n['Data']['id']:n['Data'] for n in master['graph']['Data']['nodes']}
    assert master_nodes[0]['condition']['Data']['type']['Data']['factName'] == 'q103_done'
    assert master_nodes[0]['condition']['Data']['type']['Data']['value'] == 1
    assert value(master_nodes[7]['phaseResource']['DepotPath']).endswith('q005_afterlife_phase.questphase')
    registry = {r['community_index']:r for r in read(OUT/'patron_vanilla_registry.json')}
    cohorts = []
    for idx, name in [(1070,'q005_com_afterlife_background'), (8665,'afterlife_com'),
                      (3027,'q005_com_afterlife_community'), (7725,'q103_com_afterlife_crowd'),
                      (2821,'q005_com_afterlife_tube_dancers')]:
        r = registry[idx]; c = r['community']; entries = []
        for e in r['entries']:
            phases = []
            for ph in e['data']['phases']:
                d = ph['Data']
                phases.append({'name':value(d['phaseName']), 'alwaysSpawned':d.get('alwaysSpawned'),
                               'appearances':[value(a) for a in d['appearances']],
                               'periods':d['timePeriods']})
            entries.append({'name':e['name'],'record':value(e['data']['characterRecordId']),
                            'spawnInView':e['data'].get('spawnInView'),'phases':phases})
        # A capacity per entry, never a sum over mutually exclusive phases.
        capacity = sum(max(t['quantity'] for ph in e['phases'] for t in ph['periods']) for e in entries)
        cohorts.append({'index':idx,'name':name,'community_id':c['communityId']['entityId']['hash'],
                        'area_type':c['communityAreaType'],'entries':entries,'entry_count':len(entries),
                        'configured_entry_capacity_sum':capacity,'initial_states':c['entriesInitialState']})
    by_name = {c['name']:c for c in cohorts}
    assert by_name['q005_com_afterlife_background']['configured_entry_capacity_sum'] == 66
    assert by_name['q103_com_afterlife_crowd']['configured_entry_capacity_sum'] == 80
    assert by_name['q005_com_afterlife_tube_dancers']['configured_entry_capacity_sum'] == 10
    phase_root = next(e['Content'] for e in embedded if value(e['FileName']).endswith('q005_afterlife_phase.questphase'))
    ordinary = graph(phase_root, 'embedded_q005_afterlife/root')
    child_handles = {str(v['HandleId']): v['Data'] for v in walk(master) if 'HandleId' in v and 'Data' in v}
    mission_edges = graph_edges(master_nodes[4]['phaseGraph']['Data'], 'master/node4', child_handles)
    assert any(e['destination_node_id']==5 and e['destination_socket']=='q103_In' for e in mission_edges)
    assert any(e['destination_node_id']==54 and e['destination_socket']=='q005_In' for e in ordinary['edges'])
    ordinary_actions = [x for x in walk(ordinary['nodes']) if x.get('$type')=='questCommunityTemplate_NodeType']
    assert len(ordinary_actions) == 6
    assert {value(a['communityEntryName']) for a in ordinary_actions if value(a['spawnerReference'])=='#afterlife_com'} == {'cleaner','mercenary_big','valentino_01','valentino_02','valentino_03'}
    scene = read(scene_path)['Data']['RootChunk']
    scene_nodes = {n['Data']['nodeId']['id']:n['Data'] for n in scene['sceneGraph']['Data']['graph']}
    scene_routes = []
    for ep in scene['entryPoints']:
        pending = [ep['nodeId']['id']]; seen = set()
        while pending:
            i = pending.pop()
            if i in seen: continue
            seen.add(i)
            pending.extend(d['nodeId']['id'] for s in scene_nodes[i]['outputSockets'] for d in s['destinations'])
        actions=[]; conditions=[]
        for i in sorted(seen):
            for x in walk(scene_nodes[i].get('questNode',{})):
                if x.get('$type') == 'questCommunityTemplate_NodeType':
                    actions.append({'node':i, **{k:value(x[k]) for k in ('action','spawnerReference','communityEntryName','communityEntryPhaseName')}})
                if 'factName' in x: conditions.append({'node':i,**x})
        scene_routes.append({'input':value(ep['name']),'reachable_nodes':sorted(seen),'actions':actions,'fact_conditions_or_writes':conditions})
    area = read(area_path)['Data']['RootChunk']; area_rows=[]
    for i,h in enumerate(area['nodes']):
        n=h.get('Data',{})
        cid=n.get('sourceObjectId',{}).get('hash')
        if cid not in {c['community_id'] for c in cohorts}:continue
        es=n['area']['Data']['entriesData']
        area_rows.append({'node':i,'community_id':cid,'type':n['$type'],'source_prefab_hash':n['sourcePrefabHash'],
                          'streaming_distance':n['streamingDistance'],
                          'spots':[{'entry':value(e['entryName']), 'phase':value(ph['entryPhaseName']),
                                    'period':value(t['periodName']), 'ids':[s['hash'] for s in t['spotNodeIds']]}
                                   for e in es for ph in e['phasesData'] for t in ph['timePeriodsData']]})
    assert sum(len(t['ids']) for a in area_rows if a['community_id']==by_name['q005_com_afterlife_background']['community_id'] for t in a['spots']) == 66
    record_evidence=read(OUT/'population_rules_records.json')
    assert all(s['facts']['q103_done']==[1] and s['unchanged'] for s in record_evidence['save_samples'])
    pm=read(OUT/'patrons_manifest.json'); r1=read(OUT/'manifest.json')
    branches=[b for b in r1['population_branches'] if b['role']=='patron']
    assert len(branches)==26
    assert all(b['original_spawner'].endswith('/#q103_com_afterlife_crowd') for b in branches)
    runtime=read(OUT/'population_phase.json')
    facts=sorted({x['factName'] for x in walk(runtime) if 'factName' in x})
    assert 'q103_done' not in facts and 'afterlife_community_activated' not in facts
    assert not any(x.get('$type')=='questTriggerCondition' for x in walk(runtime))
    report={
        'status':'RESEARCH_CONFIRMED_COHORT_SELECTION_DEFECT_NO_REPAIR_DEPLOYED',
        'sources':[{'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in source_paths],
        'master_owner':owner,'ordinary_phase':ordinary,'q103_child_edges':mission_edges,'cohorts':cohorts,'scene_routes':scene_routes,'compiled_areas':area_rows,
        'r1_comparison':{'ordinary_patron_entries':len(branches),'ordinary_patron_capacity':sum(e['quantity'] for e in pm['entries'] if e['role']=='patron'),
                         'q103_done_guard_present':False,'vanilla_area_trigger_present':False,
                         'q005_background_handoff_present':False,'selection_matches_completed_q103_branch':False,
                         'appearance_record_overrides':False,'ordinary_release_targets':'private entries only',
                         'warning':'Original q103 active count zero cannot rule out surviving q005 background actors.'},
        'static_validation':{'assertions':'PASS: source edges, branch identity, source quotas/66 spots, two saved q103_done values, reproduced R1 counterexample',
                             'r1_population_policy':'FAIL: wrong cohort for supplied completed-q103 save samples',
                             'runtime_count_or_duplicate_proof':False},
        'limits':['Configured capacities are not visible headcounts.', 'Scene reachability does not mean every actor is simultaneous.',
                  'The 51-item prior registry search includes remote actors with afterlife-named records; it is not a local census.',
                  'Engine density/arbitration and live appearance selection remain unmeasured.',
                  'No new game build, installation, runtime write, save edit or story fact change.']}
    dest=OUT/'population_rules_audit.json'; dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(dest.relative_to(ROOT)), 'status':report['status'],'cohorts':[(c['name'],c['entry_count'],c['configured_entry_capacity_sum'])for c in cohorts], 'static_validation':report['static_validation']},indent=2))


if __name__=='__main__': main()
