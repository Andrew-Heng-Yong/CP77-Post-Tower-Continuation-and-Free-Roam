"""Freeze Zane's narrow owner and service-only scene delta; no game writes."""
import json
from audit_b0_claire import ROOT, COMMON, sha, read
from audit_b0_deferred_vendors import walk, graph_at, graph_edges, compact_node
from report_scene_route import scalars

OUT = ROOT / 'research/b0_story_zane'
OWNER = ROOT / 'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json'
SCENE = ROOT / 'research/b0_vendor_rollout/special_scene_sources/json/base/open_world/vendors/city_center/downtown/cct_dtn_cloth_01/cct_dtn_cloth_01.scene.json'
PREFIX = 'PTFRB0ZAN_'

def main():
    r = read(OWNER)['Data']['RootChunk']
    hs = {str(v['HandleId']): v['Data'] for v in walk(r) if 'HandleId' in v and 'Data' in v}
    graphs = {}
    for route in ['root/node7/node25', 'root/node7/node25/node2']:
        g = graph_at(r, route)
        graphs[route] = {'nodes': [compact_node(n['Data']) for n in g['nodes']], 'edges': graph_edges(g, route, hs)}
    s = read(SCENE)['Data']['RootChunk']
    ns = {n['Data']['nodeId']['id']: n['Data'] for n in s['sceneGraph']['Data']['graph']}
    writers = {i: compact_node(n['questNode']['Data']) for i, n in ns.items()
               if n.get('questNode', {}).get('Data', {}).get('$type') == 'questFactsDBManagerNodeDefinition'}
    assert list(scalars(writers[43], 'factName')) == ['mq030_zane_met']
    assert list(scalars(ns[19], 'factName')) == ['mq030_zane_grateful']
    assert list(scalars(ns[162], 'factName')) == ['mq030_zane_discount']
    report = {'owner': str(OWNER.relative_to(ROOT)), 'owner_sha256': sha(OWNER),
              'scene': str(SCENE.relative_to(ROOT)), 'scene_sha256': sha(SCENE),
              'common_guards': COMMON, 'graphs': graphs, 'scene_writers': writers,
              'scene_change': {'node': 43, 'property': 'questNode.type.factName',
                               'old': 'mq030_zane_met', 'new': PREFIX + 'ServiceMet'},
              'lease': PREFIX + 'QuestOwns', 'release_ack': PREFIX + 'Released',
              'scope': 'One mod-owned Zane owner and scene; no vanilla replacement or mq030 root.'}
    dependency = OUT/'quest_sources/json/base/quest/minor_quests/mq030/mq030.questphase.json'
    dr=read(dependency)['Data']['RootChunk']
    dg=graph_at(dr,'root/node43')
    dn={h['Data']['id']:h['Data']for h in dg['nodes']}
    assert list(scalars(dn[12],'factName'))==['mq030_zane_met']
    assert list(scalars(dn[10],'factName'))==['cct_dtn_cloth_01_default_on']
    assert dn[10]['type']['Data']['value']==0
    assert not any(v.get('factName') in ('cct_dtn_cloth_01_use','cct_dtn_cloth_01_wardrobe')for v in walk(dr))
    report['quest_dependency']={'source':str(dependency.relative_to(ROOT)),'sha256':sha(dependency),
        'meeting_wait':'root/node43/node12','default_service_off':'root/node43/node10',
        'scope':'No use/wardrobe fact references in this extracted mq030 questphase; not a game-wide fact reader proof.'}
    OUT.mkdir(exist_ok=True)
    (OUT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print('AUDITED: Zane owner; service-only greeting write, unchanged earned discount and dialogue')

if __name__ == '__main__': main()
