"""Read-only census of every W3 manifest owner and omitted native graph payload."""
import collections, hashlib, json
from pathlib import Path

OUT=Path(__file__).resolve().parent
WS=OUT.parents[2]
MANIFEST=WS/'prealpha/world_workspots_w2/manifest_03.json'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x,p='$'):
    yield p,x
    if isinstance(x,dict):
        for k,v in x.items(): yield from walk(v,p+'.'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from walk(v,p+f'[{i}]')
def handles(d): return {v['HandleId']:v['Data'] for _,v in walk(d) if isinstance(v,dict) and 'HandleId' in v and 'Data' in v}
def resolve(v,hs):
    if v is None: return None
    if 'HandleRefId' in v: return hs[v['HandleRefId']]
    if 'HandleId' in v and 'Data' in v: return v['Data']
    return v
def norm(v,hs):
    if isinstance(v,dict):
        if 'HandleRefId' in v or ('HandleId' in v and 'Data' in v): return norm(resolve(v,hs),hs)
        return {k:norm(x,hs) for k,x in v.items() if k not in ('sockets','HandleId','HandleRefId')}
    if isinstance(v,list): return [norm(x,hs) for x in v]
    return v
def getnode(graph,i,hs): return next(resolve(x,hs) for x in graph['nodes'] if resolve(x,hs).get('id')==i)
def lookup(root,path,hs):
    graph=resolve(root['graph'],hs)
    for i in path.split('/')[1:]:
        node=getnode(graph,int(i),hs)
        if node.get('phaseGraph'): graph=resolve(node['phaseGraph'],hs)
    return node
def refs(n):
    return [{'path':p,'type':v['$type'],'value':v['$value']} for p,v in walk(n) if isinstance(v,dict) and v.get('$type') in ('NodeRef','ResourcePath','TweakDBID') and v.get('$value') not in ('0','',None)]
def enums(n):
    return [{'path':p,'value':v} for p,v in walk(n) if p.rsplit('.',1)[-1] in ('action','function','type','operation','factName') and isinstance(v,(str,int))]
def graph_edges(graph,hs):
    owners={}
    def key(h): return h.get('HandleId',h.get('HandleRefId'))
    for h in graph['nodes']:
        n=resolve(h,hs)
        for s in n.get('sockets',[]): owners[key(s)]=(n['id'],resolve(s,hs).get('name',{}).get('$value'))
    edges=set()
    for h in graph['nodes']:
        n=resolve(h,hs)
        for s in n.get('sockets',[]):
            for c in resolve(s,hs).get('connections',[]):
                c=resolve(c,hs); src=owners.get(key(c['source'])); dst=owners.get(key(c['destination']))
                assert src is not None and dst is not None,(src,dst,n['id'])
                edges.add((src[0],src[1],dst[0],dst[1]))
    return sorted(edges)
def phases(n,path,hs):
    if not n.get('phaseGraph'):
        if n.get('$type')=='questPhaseNodeDefinition':
            nn=norm(n,hs)
            return [{'path':path,'node_type':n['$type'],'node_count':0,'edges':[],'direct_node_types':{},'payload_types':dict(collections.Counter(v['$type'] for _,v in walk(nn) if isinstance(v,dict) and '$type' in v)),'prefabs':nn.get('phaseInstancePrefabs',[]),'references':refs(nn),'operations':enums(nn),'payload':nn}]
        return []
    graph=resolve(n['phaseGraph'],hs); nn=norm(n,hs)
    direct=[resolve(h,hs) for h in graph['nodes']]
    result=[{'path':path,'node_type':n['$type'],'node_count':len(direct),
      'edges':graph_edges(graph,hs),'direct_node_types':dict(collections.Counter(x['$type'] for x in direct)),
      'payload_types':dict(collections.Counter(v['$type'] for _,v in walk(nn) if isinstance(v,dict) and '$type' in v)),
      'prefabs':nn.get('phaseInstancePrefabs',[]),'references':refs(nn),
      'operations':enums(nn),'payload':nn}]
    for x in direct: result.extend(phases(x,path+'/'+str(x['id']),hs))
    return result

manifest=read(MANIFEST); assert len(manifest['groups'])==237
cache={}; rows=[]
for group in manifest['groups']:
    source=WS/group['source']; binary=WS/group['native_binary']
    if str(source) not in cache:
        data=read(source); hs=handles(data)
        actual=sha(binary); assert actual==group['native_binary_sha256'],(binary,actual)
        cache[str(source)]=(data,hs,actual)
    data,hs,binarysha=cache[str(source)]
    owner=lookup(data['Data']['RootChunk'],group['node_path'],hs)
    pp=phases(owner,group['node_path'],hs)
    assert pp,(group['id'],group['node_path'])
    allnodes=[v for _,v in walk(norm(owner,hs)) if isinstance(v,dict) and str(v.get('$type','')).endswith('NodeDefinition')]
    rows.append({'id':group['id'],'prefix':group['prefix'],'source':str(source),'native_binary':str(binary),'native_binary_sha256':binarysha,
       'node_path':group['node_path'],'prefab':group['prefab'],'community_refs':group['community_refs'],
       'spawner_hashes':group['spawner_hashes'],'phase_count':len(pp),'descendant_phase_count':len(pp)-1,
       'all_node_types':dict(collections.Counter(x['$type'] for x in allnodes)), 'phases':pp})

out={'status':'EXHAUSTIVE_NATIVE_GRAPH_INVENTORY_NOT_ALLOWLIST','owner_count':len(rows),'source_count':len(cache),
    'manifest':str(MANIFEST),'manifest_sha256':sha(MANIFEST),'sources':[{'path':p,'json_sha256':sha(Path(p)),'binary_sha256':s} for p,(d,h,s) in cache.items()],
    'descendant_phase_distribution':dict(sorted(collections.Counter(r['descendant_phase_count'] for r in rows).items())),
    'all_direct_types':dict(collections.Counter(n for r in rows for p in r['phases'] for n,num in p['direct_node_types'].items() for _ in range(num))),
    'owners':rows,'game_writes':0,'save_writes':0}
(OUT/'census_raw_01.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
summary=[{'id':r['id'],'path':r['node_path'],'nested':[{'path':p['path'],'nodes':p['node_count'],'types':p['direct_node_types']} for p in r['phases'][1:]],'roottypes':r['phases'][0]['direct_node_types']} for r in rows]
(OUT/'census_summary_01.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('owners','sources','all_direct_types')},indent=2))
print(json.dumps(out['all_direct_types'],indent=2))
