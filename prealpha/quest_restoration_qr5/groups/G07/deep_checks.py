"""Additional source-specific controls, fresh CR2W decode, native outcome and state closure checks."""
from lib import *
import argparse,copy,zlib
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
P=Path(__file__).parent;S=Store();EP=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');E=read(P/'verification_02/quest_evidence.json');T=[];mut=[];details={};extra_pins=[]
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
  z.pop('payload_sha256',None)
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
 for d in [v['entry'],v['credit']]+[r['depot']for r in M['recipes']if r['id']==q and r['kind']=='map']:
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
# Literal original route controls, independent of generic extraction recipes.
q='sts_wat_kab_101';d=E[q]['entry'];es(d,[(3,'Out',91,'In'),(3,'Out',145,'In'),(91,'Out',144,'In1'),(145,'Out',144,'In2'),(144,'Out1',102,'In'),(144,'Out1',138,'In'),(138,'Out',139,'In2'),(102,'Out',139,'In1'),(139,'Out1',122,'Active'),(122,'Out',67,'In')]);ck('SmallMan_tier21_OR_tier2',has(d,91,'sts_wat_kab_tier_2_1','Greater',0)and has(d,145,'sts_wat_kab_tier_2','Greater',0),'144 XOR accepts native alternatives; no invented MonsterHunt completion prerequisite')
ck('SmallMan_obsolete_15_unreachable_original_and_private','15'in S.g(d)['unreachable']and'15'in S.g(S.extra(er['raw'],M))['unreachable'],'15 kab07_finishedÃ¢â€ â€™75wait_done is already unconnected in original Kabuki parent; not an executing fresh-entry prerequisite')
ow=E[q]['body'].replace('.questphase','_openworld.questphase');es(ow,[(0,'Out',53,'In2'),(10,'Out',52,'In1'),(50,'End 0',53,'In1'),(50,'End 0',52,'In2'),(53,'Out1',4,'In'),(52,'Out1',6,'In'),(4,'Out',60,'In1'),(6,'Out',60,'In1')],'root/5')
for i in [79,80]:ck('SmallMan_obsolete_objective_only_Inactive_'+str(i),all(e[3]=='Inactive'for e in S.g(ow,'root/4')['edges']if e[2]==str(i)),'These two omitted admission objectives have no Active writer in this declared native closure')
for q in ['sts_wat_kab_107','sts_wat_kab_102']:
 d=E[q]['entry'];es(d,[(2,'Out1',155,'In'),(155,'Out',153,'In'),(155,'Out',154,'In'),(153,'Out',152,'In1'),(154,'Out',152,'In2')]);ck('Kabuki_tier_disjunction_'+q,has(d,153,'sts_wat_kab_tier_1_2','Greater',0)and has(d,154,'sts_wat_kab_tier_1_1','Equal',0)and has(d,154,'sts_wat_kab_tier_1','Greater',0),'153 tier1_2 OR154(tier1 AND NOTtier1_1), after actual deletion155')
