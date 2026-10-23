"""Bounded vanilla Afterlife community/owner extraction; no game writes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/afterlife_world'
OUT.mkdir(parents=True, exist_ok=True)

def val(obj):
    return obj.get('$value', obj) if isinstance(obj, dict) else obj

def walk(obj, path=''):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk(v, path + '/' + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, path + '/' + str(i))

def contains(obj, words):
    return any(any(w in str(v).lower() for w in words) for _, o in walk(obj) for v in o.values() if isinstance(v, str))

phase_path = ROOT / 'research/phase2b_p4/vendor_owner/json/base/open_world/community/watson/little_china/wat_lch_phase.questphase.json'
phase = json.loads(phase_path.read_text(encoding='utf-8-sig'))
graphs = []
for path, obj in walk(phase):
    if obj.get('$type') == 'questGraphDefinition':
        nodes = [v.get('Data', {}) for v in obj.get('nodes', [])]
        if any(contains({k:v for k,v in n.items() if k != 'phaseGraph'}, ['afterlife', 'dancer']) for n in nodes):
            graphs.append({'path':path, 'nodes':nodes})
(OUT/'hologram_vanilla_phase_graphs.json').write_text(json.dumps(graphs, indent=2), encoding='utf-8')
print('matching graphs', [(g['path'], len(g['nodes'])) for g in graphs])
world_path = ROOT / 'research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/always_loaded_1.streamingsector.json'
world = json.loads(world_path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
print('world keys', list(world))
selected=[]
for i, handle in enumerate(world['nodes']):
    node=handle.get('Data', {})
    if node.get('$type') == 'worldCommunityRegistryNode':
        for ci, item in enumerate(node.get('communitiesData', [])):
            if contains(item, ['afterlife_ws_dancer']):
                selected.append({'node':i,'community_index':ci,'community':item})
    elif contains(node, ['afterlife_tube_dancers']):
        selected.append({'node':i, 'data':node})
(OUT/'hologram_vanilla_registry.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
print('selected', [(s['node'],s.get('community_index')) for s in selected])
print('nodeData keys', list(world['nodeData']))
placements=[]
ref_data=json.loads((OUT/'hologram_record_and_refs.json').read_text())
ref_hashes={r['hash']:r['ref'] for r in ref_data['refs']}
for path, obj in walk(world['nodeData']):
    if 'QuestPrefabRefHash' in obj and (str(val(obj['QuestPrefabRefHash'])) in ref_hashes or contains(obj, ['afterlife_ws_dancer','afterlife_tube_dancers'])):
        placements.append({'path':path, 'datum':obj, 'node':world['nodes'][int(obj['NodeIndex'])]})
(OUT/'hologram_vanilla_placements.json').write_text(json.dumps(placements,indent=2),encoding='utf-8')
print('placements', len(placements))
persist=[o for p,o in walk(world['nodes'][3256]['Data'].get('workspotsPersistentData', [])) if o.get('globalNodeId',{}).get('hash') in ref_hashes]
(OUT/'hologram_vanilla_spot_persistent.json').write_text(json.dumps(persist,indent=2),encoding='utf-8')
print('persistent',len(persist))
block_path=ROOT/'research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/blocks/all.streamingblock.json'
block=json.loads(block_path.read_text(encoding='utf-8-sig'))
descriptors=[{'path':p,'descriptor':o} for p,o in walk(block) if o.get('$type')=='worldStreamingSectorDescriptor' and contains(o,['afterlife'])]
(OUT/'hologram_afterlife_descriptors.json').write_text(json.dumps(descriptors,indent=2),encoding='utf-8')
print('descriptors',len(descriptors))
summary=[]
for g in graphs:
    summary.append({'path':g['path'],'nodes':[{k:v for k,v in n.items() if k not in ['sockets','phaseGraph']} for n in g['nodes']]})
(OUT/'hologram_phase_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
physical=[]
for rel in [
    'research/afterlife_world/hologram_sources/json/base/worlds/03_night_city/_compiled/default/exterior_-12_7_0_1.streamingsector.json',
    'research/misty_viktor_world/r7_showworld_sources/json/base/worlds/03_night_city/_compiled/default/exterior_-12_8_0_1.streamingsector.json',
]:
    wr=json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))['Data']['RootChunk']
    for di,datum in enumerate(wr['nodeData']['Data']):
        ref=val(datum['QuestPrefabRefHash'])
        if isinstance(ref,str) and 'afterlife_ws_dancer_' in ref:
            ni=datum['NodeIndex'];node=wr['nodes'][ni]['Data']
            variant_ranges=[]
            for ri,(lo,hi) in enumerate(zip(wr['variantIndices'],wr['variantIndices'][1:])):
                if ni in wr['variantNodes'][lo:hi]:variant_ranges.append(ri)
            physical.append({'source_json':rel,'datum_index':di,'node_index':ni,'ref':ref,'category':wr['category'],'level':wr['level'],'variant_ranges':variant_ranges,'datum':datum,'node':node})
assert len(physical)==10, len(physical)
assert all(x['node']['$type']=='worldAISpotNode' and not x['variant_ranges'] for x in physical)
(OUT/'hologram_physical_spots.json').write_text(json.dumps(physical,indent=2),encoding='utf-8')
print('physical spots',[(x['node_index'],x['ref'].rsplit('/',1)[-1],x['variant_ranges']) for x in physical])
