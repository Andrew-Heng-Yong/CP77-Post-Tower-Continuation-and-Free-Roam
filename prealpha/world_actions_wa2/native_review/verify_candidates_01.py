"""Independent native slice, payload, lifecycle and reference proof."""
import copy,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;WS=OUT.parents[2]
run=sys.argv[1] if len(sys.argv)>1 else '02'
ss=(OUT/'census_02.py').read_text();q={'__file__':str(OUT/'census_02.py')};exec(ss[:ss.index('\nmanifest=read')],q)
read,sha,handles,norm,walk=[q[n] for n in ('read','sha','handles','norm','walk')]
contracts=read(OUT/'action_contracts_02.json')['contracts'];C={c['group']:c for c in contracts}
P=read(OUT/f'fresh_candidates_{run}/proof.json')
ba=read(WS/'prealpha/bottle_actions_ba1/native_review/fresh_candidate_01.json');base=norm(ba['Data']['RootChunk'],handles(ba));bp=read(WS/'prealpha/bottle_actions_ba1/native_review/fresh_graph_proof_01.json')
environment=read(OUT.parent/'environment_review/assessment_01.json');support=read(OUT.parent/'coverage_review/support_assessment_01.json')
rebinds=read(OUT.parent/'environment_review/community_rebinds_01.json')
checks=[];results=[]
def ck(ok,label):assert ok,label;checks.append(label)
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
def rewrite(v,group,community):
    if isinstance(v,dict):return {k:rewrite(x,group,community) for k,x in v.items()}
    if isinstance(v,list):return [rewrite(x,group,community) for x in v]
    if isinstance(v,str):return v.replace('PTFRBA1_',f'PTFRWA2_{group}_').replace('PTFRWW2_179_',f'PTFRWW2_{group}_').replace(C[179]['community_refs'][0],community)
    return v
def qualify(v,community):
    for _,x in walk(v):
        if isinstance(x,dict) and x.get('$type')=='NodeRef' and str(x.get('$value','')).startswith('#') and x['$value']!='#player':x['$value']=community
    return v
def semantic(v):
    v=copy.deepcopy(v)
    for _,x in walk(v):
        if isinstance(x,dict) and x.get('$type')=='NodeRef' and x.get('$value')!='0':
            x['$value']=P['node_ref_hashes'][x['$value']];x['$storage']='uint64'
    return v
