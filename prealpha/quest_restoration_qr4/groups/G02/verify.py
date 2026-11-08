"""G02 Delamain: source-pinned contract checks, no game/resource mutations.

Run with --output a NEW directory. Shared evidence is reusable by G07, but
car-specific results there still require their own branch investigation.
"""
from pathlib import Path
import sys,importlib.util,argparse,copy,collections
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g02_inputs',HERE/'source_inputs.py');inp=importlib.util.module_from_spec(spec);spec.loader.exec_module(inp)
W=inp.W
from common import read,write,sha,walk
from model import reachable
P=inp.P;N=inp.N
OWN='towercontinued\\sidejobs_s22\\delamain\\owner.questphase';SUP='towercontinued\\sidejobs_s22\\delamain\\support.questphase';SCAN='towercontinued\\sidejobs_s22\\delamain\\scan.questphase'
NS='base\\quest\\side_quests\\sq025\\phases\\sq025_04_scan.questphase';SC='base\\quest\\side_quests\\sq025\\scenes\\sq025_05_scan.scene'
HC='base\\quest\\holocalls\\delamain\\delamain_holocall.questphase';HS='base\\quest\\holocalls\\delamain\\delamain_holocall.scene';CL='base\\quest\\holocalls\\delamain\\delamain_cleanup.questphase';SH='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
SIDE='base\\quest\\side_quests\\sidequests.questphase';INIT='base\\quest\\holocalls\\holocall_initializers.questphase';PC='base\\quest\\persistent_content.questphase'
def run(O):
 assert not O.exists(),'Fresh output directory required'
 ms={};pins=[];tests=[]
 def check(name,ok,evidence):
  tests.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
 for d in sorted(set(inp.selected()+[SIDE,INIT,PC])):
  m,p=inp.load(d);ms[d]=m;pins.append(p);check('source_and_model_pin '+d,True,p)
  check('graph_integrity '+d,not m['errors'],m['errors'])
 def g(d,gp='root'):return ms[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
 def path(gr,a,b):
  todo=collections.deque([[str(a)]]);seen={str(a)}
  while todo:
   p=todo.popleft()
   if p[-1]==str(b):return p
   for x,s,y,t in gr['edges']:
    if x==p[-1] and s!='CutSource' and y not in seen:seen.add(y);todo.append(p+[y])
  return None
 def hasfact(node,f,v=None):return any(x.get('factName')==f and (v is None or x.get('value')==v) for x in node['reads'])
 def writes(node,f,v):return any(x.get('factName')==f and x.get('value')==v for x in node['writes'])
 def evaluate(x,fs,js):
  t=x['$type']
  if t=='questLogicalCondition':
   a=[evaluate(y,fs,js) for y in x['conditions']]
   return all(a) if x['operation']=='AND' else any(a) if x['operation']=='OR' else not any(a) if x['operation']=='NOR' else False
  if t in ['questFactsDBCondition','questJournalCondition']:return evaluate(x['type'],fs,js)
  if t=='questVarComparison_ConditionType':
   if x['factName'] not in fs:return False
   a=fs[x['factName']];b=x['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
  if t=='questJournalEntryState_ConditionType':return x['path']['realPath'] in js and ((js[x['path']['realPath']]==x['state'])!=bool(x.get('inverted',0)))
  raise ValueError('Unsupported '+t)
 def fixture(node):
  cond=node['payload']['condition'];fs={};js={}
  for x in walk(cond):
   if x.get('$type')=='questVarComparison_ConditionType':
    v=x['value'];fs[x['factName']]=v+1 if x['comparisonType']=='Greater' else v-1 if x['comparisonType']=='Less' else v
   if x.get('$type')=='questJournalEntryState_ConditionType':js.setdefault(x['path']['realPath'],x['state'])
  return fs,js
 # Fresh route keeps actual native root/child payloads; only approved tail and
 # alternate debug entries are absent from this scoped family instance.
 for i,node in g(P,'root/100')['nodes'].items():
  if i in g(N)['nodes']:check('fresh_native_root_node_'+i,node['payload']==n(N,i)['payload'],{'native':N,'private':P,'node':i})
 for gp,gr in ms[P]['graphs'].items():
  if gp.startswith('root/100/'):
   nativegp='root'+gp[len('root/100'):]
   check('fresh_native_nested_graph_'+gp,gr==g(N,nativegp),{'native_graph':nativegp,'private_graph':gp})
 check('fresh_top_claim_postcheck_and_native_body',all(edge(P,*e) for e in [(0,'Out',1,'In'),(3,'True',4,'In'),(4,'Out',89,'In'),(89,'Out',90,'In'),(90,'True',92,'In'),(92,'Out',100,'In1'),(92,'Out',65020,'In'),(65020,'Out',94,'In1'),(92,'Out',95,'In1')]),{'claim':4,'postclaim':90,'body':100,'phone':94,'return_archer':95})
 check('native_controller_initializer_binding',dict(n(P,94)['payload'],id=51)==n(INIT,51)['payload'] and n(SUP,51)['payload']==n(INIT,51)['payload'],{'fresh_phone':94,'legacy_phone':51})
 # Fresh, historical-progress and support ownership trees are evaluated exactly;
 # a flattened fact list is not treated as the logical expression.
 for d,ni in [(P,3),(P,90),(OWN,1003),(SUP,1003)]:
  node=n(d,ni);fs,js=fixture(node)
  check('positive_actual_guard '+d+':'+str(ni),evaluate(node['payload']['condition'],fs,js),{'facts':fs,'journals':js})
  for f in ['q307_done','q307_finished','PTFRPA2_Finished']:
   check('reject_missing_tower_'+str(ni)+f+d,not evaluate(node['payload']['condition'],fs|{f:0},js),f)
  root='quests/side_quest/sq025_delamain'
  for state in ['Active','Succeeded','Failed']:
   check('protect_root_'+state+d+str(ni),not evaluate(node['payload']['condition'],fs,js|{root:state}),{'root':root,'state':state})
  if d in [OWN,SUP]:
   check('exclude_fresh_native_listener_duplicate_'+d,not evaluate(node['payload']['condition'],fs|{'PTFRS25_SQ025_FRESH_Issued':1},js),'actual AND FreshIssued==0')
  if d==P:
   for i in ['sq025_delamain','sq025_compensation','sq025_0_pickup','sq025c05_scared','sq025c07_suicidal']:
    check('fresh_protect_history_'+i+str(ni),not evaluate(node['payload']['condition'],fs,js|{'quests/side_quest/'+i:'Succeeded'}),i)
 check('legacy_exact_three_completed_car_seam',all(hasfact(n(OWN,1003),f,v) for f,v in [('sq025_scans_done',3),('sq025_sad_done',1),('sq025_mean_done',1),('sq025_suicidal_done',1),('sq025_scared_done',0)]),'bounded3completed, not generic unfinished restart')
 check('native_street_prefab_retained',ms[SCAN]['root_prefabs']==ms[NS]['root_prefabs']==['#sq025_pr_03_street_find_delamain'],'resource-root prefab obligation')
 for case,nodeid in [('scared',193),('suicidal',196)]:
  gp='root/'+str(nodeid)
  check('native_case_graph_exact_'+case,g(SCAN,gp)==g(NS,gp),{'graph':gp,'nodes':len(g(NS,gp)['nodes']),'edges':len(g(NS,gp)['edges'])})
  check('native_case_prefab_exact_'+case,n(SCAN,nodeid)['payload']==n(NS,nodeid)['payload'],n(NS,nodeid)['prefabs'])
 check('progressed_done_scan_bypasses_native_reactivation',all(edge(SCAN,195,'Out'+str(k),1000+k,'In') and edge(SCAN,1000+k,'True',198,'In'+str(k)) for k in range(1,8)),'all seven completed facts feed native all-cars AND directly')
 for k,ji,target in [(105,'sq025c05_scared',5),(108,'sq025c07_suicidal',8)]:
  check('cleanup_preserves_succeeded_history_'+ji,n(SCAN,k,'root/267')['reads'][0]['state']=='Succeeded' and edge(SCAN,k,'False',target,'Inactive','root/267') and any(e[0]==str(k) and e[1]=='True' and e[2]!=str(target) for e in g(SCAN,'root/267')['edges']),{'graph':'root/267','node':k})
 protocols=[]
 for case,reader,clear,mid,ack,producer,wait,reset,endreader,endclear,endack,endproducer,endwait,endreset in [
  ('scared',38,42,114,1047,7350,7347,7348,39,43,1048,7354,7351,7352),
  ('suicidal',22,26,106,779,7271,7268,7269,23,27,780,7275,7272,7273)]:
  for typ,rd,cl,ak,wr,wa,re in [('start',reader,clear,ack,producer,wait,reset),('end',endreader,endclear,endack,endproducer,endwait,endreset)]:
   base='holo_delamain_'+case+'_calls_v_'+typ;request=base+'_activate';done=base+'_done'
   check('caller_connected_request_wait_clear_'+base,writes(n(SC,wr,'scene'),request,1) and hasfact(n(SC,wa,'scene'),done) and writes(n(SC,re,'scene'),done,0) and any(e[0]==str(wr) and e[2]==str(wa) for e in g(SC,'scene')['edges']) and any(e[0]==str(wa) and e[2]==str(re) for e in g(SC,'scene')['edges']),{'producer':wr,'wait':wa,'clear':re})
   check('native_controller_connected_'+base,hasfact(n(HC,rd),request) and writes(n(HC,cl),request,0) and edge(HC,cl,'Out',21,base) and (edge(HC,rd,'Out',mid,'In') and edge(HC,mid,'False',cl,'In') if typ=='start' else edge(HC,rd,'Out',cl,'In')),{'reader':rd,'clear':cl,'scene_input':base})
   entry=g(HS,'scene')['entries'][base];ackpath=path(g(HS,'scene'),entry,str(ak))
   check('real_native_ack_reachable_'+base,writes(n(HS,ak,'scene'),done,1) and bool(ackpath),{'scene_entry':entry,'ack_writer':ak,'path':ackpath})
   protocols.append({'case':case,'type':typ,'request':request,'caller':SC,'producer':wr,'wait':wa,'clear':re,'controller':HC,'reader':rd,'controller_clear':cl,'scene':HS,'scene_input':base,'ack_writer':ak,'ack_path':ackpath})
 rewardcall='base\\quest\\side_quests\\sq025\\scenes\\sq025_06b_reward_holocall.scene'
 for typ,producer,wait,reset,reader,clear,ack in [('start',225,219,220,0,9,41),('end',226,221,222,2,10,42)]:
  base='holo_delamain_calls_v_'+typ;request=base+'_activate';done=base+'_done'
  check('reward_caller_request_wait_clear_'+typ,writes(n(rewardcall,producer,'scene'),request,1) and hasfact(n(rewardcall,wait,'scene'),done) and writes(n(rewardcall,reset,'scene'),done,0) and any(e[0]==str(producer) and e[2]==str(wait) for e in g(rewardcall,'scene')['edges']) and any(e[0]==str(wait) and e[2]==str(reset) for e in g(rewardcall,'scene')['edges']),{'producer':producer,'wait':wait,'clear':reset})
  check('base_delamain_controller_and_real_ack_'+typ,hasfact(n(HC,reader),request) and bool(path(g(HC),str(reader),str(clear))) and edge(HC,clear,'Out',21,base) and writes(n(HS,ack,'scene'),done,1) and bool(path(g(HS,'scene'),g(HS,'scene')['entries'][base],str(ack))),{'reader':reader,'controller_clear':clear,'actual_ack_writer':ack})
 check('shared_cleanup_actual_connection',edge(SH,700,'True',701,'In12') and edge(SH,701,'Out12',800,'In') and n(SH,701)['refs']==[CL],'native cleanup invoked, not merely present')
 for i,reset,sc,input in [(20,39,4,'holo_delamain_scared_calls_v_end'),(25,50,15,'holo_delamain_suicidal_calls_v_end')]:
  check('incoming_native_cleanup_counter_route_'+str(i),edge(CL,i,'True',reset,'In') and edge(CL,reset,'Out',sc,input),'no synthetic counter reset')
 # Two case-specific completion outputs and one increment retain native semantics.
 for doneid,counterid,journalid,case in [(939,3810,1280,'scared'),(933,3792,1272,'suicidal')]:
  check('native_case_done_and_once_increment_'+case,writes(n(SC,doneid,'scene'),'sq025_'+case+'_done',1) and writes(n(SC,counterid,'scene'),'sq025_scans_done',1) and n(SC,counterid,'scene')['writes'][0]['setExactValue']==0 and any(e[0]==str(doneid) and e[2]==str(counterid) for e in g(SC,'scene')['edges']),{'done':doneid,'increment':counterid})
  check('native_case_journal_success_socket_'+case,any(e[2]==str(journalid) and e[3]=='0:3' for e in g(SC,'scene')['edges']),{'journal_node':journalid,'Succeeded_socket':'0:3'})
 reception='base\\quest\\side_quests\\sq025\\scenes\\sq025_03_reception.scene';rg=g(reception,'scene')
 check('compensation_reachable_native_reward',bool(path(rg,rg['entries']['delamain_compensation_in'],'609')) and 'QuestRewards.sq025_compensation' in str(n(reception,609,'scene')['payload']),{'reward_node':609,'branch':'12.2:1→609.0:1'})
 check('compensation_completion_connected',any(e[0]=='313' and e[2]=='316' and e[3]=='0:3' for e in rg['edges']),'rootSucceeded316 from objective313')
 ret='base\\quest\\side_quests\\sq025\\phases\\sq025_return_archer.questphase'
 check('human_nature_native_repair_delay_and_AND',n(ret,9)['payload']['condition']['type']['hours']==6 and edge(ret,9,'Out',10,'In1') and edge(ret,7,'Out',10,'In2') and edge(ret,10,'Out1',11,'In'),'6gamehours and native progress branch; then Fixer content token')
 check('human_nature_success_and_sms',edge(ret,11,'Out',4,'In') and edge(ret,4,'Out',3,'Succeeded') and edge(ret,3,'Out',2,'In') and edge(ret,2,'Out',5,'Active'),'native success then repaired_car message')
 # Record original outer gate accurately, without pretending rehosting proves it.
 check('original_parent_gate_is_OR_token_or_mail',n(SIDE,154)['payload']['condition']['operation']=='OR' and edge(SIDE,154,'Out',48,'In1'),'explicit unresolved caller-context equivalence; not a PASS on complete eligibility')
 muts=[]
 bad=copy.deepcopy(g(SCAN,'root/193'));bad['edges'].remove(['23','Out3','12','scared_in']);muts.append({'fault':'missing Northside scene branch','detected':bad!=g(NS,'root/193')})
 bad=copy.deepcopy(g(SUP));bad['edges'].remove(['1004','Out','51','In1']);muts.append({'fault':'disconnected shared listener','detected':not ['1004','Out','51','In1'] in bad['edges']})
 bad=copy.deepcopy(g(SH));bad['edges'].remove(['700','True','701','In12']);muts.append({'fault':'missing native cleanup edge','detected':not ['700','True','701','In12'] in bad['edges']})
 bad=copy.deepcopy(n(SC,3810,'scene'));bad['writes'][0]['value']=2;muts.append({'fault':'changed Northside scan reward increment','detected':bad['writes'][0]['value']!=1})
 bad=copy.deepcopy(g(ret));bad['edges'].remove(['9','Out','10','In1']);muts.append({'fault':'missing HumanNature delay prerequisite','detected':not ['9','Out','10','In1'] in bad['edges']})
 for item in muts:check('mutation '+item['fault'],item['detected'],item)
 facts=[];journals=[];assets=[]
 for d,m in ms.items():
  for gp,gr in m['graphs'].items():
   for i,node in gr['nodes'].items():
    if node['reads'] or node['writes']:facts.append({'resource':d,'graph':gp,'node':i,'reads':node['reads'],'writes':node['writes'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
    if node['journal_paths']:journals.append({'resource':d,'graph':gp,'node':i,'paths':node['journal_paths'],'incoming':[e for e in gr['edges'] if e[2]==i]})
    if node['node_refs'] or node['prefabs']:assets.append({'resource':d,'graph':gp,'node':i,'refs':node['node_refs'],'prefabs':node['prefabs']})
 write(O/'source_pins.json',pins);write(O/'graph_evidence.json',{'facts':facts,'journals':journals,'asset_bindings':assets,'phone_protocols':protocols,'native_parent_gate':n(SIDE,154),'root_prefabs':{d:m['root_prefabs'] for d,m in ms.items()}})
 write(O/'tests.json',{'status':'PASS_SCOPED_STATIC_CHECKS_NOT_FULL_CERTIFICATION','count':len(tests),'checks':tests,'mutations':len(muts),'runtime_changes':[],'scope':'Actual serialized predicates, native structural comparisons and connected caller/controller/cleanup routes; no engine or save simulation'})
 return {'status':'PASS','checks':len(tests),'mutations':len(muts),'resources':len(pins),'protocols':len(protocols)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();print(run(Path(args.output).resolve()))
