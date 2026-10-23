"""Bounded door/appearance provenance from existing Tower and world exports."""
import json
from collections import Counter
from pathlib import Path
from analyze_q307 import walk

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/misty_viktor_world'

def val(x):return x.get('$value',x) if isinstance(x,dict) else x

def main():
    actions=[]
    base=ROOT/'research/q307_extracted/json/ep1/quest/main_quests/q307'
    for path in sorted(base.rglob('*.json')):
        if '/test/' in path.as_posix():continue
        for obj,loc,parents in walk(json.loads(path.read_text(encoding='utf-8-sig'))):
            if obj.get('$type')!='questDeviceManager_NodeTypeParams':continue
            ref=val(obj.get('objectRef'))
            if not ref or not any(s in str(ref) for s in ('misty_door','zetatech_door','ripperdoc_room_door')):continue
            actions.append({'resource':str(path.relative_to(base)),
                            'json_path':'.'.join(map(str,loc)),
                            'nodes':[{'id':p.get('id'),'type':p['$type']} for p in parents if 'NodeDefinition' in p.get('$type','')],
                            'object':ref,'action':val(obj.get('deviceAction')),
                            'controller':val(obj.get('deviceControllerClass')),
                            'properties':obj.get('actionProperties')})
    compiled=json.loads((ROOT/'research/phase2b_p4/compiled_staging_members.json').read_text())
    samples=json.loads((ROOT/'research/phase2b_p4/physical_member_samples.json').read_text())
    selected=[]
    for group in compiled+samples:
        name=group.get('name',group.get('variant',{}).get('name'))
        if name not in ('neon_hide','q307_decoration','q307_zetatech_deco','q307_zetatech','q307_entities'):continue
        members=group['members']
        relevant=[m for m in members if any(s in str(m).lower() for s in ('neon','zetatech','sign','door','myst','logo'))]
        selected.append({'variant':name,'sector':group['sector'],
                         'counts':group['type_counts'],'appearance_or_door_members':relevant})
    result={'status':'READ_ONLY_SOURCE_TRACE_NOT_A_DOOR_UNLOCK_OR_FACADE_FIX',
            'door_actions':actions,'world_ranges':selected}
    (OUT/'access_appearance_trace.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'door_actions':actions},indent=2))
    for row in selected:
        print(row['variant'],row['sector'],row['counts'])
        for member in row['appearance_or_door_members']:
            print({k:member[k] for k in ('node_data_index','node_data','node_index','name','ref','node_ref','mesh','entityTemplate') if k in member})

if __name__=='__main__':main()
