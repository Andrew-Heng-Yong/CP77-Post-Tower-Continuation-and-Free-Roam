import sys,json,gzip,copy,argparse
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent));from lib import *
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True);S=Store();T=[];mods={};pins=[]
def ck(n,b,e):T.append({'name':n,'status':'PASS'if b else'FAIL','evidence':e});assert b,n
sets=[read(P/'raw_exports_01/manifest.json'),read(P.parent/'raw_exports_01/manifest.json'),read(W/'prealpha/quest_restoration_qr5/groups/G07/reviews/ARR12/raw_exports_01/manifest.json')]
needed=['sts_wat_nid_02_bugfixing.questphase','sts_nid_bugfixing.questphase','sts_wat_nid_02_phase.questphase','sts_wat_nid_02_ow.questphase','sts_wat_nid_02_entry.questphase','cyberpunk2077.questphase','bugfixing.questphase','open_world_bugfixing.questphase']
for tail in needed:
 x=next(x for arr in sets for x in arr if x['depot'].endswith('\\'+tail));ck('actual_raw_pin '+x['depot'],sha(x['raw'])==x['raw_sha256'],x['raw']);ck('actual_export_pin '+x['depot'],sha(x['json'])==x['json_sha256'],x['json']);mods[x['depot']]=Resource(read(x['json'])).normalize();ck('decode '+tail,not mods[x['depot']]['errors'],mods[x['depot']]['errors']);pins.append(x)
