"""Review the serialized owner and native support independently of the builder."""
import collections, hashlib, json
from pathlib import Path
H=Path(__file__).resolve().parent; W=H.parents[1]; C=H/'candidate_01'; R=H/'native_review_02'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def val(x): return x.get('$value') if isinstance(x,dict) else x
proof=read(R/'providers_01.json')
for row in proof['hits']: assert sha(Path(row['source']))==row['sha256']
full='$/03_night_city/c_watson/kabuki/loc_q004_lizzys_nightclub_prefabMARLNHA/#loc_q004_lizzys_nightclub_openworld'
assert proof['archives']==134 and len(proof['descriptors'])==2
assert all(d['prefab']==full and d['category']=='Quest' and d['variants']==0 for d in proof['descriptors'])
s=read(next((R/'source').rglob('*.streamingsector.json')))['Data']['RootChunk']
nodes=[h['Data'] for h in s['nodes']]; counts=collections.Counter(n['$type'] for n in nodes)
assert len(nodes)==461 and counts['worldAISpotNode']==393
refs={val(n) for n in s['nodeRefs']}
refs.update(val(n) for n in walk(s['nodeData']) if n.get('$type')=='NodeRef' and n.get('$storage')=='string')
marks={val(m) for n in nodes if n['$type']=='worldAISpotNode' for m in n['markings']}
def matches(ref): return sorted(x for x in refs if x==ref or x.endswith('/'+ref))
essential=['#lizzies_club_ws_mox_reception','#ws_lizzies_default_bouncer_quest_01','#ws_lizzies_default_bouncer_quest_02','#q004_tr_meet_the_lizzies','#tr_lizzies_club_reception','#tr_lizzies_area','#tr_lizzies_club']
bindings={ref:matches(ref) for ref in essential}
assert all(len(v)==1 for v in bindings.values()),bindings
old=read(W/'prealpha/lizzies_lr1/candidate_02/owner_readback_01.json')
triggers=sorted({val(n['triggerAreaRef']) for n in walk(old) if n.get('$type')=='questTriggerCondition'})
assert all(matches(ref) for ref in triggers),triggers
assert not any(n.get('phasePrefabs') or n.get('phaseInstancePrefabs') for n in walk(old)), 'LR1 missing-support diagnosis invalid'
population=[]
source=W/'diagnostics/lizzies_restoration_audit_20261029_01/native/json'
for name in ['lizzies_default.community.json','lizzies_default_after_q105.community.json']:
    obj=read(next(source.rglob(name)))
    spotrefs={val(n) for n in walk(obj) if n.get('$type')=='NodeRef' and n.get('$storage')=='string'}
    usedmarks={val(m) for n in walk(obj) if n.get('$type')=='communityPhaseTimePeriod' for m in n['markings']}
    missingrefs=sorted(r for r in spotrefs if r!='0' and not matches(r))
    missingmarks=sorted(usedmarks-marks)
    # Review all schedules, including those not activated by LR1.
    population.append({'resource':name,'spot_refs':len(spotrefs),'matched_refs':len(spotrefs)-len(missingrefs),'missing_refs':missingrefs,'markings':len(usedmarks),'missing_markings':missingmarks})
    assert not missingrefs and not missingmarks,population[-1]
spawners=[n for n in nodes if n['$type']=='worldPopulationSpawnerNode']
assert len(spawners)==5 and all(n['spawnOnStart']==0 and n['alwaysSpawned'] in ('false_','default__false_') for n in spawners)
conversations=[val(c['Data']['sceneFilename']['DepotPath']) for n in nodes if n['$type']=='worldInterestingConversationsAreaNode' for c in n['conversations']]
assert len(conversations)==11 and all(p.startswith('base\\open_world\\scenes\\conversations\\') for p in conversations)
o=read(C/'owner_readback_01.json'); root=o['Data']['RootChunk']; handles={n['HandleId']:n['Data'] for n in walk(o) if 'HandleId' in n and 'Data' in n}
def deref(h): return h['Data'] if 'Data' in h else handles[h['HandleRefId']]
def edges(g):
    sockets={}
    for h in g['nodes']:
        n=deref(h)
        for sh in n['sockets']:
            sd=deref(sh); sockets[id(sd)]=(n['id'],val(sd['name']))
    result=set()
    for sd_id,owner in sockets.items():
        sd=next(d for d in handles.values() if id(d)==sd_id)
        for ch in sd['connections']:
            c=deref(ch); a=sockets[id(deref(c['source']))]; b=sockets[id(deref(c['destination']))]
            result.add((a[0],a[1],b[0],b[1]))
    return result
g=deref(root['graph']); gn={deref(h)['id']:deref(h) for h in g['nodes']}
assert not root['phasePrefabs'] and not root['inplacePhases']
assert set(gn)=={0,1,2,3}
assert edges(g)=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In1')}
owner=gn[3]; assert owner['$type']=='questPhaseNodeDefinition'
assert len(owner['phaseInstancePrefabs'])==1 and val(owner['phaseInstancePrefabs'][0]['prefabNodeRef'])==full
guard=deref(gn[1]['condition']); assert guard['operation']=='AND'
facts={}
for h in guard['conditions']:
    c=deref(h); assert c['$type']=='questFactsDBCondition'
    f=deref(c['type']); assert f['comparisonType']=='Equal'; facts[f['factName']]=f['value']
expected={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_active':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q305_johnny_scene_active':0,'q115_point_of_no_return':0,'q004_done':1,'q105_01_done':1,'PTFRBASE_Suspended':0,'PTFRLR1_Claimed':1,'PTFRLR2_Claimed':0,'PTFRLR2_Entered':0,'PTFRLR2_Hold':0}
assert facts==expected and len(guard['conditions'])==len(expected)
inner=deref(owner['phaseGraph']); ins={deref(h)['id']:deref(h) for h in inner['nodes']}
assert set(ins)=={0,1,2} and edges(inner)=={(0,'Out',1,'In'),(1,'Out',2,'In')}
hold=deref(deref(ins[2]['condition'])['type']);assert (hold['factName'],hold['value'],hold['comparisonType'])==('PTFRLR2_Hold',1,'Equal')
writes=[n for n in walk(o) if n.get('$type')=='questSetVar_NodeType']
assert {(n['factName'],n['value'],n['setExactValue']) for n in writes}=={('PTFRLR2_Claimed',1,1),('PTFRLR2_Entered',1,1)} and len(writes)==2
allowed={'questInputNodeDefinition','questPauseConditionNodeDefinition','questFactsDBManagerNodeDefinition','questPhaseNodeDefinition'}
assert all(n['$type'] in allowed for n in list(gn.values())+list(ins.values()))
out={'status':'PASS_NATIVE_BINDINGS_AND_SERIALIZED_OWNER','native_sector_nodes':len(nodes),'node_types':dict(counts),'essential_bindings':bindings,'lr1_trigger_bindings':triggers,'community_coverage':population,'inactive_spawners':len(spawners),'ambient_conversation_scenes':conversations,'owner_nodes':7,'owner_edges':5,'guard_facts':facts,'writes':[n['factName'] for n in writes],'root_prefabs':0,'new_population_commands':0,'native_story_writes_in_new_graph':0,'source_proof_sha256':sha(R/'providers_01.json'),'owner_readback_sha256':sha(C/'owner_readback_01.json'),'live_result':'unverified'}
(C/'semantic_verification_01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
