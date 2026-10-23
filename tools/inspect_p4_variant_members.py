"""Enumerate compiled sector descriptors containing exact q307 staging variants."""
import json
import collections
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCAN=ROOT/'research/phase2b_p4/staging_scan'
NAMES={'q307_zetatech','q307_entities','q307_misty_alley','q307_zetatech_deco','q307_decoration','q307_hide_misty'}
def val(v):return v.get('$value') if isinstance(v,dict) else v
def xyz(p):return [p.get(k) for k in ('X','Y','Z')]

def compile_members(rows):
    results=[]
    for row in rows:
        path=ROOT/'research/phase2b_p4/variant_sectors/ep1_1_nightcity/json'/Path(row['sector']+'.json')
        if not path.exists():continue
        root=json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        instances=root.get('nodeData',{}).get('Data')
        if not isinstance(instances,list):continue
        starts=root['variantIndices']
        for variant in row['variants']:
            idx=variant['rangeIndex']
            start=starts[idx];end=starts[idx+1] if idx+1<len(starts) else len(instances)
            members=[]
            for di in range(start,end):
                d=instances[di];ni=d['NodeIndex'];n=root['nodes'][ni]['Data']
                m={'node_data_index':di,'node_index':ni,'type':n['$type'],'name':val(n.get('debugName')),'position':xyz(d['Position']),'orientation':d.get('Orientation'),'ref':val(d.get('QuestPrefabRefHash'))}
                for key in ('mesh','entityTemplate'):
                    if key in n:m[key]=val(n[key]['DepotPath'])
                if n['$type']=='worldCollisionNode':
                    actors=n.get('compiledData',{}).get('Data',{}).get('Actors',[])
                    m['actors']=len(actors)
                    m['shape_types']=dict(collections.Counter(s['ShapeType'] for a in actors for s in a.get('Shapes',[])))
                    m['floor_height_actors']=[]
                    for ai,a in enumerate(actors):
                        p=[a['Position'][k]['Bits']/131072 for k in ('x','y','z')]
                        if -1552<p[0]<-1535 and 1190<p[1]<1207 and 15.7<p[2]<16.4:
                            m['floor_height_actors'].append({'actor_index':ai,'position':p,'orientation':a.get('Orientation'),'shapes':a.get('Shapes',[])})
                members.append(m)
            r={k:row[k] for k in ('sector','block','descriptor_index')}
            r.update({'variant':variant,'range_start':start,'range_end_exclusive':end,'type_counts':dict(collections.Counter(m['type'] for m in members)),'members':members})
            results.append(r)
    (ROOT/'research/phase2b_p4/compiled_staging_members.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    floors=[(r,m) for r in results if r['variant']['name']=='q307_zetatech' for m in r['members'] if 'int_common_a_floor' in str(m.get('name',''))]
    matches=[]
    for row in results:
        if row['variant']['name']!='q307_zetatech':continue
        for member in row['members']:
            for actor in member.get('floor_height_actors',[]):
                for floor_row,floor in floors:
                    distance=math.dist(actor['position'],floor['position'])
                    if distance<.001:
                        qa=[actor['orientation'][k] for k in ('i','j','k','r')]
                        qf=[floor['orientation'][k] for k in ('i','j','k','r')]
                        qdistance=min(math.dist(qa,qf),math.dist(qa,[-x for x in qf]))
                        matches.append({'collision_sector':row['sector'],'collision_node_data':member['node_data_index'],'collision_node':member['node_index'],'actor_index':actor['actor_index'],'position':actor['position'],'floor_sector':floor_row['sector'],'floor_node_data':floor['node_data_index'],'floor_node':floor['node_index'],'floor_mesh':floor.get('mesh'),'position_distance':distance,'quaternion_distance':qdistance,'shapes':actor['shapes']})
    (ROOT/'research/phase2b_p4/floor_collider_matches.json').write_text(json.dumps(matches,indent=2),encoding='utf-8')
    for r in results:
        if r['variant']['name'] in ('q307_zetatech','q307_entities'):
            print(r['sector'],r['variant']['name'],r['range_start'],r['range_end_exclusive'],r['type_counts'])
def main():
    result=[]
    for path in SCAN.rglob('all.streamingblock.json'):
        doc=json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        for i,d in enumerate(doc['descriptors']):
            variants=[v for v in d.get('variants',[]) if val(v.get('name')) in NAMES]
            if not variants:continue
            row={'block':str(path.relative_to(ROOT)),'descriptor_index':i,'sector':val(d['data']['DepotPath']), 'category':d.get('category'),'level':d.get('level'),'questPrefabNodeRef':val(d.get('questPrefabNodeRef')),'numNodeRanges':d.get('numNodeRanges'),'variants':[{k:val(v) for k,v in x.items() if k!='$type'} for x in variants]}
            result.append(row)
            print(json.dumps(row,separators=(',',':')))
    (ROOT/'research/phase2b_p4/staging_variant_sectors.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    compile_members(result)
if __name__=='__main__':main()
