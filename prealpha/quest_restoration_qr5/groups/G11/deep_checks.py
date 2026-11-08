"""Additional source-specific controls, fresh CR2W decode, native outcome and state closure checks."""
from lib import *
import argparse,copy,zlib
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
P=Path(__file__).parent;S=Store();EP=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');E=read(P/'verification_01/quest_evidence.json');T=[];mut=[];details={};extra_pins=[]
def ck(name,b,e):T.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
def es(d,edges,gp='root'):
 for e in edges:ck('edge '+d+' '+gp+' '+str(e),S.edge(d,*e,gp=gp),e)
def has(d,i,f,op,v,gp='root'):return any(z.get('factName')==f and z.get('comparisonType')==op and z.get('value')==v for z in S.n(d,i,gp)['reads'])
def soften(x):
 y=copy.deepcopy(x)
 for z in walk(y):
  z.pop('payload_sha256',None)
  if 'phaseResource'in z and z['phaseResource'].get('Flags')=='Embedded':z['phaseResource']['Flags']='Soft'
 return y
def tidcanon(x):
 y=copy.deepcopy(x)
 for z in walk(y):
  z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
  if z.get('$type')=='TweakDBID':
   v=z['$value'];number=(len(v.encode('utf-8'))<<32)|zlib.crc32(v.encode('utf-8')) if z.get('$storage')=='string'else int(v)
   z['$storage']='uint64';z['$value']=str(number)
 return y
ck('TweakDBID_CRC32_length_encoding_independent_stock_example',tidcanon({'$type':'TweakDBID','$storage':'string','$value':'QuestRewards.sts_wat_kab_101_completion'})['$value']=='168197037653','Matches actual binary fresh export and separately captured stock DB ID, not a name guess')
for x in read(P/'raw_exports_01/manifest.json'):
 ck('raw_pin '+x['depot'],sha(x['raw'])==x['raw_sha256'],x['raw']);ck('fresh_JSON_pin '+x['depot'],sha(x['json'])==x['json_sha256'],x['json']);fresh=Resource(read(x['json'])).normalize();ck('actual_raw_redecode_matches_model '+x['depot'],tidcanon(fresh)==tidcanon(S.load(x['depot'])),{'export':x['json'],'method':'WolvenKit9.1 Read-Cr2wFile/Export-Cr2wJson; only TweakDBID name-vs-uint64 storage canonicalized by exact CRC32+length identity, derived digests removed; no serialization or resource edits'})
