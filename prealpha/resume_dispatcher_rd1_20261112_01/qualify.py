"""Independent serialized-graph diff and bounded state-contract fixtures.

Does not claim engine execution. The graph-condition evaluator consumes readback
exports, not the builder's object graph. Save-derived fixtures explicitly supply
inventory/safety/continuation doubles; they are not live save tests.
"""
import argparse
from copy import deepcopy
import json
import re
import sqlite3
import sys
from common import HERE, ROOT, REGISTRY, RED_DIR, HISTORY, baseline, read, sha, write
sys.path.insert(0,str(REGISTRY.parent.parent))
from model import normalize, load_export, reachable, walk

NATIVE=HERE/'archive_04'
CANDIDATE=HERE/'candidate_04'
checks=[]
fixtures=[]


def check(name, condition):
    assert condition,name
    checks.append(name)


def graph(model,path='root'):
    return next(g for g in model['graphs'] if g['path']==path)


def nodes(g):return {n['id']:n for n in g['nodes']}
def clean_node(n):return {k:v for k,v in n.items() if k!='from_any_input'}
def params(g,i):return nodes(g)[i]['parameters']


def renamed(value):
    if isinstance(value,str):return value.replace('PTFRS23_MQ007_RESUME','PTFRRD1_MQ007_DELIVERY')
    if isinstance(value,list):return [renamed(x) for x in value]
    if isinstance(value,dict):return {k:renamed(v) for k,v in value.items()}
    return value


