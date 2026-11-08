"""Read-only, raw-backed MQ037 family verification. Requires a fresh output."""
from pathlib import Path
import argparse,sys,json,gzip,hashlib,copy,re,collections
W=Path(__file__).resolve().parents[4]
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
O=Path(parser.parse_args().output).resolve();assert not O.exists(),'Preserve existing evidence';O.mkdir(parents=True)
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
from common import read,write,sha,walk,value
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
PH3=W/'prealpha/phone_studios_ph3/candidate_01'
N=r'base\quest\minor_quests\mq037\mq037_brendan.questphase'
P=r'towercontinued\sidejobs_s23\base_b\mq037.questphase'
S=r'base\quest\minor_quests\mq037\scenes\mq037_01_brendan_scenes.scene'
B=r'base\quest\bugfixing\minor_quests\mq037\mq037_quest_bugfixes.questphase'
PAR=r'base\quest\minor_quests\minorquests.questphase'
MODELS={};pins=[];checks=[]
def check(name,ok,evidence):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
for d in [N,P,S,B,PAR]:
 r=IDX[d];j=Path(r['json']);binary=PH3/'archive_source'/d.replace('\\','/') if d.startswith('towercontinued') else j.with_suffix('')
 check('binary hash '+d,binary.is_file() and sha(binary)==r['sha256'],str(binary))
 m=Resource(read(j)).normalize();cache=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cache.setdefault('embedded_files',[])
 check('raw JSON normalization '+d,m==cache,{'source_json':str(j),'model':MI[d]['normalized_model']})
 MODELS[d]=m;pins.append({'depot':d,'binary':str(binary),'sha256':sha(binary),'provider':r['archive'],'source_json':str(j),'source_json_sha256':sha(j),'normalized_model':MI[d]['normalized_model'],'normalized_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']})
def g(d,gp='root'):return MODELS[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def hasedge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
def reachable(graph,seeds):
 seen=set(map(str,seeds));todo=list(seen)
 while todo:
  a=todo.pop()
  for x,s,y,t in graph['edges']:
   if x==a and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);todo.append(y)
 return seen
