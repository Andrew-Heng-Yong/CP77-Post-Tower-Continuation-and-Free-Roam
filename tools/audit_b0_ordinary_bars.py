"""Compact, reproducible audit of four complete ordinary bar scenes."""
import json
from plan_b0_ordinary_vendor_batch import ROOT, BASE, OUT, read, walk, unwrap, resource, graph_at, nm

DEST = ROOT / 'research/b0_ordinary_bars'
KEYS = {'cct_cpz_food_01': ('corpo_bar', 'Corpo Plaza bar'),
        'std_arr_foodshop_01': ('arroyo_bar', 'Arroyo bar'),
        'wat_nid_foodshop_02': ('northside_bar', 'Northside bar'),
        'wbr_hil_foodshop_01': ('charter_bar', 'Charter Hill bar')}

def compact(value):
    if isinstance(value, list): return [compact(v) for v in value]
    if not isinstance(value, dict): return value
    if '$value' in value: return value['$value']
    if 'Data' in value: return compact(value['Data'])
    return {k: compact(v) for k,v in value.items() if k not in ('sockets','HandleId','uniqueNodeId')}

def main():
    DEST.mkdir(exist_ok=True)
    result=[]
    for row in read(OUT/'owner_audit.json'):
        if row['id'] not in KEYS: continue
        sr=read(BASE/row['scene_group']/'json'/(row['scene'].replace('\\','/')+'.json'))['Data']['RootChunk']
        nodes={h['Data']['nodeId']['id']:h['Data'] for h in sr['sceneGraph']['Data']['graph']}
        entry=next(e['nodeId']['id'] for e in sr['entryPoints'] if unwrap(e['name'])==row['scene_socket'])
        queue=[entry];seen=set()
        while queue:
            i=queue.pop()
            if i in seen: continue
            seen.add(i)
            queue.extend(d['nodeId']['id'] for s in nodes[i].get('outputSockets',[]) for d in s.get('destinations',[]))
        actors=[{'id':a['actorId']['id'],'name':a['actorName'],'acquisition':a['acquisitionPlan'],
                 'spawn':compact(a['spawnSetParams'])} for a in sr['actors']]
        ops=[]
        for i in sorted(seen):
            n=nodes[i]
            quest=[]
            for v in walk(n):
                t=v.get('$type')
                if t=='questSetVar_NodeType': quest.append(compact(v))
                elif t=='questUseWorkspotNodeDefinition':
                    p=v['paramsV1']['Data']
                    quest.append({'type':t,'entity':compact(v['entityReference']),
                                  'function':p['function'],'isPlayer':p['isPlayer'],
                                  'instance':compact(p.get('workspotInstanceId'))})
                elif t in ('questScene_NodeType','questVendorPanel_NodeType','questTrigger_ConditionType'):
                    quest.append(compact(v))
            ops.append({'id':i,'type':n['$type'],'next':[d['nodeId']['id'] for s in n.get('outputSockets',[]) for d in s.get('destinations',[])], 'ops':quest})
        props=[{'name':p['propName'],'plan':p['entityAcquisitionPlan'],
                'findNode':compact(p['findEntityInNodeParams']),
                'spawn':compact(p['spawnDespawnParams'])} for p in sr.get('props',[])]
        refs=sorted({v['$value'] for v in walk(sr) if v.get('$type')=='NodeRef' and v.get('$storage')=='string'})
        owner=resource(row['source']); branch=nm(graph_at(owner,'root/node'+str(row['outer'])))
        assert nm(owner['graph']['Data'])[row['outer']]['phaseInstancePrefabs']==[]
        assert branch[row['phase']]['phaseInstancePrefabs']==[]
        assert not any('ancestor' in s for s in row['reasons'])
        assert not any(f.startswith(('q0','q1','q2','q3','sq','mq','sts_')) for f in row['scene_fact_writes'])
        result.append({'id':row['id'],'actors':actors,'props':props,'refs':refs,'entry':entry,'nodes':ops,
                       'interruptionScenarios':compact(sr.get('interruptionScenarios',[])),
                       'workspotInstances':compact(sr.get('workspotInstances',[])),
                       'owner':row})
    (DEST/'scene_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    for a in result:
        print(a['id'], '\n actors',a['actors'],'\n refs',a['refs'])
        for n in a['nodes']:
            if n['ops']: print(n['id'], '->',n['next'],json.dumps(n['ops']))

if __name__=='__main__': main()
