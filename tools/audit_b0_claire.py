"""Freeze the one Claire default-service owner, not the race/default root."""
import json, hashlib
from audit_b0_deferred_vendors import ROOT, walk, graph_edges, compact_node, graph_at
from report_scene_route import scalars

OUT=ROOT/'research/b0_claire'
OWNER=ROOT/'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json'
SCENE=ROOT/'research/b0_vendor_rollout/special_scene_sources/json/base/quest/tertiary_characters/default_dialogues/claire_default.scene.json'
COMMON={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_active':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q305_johnny_scene_active':0,'q115_point_of_no_return':0,'q000_done':1}
PREFIX='PTFRB0CLA_'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    r=read(OWNER)['Data']['RootChunk'];hs={str(v['HandleId']):v['Data'] for v in walk(r) if 'HandleId' in v and 'Data' in v}
    graphs={}
    for route in ['root/node4','root/node4/node19','root/node4/node19/node26','root/node4/node19/node26/node7']:
        g=graph_at(r,route)
        graphs[route]={'nodes':[compact_node(n['Data']) for n in g['nodes'] if route!='root/node4' or n['Data']['id'] in (19,73,74)],'edges':graph_edges(g,route,hs)}
    s=read(SCENE)['Data']['RootChunk'];nodes={n['Data']['nodeId']['id']:n['Data'] for n in s['sceneGraph']['Data']['graph']}
    edges={i:[v['nodeId']['id'] for o in n.get('outputSockets',[]) for v in o.get('destinations',[])] for i,n in nodes.items()}
    routes={}
    for entry in s['entryPoints']:
        todo=[entry['nodeId']['id']];seen=set()
        while todo:
            i=todo.pop()
            if i in seen:continue
            seen.add(i);todo.extend(edges.get(i,[]))
        routes[entry['name']['$value']]={'reachable':sorted(seen),'vendors':[i for i in seen if list(scalars(nodes[i],'vendorId'))],
          'writers':{i:compact_node(nodes[i]['questNode']['Data']) for i in sorted(seen) if nodes[i].get('questNode',{}).get('Data',{}).get('$type')=='questFactsDBManagerNodeDefinition'}}
    scene_nodes=[]
    for i,n in nodes.items():
        q=n.get('questNode',{}).get('Data')
        scene_nodes.append({'id':i,'type':n['$type'],'quest':compact_node(q) if q else None,'targets':edges[i],
                           'choice_facts':list(scalars(n.get('options',[]),'factName'))})
    report={'owner':str(OWNER.relative_to(ROOT)),'owner_sha256':sha(OWNER),'scene':str(SCENE.relative_to(ROOT)),
      'scene_sha256':sha(SCENE),'graphs':graphs,'scene_routes':routes,'scene_nodes':scene_nodes,'common_guards':COMMON,
      'scope':'Only prefab-owning root/node4/node19, with its children; no enclosing roots or sq024 owner.'}
    OUT.mkdir(exist_ok=True)
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(routes,indent=2))
if __name__=='__main__':main()
