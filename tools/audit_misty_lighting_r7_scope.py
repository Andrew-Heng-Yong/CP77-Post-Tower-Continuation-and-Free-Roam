"""Read-only full WLC03 original variant pair scope and exact candidates."""
import collections
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/misty_viktor_world'
PAIR=('WLC_03_Default','WLC_03_Q307')
CENTER=(-1548.0,1190.0,17.0)

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
def val(v):return v.get('$value',v) if isinstance(v,dict) else v
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)

ranges=[]
for bp in (ROOT/'research/phase2b_p4/staging_scan/ep1_1_nightcity/json').rglob('all.streamingblock.json'):
    for di,d in enumerate(read(bp)['descriptors']):
        chosen=[v for v in d.get('variants',[]) if val(v['name']) in PAIR]
        if not chosen:continue
        depot=val(d['data']['DepotPath']);p=OUT/'r7_lighting_sources'/(depot+'.json')
        s=read(p);data=s['nodeData']['Data'];starts=s['variantIndices']
        for v in chosen:
            ri=v['rangeIndex'];start=starts[ri];end=starts[ri+1] if ri+1<len(starts) else len(data)
            members=[]
            for idx in range(start,end):
                nd=data[idx];n=s['nodes'][nd['NodeIndex']]['Data'];pos=[nd['Position'][a] for a in 'XYZ']
                members.append({'data_index':idx,'node_index':nd['NodeIndex'],'type':n['$type'],'name':val(n.get('debugName')),
                     'position':pos,'distance_from_shop':round(math.dist(CENTER,pos),4),
                     'resources':[val(x['DepotPath']) for x in walk(n) if 'DepotPath' in x],
                     'color':n.get('color'),'appearance':val(n.get('meshAppearance')),
                     'node_data':nd,'node':n})
            ranges.append({'sector':depot,'block':str(bp.relative_to(ROOT)),'descriptor':di,'variant':v,
                           'start':start,'end_exclusive':end,'type_counts':dict(collections.Counter(x['type'] for x in members)),
                           'members':members})
sources=[]
for p in (ROOT/'research/q307_extracted/json').rglob('*.json'):
    doc=read(p)
    for x in walk(doc):
        if x.get('$type')=='questTogglePrefabVariant_NodeTypeParams' and any(val(y['name']) in PAIR for y in x['variantStates']):
            sources.append({'source':str(p.relative_to(ROOT)),'param':x})
summaries={}
for name in PAIR:
    these=[r for r in ranges if val(r['variant']['name'])==name]
    members=[m for r in these for m in r['members']]
    summaries[name]={'ranges':len(these),'members':len(members),'type_counts':dict(collections.Counter(m['type'] for m in members)),
                     'position_min':[min(m['position'][a] for m in members) for a in range(3)],
                     'position_max':[max(m['position'][a] for m in members) for a in range(3)],
                     'max_distance':max(m['distance_from_shop'] for m in members),
                     'beyond120m':[m for m in members if m['distance_from_shop']>120]}
result={'summary':summaries,'ranges':ranges,'vanilla_actions':sources}
(OUT/'r7_lighting_scope.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{x:y for x,y in v.items() if x!='beyond120m'} for k,v in summaries.items()},indent=2))
for name,v in summaries.items():
    print(name,'beyond120m',[(m['name'],m['type'],m['position']) for m in v['beyond120m']])
print('actions',sources)