for res in P['resources']:
    g=res['group'];c=C[g];community=support['candidate250']['community_ref'] if g==250 else c['community_refs'][0]
    d=read(Path(res['fresh_json']));actual=norm(d['Data']['RootChunk'],handles(d))
    expected=rewrite(copy.deepcopy(base),g,community);el=copy.deepcopy(node(expected['graph'],15)['condition'])
    cid=64 if g==172 else 61 if g==173 else 60000
    actual_controller=node(node(actual['graph'],10)['phaseGraph'],cid)
    originals=qualify(copy.deepcopy(c['nodes']),community)
    if g==256:
        for i in (2,6):next(n for n in originals if n['id']==i)['condition']['type']['spawnerReference']['$value']=community
    if g==319:next(n for n in originals if n['id']==31)['condition']['type']['objectRef']['reference']['$value']=community
    if g==246:
        for change in environment['required_candidate_corrections']:
            n=next(n for n in originals if n['id']==change['node']);f=n['condition']['type']['objectRef'];ck(f['$value']==change['old'],f'{g}exactsecurityoldref{n["id"]}');f['$value']=change['new']
    vehicle='vehicle' in c['kind']
    gate=2 if c['kind']=='isolated_vehicle_radio_door_phase' else c['entry_gate_id']
    if vehicle and c['kind']!='nested_vehicle_radio_event_only':
        n=next(n for n in originals if n['id']==gate);n['condition']={'$type':'questLogicalCondition','conditions':copy.deepcopy(el['conditions'])+[n['condition']],'operation':'AND'}
    expected_nodes=originals
    base_controller=node(node(base['graph'],10)['phaseGraph'],61)
    if c['kind'] not in ('isolated_shoot_phase','isolated_vehicle_radio_door_phase'):
        inp=copy.deepcopy(node(base_controller['phaseGraph'],0));inp['id']=65000
        end=copy.deepcopy(node(base_controller['phaseGraph'],1));end['id']=65001
        nr=rewrite(copy.deepcopy(node(base_controller['phaseGraph'],31)),g,community);nr['id']=65002
        expected_nodes+=[inp,end,nr]
        if c['kind']=='nested_vehicle_radio_event_only':
            extra=qualify(copy.deepcopy(c['outer_gate_payload']),community);extra['id']=65003
            extra['condition']={'$type':'questLogicalCondition','conditions':copy.deepcopy(el['conditions'])+[extra['condition']],'operation':'AND'}
            expected_nodes.append(extra)
    expected_controller=copy.deepcopy(base_controller);expected_controller['id']=cid;expected_controller['phaseGraph']['nodes']=expected_nodes
    ck(semantic(actual_controller)==semantic(expected_controller),f'{g}exactnativepayloadandreviewedsyntheticgates')
    loop=node(expected['graph'],10)['phaseGraph'];idx=next(i for i,n in enumerate(loop['nodes']) if n['id']==61);loop['nodes'][idx]=expected_controller
    root_edges=bp['root_edges']
    if vehicle:
        expected['graph']['nodes']=[n for n in expected['graph']['nodes'] if n['id']<11]
        ids={n['id'] for n in expected['graph']['nodes']}
        root_edges=[e for e in root_edges if int(e.split('.')[0]) in ids and int(e.split(' -> ')[1].split('.')[0]) in ids]
    ck(semantic(actual)==semantic(expected),f'{g}wholewrapperpayloadexact'+('persistseventlifetime' if vehicle else 'safetycutloop'))
    ck(res['root_edges']==root_edges,f'{g}rootedgesexact')
    ck(res['loop_edges']==sorted(e.replace('61.',str(cid)+'.') for e in bp['loop_edges']),f'{g}loopedgesexact')
    edges=[list(e) for e in c['internal_edges']]
    if c['kind'] not in ('isolated_shoot_phase','isolated_vehicle_radio_door_phase'):
        edges += [[65000,'Out',65002,'In'],[65002,'Out',65001,'In']]
        if c['kind']=='nested_vehicle_radio_event_only':edges += [[65000,'Out',65003,'In'],[65003,'Out',2,'In']]
        else:edges += [[65000,'Out',c['entry_gate_id'],'In']]
    ck(res['controller_edges']==sorted(f'{a}.{b} -> {x}.{y}' for a,b,x,y in edges),f'{g}allnativeandsyntheticinternaledgesexact')
    ck(not any(isinstance(v,dict) and v.get('$type') in ('questSpawnManagerNodeDefinition','questSceneNodeDefinition','questCheckpointNodeDefinition','questCharacterManagerNodeDefinition') for _,v in walk(actual)),f'{g}nospawnscenecheckpointcharacterstate')
    ck(all(not v.get('phaseInstancePrefabs') for _,v in walk(actual) if isinstance(v,dict) and v.get('$type')=='questPhaseNodeDefinition'),f'{g}noprefabownership')
    writes=[v for _,v in walk(actual) if isinstance(v,dict) and v.get('$type')=='questSetVar_NodeType']
    ck(all(v['factName'].startswith(f'PTFRWA2_{g}_') and v['setExactValue']==1 for v in writes),f'{g}onlyownexactreceiptwrites')
    allrefs=[v['reference']['$value'] for _,v in walk(actual_controller) if isinstance(v,dict) and v.get('$type')=='gameEntityReference' and v.get('reference',{}).get('$value') not in ('0','#player')]
    spawnerrefs=[v['spawnerReference']['$value'] for _,v in walk(actual) if isinstance(v,dict) and v.get('$type') in ('questSpawnerReady_ConditionType','questSpawnerNotReady_ConditionType')]
    wanted=P['node_ref_hashes'][community]
    ck(all(P['node_ref_hashes'][r]==wanted for r in allrefs+spawnerrefs),f'{g}everyactorandReadyNotReadyrefresolvesowncommunity')
    ck(sha(Path(res['path']))==res['sha256'],f'{g}candidateunchangedduringreview')
    if vehicle:
        ck(not any(e.startswith('12.CutSource') for e in res['root_edges']),f'{g}safetybouncedoesnotreplayevents')
        exit_id=1 if c['kind']=='isolated_vehicle_radio_door_phase' else 65001
        notready_id=6 if c['kind']=='isolated_vehicle_radio_door_phase' else 65002
        ck(node(actual_controller['phaseGraph'],exit_id)['type']=='Terminating' and [e for e in res['controller_edges'] if e.endswith(f' -> {exit_id}.In')]==[f'{notready_id}.Out -> {exit_id}.In'],f'{g}onlyNotReadyterminateseventlifetime')
    results.append({k:res[k] for k in ('group','resource','path','sha256')})
ck(len(results)==len({r['group'] for r in results}),'Distinctownerresources')
out={'status':'PASS_INDEPENDENT_COOKED_ACTION_PAYLOADS_GRAPHS_LIFETIMES_REFERENCES','checks':len(checks),'assertions':checks,'resources':results,'action_resources':len(results),
 'vehicle_once_per_ready_lifetime':sum('vehicle' in C[r['group']]['kind'] for r in results),'shooting_full_safety_cut':sum('shoot' in C[r['group']]['kind'] for r in results),
 'source_pins':[{'path':str(p),'sha256':sha(p)} for p in [OUT/'verify_candidates_01.py',OUT/'action_contracts_02.json',OUT/f'fresh_candidates_{run}/proof.json']],
 'game_writes':0,'save_writes':0,'limits':['Static source/serialization proof only; gameplay and save-reload not live verified.','Only listed exact resource hashes reviewed; additions require a new proof.']}
(OUT/f'candidate_assessment_{run}.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('assertions','source_pins','resources')},indent=2))
