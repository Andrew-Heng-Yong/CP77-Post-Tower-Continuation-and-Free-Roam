"""Independent BA1 payload, exact guard, migration and negative-control review."""
import copy, hashlib, itertools, json
from pathlib import Path
H=Path(__file__).resolve().parent
W=H.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(v,path='$'):
    yield path,v
    if isinstance(v,dict):
        for k,x in v.items():yield from walk(x,path+'.'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):yield from walk(x,path+f'[{i}]')
def handles(d):return {v['HandleId']:v['Data'] for _,v in walk(d) if isinstance(v,dict) and 'HandleId' in v and 'Data' in v}
def norm(v,hs):
    if isinstance(v,dict):
        if 'HandleRefId' in v and len(v)==1:return norm(hs[v['HandleRefId']],hs)
        if 'HandleId' in v and 'Data' in v:return norm(v['Data'],hs)
        return {k:norm(x,hs) for k,x in v.items() if k not in ('sockets','HandleId','HandleRefId')}
    if isinstance(v,list):return [norm(x,hs) for x in v]
    return v
def node(g,n):return next(h['Data'] for h in g['nodes'] if h.get('Data',{}).get('id')==n)
checks=[]
def check(ok,label):
    assert ok,label
    checks.append(label)
n=read(H/'fresh_native_01.json');c=read(H/'fresh_candidate_01.json')
nh,ch=handles(n),handles(c)
ng=n['Data']['RootChunk']['graph']['Data'];cg=c['Data']['RootChunk']['graph']['Data']
n14=node(node(ng,28)['phaseGraph']['Data'],14)
n61=node(n14['phaseGraph']['Data'],61)
loop=node(cg,10)['phaseGraph']['Data'];c61=node(loop,61)
canonical_native=norm(n61,nh);canonical_candidate=norm(c61,ch)
full='$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/cs_goons_shooting_openworld_002_prefabPFINICQ/cs_goons_shooting_com;#ce_pac_cvi_112_com'
changes=[]
def qualify(v,path='$'):
    if isinstance(v,dict):
        if v.get('$type')=='NodeRef' and v.get('$value')=='#ce_pac_cvi_112_com':
            changes.append(path);v['$value']=full
        for k,x in v.items():qualify(x,path+'.'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):qualify(x,path+f'[{i}]')
expected=copy.deepcopy(canonical_native);qualify(expected)
check(len(changes)==10,'Exactly ten native community references qualified')
check(expected==canonical_candidate,'All controller payloads exact except ten community references')
fresh=read(H/'fresh_graph_proof_01.json')
check(fresh['nodes']==32 and fresh['edges']==43,'All32nodes43edges freshly compared against current native source')
check(fresh['community_hash']=='8640981183263935109','Fully qualified community resolves exact captured spawner hash')
check(fresh['candidate_sha256']=='F7B56384298F4FAEF2BE844AD0CC86B24A2A45520430C7748F3D045DFADA0334','Candidate binary pin')
check(norm(node(cg,12),ch)['permanent']==0,'External whole-loop cut is nonpermanent for rearm')
check(canonical_candidate['phaseGraph']['nodes'][1]['type']=='Terminating','Native NotReady output terminates native controller')

