"""Classify the remaining58 native owners by concrete omitted payload family."""
import collections,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;WS=OUT.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def load(source):
    doc=read(WS/source)
    hs={v['HandleId']:v['Data'] for v in walk(doc) if 'HandleId' in v and 'Data' in v}
    def res(v):return v.get('Data',hs.get(v.get('HandleRefId'),v))
    def norm(v):
        if isinstance(v,dict):
            if 'HandleId' in v or 'HandleRefId' in v:return norm(res(v))
            return {k:norm(x) for k,x in v.items() if k not in ('sockets','phaseGraph')}
        if isinstance(v,list):return [norm(x) for x in v]
        return v
    idx={}
    def visit(g,path):
        for h in g['nodes']:
            n=res(h);p=path+'/'+str(n['id']);idx[p]=norm(n)
            if n.get('phaseGraph'):visit(res(n['phaseGraph']),p)
    visit(res(doc['Data']['RootChunk']['graph']),'root')
    return idx
a=read(OUT/'assessment_01.json');c=read(OUT/'coverage_01.json')
ids={r['candidate_index'] for r in a['decisions'] if r['decision']=='REQUIRES_INDIVIDUAL_CONTENT_AND_SUPPORT_REVIEW'}
cache={};rows=[]
common={'questInputNodeDefinition','questOutputNodeDefinition','questSpawnManagerNodeDefinition','questPauseConditionNodeDefinition','questConditionNodeDefinition','questLogicalHubNodeDefinition','questLogicalAndNodeDefinition','questLogicalXorNodeDefinition','questRandomizerNodeDefinition','questCrowdManagerNodeDefinition','questDeletionMarkerNodeDefinition','questPhaseNodeDefinition'}
for r in c['rows']:
    if r['candidate_index'] not in ids:continue
    if r['source'] not in cache:cache[r['source']]=load(r['source'])
    nodes={p:n for p,n in cache[r['source']].items() if p.startswith(r['node_path']+'/')}
    special={p:n for p,n in nodes.items() if n['$type'] not in common}
    rows.append({'id':r['candidate_index'],'source':r['source'],'node_path':r['node_path'],'prefab':r['full_ref'],'exclusion':r['exclusion'],'support_reason':r['asset_reasons'],
        'special_payloads':special,'nested_phases':r['nested_phases'],
        'community_actions':sorted({v['action'] for v in walk(nodes) if v.get('$type')=='questCommunityTemplate_NodeType'}),
        'all_payload_types':dict(collections.Counter(v['$type'] for v in walk(nodes) if '$type' in v)),
        'crowd_operations':[n for n in nodes.values() if n['$type']=='questCrowdManagerNodeDefinition']})
assert len(rows)==58
dest=OUT/'remaining_payloads_01.json';assert not dest.exists();dest.write_text(json.dumps({'rows':rows,'game_writes':0,'save_writes':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'id':r['id'],'special':[{'path':p,'type':n['$type'],'payload':{k:v for k,v in n.items() if k not in ('id','$type')}} for p,n in r['special_payloads'].items()]} for r in rows if r['special_payloads']],indent=2))
