"""Summarize variant member types/assets from existing per-archive sectors."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/phase2b_p4'
NAMES={'q307_delamain_ride','q307_delamain_ride_hide','q307_garry_lives','q307_garry_donated','q307_garry_not_donated','neon_hide','q307_misty_scene','q307_misty_scene_hide','q307_credits_2079','q307_credits_2077','q307_credits_hide'}
def val(v):return v.get('$value')if isinstance(v,dict)else v
def main():
    census=json.loads((OUT/'physical_variant_census.json').read_text())
    results=[];seen=set()
    for g in census['variants']:
        if g['name']not in NAMES:continue
        for d in g['exact_owner_matches']+g['name_only_candidates']:
            key=(d['sector'],d['variant']['rangeIndex'])
            if key in seen:continue
            seen.add(key)
            path=next((p for group in ['physical_samples','variant_sectors','staging_scan','normal_candidates'] if (p:=OUT/group/'ep1_1_nightcity/json'/Path(d['sector']+'.json')).exists()),None)
            if path is None:continue
            root=json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk'];data=root.get('nodeData',{}).get('Data');starts=root.get('variantIndices',[])
            if not isinstance(data,list):continue
            ri=d['variant']['rangeIndex'];start=starts[ri];end=starts[ri+1]if ri+1<len(starts)else len(data)
            members=[]
            for i in range(start,end):
                nd=data[i];n=root['nodes'][nd['NodeIndex']]['Data'];m={'node_data':i,'node_index':nd['NodeIndex'],'type':n['$type'],'name':val(n.get('debugName')),'position':{k:nd['Position'][k]for k in ['X','Y','Z']},'node_ref':val(nd.get('QuestPrefabRefHash'))}
                for k in ['mesh','entityTemplate','effect','particleSystem','resource']:
                    if k in n and isinstance(n[k],dict) and'DepotPath'in n[k]:m[k]=val(n[k]['DepotPath'])
                members.append(m)
            results.append({'name':d['variant']['name'],'owner':d['variant']['nodeRef'],'sector':d['sector'],'range_index':ri,'range_start':start,'range_end_exclusive':end,'enabled_by_default':d['variant']['enabledByDefault'],'type_counts':dict(Counter(x['type']for x in members)),'members':members})
    (OUT/'physical_member_samples.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    for r in results:
        print(r['name'],r['sector'],r['type_counts'])
        print([(m['name'],m.get('entityTemplate',m.get('mesh')))for m in r['members'][:20]])
if __name__=='__main__':main()