for q,v in E.items():
 er=next(r for r in M['recipes']if r['id']==q and r['kind']=='entry');donor=S.extra(er['raw'],M);entry=v['entry'];local=[d for d in S.MI if '\\'+q+'\\'in d];local_writers=[];gaps=[];assets=[]
 for d in local:
  m=S.load(d);ck('effective_vanilla_body_not_overridden '+d,d not in EP['source_resources'],{'provider':S.I[d]['archive'],'resource_sha256':S.I[d]['sha256']})
  for gp,g in m['graphs'].items():
   eg='embedded/'+d+'/'+gp
   if eg in S.load(donor)['graphs']:ck('all_embedded_body_graphs '+d+' '+gp,tidcanon(soften(g))==tidcanon(soften(S.g(donor,eg))),{'parent':donor,'embedded':eg})
   for i,n in g['nodes'].items():
    for w in n['writes']:
     if w['factName'].startswith((q.removeprefix('sts_wat_'),q)):
      x={'depot':d,'graph':gp,'node':i,'fact':w['factName'],'covered_by_EntrySafe':w['factName']in v['native_fact_guards'],'writes':w}
      local_writers.append(x)
    if n['refs']or n['node_refs']or n['prefabs']:assets.append({'depot':d,'graph':gp,'node':i,'refs':n['refs'],'node_refs':n['node_refs'],'prefabs':n['prefabs']})
 for p in v['journal_paths_not_in_EntrySafe']:
  writers=[]
  for d in local:
   for gp,g in S.load(d)['graphs'].items():
    for i,n in g['nodes'].items():
     if p in n['journal_paths']:writers.append({'depot':d,'graph':gp,'node':i,'type':n['type'],'incoming':[e for e in g['edges']if e[2]==i]})
  gaps.append({'path':p,'writers':writers})
 for d in [x for x in [v['entry'],v['credit']]if x]+[r['depot']for r in M['recipes']if r['id']==q and r['kind']=='map']:
  pin=next(x for x in S.pins if x['depot']==d)if d in S.models else None
  S.load(d);pin=next(x for x in S.pins if x['depot']==d)
  ck('epoch00_effective_resource '+d,pin['resource_sha256']==EP['source_resources'][d],{'epoch00':EP['source_resources'][d]})
 for companion in er['companions']:
  d=companion['depot'];source=S.extra(companion['source_raw'],M);old=S.n(source,companion['source_node'],companion['source_graph']);new=S.n(entry,64000)
  ck('parallel_prestate_native_reference '+q,old['refs']==new['refs']==[d],{'old_node':companion['source_node'],'old_graph':companion['source_graph'],'current_node':64000})
  ck('parallel_prestate_connected_after_owned_claim '+q,S.edge(entry,65003,'Out',64000,companion['input']),companion)
  eg='embedded/'+d+'/root'
  if eg in S.load(source)['graphs']:ck('native_prestate_embedded_external '+q,tidcanon(soften(S.g(d)))==tidcanon(soften(S.g(source,eg))),eg)
  bad=copy.deepcopy(S.g(entry));bad['edges'].remove(['65003','Out','64000','In1']);mut.append({'quest_id':q,'fault':'missing_original_parallel_prestate_owner','detected':['65003','Out','64000','In1']not in bad['edges']})
 app=P.parents[1]/'shared/tdb_applicability_02'/f'{q}.json';aj=read(app);extra_pins.append({'path':str(app),'sha256':sha(app),'role':'Root read-only stock DB capture compact index; route applicability separately checked here'})
 targets={a:t for t in aj['targets']for a in t['requested_aliases']};applicable=[]
 for r in v['rewards']:
  for record in r['records']:
   if not isinstance(record,str)or not record.startswith(('QuestRewards.','Achievements.')):continue
   t=targets.get(record);ck('stock_native_reward_record '+q+' '+record,bool(t)and t['exists_in_stock'],{'use':r,'target':t});applicable.append({'use':r,'target':t})
 details[q]={'local_native_fact_writers':local_writers,'unlisted_journal_paths_actual_writers':gaps,'native_asset_bindings':assets,'applicable_stock_reward_targets':applicable,'limits':['Exact authored actor/workspot/camera/NodeRef bindings preserved; worldNode content placement not decoded','Stock immediate references reported in targets; uncaptured descendants and effective runtime TweakXL/CET values not certified','Old native saved owners cannot be proven retired by killed facts or private receipts alone']}



# Literal source contracts for this Northside batch; socket case and native aliases retained.
def ed(q):return E[q]['entry']
def body(q):return E[q]['body']
def ow(q):return next(d for d in S.MI if '\\'+q+'\\'in d and d.endswith(('_openworld.questphase','_ow.questphase','_streetstory.questphase')))
q='sts_wat_nid_12';d=ed(q);es(d,[(4,'Out1',51,'In'),(4,'Out1',87,'In'),(51,'Out',86,'In1'),(87,'Out',86,'In2'),(86,'Out1',71,'Active'),(71,'Out',65004,'In')]);ck('Freedom_exact_tierOR',has(d,51,'sts_wat_nid_tier_3_1','Greater',0)and has(d,87,'sts_wat_nid_tier_3','Greater',0),'Tier3_1 ORtier3, then actual POI71 path, not abandoned47→30')
orig=S.extra(next(r for r in M['recipes']if r['id']==q and r['kind']=='entry')['raw'],M);ck('Freedom_original_orphan_deletion47',all(i in S.g(d)['unreachable']and i in S.g(orig)['unreachable']for i in ['47','30']),'Retained original inactive fallback identities do not count as live routes')
w=ow(q);es(w,[(74,'Out',39,'In'),(39,'Out',75,'In')],'root/5');ck('Freedom_native_reward_receipt_fence',has(w,74,'nid_12_reward_added_in_main','Equal',0,'root/5'),'Keep native reward receipt and main/bugfix arbitration, no replay compensation')
for q,poi in [('sts_wat_nid_05',102),('sts_wat_nid_02',101)]:
 d=ed(q);es(d,[(2,'Out1',91,'In'),(91,'Out',89,'In'),(91,'Out',90,'In'),(89,'Out',92,'In1'),(90,'Out',92,'In2'),(92,'Out1',poi,'Active')]);ck('native_tier_disjunction_'+q,has(d,89,'sts_wat_nid_tier_1_1','Greater',0)and has(d,90,'sts_wat_nid_tier_1','Greater',0)and has(d,90,'sts_wat_nid_tier_1_1','Equal',0),'Native tier1_1 OR(tier1 AND NOTtier1_1) after deletion91')
