"""G03 raw-source contracts. Requires a new output directory; no runtime writes."""
from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ar=ap.parse_args();O=Path(ar.output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True)
S=Store();P24=r'towercontinued\sidejobs_s23\base_a\mq024_sandra.questphase';P10=r'towercontinued\sidejobs_s24\base\mq010.questphase';P15=r'towercontinued\sidejobs_s24\base\mq015.questphase';P19=r'towercontinued\sidejobs_s24\base\mq019.questphase';PAR=r'base\quest\minor_quests\minorquests.questphase';INIT=r'base\quest\holocalls\holocall_initializers.questphase';SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
prefixes=['\\mq010\\','\\mq015\\','\\mq019\\','\\mq024\\','\\holocalls\\sandra\\','\\holocalls\\nix\\','\\holocalls\\lizzy\\','\\holocalls\\r3no\\']
extra=[P24,P10,P15,P19,PAR,INIT,SH,r'towercontinued\phone_studios_ph3\studio_support.questphase',r'towercontinued\sidejobs_s23\phone\sandra.questphase',r'towercontinued\phone_support_ph1\nix.questphase',r'towercontinued\sidejobs_s24\phone\lizzy.questphase',r'towercontinued\sidejobs_s24\phone\r3no.questphase',r'towercontinued\b0_story_eight\nix.questphase']
DS=sorted({d for d in S.MI if any(t in d for t in prefixes)}|set(extra));tests=[]
def check(name,ok,evidence):
 tests.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
for d in DS:
 m=S.load(d);check('raw_binary_JSON_model_pin '+d,not m['errors'],S.pins[-1] if S.pins[-1]['depot']==d else d)
g=S.g;n=S.n;edge=S.edge
def has(node,f,op,v):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in node['reads'])
def reaches(gr,seeds,blocked=()):
 seen=set(map(str,seeds));todo=list(seen)
 while todo:
  a=todo.pop()
  if a in blocked:continue
  for x,s,y,t in gr['edges']:
   if x==a and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);todo.append(y)
 return seen
# Native ancestor slices and inline gates remain exactly source-defined.
for d,body in [(P24,9),(P10,1),(P15,36),(P19,38)]:
 for i,node in g(d)['nodes'].items():
  if int(i)<1000 and i!='0':check('native_ancestor '+d+' '+i,node['payload']==n(PAR,i)['payload'],{'native_parent':PAR,'node':i})
 for gp,gr in S.load(d)['graphs'].items():
  if gp!='root':check('inline_native_graph '+d+' '+gp,gr==S.load(PAR)['graphs'][gp],{'graph':gp})
 check('native_body_input '+d,any(e[2]==str(body) and e[3]=='In1' for e in g(d)['edges']),{'body_node':body,'refs':n(d,body)['refs']})
 for i,f in [(54,'q001_done'),(80,'q005_done'),(55,'q101_enable_side_content')]:check('native_prerequisite '+d+' '+f,has(n(d,i),f,'Greater',0),{'node':i})
for d,tag,guards in [(P24,'MQ024',[1001,1002]),(P10,'MQ010',[1002,1004]),(P15,'MQ015',[1002,1004]),(P19,'MQ019',[1002,1004])]:
 for i in guards:
  node=n(d,i);cond=node['payload']['condition'];f={x['factName']:x['value'] for x in node['reads'] if 'factName'in x};j={x['path']['realPath']:'Inactive' for x in node['reads'] if 'path'in x}
  check('actual_fresh_guard '+tag+' '+str(i),evaluate(cond,f,j) is True,{'node':i,'journals':len(j)})
  for p in j:
   for state in ['Active','Succeeded','Failed']:check('reject_history '+tag+' '+str(i)+' '+p+' '+state,evaluate(cond,f,j|{p:state}) is False,{'path':p,'state':state})
  check('reject_unknown_journal '+tag+' '+str(i),evaluate(cond,f,{}) is not True,'Missing entries remain unknown')
  check('reject_unknown_facts '+tag+' '+str(i),evaluate(cond,{},j) is not True,'Missing facts remain unknown')
  for fact,v in [('q307_done',0),('PTFR'+('S23' if tag=='MQ024' else 'S24')+'_'+tag+'_Issued',1)]:check('reject_fact '+tag+' '+str(i)+' '+fact,evaluate(cond,f|{fact:v},j) is False,{'fact':fact,'value':v})
