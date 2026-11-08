"""Read-only MQ035 contract checks against pinned original resources.

Run from repository root with Python -B and --output <fresh-directory>.
No builder, game API, deployment or original evidence is imported/executed.
"""
from pathlib import Path
import sys,json,gzip,hashlib,collections,copy,argparse

ROOT=Path(__file__).resolve().parents[4]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',required=True,type=Path,help='New output directory; existing paths are refused')
OUT=parser.parse_args().output.resolve()
if OUT.exists():
    parser.error('Use a fresh output directory; preserve completed and partial evidence: '+str(OUT))
OUT.mkdir(parents=True)
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource

AUDIT=ROOT/'diagnostics/vanilla_parity_20261029_01/analysis_02'
INDEX=json.loads((AUDIT/'resource_inventory.json').read_text())
MI=json.loads((AUDIT/'model_inventory.json').read_text())
PH3=ROOT/'prealpha/phone_studios_ph3/candidate_01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
P=r'towercontinued\sidejobs_s23\base_a\mq035_ozob.questphase'
PN=r'towercontinued\sidejobs_s23\phone\ozob.questphase'
N=r'base\quest\minor_quests\mq035\mq035_ozob.questphase'
PAR=r'base\quest\minor_quests\minorquests.questphase'
C=r'base\quest\holocalls\ozob\ozob_holocall.questphase'
CS=r'base\quest\holocalls\ozob\ozob_holocall.scene'
CL=r'base\quest\holocalls\ozob\ozob_cleanup.questphase'
SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
ST=r'towercontinued\phone_studios_ph3\studio_support.questphase'
HOOK=r'base\quest\minor_quests\mq035\phases\mq035_01_car_theft.questphase'
HS=r'base\quest\minor_quests\mq035\scenes\mq035_hook_call.scene'
DS=r'base\quest\minor_quests\mq035\scenes\mq035_ozob_dialogues.scene'
RO=r'base\quest\minor_quests\mq035\phases\mq035_03_robbery.questphase'
AM=r'base\quest\minor_quests\mq035\phases\mq035_04_ambush.questphase'
DEPS=[d for d in INDEX if '\\mq035\\' in d or '\\holocalls\\ozob\\' in d]+[P,PN,PAR,SH,ST,r'base\quest\holocalls\holocall_initializers.questphase']
DEPS=sorted(set(DEPS))
models={};pins=[];checks=[]
for d in DEPS:
    r=INDEX[d];j=Path(r['json']);b=j.with_suffix('')
    # Native JSONs have their exact decoded binary beside them. Private JSONs
    # bind to the current consolidated resource, not a prototype directory.
    if d.startswith('towercontinued\\'):b=PH3/'archive_source'/Path(d.replace('\\','/'))
    assert b.is_file(),f'Binary input missing: {b}'
    assert sha(b)==r['sha256'],f'Stale binary: {d}'
    m=Resource(json.loads(j.read_text(encoding='utf-8-sig'))).normalize()
    cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()))
    # Older cache schema omitted the empty embedded-file list; require actual
    # graph/payload identity after this explicit representation-only migration.
    cached.setdefault('embedded_files',[])
    assert m==cached,f'Raw JSON/model discrepancy: {d}'
    models[d]=m
    pins.append({'depot':d,'binary':str(b),'sha256':sha(b),'provider':r['archive'],'source_json':str(j),'source_json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']})
save('source_pins.json',pins)
def g(d,gp='root'):return models[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
def facts(node):return [x for x in walk(node['payload']) if x.get('$type')=='questVarComparison_ConditionType']
def writes(node):return [x for x in walk(node['payload']) if x.get('$type')=='questSetVar_NodeType']
def reachable(gr,seeds,removed=()):
    seen=set(map(str,seeds));todo=list(seen)
    while todo:
        for a,s,b,t in gr['edges']:
            if a==todo[-1] and b not in seen and b not in removed:
                seen.add(b);todo.insert(0,b)
        todo.pop()
    return seen
def hascond(node,f,c,v):return any(x.get('factName')==f and x.get('comparisonType')==c and x.get('value')==v for x in facts(node))
def evaluate(x,fs,js):
    t=x['$type']
    if t=='questLogicalCondition':
        vs=[evaluate(y,fs,js) for y in x['conditions']]
        return all(vs) if x['operation']=='AND' else any(vs) if x['operation']=='OR' else not any(vs) if x['operation']=='NOR' else (_ for _ in ()).throw(ValueError(t))
    if t in ('questFactsDBCondition','questJournalCondition'):return evaluate(x['type'],fs,js)
    if t=='questVarComparison_ConditionType':
        a=fs[x['factName']];b=x['value'];return {'Equal':a==b,'Less':a<b,'Greater':a>b,'LessOrEqual':a<=b,'GreaterOrEqual':a>=b,'NotEqual':a!=b}[x['comparisonType']]
    if t=='questJournalEntryState_ConditionType':return (js[x['path']['realPath']]==x['state']) != bool(x.get('inverted',0))
    raise ValueError('Unsupported predicate '+t)
def check(name,ok,evidence):
    checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence})
    assert ok,name

