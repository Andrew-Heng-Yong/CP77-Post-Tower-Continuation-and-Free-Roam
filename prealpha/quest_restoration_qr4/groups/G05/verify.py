"""G05 source-backed verification; no build/deploy imports; fresh outputs only."""
from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists(),'Fresh --output required';O.mkdir(parents=True)
S=Store();tests=[];mut=[]
GIG=r'towercontinued\sidejobs_s24\services\the_gig_fresh.questphase';RES=r'towercontinued\sidejobs_s22\the_gig_reward_resume.questphase';GUN=r'towercontinued\sidejobs_s25\services\gun_fresh.questphase';ORDER=r'towercontinued\sidejobs_s25\services\gun_order.scene';WV=r'towercontinued\b0_wilson_vendor\body.questphase';WO=r'towercontinued\b0_wilson_vendor\owner.questphase';WAK=r'towercontinued\fixer_offices_fo1\wakako.questphase';CAS=r'towercontinued\b0_story_services\cassius.questphase';MQ11=r'towercontinued\sidejobs_s23\base_b\mq011.questphase';MQ12=r'towercontinued\sidejobs_s23\base_a\mq012_stud.questphase'
NATIVEGIG=r'base\quest\main_quests\prologue\q001\phases\q101_wakako_reward.questphase';NATIVEGUN=r'base\quest\main_quests\prologue\q001\phases\q001_wilson.questphase';SHOP=r'base\open_world\vendors\watson\little_china\wat_lch_gunsmith_01\wat_lch_gunsmith_01.scene';WAKSC=r'base\open_world\fixers\wakako\scenes\wakako_okada_default.scene';CASSC=r'base\open_world\vendors\watson\northside\wat_nid_ripperdoc_01\wat_nid_ripperdoc_01.scene';PAR=r'base\quest\minor_quests\minorquests.questphase';INIT=r'base\quest\holocalls\holocall_initializers.questphase';SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
EX=[GIG,RES,GUN,ORDER,WV,WO,WAK,CAS,NATIVEGIG,NATIVEGUN,SHOP,WAKSC,CASSC,MQ11,MQ12,PAR,INIT,SH,r'towercontinued\b0_wilson_vendor\shop.scene',r'towercontinued\phone_studios_ph3\studio_support.questphase',r'base\quest\default_dialogs.questphase',r'base\quest\bugfixing\prologue\q001\q001_quest_bugfixes.questphase',r'towercontinued\sidejobs_s23\phone\wilson.questphase',r'towercontinued\sidejobs_s23\phone\mrstud.questphase']
DS=sorted(set(EX)|{d for d in S.MI if any(p in d for p in ['\\mq011\\','\\mq012\\','\\holocalls\\wilson\\','\\holocalls\\mr_stud\\'])})
def ck(name,b,e):
 tests.append({'name':name,'status':'PASS' if b else 'FAIL','evidence':e});assert b,name
for d in DS:ck('source_binary_JSON_model '+d,not S.load(d)['errors'],d)
g=S.g;n=S.n;edge=S.edge
def has(q,f,op,v):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in q['reads'])
def reach(gr,seeds,blocked=()):
 seen=set(map(str,seeds));todo=list(seen)
 while todo:
  i=todo.pop()
  if i in blocked:continue
  for x,s,y,t in gr['edges']:
   if x==i and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);todo.append(y)
 return seen
def ec(d,edges,gp='root'):
 for e in edges:ck('connected '+d+' '+str(e),edge(d,*e,gp=gp),{'graph':gp,'edge':e})
# Direct original contracts, not a generated list of expected current graphs.
for p,v in [(GIG,NATIVEGIG),(RES,NATIVEGIG),(GUN,NATIVEGUN)]:
 for i,q in g(p)['nodes'].items():
  if i in g(v)['nodes'] and i not in ['0','1']:ck('retained_vanilla_payload '+p+' '+i,q['payload']==n(v,i)['payload'],{'original':v,'node':i})
for p in [MQ11,MQ12]:
 for i,q in g(p)['nodes'].items():
  if int(i)<1000 and i!='0':ck('native_ancestor '+p+' '+i,q['payload']==n(PAR,i)['payload'],{'parent':PAR,'node':i})
 for gp,gr in S.load(p)['graphs'].items():
  if gp!='root':ck('native_nested_graph '+p+' '+gp,gr==S.load(PAR)['graphs'][gp],{'parent':PAR,'graph':gp})