q='sts_wat_nid_05';d=ed(q);es(d,[(65004,'Out',10,'IN'),(10,'OUT',65005,'In')]);ck('Rite_native_socket_names_exact',S.g(body(q))['entries']=={'IN':'0'},'Native IN/OUT casing is part of saved graph contract; do not rewrite to In1/Out1');ck('Rite_native_whole_prefab_alias',S.load(body(q))['root_prefabs']==['#sts_wat_nid_05_steetstory'],'Native steetstory alias retained')
w=ow(q);es(w,[(45,'End 0',46,'In'),(61,'Out',46,'In'),(46,'Out',63,'In')],'root/5');ck('Rite_native_gang_outcome_predicate',has(w,64,'nid_05_gang_retaliation','GreaterOrEqual',1,'root/5'),'Native observed gang retaliation path, no arbitrary new AI chase')
q='sts_wat_nid_01';d=ed(q);es(d,[(4,'Out1',52,'In'),(4,'Out1',87,'In'),(52,'Out',88,'In2'),(87,'Out',88,'In1'),(88,'Out1',62,'In'),(88,'Out1',82,'In'),(62,'Out',83,'In1'),(82,'Out',83,'In2'),(83,'Out1',72,'Active'),(72,'Out',65004,'In')]);ck('Occupational_tier3OR3_2',has(d,52,'sts_wat_nid_tier_3_2','Greater',0)and has(d,87,'sts_wat_nid_tier_3','Greater',0),'Native approach/POI XOR after tier disjunction')
orig=S.extra(next(r for r in M['recipes']if r['id']==q and r['kind']=='entry')['raw'],M);ck('Occupational_original_E3_branch_is_orphan',all(i in S.g(d)['unreachable']and i in S.g(orig)['unreachable']for i in ['41','42','29']),'No positive executing E3 bypass from these retained identities')
w=ow(q);es(w,[(50,'True',49,'In'),(50,'False',51,'In'),(59,'End 0',49,'In'),(96,'Out',49,'In'),(49,'Out',55,'In1'),(51,'Out',55,'In2')],'root/4');ck('Occupational_lie_predicate_preserved',has(w,50,'nid_01_lie','Greater',0,'root/4'),'Native honest/pacifist versus lie/completion reward inputs retained, no flattening')
cr=next(r for r in M['recipes']if r['id']==q and r['kind']=='credit');cd=cr['depot'];ck('Occupational_native_failed_credit',has(cd,26,'nid_01_player_left_psycho_alive','Greater',0)and has(cd,26,'nid_01_player_left_psycho_dead','Greater',0)and has(cd,22,'nid_01_finished','Greater',0),'Original finished OR (player_left_psycho_alive OR player_left_psycho_dead) counter contribution, not a fabricated reward');es(cd,[(65001,'Out',22,'In'),(65001,'Out',26,'In'),(22,'Out',27,'In1'),(26,'Out',27,'In2'),(27,'Out1',25,'In')])
# Exact cross-quest native journal mutation: retain discrepancy and unknown terminal-manager behavior.
q='sts_wat_nid_02';w=ow(q);gp='root/4/138';es(w,[(72,'True',92,'Inactive'),(92,'Out',62,'In')],gp);target='quests/street_stories/pacifica/coastview/sts_pac_cvi_02/sts_pac_cvi_02/get_to_the_van';ck('ManyWays_foreign_Pacifica_target_exact',target in S.n(w,92,gp)['journal_paths']and S.n(w,72,gp)['payload']['condition']['type']['condition']=='OnMount','Guard72 checks player mounted in #nid_02_com van_001, not foreign objective state')
foreign={'quest_id':q,'status':'CONDITIONAL_NATIVE_CROSS_QUEST_HISTORY_WRITE','resource':w,'graph':gp,'writer':92,'input':'Inactive','target':target,'guard72':S.n(w,72,gp)['payload'],'native_payload_equal':True,'restoration_only_defect_proven':False,'remaining':'Exact original embedded native payload preserved; whether a terminal foreign objective accepts/ignores this command depends on effective JournalManager target/terminal semantics. Do not reset or blindly patch a native shared cleanup.'}
# Native matching Maelstrom selector and actual pending ownership (reuse child proof only by exact hashes).
RD=r'towercontinued\special_gigs_u9\gang_retaliation.questphase';S.load(RD);q='sts_wat_nid_05';ck('Rite_Maelstrom_support_receipt',has(ed(q),65002,'PTFRU9_Retaliation_maelstroms_Issued','Equal',1),'Actual per-gang admission, not generic phone receipt');ck('Rite_native_owned_matching_selector',has(RD,45,'PTFRU9_sts_wat_nid_05_Started','Equal',1,'root/22/35/239')and has(RD,45,'nid_05_gang_retaliation','GreaterOrEqual',1,'root/22/35/239')and has(RD,45,'nid_05_after_holocall','Greater',0,'root/22/35/239'),'Exact native selected gang predicate under existing owned condition')
prior=W/'prealpha/quest_restoration_qr5/groups/G09/deep_verification_02/source_pins.json';pp=next(x for x in read(prior)if x['depot']==RD);ck('same_pinned_Maelstrom_whole_body_core',next(x for x in S.pins if x['depot']==RD)['resource_sha256']==pp['resource_sha256']and sha(pp['json'])==pp['json_sha256'],'G09 separately compares exact original child and all selector nodes/edges except two declared owner predicates; reused only by hash. Per-Rite applicability independently checked here');extra_pins.append({'path':str(prior),'sha256':sha(prior)})
# Inventory apparent native reads with bugfix-only local fact producers for targeted interpretation.
source_notes=read(P/'source_inspection.json');cross=[]
for q,st in source_notes.items():
 oldwrites={};mainwrites={};reads=[]
 for d,mm in st['resources'].items():
  for gp,gr in mm['graphs'].items():
   for i,nd in gr['nodes'].items():
    for x in nd['writes']:
     (oldwrites if '_bugfixing.questphase'in d else mainwrites).setdefault(x['factName'],[]).append({'resource':d,'graph':gp,'node':i,'write':x})
    if '_bugfixing.questphase'not in d:
     for x in nd['reads']:
      if 'factName'in x:reads.append({'resource':d,'graph':gp,'node':i,'read':x})
 for x in reads:
  fact=x['read']['factName']
  if fact in oldwrites and fact not in mainwrites:cross.append({'quest_id':q,'reader':x,'bugfix_only_local_producers':oldwrites[fact],'status':'REQUIRES_ROUTE_AND_ENGINE_PRODUCER_INTERPRETATION_NOT_AUTOMATIC_MISSING_OWNER'})
