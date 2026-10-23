"""Select inert Tower clinic art/collision, never whole ending variants.

Reads existing vanilla exports. Emits a small explicit node manifest for an
independent mod-owned streaming candidate; this is not a runtime repair.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/misty_viktor_world'
ALLOW={'worldStaticMeshNode','worldStaticDecalNode','worldCollisionNode'}

def val(value):
    return value.get('$value',value) if isinstance(value,dict) else value

def main():
    source=json.loads((ROOT/'research/phase2b_p4/compiled_staging_members.json').read_text())
    rows=[]
    for group in source:
        if group['variant']['name']!='q307_zetatech':
            continue
        path=ROOT/'research/phase2b_p4/variant_sectors/ep1_1_nightcity/json'/Path(group['sector']+'.json')
        rel=Path('research/phase2b_p4/variant_sectors/ep1_1_nightcity/raw')/Path(group['sector'])
        raw=ROOT/rel
        data=json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        instances=data['nodeData']['Data']
        chosen=[];excluded=[]
        for index in range(group['range_start'],group['range_end_exclusive']):
            instance=instances[index]
            node=data['nodes'][instance['NodeIndex']]['Data']
            kind=node['$type']
            record={'data_index':index,'node_index':instance['NodeIndex'],
                    'type':kind,'name':val(node.get('debugName')),
                    'reference':val(instance.get('QuestPrefabRefHash')),
                    'position':[instance['Position'][a] for a in ('X','Y','Z')]}
            if kind in ALLOW:
                for name in ('mesh','material'):
                    if isinstance(node.get(name),dict):
                        record[name]=val(node[name].get('DepotPath'))
                chosen.append(record)
            else:
                excluded.append(record)
        if chosen:
            rows.append({'source_sector':group['sector'],'raw_path':str(rel),
                         'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                         'range': [group['range_start'],group['range_end_exclusive']],
                         'descriptor_index':group['descriptor_index'],
                         'source_block':group['block'],
                         'variant':group['variant'],
                         'selected':chosen,'excluded':excluded})
    types=Counter(n['type'] for r in rows for n in r['selected'])
    excluded=Counter(n['type'] for r in rows for n in r['excluded'])
    assert types['worldCollisionNode']==5,types
    assert types['worldStaticMeshNode']==688,types
    assert types['worldStaticDecalNode']==149,types
    assert all(n['type'] in ALLOW for r in rows for n in r['selected'])
    # Source membership, not runtime floor residency/navmesh/access certification.
    floors=json.loads((ROOT/'research/phase2b_p4/floor_collider_matches.json').read_text())
    matches=[m for m in floors if any(r['source_sector']==m['collision_sector']
             and any(n['data_index']==m['collision_node_data'] for n in r['selected'])
             for r in rows)]
    result={'status':'INERT_GEOMETRY_SELECTION_ONLY_NOT_BUILT_OR_INSTALLED',
            'preserve':'Tower Zetatech appearance; no old Misty shop/resident restoration',
            'allow_types':sorted(ALLOW),'selected_types':dict(types),
            'excluded_types':dict(excluded),'source_ranges':rows,
            'floor_collision_matches':matches,
            'forbidden':['original q307_zetatech toggle','q307_entities toggle',
                         'q307_misty_alley toggle','q307_hide_misty toggle',
                         'q307/root/ending scene start','actors/communities/triggers',
                         'story fact changes','door unlocks'],
            'pending':['private world block/variant ownership and native gated acquisition',
                       'identity and collision-buffer safety','streaming roundtrip/readback',
                       'walkable shell and surviving door route live check',
                       'clinic access/lighting/device facade follow-up as demonstrated']}
    OUT.mkdir(exist_ok=True)
    (OUT/'geometry_selection.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'selected':dict(types),
                      'excluded':dict(excluded),'ranges':len(rows),
                      'floor_matches':len(matches)},indent=2))

if __name__=='__main__':
    main()