# Fresh guards reject all authored history states, with no assumption that missing means zero.
for p,ids in [(GIG,[1002,1003]),(GUN,[1002,1003]),(MQ11,[1002,1004,1104]),(MQ12,[1001,1002])]:
 for i in ids:
  q=n(p,i);f={x['factName']:x['value']+(1 if x['comparisonType']=='Greater' else 0) for x in q['reads'] if 'factName'in x};j={x['path']['realPath']:'Inactive' for x in q['reads'] if 'path'in x}
  if p==GUN:f['fixture_inventory:Items.Preset_Q001_Lexington']=0
  ck('fresh_fixture '+p+' '+str(i),evaluate(q['payload']['condition'],f,j) is True,{'journals':len(j),'facts':f})
  for path in j:
   for state in ['Active','Succeeded','Failed']:ck('history_rejection '+p+' '+str(i)+' '+path+' '+state,evaluate(q['payload']['condition'],f,j|{path:state}) is False,{'path':path,'state':state})
  ck('unknown_history_defer '+p+' '+str(i),evaluate(q['payload']['condition'],f,{}) is not True,'Missing journal is not proven Inactive')
  ck('unknown_facts_defer '+p+' '+str(i),evaluate(q['payload']['condition'],{},j) is not True,'Missing facts are not proven zero')
  ck('completed_Tower_required '+p+' '+str(i),evaluate(q['payload']['condition'],f|{'q307_done':0},j) is False,'No pre-Tower admission')
  if p==MQ12:ck('MRSTUD_listener_required '+str(i),evaluate(q['payload']['condition'],f|{'PTFRS23_PHONE_MRSTUD_Issued':0},j) is False,'Actual MR_STUD, not Dennis')
for i in [1002,1003]:
 ck('Gig_earned_prerequisites '+str(i),all(has(n(GIG,i),f,'GreaterOrEqual',1) for f in ['q001_done','q101_enable_side_content','wakako_default_on','wat_nid_ripperdoc_01_default_on']),'These history facts are read, never manufactured')
 ck('Gig_fresh_resume_disjoint '+str(i),has(n(GIG,i),'q001_wakako_reward_given','Equal',0) and has(n(RES,1001),'q001_wakako_reward_given','Equal',1),'Resume needs earned Wakako payment; fresh needs unpaid')
