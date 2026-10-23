"""Bounded, reproducible inventory of uninstalled controller leaves and payloads."""
import json
from pathlib import Path
from index_mirror_leaves import PATH, ROOT, walk, values
from test_streetkid_scene_load_s3 import quest_edges

out = ROOT/'research/b0_remaining_mirrors'
out.mkdir(exist_ok=True)
doc = json.loads(PATH.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
outer = next(n['Data'] for n in doc['graph']['Data']['nodes'] if n['Data']['id']==42)
c4 = json.loads((ROOT/'research/b0_mirror_rollout/validation_c4/build_manifest.json').read_text(encoding='utf-8-sig'))
installed = {s['id'] for s in c4['sites']} | {11,42,48}
block = json.loads((ROOT/'research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/blocks/all.streamingblock.json').read_text(encoding='utf-8-sig'))['Data']['RootChunk']['descriptors']
rows=[]
for item in outer['phaseGraph']['Data']['nodes']:
    leaf=item['Data']; ident=leaf['id']
    if leaf['$type']!='questPhaseNodeDefinition' or ident in installed:
        continue
    graph=leaf['phaseGraph']['Data']
    scenes=[n['Data'] for n in graph['nodes'] if n['Data']['$type']=='questSceneNodeDefinition']
    if len(scenes)!=1: continue
    node=scenes[0]; depot=node['sceneFile']['DepotPath']['$value']
    marker=node['sceneLocation']['nodeRef']['$value']
    prefab=marker.replace('#mirror_sm_','#mirror_')
    descriptors=[d for d in block if d.get('questPrefabNodeRef',{}).get('$value','').endswith('/'+prefab)]
    scene=None
    for folder in ['research/b0_remaining_mirrors/extracted/json','research/b0_mirror_rollout/vanilla_ordinary/json','research/b0_mirror_investigation/extracted/json']:
        path=ROOT/folder/Path(depot.replace('\\','/')+'.json')
        if path.exists():
            scene=json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk'];break
    row=dict(id=ident,scene=depot,prefab=prefab,marker=marker,
             sectors=[d['data']['DepotPath']['$value'] for d in descriptors],
             leaf_nodes=len(graph['nodes']),triggers=sorted(values(graph,'triggerAreaRef')),
             leaf_facts=sorted(values(graph,'factName')),
             leaf_nodes_summary=[{'id':n['Data']['id'],'type':n['Data']['$type'],
                 'conditions':[o for o in walk(n['Data'].get('condition',{})) if o.get('$type') in ['questVarComparison_ConditionType','questCharacterCombat_ConditionType','questTriggerCondition','questJournalEntryState_ConditionType']]} for n in graph['nodes']])
    if scene:
        row.update(scene_nodes=len(scene['sceneGraph']['Data']['graph']),scene_facts=sorted(values(scene,'factName')),
                   writers=[o for o in walk(scene) if o.get('$type')=='questSetVar_NodeType'],
                   quest_types=sorted({o['$type'] for o in walk(scene) if o.get('$type','').startswith('quest')}),
                   triggers=sorted(set(row['triggers'])|values(scene,'triggerAreaRef')),
                   johnny='johnny' in json.dumps(scene).lower())
    rows.append(row)
(out/'inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
for r in rows:
    print(json.dumps({k:r.get(k) for k in ['id','scene','leaf_nodes','scene_nodes','leaf_facts','scene_facts','writers','johnny','sectors']}))
print('Remaining controller leaves:',len(rows),'already installed:',len(installed))
