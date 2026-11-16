"""Lossless parameter indexing with explicit quest and scene socket graphs.

This is structural evidence, not a simulation or a saved-owner decoder.
"""
import gzip
import json
from collections import defaultdict, deque
from pathlib import Path

def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

def value(x):
    if isinstance(x, dict): return x.get('$value', x.get('id', x))
    return x

def load_export(path):
    p = Path(path)
    data = p.read_bytes()
    return json.loads(gzip.decompress(data) if p.suffix == '.gz' else data)

def normalize(obj):
    handles = {}
    for x in walk(obj):
        if 'HandleId' in x and 'Data' in x:
            if x['HandleId'] in handles and handles[x['HandleId']] != x['Data']:
                raise ValueError('Conflicting handle definition')
            handles[x['HandleId']] = x['Data']
    def deref(x):
        if not isinstance(x, dict): return x
        if 'Data' in x and 'HandleId' in x: return x['Data']
        if 'HandleRefId' in x:
            if str(x['HandleRefId']) in ('-1','0') and x['HandleRefId'] not in handles: return None
            if x['HandleRefId'] not in handles: raise ValueError('Unbound handle '+str(x))
            return handles[x['HandleRefId']]
        return x
    def clean(x, seen=frozenset()):
        if isinstance(x, dict):
            h = x.get('HandleId', x.get('HandleRefId'))
            if h is not None:
                if h in seen: return {'cycle_to_handle':h}
                return clean(deref(x), seen | {h})
            return {k:clean(v,seen) for k,v in x.items()
                    if k not in ('sockets','connections','phaseGraph','outputSockets','sceneGraph','graph')}
        if isinstance(x,list): return [clean(v,seen) for v in x]
        return x
    root = obj['Data']['RootChunk']
    graphs = []
    def quest_graph(g,path):
        g=deref(g)
        if not g: return
        ns=[deref(n) for n in g['nodes']]
        ids=[n['id'] for n in ns]
        if len(ids)!=len(set(ids)): raise ValueError('Duplicate node IDs at '+path)
        sockets={}
        for n in ns:
            for s in n.get('sockets',[]):
                ds=deref(s)
                key=s.get('HandleId',s.get('HandleRefId'))
                endpoint=(n['id'],value(ds['name']),ds['type'])
                if key in sockets and sockets[key]!=endpoint: raise ValueError('Socket has two owners')
                sockets[key]=endpoint
        edges=[];connections=set();unresolved=[]
        for n in ns:
            for s in n.get('sockets',[]):
                for c in deref(s).get('connections',[]):
                    key=c.get('HandleId',c.get('HandleRefId'))
                    if key in connections:continue
                    connections.add(key)
                    c=deref(c)
                    if any(not isinstance(c.get(k),dict) for k in ('source','destination')):
                        unresolved.append({'connection_handle':key,'source':c.get('source'),'destination':c.get('destination')})
                        continue
                    ends=[]
                    for k in ['source','destination']:
                        h=c[k].get('HandleId',c[k].get('HandleRefId'))
                        if h not in sockets: raise ValueError('Unbound socket at '+path)
                        ends.append(sockets[h])
                    edges.append((*ends[0],*ends[1]))
        entry=[n['id'] for n in ns if n['$type'] in ('questInputNodeDefinition','questStartNodeDefinition')]
        reach=reachable(entry,[(e[0],e[3]) for e in edges if e[2]=='Output' and e[5]=='Input'])
        nodes=[]
        for n in ns:
            sockets_n=[{'name':value(deref(s)['name']),'type':deref(s)['type']} for s in n.get('sockets',[])]
            nodes.append({'id':n['id'],'type':n['$type'],'parameters':clean(n),
                          'sockets':sockets_n,'from_any_input':n['id'] in reach})
        graphs.append({'path':path,'kind':'quest','nodes':nodes,'edges':sorted(edges), 'inputs':entry,
                       'unresolved_connections':unresolved})
        for n in ns:
            if isinstance(deref(n.get('phaseGraph')),dict): quest_graph(n['phaseGraph'],path+'/'+str(n['id']))
    if 'graph' in root: quest_graph(root['graph'],'root')
    if 'sceneGraph' in root:
        g=deref(root['sceneGraph'])
        if g:
            ns=[deref(n) for n in g['graph']]
            ids=[value(n['nodeId']) for n in ns]
            if len(ids)!=len(set(ids)): raise ValueError('Duplicate scene nodes')
            edges=[]; unresolved=[]
            for n in ns:
                qn=deref(n.get('questNode'))
                if isinstance(qn,dict) and isinstance(deref(qn.get('phaseGraph')),dict):
                    quest_graph(qn['phaseGraph'],'scene/'+str(value(n['nodeId'])))
                for s in n.get('outputSockets',[]):
                    for d in s.get('destinations',[]):
                        edge=(value(n['nodeId']),json.dumps(s['stamp'],sort_keys=True),'Output',
                              value(d['nodeId']),json.dumps(d['isockStamp'],sort_keys=True),'Input')
                        edges.append(edge)
                        if edge[3] not in ids: unresolved.append(edge)
            entries=[value(e['nodeId']) for e in root.get('entryPoints',[])]
            reach=reachable(entries,[(e[0],e[3]) for e in edges])
            graphs.append({'path':'scene','kind':'scene','inputs':entries,'edges':sorted(edges),
                'unresolved_scene_destinations':unresolved,
                'nodes':[{'id':value(n['nodeId']),'type':n['$type'],'parameters':clean(n),
                          'sockets':[],'from_any_input':value(n['nodeId']) in reach} for n in ns]})
    embedded=[]
    for e in obj.get('Data',{}).get('EmbeddedFiles',[]):
        content=e.get('Content',{});name=str(value(e.get('FileName','')))
        if 'graph' in content:quest_graph(content['graph'],'embedded/'+name+'/root')
        embedded.append({'depot':name,'parameters':clean(content),
                         'scene_graph_unindexed':'sceneGraph' in content})
    support=clean(root);support['embedded_resources']=embedded
    return {'root_type':root['$type'],'graphs':graphs,'support':support}

def reachable(seeds,edges):
    adj=defaultdict(set)
    for a,b in edges: adj[a].add(b)
    seen=set(seeds); todo=deque(seeds)
    while todo:
        for n in adj[todo.popleft()]-seen:
            seen.add(n);todo.append(n)
    return seen

def journal_refs(params):
    return sorted({(x['realPath'],str(value(x.get('className','')))) for x in walk(params)
                   if x.get('$type')=='gameJournalPath' and x.get('realPath')})

def resource_refs(params):
    return sorted({str(value(x['DepotPath'])) for x in walk(params)
                   if 'DepotPath' in x and str(value(x['DepotPath'])) not in ('0','None','')})

def effects(params):
    result=[]
    for x in walk(params):
        t=x.get('$type','')
        # Retain entire typed records. An indexed award is not a proven one-time receipt.
        if any(s in t for s in ('GiveReward','ItemManager','Inventory','Transaction','Achievement',
                                'SetVar_','AddRemoveItem','FactDB','SetFact')):
            result.append(x)
    return result