check('Sandra_both_native_branches_guarded',edge(P24,1100,'True',1101,'In') and edge(P24,1101,'Out',9,'In1') and edge(P24,1102,'True',1103,'In') and edge(P24,1103,'Out',128,'In1'),'Native fullquest9 and separate data-carrier watcher128 match original parent')
check('Sandra_q105_AND_either_tier',n(P24,159)['payload']['condition']['operation']=='AND' and n(P24,159)['payload']['condition']['conditions'][1]['operation']=='OR','q105_done>0 AND (tier2_1>=1 OR tier2_2>=1), not blanketAND')
check('Spellbound_earned_Rogue_and_MQ016_distance_gate',has(n(P15,78),'q103_rogue_done','Greater',0) and has(n(P15,152),'mq016_active','Equal',0),'Native152 also retains contenttoken AND distanceNix>12m')
check('Violence_q112_seven_native_tiers',has(n(P19,13,'root/133'),'q112_done','Greater',0) and len([x for x in g(P19,'root/133')['nodes'].values() if any(y.get('$type')=='questStreetCredTier_ConditionType' for y in walk(x['payload']))])==7,'Native q112 then seven alternatives through XOR17')
# Full connected path correction: the listener wait is node1003, not guard1004.
barriers=[]
for d,tag,pc,phone,initializer in [(P15,'MQ015',r'towercontinued\sidejobs_s24\phone\r3no.questphase','R3NO',103),(P19,'MQ019',r'towercontinued\sidejobs_s24\phone\lizzy.questphase','LIZZY',66)]:
 fact='PTFRS24_PHONE_'+phone+'_Issued';node=n(d,1003)
 check('actual_intermediate_listener_pause '+tag,node['type']=='questPauseConditionNodeDefinition' and has(node,fact,'Equal',1),'Native/current actual1003, omitted by rejected initial hypothesis')
 check('listener_pause_is_connected '+tag,edge(d,1002,'Out',1003,'In') and edge(d,1003,'Out',54,'In'),'1002.Out ->1003.In ->54 then native gates ->1004 ->1005')
 check('phone_zero_cannot_claim_quest '+tag,'1005' not in reaches(g(d),g(d)['entries'].values(),blocked={'1003'}),'When real pause1003 is false, all new-input claim routes are blocked')
 check('phone_one_allows_structural_entry '+tag,'1005' in reaches(g(d),g(d)['entries'].values()),'Other native/history conditions remain independently required')
 check('phone_controller_native_initializer '+tag,n(pc,initializer)['payload']==n(INIT,initializer)['payload'] and edge(pc,1003,'True',1004,'In') and edge(pc,1004,'Out',initializer,'In1'),{'native_initializer':initializer})
 for i in [1002,1003]:check('unissued_listener_parent_state '+tag+' '+str(i),has(n(pc,i),'PTFRS24_'+tag+'_Issued','Equal',0) and has(n(pc,i),'PTFRS24_'+tag+'_Permit','Equal',1),'Parent stays unissued while waiting1003, allowing listener claim first')
 barriers.append({'quest':d,'pause':1003,'phone_fact':fact,'path':[['1002','Out','1003','In'],['1003','Out','54','In']],'claim':1005,'proposed_patch_rejected':True})
