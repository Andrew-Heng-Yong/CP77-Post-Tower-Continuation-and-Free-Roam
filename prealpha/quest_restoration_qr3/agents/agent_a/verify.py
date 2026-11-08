"""Scoped SQ024/MQ056 source-pinned checks. No game/build/deployment writes.

Run with --output NEW_DIRECTORY; output must not exist. Inputs are the current
PH3 payloads and original vanilla exports, never a newly invented recipe.
"""
from pathlib import Path
import argparse,sys,json,gzip,copy,hashlib,collections
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,compare_graph
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
args=parser.parse_args();O=Path(args.output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True)
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
PH3=W/'prealpha/phone_studios_ph3/candidate_01'
P=r'towercontinued\sidejobs_s27\claire\sq024_fresh.questphase';N=r'base\quest\side_quests\sq024\sq024.questphase'
PN=r'towercontinued\sidejobs_s27\phone\claire.questphase';C=r'base\quest\holocalls\claire\claire_holocall.questphase';CS=r'base\quest\holocalls\claire\claire_holocall.scene';CL=r'base\quest\holocalls\claire\claire_cleanup.questphase'
HI=r'base\quest\holocalls\holocall_initializers.questphase';HC=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
SP=r'base\quest\side_quests\sidequests.questphase';HS=r'base\quest\side_quests\sq024\scenes\sq024_00_claire_hook.scene'
RB=r'towercontinued\races_r1\boot.questphase';RO=r'towercontinued\races_r1\owner.questphase';RM=r'towercontinued\races_r1\main.questphase'
NO=r'base\quest\minor_quests\mq056\mq056.questphase';NM=r'base\quest\minor_quests\mq056\phases\mq056_00_main.questphase'
B0=r'towercontinued\b0_claire\claire_service.questphase';ST=r'towercontinued\phone_studios_ph3\studio_support.questphase'
DD=r'base\quest\default_dialogs.questphase'
selected={d for d in MI if '\\sq024\\' in d or '\\mq056\\' in d or '\\holocalls\\claire\\' in d}
selected|={P,PN,HI,HC,SP,RB,RO,RM,B0,ST,DD}
models={};pins=[];checks=[];source_errors=[]
def check(name,ok,evidence):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence})
 assert ok,name
for d in sorted(selected):
 r=IDX[d];j=Path(r['json']);raw=j.with_suffix('')
 if d.startswith('towercontinued\\'):raw=PH3/'archive_source'/Path(d.replace('\\','/'))
 elif not raw.exists() and '\\json\\' in str(j):raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file(),str(raw)
 check('binary pin '+d,sha(raw)==r['sha256'],str(raw))
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 check('raw JSON/cache identity '+d,m==cached,{'json':str(j),'json_sha256':sha(j)})
 models[d]=m
 pins.append({'depot':d,'binary':str(raw),'sha256':sha(raw),'source_json':str(j),'json_sha256':sha(j),'provider':r['archive'],'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model'])})
 source_errors += [{'depot':d,'error':x} for x in m['errors']]
