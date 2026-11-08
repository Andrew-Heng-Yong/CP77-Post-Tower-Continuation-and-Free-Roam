import sys,json,copy,gzip,zlib,argparse
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]));from lib import *
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True);S=Store();T=[];models={};pins=[];mut=[]
def ck(n,b,e):T.append({'name':n,'status':'PASS'if b else'FAIL','evidence':e});assert b,n
for x in read(P/'raw_exports_01/manifest.json'):
 ck('actual_raw_source_pin '+x['depot'],sha(x['raw'])==x['raw_sha256'],x['raw']);ck('fresh_JSON_pin '+x['depot'],sha(x['json'])==x['json_sha256'],x['json']);m=Resource(read(x['json'])).normalize();ck('fresh_raw_no_decode_error '+x['depot'],not m['errors'],m['errors']);models[x['depot']]=m;pins.append(x)
def d(t):return next(d for d in models if d.endswith('\\'+t))
def g(d,gp='root'):return models[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
def es(d,edges,gp='root'):
 for e in edges:ck('actual_edge '+d+' '+gp+str(e),edge(d,*e,gp=gp),e)
def has(d,i,f,op,v,gp='root'):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in n(d,i,gp)['reads'])
EP=d('ep1.questphase');AD=d('ep1_additional_game_elements.questphase');DD=d('ep1_default_dialogs.questphase');ACT=d('steven_default.questphase');BOOT=d('steven_boot.questphase');SPY=d('sts_ep1_08_entry.questphase');CL=d('sts_ep1_08_cleanup.questphase');NC=d('sts_08_steven_default_new_biomonitor_not_destroyed.scene');STAD=d('sts_08_steven_default_stadium.scene');E=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json')
for dp in [SPY,BOOT]:ck('private_actual_frozen_epoch00 '+dp,sha(next(x['raw']for x in pins if x['depot']==dp))==E['source_resources'][dp],dp)
ck('Tower_actual_EP1_cut_predicate',any(x.get('state')=='Succeeded'and x.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow'for x in n(EP,8,'root/10')['reads']),n(EP,8,'root/10')['payload']);es(EP,[(8,'Out',9,'In'),(9,'CutSource',4,'CutDestination'),(9,'Out',10,'In')],'root/10');ck('actual_cut_subtree_has_default_owner',n(EP,4,'root/10')['refs']==[AD]and n(AD,1)['refs']==[DD],{'ep1':'root/10:4','additional':'root:1','default':'root:17/19'})
es(DD,[(3,'Out1',19,'In'),(19,'Out',17,'In1'),(17,'Out1',19,'In')]);ck('native19_default_wait_exact_flags',has(DD,19,'steven_santos_default_on','Greater',0)and has(DD,19,'q304_stadium_escape_active','Equal',0),'Native parent does NOT itself exclude Ana; future actor dispatch needs late Ana0 narrowing')
ck('native17_actor_ref_exact',n(DD,17)['refs']==[ACT],ACT);es(SPY,[(23,'Out1',64000,'In1'),(23,'Out1',65005,'In')],'root/50');ck('actual_private_real_cleanup_reference',n(SPY,64000,'root/50')['refs']==[CL],CL);es(CL,[(0,'Out',88,'In'),(88,'Out',3,'In1')]);ck('native66hour_timer',n(CL,5,'root/3')['payload']['condition']['type']['hours']==66,n(CL,5,'root/3')['payload'])
es(CL,[(0,'Out',3,'In'),(3,'False',5,'In'),(3,'True',4,'In'),(4,'Out',6,'In'),(6,'Out',2,'In'),(56,'Out',8,'In'),(8,'Out',58,'Active'),(58,'Out',96,'Active'),(96,'Out',17,'In'),(17,'Out',59,'Succeeded'),(59,'Out',9,'Active'),(9,'Out',2,'In')],'root/3');ck('native_cleanup_default_on_writer',n(CL,2,'root/3')['writes']==[{'$type':'questSetVar_NodeType','factName':'steven_santos_default_on','setExactValue':1,'value':1}],n(CL,2,'root/3')['payload'])
ck('Ana_branch_also_writes_default_on1',has(CL,3,'sts_ep1_08_biomonitor_ana','Greater',0,'root/3')and edge(CL,3,'True',4,'In','root/3')and edge(CL,6,'Out',2,'In','root/3'),'Late Ana exclusion is required; entry-time Ana0 is not enough before later job choice')
es(ACT,[(0,'Out',2,'In'),(2,'False',5,'In'),(2,'False',26,'In'),(2,'True',3,'In'),(2,'True',24,'In'),(26,'Out',28,'In1'),(28,'Out1',26,'In'),(24,'Out',27,'In1')]);ck('native_actor_branch_selection',has(ACT,2,'sts_ep1_08_biomonitor_ana','Greater',0),'Native True stadium community/scene27;False NightCity community/scene28. Caller must narrow dispatch without editing native actor body')
ck('NightCity_scene_and_marker_reference',n(ACT,3,'root/28')['refs']==[NC]and '#sts_08_sm_steven_default_new_biomonitor_not_destroyed'in n(ACT,3,'root/28')['node_refs'],'Exact original scene/marker, not arbitrary spawned actor');ck('stadium_scene_is_distinct',n(ACT,3,'root/27')['refs']==[STAD],STAD)
es(ACT,[(3,'End 2',13,'In'),(13,'CutSource',11,'CutDestination'),(13,'Out',15,'Succeeded'),(15,'Out',16,'Succeeded'),(16,'Out',33,'In'),(33,'Out',30,'In'),(30,'Out',12,'In'),(12,'Out',7,'In'),(7,'Out',14,'In'),(14,'Out',23,'In'),(23,'Out',27,'In')],'root/28');ck('authored_native_default_off_cleanup_preserved',n(ACT,14,'root/28')['writes']==[{'$type':'questSetVar_NodeType','factName':'steven_santos_default_on','setExactValue':1,'value':0}],'Legitimate native post-conversation cleanup, not an invented historical reset')
# All actual ancestor/PIP scopes, not only empty actor root.
scopes=[{'depot':dp,'root_prefabs':models[dp]['root_prefabs']}for dp in [EP,AD,DD,ACT]]
for dp,gp,i in [(EP,'root',10),(EP,'root/10',4),(AD,'root',1),(DD,'root',17)]:ck('ancestor_PIP_empty '+dp+gp+str(i),not n(dp,i,gp)['prefabs'],n(dp,i,gp)['payload'])
ck('ancestor_root_prefabs_empty',all(not x['root_prefabs']for x in scopes),scopes)
for gp,gr in models[ACT]['graphs'].items():
 for i,nd in gr['nodes'].items():
  ck('ALL_recursive_actor_PIPs '+gp+':'+i,not nd['prefabs'],'No recursive root27/28 helper support stripped');scopes.append({'depot':ACT,'graph':gp,'node':i,'prefabs':nd['prefabs'],'refs':nd['refs'],'node_refs':nd['node_refs']})
# Exact old supported pre-Tower ownership remains distinct and refuses future U9 case.
for i in [2,3,90]:ck('currentS23_excludes_U9_and_existing_default '+str(i),all(has(BOOT,i,f,'Equal',0)for f in ['PTFRU9_sts_ep1_08_ParentEntered','PTFRU9_sts_ep1_08_Started','steven_santos_default_on']),n(BOOT,i)['reads'])
condition=n(BOOT,3)['payload']['condition'];facts={};journals={}
for z in n(BOOT,3)['reads']:
 if 'factName'in z:
  f=z['factName'];v=z['value'];op=z['comparisonType'];facts.setdefault(f,v+1 if op=='Greater'else v-1 if op=='Less'else v)
 if z.get('$type')=='questJournalEntryState_ConditionType':journals[z['path']['realPath']]=z['state']
ck('supported_preTower_fixture_still_admits',evaluate(condition,facts,journals)is True,{'facts':facts,'journals':journals});future=facts|{'PTFRU9_sts_ep1_08_ParentEntered':1,'PTFRU9_sts_ep1_08_Started':1,'steven_santos_default_on':1};ck('actual_future_U9_counterexample_refuses_S23',evaluate(condition,future,journals)is False,'Native invitation visited/default1 is not an actor owner; original actor tree cut and private S23 refuses all three actual flags')
for i in [17,19]:ck('old_S23_actor_payload_exact_native '+str(i),n(BOOT,i,'root/100')['payload']==n(DD,i)['payload'],'No S23 relaxation/message replay needed')
# Independent full model/resource-reference scan also checks numeric FNV depot references.
def fnv(s):
 h=14695981039346656037
 for b in s.encode():h=((h^b)*1099511628211)&0xffffffffffffffff
 return str(h)
ck('FNV_depot_identity_matches_independent_known_filekey',fnv(ACT)=='15519998154120600467','Actor key recorded by resource inventory/ArchiveReader, not guessed NodeRef hashing')
targets={ACT,DD,AD,EP,NC,STAD};hm={fnv(x):x for x in targets};hits=[];rawpins=[]
for dp,row in S.MI.items():
 data=gzip.decompress(Path(row['normalized_model']).read_bytes())
 if not any(t.encode()in data for t in [json.dumps(x)[1:-1]for x in targets]+list(hm)+['steven_santos_default_on','#steven_default_night_city_com']):continue
 mm=json.loads(data);rawpins.append({'path':row['normalized_model'],'sha256':sha(row['normalized_model'])})
 for gp,gr in mm['graphs'].items():
  for i,nd in gr['nodes'].items():
   refs=[]
   for z in walk(nd['payload']):
    if z.get('$type')=='ResourcePath':
     v=str(z.get('$value'));t=v if v in targets else hm.get(v)
     if t:refs.append(t)
   if refs:hits.append({'depot':dp,'graph':gp,'node':i,'refs':sorted(set(refs))})
private=[x for x in hits if x['depot'].startswith('towercontinued\\')];ck('only_known_private_actor_reference_is_S23',[(x['depot'],x['graph'],x['node'])for x in private if ACT in x['refs']]==[(BOOT,'root/100','17')],private);ck('no_hidden_broad_parent_private_reference',not any(set(x['refs'])&{DD,AD,EP}for x in private),'Includes decoded names and numeric FNV ResourcePath values; no broad EP1/default rehost discovered')
# Source fault oracles/mutations require a real native actor call, not only message/default flag presence.
def future_owner(owners,f):return any(x['depot']!=BOOT for x in owners if ACT in x['refs'])or evaluate(condition,f,journals)is True
ck('defective_actual_sources_fail_future_owner_oracle',not future_owner(private,future),'Counterexample must distinguish actual actor owner from SMS/default flag')
bad=copy.deepcopy(private)+[{'depot':'review_fixture_only','graph':'helper','node':'17','refs':[ACT]}];mut.append({'fault':'missing_future_actor_consumer','detected':future_owner(bad,future)and not future_owner(private,future),'fixture':'Non-runtime actor owner model only; no patch approval'})
# Show the erroneous early-only Ana fence can admit a later forbidden choice.
entry=future|{'sts_ep1_08_biomonitor_ana':0};later=entry|{'sts_ep1_08_biomonitor_ana':1};native_dispatch=has(DD,19,'steven_santos_default_on','Greater',0)and later['steven_santos_default_on']>0;mut.append({'fault':'Ana_only_checked_at_entry','detected':native_dispatch and later['sts_ep1_08_biomonitor_ana']==1,'required':'Late default wait/dispatch must additionally require Ana0 on every iteration'})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
report={'status':'SOURCE_CONFIRMED_FUTURE_U9_STEVEN_ACTOR_OWNER_GAP_PENDING_EXACT_PROPOSAL','checks':len(T),'actual_raw_resources':len(pins),'mutations':len(mut),'native_actor':ACT,'carrier':SPY,'counterexample':future,'source_finding':'Actual U9 main completion owns native cleanup/invitation but original EP1 default actor tree is cut; sole private actor call is S23 and actual future flags refuse that guard','constraints':['No patch approved until exact proposal','Future positive entry event only; unknown/already-entered saved owners require separate adoption review','Keep existing S23 exclusion/actor/message slices and all native cleanup66hour/SMS/journal/timer branches unchanged','Late actor dispatch must require native19 plus Ana0; entry-time Ana0 alone is insufficient','Initial fresh enrollment conditions must not be reapplied at post-completion late wait when Started/OwnerFinished legitimately1','Native actor28 full journal/default-off/contact/notifier/vehicle cleanup and loop lifetime must remain exact','No new global default/additional parent, new prefab owner or stadium/Ana branch invocation'],'scopes':str(O/'scopes.json'),'global_scan':str(O/'global_references.json'),'tests':str(O/'tests.json'),'limits':['World sectors/community placements/NodeRef resolution and independent saved/external-mod runtime ownership remain opaque','Static missing controller route does not itself prove in-game actor absence','Full scan is5136 pinned normalized models plus actual selected resources against frozenQR5epoch00; later ARR12 change is unrelated'],'runtime_changes':[],'scan_refinement':'NEW supersession evidence: resource depot prefilter now matches JSON-escaped backslashes as well as numeric FNV IDs; original source_verification_01 and proposal reviews preserved unchanged'}
save(O/'tests.json',{'checks':T,'mutations':mut});save(O/'source_pins.json',pins);save(O/'scopes.json',scopes);save(O/'global_references.json',{'models_scanned':len(S.MI),'hits':hits,'pins':rawpins,'numeric_ResourcePath_FNV_map':hm});save(O/'review.json',report);print(json.dumps({'checks':len(T),'mutations':len(mut),'review_sha256':sha(O/'review.json')}))