# This compares serialized node payloads and every nested connection to the
# independent native parent. It is not a comparison to an invented recipe.
check('native_q110_and_seven_streetcred_branches_exact',g(P,'root/130')==g(PAR,'root/130'),{'native':PAR,'private':P,'graph':'root/130','nodes':12,'edges':17})
for i in [32,47,54,55,59,62,70,73,76,80,81,83,84,86,130]:
    check('native_ancestor_node_'+str(i),n(P,i)['payload']==n(PAR,i)['payload'],{'node':i,'graph':'root'})
required=[e for e in g(PAR)['edges'] if e[0] in {'47','54','55','59','62','70','73','76','80','81','83','84','86'} and e[2] in g(P)['nodes']]
check('native_admission_ancestor_edges_preserved',all(e in g(P)['edges'] for e in required),required)
check('final_native_gate_before_native_body',edge(P,130,'Out1',1100,'In') and edge(P,1100,'True',1101,'In') and edge(P,1101,'Out',32,'In1'),['130.Out1 ->1100.In;1100.True ->1101.In;1101.Out ->32.In1'])

# Evaluate actual serialized admission guards, including the CR1 root ownership
# correction. Tests do not rewrite guards to a simpler presumed rule.
root='quests/minor_quest/mq035_ozob'
for i in [1001,1002]:
    cond=n(P,i)['payload']['condition'];fs={x['factName']:x['value'] for x in facts(n(P,i))}
    js={x['path']['realPath']:'Inactive' for x in walk(cond) if x.get('$type')=='questJournalEntryState_ConditionType'}
    check('fresh_admission_'+str(i),evaluate(cond,fs,js),{'node':i,'root':'Inactive','facts':'Exact serialized comparisons'})
    for state in ['Active','Succeeded','Failed']:
        q=js|{root:state};check('reject_'+state+'_'+str(i),not evaluate(cond,fs,q),{'node':i,'root':state})
    check('reject_pre_tower_'+str(i),not evaluate(cond,fs|{'q307_done':0},js),{'node':i,'fact':'q307_done=0'})
    check('reject_issued_'+str(i),not evaluate(cond,fs|{'PTFRS23_MQ035_Issued':1},js),{'node':i})
    check('reject_used_native_car_ride_'+str(i),not evaluate(cond,fs|{'mq035_car_ride':1},js),{'node':i})
check('failed_reactivation_branch_not_admitted_in_fresh_snapshot',n(P,1004)['payload']['condition']['type']['state']=='Failed',{'guard_nodes':[1001,1002],'failed_node':1004,'inactive_and_failed_cannot_both_hold':'serialized snapshot; asynchronous engine mutation between nodes is not proved impossible'})
check('postclaim_identity_preserved',hascond(n(P,1007),'PTFRS23_MQ035_Issued','Equal',1) and hascond(n(P,1008),'PTFRS23_MQ035_Issued','Equal',1),{'nodes':[1007,1008]})
check('no_native_or_ack_writes_from_wrapper',all(x['factName'].startswith('PTFRS23_MQ035_') for gr in models[P]['graphs'].values() for node in gr['nodes'].values() for x in writes(node)),{'private':P})
check('native_phone_binding_exact',n(PN,78)['payload']==n(r'base\quest\holocalls\holocall_initializers.questphase',78)['payload'],{'phone_node':78,'resource':C,'socket':'In1'})
check('phone_owner_before_quest_owner',hascond(n(P,1001),'PTFRS23_PHONE_OZOB_Issued','Equal',1) and hascond(n(P,1002),'PTFRS23_PHONE_OZOB_Issued','Equal',1),{'nodes':[1001,1002]})
check('hook_sms_and_rejection_retry',edge(HOOK,21,'Out',11,'In') and edge(HOOK,21,'Out',20,'In') and edge(HOOK,12,'reject_out',18,'In') and edge(HOOK,18,'Out',17,'In') and edge(HOOK,17,'Out',12,'call_again_in'),{'sms_node':21,'visited_node':20,'incoming_wait':11,'reject_retry':[12,18,17,12]})
for request,reader,clear,scene_input,ack,hswriter,hswait,hsclear in [
 ('audio_v_calls_ozob_start_activate',17,19,'audio_v_calls_ozob_start',22,118,111,112),
 ('audio_v_calls_ozob_end_activate',18,20,'audio_v_calls_ozob_end',23,119,113,114)]:
    check('native_protocol_'+request,hascond(n(C,reader),request,'Greater',0) and any(x['factName']==request and x['value']==0 for x in writes(n(C,clear))) and scene_input in g(CS,'scene')['entries'] and any(x['factName']==request and x['value']==1 for x in writes(n(HS,hswriter,'scene'))) and any(x['factName']=='holo_v_calls_ozob_'+('start' if 'start' in request else 'end')+'_done' and x['value']==1 for x in writes(n(CS,ack,'scene'))) and hascond(n(HS,hswait,'scene'),'holo_v_calls_ozob_'+('start' if 'start' in request else 'end')+'_done','Greater',0),{'controller_read':reader,'controller_clear':clear,'caller_request':hswriter,'caller_wait':hswait,'caller_clear':hsclear,'ack_writer':ack})
