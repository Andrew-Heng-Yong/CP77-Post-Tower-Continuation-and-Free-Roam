"""Independent QR5 ARR12 source/proposal review; no worker verifier imports or runtime writes."""
import sys,json,copy,gzip,zlib,argparse
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]));from lib import *
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True);S=Store();T=[];mut=[];mods={};pins=[]
def ck(n,b,e):T.append({'name':n,'status':'PASS'if b else'FAIL','evidence':e});assert b,n
def canon(m):
 c=copy.deepcopy(m)
 for z in walk(c):
  z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
  if z.get('$type')=='TweakDBID':
   v=z['$value'];z['$value']=str((len(v.encode())<<32)|zlib.crc32(v.encode()))if z.get('$storage')=='string'else str(int(v));z['$storage']='uint64'
 return c
for x in read(P/'raw_exports_01/manifest.json'):
 ck('raw_hash '+x['depot'],sha(x['raw'])==x['raw_sha256'],x);ck('JSON_hash '+x['depot'],sha(x['json'])==x['json_sha256'],x);m=Resource(read(x['json'])).normalize();ck('raw_no_decode_errors '+x['depot'],not m['errors'],m['errors']);mods[x['depot']]=m;pins.append(x)
 if x['depot']in S.I:
  old=S.load(x['depot'])
  if x['depot'].endswith('open_world_bugfixing.questphase'):
   ck('actual_ARR12_ancestry_graph_equals_pinned_model',canon(m['graphs']['root/1'])==canon(old['graphs']['root/1']),{'scope':'root/1 ancestry only','other_graph_discrepancy':'Fresh root/6/50/9 unrelated community NodeRef has #rancho_coronado while historical JSON has rancho_coronado; raw bytes pinned identical. Do not certify that unrelated graph or strip its #.'})
  else:ck('actual_raw_equals_separately_pinned_model '+x['depot'],canon(m)==canon(old),'Only exact TweakDBID numeric identity canonicalization and derived payload/metadata digests; all other fields compare')
