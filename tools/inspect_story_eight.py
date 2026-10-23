"""Read-only bounded views of the eight story-linked service candidates."""
import json,sys
from pathlib import Path
from audit_b0_claire import ROOT,read
from audit_b0_deferred_vendors import walk,graph_at,graph_edges,compact_node
from inspect_story_services import nodes,reach
from report_scene_route import scalars

def find(name):
    candidates=list((ROOT/'research/b0_story_eight').glob('**/json/**/'+name+'.json'))
    candidates+=list((ROOT/'research/b0_story_services/quest_sources/json').glob('**/'+name+'.json'))
    if not candidates:candidates=list((ROOT/'research/b0_vendor_rollout').glob('**/json/**/'+name+'.json'))
    if not candidates:candidates=list((ROOT/'research/q307_extracted/json').glob('**/'+name+'.json'))
    if name=='default_dialogs.questphase': candidates=[ROOT/'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json']
    assert len(candidates)==1,(name,candidates)
    return candidates[0]

def main():
    p=find(sys.argv[1]);r=read(p)['Data']['RootChunk'];print('SOURCE',p.relative_to(ROOT))
    if '.scene' in p.name:
        ns=nodes(r)
        if len(sys.argv)>2 and sys.argv[2].startswith('compact:'):
            starts=list(map(int,sys.argv[2][8:].split(',')))
            for i in sorted(reach(ns,starts)):
                n=ns[i];out=[[d['nodeId']['id'] for d in o.get('destinations',[])]for o in n.get('outputSockets',[])]
                q=n.get('questNode',{}).get('Data',{})
                brief={k:list(scalars(q,k))for k in ['factName','vendorId','realPath','action','sceneFile','reference','objectRef','performerId'] if list(scalars(q,k))}
                print(i,n['$type'],out,q.get('$type',''),json.dumps(brief),[(o.get('caption',{}).get('$value'),list(scalars(o,'factName')))for o in n.get('options',[])])
            return
        if len(sys.argv)==2:
            print('ENTRIES',r['entryPoints'])
            for e in r['entryPoints']:
                rr=reach(ns,[e['nodeId']['id']]);print('REACH',e['name'],len(rr))
                for i in sorted(rr):
                    q=ns[i].get('questNode',{}).get('Data',{})
                    if any(t in q.get('$type','') for t in ['FactsDB','Journal','Reward','Item']):print(i,json.dumps(compact_node(q)))
        for arg in sys.argv[2:]:
            if arg=='actors':print(json.dumps(r['actors'],indent=2));continue
            for i in map(int,arg.split(',')):
                n=ns[i]; print(i,json.dumps(n,indent=2))
    else:
        hs={str(v['HandleId']):v['Data'] for v in walk(r) if 'HandleId' in v and 'Data'in v}
        if len(sys.argv)>2 and sys.argv[2].startswith('find:'):
            term=sys.argv[2][5:]
            def rec(g,route):
                for h in g['nodes']:
                    n=h['Data']
                    if term in str(compact_node(n)):
                        print(route,n['id'],json.dumps(compact_node(n)))
                        ee=graph_edges(g,route,hs)
                        print('EDGES',json.dumps([e for e in ee if n['id'] in [e['source_node_id'],e['destination_node_id']]]))
                    if n.get('phaseGraph'):rec(n['phaseGraph']['Data'],route+'/node'+str(n['id']))
            rec(r['graph']['Data'],'root');return
        route=sys.argv[2] if len(sys.argv)>2 else 'root';g=graph_at(r,route)
        only=set(map(int,sys.argv[3].split(',')))if len(sys.argv)>3 else None
        for h in g['nodes']:
            n=h['Data']
            if only is None or n['id'] in only:print(n['id'],json.dumps(compact_node(n)))
        print('EDGES',json.dumps(graph_edges(g,route,hs)))

if __name__=='__main__':main()
