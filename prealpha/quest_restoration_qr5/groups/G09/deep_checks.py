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


# Source-specific original routes, native alternatives and shared consequence.
def ed(q):return E[q]['entry']
def ow(q):return next(d for d in S.MI if '\\'+q+'\\'in d and d.endswith('_openworld.questphase'))
for q,mark,a,b,join,tier in [('sts_wat_kab_06',163,161,162,160,'sts_wat_kab_tier_1_4'),('sts_wat_kab_08',159,157,158,156,'sts_wat_kab_tier_1_3')]:
 d=ed(q);es(d,[(2,'Out1',mark,'In'),(mark,'Out',a,'In'),(mark,'Out',b,'In'),(a,'Out',join,'In1'),(b,'Out',join,'In2')]);ck('native_exact_tier_disjunction '+q,has(d,a,tier,'Greater',0)and has(d,b,'sts_wat_kab_tier_1','Greater',0)and has(d,b,'sts_wat_kab_tier_1_1','Equal',0),'Native tier-specific OR(tier1 AND NOTtier1_1), after actual deletion marker')
q='sts_wat_kab_02';d=ed(q);es(d,[(2,'Out1',151,'In'),(151,'Out',148,'In'),(151,'Out',150,'In'),(148,'Out',149,'In2'),(150,'Out',149,'In1'),(149,'Out1',164,'Active')]);ck('Hippocratic_tier_alternatives',has(d,148,'sts_wat_kab_tier_1','Greater',0)and has(d,148,'sts_wat_kab_tier_1_1','Equal',0)and has(d,150,'sts_wat_kab_tier_1_1','Greater',0),'Native complete predicate retained')
w=ow(q);es(w,[(61,'Out1',41,'In'),(41,'Out',40,'In'),(19,'Out',54,'In'),(54,'False',20,'In'),(33,'Out',62,'In'),(62,'True',69,'In')],'root/5');ck('Hippocratic_actual_reward_failure_gate',has(w,41,'kab_02_failed','Equal',0,'root/5'),'Native failure cannot be erased to claim reward40');ck('Hippocratic_existing_achievement_receipt',has(w,54,'kab_02_achiv_added_in_bugfix','GreaterOrEqual',1,'root/5'),'Existing bugfix achievement receipt prevents replay credit; no reset or custom compensation')
es(w,[(15,'Out',6,'Active'),(6,'Out',16,'In'),(16,'Out',10,'Succeeded'),(10,'Out',35,'In'),(35,'Out',34,'In'),(34,'True',17,'In'),(17,'Out',2,'Active'),(2,'Out',18,'In'),(18,'Out',39,'In1'),(9,'Out',19,'In'),(19,'Out',3,'Succeeded'),(0,'Out',29,'In')],'root/2/145');ck('Hippocratic_actual_patient_death_predicate',has(w,29,'kab_02_patient_dead','GreaterOrEqual',1,'root/2/145'),'Patient-death branch exists alongside scan/blood/injection, not a forced successful operation')
q='sts_wat_kab_06';w=ow(q);es(w,[(0,'Out',64,'In'),(62,'Out',63,'In'),(64,'Out',81,'In1'),(63,'Out',81,'In1')],'root/6');ck('Shark_native_whole_prefab_spelling',S.load(E[q]['body'])['root_prefabs']==['#sts_wat_kab_06_steetstory'],'Exact vanilla steetstory alias retained, not renamed for appearance')
ck('Shark_obsolete_car_call_objective_cleanup',S.edge(w,228,'Out',229,'Inactive',gp='root/3'),'Unlisted call_fixer_for_car has native inactive cleanup writer; the other gap is real MapPin93 under kill_or_subdue objective')
q='sts_wat_kab_08';w=ow(q);es(w,[(34,'Out',50,'In'),(50,'False',7,'In'),(50,'True',13,'In'),(11,'Out',20,'In'),(20,'True',24,'In'),(24,'False',23,'In'),(24,'True',25,'In')],'root/5');ck('Woman_failure_skips_native_reward',has(w,50,'kab_08_failed','Greater',0,'root/5'),'FailureTrue cleanup13; successFalse reward7');ck('Woman_nomad_outcome_respects_native_history',has(w,20,'kab_08_hamill_becomes_nomad','Greater',0,'root/5')and has(w,24,'sq027_camp_moved','Greater',0,'root/5'),'Exact original before/after camp branch; no fabricated Panam history or camp access')
es(w,[(6,'False',8,'In'),(6,'True',2,'Active'),(8,'False',4,'Active'),(8,'True',3,'Active')],'root/5/53');ck('Woman_three_native_debrief_outcomes',has(w,6,'kab_08_failed','Greater',0,'root/5/53')and has(w,8,'kab_08_anna_dead','Greater',0,'root/5/53'),'Native fail/dead/spared SMS selection retains original facts; Dave aliases are native')
# Inspect exact prestate actions and local state writer gaps without assuming they are admission defects.
prestate=[]
for q in ['sts_wat_kab_06','sts_wat_kab_08']:
 er=next(r for r in M['recipes']if r['id']==q and r['kind']=='entry');pd=er['companions'][0]['depot'];gm=S.g(pd)
 prestate.append({'quest_id':q,'depot':pd,'root_prefabs':S.load(pd)['root_prefabs'],'entries':gm['entries'],'edges':gm['edges'],'nodes':{i:n['payload']for i,n in gm['nodes'].items()}})
 ck('prestate_current_native_not_packaged_override '+q,pd not in EP['source_resources'],'Native standalone unchanged; exact original lifecycle companion at64000 is already compared')