def d(t):return next(d for d in mods if d.endswith('\\'+t))
def g(d,gp='root'):return mods[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
def es(d,edges,gp='root'):
 for e in edges:ck('edge '+d+' '+gp+' '+str(e),edge(d,*e,gp=gp),e)
def has(d,i,f,op,v,gp='root'):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in n(d,i,gp)['reads'])
CP=d('cyberpunk2077.questphase');BP=d('bugfixing.questphase');OP=d('open_world_bugfixing.questphase');AP=d('sts_arroyo_bugfixing.questphase');B=d('sts_std_arr_12_bugfixing.questphase');OW=d('sts_std_arr_12_ow.questphase');GPL=d('sts_std_arr_12_gpl.questphase');BODY=d('sts_std_arr_12.questphase');ENTRY=d('sts_std_arr_12_entry.questphase');DEB=d('sts_std_arr_12_holocall_debriefs.scene')
es(CP,[(106,'Out',109,'In'),(109,'Out',107,'In')]);ck('Tower_is_genuine_journal_success',any(x.get('state')=='Succeeded'and x.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow'for x in n(CP,106)['reads']),n(CP,106)['payload']);ck('original_root_terminates',n(CP,107)['payload']['type']=='Terminating','Native root107 retires nested root82 subtree')
for d0,ni,gp,ref in [(CP,4,'root/82',BP),(BP,11,'root',OP),(OP,43,'root/1',AP),(AP,15,'root',B)]:ck('exact_ancestry '+d0+str(ni),n(d0,ni,gp)['refs']==[ref]and not n(d0,ni,gp)['prefabs'],{'graph':gp,'node':ni,'ref':ref})
ck('current_entry_effective_epoch00',sha(next(x['raw']for x in pins if x['depot']==ENTRY))==read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json')['source_resources'][ENTRY],'Actual QR4 candidate03 frozen source')
ck('current_has_no_monitor_owner',all(B not in x['refs']for gr in mods[ENTRY]['graphs'].values()for x in gr['nodes'].values())and not any('arr_12_fail_loop_end'in str(x['writes'])for gr in mods[ENTRY]['graphs'].values()for x in gr['nodes'].values()),ENTRY)
ck('main_alternative_health_wait_is_unarmed',not any(e[2]=='223'for e in g(OW,'root/4')['edges'])and edge(OW,223,'Out',352,'In','root/4'),'No incoming223; obsolete fallback cannot replace separate bugfix monitor')
for d0,gp,i in [(GPL,'root',8),(GPL,'root/1',571),(OW,'root/3/2',56),(OW,'root/4',375)]:ck('actual_cleanup_consumer '+d0+gp+str(i),has(d0,i,'arr_12_fail_loop_end','Greater',0,gp),n(d0,i,gp)['payload'])
es(B,[(0,'Out',15,'In'),(15,'False',14,'In'),(14,'Out',13,'In'),(13,'Out',4,'In'),(4,'Out',10,'In'),(10,'Out',34,'In2'),(34,'Out1',5,'In'),(5,'Out',8,'In'),(8,'Out',7,'Failed'),(7,'Out',6,'Failed'),(6,'Out',12,'In'),(12,'Out',11,'after_fail_start'),(11,'after_fail_end',9,'In'),(9,'Out',16,'In'),(16,'Out',22,'In')],'root/3')
ck('native_arm_receipt_before_future_start',n(B,14,'root/3')['writes']==[{'$type':'questSetVar_NodeType','factName':'arr_12_fail_loop_start','setExactValue':1,'value':1}]and has(B,13,'arr_12_start','Greater',0,'root/3'),'A never-started native save can legitimately have arm1. No reset or whole-resource replay allowed')
# Complete original recursive scope. Empty initializer PIPs alone would not suffice.
scopes=[]
for d0,gps in [(B,[p for p in mods[B]['graphs']if p.startswith('root/3')]),(AP,['root']),(BP,['root']),(OP,['root/1'])]:
 for gp in gps:
  for i,x in g(d0,gp)['nodes'].items():
   if d0==B or (d0,i)in[(AP,'15'),(BP,'11'),(OP,'43')]:scopes.append({'depot':d0,'graph':gp,'node':i,'prefabs':x['prefabs'],'node_refs':x['node_refs'],'refs':x['refs']})
ck('monitor_root_and_ALL_recursive_PIPs_empty',not mods[B]['root_prefabs']and not any(x['prefabs']for x in scopes if x['depot']==B),'All root/3,root/3/32,root/3/36 nodes checked, plus containing root3 metadata')
ck('native_main_whole_support_preserved',mods[BODY]['root_prefabs']==['#arr_12_motel','#arr_12_diner','#arr_12_gas_station_logic','#arr_12_carchase'],'Do not add unfiltered world support owner')
ck('GPL_nested_gas_station_support_preserved',n(GPL,2)['prefabs']==['#arr_12_gas_station_logic'],'Native combat phase reference carries the extra PIP')
ck('monitor_and_main_shared_Convoy_binding',any(z.get('$value')=='Convoy'for z in walk(n(B,4,'root/3')['payload']))and '#arr_12_com'in n(B,4,'root/3')['node_refs'],'Native spawned Convoy waiter precedes health listener; exact matching authored reference retained')
# Failure-state dominance, not merely source presence: every route to call/SMS goes through failure writer8.
def reachable(gr,start,blocked=()):
 seen=set();todo=[str(start)]
 while todo:
  i=todo.pop()
  if i in seen or i in set(map(str,blocked)):continue
  seen.add(i);todo +=[e[2]for e in gr['edges']if e[0]==i and e[1]!='CutSource']
 return seen
monitor=g(B,'root/3');ck('writer8_dominates_both_debrief_routes',not ({'17','25','22'}&reachable(monitor,13,[8]))and{'17','25','22'}<=reachable(monitor,13),'Removing8 makes all failure continuation call/SMS/end consumers unreachable')
ck('writer8_exact_failure1',n(B,8,'root/3')['writes']==[{'$type':'questSetVar_NodeType','factName':'dlc_sts_std_arr_12_failed','setExactValue':1,'value':1}],n(B,8,'root/3')['payload'])
ck('monitor_reward_SMS_requires_failure0',has(B,25,'dlc_sts_std_arr_12_failed','Equal',0,'root/3'),'25.False goes failSMS23; True only goes26success selection→27/28→20')
es(B,[(25,'False',23,'Active'),(25,'True',26,'In'),(26,'False',28,'Active'),(26,'True',27,'Active'),(27,'Out',20,'In'),(28,'Out',20,'In'),(17,'success',20,'In')],'root/3')
ck('real_scene_condition_requires_failure0',has(DEB,268,'dlc_sts_std_arr_12_failed','Equal',0,'scene'),'Master actual native debrief scene gate, not inferred from output names')
es(DEB,[(268,'0:1',22,'666:1'),(22,'666:0',20,'0:0'),(20,'0:0',259,'0:1'),(88,'0:0',259,'0:0'),(259,'0:0',249,'0:0'),(268,'0:0',21,'666:1'),(21,'666:0',43,'0:1'),(252,'0:0',251,'0:0'),(88,'0:0',251,'0:1'),(251,'0:0',16,'0:0')],'scene')
rawscene=read(next(x['json']for x in pins if x['depot']==DEB))['Data']['RootChunk'];outs={str(x['nodeId']['id']):val(x['name'])for x in rawscene['exitPoints']};ck('actual_scene_exit_identity',outs['16']=='success'and outs['249']=='fail','Not guessed scene node labels')
# Conservative pulse closure lets all nongated operations finish; AND nodes require all actual input ports.
def pulse(gr,seed):
 fired=set();ports={};queue=[seed]
 while queue:
  i,port=queue.pop(0);ports.setdefault(i,set()).add(port)
  if i in fired:continue
  nd=gr['nodes'][i]
  if nd['type']=='scnAndNode'and len(ports[i])<nd['payload']['numInSockets']:continue
  fired.add(i)
  queue +=[(e[2],e[3])for e in gr['edges']if e[0]==i]
 return fired,ports
fired,ports=pulse(g(DEB,'scene'),('22','666:1'));ck('failed_scene_can_end_fail_but_CANNOT_emit_success', '249'in fired and'16'not in fired and ports.get('251')=={'0:1'}, {'successful_AND251_missing_port':'0:0 requires success-only252','failure_AND259_ports':sorted(ports['259'])})
ck('normal_OW_reward_has_same_failure_exclusion',has(OW,45,'dlc_sts_std_arr_12_failed','Equal',0,'root/5')and DEB in n(OW,14,'root/5')['refs'],'OW reward18 shares exact same debrief scene failure selector plus SMS45; new monitor does not make old reward20 unconditional')
es(OW,[(45,'False',43,'Active'),(45,'True',46,'In'),(46,'True',47,'Active'),(46,'False',48,'Active'),(47,'Out',18,'In'),(48,'Out',18,'In'),(14,'success',18,'In')],'root/5')
# Independently scan every pinned normalized model for relevant writers and private references.
facts=['arr_12_fail_loop_end','dlc_sts_std_arr_12_failed','arr_12_fail_loop_start'];hits=[];mpins=[]
for depot,r in S.MI.items():
 data=gzip.decompress(Path(r['normalized_model']).read_bytes())
 if not any(f.encode()in data for f in facts)and B.encode()not in data:continue
 model=json.loads(data);mpins.append({'path':r['normalized_model'],'sha256':sha(r['normalized_model'])})
 for gp,gr in model['graphs'].items():
  for i,x in gr['nodes'].items():
   wr=[z for z in x['writes']if z.get('factName')in facts]
   if wr or (depot.startswith('towercontinued\\')and B in x['refs']):hits.append({'depot':depot,'graph':gp,'node':i,'writes':wr,'refs':x['refs']})
ck('unique_positive_failure_end_writer',[(x['depot'],x['graph'],x['node'])for x in hits for z in x['writes']if z['factName']=='arr_12_fail_loop_end'and z['value']==1]==[(B,'root/3','22')],'Original global native bugfix monitor is sole knownend producer')
failed_writes=[z for x in hits for z in x['writes']if z['factName']=='dlc_sts_std_arr_12_failed'];ck('no_captured_native_failed_reset',bool(failed_writes)and all(z['value']>0 for z in failed_writes),failed_writes)
ck('no_alternate_current_private_monitor',not any(x['depot'].startswith('towercontinued\\')for x in hits),hits)
# Proposal pinned independently, then an isolated MODEL fixture of the tightened allowed delta.
prop=W/'prealpha/quest_restoration_qr5/groups/G04/arr12_proposal_01/proposal.json';ck('exact_proposal_pin',sha(prop)=='A428FF0E5F5EFD7DCA24CF09075A66317FA12283F443DD4F3607C2DF7F40FBFF',str(prop));proposal=read(prop)
oldentry=g(ENTRY,'root/10');ck('attachment_exact_old_edge',['65003','Out','8','In']in oldentry['edges'],oldentry['edges']);ck('private_attachment_no_outer_terminator',not any(x['type']=='questOutputNodeDefinition'and x['payload'].get('type')=='Terminating'for x in oldentry['nodes'].values()),'Monitor1202 sibling of native main12; no outer terminating output')
ck('new_local_IDs_unused',all(str(i)not in oldentry['nodes']for i in [1200,1201,1202]),'Local graph namespace, independent from ArchiveXL registrations')
fields={'PTFRU9_sts_std_arr_12_ParentEntered':1,'PTFRU9_sts_std_arr_12_Started':0,'PTFRU9_sts_std_arr_12_MainFinished':0,'PTFRU9_sts_std_arr_12_OwnerFinished':0,'PTFRU9_sts_std_arr_12_Fault':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'arr_12_start':0,'arr_12_finished':0,'PTFRU9_sts_std_arr_12_MonitorEntered':0,'arr_12_fail_loop_end':0,'dlc_sts_std_arr_12_failed':0,'dlc_sts_std_arr_12_convoy_destroyed':0,'dlc_sts_std_arr_12_failed_spawn_additional_car':0}
def guard(f):return all(f.get(k,0)==v for k,v in fields.items()) # scalar missing fact=0 engine convention; positive event is mandatory
for arm in [0,1]:ck('native_arm'+str(arm)+'_preserved_and_admitted',guard(fields|{'arr_12_fail_loop_start':arm})and(fields|{'arr_12_fail_loop_start':arm})['arr_12_fail_loop_start']==arm,'No old arm receipt read-reset or write; private guard plus fresh event is authority')
for k in fields:
 f=fields|{k:0 if fields[k] else 1};ck('exact_guard_refuses_'+k,not guard(f),f)
ck('absent_private_positive_event_refuses',not guard({k:v for k,v in fields.items()if k!='PTFRU9_sts_std_arr_12_ParentEntered'}),'Absent positive fact reads0; missing expected0 fields do NOT imply refusal')
fixture=copy.deepcopy(oldentry);fixture['edges'].remove(['65003','Out','8','In']);fixture['edges'] +=[['65003','Out','1200','In'],['1200','True','1201','In'],['1201','Out','1202','In1'],['1201','Out','8','In']]
for i in [1200,1201,1202]:fixture['nodes'][str(i)]={'review_fixture_only':True}
child=copy.deepcopy(monitor);child['edges'].remove(['0','Out','15','In']);child['edges'].append(['0','Out','13','In'])
def oracle(eg,cg):return all(str(i)in eg['nodes']for i in [1200,1201,1202])and ['1201','Out','1202','In1']in eg['edges']and cg['nodes']==monitor['nodes']and set(map(tuple,cg['edges']))==(set(map(tuple,monitor['edges']))-{('0','Out','15','In')}|{('0','Out','13','In')})
ck('defective_actual_raw_fails_owned_monitor_oracle',not oracle(oldentry,monitor),'Before resource has no owned future monitor path')
ck('proposed_tightened_model_restores_exact_monitor',oracle(fixture,child),'MODEL fixture only, not serialized runtime implementation')
ck('cloned_arm14_15_retained_but_unreachable',{'14','15'}<=set(child['nodes'])and not ({'14','15'}&reachable(child,0)),'Keep original identities and no active native receipt write')
for label,edge0 in [('missing_spawn_wait',['13','Out','4','In']),('missing_failed_writer',['5','Out','8','In']),('unconditional_reward',['25','False','23','Active']),('missing_native_afterfail_cleanup',['11','after_fail_end','9','In'])]:
 bad=copy.deepcopy(child);bad['edges'].remove(edge0);mut.append({'fault':label,'detected':not oracle(fixture,bad)})
bad=copy.deepcopy(child);bad['edges'].remove(['0','Out','13','In']);bad['edges'].append(['0','Out','15','In']);mut.append({'fault':'incorrect_native_arm_receipt_replay','detected':not oracle(fixture,bad)})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
limits=['Proposal approval is bounded source-level approval, not serialized/package approval; parent must independently diff/readback the actual implementation','No native world sector NodeRef resolution or saved-state runtime scheduling/reload proof; unrelated open_world_bugfixing root/6/50/9 fresh versus historical NodeRef text mismatch explicitly excluded from ancestry proof','Future-only new65003 execution; already ParentEntered/Started/progressed unsupported saved owners are not retroactively enrolled','Guard zero fields may be absent and read0; only positive fresh ParentEntered event plus existing certified admission provides provenance','Native full monitor success/reward branch is preserved but infeasible in the fresh failure closure while failed1 dominates and no reset occurs; external runtime fact modification is outside this proof','Global scan covers5136 pinned cache models; current frozen candidate differs only in four named unrelated prior repair payloads, not a new provider scan']
report={'status':'APPROVE_SOURCE_CONFIRMED_DEFECT_AND_TIGHTENED_FUTURE_EVENT_REPAIR_SCOPE','quest_id':'sts_std_arr_12','proposal':str(prop),'proposal_sha256':sha(prop),'checks':len(T),'actual_raw_exports':len(pins),'mutations':len(mut),'approved_delta':{'resource':ENTRY,'graph':'root/10','replace_only':['65003','Out','8','In'],'new_local_ids':[1200,1201,1202],'keep_old_nodes_all':True,'monitor':'Exact original node3 metadata/root3 and recursive32/36; only cloned0.Out→15.In replaced by0.Out→13.In','private_guard_required_values':fields,'native_arm_receipt':'Never reset/write; both0 and1 valid fresh histories','reward_basis':'failed1 writer8 dominates17/25; actual scene268False→failure22→20section→AND259→249fail. AND251success requires exclusive success252 pulse, absent in failure closure. Normal OW18 uses same scene/failure0 SMS45 guard','lifetime':'Sibling1202 under nonterminating private root/10, native main12 independent; no new root output/owner/provider/XL registration'},'limits':limits,'runtime_changes_by_reviewer':[],'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'global_scan':str(O/'global_model_hits.json')}
save(O/'tests.json',T);save(O/'source_pins.json',pins+S.pins);save(O/'global_model_hits.json',{'models':len(S.MI),'hits':hits,'pins':mpins});save(O/'scopes.json',scopes);save(O/'review.json',report);save(O/'isolated_model_fixture.json',{'runtime_resource':False,'attachment':fixture,'monitor':child,'nested32':g(B,'root/3/32'),'nested36':g(B,'root/3/36')})
print(json.dumps({'checks':len(T),'mutations':len(mut),'review':str(O/'review.json'),'review_sha256':sha(O/'review.json')}))
