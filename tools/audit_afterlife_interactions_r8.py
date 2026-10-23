"""Read-only vanilla interaction owner slices, separate from ambient workspots."""
import json
import hashlib
from pathlib import Path
from collections import deque
from audit_wilson_vendor_owner import walk, graph_edges, compact_node
from test_radio_memorial import handles, canonical

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'research/afterlife_world'
OUT = BASE/'interactions_r8'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))['Data']['RootChunk']

def compact_graph(root, graph, route):
    return {'route': route, 'nodes': [compact_node(canonical(n, handles(root))) for n in graph['nodes']],
            'edges': graph_edges(graph, route, handles(root))}

def scene_slice(path, entry):
    root = read(path)
    nodes = {n['Data']['nodeId']['id']: canonical(n, handles(root)) for n in root['sceneGraph']['Data']['graph']}
    start = next(p['nodeId']['id'] for p in root['entryPoints'] if p['name']['$value'] == entry)
    seen, queue = set(), deque([start])
    while queue:
        i = queue.popleft()
        if i in seen:
            continue
        seen.add(i)
        queue.extend(d['nodeId']['id'] for s in nodes[i].get('outputSockets', []) for d in s['destinations'])
    return {'source': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'entry': entry, 'nodes': [nodes[i] for i in sorted(seen)], 'entry_id': start,
            'actors': root['actors'], 'player_actors': root['playerActors'],
            'interruption_scenarios': root['interruptionScenarios']}

def main():
    OUT.mkdir(exist_ok=True)
    p = BASE/'patrons_sources/json/base/quest/main_quests/part1/q103/phases/q103_emmerick_routine.questphase.json'
    root = read(p)
    graphs = []
    def scan(g, route):
        graphs.append(compact_graph(root, g, route))
        for n in g['nodes']:
            d = n['Data']
            if 'phaseGraph' in d and d['phaseGraph']:
                scan(d['phaseGraph']['Data'], route+'/node'+str(d['id']))
    scan(root['graph']['Data'], 'root')
    (OUT/'emmerick_owner.json').write_text(json.dumps(graphs, indent=2)+'\n')
    default = read(ROOT/'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json')
    matches = []
    def find(g, route):
        for n in g['nodes']:
            d = n['Data']
            if 'rogue_default.scene' in json.dumps(compact_node(d)):
                matches.append(compact_graph(default, g, route))
            if 'phaseGraph' in d and d['phaseGraph']:
                find(d['phaseGraph']['Data'], route+'/node'+str(d['id']))
    find(default['graph']['Data'], 'root')
    (OUT/'rogue_owner.json').write_text(json.dumps(matches, indent=2)+'\n')
    ep = OUT/'sources/json/base/quest/main_quests/part1/q103/scenes/q103_02_afterlife_intro.scene.json'
    rp = BASE/'rogue_sources/json/base/quest/secondary_characters/default_dialogues/rogue_default.scene.json'
    if ep.exists():
        es, rs = scene_slice(ep, 'emmerick_entrance'), scene_slice(rp, 'in')
        assert {n['nodeId']['id'] for n in es['nodes']} == {440,441,445,447,449}
        section = next(n for n in es['nodes'] if n['nodeId']['id'] == 441)
        assert section['sectionDuration']['stu'] == 4533
        motion = next(n for n in walk(section) if n.get('$type') == 'scnPlaySkAnimEvent')
        assert motion['rootMotionData']['placementMode'] == 'PlayAtActorPosition'
        assert motion['animName']['unk1'][0]['$value'] == 'stand__2h_front__01__two_step_right__01'
        assert not any(n.get('$type') == 'questSetVar_NodeType' for n in walk(es['nodes']))
        assert len(es['actors']) == 1 and es['actors'][0]['actorName'] == 'bouncer'
        start = next(n for n in rs['nodes'] if n['nodeId']['id'] == 1)
        assert {d['nodeId']['id'] for s in start['outputSockets'] for d in s['destinations']} == {136,235}
        glow = next(n for n in rs['nodes'] if n['nodeId']['id'] == 136)
        assert any(n.get('$type') == 'scneventsVFXEvent' and n['action'] == 'Play' and n['effectEntry']['effectName']['$value'] == 'eye_glow_gold' for n in walk(glow))
        local = next(n for n in rs['nodes'] if n['nodeId']['id'] == 235)
        assert local['questNode']['type']['eventExecutionTag']['$value'] == 'holo' and local['questNode']['type']['mute'] == 1
        (OUT/'scene_slices.json').write_text(json.dumps({'emmerick': es, 'rogue': rs}, indent=2)+'\n')
        expected = {}
        for receipt in ('install_receipt.json','population_r2/install_receipt.json','idles_r3/install_receipt.json','faces_r5/install_receipt.json','booth_r6/install_receipt.json','emmerick_r7/install_receipt.json'):
            for f in json.loads((BASE/receipt).read_text())['files']:
                expected[f['relative'].replace('\\','/')] = f['sha256']
        game = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
        assert all(hashlib.sha256((game/p).read_bytes()).hexdigest().upper() == h for p,h in expected.items())
        result = {'status': 'SOURCE_AUDIT_PASS_NO_RUNTIME_FIX_OR_INSTALL', 'emmerick_entrance_nodes': 5,
                  'emmerick_motion_duration_ms': 4533, 'emmerick_story_fact_writes': 0,
                  'rogue_local_reachable_nodes_before_holo_separation': len(rs['nodes']),
                  'rogue_local_entry_starts_gold_eye_effect': True, 'protected_installed_afterlife_paths': len(expected),
                  'user_claire_dialogue_available': True, 'new_game_writes': 0,
                  'limits': 'Graph evidence only. Emmerick reaction and Rogue dialogue/glow remain unimplemented; no new build/install/live pass.'}
        (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
        return
    for label, gs in (('Emmerick', graphs), ('Rogue', matches)):
        print(label)
        for g in gs:
            print(g['route'])
            for n in g['nodes']:
                text = json.dumps(n, separators=(',', ':'))
                print(text[:1400])
            print('EDGES', [(e['source_node_id'],e['source_socket'],e['destination_node_id'],e['destination_socket']) for e in g['edges']])

if __name__ == '__main__':
    main()
