"""Prove the bounded after-introduction MQ025 route against original resources."""
import json,sys,hashlib,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from audit import graphs

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def nm(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def ev(c,f,j):
    if c['$type']=='questLogicalCondition':
        parts=[ev(x,f,j) for x in c['conditions']]
        return all(parts) if c['operation']=='AND' else any(parts)
    t=c['type']
    if c['$type']=='questJournalCondition':return j.get(t['path']['realPath'])==t['state']
    assert c['$type']=='questFactsDBCondition' and t['comparisonType']=='Equal'
    return f.get(t['factName'])==t['value']

def verify(out):
    spec=load(HERE/'contract.json');m=load(out/'manifest.json');checks=cases=0
    for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
    assert sha(out/'mq025_progress.questphase')==m['raw_sha256']
    original={g['path']:g for g in graphs(ROOT/(spec['native_source'].replace('/raw/','/json/')+'.json'))}
    actual={g['path']:g for g in graphs(out/'mq025_progress.json')}
    a=nm(actual['root']);o=nm(original['root']);ids=spec['selected_nodes']
    assert set(a)==set(ids)|set(range(1000,1010))
    for i in ids:assert a[i]==o[i],('native payload drift',i);checks+=1
    for path,g in original.items():
        if path!='root' and int(path.split('/')[1]) in ids:assert actual[path]==g,path;checks+=len(g['nodes'])
    assert set(actual)=={'root'}|{p for p in original if p!='root' and int(p.split('/')[1]) in ids}
    expected={e for e in edges(original['root']) if e[0] in ids and e[2] in ids and e[0]!=0 and e!=(25,'Out1',1,'In')}
    expected|={(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'True',1003,'In'),(1002,'False',1005,'In'),(1003,'Out',1006,'Active'),(1006,'Out',1007,'Active'),(1007,'Out',1008,'In'),(1008,'Out',1009,'In'),(1009,'True',55,'In1'),(1009,'False',1005,'In'),(25,'Out1',1004,'In'),(1004,'Out',1,'In')}
    assert edges(actual['root'])==expected
    # Post-tease hub preserves the stock native continuation, not In1 tutorial.
    assert (2,'Out1',55,'In1') in edges(original['root'])
    assert not {2,17,30,37,38,46,65,68,69,70}&set(a)
    for i,suffix in [(1000,'Ready'),(1003,'Issued'),(1004,'Finished'),(1005,'Refused')]:
        assert a[i]['type']=={'$type':'questSetVar_NodeType','factName':spec['tag']+'_'+suffix,'setExactValue':1,'value':1};checks+=1
    for i,j in zip([1006,1007],spec['journal_writes']):
        t=a[i]['type'];assert t['path']['realPath']==j['path'] and t['path']['className']['$value']==j['class']
        assert t['sendNotification']==0 and t['trackQuest']==0;checks+=1
        assert set(t)=={'$type','optional','path','sendNotification','trackQuest','version'}
    # Every graph writer added belongs to this owner. No reset of native facts.
    assert not spec['native_fact_writes_added']
    assert a[1001]['condition']==a[1002]['condition'] and a[1008]['condition']==a[1009]['condition']
    guard=a[1001]['condition'];ack=a[1008]['condition']
    f=m['guard_equal'];j={row['path']:row['states'][0] for row in spec['journals']}
    assert ev(guard,f,j);cases+=1
    factterms={c['type']['factName']:c['type']['value'] for c in guard['conditions'] if c['$type']=='questFactsDBCondition'}
    assert factterms==f
    for k,v in f.items():
        for wrong in [-1,0,1,2,None,999]:
            if wrong!=v:assert not ev(guard,f|{k:wrong},j),(k,wrong);cases+=1
    for row in spec['journals']:
        for state in [None,'Inactive','Active','Failed','Succeeded','Unknown']:
            state_expected=state in row['states'];assert ev(guard,f,j|{row['path']:state})==state_expected,(row['path'],state);cases+=1
    # No permit dependency after issue; the native journal acknowledgement is
    # independent of the script's now-ChangedState/Issued state.
    af=f|{spec['tag']+'_Issued':1,spec['tag']+'_Permit':0}
    aj=j|{x['path']:'Active' for x in spec['journal_writes']}
    assert ev(ack,af,aj) and not ev(guard,af,aj);cases+=2
    for row in spec['journal_writes']:
        for wrong in [None,'Inactive','Failed','Succeeded','Unknown']:
            assert not ev(ack,af,aj|{row['path']:wrong});cases+=1
    for row in spec['journals'][7:]:
        assert not ev(ack,af,aj|{row['path']:'Succeeded'});cases+=1
    # Existing stock gates and parallel completion signals remain exact.
    assert o[24]['condition']['type']['factName']=='mq035_done'
    assert o[31]['condition']['type']['days']==1 and o[31]['condition']['type']['hours']==3
    assert {(3,'Out1',10,'In1'),(5,'Out1',10,'In2'),(7,'Out1',10,'In3'),(9,'Out1',10,'In4'),(10,'Out1',11,'In1')}<=expected
    assert (8,'Cleanup',25,'In2') in expected and (11,'Out1',25,'In1') in expected
    checks+=8
    # Bound the immediate four native prefixes before any spatial encounter.
    prefixes={
      'mq025_02_kabuki':([0,13,131,120,69],13,'mq025_02_kabuki_active',120),
      'mq025_03_arroyo':([26,5,105,99,39],5,'mq025_03_arroyo_active',99),
      'mq025_05_glen':([0,94,4,89,38],4,'mq025_05_glen_active',89),
      'mq025_07_fight_club':([0,70,69,37,30],37,'mq025_07_fight_club',69),
    }
    prefix_report=[]
    base=ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq025/phases'
    for name,(seq,setter,fact,objective) in prefixes.items():
        gs={g['path']:g for g in graphs(base/(name+'.questphase.json'))};g=gs['root'];n=nm(g)
        for src,dst in zip(seq,seq[1:]):assert any(e[0]==src and e[2]==dst for e in edges(g)),(name,src,dst)
        assert n[setter]['type']=={'$type':'questSetVar_NodeType','factName':fact,'setExactValue':1,'value':1}
        assert n[objective]['type']['path']['realPath'].startswith(spec['root']+'/find_fights/')
        assert all(n[i]['$type'] not in ['questRewardManagerNodeDefinition','questItemManagerNodeDefinition','questSceneNodeDefinition'] for i in seq)
        if name.endswith('fight_club'):
            child=gs['root/30'];assert (0,'Out',37,'In') in edges(child)
            assert nm(child)[37]['condition']['$type']=='questTriggerCondition'
            assert n[38]['condition']['type']['factName']=='wwd_05_done' and spec['fact_equal']['wwd_05_done']==0
        else:assert n[seq[-1]]['condition']['$type']=='questTriggerCondition'
        prefix_report.append({'native':name,'prefix':seq,'native_exact_active_setter':fact,'encounter_gate':'spatial trigger','added_payouts':0});checks+=len(seq)+3
    # Native scenes are untouched; actual Johnny records fit unchanged JV1.
    scene_manifest=load(ROOT/'research/sidejobs_s22/boxing/native_02/manifest.json')
    johnny=[];rewards=[]
    def walk(x):
        if isinstance(x,dict):
            yield x
            for v in x.values():yield from walk(v)
        elif isinstance(x,list):
            for v in x:yield from walk(v)
    for row in scene_manifest['scenes']:
        assert sha(Path(row['raw']))==row['sha256'] and sha(Path(row['json']))==row['json_sha256']
        obj=load(Path(row['json']));allrows=list(walk(obj))
        if any(x.get('$value')=='Character.Silverhand' for x in allrows):johnny.append(row['depot'])
        rewards.extend({'scene':row['depot'],'reward':x.get('reward',x.get('rewardName',x))} for x in allrows if x.get('$type')=='questGiveReward_NodeType')
    assert len(scene_manifest['scenes'])==6 and len(johnny)==2
    result={'status':'PASS_OFFLINE_NOT_LIVE','checks':checks,'policy_cases':cases,'native_payloads_checked':len(ids)+sum(len(g['nodes']) for p,g in original.items() if p!='root' and int(p.split('/')[1]) in ids),'prefixes':prefix_report,'johnny_original_scenes':johnny,'native_scene_reward_nodes':len(rewards),'scope':'One intro-completed/no-bout progress-preserving family route. No failed-child, won-bout or mid-bout migration. No archive packing, installation or live verification by this test.','test_sha256':sha(Path(__file__))}
    dest=out/'tests.json'
    if dest.exists():raise RuntimeError('Immutable evidence exists')
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]))))
