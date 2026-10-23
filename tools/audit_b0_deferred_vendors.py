"""Bounded vanilla owner slices for Christine and Japantown netrunner 02."""
import json
import hashlib
from pathlib import Path
from audit_wilson_vendor_owner import walk, graph_edges, compact_node
from plan_b0_ordinary_vendor_batch import graph_at

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'research/b0_deferred_ordinary'
SOURCES={
 'christine': (ROOT/'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json',
               ['root','root/node7','root/node7/node35','root/node7/node35/node8','root/node7/node35/node8/node9']),
 'netrunner02': (ROOT/'research/b0_vendor_rollout/regional_sources/json/base/open_world/vendors/westbrook/japantown/japantown_vendors.questphase.json',
                 ['root','root/node19','root/node19/node15'])}

def main():
    OUT.mkdir(exist_ok=True)
    result={}
    for key,(path,routes) in SOURCES.items():
        root=json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        handles={str(v['HandleId']):v['Data'] for v in walk(root) if 'HandleId' in v and 'Data' in v}
        rec={'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper(),
             'phasePrefabs':root.get('phasePrefabs',[]),'graphs':{}}
        for route in routes:
            graph=graph_at(root,route)
            rec['graphs'][route]={'nodes':[compact_node(h['Data']) for h in graph['nodes']],
                                 'edges':graph_edges(graph,route,handles)}
        result[key]=rec
    (OUT/'owner_slices.json').write_text(json.dumps(result,indent=2)+'\n')
    rescue=OUT/'rescue_sources/json/base/open_world/street_stories/westbrook/japantown/sts_wbr_jpn_05/phases/sts_wbr_jpn_05_openworld.questphase.json'
    if rescue.exists():
        r=json.loads(rescue.read_text())['Data']['RootChunk']
        hs={str(v['HandleId']):v['Data'] for v in walk(r) if 'HandleId' in v and 'Data' in v}
        def scan(g,route):
            nodes={n['Data']['id']:n['Data'] for n in g['nodes']}
            edges=graph_edges(g,route,hs)
            targets={i for i,n in nodes.items() if any(v.get('factName') in ('jpn_05_finished','jpn_05_nam_endings') for v in walk(compact_node(n)))}
            for _ in range(3):targets|={e['source_node_id'] for e in edges if e['destination_node_id'] in targets}
            if targets:
                yield {'route':route,'nodes':[compact_node(nodes[i]) for i in sorted(targets)],'edges':[e for e in edges if e['destination_node_id'] in targets]}
            for i,n in nodes.items():
                if 'phaseGraph' in n and 'Data' in n['phaseGraph']:
                    yield from scan(n['phaseGraph']['Data'],f'{route}/node{i}')
        (OUT/'rescue_completion.json').write_text(json.dumps(list(scan(r['graph']['Data'],'root')),indent=2)+'\n')
    for key,rec in result.items():
        print('\nOWNER',key)
        for route,g in rec['graphs'].items():
            print(route)
            for n in g['nodes']:
                print(json.dumps(n,separators=(',',':')))
            print('EDGES',[(e['source_node_id'],e['source_socket'],e['destination_node_id'],e['destination_socket']) for e in g['edges']])

if __name__=='__main__':main()