def g(d,gp='root'):return models[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
def rewrite(x,changes):
 if isinstance(x,dict):return {k:rewrite(v,changes) for k,v in x.items()}
 if isinstance(x,list):return [rewrite(v,changes) for v in x]
 return changes.get(x,x) if isinstance(x,str) else x
def evalc(x,fs,js):
 t=x['$type']
 if t=='questLogicalCondition':
  vs=[evalc(c,fs,js) for c in x['conditions']]
  return {'AND':all(vs),'OR':any(vs),'NOR':not any(vs)}[x['operation']]
 if t in ('questFactsDBCondition','questJournalCondition'):return evalc(x['type'],fs,js)
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in fs:return False
  a=fs[x['factName']];b=x['value']
  return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  if x['path']['realPath'] not in js:return False
  return (js[x['path']['realPath']]==x['state']) != bool(x.get('inverted',0))
 raise ValueError('Unsupported predicate '+t)
spec=read(W/'prealpha/sidejobs_s27/claire/contract03.json');s=spec['owners'][0]
fs=spec['common_equal']|s['facts_equal']|{k:v['min'] for k,v in s['fact_ranges'].items()}|{s['tag']+'_Permit':1,s['tag']+'_Issued':0,s['tag']+'_Fault':0,s['tag']+'_Finished':0,spec['phone']['support_fact']:1}
js={x['path']:'Inactive' for x in s['journals']}
native_phase=copy.deepcopy(n(SP,50)['payload']);native_phase['id']=100
check('fresh wrapper native parent phase identity',n(P,100)['payload']==native_phase,{'native':SP,'node':50,'current':P,'node_current':100})
check('native parent earned q101 prerequisite',n(SP,31)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'q101_enable_side_content','value':0}] and edge(SP,31,'Out',50,'sq024_in'),{'node':31,'edge':'31.Out ->50.sq024_in'})
manifest=read(W/'prealpha/sidejobs_s27/claire/build/claire_03/component.json')
qr=manifest['native_resources'][r'base\quest\side_quests\sq024\sq024.quest'];qraw=W/qr['raw'];qjson=W/qr['json']
check('original native quest contact source pin',sha(qraw)==qr['raw_sha256'] and sha(qjson)==qr['json_sha256'],qr)
qm=Resource(read(qjson)).normalize();expected=copy.deepcopy(qm['graphs']['root']['nodes']['13']['payload']);expected['id']=93
check('native add Claire contact retained',n(P,93)['payload']==expected,{'source':str(qjson),'original_node':13,'current_node':93,'contact':'contacts/marianne'})
pins.append({'depot':r'base\quest\side_quests\sq024\sq024.quest','binary':str(qraw),'sha256':sha(qraw),'source_json':str(qjson),'json_sha256':sha(qjson),'provider':'Recorded original component source; coordinator bounded lookup requested'})
entry_edges=[['0','Out','1','In'],['1','Out','2','In'],['2','Out','3','In'],['3','False','2','In'],['3','True','4','In'],['4','Out','89','In'],['89','Out','90','In'],['90','True','92','In'],['90','False','91','In'],['92','Out','93','In'],['93','Out','100','sq024_in'],['100','sq024_out','101','In']]
check('actual fresh route exact sockets',g(P)['edges']==sorted(entry_edges),entry_edges)
check('postclaim two tick wait',n(P,89)['payload']['condition']['type']['tickCount']==2,{'node':89})
for i in [2,3,90]:
 f=fs|{s['tag']+'_Issued':int(i==90)};c=n(P,i)['payload']['condition']
 check('fresh admissible serialized '+str(i),evalc(c,f,js),{'node':i,'journals':len(js),'facts':len(f)})
 for root in s['ids']:
  p=next(x['path'] for x in s['journals'] if x['path'].split('/')[-1]==root)
  for state in ['Active','Succeeded','Failed']:
   check('reject prior '+root+' '+state+' '+str(i),not evalc(c,f,js|{p:state}),{'path':p,'state':state,'guard':i})
 for name in ['q307_done','q307_main_game_killed','q101_enable_side_content',spec['phone']['support_fact']]:
  check('refuse absent input '+name+' '+str(i),not evalc(c,{k:v for k,v in f.items() if k!=name},js),{'guard':i})
 check('refuse missing root '+str(i),not evalc(c,f,{k:v for k,v in js.items() if k!='quests/meta/07_nc_underground'}),{'guard':i})
 check('refuse story done '+str(i),not evalc(c,f|{'sq024_done':1},js),{'guard':i})
 check('refuse replay owned '+str(i),not evalc(c,f|{'PTFRR1_Issued':1},js),{'guard':i})
 # Every historic counter is deliberately unconstrained: these are not ack resets.
 hist={f'holo_{direction}_{suffix}':77 for direction in ['claire_calls_v','v_calls_claire'] for suffix in ['start_count','end_count','start_done','end_done']}
 check('history counters do not block fresh admission '+str(i),evalc(c,f|hist,js),{'guard':i})
