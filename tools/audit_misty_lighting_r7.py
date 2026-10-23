"""Read-only nearby original lighting/mesh/entity owner and override inventory."""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/misty_viktor_world'
POINTS={'police':(-1552.9783,1171.5599,16.3545),'neon':(-1542.3109,1180.8624,16.9070)}

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
def val(v):return v.get('$value',v) if isinstance(v,dict) else v
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)

desc={}
for bp in (ROOT/'research/phase2b_p4/staging_scan/ep1_1_nightcity/json').rglob('all.streamingblock.json'):
    for i,d in enumerate(read(bp)['descriptors']):desc[val(d['data']['DepotPath'])]=(str(bp.relative_to(ROOT)),i,d)
paths={}
for folder in (ROOT/'research/phase2b_p4/variant_sectors/ep1_1_nightcity/json',OUT/'r6_variant_audit_lighting_sources'):
    for p in folder.rglob('*.streamingsector.json'):paths[str(p.relative_to(folder)).replace('/','\\')[:-5]]=p
rows=[]
for depot,p in paths.items():
    s=read(p)
    if 'Data' not in s.get('nodeData',{}):continue
    dd=desc.get(depot);starts=s['variantIndices']
    for i,nd in enumerate(s['nodeData']['Data']):
        n=s['nodes'][nd['NodeIndex']]['Data'];pos=[nd['Position'][a] for a in 'XYZ']
        distances={k:round(math.dist(pos,v),4) for k,v in POINTS.items()}
        if min(distances.values())>12:continue
        typ=n['$type'];name=val(n.get('debugName',''))
        if not ('Light' in typ or 'Entity' in typ or any(v in name.lower() for v in ('neon','lamp','strip','police','spot'))):continue
        ri=max(k for k,v in enumerate(starts) if v<=i)
        row={'sector':depot,'data_index':i,'node_index':nd['NodeIndex'],'name':name,'type':typ,
             'distances':distances,'position':pos,'variant_index':ri,
             'variants':[] if dd is None else [v for v in dd[2].get('variants',[]) if v['rangeIndex']==ri],
             'resources':[val(v['DepotPath']) for v in walk(n) if 'DepotPath' in v],
             'node_data':nd,'node':n}
        rows.append(row)
rows.sort(key=lambda r:min(r['distances'].values()))
(OUT/'r7_lighting_nearby.json').write_text(json.dumps({'points':POINTS,'rows':rows},indent=2)+'\n')
for r in rows:
    print(json.dumps({k:r[k] for k in ('data_index','node_index','name','type','distances','position')}|{'variants':[val(v['name']) for v in r['variants']],'color':r['node'].get('color'),'ref':val(r['node_data'].get('QuestPrefabRefHash'))}))