ec(GIG,[(1005,'Out',25,'In'),(7,'Out',9,'Succeeded'),(3,'Out',11,'In'),(11,'Out',6,'Succeeded'),(15,'Out',30,'In'),(30,'Out',28,'In'),(27,'Out',1007,'In')])
ec(RES,[(1003,'Out',25,'In'),(1006,'Out',15,'Active'),(15,'Out',1007,'In'),(1008,'True',30,'In'),(27,'Out',1004,'In')])
ck('resume_no_repeated_Wakako_reward','11' not in g(RES)['nodes'] and all(not q['reward'] for q in g(RES)['nodes'].values()),'Native monetary reward11 deliberately bypassed after reward_given1')
ck('resume_exact_earned_objectives',all(any(x.get('path',{}).get('realPath','').endswith('/'+tail) and x.get('state')=='Succeeded' for x in n(RES,1001)['reads']) for tail in ['00_reward','01_reward']),'Completed early objective receipts required')
ck('Gig_prefab_gap_explicit',S.load(NATIVEGIG)['root_prefabs']==['#sq_q001_pr_wakako_reward'] and not S.load(GIG)['root_prefabs'] and not S.load(RES)['root_prefabs'],'OPAQUE obligation, not approved omission or confirmed defect')
ck('Gig_obsolete_node_deletion',n(NATIVEGIG,30)['type']=='questDeletionMarkerNodeDefinition' and '24' not in g(NATIVEGIG)['nodes'],'Original placement consumer24 removed by native deletion marker30')
ck('Wakako_payment_writer_is_native',any(w['factName']=='q001_wakako_reward_given' and w['value']==1 for w in n(WAKSC,35,'scene')['writes']),'Native choice29 output2:1 ->35; no synthetic reward_given writer')
ck('separate_Wakako_default_prefab','#wakako_okada_default' in n(WAK,100)['prefabs'],'Does not prove coverage of distinct #sq_q001_pr_wakako_reward')
ck('separate_Cassius_prefab','#pr_wat_nid_ripperdoc_01' in n(CAS,5)['prefabs'],'Distinct service support, not TheGig root prefab')
ec(GUN,[(1005,'Out',1008,'In'),(1008,'Out',1007,'In'),(52,'Out',53,'In'),(53,'False',49,'Active'),(49,'Out',56,'In'),(56,'Out',61,'In')])
ck('Gun_real_completion_observer',any(x.get('state')=='Succeeded' and x.get('path',{}).get('realPath')=='quests/side_quest/sq_q001_wilson' for x in n(GUN,1008)['reads']),'Issued is not immediately Finished')
ec(WV,[(4,'Out',100,'In'),(100,'True',101,'wilson_default_in'),(100,'False',5,'wilson_default_in'),(12,'CutSource',101,'CutDestination'),(12,'CutSource',5,'CutDestination')])
ck('Gun_order_gate',has(n(WV,100),'PTFRS25_GUN_Issued','Equal',1) and has(n(WV,100),'PTFRS25_GUN_Finished','Equal',0),'Private order branch only while this entitlement is owned')
ec(ORDER,[(42,'0:0',305,'0:0'),(305,'0:0',285,'0:1'),(285,'0:0',277,'0:1'),(277,'0:0',281,'0:1'),(281,'0:0',430,'0:1'),(430,'0:0',209,'0:3'),(209,'0:0',369,'0:3'),(365,'0:0',361,'0:1'),(361,'0:0',363,'0:3')],'scene')
for i in [281,361]:ck('Gun_possession_predicate '+str(i),any(x.get('$type')=='questInventory_ConditionType' and val(x.get('itemID'))=='Items.Preset_Q001_Lexington' and x.get('quantity')==1 for x in walk(n(ORDER,i,'scene')['payload'])),'Native itemID, quantity and predicate retained')
for i in [209,281,285,288,352,353,361,363,365,369,415,430,573,579,650]:ck('Gun_retained_semantics '+str(i),n(ORDER,i,'scene')['payload']==n(SHOP,i,'scene')['payload'],{'source':SHOP,'node':i})
ck('Gun_vendor_identity',any(x.get('$type')=='questVendorPanel_NodeType' and x.get('vendorId')=='Vendors.wat_lch_gunsmith_01' for x in walk(n(ORDER,277,'scene')['payload'])),'No direct arbitrary gun grant added')
for k in ['actors','playerActors','workspots','workspotInstances','referencePoints','localMarkers','ridResources','resouresReferences']:ck('Gun_presentation_metadata '+k,S.load(ORDER)['metadata'][k]==S.load(SHOP)['metadata'][k],'Source metadata retained; binding resolution remains opaque')
ec(MQ11,[(1002,'Out',1003,'In'),(1003,'Out',54,'In'),(54,'Out',80,'In'),(80,'Out',55,'In'),(55,'Out',184,'In'),(93,'Out',1110,'In'),(1110,'Out',1111,'In'),(1111,'Out',1112,'In'),(1112,'Out',1004,'In'),(1006,'Out',15,'In1'),(184,'False',1120,'In'),(1120,'Out',1121,'In'),(1121,'Out',1122,'In'),(1122,'Out',1104,'In'),(1106,'Out',15,'EP1_Standalone'),(15,'Out1',1007,'In'),(1007,'Out',1012,'In')])
ck('MQ011_actual_listener_barrier',has(n(MQ11,1003),'PTFRS23_PHONE_WILSON_Issued','Equal',1) and '1005' not in reach(g(MQ11),g(MQ11)['entries'].values(),{'1003'}),'Full connected path; no skipped intermediate')
for i in [1112,1122]:
 ck('MQ011_vendor_release '+str(i),all(has(n(MQ11,i),f,'Equal',v) for f,v in [('PTFRB0WV_Released',1),('PTFRB0WV_Near',0),('PTFRB0WV_SpawnActionOut',0),('PTFRB0WV_ActorDistanceGate',0)]),'LeaseRequested and QuestOwns are already set; this wait does not require QuestOwns0')
 ck('MQ011_no_self_deadlock '+str(i),not has(n(MQ11,i),'PTFRB0WV_QuestOwns','Equal',0),'Old unreachable1011 is not substituted for actual wait')
