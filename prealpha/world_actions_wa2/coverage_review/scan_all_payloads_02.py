"""Resolve all shared payload handles before classifying omitted action families."""
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
def index(source):
    doc=read(source);hs={v['HandleId']:v['Data'] for v in walk(doc) if 'HandleId' in v and 'Data' in v}
    def res(v):return v.get('Data',hs.get(v.get('HandleRefId'),v))
    def norm(v):
        if isinstance(v,dict):
            if 'HandleId' in v or 'HandleRefId' in v:return norm(res(v))
            return {k:norm(x) for k,x in v.items() if k not in ('sockets','phaseGraph')}
        if isinstance(v,list):return [norm(x) for x in v]
        return v
    idx={}
    def visit(g,p):
        for h in g['nodes']:
            n=res(h);q=p+'/'+str(n['id']);idx[q]=norm(n)
            if n.get('phaseGraph'):visit(res(n['phaseGraph']),q)
    visit(res(doc['Data']['RootChunk']['graph']),'root');return idx
rows=[];cache={}
for r in read(OUT/'coverage_01.json')['rows']:
    s=r['source']
    if s not in cache:cache[s]=index(WS/s)
    ns={p:n for p,n in cache[s].items() if p.startswith(r['node_path']+'/')}
    rows.append({'scope':'outside_inline','ids':[r['candidate_index']],'source':s,'nodes':ns})
for r in read(OUT/'external_assessment_01.json')['rows']:
    rows.append({'scope':'external','ids':r['candidate_indices'],'source':r['source'],'nodes':index(Path(r['source']))})
totals={};summaries=[]
for r in rows:
    types=collections.Counter(v['$type'] for v in walk(r['nodes']) if '$type' in v)
    special={p:n for p,n in r['nodes'].items() if any(t in n['$type'] for t in ('AI','MovePuppet','Workspot','Scene','Audio','Vehicle','Item','Character','Puppet'))}
    interesting={p:n for p,n in r['nodes'].items() if any('UseWeapon' in v.get('$type','') or 'ForceShoot' in v.get('$type','') for v in walk(n))}
    summaries.append({k:v for k,v in r.items() if k!='nodes'}|{'node_count':len(r['nodes']),'all_payload_types':dict(types),'special_payloads':special,'shooting_payloads':interesting})
    totals.setdefault(r['scope'],collections.Counter()).update(types)
result={'status':'COMPLETE_HANDLE_RESOLVED_PAYLOAD_CENSUS_NOT_ALLOWLIST','counts':{s:dict(c) for s,c in totals.items()},'rows':summaries,'game_writes':0,'save_writes':0}
dest=OUT/'all_payloads_02.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({s:{k:v for k,v in c.items() if any(x in k for x in ('Command','Weapon','SceneNode','Audio','Workspot','MovePuppet','ItemManager'))} for s,c in totals.items()},indent=2))
print(json.dumps([{'scope':r['scope'],'ids':r['ids'],'shooting':list(r['shooting_payloads'])} for r in summaries if r['shooting_payloads']],indent=2))
