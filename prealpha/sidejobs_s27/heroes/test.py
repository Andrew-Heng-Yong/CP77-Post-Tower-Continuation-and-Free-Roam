"""Source-exact Heroes package branch, service ownership and admission tests."""
import copy,hashlib,json,sys
from pathlib import Path
from inspect import ROOT,read,graphs

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def value(v):return v.get('$value') if isinstance(v,dict) else v
def walk(v):
    if isinstance(v,dict):
        yield v
        for a in v.values():yield from walk(a)
    elif isinstance(v,list):
        for a in v:yield from walk(a)
def evaluate(c,f,j,key_quantity=0,distance=40):
    t=c['$type']
    if t=='questLogicalCondition':
        a=[evaluate(x,f,j,key_quantity,distance) for x in c['conditions']]
        return {'AND':all(a),'OR':any(a),'NOR':not any(a)}[c['operation']]
    if t=='questFactsDBCondition':
        v=c['type'];a=f.get(v['factName']);b=v['value']
        if a is None:return False
        return {'Equal':a==b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[v['comparisonType']]
    if t=='questJournalCondition':
        v=c['type'];p=v['path'];return j.get((p['realPath'],value(p['className'])))==v['state']
    if t=='questObjectCondition':
        v=c['type'];assert v['$type']=='questInventory_ConditionType';assert v['itemID']['hash']==120771320143
        return key_quantity is not None and key_quantity==v['quantity']
    if t=='questDistanceCondition':
        v=c['type'];assert v['comparisonType']=='Greater'
        return distance is not None and distance>v['distanceDefinition2']['distanceValue']
    raise AssertionError(t)

def main():
    build=Path(sys.argv[1]);m=read(build/'component.json');spec=read(ROOT/m['contract']);o=spec['owners'][0]
    checks=positive=negative=0
    for rel,h in m['source_pins'].items():assert sha(ROOT/rel)==h,rel;checks+=1
    assert sha(ROOT/m['contract'])==m['contract_sha256'];checks+=1
    for r in m['resource_details']:
        assert sha(build/r['relative'])==r['sha256'];assert sha(build/r['readback'])==r['readback_sha256'];checks+=2
    for c in m['native_copies']:
        oldgs=graphs(ROOT/(c['source'].replace('/raw/','/json/')+'.json'))
        old=nodes(oldgs[c['source_graph']])[c['source_id']]
        file,gp=c['target_graph'].split('/',1);newgs=graphs(build/'readback'/f'{file}.json');new=nodes(newgs[gp])[c['target_id']]
        exp=copy.deepcopy(old);exp['id']=c['target_id'];assert exp==new,c;checks+=1
        prefix=c['source_graph']+'/'+str(c['source_id'])
        for sub,g in oldgs.items():
            if sub!=prefix and not sub.startswith(prefix+'/'):continue
            target=gp+'/'+str(c['target_id'])+sub[len(prefix):]
            assert newgs[target]['nodes']==g['nodes'];assert edges(newgs[target])==edges(g);checks+=len(g['nodes'])+len(g['edges'])
    b=graphs(build/'readback/heroes_package.json')['root'];bn=nodes(b)
    assert set(bn)=={42,89,119,1000,1001,1002,1003,1004,1005,1006,1007,1008,1010};checks+=1
    expected={(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'Out',89,'In'),(89,'Out',119,'In'),(119,'Out',1004,'In'),(1004,'False',1002,'In'),(1004,'True',1005,'In'),(1005,'Out',1006,'In'),(1006,'Out',1010,'In'),(1010,'Out',42,'In'),(42,'Out2',1007,'In'),(42,'Out1',1008,'In')}
    assert edges(b)==expected;checks+=1
    assert value(bn[42]['phaseResource']['DepotPath'])=='base\\quest\\side_quests\\sq018\\phases\\sq018_00_holocall.questphase';checks+=1
    assert bn[1010]['type']['params'][0]['contact']['realPath']=='contacts/mama_welles';checks+=1
    assert bn[1010]['type']['params'][0]['contact']['fileEntryIndex']==1;checks+=1
    assert bn[1007]['type']['factName']==o['tag']+'_Finished' and bn[1008]['type']['factName']==o['tag']+'_Fault';checks+=1
    # All new writes are owned. Native phase owns its original package, rewards,
    # bike and Mama placement; no q005 outcome changes or journal reactivation.
    assert not any(n['$type']=='questJournalNodeDefinition' for n in b['nodes']);checks+=1
    for n in b['nodes']:
        if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(o['tag']+'_');checks+=1
    assert bn[1003]['condition']['conditions']==[{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS27_PHONE_MAMA_Issued','value':1}}];checks+=1
    native=graphs(ROOT/(o['native_only_checks'][0]['source'].replace('/raw/','/json/')+'.json'))
    inv=copy.deepcopy(nodes(native['root/47'])[5]['condition']);inv['type']['quantity']=0
    olddefault=graphs(ROOT/(o['service_source'].replace('/raw/','/json/')+'.json'))
    dist=nodes(olddefault['root/7/27/3/16'])[58]['condition']['conditions'][0]
    facts=spec['common_equal']|o['facts_equal']|{k:v['min'] for k,v in o['fact_ranges'].items()}|{o['tag']+'_Permit':1,o['tag']+'_Issued':0,o['tag']+'_Finished':0,o['tag']+'_Fault':0,'PTFRS27_PHONE_MAMA_Issued':1}
    journal={(j['path'],j['class']):'Inactive' for j in o['journals']}
    assert len([j for j in o['journals'] if j['class']=='gameJournalQuest'])==1;checks+=1
    assert o['facts_equal']['q005_jackie_to_mama']==o['facts_equal']['q005_jackie_stay_notell']==o['facts_equal']['sq018_done']==0;checks+=1
    for id in (1002,1004):
        cond=bn[id]['condition'];assert cond['conditions'][-2:]==[inv,dist];checks+=1
        assert evaluate(cond,facts,journal);positive+=1
        for name,num in facts.items():
            bounds=o['fact_ranges'].get(name);bad=[bounds['min']-1,bounds['max']+1] if bounds else [num-1,num+1]
            for v in bad:assert not evaluate(cond,facts|{name:v},journal),(id,name,v);negative+=1
            ff=facts.copy();del ff[name];assert not evaluate(cond,ff,journal);negative+=1
        for k in journal:
            for state in ('Active','Succeeded','Failed',None):assert not evaluate(cond,facts,journal|{k:state}),(id,k,state);negative+=1
        for quantity in (-1,1,2,None):assert not evaluate(cond,facts,journal,key_quantity=quantity);negative+=1
        for distance in (-1,0,29,30,None):assert not evaluate(cond,facts,journal,distance=distance);negative+=1
        # Historical phone counters cannot prevent a fresh route or be zeroed.
        assert evaluate(cond,facts|{'holo_mama_welles_calls_v_start_count':7,'holo_mama_welles_calls_v_end_count':2},journal);positive+=1
    capture=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')['second']['jobs']
    job=next(x for x in capture if x['id']==o['id'])
    jf=journal|{(j['path'],j['class']):j['state'] for j in job['journals']}
    assert not evaluate(bn[1004]['condition'],facts|job['facts'],jf);negative+=1
    # Source proves the original package route completes internally and never
    # enters funeral/storage. q005 choice condition remains unmodified there.
    nn=nodes(native['root']);assert {(64,'True',68,'In2'),(68,'Out1',75,'In'),(75,'Out',76,'In'),(76,'Out',41,'Succeeded'),(41,'Out',20,'In'),(30,'Out',19,'In'),(23,'Out',69,'In')}<=edges(native['root']);checks+=1
    assert nn[69]['$type']=='questOutputNodeDefinition';assert value(nn[69]['socketName'])=='Out2';checks+=1
    package=nodes(native['root/47']);assert package[5]['condition']['type']['quantity']==1;checks+=1
    # Mama service receives no input until this package owner finished. Its
    # original interaction/reset/phone lifecycle remains completely unchanged.
    sg=graphs(build/'readback/mama_default.json')['root'];sn=nodes(sg)
    assert set(sn)=={16,17,1000,1001,1002,1003};checks+=1
    assert edges(sg)=={(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'Out',16,'In'),(16,'Out',17,'In1'),(17,'Out1',16,'In')};checks+=1
    sf=spec['common_equal']|{o['tag']+'_Issued':1,o['tag']+'_Finished':1,o['tag']+'_Fault':0,'PTFRS27_PHONE_MAMA_Issued':1,'PTFRS27_HEROES_MAMA_Issued':0}
    assert evaluate(sn[1002]['condition'],sf,{});positive+=1
    for k,v in sf.items():
        for x in (v-1,v+1,None):assert not evaluate(sn[1002]['condition'],sf|{k:x},{});negative+=1
    for dep,r in m['native_resources'].items():assert sha(ROOT/r['raw'])==r['raw_sha256'];assert sha(ROOT/r['json'])==r['json_sha256'];checks+=2
    assert len(m['resources'])==2 and len(m['boots'])==2 and not m['override_donors'];checks+=1
    result={'status':'PASS_COMPONENT_NOT_LIVE','component_sha256':sha(build/'component.json'),'contract_sha256':sha(ROOT/m['contract']),'tester_sha256':sha(Path(__file__)),'native_payload_checks':checks,'policy_cases':positive+negative,'positive_policy_cases':positive,'negative_policy_cases':negative,'owners':1,'roots':1,'resources':2,'native_progress_resets':False,'game_writes':False,'scope':'Fresh original package-only outcome. Completed/Failed/progressed and funeral outcomes defer. Does not implement requested unfinished restart policy.','pending':['Native package/call/SMS/reward/Mama interaction on genuinely fresh branch','H10 package streaming/physical pickup after apartment repurchase policy','Cold reload and original bike variant/reward once','Aggregate official bytes, dependency closure, metadata and deployment audits']}
    dest=build/'tests.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