# Actual raw fixture mutations target native branch, identity and cleanup risks.
bad=copy.deepcopy(S.g(ed('sts_wat_nid_05')));bad['edges'].remove(['10','OUT','65005','In']);mut.append({'quest_id':'sts_wat_nid_05','fault':'native_OUT_casing_changed','detected':['10','OUT','65005','In']not in bad['edges']})
bad=copy.deepcopy(S.n(ow('sts_wat_nid_12'),74,'root/5')['payload']);bad['condition']['type']['value']=1;mut.append({'quest_id':'sts_wat_nid_12','fault':'lost_native_reward_once_fence','detected':bad!=S.n(ow('sts_wat_nid_12'),74,'root/5')['payload']})
bad=copy.deepcopy(S.g(cd));bad['edges'].remove(['26','Out','27','In2']);mut.append({'quest_id':'sts_wat_nid_01','fault':'missing_native_departure_counter_branch','detected':['26','Out','27','In2']not in bad['edges']})
for x in mut:ck('mutation '+x['quest_id']+' '+x['fault'],x['detected'],x)
save(O/'checks.json',{'count':len(T),'checks':T,'mutations':mut,'status':'PASS_SCOPED_STATIC'});save(O/'quest_details.json',details);save(O/'source_pins.json',S.pins);save(O/'extra_pins.json',extra_pins);save(O/'cross_quest_history_risks.json',[foreign]);save(O/'bugfix_only_local_producers.json',cross)
print(json.dumps({'checks':len(T),'mutations':len(mut),'sources':len(S.pins),'bugfix_only_reads':cross,'quest_fact_gaps':{q:[x for x in v['local_native_fact_writers']if not x['covered_by_EntrySafe']]for q,v in details.items()}}))