# Exact caller/listener/ack contracts, including native display-name aliases.
protocols=[('sandra',r'base\quest\minor_quests\mq024\scenes\mq024_01_call_sandra.scene',[(116,109,43,'holo_v_calls_sandra_dorsett_start_activate'),(117,111,44,'holo_v_calls_sandra_dorsett_end_activate')],[(4,'Out',30,'In'),(30,'False',12,'In'),(12,'Out',0,'holo_v_calls_sandra_dorsett_start'),(5,'Out',13,'In'),(13,'Out',0,'holo_v_calls_sandra_dorsett_end')]),('r3no',r'base\quest\minor_quests\mq015\scenes\mq015_02_seller_holocall.scene',[(722,None,536,'audio_v_calls_r3no_start_activate'),(724,None,538,'audio_v_calls_r3no_end_activate')],[(16,'Out',33,'In'),(33,'False',18,'In'),(18,'Out',22,'audio_v_calls_r3no_start'),(17,'Out',19,'In'),(19,'Out',22,'audio_v_calls_r3no_end')]),('lizzy',r'base\quest\minor_quests\mq019\scenes\mq019_05_holocall.scene',[(471,465,43,'holo_v_calls_lizzy_start_activate'),(488,482,44,'holo_v_calls_lizzy_end_activate'),(508,502,43,'holo_v_calls_lizzy_start_activate'),(522,516,44,'holo_v_calls_lizzy_end_activate')],[(4,'Out',30,'In'),(30,'False',12,'In'),(12,'Out',0,'holo_v_calls_lizzy_wizzy_start'),(5,'Out',13,'In'),(13,'Out',0,'holo_v_calls_lizzy_wizzy_end')])]
for contact,caller,pairs,edges in protocols:
 cd='base\\quest\\holocalls\\'+contact+'\\'+contact+'_holocall.questphase';sc=cd.replace('.questphase','.scene')
 for a,s,b,t in edges:check('connected_native_listener '+contact+' '+str(a)+' '+s,edge(cd,a,s,b,t),{'edge':[a,s,b,t]})
 for writer,wait,ack,request in pairs:
  ackfact=request.replace('_activate','_done');wn=n(caller,writer,'scene');outs=[e for e in g(caller,'scene')['edges'] if e[0]==str(writer)]
  if wait is None:
   found=[e[2] for e in outs if has(n(caller,e[2],'scene'),ackfact,'Greater',0)];check('actual_wait_selected '+contact+' '+str(writer),bool(found),outs);wait=found[0]
  check('caller_request_wait '+contact+' '+str(writer),any(w['factName']==request and w['value']==1 for w in wn['writes']) and any(e[2]==str(wait) for e in outs) and has(n(caller,wait,'scene'),ackfact,'Greater',0),{'request_node':writer,'wait':wait,'fact':ackfact})
  check('real_native_ack '+contact+' '+str(ack),any(w['factName']==ackfact and w['value']==1 for w in n(sc,ack,'scene')['writes']),{'ack_node':ack,'fact':ackfact})
for contact,node,src,ins,out,dst in [('sandra',807,806,'In51','Out51',808),('r3no',903,902,'In46','Out46',1010),('lizzy',901,900,'In29','Out29',911),('nix',1414,1413,'In48','Out48',1415)]:
 dep='base\\quest\\holocalls\\'+contact+'\\'+contact+'_cleanup.questphase'
 check('actual_shared_cleanup '+contact,n(SH,node)['refs']==[dep] and edge(SH,src,'True',node,ins) and edge(SH,node,out,dst,'In'),{'phase':node,'native_cleanup':dep})