def evalcondition(c,f,j):
 t=c['$type']
 if t in ['questFactsDBCondition','questJournalCondition']:return evalcondition(c['type'],f,j)
 if t=='questLogicalCondition':
  v=[evalcondition(x,f,j) for x in c['conditions']]
  if c['operation']=='AND':return all(v)
  if c['operation']=='OR':return any(v)
  if c['operation']=='NOR':return not any(v)
  raise ValueError(c['operation'])
 if t=='questVarComparison_ConditionType':
  if c['factName'] not in f:return False
  a=f[c['factName']];b=c['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[c['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  p=c['path']['realPath']
  if p not in j:return False
  return (j[p]==c['state']) != bool(c.get('inverted',0))
 raise ValueError('Unsupported predicate '+t)

# Native parent and all bodies stay native; exact input/socket/order is important.
for i in [34,54,80,55]:check('native ancestor payload '+str(i),n(P,i)['payload']==n(PAR,i)['payload'],{'native':PAR,'private':P,'node':i})
for e in [['1000','Out','1001','In'],['1001','Out','1002','In'],['1002','Out','1003','In'],['1003','Out','54','In'],['54','Out','80','In'],['80','Out','55','In'],['55','Out','1004','In'],['1004','True','1005','In'],['1004','False','1002','In'],['1005','Out','1006','In'],['1006','Out','34','In1'],['34','Out1','1007','In']]:
 check('private connected edge '+str(e),e in g(P)['edges'],e)
check('native body and prefab delegation',n(P,34)['refs']==[N] and MODELS[N]['root_prefabs']==['#mq037_pr_machine_spot','#mq037_service_point'],{'body_input':'In1','native_root_prefabs':MODELS[N]['root_prefabs']})
check('one shared owner covers both selected jobs',sum(N in x['refs'] for x in g(P)['nodes'].values())==1,{'private':P,'native':N})
check('all wrapper writes are owned receipts',all(x['factName'].startswith('PTFRS23_MQ037_') for gr in MODELS[P]['graphs'].values() for node in gr['nodes'].values() for x in node['writes']),P)
check('preclaim guards identical',n(P,1002)['payload']['condition']==n(P,1004)['payload']['condition'],[1002,1004])
cases=[]
for i in [1002,1004]:
 c=n(P,i)['payload']['condition'];f={x['factName']:x['value'] for x in walk(c) if x.get('$type')=='questVarComparison_ConditionType'};j={x['path']['realPath']:x['state'] for x in walk(c) if x.get('$type')=='questJournalEntryState_ConditionType'}
 check('actual all-inactive guard accepts fresh '+str(i),evalcondition(c,f,j),{'node':i,'facts':f,'journals':j})
 for path in j:
  for state in ['Active','Succeeded','Failed']:
   check('fresh guard rejects '+str(i)+' '+path+' '+state,not evalcondition(c,f,j|{path:state}),{'path':path,'state':state})
  missing=dict(j);missing.pop(path);check('fresh guard refuses missing '+str(i)+' '+path,not evalcondition(c,f,missing),path)
 for fact in f:
  bad=f|{fact:1 if f[fact]==0 else 0};check('fresh guard rejects changed '+str(i)+' '+fact,not evalcondition(c,bad,j),fact)
 cases.append({'node':i,'facts':f,'journals':j})
 # Exact earned root is refused by this old all-inactive seam.
 check('earned Dumpster completion not admitted '+str(i),not evalcondition(c,f,j|{'quests/minor_quest/mq037_brendan_dumpster':'Succeeded'}),'No supported earned-history adapter is implemented by this seam')

# Native complete path enters the excluded Dumpster job before the selected jobs.
for e in [['0','Out','34','In1'],['34','Out1','10','In1'],['10','Out1','19','In1'],['19','Out1','23','In1'],['23','Out1','25','In1'],['25','Out1','28','In1']]:check('native ordered family edge '+str(e),e in g(N)['edges'],e)
for e in [['6','help_plz_out','22','Inactive'],['22','Out','16','Active'],['16','Out','12','Active'],['12','Out','7','In'],['7','Out','13','Succeeded'],['13','Out','14','Active'],['15','Out','17','Succeeded'],['17','Out','23','In'],['23','Out','24','In'],['24','Out','25','In'],['25','Out','26','In'],['26','Out','1','In']]:check('native excluded prerequisite edge '+str(e),e in g(N,'root/19')['edges'],{'graph':'root/19','edge':e})
check('excluded journal actual writer',n(N,16,'root/19')['payload']['type']['path']['realPath']=='quests/minor_quest/mq037_brendan_dumpster' and hasedge(N,22,'Out',16,'Active','root/19'),{'graph':'root/19','node':16})
check('native physical interaction is real gate',n(N,7,'root/19')['payload']['condition']['type']['deviceConditionFunction']['$value']=='DemolitionPerformed',n(N,7,'root/19')['payload'])

# Selected Spray Paint success/failure and final Coin Operated Boy branches.
for e in [['106','False','109','Active'],['109','Out','86','Active'],['86','Out','73','Active'],['73','Out','62','In1'],['49','Out','35','Inactive'],['35','Out','50','Active'],['51','Out','52','Succeeded'],['122','Out','123','Failed']]:check('Spray Paint native branch '+str(e),e in g(N,'root/25')['edges'],{'graph':'root/25','edge':e})
check('Spray failure fact remains native',n(N,122,'root/25')['writes']==[{'$type':'questSetVar_NodeType','factName':'mq037_vandal_painted_brendan','setExactValue':1,'value':1}],{'graph':'root/25','node':122})
for e in [['4','bad_news_out','5','Succeeded'],['5','Out','6','Succeeded'],['6','Out','11','In'],['11','Out','9','In'],['9','Out','8','In']]:check('Coin final completion branch '+str(e),e in g(N,'root/28/140')['edges'],{'graph':'root/28/140','edge':e})
check('native completion reward pointer',any(x.get('$type')=='TweakDBID' and value(x)=='QuestRewards.mq037_done' for x in walk(n(N,11,'root/28/140')['payload'])),{'graph':'root/28/140','node':11})
check('native final done writer',n(N,9,'root/28/140')['writes']==[{'$type':'questSetVar_NodeType','factName':'mq037_done','setExactValue':1,'value':1}],{'graph':'root/28/140','node':9})
comms=[{'resource':d,'graph':gp,'node':i,'type':x.get('$type'),'payload':x} for d in [P,N,S] for gp,gr in MODELS[d]['graphs'].items() for i,node in gr['nodes'].items() for x in walk(node['payload']) if x.get('$type') in ['questSendMessage_NodeType','questPhoneCall_NodeType'] or (x.get('$type') in ['questSetVar_NodeType','questVarComparison_ConditionType'] and re.match(r'^(audio_|holo_|phonecall_)',x.get('factName','')))]
check('no quest-owned phone or acknowledgement protocol',not comms,comms)

# Bind the actual effective producers, not merely a hypothetical Permit fact.
script=PH3/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
hs=PH3/'package/r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
src=script.read_text(encoding='utf-8-sig');hsrc=hs.read_text(encoding='utf-8-sig')
def method(text,name):
 m=re.search(r'func\s+'+re.escape(name)+r'\([^)]*\)[^{]*\{',text);assert m,name
 start=m.end();depth=1;i=start
 while depth:
  depth+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[start:i-1]
paths=json.loads(re.search(r'func Paths13\(\)[^{]*\{ return (\[.*?\]);',src).group(1))
states_a=json.loads(re.search(r'func StatesA13\(\)[^{]*\{ return (\[.*?\]);',src).group(1));states_b=json.loads(re.search(r'func StatesB13\(\)[^{]*\{ return (\[.*?\]);',src).group(1))
check('runtime sample accepts all18Inactive',len(paths)==18 and states_a==states_b==[1]*18,{'paths':paths,'states_a':states_a,'states_b':states_b})
check('runtime sampler and actual guards journal sets agree',set(paths)==set(cases[0]['journals']),paths)
ready=method(src,'Ready');permit=method(src,'Permit');poll=method(src,'Poll');allows=method(hsrc,'Allows')
check('actual Permit producer stable sample route','this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i))' in poll,{'method':'Poll','source':str(script)})
check('actual Ready has no MQ037-specific hold','SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS23.ID(i))' in ready and 'i == 13' not in ready and 'i==13' not in ready,{'method':'Ready','body':ready})
check('snapshot admits fresh primary without earned Dumpster test','this.rows[i].states[0]==1 || this.rows[i].states[0]==2' in allows and 'dumpster' not in allows,{'method':'Allows','body':allows})
check('issued owner is not revoked by Permit producer','this.Own(i, "Issued") != 0' in permit,{'method':'Permit','body':permit})
policy=W/'docs/whitelist_final_r6.md';policytext=policy.read_text(encoding='utf-8-sig')
check('explicit current policy excludes fresh prerequisite','Spray Paint and Coin Operated Boy remain selected only when the earlier' in policytext and 'They do not authorize' in policytext,{'path':str(policy),'sha256':sha(policy)})
queue=read(W/'prealpha/quest_restoration_qr2/queue.json');check('current catalogue excludes Dumpster','mq037_brendan_dumpster' in queue['excluded'],{'source':queue['source_catalogue'],'catalogue_sha256':queue['catalogue_sha256']})

def fresh_reaches_native(graph):return '34' in reachable(graph,['1000']) and ['1004','True','1005','In'] in graph['edges']
def policy_violation(graph):return fresh_reaches_native(graph) and evalcondition(graph['nodes']['1002']['payload']['condition'],cases[0]['facts'],cases[0]['journals'])
check('failing-before policy counterexample is reproducible',policy_violation(g(P)),{'expected':'DEFECT_PRESENT','private_true_edge':['1004','True','1005','In'],'excluded_journal_writer':'native root/19 node16 Active'})
# Proposed quarantine is in-memory only. Root owns serialization and deployment.
proposal=copy.deepcopy(g(P));proposal['edges'].remove(['1004','True','1005','In']);proposal['edges'].append(['1004','True','1008','In']);proposal['edges'].sort()
check('passing-after proposed quarantine blocks fresh excluded path',not policy_violation(proposal) and '34' not in reachable(proposal,['1000']) and '1008' in reachable(proposal,['1000']),{'proposal_only':True,'new_edge':['1004','True','1008','In']})
check('quarantine preserves all saved nodes and old descendants',proposal['nodes']==g(P)['nodes'] and reachable(proposal,['1005'])==reachable(g(P),['1005']),{'saved_nodes_unchanged':len(proposal['nodes']),'issued_descendant_seed':'1005'})
mutations=[]
bad=copy.deepcopy(g(P));bad['edges'].remove(['55','Out','1004','In']);mutations.append({'fault':'lost native prerequisite connection','detected':'34' not in reachable(bad,['1000'])})
bad=copy.deepcopy(proposal);bad['edges'].remove(['1004','True','1008','In']);bad['edges'].append(['1004','True','1005','In']);mutations.append({'fault':'reintroduced excluded prerequisite path','detected':policy_violation(bad)})
bad=copy.deepcopy(n(N,7,'root/19')['payload']);bad['condition']['type']['deviceConditionFunction']['$value']='AlwaysTrue';mutations.append({'fault':'fabricated physical prerequisite completion','detected':bad!=n(N,7,'root/19')['payload']})
bad=copy.deepcopy(n(N,11,'root/28/140')['payload']);bad['type']['rewards'][0]['$value']='QuestRewards.wrong';mutations.append({'fault':'wrong final reward pointer','detected':bad!=n(N,11,'root/28/140')['payload']})
for m in mutations:check('mutation '+m['fault'],m['detected'],m)
write(O/'source_pins.json',pins)
trace=[]
for d,m in MODELS.items():
 if d==PAR:continue
 for gp,gr in m['graphs'].items():
  for i,node in gr['nodes'].items():
   if node['writes'] or node['reads'] or node['journal_paths'] or node['refs'] or node['node_refs'] or node['reward']:
    trace.append({'resource':d,'graph':gp,'node':i,'type':node['type'],'payload':node['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
write(O/'graph_evidence.json',{'pins':pins,'handlers':trace,'root_prefabs':{d:m['root_prefabs'] for d,m in MODELS.items()},'scene_entry_points':g(S,'scene')['entries'],'runtime_sources':[{'path':str(script),'sha256':sha(script)},{'path':str(hs),'sha256':sha(hs)}],'producer_methods':{'Ready':ready,'Permit':permit,'Allows':allows},'case':cases[0],'mutations':mutations})
write(O/'defects.json',{'defects':[{'id':'QR3-MQ037-EXCLUDED-PREREQUISITE','severity':'HIGH','status':'SOURCE_CONFIRMED','affected_quests':['mq037_brendan','mq037_brendan_hooligan001'],'resource':P,'resource_sha256':IDX[P]['sha256'],'fault':'Fresh all-inactive family seam admits native full In1 and can activate explicitly excluded Dumpster before selected sequels. Earned completion is simultaneously rejected by the adapter.','runtime_observed':False,'evidence':['graph_evidence.json','tests.json'],'proposal':'One preclaim edge1004.True->1005.In becomes1004.True->1008.In (existing Refused writer). No runtime proposal serialized here.','implementation_blocker':'Earned-history continuation needs an exact reviewed stage/owner adapter, accurate native journal/fact seam and frozen pre-Tower evidence; do not simply call full In1 after Succeeded prerequisite.'}]})
write(O/'proposed_quarantine.json',{'status':'PROPOSAL_ONLY_NOT_SERIALIZED','resource':P,'before_sha256':IDX[P]['sha256'],'changed_edges':[{'remove':['1004','True','1005','In'],'add':['1004','True','1008','In']}],'changed_nodes':[],'new_identifiers':[],'preserve':'All existing nodes/IDs/body resource/saved descendants; no native fact/journal or reward write','limits':['No save transition or engine queued-input fixture is proved','Already-issued owners retain original body; no cancellation/reset','Selected sequel IDs remain INCLUDE but new owner deferred until earned-history seam exists']})
write(O/'provider_requests.json',sorted({d for d in MODELS}|{r for d,m in MODELS.items() if d!=PAR for r in m['refs']}))
write(O/'tests.json',{'status':'PASS_SOURCE_VERIFICATION_WITH_CONFIRMED_POLICY_DEFECT','checks':len(checks),'results':checks,'mutations':mutations,'confirmed_defects':1,'baseline_policy_compliance':'FAIL_EXPECTED_COUNTEREXAMPLE','proposed_in_memory_policy_compliance':'PASS_NEW_OWNER_QUARANTINE_ONLY','runtime_changes':False,'verifier_sha256':sha(Path(__file__))})
print(json.dumps({'checks':len(checks),'sources':len(pins),'confirmed_defects':1,'mutations':len(mutations),'runtime_changes':False}))