def d(t):return next(dp for dp in mods if dp.endswith('\\'+t))
def g(dp,gp='root'):return mods[dp]['graphs'][gp]
def n(dp,i,gp='root'):return g(dp,gp)['nodes'][str(i)]
def edge(dp,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(dp,gp)['edges']
def es(dp,edges,gp='root'):
 for e in edges:ck('native_connected '+dp+gp+str(e),edge(dp,*e,gp=gp),e)
B=d('sts_wat_nid_02_bugfixing.questphase');NP=d('sts_nid_bugfixing.questphase');CP=d('cyberpunk2077.questphase');BP=d('bugfixing.questphase');OP=d('open_world_bugfixing.questphase');OW=d('sts_wat_nid_02_ow.questphase');ENTRY=d('sts_wat_nid_02_entry.questphase');BODY=d('sts_wat_nid_02_phase.questphase');F='sts_wat_nid_02_fail'
es(CP,[(106,'Out',109,'In'),(109,'Out',107,'In')]);ck('genuine_Tower_root_termination',n(CP,107)['payload']['type']=='Terminating'and any(x.get('state')=='Succeeded'and x.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow'for x in n(CP,106)['reads']),'Native actualTower success, not killed receipt alone')
for dp,gp,i,ref in [(CP,'root/82',4,BP),(BP,'root',11,OP),(OP,'root/1',35,NP),(NP,'root',17,B)]:ck('original_executing_ancestry '+dp+str(i),n(dp,i,gp)['refs']==[ref],{'graph':gp,'node':i,'target':ref})
es(B,[(0,'Out',12,'In'),(12,'False',13,'In'),(13,'Out',33,'In'),(33,'Out',16,'In'),(16,'False',2,'In'),(16,'False',50,'In'),(2,'Out',41,'In1'),(50,'Out',49,'In'),(49,'Out',41,'In2'),(41,'Out1',34,'In'),(41,'Out1',4,'Failed'),(4,'Out',3,'Failed')],'root/23')
ck('native_CYB_receipt_armed_before_future_start',n(B,13,'root/23')['writes']==[{'$type':'questSetVar_NodeType','factName':'CYB-651268','setExactValue':0,'value':1}]and n(B,33,'root/23')['reads'][0]['factName']=='nid_02_start','CYB1 is legitimate never-started history; do not reset it or replay whole global bugfix')
ck('native_monitor_defers_already_finished',n(B,16,'root/23')['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'nid_02_finished','value':0}],'16False only then health/water monitor')
ck('native_health_water_join_is_XOR_not_AND',n(B,41,'root/23')['type']=='questLogicalXorNodeDefinition','One native health or water branch can advance failure; do not require both')
ck('native_health_listener_actual_van',n(B,2,'root/23')['type']=='questPauseConditionNodeDefinition'and n(B,2,'root/23')['payload']['condition']['type']['percent']==0 and '#nid_02_com'in n(B,2,'root/23')['node_refs'],'Waits van_001 health<=0, not an idle source node')
water=n(B,49,'root/23')['payload']['condition'];ck('native_water_requires_submerged_AND_player_mounted',water['operation']=='AND'and any(x.get('$type')=='questVehicleWater_ConditionType'and x['submergedOnly']==1 for x in walk(water))and any(x.get('$type')=='questCharacterMount_ConditionType'and x['condition']=='OnMount'for x in walk(water)),water)
ck('native_unique_failure_fact_write',n(B,34,'root/23')['writes']==[{'$type':'questSetVar_NodeType','factName':F,'setExactValue':0,'value':1}],n(B,34,'root/23')['payload'])
es(B,[(41,'Out1',11,'In'),(11,'Out',10,'In'),(3,'Out',6,'In'),(3,'Out',7,'In'),(7,'True',8,'In'),(8,'Out',9,'In1'),(7,'False',9,'In1'),(6,'Out',9,'In2'),(9,'Out1',25,'In'),(25,'Out',30,'In'),(30,'Out',43,'In'),(43,'False',24,'Start 0'),(24,'Holocall INT',27,'In'),(24,'Holocall RET',26,'In'),(24,'End 0',21,'In'),(24,'End 0',37,'In')],'root/23')
ck('native_failure_force_disconnect_is_authored_cleanup',n(B,8,'root/23')['payload']['type']['params'][0]['deviceAction']['$value']=='QuestForceDisconnectPersonalLink','Only after proven van failure and original IsPersonalLinkConnected gate; not a synthetic progression bypass')
# Main has only initial instantaneous health check; no continuing native-body health/water listener substitutes it.
ck('main_health267_is_one_shot_not_monitor',n(OW,267,'root/4')['type']=='questConditionNodeDefinition'and[e for e in g(OW,'root/4')['edges']if e[0]=='267']==[['267','False','264','In']],'Alive initial False path can proceed, later van destruction no longer samples267')
es(OW,[(281,'Out',280,'In'),(280,'Out',258,'In')],'root/4');ck('actual_main_waits_missing_fail_fact',n(OW,280,'root/4')['type']=='questPauseConditionNodeDefinition'and n(OW,280,'root/4')['reads'][0]['factName']==F,'Native main cleanup requires unique retired producer')
local=read(P.parent/'source_inspection.json')['sts_wat_nid_02']['resources'];physical=[]
for dp,mm in local.items():
 if '_bugfixing.questphase'in dp:continue
 for gp,gr in mm['graphs'].items():
  for i,nd in gr['nodes'].items():
   if '#nid_02_com'in nd['node_refs']and any(z.get('$type')in ['questCharacterHealth_ConditionType','questVehicleWater_ConditionType']for z in walk(nd['payload'])):physical.append({'resource':dp,'graph':gp,'node':i,'type':nd['type'],'incoming':[e for e in gr['edges']if e[2]==i]})
ck('only_local_main_physical_failure_check_is267',len(physical)==1 and physical[0]['node']=='267',physical)
# Full independent scan: ASCII fact producers plus escaped and hashed broad owner references.
def fnv(v):
 h=14695981039346656037
 for b in v.encode():h=((h^b)*1099511628211)&0xffffffffffffffff
 return str(h)
targets={B,NP,OP,BP};hashes={fnv(x):x for x in targets};needles=[F]+[json.dumps(x)[1:-1]for x in targets]+list(hashes);hits=[];refhits=[];modelpins=[]
for dp,row in S.MI.items():
 data=gzip.decompress(Path(row['normalized_model']).read_bytes())
 if not any(x.encode()in data for x in needles):continue
 mm=json.loads(data);modelpins.append({'path':row['normalized_model'],'sha256':sha(row['normalized_model'])})
 for gp,gr in mm['graphs'].items():
  for i,nd in gr['nodes'].items():
   wr=[x for x in nd['writes']if x.get('factName')==F];rr=[x for x in nd['reads']if x.get('factName')==F]
   if wr or rr:hits.append({'resource':dp,'graph':gp,'node':i,'writes':wr,'reads':rr})
   refs=[]
   for z in walk(nd['payload']):
    if z.get('$type')=='ResourcePath':
     v=str(z.get('$value'));t=v if v in targets else hashes.get(v)
     if t:refs.append(t)
   if refs:refhits.append({'resource':dp,'graph':gp,'node':i,'refs':sorted(set(refs))})
writers=[x for x in hits if x['writes']];ck('only_captured_fail_writer_is_retired_native23_34',len(writers)==1 and writers[0]['resource']==B and writers[0]['graph']=='root/23'and writers[0]['node']=='34',writers)
ck('no_private_failure_producer_or_broad_old_owner_rehost',not any(x['resource'].startswith('towercontinued\\')and x['writes']for x in hits)and not any(x['resource'].startswith('towercontinued\\')for x in refhits),refhits)
# Exact current package source mentions: generated history/admission reads are not controllers.
scriptmentions=[];root=W/'prealpha/quest_restoration_qr4/candidate_01/package'
for p in root.rglob('*'):
 if p.is_file()and p.suffix.lower()in ['.reds','.lua','.yaml','.yml']:
  txt=p.read_text(encoding='utf-8-sig',errors='replace')
  if F in txt:scriptmentions.append({'path':str(p),'sha256':sha(p),'lines':[{'line':i,'text':x}for i,x in enumerate(txt.splitlines(),1)if F in x]})
# Scope: preserve real native parent and all descendants, not assume empty initializer means no support.
scopes={'native_bugfix_root_prefabs':mods[B]['root_prefabs'],'original_monitor23':n(B,23)['payload'],'monitor_nodes':[{'graph':gp,'node':i,'prefabs':nd['prefabs'],'refs':nd['refs'],'node_refs':nd['node_refs']}for gp,gr in mods[B]['graphs'].items()if gp.startswith('root/23')for i,nd in gr['nodes'].items()],'main_root_prefabs':mods[BODY]['root_prefabs']}
ck('native_monitor_no_unreviewed_PIPs',not scopes['native_bugfix_root_prefabs']and not n(B,23)['prefabs']and all(not x['prefabs']for x in scopes['monitor_nodes']),'Full actual monitor subtree and containing metadata, not just root')
ck('whole_native_main_van_support_retained',mods[BODY]['root_prefabs']==['#loc_sts_wat_nid_02_streetstory'],'No new global actor/community support owner approved; preserve exact marker/computer/van refs')
mut=[];bad=copy.deepcopy(g(B,'root/23'));bad['edges'].remove(['41','Out1','34','In']);mut.append({'fault':'missing_actual_van_failure_producer_connection','detected':['41','Out1','34','In']not in bad['edges']})
bad=copy.deepcopy(g(B,'root/23'));bad['edges'].remove(['49','Out','41','In2']);mut.append({'fault':'missing_native_submerged_player_mounted_branch','detected':['49','Out','41','In2']not in bad['edges']})
bad=copy.deepcopy(n(B,41,'root/23')['payload']);bad['$type']='questLogicalAndNodeDefinition';mut.append({'fault':'changed_either_failure_join_to_AND','detected':bad!=n(B,41,'root/23')['payload']})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
evidence={'id':'QR5-G11-NID02-MISSING-FUTURE-VAN-FAILURE-MONITOR','status':'SOURCE_CONFIRMED_PENDING_INDEPENDENT_REVIEW','severity':'HIGH','quest_id':'sts_wat_nid_02','carrier':ENTRY,'carrier_sha256':read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json')['source_resources'][ENTRY],'defective_epoch':'QR5:00 (QR4candidate03); later ARR12/Steven changes unrelated','native_source':B,'native_monitor_graph':'root/23','counterexample':'Verified fresh future NID02 starts nid_02_start1, nid_02_finished0 and initially alive van267.False proceeds. Later van_001 health reaches0 or player-mounted van submerges. Genuine Tower retired original global bugfix23; only main continuing wait280 needs sts_wat_nid_02_fail, whose sole captured writer23/34 is absent from private ownership. No current continuing health/water listener replaces it. Native failure/debrief/token/computer/personal-link cleanup route is structurally missing.','critical_constraints':['CYB-651268 is written before future nid_02_start and may legitimately be1 on a never-started save; do not reset/replay global bugfix','No source patch approved yet; root must receive independent ownership/outcome/reward review of any exact proposal','Prefer fresh positive entry-only private monitor, exact original23 metadata/all branches, with old global prefix bypassed conservatively and no old-save adoption','Ordering must guard before native progression (Steven lesson); preserve original job path even if optional helper refuses unsupported history','Preserve native failure phone/SMS, personal-link disconnect, token, achievement and existing scene/actor references; do not manufacture failure/ack/completion','Native foreign PAC02 objective Inactive92 is a separate original target/history risk; not part of this missing monitor repair'],'checks':len(T),'raw_input_resources':len(pins),'fresh_new_raw_exports':3,'global_models_scanned':len(S.MI),'global_scan':str(O/'global_scan.json'),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'scope':str(O/'scopes.json'),'affected_contracts':['communications','ownership','progression','completion_rewards_cleanup','shared_dependencies'],'limits':['Static missing native controller/producer proven within pinned source universe, not an in-game failure observation','World/vehicle/community placements, external dynamic fact writers and engine critical-entity behavior not fully resolved','Already-started/saved old monitor owners need separate adoption evidence; no CYB/history reset authorized'],'runtime_changes':[]}
save(O/'tests.json',{'checks':T,'mutations':mut});save(O/'source_pins.json',pins);save(O/'global_scan.json',{'models':len(S.MI),'fact_hits':hits,'reference_hits':refhits,'pins':modelpins,'script_mentions':scriptmentions,'escaped_and_FNV_refs':hashes});save(O/'scopes.json',scopes);save(O/'evidence.json',evidence);print(json.dumps({'checks':len(T),'models':len(S.MI),'evidence_sha256':sha(O/'evidence.json')}))