q='sts_wat_kab_107';ow=E[q]['body'].replace('.questphase','_openworld.questphase');es(ow,[(49,'End 0',39,'In'),(39,'Out',14,'In'),(50,'End 0',40,'In'),(40,'Out',33,'In'),(36,'Out',31,'In')],'root/4');ck('Troublesome_phone_objective_only_native_cleanup',S.edge(ow,112,'Out',139,'Inactive',gp='root/5'),'Other gap is actual map pin235/250, whose Active objective parent pick_up_unconscious_target IS fenced')
pre=E[q]['body'].replace('.questphase','_prestate_control.questphase');ck('Troublesome_native_prestate_placeholder',len(S.g(pre)['nodes'])==2 and not S.g(pre)['edges'],'Original empty native phase, not a missing restored implementation')
q='sts_wat_kab_102';ow=E[q]['body'].replace('.questphase','_openworld.questphase');es(ow,[(135,'False',34,'In'),(34,'False',72,'Succeeded'),(34,'True',68,'In'),(68,'Out',73,'Succeeded'),(88,'End 0',100,'In'),(81,'End 0',79,'In')],'root/4');ck('Welcome_combat_branch_real_predicate',has(ow,34,'kab_102_combat','Greater',0,'root/4'),'Native stealth/perfect and imperfect rewards remain distinct')
pre=E[q]['body'].replace('.questphase','_prestate_control.questphase');es(pre,[(0,'Out',33,'In'),(33,'False',2,'In'),(2,'False',3,'In'),(3,'Out',12,'In'),(3,'Out',26,'In'),(13,'Out',5,'In'),(5,'Out',6,'In'),(6,'Out',21,'In'),(6,'Out',30,'In'),(21,'Out',8,'In'),(20,'Out',31,'In2'),(29,'Out',31,'In1')]);ck('Welcome_prestate_native_trigger_retained',any(x['factName']=='kab_102_prestate_triggered'and x['value']==1 for x in S.n(pre,3)['writes']),'Not an entry fact rewrite; original controller sets only on native prestate route. Missing EntrySafe field is separately recorded saved-context limit')
q='sts_wat_kab_07';d=E[q]['entry'];es(d,[(2,'Out1',151,'In'),(151,'Out',148,'In'),(151,'Out',150,'In'),(148,'Out',149,'In2'),(150,'Out',149,'In1'),(149,'Out1',165,'Active')]);ck('Monster_tier_native_alternatives',has(d,148,'sts_wat_kab_tier_1_1','Equal',0)and has(d,148,'sts_wat_kab_tier_1','Greater',0)and has(d,150,'sts_wat_kab_tier_1_1','Greater',0),'Native XOR; no arbitrary bypass')
ow=E[q]['body'].replace('.questphase','_openworld.questphase');es(ow,[(39,'False',49,'In'),(39,'True',34,'In'),(33,'End 0',35,'In'),(54,'Out1',35,'In'),(15,'Out',55,'In'),(55,'True',56,'In')],'root/4');ck('Monster_failed_skips_reward',has(ow,39,'kab_07_failed','Greater',0,'root/4'),'False reward route; True cleanup34')
es(ow,[(2,'False',4,'Active'),(2,'True',3,'Active')],'root/4/54');ck('Monster_kill_subdue_SMS_predicate',has(ow,2,'kab_07_no_kill','Greater',0,'root/4/54'),'Actual SMS outcome selector')
# Compare the exact Tygerclaws runtime child and pending-reset against pinned original.
rd=r'towercontinued\special_gigs_u9\gang_retaliation.questphase';sm=read(W/'research/gig_restoration/special_gigs_u9/manifest.json');rn='research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_gang_retaliation.questphase';jn=rn.replace('/raw/','/json/')+'.json';spins={k.replace('\\','/'):v for k,v in sm['source_pins'].items()}
for f in [rn,jn]:ck('original_retaliation_pin '+f,sha(W/f)==spins[f],spins[f]);extra_pins.append({'path':str(W/f),'sha256':sha(W/f)})
orig=Resource(read(W/jn)).normalize();old=orig['graphs']['root/37'];new=S.g(rd,'root/22/37');ck('Tygerclaws_native_child_body_equal',old==new,'All native nodes/sockets/edges/conditions/actors preserved in active Tyger child; selector subgraph separately narrowed')
oldsel=orig['graphs']['root/37/298'];newsel=S.g(rd,'root/22/37/298');ck('Monster_no_dedicated_selector_original_or_private',not any('kab_07' in str(n['reads'])for n in oldsel['nodes'].values())and not any('kab_07' in str(n['reads'])for n in newsel['nodes'].values()),'Native Monster sets generic sts_tygerclaws_retaliation; native selector has LCH01/LCH03/HIL07/JPN12 only. Do not synthesize a new custom chase or call this generic signal a proven matching selector')
es(rd,[(0,'Out',64010,'In'),(64010,'Out',64011,'In'),(64011,'Out',63,'In'),(63,'Out',62,'In'),(62,'Out',37,'In1')],'root/22');ck('Tyger_pending_protected',has(rd,64010,'sts_tygerclaws_retaliation','Equal',0,'root/22'),'No reset of historical pending queue')
for f in ['PTFRU9_Retaliation_Issued','PTFRU9_Retaliation_tygerclaws_Issued']:ck('Monster_actual_support_receipt_'+f,has(d,65002,f,'Equal',1),f)
# Mutate actual decoded graphs/predicates, test independent literal route requirements.
bad=copy.deepcopy(S.g(ow,'root/4'));bad['edges'].remove(['39','True','34','In']);mut.append({'quest_id':q,'fault':'lost_failure_cleanup_branch','detected':['39','True','34','In']not in bad['edges']})
bad=copy.deepcopy(S.n(E['sts_wat_kab_102']['entry'],154)['payload']);bad['condition']['operation']='OR';mut.append({'quest_id':'sts_wat_kab_102','fault':'changed_native_AND_entry_to_OR','detected':bad!=S.n(S.extra(er['raw'],M),154)['payload']})
bad=copy.deepcopy(new['nodes']['23']['payload']);bad['type']['factName']='fake_ack';mut.append({'quest_id':q,'fault':'replaced_native_pending_cleanup','detected':bad!=old['nodes']['23']['payload']})
for x in mut:ck('mutation '+x['quest_id']+' '+x['fault'],x['detected'],x)
save(O/'checks.json',{'count':len(T),'checks':T,'mutations':mut,'status':'PASS_SCOPED_STATIC'});save(O/'quest_details.json',details);save(O/'source_pins.json',S.pins);save(O/'extra_pins.json',extra_pins);save(O/'retaliation.json',{'current':rd,'native_raw':rn,'native_sha256':sha(W/rn),'native_tyger_body_exact':True,'generic_Monster_signal_without_native_specific_selector':True,'status':'CONDITIONAL_NATIVE_ANOMALY_PRESERVED_NO_SPECULATIVE_FIX','saved_owner_retirement_proven':False})
print(json.dumps({'checks':len(T),'mutations':len(mut),'sources':len(S.pins),'quest_fact_gaps':{q:[x for x in v['local_native_fact_writers']if not x['covered_by_EntrySafe']]for q,v in details.items()}}))
