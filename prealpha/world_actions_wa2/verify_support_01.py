"""Verify cooked support graph, saved-claim gates and append-only driver change."""
import copy,hashlib,itertools,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
prefix='PTFRWW2_250_'
want={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_active':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'PTFRBASE_Suspended':0,'q305_johnny_scene_active':0,'q115_point_of_no_return':0,'q000_done':1,prefix+'Request':1,prefix+'Claimed':0,prefix+'Entered':0,prefix+'Hold':0}
prefab=read(H/'coverage_review/support_assessment_01.json')['candidate250']['prefab']
def validate(doc):
    hs={str(v['HandleId']):v['Data'] for v in walk(doc) if 'HandleId' in v and isinstance(v.get('Data'),dict)}
    def deref(v):return v.get('Data',hs.get(str(v.get('HandleRefId')),v))
    def nodes(g):return {n['id']:n for n in map(deref,g['nodes'])}
    def edges(g):
        nd=nodes(g);ss={}
        for n in nd.values():
            for h in n['sockets']:
                o=deref(h);ss[id(o)]=(n['id'],o['name']['$value'])
        result=set()
        for n in nd.values():
            for sk in map(deref,n['sockets']):
                for cn in map(deref,sk['connections']):result.add((*ss[id(deref(cn['source']))],*ss[id(deref(cn['destination']))]))
        return result
    root=doc['Data']['RootChunk'];g=deref(root['graph']);n=nodes(g)
    assert set(n)=={0,100,101,102,103,104,105}
    assert edges(g)=={(0,'Out',100,'In'),(100,'Out',101,'In'),(101,'Out',102,'In'),(102,'Out',103,'In'),(103,'Out',104,'In'),(104,'Out',105,'In1')}
    cond=deref(n[101]['condition']);assert cond['$type']=='questLogicalCondition' and cond['operation']=='AND'
    tests=[v for v in walk(cond) if 'comparisonType' in v]
    assert len(tests)==16 and all(v['comparisonType']=='Equal' for v in tests)
    assert {v['factName']:v['value'] for v in tests}==want
    owner=n[105];assert owner['phaseInstancePrefabs']==[{'$type':'questQuestPrefabEntry','prefabNodeRef':{'$type':'NodeRef','$storage':'string','$value':prefab}}]
    inn=deref(owner['phaseGraph']);ins=nodes(inn);assert set(ins)=={0,1,2}
    assert edges(inn)=={(0,'Out',1,'In'),(1,'Out',2,'In')}
    hold=[v for v in walk(deref(ins[2]['condition'])) if 'comparisonType' in v]
    assert [(v['factName'],v['value'],v['comparisonType']) for v in hold]==[(prefix+'Hold',1,'Equal')]
    writers=[v for v in walk(doc) if v.get('$type')=='questSetVar_NodeType']
    assert sorted((v['factName'],v['value']) for v in writers)==sorted([(prefix+'Ready',1),(prefix+'Claimed',1),(prefix+'Request',0),(prefix+'Ready',0),(prefix+'Entered',1)])
    assert all(v['setExactValue']==1 for v in writers)
    forbidden={'questSpawnManagerNodeDefinition','questCommunityTemplate_NodeType','questSceneNodeDefinition','questPuppetAIManagerNodeDefinition','questOutputNodeDefinition','questCombatNodeDefinition','questMovePuppetNodeDefinition','questWorldDataManagerNodeDefinition'}
    assert not any(v.get('$type') in forbidden for v in walk(doc))
    assert not root.get('phasePrefabs') and not root.get('inplacePhases') and not doc['Data'].get('EmbeddedFiles')
    return tests
doc=read(C/'support_owner_readback_01.json');tests=validate(doc)
accepts=0
for values in itertools.product((0,1),repeat=16):
    state=dict(zip(want,values))
    accepted=all(state[t['factName']]==t['value'] for t in tests)
    expected=state==want
    assert accepted==expected
    accepts+=accepted
assert accepts==1
negative=[]
for fact in [prefix+'Claimed',prefix+'Entered','q307_done']:
    mutated=copy.deepcopy(doc)
    t=next(v for v in walk(mutated) if v.get('factName')==fact and 'comparisonType' in v);t['value']=1-t['value']
    try:validate(mutated)
    except AssertionError:negative.append('flipped_gate_'+fact)
    else:raise AssertionError('Negative control accepted '+fact)
mutated=copy.deepcopy(doc);next(v for v in walk(mutated) if v.get('$type')=='questSetVar_NodeType')['factName']='q307_done'
try:validate(mutated)
except AssertionError:negative.append('native_fact_writer')
else:raise AssertionError('Native writer negative control accepted')

build=read(C/'script_source/support_build_01.json');candidate=Path(build['candidate']);old=Path(build['source'])
assert sha(candidate)==build['candidate_sha256'] and sha(old)==build['original_sha256']
oldbytes=old.read_bytes();new=candidate.read_bytes();nl=b'\r\n' if b'\r\n' in oldbytes else b'\n'
lines=new.splitlines(keepends=True);ids=[i for i,l in enumerate(lines) if b'g.id = 250; g.prefix = "PTFRWW2_250_"' in l]
assert len(ids)==1;i=ids[0];insert=b''.join(lines[i:i+3]);assert b'3323904054656225535ul' in insert and build['new_group']['community_ref'].encode() in insert
assert new.replace(insert,b'',1)==oldbytes
oldids=re.findall(rb'g\.id = (\d+); g\.prefix = "([^"]+)";',oldbytes)
newids=re.findall(rb'g\.id = (\d+); g\.prefix = "([^"]+)";',new)
assert newids==oldids+[(b'250',b'PTFRWW2_250_')] and len(oldids)==237
assert b's.settled >= 2' in oldbytes or b'sample.settled >= 2' in oldbytes
compile=read(C/'compile_01/result.json');assert compile['status']=='PASS' and compile['source_count']==64 and compile['candidate_sha256']==sha(candidate)
resource=C/'source/towercontinued/world_actions_wa2/group250_support.questphase'
proof=read(C/'support_owner_proof_01.json');assert sha(resource)==proof['sha256']
result={'status':'PASS_GROUP250_SUPPORT_GRAPH_AND_APPEND_ONLY_ADMISSION','guards':16,'guard_states':65536,'accepting_guard_states':1,
 'negative_controls_rejected':negative,'outer_nodes':7,'inner_nodes':3,'edges':8,'new_support_owners':1,'previous_owners_unchanged':237,
 'driver_change':'exact3line appended mapping only; all existing actor identity, active-entry, two settled samples, safety and persistent claim logic byte-identical',
 'persistent_schema_changes':0,'receipt_resets':0,'native_fact_writers':0,'native_spawn_or_AI_actions':0,
 'resource':str(resource),'resource_sha256':sha(resource),'candidate_sha256':sha(candidate),'fresh_compile_sources':64,
 'readback_sha256':sha(C/'support_owner_readback_01.json'),'game_writes':0,'save_writes':0}
dest=C/'support_validation_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