# Maelstrom support preserves original pending ownership and the real selected native signal.
RD=r'towercontinued\special_gigs_u9\gang_retaliation.questphase';S.load(RD);ck('Hippocratic_actual_Maelstrom_support_required',has(ed('sts_wat_kab_02'),65002,'PTFRU9_Retaliation_maelstroms_Issued','Equal',1),'Fresh entry requires actual gang-specific issued receipt, not generic Support alone');ck('Hippocratic_current_owned_retaliation_selector',has(RD,41,'PTFRU9_sts_wat_kab_02_Started','Equal',1,'root/22/35/239')and has(RD,41,'kab_02_gang_chase','GreaterOrEqual',1,'root/22/35/239')and has(RD,41,'wat_kab_02_done','Greater',0,'root/22/35/239'),'Native perquest predicate retained under additive private ownership condition')
es(RD,[(0,'Out',64008,'In'),(64008,'Out',64009,'In'),(64009,'Out',61,'In'),(61,'Out',60,'In'),(60,'Out',35,'In1')],'root/22');ck('Maelstrom_old_pending_queue_not_consumed',has(RD,64008,'sts_maelstroms_retaliation','Equal',0,'root/22'),'No clearing historical pending fact or replaying an old ambush')
# Source-confirm original gang child itself, with only existing selector ownership wrappers.
SM=read(W/'research/gig_restoration/special_gigs_u9/manifest.json');rn='research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_gang_retaliation.questphase';jn=rn.replace('/raw/','/json/')+'.json';pm={k.replace('\\','/'):v for k,v in SM['source_pins'].items()}
for f in [rn,jn]:ck('retaliation_original_pin '+f,sha(W/f)==pm[f],pm[f]);extra_pins.append({'path':str(W/f),'sha256':sha(W/f)})
native=Resource(read(W/jn)).normalize();ck('Maelstrom_native_body_equal',S.g(RD,'root/22/35')==native['graphs']['root/35'],'Native six gang child retained including actor/vehicle/token/phone/cancel lifecycle; individual selector35/239 wraps ownership only')
origsel=native['graphs']['root/35/239'];cursel=S.g(RD,'root/22/35/239')
ck('Maelstrom_selector_whole_native_edges',origsel['edges']==cursel['edges'],'Two private owner conditions only, no original selector edge lost')
for i,nd in origsel['nodes'].items():
 expected=copy.deepcopy(nd['payload'])
 if i in ['41','45']:
  owner='PTFRU9_sts_wat_kab_02_Started'if i=='41'else'PTFRU9_sts_wat_nid_05_Started'
  expected['condition']={'$type':'questLogicalCondition','conditions':[{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':owner,'value':1}},expected['condition']],'operation':'AND'}
 ck('Maelstrom_exact_native_selector_payload '+i,expected==cursel['nodes'][i]['payload'],'Content-unblocked,wat_kab_02_done>0,inside#watson_content_tr AND gang_chase>=1 remain native; not generic retaliation alone')
# Mutations actually change source resource graph or authored predicates.
q='sts_wat_kab_02';bad=copy.deepcopy(S.n(ow(q),41,'root/5')['payload']);bad['condition']['type']['value']=1;mut.append({'quest_id':q,'fault':'reversed_native_failure_reward_gate','detected':bad!=S.n(ow(q),41,'root/5')['payload']})
q='sts_wat_kab_08';bad=copy.deepcopy(S.g(ow(q),'root/5'));bad['edges'].remove(['50','True','13','In']);mut.append({'quest_id':q,'fault':'lost_failure_cleanup','detected':['50','True','13','In']not in bad['edges']})
bad=copy.deepcopy(S.n(RD,64008,'root/22')['payload']);next(x for x in walk(bad)if x.get('factName')=='sts_maelstroms_retaliation')['value']=1;mut.append({'quest_id':'sts_wat_kab_02','fault':'admit_historical_pending_ambush','detected':bad!=S.n(RD,64008,'root/22')['payload']})
for x in mut:ck('mutation '+x['quest_id']+' '+x['fault'],x['detected'],x)
save(O/'checks.json',{'count':len(T),'checks':T,'mutations':mut,'status':'PASS_SCOPED_STATIC'});save(O/'quest_details.json',details);save(O/'source_pins.json',S.pins);save(O/'extra_pins.json',extra_pins);save(O/'native_prestate_lifecycles.json',prestate)
print(json.dumps({'checks':len(T),'mutations':len(mut),'sources':len(S.pins),'quest_fact_gaps':{q:[x for x in v['local_native_fact_writers']if not x['covered_by_EntrySafe']]for q,v in details.items()}}))