check('native q105 token and offsite gates retained',n(N,6,'root/92')['reads'][0]=={'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'q105_done','value':0} and n(N,7,'root/92')['payload']['condition']['operation']=='AND' and edge(N,6,'Out',7,'In','root/92'),{'graph':'root/92','q105':6,'token_and_trigger':7})
check('no native reset ack journal writes by fresh wrapper',all(w['factName'].startswith(s['tag']+'_') for gr in models[P]['graphs'].values() for x in gr['nodes'].values() for w in x['writes']) and all(x['type']!='questJournalNodeDefinition' for x in g(P)['nodes'].values()),P)
check('phone native initializer copied exact',n(PN,46)['payload']==n(HI,46)['payload'],{'initializer':46,'native_controller':C})
check('phone wrapper actual admission route',all(edge(PN,*e) for e in [[1000,'Out',1001,'In'],[1001,'Out',1002,'In'],[1002,'Out',1003,'In'],[1003,'False',1002,'In'],[1003,'True',1004,'In'],[1004,'Out',46,'In1']]),{'native_entry':46})
for i in [1002,1003]:
 c=n(PN,i)['payload']['condition'];f=fs|{'PTFRS27_PHONE_CLAIRE_Issued':0};check('listener claims before own caller '+str(i),evalc(c,f,js),i)
 check('listener refuses pending external start '+str(i),not evalc(c,f|{'holo_claire_calls_v_start_activate':1},js),i)
for a,sock,b,dest in [(20,'Out',1,'In1'),(1,'Out1',0,'In'),(0,'Out',28,'In'),(28,'False',9,'In'),(9,'Out',21,'holo_claire_calls_v_start'),(2,'Out',10,'In'),(10,'Out',21,'holo_claire_calls_v_end'),(3,'Out',30,'In'),(30,'False',11,'In'),(11,'Out',21,'holo_v_calls_claire_start'),(4,'Out',12,'In'),(12,'Out',21,'holo_v_calls_claire_end')]:
 check('native controller connected '+str(a)+sock+str(b),edge(C,a,sock,b,dest),{'edge':[a,sock,b,dest]})
for writer,wait,clear in [(312,306,307),(313,308,309)]:
 check('caller request ack wait clear '+str(writer),edge(HS,writer,'0:0',wait,'0:1','scene') and edge(HS,wait,'0:0',clear,'0:1','scene'),{'producer':writer,'wait':wait,'clear':clear,'writes':n(HS,writer,'scene')['writes'],'reads':n(HS,wait,'scene')['reads']})
for scene,pairs in [
 (r'base\quest\side_quests\sq024\scenes\sq024_02_santo_domingo_race.scene',[(1114,1107,1108),(1115,1109,1110)]),
 (r'base\quest\side_quests\sq024\scenes\sq024_03_badlands_race.scene',[(1188,1181,1182),(1189,1183,1184)]),
 (r'base\quest\side_quests\sq024\scenes\sq024_04_city_race.scene',[(1437,1430,1431),(1438,1432,1433)]),
 (r'base\quest\side_quests\sq024\scenes\sq024_05_big_race.scene',[(1188,1181,1182),(1189,1183,1184)])]:
 for writer,wait,clear in pairs:
  check('race outgoing request ack continuation '+scene+str(writer),edge(scene,writer,'0:0',wait,'0:1','scene') and edge(scene,wait,'0:0',clear,'0:1','scene') and any(x['factName'].startswith('holo_v_calls_claire_') and x['factName'].endswith('_done') and x['comparisonType']=='Greater' and x['value']==0 for x in n(scene,wait,'scene')['reads']),{'request':writer,'wait':wait,'clear':clear})
for ack in [41,42,43,44]:
 check('native actual ack writer '+str(ack),any(w['factName'].endswith('_done') and w['value']==1 for w in n(CS,ack,'scene')['writes']),{'node':ack,'incoming':[e for e in g(CS,'scene')['edges'] if e[2]==str(ack)]})
check('native rejection and interrupt retention',edge(r'base\quest\side_quests\sq024\phases\sq024_00_hook.questphase',2,'Holocall INT',30,'In') and edge(r'base\quest\side_quests\sq024\phases\sq024_00_hook.questphase',2,'Holocall RET',29,'In'),{'hook':'2.INT ->30 end;2.RET ->29 start;call_rejected ->31'})
check('matching cleanup wired in shared chain',n(HC,1003)['refs']==[CL] and edge(HC,1002,'True',1003,'In7') and edge(HC,1003,'Out7',1240,'In'),{'condition':1002,'cleanup':1003,'next':1240})
check('native outgoing and incoming cleanup edges',all(edge(CL,*e) for e in [[2,'Out',4,'In'],[4,'True',6,'In'],[6,'Out',0,'holo_claire_calls_v_end'],[4,'False',5,'In'],[5,'True',7,'In'],[7,'Out',1,'holo_v_calls_claire_end'],[5,'False',3,'In']]),{'counts':[n(CL,x)['reads'] for x in [4,5]]})
check('full MQ056 owner preserved except main resource relocation',not compare_graph(models[NO],models[RO],{NM:RM}),{'native':NO,'private':RO,'only_relocation':{NM:RM}})
# Comparison of retained native payload/socket/nested-graph content avoids a
# reachability-summary artifact from the added two nodes.
for gp,gr in models[NM]['graphs'].items():
 check('MQ056 main retained native graph '+gp,all(g(RM,gp)['nodes'][i]==n for i,n in gr['nodes'].items()) and all(e in g(RM,gp)['edges'] for e in gr['edges'] if e!=['0','Out','34','In']),{'graph':gp,'nodes':len(gr['nodes']),'edges':len(gr['edges'])})
check('MQ056 main exact added invitation routing',set(map(tuple,g(RM)['edges']))-set(map(tuple,g(NM)['edges']))=={('0','Out','1000','In'),('1000','False','34','In'),('1000','True','1001','In'),('1001','Out','23','In1')},'Delivered invitation resumes23;else original34')
for state,expected in [('Inactive',False),('Active',True),('Succeeded',True),('Failed',False)]:
 check('MQ056 invitation resume '+state,evalc(n(RM,1000)['payload']['condition'],{}, {'contacts/announcer_mq056/mq056_hook/01_hook2':state})==expected,state)
for i in [2,3]:
 c=n(RB,i)['payload']['condition'];f={x['factName']:x['value'] for x in n(RB,i)['reads'] if x.get('factName')};f['sq024_done']=1
 jj={'quests/minor_quest/mq056_race_replay/'+x:'Inactive' for x in ['01_city_center','02_badlands','03_santo_domingo','04_big_race']}
 check('MQ056 earned completion gate '+str(i),evalc(c,f,jj) and not evalc(c,f|{'sq024_done':0},jj),{'guard':i})
 for p in jj:check('MQ056 active race excluded '+str(i)+p,not evalc(c,f,jj|{p:'Active'}),{'guard':i,'phase':p})
check('native inline hackable helper retained not missing external resource',len(g(N,'root/53/55')['nodes'])==20 and len(g(N,'root/53/55')['edges'])==28 and edge(N,0,'Out',55,'make_hackable_in','root/53'),{'embedded_graph':'root/53/55','entries':g(N,'root/53/55')['entries']})
parent=copy.deepcopy(n(DD,19,'root/4')['payload']);parent['id']=5
check('B0 Claire native parent prefab preserved',n(B0,5)['payload']==parent,{'native_graph':'root/4','native_node':19,'current_node':5,'prefab':'#pr_claire_default'})
def edge_with_owned_diagnostics(gr,e,allowed):
 if e in gr['edges']:return True
 starts=[b for a,s,b,t in gr['edges'] if a==e[0] and s==e[1] and b in allowed]
 seen=set();todo=starts[:]
 while todo:
  i=todo.pop()
  if i in seen:continue
  seen.add(i)
  for a,s,b,t in gr['edges']:
   if a!=i:continue
   if b==e[2] and t==e[3]:return True
   if b in allowed:todo.append(b)
 return False
for gp,gr in models[DD]['graphs'].items():
 if gp!='root/4/19' and not gp.startswith('root/4/19/'):continue
 newgp=gp.replace('root/4/19','root/5',1);curr=g(B0,newgp);extra=set(curr['nodes'])-set(gr['nodes'])
 check('B0 Claire retained native payloads '+newgp,all(curr['nodes'][i]['payload']==nn['payload'] and curr['nodes'][i]['sockets']==nn['sockets'] for i,nn in gr['nodes'].items()),{'native_graph':gp,'current_graph':newgp,'nodes':len(gr['nodes'])})
 check('B0 Claire additions owned diagnostics only '+newgp,all(curr['nodes'][i]['type']=='questFactsDBManagerNodeDefinition' and curr['nodes'][i]['writes'] and all(w['factName'].startswith('PTFRB0CLA_') for w in curr['nodes'][i]['writes']) for i in extra),{'new_nodes':sorted(extra)})
 check('B0 Claire native edges retained via diagnostics '+newgp,all(edge_with_owned_diagnostics(curr,e,extra) for e in gr['edges']),{'native_edges':len(gr['edges'])})
check('native quest role reactivation precedes default service release',edge(r'base\quest\side_quests\sq024\phases\sq024_01_garage.questphase',96,'Out',111,'In','root/54') and n(r'base\quest\side_quests\sq024\phases\sq024_01_garage.questphase',111,'root/54')['writes'][0]['factName']=='claire_default_on',{'quest_role':96,'default_off':111})
check('all485 historical journal class paths preserved',len(js)==485 and all(sorted((x['path']['realPath'],value(x['path']['className']),x['state']) for x in n(P,i)['reads'] if x.get('$type')=='questJournalEntryState_ConditionType')==sorted((x['path'],x['class'],'Inactive') for x in s['journals']) for i in [2,3,90]),{'journal_predicates':485,'guards':[2,3,90]})
BR=r'base\quest\side_quests\sq024\phases\sq024_05_the_big_race.questphase'
MSG=r'base\quest\side_quests\sq024\phases\text_messages\sq024_03_msg_big_race.questphase'
check('native failed story journal route retained',edge(N,8,'Out',6,'Failed','root/22') and 'quests/meta/07_nc_underground' in n(N,6,'root/22')['journal_paths'],{'graph':'root/22','failed_node':6})
check('native success story journal routes retained',edge(BR,7,'Out',6,'Succeeded','root/114') and edge(MSG,134,'Out',133,'Succeeded') and 'quests/meta/07_nc_underground' in n(MSG,133)['journal_paths'],{'final_race_graph':'root/114','final_race_node':6,'message_node':133})
check('native durable story completed and service handback retained',n(N,4,'root/68')['writes']==[{'$type':'questSetVar_NodeType','factName':'sq024_done','setExactValue':1,'value':1}] and edge(N,3,'Out',4,'In','root/68'),{'cleanup_graph':'root/68','done_node':4,'quest_active_zero':3,'default_claire_reactivate':7})
reward_sites=[(N,'root/54',33,'QuestRewards.sq024_finish_big_race'),(BR,'root/57/185/116',50,'QuestRewards.sq024_win_big_race'),(BR,'root/57/185/116/118',7,'QuestRewards.sq024_finish_big_race')]
for d,gp,i,record in reward_sites:
 check('native reward pointer preserved '+record+gp,any(x.get('$type')=='TweakDBID' and value(x)==record for x in walk(n(d,i,gp)['payload'])),{'resource':d,'graph':gp,'node':i,'record':record,'target_definition':'Not resolved by graph proof'})
mutations=[]
bad=copy.deepcopy(n(P,3)['payload']['condition'])
for x in walk(bad):
 if x.get('$type')=='questJournalEntryState_ConditionType' and x['path']['realPath']=='quests/meta/07_nc_underground':x['state']='Active'
mutations.append({'fault':'admit active story root','detected':evalc(bad,fs,js|{'quests/meta/07_nc_underground':'Active'}) and not evalc(n(P,3)['payload']['condition'],fs,js|{'quests/meta/07_nc_underground':'Active'})})
bad=copy.deepcopy(g(P));bad['edges'].remove(['93','Out','100','sq024_in']);mutations.append({'fault':'lose native story entry edge','detected':bad['edges']!=sorted(entry_edges)})
bad=copy.deepcopy(g(C));bad['edges'].remove(['9','Out','21','holo_claire_calls_v_start']);mutations.append({'fault':'lose incoming phone listener continuation','detected':['9','Out','21','holo_claire_calls_v_start'] not in bad['edges']})
bad=copy.deepcopy(g(HC));bad['edges'].remove(['1003','Out7','1240','In']);mutations.append({'fault':'lose shared phone cleanup continuation','detected':['1003','Out7','1240','In'] not in bad['edges']})
bad=copy.deepcopy(models[RO]);bad['graphs']['root']['nodes']['9']['payload']['phaseResource']['DepotPath']['$value']=NM
mutations.append({'fault':'replace corrected R1 main donor with old native main','detected':bool(compare_graph(models[NO],bad,{NM:RM}))})
for v in mutations:check('mutation '+v['fault'],v['detected'],v)
trace=[];bindings=[];refs=set();root_prefabs={}
for d,m in models.items():
 refs.update(m['refs']);root_prefabs[d]=m['root_prefabs']
 for gp,gr in m['graphs'].items():
  for i,x in gr['nodes'].items():
   if x['reads'] or x['writes'] or x['journal_paths'] or x['reward'] or x['sms']:
    trace.append({'resource':d,'graph':gp,'node':i,'payload':x['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if x['prefabs'] or x['node_refs']:bindings.append({'resource':d,'graph':gp,'node':i,'prefabs':x['prefabs'],'node_refs':x['node_refs']})
scripts={}
for name in ['PTFR_SideJobsS27.reds','PTFR_B0Claire.reds','PTFR_JohnnyVoiceJV1.reds']:
 p=PH3/'package/r6/scripts/PTFR_Consolidated'/name;scripts[str(p)]={'sha256':sha(p)}
write(O/'source_pins.json',pins);write(O/'graph_evidence.json',{'trace':trace,'bindings':bindings,'root_prefabs':root_prefabs,'source_errors':source_errors,'script_pins':scripts})
write(O/'dependency_depots.json',{'depots':sorted(refs|set(models)),'scope':'Graph and declared asset references, not proof of decoded placement or runtime resolution'})
write(O/'tests.json',{'status':'PASS_SCOPED_STATIC_CHECKS','checks':len(checks),'results':checks,'mutations':mutations,'sources':len(pins),'node_count':sum(len(g['nodes']) for m in models.values() for g in m['graphs'].values()),'source_errors':source_errors,'runtime_changes':[],'scope':'Exact native delegation and current wrapper predicates/routes; not world/TweakDB/save/engine certification'})
print(json.dumps({'status':'PASS_SCOPED_STATIC_CHECKS','checks':len(checks),'mutations':len(mutations),'sources':len(pins),'source_errors':len(source_errors)}))
