"""Read-only deep checks for MQ041/MQ044/MQ049. Fresh output required."""
from pathlib import Path
import sys,json,gzip,hashlib,copy,argparse,collections
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
O=Path(args.output).resolve();assert not O.exists(),'Preserve pinned results; use fresh output';O.mkdir(parents=True)
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=json.loads((A/'resource_inventory.json').read_text());MI=json.loads((A/'model_inventory.json').read_text())
P41=r'towercontinued\sidejobs_s23\base_a\mq041_corpo.questphase';P44=r'towercontinued\sidejobs_s23\base_a\mq044_jakes_vehicle.questphase';P49=r'towercontinued\sidejobs_s23\base_b\mq049.questphase'
PAR=r'base\quest\minor_quests\minorquests.questphase';BUG=r'base\quest\bugfixing\quest_bugfixing.questphase';N41=r'base\quest\minor_quests\mq041\mq041_corpo.questphase';N44=r'base\quest\minor_quests\mq044\phases\mq044.questphase';N49=r'base\quest\minor_quests\mq049\mq049.questphase'
C=r'base\quest\holocalls\frank\frank_holocall.questphase';CS=r'base\quest\holocalls\frank\frank_holocall.scene';CL=r'base\quest\holocalls\frank\frank_cleanup.questphase';PC=r'towercontinued\sidejobs_s23\phone\frank.questphase'
INIT=r'base\quest\holocalls\holocall_initializers.questphase';SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';ST=r'towercontinued\phone_studios_ph3\studio_support.questphase'
HOOK=r'base\quest\minor_quests\mq041\phases\mq041_corpo_01_hook.questphase';HC=r'base\quest\minor_quests\mq041\scenes\mq041_corpo_01_deadmans_switch.scene';MAIN41=r'base\quest\minor_quests\mq041\phases\mq041_corpo_00_main.questphase';END41=r'base\quest\minor_quests\mq041\phases\mq041_corpo_02_confrontation.questphase'
MAIN44=r'base\quest\minor_quests\mq044\phases\mq044_main.questphase';REYES=r'base\quest\minor_quests\mq049\phases\mq049_messages_reyes.questphase';FALCO=r'base\quest\minor_quests\mq049\phases\mq049_messages_falco.questphase'
DS=sorted({d for d in MI if any(x in d for x in ['\\mq041\\','\\mq044\\','\\mq049\\'])}|{P41,P44,P49,PAR,BUG,C,CS,CL,PC,INIT,SH,ST})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def save(n,x):(O/n).write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
models={};pins=[];tests=[]
def check(name,ok,evidence):
 tests.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence})
 assert ok,name
for d in DS:
 r=I[d];j=Path(r['json']);raw=j.with_suffix('')
 if d.startswith('towercontinued\\'):raw=W/'prealpha/phone_studios_ph3/candidate_01/archive_source'/Path(d.replace('\\','/'))
 if not raw.is_file() and 'json' in j.parts:
  parts=list(j.parts);parts[parts.index('json')]='raw';raw=Path(*parts).with_suffix('')
 assert raw.is_file(),str(raw)
 check('raw pin '+d,sha(raw)==r['sha256'],str(raw))
 m=Resource(json.loads(j.read_text(encoding='utf-8-sig'))).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 check('actual raw JSON normalization equals pinned model '+d,m==cached,str(j))
 models[d]=m;pins.append({'depot':d,'binary':str(raw),'resource_sha256':sha(raw),'source_json':str(j),'json_sha256':sha(j),'normalized_model':MI[d]['normalized_model'],'normalized_sha256':sha(MI[d]['normalized_model']),'provider':r['archive'],'normalizer_errors':m['errors']})
def g(d,gp='root'):return models[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
def reach(gr,seed):
 seen=set(map(str,seed));todo=list(seen)
 while todo:
  a=todo.pop()
  for x,s,y,t in gr['edges']:
   if x==a and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);todo.append(y)
 return seen