def condition(c, state):
    kind=c['$type']
    if kind=='questLogicalCondition':
        values=[condition(x,state) for x in c['conditions']]
        assert c['operation'] in ('AND','OR')
        return all(values) if c['operation']=='AND' else any(values)
    if kind=='questFactsDBCondition':
        t=c['type'];assert t['$type']=='questVarComparison_ConditionType'
        a,b=state['facts'].get(t['factName'],0),t['value']
        return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[t['comparisonType']]
    if kind=='questJournalCondition':
        t=c['type'];assert t['$type']=='questJournalEntryState_ConditionType'
        match=state['journals'].get(t['path']['realPath'],1)=={'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}[t['state']]
        return not match if t.get('inverted') else match
    if kind=='questObjectCondition':
        t=c['type'];assert t['$type']=='questInventory_ConditionType' and t['itemID']['$value']=='Items.mq007_skippy'
        return state['item']==t['quantity'] if t['comparisonType']=='Equal' else state['item']>=t['quantity']
    if kind=='questTriggerCondition':
        assert c['type']=='IsOutside'
        return state['outside']
    if kind=='questTimeCondition':
        assert c['type']=={'$type':'questRealtimeDelay_ConditionType','hours':0,'miliseconds':100,'minutes':0,'seconds':0}
        return True  # explicit completed 100 ms delay double, not timing evidence
    raise AssertionError(('unmodeled guard condition',kind))


def source_decision(source, **values):
    """Execute only the actual policy's ordered, side-effect-free return clauses."""
    body=source.split('public static func Decide(',1)[1].split('public static func HistoryAdmits',1)[0]
    rules=re.findall(r'if ([^\n{]+) \{ return ResumeDecisionRD1\.(\w+); \}',body)
    assert len(rules)==8
    for expr,result in rules:
        expr=expr.replace('&&',' and ').replace('||',' or ')
        expr=re.sub(r'!(?!=)',' not ',expr)
        if eval(expr,{'__builtins__':{}},values):return result
    assert 'return ResumeDecisionRD1.Defer;' in body
    return 'Defer'


def historical(row):
    return {'valid':row['stable'],'journals':dict(zip((j[0] for j in row['definition']['journals']),row['states'])),
        'facts':dict(zip(row['definition']['fact_names'],row['facts'])),
        'counters':dict(zip((j[0] for j in row['definition']['journals']),row['counters']))}


def contract_accept(c,h,s):
    if not h['valid'] or not s['settled']:return False
    for j in c['journals']:
        if h['journals'].get(j['path'],-1) not in j['history'] or s['journals'].get(j['path'],-1) not in j['live']:return False
        if j['class']=='gameJournalQuestObjective' and (h['counters'].get(j['path'],-1)!=0 or s['counters'].get(j['path'],-1)!=0):return False
    for k,v in c['fixed_facts'].items():
        if h['facts'].get(k,-999)!=v or s['facts'].get(k,0)!=v:return False
    for k in c['choice_facts']:
        if h['facts'].get(k,-999) not in (0,1) or s['facts'].get(k,0)!=h['facts'][k]:return False
    for k in c['counter_facts']:
        if h['facts'].get(k,-1)<0 or s['facts'].get(k,0)<h['facts'][k]:return False
    if any(s['facts'].get(k,0)!=v for k,v in c['live_only_facts'].items()):return False
    if any(s['facts'].get(k,0)!=0 for k in c['other_owner_receipts']+c['own_receipts']):return False
    if c['item'] and s['item']!=1:return False
    for tag in c['handoff']:
        f=s['facts']
        if not (f.get(tag+'_Stopped',0)==1 or (all(f.get(tag+'_'+k,0)==0 for k in ('Claimed','Entered','Request')) and f.get(tag+'_Stop',0)==1)):return False
    return True


def common_fixture(row,save):
    h=historical(row)
    s={'journals':{j[0]:1 for j in row['definition']['journals']},'facts':{k:(v or 0) for k,v in save['facts'].items()},
       'counters':deepcopy(h['counters']),'item':1,'outside':True,'settled':True}
    s['journals'].update({j['path']:j['state_u32'] for j in save['journals']})
    # Explicit doubles. These values are not represented as observations of the save.
    s['facts'].update({k:1 for k in ('PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','PTFRU9_Support_Issued')})
    s['facts'].update({k:(v or 0) for k,v in read(HERE/'fixture_prerequisites_01.json')['facts'].items()})
    for tag in ('PTFRSKIP_Ambient','PTFRSKIP_SC3'):s['facts'][tag+'_Stop']=1
    return h,s


def admission_route(g,s,stop):
    """Execute boot admission only; phases/scenes/engine scheduling are out of scope."""
    state=deepcopy(s);todo=[(0,'In')];seen=[];entered=[]
    while todo:
        assert len(seen)<100,'admission loop'
        i,socket=todo.pop(0);seen.append(i);n=params(g,i);kind=n['$type']
        if i==stop:entered.append(i);continue
        if i in (1010,1200):continue  # separate completion/follow-up owners
        output='Out'
        if kind=='questFactsDBManagerNodeDefinition':
            t=n['type'];assert t['$type']=='questSetVar_NodeType' and t['setExactValue']==1
            state['facts'][t['factName']]=t['value']
        elif kind in ('questConditionNodeDefinition','questPauseConditionNodeDefinition'):
            result=condition(n['condition'],state)
            if kind=='questConditionNodeDefinition':output='True' if result else 'False'
            elif not result:continue
        elif kind=='questJournalNodeDefinition':
            assert socket=='Active'
            state['journals'][n['type']['path']['realPath']]=2
        elif kind=='questLogicalHubNodeDefinition':
            assert n['inputSocketCount']==1 and n['outputSocketCount']==1
            output='Out1'
        elif kind!='questInputNodeDefinition':
            raise AssertionError(('unmodeled boot node',i,kind))
        todo.extend((e[3],e[4]) for e in g['edges'] if e[0]==i and e[1]==output and e[5]=='Input')
    return entered,state,seen


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    out=HERE/args.out;assert out.parent==HERE and not out.exists();out.mkdir()
    manifest,game=baseline();candidate=read(CANDIDATE/'manifest.json');package=CANDIDATE/'package'
    before=read(HERE/'evidence_02/graphs.json');contracts=read(HERE/'analysis_03/contracts.json')
    models={}
    for name in ('mq007_delivery_owner','mq007_delivery_boot','moving_heat_boot'):
        p=NATIVE/(name+'.questphase.json');models[name]=json.loads(json.dumps(normalize(load_export(p))))
        for g in models[name]['graphs']:check(name+' resolved edges '+g['path'],not g['unresolved_connections'])
    owner=models['mq007_delivery_owner'];boot=models['mq007_delivery_boot'];heat=models['moving_heat_boot']
    for new,rid in ((owner,'14545'),(boot,'15234'),(heat,'14686')):
        check('root/support/prefab equality '+rid,new['support']==before[rid]['support'])
        check('nested graph identity set '+rid,[g['path'] for g in new['graphs']]==[g['path'] for g in before[rid]['graphs']])
    for g in owner['graphs']:
        old=graph(before['14545'],g['path'])
        check('Skippy original node parameters/sockets '+g['path'],[clean_node(n) for n in g['nodes']]==[clean_node(n) for n in old['nodes']])
        removed=[e for e in old['edges'] if e not in g['edges']];added=[e for e in g['edges'] if e not in old['edges']]
        expected_removed=[[0,'Out','Output',32,'In','Input']] if g['path']=='root/5' else []
        expected_added=[[0,'Out','Output',11,'Active','Input'],[0,'Out','Output',72,'In','Input']] if g['path']=='root/5' else []
        check('Skippy only earned-entry edge change '+g['path'],removed==expected_removed and added==expected_added)
    delivery=graph(owner,'root/5');reach=reachable([0],[(e[0],e[3]) for e in delivery['edges'] if e[2]=='Output' and e[5]=='Input'])
    check('gun grant and owner reveal unreachable from delivery input',not reach.intersection({30,63,32}))
    check('legitimate return outcome/reward/cleanup retained',all(i in reach for i in (10,13,66)) and params(delivery,10)==params(graph(before['6542'],'root/5'),10))
    check('delivery listeners reachable',all(i in reach for i in (11,20,21,51,71,72,99)))
    check('Skippy owner has no Johnny resource reference','johnny' not in json.dumps(owner).lower())
    for path in ('root/3','root/5','root/7'):
        for g in [v for v in owner['graphs'] if v['path']==path or v['path'].startswith(path+'/')]:
            native=graph(before['6542'],g['path'])
            check('native Skippy body parameters retained '+g['path'],{i:clean_node(n) for i,n in nodes(g).items()}=={i:clean_node(n) for i,n in nodes(native).items()})
    for g in boot['graphs']:
        old=renamed(graph(before['15234'],g['path']))
        if g['path']!='root':
            check('saved follow-up nested graph retained '+g['path'],g==old);continue
        allowed={21,1001,1002,1004,1007,1008,1100,60000}
        check('new boot only reviewed node edits',all(n['id'] in allowed or clean_node(n)==clean_node(nodes(old)[n['id']]) for n in g['nodes']))
        check('new boot old IDs retained',set(nodes(old)).issubset(nodes(g)))
        check('new phase activation only inserted edge',set(map(tuple,g['edges']))==(set(map(tuple,old['edges']))-{(1101,'Out','Output',21,'In1','Input')}|{(1101,'Out','Output',60000,'Active','Input'),(60000,'Out','Output',21,'In1','Input')}))
        phase=params(g,60000)['type']
        check('phase activation exact earned phase without tracking',phase['path']['realPath']==contracts[0]['journals'][1]['path'] and phase['sendNotification']==0 and phase['trackQuest']==0)
        for i in (1001,1002,1007,1008,1100):
            atoms=list(walk(params(g,i)['condition']))
            facts=[v for v in atoms if v.get('$type')=='questVarComparison_ConditionType']
            check('no fixture-specific counters or mode prerequisite '+str(i),not any(v['factName'] in contracts[0]['counter_facts'] or v['factName']=='PTFRS23_MQ007_ModeTalkConfirmed' for v in facts))
            check('owner known at every admission boundary '+str(i),any(v['factName']=='mq007_skippy_owner_known' and v['value']==1 for v in facts))
    for g in heat['graphs']:
        old=graph(before['14686'],g['path'])
        check('Moving Heat all edges/identities retained '+g['path'],g['edges']==old['edges'] and set(nodes(g))==set(nodes(old)))
        for n in g['nodes']:
            if g['path']=='root' and n['id'] in (2,3,9):
                c=n['parameters']['condition']
                check('Moving Heat legacy predicate retained '+str(n['id']),c['operation']=='OR' and len(c['conditions'])==2 and c['conditions'][0]==params(old,n['id'])['condition'])
            else:check('Moving Heat unchanged node '+g['path']+'/'+str(n['id']),clean_node(n)==clean_node(nodes(old)[n['id']]))
    check('Moving Heat original scoped support wrapper retained',params(graph(heat),1200)==params(graph(before['14686']),1200))
    payload=read(NATIVE/'readback.json');members=payload['members']
    check('complete 1742-member readback',len(members)==1742)
    check('only one existing payload replaced',sum(r['unchanged'] for r in members)==1739)
    check('exact three-resource delta',{r['depot'] for r in members if not r['unchanged']}==set(payload['changed']))
    check('current Moving Heat body byte identical',next(r for r in members if r['depot'].endswith('moving_heat_resume.questphase'))['sha256']==next(r for r in read(HERE/'evidence_02/sources.json') if r['rid']==15402)['sha256'])
    check('original S23 owners remain byte identical',all(r['unchanged'] for r in members if r['depot'].startswith('towercontinued\\sidejobs_s23\\')))
    check('Highwayman S28 resources unchanged',all(r['unchanged'] for r in members if 'sidejobs_s28' in r['depot']))
    check('Highwayman S28 script unchanged',sha(package/RED_DIR/'PTFR_SideJobsS28.reds')==sha(game/RED_DIR/'PTFR_SideJobsS28.reds'))
    check('q307 and original retirement resources unchanged',all(r['unchanged'] for r in members if not r['depot'].startswith('towercontinued\\')))
    providers=read(CANDIDATE/'additional_providers.json');check('parent/ambient exact current providers',providers['status']=='PASS' and len(providers['providers'])==3)
    registry=sqlite3.connect(REGISTRY.as_uri()+'?mode=ro',uri=True)
    for rid,tag in ((14910,'PTFRSKIP_Ambient'),(15166,'PTFRSKIP_SC3')):
        n=json.loads(registry.execute('select parameters_json from nodes where rid=? and graph=? and id=2',(rid,'root')).fetchone()[0])
        atoms=[x for x in walk(n) if x.get('$type')=='questVarComparison_ConditionType']
        check('unclaimed ambient is fenced by Stop=0 '+tag,any(x['factName']==tag+'_Stop' and x['comparisonType']=='Equal' and x['value']==0 for x in atoms))
    compiled=read(HERE/'compile_02/result.json');check('full 148-source compile',compiled['status']=='PASS' and compiled['source_count']==148)
    for rel,pin in read(HERE/'candidate_02/script_manifest.json')['changed_sources'].items():check('compiled final bytes '+rel,sha(package/rel)==pin)
    for row in candidate['core_files']:check('candidate file hash '+row['path'],sha(package/row['path'])==row['sha256'])
    registrations=read(CANDIDATE/'registration_inventory.json')
    check('new registered phase ID collision-free',registrations['new_id']==8694 and registrations['previous_xl_retained_byte_for_byte'])
    for pin in registrations['xl_inputs']:check('XL inventory still current '+pin['path'],sha(pin['path'])==pin['sha256'])
    for pin in read(HERE/'evidence_02/sources.json')+read(CANDIDATE/'additional_sources.json'):check('reviewed export unchanged '+str(pin['rid']),sha(pin['export_path'])==pin['export_sha256'])

    policy=(package/HISTORY).read_text(encoding='utf-8')
    # Outcomes are expectations independent of the policy source being executed.
    defaults=dict(history=2,live=4,privateReceipt=0,originalOwnerProven=False,retirementQualified=True,freshMatch=False,stageMatch=True)
    decision_cases=[('earned stage',{},'EarnedStage'),('completed history',{'history':3},'PreserveHistory'),('failed history',{'history':4},'PreserveHistory'),
        ('current completed',{'live':3},'PreserveHistory'),('unknown history',{'history':-1},'Defer'),('retirement absent',{'retirementQualified':False},'Defer'),
        ('stage unsupported',{'stageMatch':False},'Defer'),('existing private owner',{'privateReceipt':1},'KeepPrivateOwner'),('invalid receipt',{'privateReceipt':-1},'Defer'),
        ('original owner proof',{'originalOwnerProven':True},'KeepOriginalOwner'),('inactive fresh',{'history':1,'live':1,'freshMatch':True},'FreshEntry'),
        ('inactive cannot earned-resume',{'history':1},'Defer'),('live unknown',{'live':-1},'Defer')]
    for name,overrides,expected in decision_cases:
        actual=source_decision(policy,**(defaults|overrides));check('dispatcher '+name,actual==expected);fixtures.append({'case':name,'result':actual})
    snapshot=game/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/snapshot_hs1_20261112T193921Z_151_2.json'
    check('exact good snapshot fixture',sha(snapshot)=='C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE')
    rows={r['definition']['id']:r for r in read(snapshot)['rows']}
    save_path=ROOT/'prealpha/handler_preservation_hp1_20261112_01/analysis_01/save_comparison.json';saves=read(save_path)
    for c,index,g,gate,stop in ((contracts[0],0,graph(boot),1001,21),(contracts[1],1,graph(heat),2,1200)):
        h,s=common_fixture(rows[c['id']],saves['AutoSave-5'])
        check(c['id']+' good history + historical after-Tower states admitted',contract_accept(c,h,s))
        s['facts'][c['tag']+'_Permit']=1
        check(c['id']+' serialized initial guard admits',condition(params(g,gate)['condition'],s))
        entered,after,visited=admission_route(g,s,stop)
        check(c['id']+' complete boot route reaches owner once',entered==[stop])
        check(c['id']+' durable issued receipt set',after['facts'][c['tag']+'_Issued']==1)
        check(c['id']+' repeated admission refused',not condition(params(g,gate)['condition'],after) and not contract_accept(c,h,after))
        check(c['id']+' boot does not change native facts',{k:v for k,v in after['facts'].items() if not k.startswith('PTFR')}=={k:v for k,v in s['facts'].items() if not k.startswith('PTFR')})
        fixtures.append({'case':c['id']+' admission replay','visited':visited,'assumptions':'Inventory quantity=1, objective counters unchanged, safe exterior, resolved journal, completed private startup and 100 ms boot delay; actual saved journals/facts from AutoSave-5.'})
        for receipt in c['other_owner_receipts']+c['own_receipts']:
            bad=deepcopy(s);bad['facts'][receipt]=1
            check(c['id']+' refuse receipt '+receipt,not contract_accept(c,h,bad) and not condition(params(g,gate)['condition'],bad))
        for j in c['journals']:
            bad=deepcopy(s);bad['journals'][j['path']]=3 if 3 not in j['live'] else 4
            check(c['id']+' refuse wrong stage '+j['path'],not contract_accept(c,h,bad) and not condition(params(g,gate)['condition'],bad))
        for name,value in c['fixed_facts'].items():
            bad=deepcopy(s);bad['facts'][name]=value+1
            check(c['id']+' refuse changed fact '+name,not contract_accept(c,h,bad) and not condition(params(g,gate)['condition'],bad))
        for field in ('valid',):
            bad=deepcopy(h);bad[field]=False;check(c['id']+' unknown/unstable history',not contract_accept(c,bad,s))
        bad=deepcopy(s);bad['settled']=False;check(c['id']+' journal transition defers',not contract_accept(c,h,bad))
        for name in c['choice_facts']:
            bad=deepcopy(s);bad['facts'][name]=1-h['facts'][name];check('Skippy changed choice '+name,not contract_accept(c,h,bad))
        for name in c['counter_facts']:
            bad=deepcopy(s);bad['facts'][name]=h['facts'][name]-1;check('Skippy regressed counter '+name,not contract_accept(c,h,bad))
            good=deepcopy(s);good['facts'][name]+=7;check('Skippy later kills preserved '+name,contract_accept(c,h,good) and condition(params(g,gate)['condition'],good))
        if c['item']:
            for qty in (0,2):
                bad=deepcopy(s);bad['item']=qty;check('Skippy inventory quantity '+str(qty)+' refused',not contract_accept(c,h,bad) and not condition(params(g,gate)['condition'],bad))
        for tag in c['handoff']:
            pending=deepcopy(s);pending['facts'].update({tag+'_Claimed':1,tag+'_Entered':1,tag+'_Stop':1,tag+'_Stopped':0})
            check(tag+' waits for true stop acknowledgement',not contract_accept(c,h,pending) and not condition(params(g,gate)['condition'],pending))
            pending['facts'][tag+'_Stopped']=1
            check(tag+' admits acknowledged stop',contract_accept(c,h,pending) and condition(params(g,gate)['condition'],pending))
        if index==1:
            bad=deepcopy(s);bad['facts']['q305_done']=0;bad['facts']['q306_done']=0
            check('Moving Heat native entitlement still required',not condition(params(g,gate)['condition'],bad))
            bad=deepcopy(s);bad['outside']=False;check('Moving Heat unsafe placement still refused',not condition(params(g,gate)['condition'],bad))
    check('inactive Highwayman fixture remains inactive',set(rows['mq029_tourist']['states'])=={1})
    check('legacy history filter retains the previous predicate',
          'public static func HistoryAdmits(history: Int32) -> Bool {\n    return history==1 || history==2;\n  }' in policy)
    result={'status':'PASS_BOUNDED_OFFLINE_QUALIFICATION','candidate':'candidate_04','checks':len(checks),'details':checks,'fixtures':fixtures,
        'gameplay':'UNVERIFIED; no deployment or game launch','scope':['Machine Gun Deliver Skippy','Moving Heat first door','inactive Highwayman unchanged regression'],
        'shared_dispatcher':'History policy shared; full stage selection currently used by these two earned-stage entries. Existing adapters retain their narrower checks.',
        'limitations':['No universal arbitrary-moment resumption. Other unfinished stages receive no new stage entry; legacy checks are retained.',
            'No original-handler preservation or timer suspension.',
            'Fixture admission evaluator does not execute scenes, callbacks, actors, support streaming, rewards or save serialization.',
            'Machine Gun return/reacquisition persistent native sector placement remains opaque to WolvenKit 9.1; exact reviewed native references retained.',
            'Global latest history is user-selected and is not same-run provenance. Live checks fence reviewed stages; do not establish every unmodeled choice.',
            'Existing native journal activation notifications/tracking for Moving Heat retained; no claim to restore all optional/tracked/phone-history metadata.'],
        'input_pins':{'snapshot':sha(snapshot),'save_comparison':sha(save_path),'native_readback':sha(NATIVE/'readback.json'),'contracts':sha(HERE/'analysis_03/contracts.json'),
                      'candidate_manifest':sha(CANDIDATE/'manifest.json'),'compile':sha(HERE/'compile_02/result.json'),'qualifier':sha(__file__)},
        'game_writes':0,'save_writes':0,'installed':False}
    write(out/'assessment.json',result)
    print(f'PASS: {len(checks)} bounded source, graph, input and state-fixture checks; gameplay unverified.')


if __name__=='__main__':main()
