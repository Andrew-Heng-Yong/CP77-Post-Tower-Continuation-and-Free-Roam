"""Exact vanilla crowd-null loading-condition precedent; no game mutation."""
import json
import hashlib
from pathlib import Path

from test_radio_memorial import handles, canonical
from test_streetkid_scene_load_s3 import quest_edges

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/misty_viktor_world'
REF = '#q001_crowd_null_area_viktor'
FULL = '$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_openworld/' + REF


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']


def find_graphs(value, ancestry=()):
    if isinstance(value, list):
        for child in value:
            yield from find_graphs(child, ancestry)
    elif isinstance(value, dict):
        if value.get('$type') == 'questPhaseNodeDefinition':
            ancestry += (value.get('id'),)
        if value.get('$type') == 'questGraphDefinition':
            yield ancestry, value
        for child in value.values():
            yield from find_graphs(child, ancestry)


def main():
    path = ROOT / 'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json'
    source = load(path)
    table = handles(source)
    matches = []
    for ancestry, graph in find_graphs(source):
        ns = [table[str(o.get('HandleId', o.get('HandleRefId')))] for o in graph['nodes']]
        wait = [n for n in ns if n.get('$type') == 'questPauseConditionNodeDefinition' and
                'condition' in n and canonical(n['condition'], table).get('$type') == 'questNodeLoadingCondition' and
                canonical(n['condition'], table)['objectRef']['$value'] == REF]
        if not wait:
            continue
        assert len(wait) == 1
        action = [n for n in ns if n.get('$type') == 'questCrowdManagerNodeDefinition' and
                  canonical(n['type'], table).get('$type') == 'questCrowdManagerNodeType_EnableNullArea' and
                  canonical(n['type'], table)['areaReference']['$value'] == REF]
        assert len(action) == 1
        graph_handle = next(key for key, value in table.items() if value is graph)
        edges = quest_edges({'source': source, 'graph': {'HandleRefId': graph_handle}})[0]
        assert (wait[0]['id'], 'Out', action[0]['id'], 'In') in edges
        matches.append({'phase_node_ancestry': list(ancestry),
                        'wait_node': canonical(wait[0], table),
                        'enable_node': canonical(action[0], table),
                        'edge': [wait[0]['id'], 'Out', action[0]['id'], 'In']})
    assert len(matches) == 1
    sector_path = ROOT / 'research/phase2b_p4/variant_sectors/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/exterior_-7_4_0_2.streamingsector.json'
    sector = load(sector_path)
    placements = []
    for i, datum in enumerate(sector['nodeData']['Data']):
        if datum['QuestPrefabRefHash']['$value'] == FULL:
            node = sector['nodes'][datum['NodeIndex']]['Data']
            assert node['$type'] == 'worldCrowdNullAreaNode'
            placements.append({'data_index': i, 'node_index': datum['NodeIndex'], 'placement': datum, 'node': node})
    assert len(placements) == 1
    report = {
        'status': 'SOURCE_CONFIRMED_NODE_LOADING_CONDITION_PRECEDES_SAME_TYPE_CROWD_ENABLE',
        'source': str(path.relative_to(ROOT)), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        'source_graph': matches[0], 'full_ref': FULL,
        'sector': str(sector_path.relative_to(ROOT)), 'sector_sha256': hashlib.sha256(sector_path.read_bytes()).hexdigest().upper(),
        'target': placements[0],
        'conclusion': 'Vanilla explicitly uses questNodeLoadingCondition to wait for a worldCrowdNullAreaNode before invoking EnableNullArea on it. Generic nonentity applicability is directly supported.',
        'limits': 'This source precedent alone does not establish inverted-condition callback timing or repeat-stream notification delivery. Those need native implementation tracing. No live R6 pass claimed.',
    }
    (OUT / 'bradbury_crowd_readiness_precedent.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'ancestry': matches[0]['phase_node_ancestry'], 'edge': matches[0]['edge'], 'node_type': placements[0]['node']['$type'], 'node_index': placements[0]['node_index'], 'data_index': placements[0]['data_index']}, indent=2))


if __name__ == '__main__':
    main()
