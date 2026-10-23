"""Flatten native Only Pain graphs for source audit; no game or save writes."""
import json
from catalog_gig_rollout_r2 import ROOT, read, handles, deref, value, walk, sha

SOURCE=ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq005'
OUT=ROOT/'research/side_job_pilot_s1'

def clean(v):
    if isinstance(v,dict):
        if '$value' in v:return v['$value']
        return {k:clean(x) for k,x in v.items() if k not in ('sockets','phaseGraph','HandleId','HandleRefId')}
    if isinstance(v,list):return [clean(x) for x in v]
    return v

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result=[]
    for p in SOURCE.rglob('*.json'):
        obj=read(p);h=handles(obj)
        graphs=[]
        def visit(g,path):
            nodes=[deref(n,h) for n in g['nodes']];owners={}
            for n in nodes:
                for s in n.get('sockets',[]):owners[s.get('HandleId',s.get('HandleRefId'))]=(n['id'],value(deref(s,h).get('name')))
            edges=[]
            for n in nodes:
                for sw in n.get('sockets',[]):
                    s=deref(sw,h)
                    for cw in s.get('connections',[]):
                        c=deref(cw,h);a=c['source'].get('HandleRefId',c['source'].get('HandleId'));b=c['destination'].get('HandleRefId',c['destination'].get('HandleId'))
                        if a in owners and b in owners:
                            edge=[*owners[a],*owners[b]]
                            if edge not in edges:edges.append(edge)
            graphs.append({'path':path,'nodes':[clean(n) for n in nodes],'edges':edges})
            for n in nodes:
                pg=deref(n.get('phaseGraph',{}),h)
                if 'nodes' in pg:visit(pg,path+'/'+str(n['id']))
        visit(deref(obj['Data']['RootChunk']['graph'],h),'root')
        result.append({'source':str(p.relative_to(ROOT)),'sha256':sha(p),'graphs':graphs,
                       'facts':sorted({v['factName'] for v in walk(obj) if 'factName' in v}),
                       'scene_paths':sorted({value(v['sceneFile']) for v in walk(obj) if 'sceneFile' in v})})
    (OUT/'native_graph_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for r in result:
        print(r['source'],r['facts'],r['scene_paths'])
        for g in r['graphs']:
            print(g['path'],len(g['nodes']),'nodes',g['edges'])
            for n in g['nodes']:
                print(n['id'],json.dumps(n,separators=(',',':'))[:2300])

if __name__=='__main__':main()