ck('MQ011_old_route_unreachable','1010' not in reach(g(MQ11),g(MQ11)['entries'].values()),'Old IDs remain for saved compatibility; fresh inputs do not reach them')
ec(WO,[(100,'True',101,'In'),(101,'Out',102,'In'),(100,'False',103,'In'),(103,'Out',4,'In1')])
ec(MQ12,[(1002,'True',1003,'In'),(1003,'Out',1004,'In'),(1004,'False',1007,'In'),(1007,'Out',1008,'In'),(1008,'True',81,'In1'),(81,'Out1',117,'In'),(117,'Out',1100,'In'),(1100,'True',1101,'In'),(1101,'Out',16,'In1'),(1101,'Out',1010,'In'),(1010,'Out',1011,'In')])
ck('MQ012_apartment_history',has(n(MQ12,117),'q001_left_v_apartment','GreaterOrEqual',1),'Native prerequisite preserved')
ck('MQ012_current_failed_reactivation_not_fresh_admission',all(x.get('state')=='Inactive' for x in n(MQ12,1001)['reads'] if 'path'in x) and any(x.get('state')=='Failed' for x in n(MQ12,1004)['reads']),'1004 old Failed branch exists, but fresh1001/1002 do not admit Failed histories')
for tag,wrapper,ini in [('wilson',r'towercontinued\sidejobs_s23\phone\wilson.questphase',99),('mr_stud',r'towercontinued\sidejobs_s23\phone\mrstud.questphase',74)]:
 ck('native_phone_initializer '+tag,n(wrapper,ini)['payload']==n(INIT,ini)['payload'],{'initializer':ini,'source':INIT});ec(wrapper,[(1003,'True',1004,'In'),(1004,'Out',ini,'In1')])
 cd='base\\quest\\holocalls\\'+tag+'\\'+tag+'_holocall.questphase';sc=cd.replace('.questphase','.scene')
 ec(cd,[(1,'Out',28,'In'),(28,'False',10,'In'),(10,'Out',0,'holo_wilson_calls_v_start'),(3,'Out',11,'In'),(11,'Out',0,'holo_wilson_calls_v_end')] if tag=='wilson' else [(0,'Out',28,'In'),(28,'False',9,'In'),(9,'Out',21,'holo_mr_stud_calls_v_start'),(2,'Out',10,'In'),(10,'Out',21,'holo_mr_stud_calls_v_end')])
 caller=r'base\quest\minor_quests\mq011\scenes\mq011_00_gun_range.scene' if tag=='wilson' else r'base\quest\minor_quests\mq012\scenes\mq012_00_stud.scene'
 for w,wait,ack,part in ([(1474,1468,41,'start'),(1475,1470,42,'end')] if tag=='wilson' else [(1795,1789,41,'start'),(1796,1791,42,'end')]):
  fact='holo_'+tag+'_calls_v_'+part
  ck('caller_request '+tag+' '+part,any(x['factName']==fact+'_activate' and x['value']==1 for x in n(caller,w,'scene')['writes']) and edge(caller,w,'0:0',wait,'0:1',gp='scene') and has(n(caller,wait,'scene'),fact+'_done','Greater',0),{'writer':w,'wait':wait,'fact':fact})
  ck('real_native_ack '+tag+' '+part,any(x['factName']==fact+'_done' and x['value']==1 for x in n(sc,ack,'scene')['writes']),{'native_scene':sc,'node':ack})
for i,sock,src,dst,tag in [(803,'37',802,804,'mr_stud'),(809,'63',808,910,'wilson')]:
 ck('shared_cleanup_ref '+tag,n(SH,i)['refs']==['base\\quest\\holocalls\\'+tag+'\\'+tag+'_cleanup.questphase'],'Exact native cleanup, not a reset replacement');ec(SH,[(src,'True',i,'In'+sock),(i,'Out'+sock,dst,'In')])