def hasfact(node,name,op,v):return any(x.get('factName')==name and x.get('comparisonType')==op and x.get('value')==v for x in node['reads'])
def evaluate(x,f,j):
 t=x['$type']
 if t=='questLogicalCondition':
  z=[evaluate(v,f,j) for v in x['conditions']]
  if any(v is None for v in z):return None
  return all(z) if x['operation']=='AND' else any(z) if x['operation']=='OR' else not any(z) if x['operation']=='NOR' else None
 if t in ['questFactsDBCondition','questJournalCondition']:return evaluate(x['type'],f,j)
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in f:return None
  a=f[x['factName']];b=x['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b,'NotEqual':a!=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  k=x['path']['realPath']
  return None if k not in j else (j[k]==x['state']) != bool(x.get('inverted',0))
 return None

# Full native entry payloads, not merely reference presence.
for private,body,native in [(P41,106,N41),(P44,149,N44),(P49,64,N49)]:
 parent,gp=(BUG,'root/3') if private==P49 else (PAR,'root')
 check('native body binding '+private,n(private,body)['payload']==n(parent,body,gp)['payload'],{'native_parent':parent,'graph':gp,'node':body,'native_body':native})
 check('native body In1 connected '+private,any(e[2]==str(body) and e[3]=='In1' for e in g(private)['edges']),{'body_node':body})
 for i in g(private)['nodes']:
  if int(i)<1000 and i!='0':check('native ancestor '+private+' node'+i,n(private,i)['payload']==n(parent,i,gp)['payload'],{'native_parent':parent,'graph':gp,'native_parent_node':i})
for d,tag,ids in [(P41,'MQ041',[1001,1002]),(P44,'MQ044',[1001,1002]),(P49,'MQ049',[1002,1004])]:
 for i in ids:
  node=n(d,i);cond=node['payload']['condition'];f={x['factName']:x['value'] for x in node['reads'] if 'factName'in x};j={x['path']['realPath']:'Inactive' for x in node['reads'] if 'path'in x}
  check('fresh guard '+tag+' '+str(i),evaluate(cond,f,j) is True,{'node':i,'journals':len(j)})
  for p in j:
   for state in ['Active','Succeeded','Failed']:
    check('reject progress '+tag+' '+str(i)+' '+p+' '+state,evaluate(cond,f,j|{p:state}) is False,{'journal':p,'state':state})
  check('reject missing journal '+tag+' '+str(i),evaluate(cond,f,{}) is not True,{'missing':'all journals'})
  for fact in ['q307_done','PTFRS23_'+tag+'_Issued','PTFRS23_'+tag+'_Permit']:
   v=1 if fact.endswith('_Issued') else 0
   check('reject protected fact '+tag+' '+str(i)+' '+fact,evaluate(cond,f|{fact:v},j) is False,{'fact':fact,'value':v})
  check('reject unknown facts '+tag+' '+str(i),evaluate(cond,{},j) is not True,{'missing':'facts'})
 if tag!='MQ049':
  check('dormant failed reactivation remains precluded '+tag,n(d,1004)['reads'][0]['state']=='Failed',{'preclaim_guards':ids,'limitation':'Stable snapshot proof; concurrent journal mutation between nodes remains unmeasured'})
  check('final guard protects native owner '+tag,edge(d,1100,'True',1101,'In') and edge(d,1101,'Out',106 if tag=='MQ041' else 149,'In1'),{'guard':1100,'receipt':1101})
 else:check('MQ049 private claim before native owner',edge(d,1004,'True',1005,'In') and edge(d,1005,'Out',1006,'In') and edge(d,1006,'Out',64,'In1'),'1004.True->1005->1006->64.In1')
for d in [P41,P44]:
 check('native early prerequisites '+d,all(hasfact(n(d,i),fact,'Greater',0) for i,fact in [(54,'q001_done'),(80,'q005_done'),(55,'q101_enable_side_content')]),{'nodes':[54,80,55]})
check('War Pigs native lifepath Corporate exact',any(x.get('$type')=='LifePath_ScriptConditionType' and val(x.get('lifePathId'))=='LifePaths.Corporate' and x.get('inverted')==0 for x in walk(n(N41,14)['payload'])),'native14.False terminates;True follows standalone gate')
check('War Pigs earned q110 standard route retained',edge(N41,29,'True',27,'In') and edge(N41,27,'Out',28,'In') and hasfact(n(N41,28),'q110_done','Greater',0) and edge(N41,28,'Out',26,'In') and edge(N41,26,'Out',20,'In1'),{'q110_gate':28,'token':26})
check('Sex on Wheels earned gig then native3day delay',hasfact(n(P44,148),'gle_06_finished','GreaterOrEqual',1) and n(P44,150)['payload']['condition']['type']['days']==3 and edge(P44,148,'Out',150,'In') and edge(P44,150,'Out',1100,'In'),{'nodes':[148,150,1100]})
co=n(MAIN44,5)['payload']['condition'];check('native MQ044 guard inversion not misread',evaluate(co,{}, {'quests/minor_quest/mq044_jakes_vehicle':'Inactive'}) is True and evaluate(co,{}, {'quests/minor_quest/mq044_jakes_vehicle':'Active'}) is False,'Native NOTActive AND NOTSucceeded, not ActiveORsucceeded')

# Exact Frank producer/listener/ack/cleanup including native name alias.
check('Frank native initializer exact',n(PC,57)['payload']==n(INIT,57)['payload'],{'native_initializer':57})
check('Frank private listener connected',edge(PC,1003,'True',1004,'In') and edge(PC,1004,'Out',57,'In1'),'1003.True->1004 Issued->57.In1')
check('Frank listener before War Pigs admission',all(hasfact(n(P41,i),'PTFRS23_PHONE_FRANK_Issued','Equal',1) for i in [1001,1002,1007,1008,1100]),'All claim/recheck guards')
for phase_reader,phase_clear,scene_in,writer,wait,clear,ack,request in [(1,10,'holo_frank_nostra_calls_v_start',78,72,73,41,'holo_frank_calls_v_start_activate'),(3,11,'holo_frank_nostra_calls_v_end',79,74,75,42,'holo_frank_calls_v_end_activate')]:
 check('Frank request actual connected caller '+request,edge(HC,writer,'0:0',wait,'0:1','scene') and edge(HC,wait,'0:0',clear,'0:1','scene') and n(HC,writer,'scene')['writes'][0]['factName']==request,{'writer':writer,'wait':wait,'clear':clear})
 check('Frank native listener edge '+request,hasfact(n(C,phase_reader),request,'Greater',0) and edge(C,phase_reader,'Out',28 if phase_reader==1 else phase_clear,'In') and (edge(C,28,'False',phase_clear,'In') if phase_reader==1 else True) and edge(C,phase_clear,'Out',0,scene_in),{'controller_reader':phase_reader,'clear':phase_clear,'scene_input':scene_in})
 expected='holo_frank_nostra_calls_v_'+('start' if phase_reader==1 else 'end')+'_done'
 check('Frank native alias acknowledgement '+expected,hasfact(n(HC,wait,'scene'),expected,'Greater',0) and n(CS,ack,'scene')['writes'][0]['factName']==expected and str(ack) in reach(g(CS,'scene'),[g(CS,'scene')['entries'][scene_in]]),{'ack':ack,'scene_entry':scene_in})
check('Frank shared cleanup connected',edge(SH,800,'True',801,'In19') and edge(SH,801,'Out19',802,'In') and n(SH,801)['refs']==[CL],'800.True->801.In19 native cleanup->802')
check('Frank native cleanup balanced counters and end routes',edge(CL,4,'True',6,'In') and edge(CL,6,'Out',0,'holo_frank_nostra_calls_v_end') and edge(CL,5,'True',7,'In') and edge(CL,7,'Out',2,'holo_v_calls_frank_nostra_end'),{'incoming_compare':4,'outgoing_compare':5})
check('Frank rejected call SMS fallback retained',edge(HOOK,4,'rejected_out',14,'Active') and edge(HOOK,14,'Out',16,'Active') and edge(HOOK,16,'Out',5,'Active'),'hook4 rejected->14 evidenceSMS->16 stashSMS->objective5')
for d in [N44,MAIN44,N49,REYES,FALCO]:
 check('SMS only no callrequest protocol '+d,not any(w.get('factName','').startswith(('holo_','audio_')) and w.get('factName','').endswith(('_activate','_done')) for gr in models[d]['graphs'].values() for nn in gr['nodes'].values() for w in nn['writes']),d)
check('Jake and Reyes native SMS branches exact',edge(MAIN44,28,'True',57,'Active','root/2') and edge(MAIN44,28,'False',58,'Active','root/2') and edge(MAIN44,28,'True',26,'Active','root/3') and edge(MAIN44,28,'False',27,'Active','root/3'),{'fact':'gle_06_succeed>=1','root2':['57Jake','58Reyes'],'root3':['26Jake','27Reyes']})
check('Reyes MQ049 SMS player choice wait and switch retained',edge(REYES,2,'Out',3,'In') and edge(REYES,3,'Out',30,'In') and edge(REYES,33,'Out1',4,'Active') and edge(REYES,8,'Out',9,'In'),{'choice':n(REYES,3)['journal_paths'],'native_lifepath_switch':9})
check('Reyes nonterminating StartFalco output retained',n(REYES,26)['payload']['type']=='NonTerminating' and edge(N49,11,'StartFalco',13,'Succeeded') and edge(N49,14,'Out',20,'In'),'Reyes26 output starts Falco without terminating remaining Reyes branch')
check('Falco alternate player answer branches retained',edge(FALCO,5,'Out',6,'In') and edge(FALCO,5,'Out',7,'In') and edge(FALCO,6,'Out',8,'In1') and edge(FALCO,7,'Out',8,'In2') and edge(FALCO,8,'Out1',9,'Active'),'choice5->6/7 Succeeded->XOR8->9')
check('Falco native response-completion and gift waits retained',edge(FALCO,15,'Out',20,'In') and edge(FALCO,20,'Out',21,'Succeeded') and edge(FALCO,23,'False',25,'Active') and edge(FALCO,26,'Out',24,'Succeeded') and hasfact(n(FALCO,26),'mq049_jacket_looted','GreaterOrEqual',1),'Gift message15 then native receipt20; jacket wait26 before quest24.Succeeded')

# Journals, native completion branches, reward data and prefab obligations.
for d in [P41,P44]:check('completion observes native succeeded '+d,n(d,1010)['reads'][0]['state']=='Succeeded' and edge(d,1010,'Out',1011,'In'),'1010 rootSucceeded->1011 privateFinished')
check('War Pigs native completion and cleanup edge',edge(END41,5,'End 0',12,'In') and edge(END41,12,'Out',13,'In') and edge(MAIN41,3,'Out1',4,'In1') and n(END41,12)['writes'][0]['factName']=='mq041_done','native scene end5->done12; main3->cleanup4')
check('War Pigs native reward record retained',any(val(x)=='QuestRewards.mq041_done' for x in walk(n(r'base\quest\minor_quests\mq041\scenes\mq041_corpo_02_confrontation.scene',527,'scene')['payload']) if x.get('$type')=='TweakDBID'),'scene527 GiveReward; target definition unverified')
check('MQ044 success precedes done and vehicle grant',edge(MAIN44,26,'Out',21,'Succeeded','root/3') and edge(MAIN44,27,'Out',21,'Succeeded','root/3') and edge(MAIN44,21,'Out',39,'In','root/3') and edge(MAIN44,39,'Out',22,'In','root/3') and edge(MAIN44,22,'Out',33,'In','root/3'),'root3 26|27->21Succeeded->39->22done->33enable vehicle')
check('MQ044 native vehicle record grant exact',n(MAIN44,33,'root/3')['payload']['type']['vehicle']=='Vehicle.v_sport1_quadra_turbo_r_player' and n(MAIN44,33,'root/3')['payload']['type']['enable']==1,'Native record pointer; target definition unresolved')
check('MQ049 exact jacket inventory wait and receipt',any(x.get('$type')=='questInventory_ConditionType' and val(x.get('itemID'))=='Items.MQ049_martinez_jacket' and x.get('quantity')==1 for x in walk(n(N49,2,'root/16')['payload'])) and edge(N49,2,'Out',3,'In','root/16') and edge(N49,3,'Out',5,'In','root/16'),'Native jacket inventory>=1 ->mq049_jacket_looted1')
check('MQ049 both lifecycle branches join before done',edge(N49,11,'Out1',15,'In1') and edge(N49,12,'Out1',15,'In2') and edge(N49,15,'Out1',17,'In') and edge(N49,17,'Out',18,'In') and edge(N49,18,'Out',23,'In1'),'AND15 prevents finishing before Reyes/Falco branches end')
check('native root prefab obligations retained',models[MAIN41]['root_prefabs']==['#mq041_pr_corpo'] and models[N44]['root_prefabs']==['#mq044_jakes_vehicle'] and models[N49]['root_prefabs']==['#mq049_pr_main','#mq049_pr_reyes'],'External native bodies still own exact native resource-root prefabs')
script=W/'prealpha/phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds';s=script.read_text()
check('S23 unknown journals defer and settled matching snapshots required','IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1' in s and 'jm.HasAnyDelayedStateChanges()' in s and 'this.Same(' in s,'Actual current S23 source')
check('S23 alreadyissued Permit not rewritten','if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }' in s,'No replay/reset by sampler')

# Mutations use actual graphs/conditions and independent native expectations.
mut=[]
bad=copy.deepcopy(g(P44));bad['nodes']['148']['payload']['condition']['type']['value']=0
mut.append({'fault':'changed earned gle_06 prerequisite','detected':bad['nodes']['148']['payload']!=n(PAR,148)['payload']})
bad=copy.deepcopy(g(PC));bad['edges'].remove(['1004','Out','57','In1'])
mut.append({'fault':'disconnected private Frank listener','detected':'57' not in reach(bad,[bad['entries']['In1']])})
bad=copy.deepcopy(g(HC,'scene'));bad['edges'].remove(['78','0:0','72','0:1'])
mut.append({'fault':'missing Frank start acknowledgement wait branch','detected':['78','0:0','72','0:1'] not in bad['edges']})
bad=copy.deepcopy(g(SH));bad['edges'].remove(['801','Out19','802','In'])
mut.append({'fault':'missing shared Frank cleanup continuation','detected':['801','Out19','802','In'] not in bad['edges']})
bad=copy.deepcopy(g(FALCO));bad['edges'].remove(['7','Out','8','In2'])
mut.append({'fault':'lost alternate Falco response','detected':['7','Out','8','In2'] not in bad['edges']})
bad=copy.deepcopy(n(MAIN44,33,'root/3')['payload']);bad['type']['vehicle']='Vehicle.wrong'
mut.append({'fault':'wrong player vehicle reward','detected':bad!=n(MAIN44,33,'root/3')['payload']})
bad=copy.deepcopy(g(N49));bad['edges'].remove(['12','Out1','15','In2'])
mut.append({'fault':'lost native completion AND prerequisite','detected':['12','Out1','15','In2'] not in bad['edges']})
bad=copy.deepcopy(models[N49]);bad['root_prefabs'].remove('#mq049_pr_reyes')
mut.append({'fault':'missing resource root prefab','detected':bad['root_prefabs']!=models[N49]['root_prefabs']})
for x in mut:check('mutation '+x['fault'],x['detected'],x)
trace=[];deps=set();asset=[]
for d,m in models.items():
 deps.update(m['refs'])
 for gp,gr in m['graphs'].items():
  for i,node in gr['nodes'].items():
   if node['reads'] or node['writes'] or node['journal_paths'] or node['reward']:
    trace.append({'depot':d,'graph':gp,'node':i,'payload':node['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if node['node_refs'] or node['refs'] or node['prefabs']:asset.append({'depot':d,'graph':gp,'node':i,'node_refs':node['node_refs'],'prefabs':node['prefabs'],'resources':node['refs']})
pins.append({'file':str(script),'sha256':sha(script),'scope':'Current sampler/Permit source, unchanged runtime'})
save('source_pins.json',pins);save('graph_evidence.json',{'traced_handlers':trace,'asset_bindings':asset,'root_prefabs':{d:m['root_prefabs'] for d,m in models.items()},'graph_errors':{d:m['errors'] for d,m in models.items() if m['errors']},'mutation_controls':mut})
save('provider_requests.json',sorted(deps|set(models)))
save('tests.json',{'status':'PASS_SCOPED_STATIC_NOT_GAMEPLAY','checks':len(tests),'mutations':len(mut),'results':tests,'resource_count':len(models),'gameplay_repairs':0,'limitations':'Original/current graph preservation and exact connected routes only; target TweakDB definitions, world placements, engine/saved-owner scheduling remain unresolved where stated.'})
print(json.dumps({'status':'PASS','checks':len(tests),'mutations':len(mut),'resources':len(models)}))
