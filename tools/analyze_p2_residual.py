"""Produce compact P2 static evidence from local exports; never accesses game/save files."""
import json
from pathlib import Path
from collections import deque
from analyze_q307 import walk, scalar_details

BASE = Path('research/phase2b_p2')
ROOT = Path('research/q307_extracted/json/ep1/quest/main_quests/q307')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def scene(name):
    return {n['Data']['nodeId']['id']: n['Data'] for n in read(ROOT / 'scenes' / (name+'.scene.json'))['Data']['RootChunk']['sceneGraph']['Data']['graph']}

def dests(n):
    return [(d['nodeId']['id'], d['isockStamp']) for s in n.get('outputSockets',[]) for d in s['destinations']]

def route(ns, start, end):
    q=deque([(start,[start])]); seen=set()
    while q:
        n,p=q.popleft()
        if n==end:return p
        if n in seen:continue
        seen.add(n)
        for d,_ in dests(ns[n]): q.append((d,p+[d]))
    return None

misty=scene('q307_08_misty'); final=scene('q307_09_cutscene')
out={}
out['scene_nodes']={}
for label,ns,ids in [('misty',misty,[634,636,740,742]),('final',final,[172])]:
    out['scene_nodes'][label]=[{ 'id':i, 'type':ns[i]['$type'], 'in':ns[i].get('isockMappings'), 'out':dests(ns[i]), 'quest':scalar_details(ns[i].get('questNode',{}))} for i in ids]
out['misty_sources_to_634']=[{'id':i,'type':n['$type'],'out':dests(n)} for i,n in misty.items() if any(d==634 for d,_ in dests(n))]
out['misty_paths_to_handoff']=[{'start':i,'to742':route(misty,i,742)} for i in [634,636]]
out['misty_start_to_activation']=[{'start':i,'to636':route(misty,i,636)} for i,n in misty.items() if n['$type']=='scnStartNode']
out['misty_section63_to_handoff']=route(misty,63,742)
out['final_to_wait']=[{'start':i,'to172':route(final,i,172)} for i,n in final.items() if n['$type']=='scnStartNode']

analysis=read('research/q307_analysis/analysis.json')
out['phase_edges']=[]
for e in analysis['edges']:
    name=e['resource'].split('\\')[-1]
    if name in ['q307.questphase','q307_08_misty.questphase','q307_09_cutscene.questphase'] and e['graph'].endswith('::Data.RootChunk.graph.Data'):
        if name=='q307.questphase' and e['source_node_id'] not in [27,28,29,30]:continue
        out['phase_edges'].append({'file':name,'from':e['source_node_id'],'out':e['source_socket'],'to':e['destination_node_id'],'in':e['destination_socket']})

sector=read(BASE/'extracted_more/json/base/worlds/03_night_city/_compiled/default/exterior_-25_19_0_0.streamingsector.json')['Data']['RootChunk']
data=sector['nodeData']['Data'][672];node=sector['nodes'][data['NodeIndex']]['Data']
ps=node['instanceData']['Data']['buffer']['Data']['Chunks'][0]['persistentState']['Data']
out['door']={'nodeDataIndex':672,'nodeIndex':data['NodeIndex'],'nodeRef':data['QuestPrefabRefHash'],'position':data['Position'],'template':node['entityTemplate'],'appearance':node['appearanceName'],'controller':'DoorControllerPS','properties':{k:v for k,v in ps.items() if k in ['isInteractive','isLocked','isSealed','deviceState','doorProperties','authorizationProperties','isLiftDoor']}}

journal=read(BASE/'extracted/json/ep1/journal/cooked_journal.journal.json')
quest=next(o for o,p,a in walk(journal) if o.get('id')=='q307_tomorrow')
out['journal_hierarchy']=[{'type':o['$type'],'id':o['id'],'parents':[x['id'] for x in a if 'id' in x],'override':o.get('journalEntryOverrideDataList'),'description':o.get('description'),'title':o.get('title')} for o,p,a in walk(quest) if o.get('id') in ['q307_tomorrow','02_mistys_alley','05_take_walk']]

writers=[]
for root in [Path('research/q307_extracted/json'),BASE/'extracted_more/json',BASE/'location/json']:
    for f in root.rglob('*.json'):
        if not f.name.endswith(('.scene.json','.questphase.json','.quest.json')): continue
        for obj,p,a in walk(read(f)):
            if obj.get('realPath','') in ['ep1/quests/main_quest/q307_tomorrow','ep1/quests/main_quest/q307_tomorrow/02_mistys_alley','ep1/quests/main_quest/q307_tomorrow/02_mistys_alley/05_take_walk']:
                owner=next((x for x in reversed(a) if 'id' in x and x.get('$type','').endswith('NodeDefinition')),None)
                writers.append({'file':str(f),'path':obj['realPath'],'owner':scalar_details(owner) if owner else None})
out['journal_references']=writers
assert out['door']['template']['DepotPath']['$value'].endswith('single_door.ent')
assert next(e for e in out['phase_edges'] if e['file']=='q307_09_cutscene.questphase' and e['to']==7)['in']=='Succeeded'
assert out['scene_nodes']['misty'][1]['in'][1]['$value']=='Active'
(BASE/'static_evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'journal_references':len(writers),'door':out['door']['nodeRef'],'misty_sources_to_634':out['misty_sources_to_634'],'final_to_wait':out['final_to_wait']},indent=1))