for tag in ['mq011','mq012']:
 d='base\\quest\\minor_quests\\'+tag+'\\'+tag+'.questphase';gp='root/24' if tag=='mq011' else 'root/13'
 ck('native_completion '+tag,any(w['factName']==tag+'_active' and w['value']==0 for w in n(d,2,gp)['writes']) and any(w['factName']==tag+'_done' and w['value']==1 for w in n(d,3,gp)['writes']),'Native active0, done1 cleanup retained')
ck('MQ011_root_prefab_retained_in_native_body',S.load(r'base\quest\minor_quests\mq011\mq011.questphase')['root_prefabs']==['#mq011_pr_wilson'],'Entry wrapper delegates whole native resource, not initializer-only support')
ck('MQ012_nested_prefabs_preserved',set(n(r'base\quest\minor_quests\mq012\mq012.questphase',8)['prefabs'])=={'#mq012_pr_ripperdoc','#mq012_pr_stud'},'Whole native body includes driving and cleanup prefab scopes')
# Mutations alter actual normalized edge/predicate payloads, then re-evaluate independent contracts.
bad=copy.deepcopy(g(MQ11));bad['edges'].remove(['1002','Out','1003','In']);bad['edges'].append(['1002','Out','54','In']);mut.append({'fault':'skip_MQ011_real_phone_pause','detected':'1005' in reach(bad,bad['entries'].values(),{'1003'})})
bad=copy.deepcopy(g(MQ11));bad['edges'].remove(['1111','Out','1112','In']);bad['edges'].append(['1111','Out','1004','In']);mut.append({'fault':'skip_vendor_release_barrier','detected':'1005' in reach(bad,bad['entries'].values(),{'1112','1122'})})
bad=copy.deepcopy(n(GUN,52)['payload']);bad['condition']['type']['value']=0;mut.append({'fault':'changed_native_elevator_prerequisite','detected':bad!=n(NATIVEGUN,52)['payload']})
bad=copy.deepcopy(g(ORDER,'scene'));bad['edges'].remove(['361','0:0','363','0:3']);mut.append({'fault':'lost_inventory_completion_branch','detected':['361','0:0','363','0:3'] not in bad['edges']})
bad=copy.deepcopy(g(SH));bad['edges'].remove(['809','Out63','910','In']);mut.append({'fault':'lost_Wilson_cleanup_connection','detected':['809','Out63','910','In'] not in bad['edges']})
bad=copy.deepcopy(n(MQ12,1001)['payload']);target=next(x for x in walk(bad) if x.get('factName')=='PTFRS23_PHONE_MRSTUD_Issued');target['value']=0;mut.append({'fault':'missing_MRSTUD_listener_requirement','detected':bad!=n(MQ12,1001)['payload']})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
handlers=[];assets=[]
for d,m in S.models.items():
 for gp,gr in m['graphs'].items():
  for i,q in gr['nodes'].items():
   if q['reads'] or q['writes'] or q['journal_paths'] or q['reward'] or q['sms']:handlers.append({'depot':d,'graph':gp,'node':i,'payload_sha256':q['payload_sha256'],'reads':q['reads'],'writes':q['writes'],'journal':q['journal_paths'],'reward':q['reward'],'sms':q['sms'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if q['refs'] or q['node_refs'] or q['prefabs']:assets.append({'depot':d,'graph':gp,'node':i,'refs':q['refs'],'node_refs':q['node_refs'],'prefabs':q['prefabs']})
save(O/'tests.json',{'status':'PASS_SCOPED_STATIC_CHECKS','count':len(tests),'checks':tests,'mutations':mut,'runtime_changes':[]});save(O/'source_pins.json',S.pins);save(O/'graph_evidence.json',{'handlers':handlers,'assets':assets,'root_prefabs':{d:m['root_prefabs'] for d,m in S.models.items()},'limitations':['World sectors/TDB definitions/journal targets not completely resolved','Original saved owners and runtime scheduling not simulated','TheGig distinct root-prefab content unresolved; native30 deletion marker not positive omission approval']})
print(json.dumps({'checks':len(tests),'sources':len(S.pins),'mutations':len(mut)}))