check('native_cleanup_in_shared_chain',edge(SH,804,'True',805,'In41') and edge(SH,805,'Out41',806,'In') and n(SH,805)['refs']==[CL],{'resource':SH,'node':805})
check('native_cleanup_outgoing_balanced_route',edge(CL,5,'True',7,'In') and edge(CL,7,'Out',2,'audio_v_calls_ozob_end') and edge(CL,2,'audio_NPC_out',3,'In'),{'count_comparison':5,'reset_counter_increment':7,'native_end_scene':2,'terminating_out':3})
check('native_success_and_failure_routes_retained',all(e in g(N)['edges'] for e in [['103','failed','197','In1'],['104','failed','197','In1'],['105','failed','197','In1'],['105','patch0','199','In1'],['105','Out1','192','In1']]),{'resource':N,'normal_cleanup':'192','failure_cleanup':'197 ->200 ->192|199'})
check('native_recipe_rewards_on_both_authored_branches',all(any(x.get('$type')=='questAddRemoveItem_NodeTypeParams' and val(x.get('itemID'))=='Items.RecipeGrenadeOzobsNose' and x.get('quantity')==1 for x in walk(n(d,i)['payload'])) for d,i in [(RO,280),(AM,330)]),{'robbery_node':280,'ambush_node':330,'quantity':1})
check('native_ending_reward_record',any(x.get('$type')=='TweakDBID' and val(x)=='QuestRewards.mq035_done' for x in walk(n(DS,278,'scene')['payload'])),{'scene':DS,'node':278})
check('completion_receipt_observes_native_success',n(P,1010)['payload']['condition']['type']['state']=='Succeeded' and edge(P,1010,'Out',1011,'In'),{'native_journal_observer':1010,'private_receipt':1011})

# Mutation controls operate on actual copied graph data and must contradict
# independent native expectations. No corrupted data is ever serialized.
mut=[]
bad=copy.deepcopy(g(P,'root/130'));bad['edges'].remove(['22','Out','13','In'])
mut.append({'fault':'missing native StreetCred branch','detected':bad!=g(PAR,'root/130')})
cond=copy.deepcopy(n(P,1002)['payload']['condition']);
for x in walk(cond):
    if x.get('$type')=='questJournalEntryState_ConditionType' and x['path']['realPath']==root:x['state']='Active'
fs={x['factName']:x['value'] for x in facts(n(P,1002))};js={x['path']['realPath']:'Inactive' for x in walk(cond) if x.get('$type')=='questJournalEntryState_ConditionType'}
mut.append({'fault':'changed root ownership admission','detected':evaluate(cond,fs,js|{root:'Active'})})
bad=copy.deepcopy(g(CL));bad['edges'].remove(['7','Out','2','audio_v_calls_ozob_end'])
mut.append({'fault':'missing native phone cleanup edge','detected':['7','Out','2','audio_v_calls_ozob_end'] not in bad['edges']})
bad=copy.deepcopy(n(P,32)['payload']);bad['phaseResource']['DepotPath']['$value']='missing.questphase'
mut.append({'fault':'wrong native body donor','detected':bad!=n(PAR,32)['payload']})
for row in mut:check('mutation_'+row['fault'],row['detected'],row)

facts_trace=[];journal_trace=[];assets=[]
for d,m in models.items():
    for gp,gr in m['graphs'].items():
        for ni,node in gr['nodes'].items():
            for x in walk(node['payload']):
                if x.get('$type') in ['questVarComparison_ConditionType','questVarVsVarComparison_ConditionType','questSetVar_NodeType']:
                    facts_trace.append({'depot':d,'graph':gp,'node':ni,'payload':x,'incoming':[e for e in gr['edges'] if e[2]==ni],'outgoing':[e for e in gr['edges'] if e[0]==ni]})
                if isinstance(x.get('path'),dict) and 'realPath'in x['path']:
                    journal_trace.append({'depot':d,'graph':gp,'node':ni,'type':x['$type'],'path':x['path']['realPath'],'state':x.get('state'),'version':x.get('version'),'incoming':[e for e in gr['edges'] if e[2]==ni]})
            if node['node_refs'] or node['prefabs'] or node['refs']:
                assets.append({'depot':d,'graph':gp,'node':ni,'node_refs':node['node_refs'],'prefabs':node['prefabs'],'assets':node['refs']})
save('graph_evidence.json',{'sources':pins,'facts':facts_trace,'journal':journal_trace,'asset_bindings':assets,'prefab_roots':{d:m['root_prefabs'] for d,m in models.items()},'checks':checks,'mutations':mut})
save('tests.json',{'status':'PASS','checks':len(checks),'mutations':len(mut),'results':checks,'scope':'Pinned raw/normalized MQ035, inherited native progression and bounded fresh predicates. Not engine/save/gameplay simulation.'})
print(json.dumps({'status':'PASS','checks':len(checks),'mutations':len(mut),'sources':len(pins)}))