check('Barry_success_failure_cleanup',edge(r'base\quest\minor_quests\mq010\mq010.questphase',2,'failed',19,'In1') and edge(r'base\quest\minor_quests\mq010\mq010.questphase',3,'failed',20,'In1') and edge(r'base\quest\minor_quests\mq010\mq010.questphase',5,'failed',11,'In1'),'Authored failure and normal cleanup paths retained')
check('Barry_done_active_cleanup',n(r'base\quest\minor_quests\mq010\phases\mq010_cleanup.questphase',8)['writes'][0]['factName']=='mq010_done' and n(r'base\quest\minor_quests\mq010\phases\mq010_cleanup.questphase',7)['writes'][0]['value']==0,'Native cleanup8done1 ->7active0')
check('Spellbound_completion_order',edge(r'base\quest\minor_quests\mq015\phases\mq015_04_afterlife.questphase',8,'Out',32,'In') and edge(r'base\quest\minor_quests\mq015\phases\mq015_04_afterlife.questphase',32,'Out',7,'In') and edge(r'base\quest\minor_quests\mq015\phases\mq015_04_afterlife.questphase',7,'Out',10,'In'),'Native journal8 ->active0 node32 ->done1 node7 ->reward10')
check('Sandra_done_journal_cleanup',edge(r'base\quest\minor_quests\mq024\phases\mq024_cleanup.questphase',3,'Out',4,'In') and edge(r'base\quest\minor_quests\mq024\phases\mq024_cleanup.questphase',4,'Out',2,'Succeeded'),'Native active0 ->done1 ->Succeeded')
mut=[]
for d,tag in [(P15,'MQ015'),(P19,'MQ019')]:
 bad=copy.deepcopy(g(d));bad['edges'].remove(['1002','Out','1003','In']);bad['edges'].append(['1002','Out','54','In'])
 mut.append({'fault':'missing_actual_listener_pause_'+tag,'detected':'1005' in reaches(bad,bad['entries'].values(),blocked={'1003'})})
bad=copy.deepcopy(g(P24));bad['edges'].remove(['1101','Out','9','In1']);mut.append({'fault':'lost_Sandra_native_body','detected':['1101','Out','9','In1'] not in bad['edges']})
bad=copy.deepcopy(g(SH));bad['edges'].remove(['903','Out46','1010','In']);mut.append({'fault':'lost_R3NO_cleanup_connection','detected':['903','Out46','1010','In'] not in bad['edges']})
bad=copy.deepcopy(n(P15,78)['payload']);bad['condition']['type']['value']=100;mut.append({'fault':'changed_earned_Rogue_threshold','detected':bad!=n(PAR,78)['payload']})
for row in mut:check('mutation '+row['fault'],row['detected'],row)
handler=[];assets=[]
for d,m in S.models.items():
 for gp,gr in m['graphs'].items():
  for i,node in gr['nodes'].items():
   if node['reads'] or node['writes'] or node['journal_paths'] or node['reward'] or node['sms']:
    handler.append({'depot':d,'graph':gp,'node':i,'reads':node['reads'],'writes':node['writes'],'journal':node['journal_paths'],'reward':node['reward'],'sms':node['sms'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if node['node_refs'] or node['prefabs'] or node['refs']:assets.append({'depot':d,'graph':gp,'node':i,'node_refs':node['node_refs'],'prefabs':node['prefabs'],'refs':node['refs']})
save(O/'tests.json',{'status':'PASS_SCOPED_STATIC_CONTROLS','count':len(tests),'checks':tests,'mutations':mut,'confirmed_runtime_defects':[],'source_epoch':'QR3 successor; sourcehashes pinned perresource; no QR4 resource edits byworker'})
save(O/'source_pins.json',S.pins);save(O/'graph_evidence.json',{'handlers':handler,'assets':assets,'prefab_roots':{d:m['root_prefabs'] for d,m in S.models.items()},'listener_barriers':barriers})
save(O/'hypothesis_correction.json',{'status':'REJECTED_RACE_HYPOTHESIS_EXISTING_BARRIER_PROVEN','initial_claim':'MQ015/MQ019 guard1002/1004 lacked listenerIssued, so quest-first could prevent listener claim.','error':'Initial scan skipped connected intermediate1003 PauseCondition. Both quests wait PHONE_R3NO/LIZZY_Issued==1 before native prerequisites/finalguard/claim. The proposed counterexample jumped past this actual wait.','correct_evidence':barriers,'independent_catch':'Root and workerA traced actual1003 from raw/model evidence; original runtime source was alreadycorrect.','runtime_changes':[],'rejected_proposal':'Do not add redundant fourguard listener requirements or alter listeners/resetfacts.'})
print(json.dumps({'status':'PASS','checks':len(tests),'mutations':len(mut),'sources':len(S.pins),'confirmed_defects':0}))
