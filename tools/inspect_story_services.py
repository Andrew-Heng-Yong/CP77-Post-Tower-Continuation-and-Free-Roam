"""Bounded read-only scene/owner inspection for the remaining story services."""
import sys, json
from pathlib import Path
from audit_b0_claire import ROOT, read
from audit_b0_deferred_vendors import walk, graph_at, compact_node, graph_edges
from report_scene_route import scalars

BASE=ROOT/'research/b0_vendor_rollout'
def scene_path(name):
    hits=list(BASE.glob('**/json/**/'+name+'.scene.json'))
    assert len(hits)==1,(name,hits)
    return hits[0]

def nodes(root):
    return {h['Data']['nodeId']['id']:h['Data'] for h in root['sceneGraph']['Data']['graph']}

def reach(ns, starts):
    todo=list(starts); seen=set()
    while todo:
        i=todo.pop()
        if i in seen: continue
        seen.add(i)
        todo.extend(d['nodeId']['id'] for o in ns[i].get('outputSockets',[]) for d in o.get('destinations',[]))
    return seen

def main():
    name=sys.argv[1];r=read(scene_path(name))['Data']['RootChunk'];ns=nodes(r)
    if len(sys.argv)>2:
        for token in sys.argv[2:]:
            if token=='actors': print(json.dumps(r.get('actors',[]),indent=2))
            else:
                n=ns[int(token)]; print(json.dumps(n,indent=2))
        return
    print('ENTRIES',r['entryPoints'])
    for e in r['entryPoints']:
        seen=reach(ns,[e['nodeId']['id']]);print('ROUTE',e['name']['$value'],len(seen))
        for i in sorted(seen):
            n=ns[i];q=n.get('questNode',{}).get('Data')
            if q and any(k in q['$type'] for k in ['FactsDB','Journal','Item','Reward','Entity','Spawn','SceneManager']):
                print(i,json.dumps(compact_node(q)))
            if list(scalars(n,'vendorId')):print('VENDOR',i,list(scalars(n,'vendorId')))
    print('ACTORS',[(v.get('actorName'),v.get('isAlwaysSpawned'))for v in r.get('actors',[])])

if __name__=='__main__':main()