eligibility={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_active':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'PTFRBASE_Suspended':0,'q305_johnny_scene_active':0,'q115_point_of_no_return':0,'q000_done':1,'PTFRWW2_179_Claimed':1,'PTFRWW2_179_Entered':1,'PTFRWW2_179_Hold':0}
admit=norm(node(cg,2)['condition'],ch);invalid=norm(node(cg,11)['condition'],ch)
rearm=norm(node(cg,15)['condition'],ch);loopguard=norm(node(loop,2)['condition'],ch)
def leaves(cond):
    return [v for _,v in walk(cond) if isinstance(v,dict) and v.get('$type')=='questVarComparison_ConditionType']
def evaluate(cond,facts,ready):
    t=cond['$type']
    if t=='questLogicalCondition':
        a=[evaluate(x,facts,ready) for x in cond['conditions']]
        assert cond['operation'] in ('AND','OR')
        return all(a) if cond['operation']=='AND' else any(a)
    if t=='questFactsDBCondition':
        d=cond['type'];a=facts.get(d['factName'],0);b=d['value']
        assert d['comparisonType'] in ('Equal','NotEqual')
        return (a==b) if d['comparisonType']=='Equal' else (a!=b)
    if t=='questSpawnerCondition':
        assert cond['type']['$type']=='questSpawnerReady_ConditionType'
        assert cond['type']['spawnerReference']['$value']==full
        assert cond['type']['communityEntryNames']==[]
        return ready
    raise AssertionError(t)
def flat(cond):
    return {x['factName']:(x['comparisonType'],x['value']) for x in leaves(cond)}
eq={k:('Equal',v) for k,v in eligibility.items()}
ne={k:('NotEqual',v) for k,v in eligibility.items()}
check(flat(admit)=={**eq,'PTFRBA1_Claimed':('Equal',0)},'Admission exact fifteen safety/support guards plus own unclaimed guard')
check(flat(invalid)==ne and invalid['operation']=='OR','Loss monitor exact inverse of every safety/support guard')
check(flat(rearm)==eq,'Suspension rearm checks all fifteen safety/support facts and no new claim')
check(flat(loopguard)==eq,'Native NotReady rearm checks all fifteen safety/support facts')
check(len([v for _,v in walk(loopguard) if isinstance(v,dict) and v.get('$type')=='questSpawnerReady_ConditionType'])==1,'Every controller entry additionally waits native Ready')
cases=0
for bits in itertools.product([0,1],repeat=15):
    f=dict(zip(eligibility,bits));expected_valid=all(f[k]==v for k,v in eligibility.items())
    assert evaluate(admit,f,False)==expected_valid
    assert evaluate(invalid,f,False)==(not expected_valid)
    assert evaluate(rearm,f,False)==expected_valid
    assert evaluate(loopguard,f,True)==expected_valid
    assert not evaluate(loopguard,f,False)
    assert not evaluate(admit,{**f,'PTFRBA1_Claimed':1},True)
    cases+=1
check(cases==32768,'Exhaustive32768 boolean states pass admission/inverse/rearm/Ready/duplicate conditions')
for k,v in eligibility.items():
    f={**eligibility,k:2}
    check(not evaluate(admit,f,True) and evaluate(invalid,f,True) and not evaluate(rearm,f,True) and not evaluate(loopguard,f,True),'Reject nonboolean unexpected state '+k)
check(evaluate(admit,eligibility,False),'Saved W3 Claimed1 Entered1 Hold0 admits new action owner while community unloaded')
check(not evaluate(loopguard,eligibility,False),'Unloaded saved W3 state cannot dispatch native action')
check(evaluate(loopguard,{**eligibility,'PTFRBA1_Claimed':1},True),'Persisted new claim permits internal reload/rearm without claim reset')

root_expected={'0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.Out -> 4.In','4.Out -> 5.In','5.Out -> 10.In1','5.Out -> 11.In','11.Out -> 12.In','12.CutSource -> 10.CutDestination','12.Out -> 13.In','13.Out -> 14.In','14.Out -> 15.In','15.Out -> 16.In','16.Out -> 5.In'}
loop_expected={'0.Out -> 2.In','2.Out -> 3.In','3.Out -> 61.In1','61.Out1 -> 4.In','4.Out -> 2.In'}
check(set(fresh['root_edges'])==root_expected and len(fresh['root_edges'])==len(root_expected),'Root topology exact: claim once, watch loss, cut whole wrapper, acknowledge suspension, rearm')
check(set(fresh['loop_edges'])==loop_expected and len(fresh['loop_edges'])==len(loop_expected),'Native termination rechecks eligibility and Ready before re-entry')
check(not any(e.startswith('10.') for e in fresh['root_edges']),'Lifecycle cannot bypass suspension via an outer natural output')
check(len(loop['nodes'])==5,'Cut wrapper contains both pending Ready gate and active native controller')
normroot=norm(c['Data']['RootChunk'],ch)
types=[v['$type'] for _,v in walk(normroot) if isinstance(v,dict) and '$type' in v]
check('questSpawnManagerNodeDefinition' not in types and 'questCommunityTemplate_NodeType' not in types,'No spawn/reactivate/reset-kill-count operations')
check(all(not v for p,v in walk(normroot) if p.endswith('.phaseInstancePrefabs')),'Action owner owns no prefab')
writers=[v for _,v in walk(normroot) if isinstance(v,dict) and v.get('$type')=='questSetVar_NodeType']
check(all(v['factName'].startswith('PTFRBA1_') for v in writers),'No native/W3 fact writes')
check({v['factName'] for v in writers}=={'PTFRBA1_Ready','PTFRBA1_Claimed','PTFRBA1_Entered','PTFRBA1_Active','PTFRBA1_Suspended'},'Only five documented new receipt facts are written')
check([v['value'] for v in writers if v['factName']=='PTFRBA1_Claimed']==[1],'New owner claim never cleared')
check(all(v['setExactValue']==1 for v in writers),'Receipt assignments are exact, not accumulating')
negative=[]
bad=copy.deepcopy(canonical_candidate);bad['phaseGraph']['nodes'][9]['params']['duration']=1
negative.append(('native payload change detected',bad!=expected))
negative.append(('missing whole-wrapper cut detected',(set(fresh['root_edges'])-{'12.CutSource -> 10.CutDestination'})!=root_expected))
bad=copy.deepcopy(admit);bad['conditions']=[x for x in bad['conditions'] if x.get('type',{}).get('factName')!='PTFRBA1_Claimed']
negative.append(('removed duplicate guard admits alreadyclaimed fixture',evaluate(bad,{**eligibility,'PTFRBA1_Claimed':1},True)))
bad=copy.deepcopy(loopguard);bad['conditions']=[x for x in bad['conditions'] if x['$type']!='questSpawnerCondition']
negative.append(('removed Ready guard admits unloaded fixture',evaluate(bad,eligibility,False)))
bad=copy.deepcopy(invalid);bad['conditions']=[x for x in bad['conditions'] if x['type']['factName']!='PTFRWW2_179_Hold']
negative.append(('missing Hold-loss guard misses suspension fixture',not evaluate(bad,{**eligibility,'PTFRWW2_179_Hold':1},True)))
for label,ok in negative:check(ok,'Negative control: '+label)
result={'status':'PASS_BA1_INDEPENDENT_NATIVE_PAYLOAD_AND_GUARDS_STATIC_ONLY','checks':len(checks),'assertions':checks,'exhaustive_guard_cases':cases,'negative_controls':len(negative),'controller_nodes':32,'controller_edges':43,'community_ref_changes':changes,'candidate_sha256':fresh['candidate_sha256'],'game_writes':0,'save_writes':0,'limits':['Target/security default-world ownership must be established by world review.','No live game execution; saved quest-graph/AI-command serialization remains engine-dependent and live unverified.','Speech origin is unbound; this validates the native shooting controller only.'],'pins':[{'path':str(p),'sha256':sha(p)} for p in (H/'fresh_native_01.json',H/'fresh_candidate_01.json',H/'fresh_graph_proof_01.json',H/'verify_graphs_01.ps1',Path(__file__))]}
(H/'assessment_01.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','checks','exhaustive_guard_cases','negative_controls','candidate_sha256')},indent=2))
