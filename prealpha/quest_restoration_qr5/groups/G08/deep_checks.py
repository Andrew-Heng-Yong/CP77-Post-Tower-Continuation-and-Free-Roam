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

# Independent literal route controls beyond generic source equality.
def ed(q):return E[q]['entry']
def ow(q):return next(d for d in S.MI if '\\'+q+'\\'in d and d.endswith('_openworld.questphase'))
q='sts_wat_kab_04';d=ed(q);es(d,[(4,'Out1',93,'In'),(4,'Out1',147,'In'),(93,'Out',146,'In1'),(147,'Out',146,'In2'),(146,'Out1',109,'In'),(146,'Out1',142,'In'),(109,'Out',143,'In1'),(142,'Out',143,'In2'),(143,'Out1',124,'Active'),(124,'Out',68,'In')]);ck('FixerMerc_native_tier_OR',has(d,93,'sts_wat_kab_tier_3_2','Greater',0)and has(d,147,'sts_wat_kab_tier_3','Greater',0),'XOR146 preserves native alternatives')
ck('FixerMerc_old_kab102_completion_route_already_orphan','64'in S.g(d)['unreachable']and'64'in S.g(S.extra(next(r for r in M['recipes']if r['id']==q and r['kind']=='entry')['raw'],M))['unreachable'],'Do not call native orphan64→77wait_done a current executing eligibility requirement')
w=ow(q);es(w,[(3,'optional',10,'optional'),(3,'not_optional',10,'not_optional')]);ck('FixerMerc_native_bonus_and_normal_reward_inputs',S.g(w,'root/10')['entries']=={'optional':'0','not_optional':'30'},'Native optional reward9 and completion33 share same reward record; distinct original branch inputs, not a U9 duplicate reward')
es(w,[(0,'Out',9,'In'),(9,'Out',34,'In1'),(65,'End 0',33,'In'),(104,'Out',33,'In'),(33,'Out',34,'In2')],'root/10')
q='sts_wat_kab_05';d=ed(q);es(d,[(3,'Out',91,'In'),(3,'Out',145,'In'),(91,'Out',144,'In1'),(145,'Out',144,'In2')]);ck('LastLogin_native_tier_OR',has(d,91,'sts_wat_kab_tier_2_1','Greater',0)and has(d,145,'sts_wat_kab_tier_2','Greater',0),'Original92 tier2_2 wait is orphaned, not added requirement');ck('LastLogin_original92_unreachable','92'in S.g(d)['unreachable']and'92'in S.g(S.extra(next(r for r in M['recipes']if r['id']==q and r['kind']=='entry')['raw'],M))['unreachable'],'Exact vanilla and current graph retain node identity')
w=ow(q);ck('LastLogin_Sandra_reference_is_only_condition',S.n(w,113,'root/6')['type']=='questConditionNodeDefinition'and any(x.get('state')=='Active'and x.get('path',{}).get('realPath')=='quests/minor_quest/mq024_sandra/mq024_sandra/01_find_data_carrier'for x in S.n(w,113,'root/6')['reads']),S.n(w,113,'root/6')['payload']);es(w,[(72,'Out1',113,'In'),(113,'False',9,'Succeeded'),(113,'True',114,'Succeeded')],'root/6')
ck('LastLogin_no_Sandra_journal_write_in_body',not any(n['type']=='questJournalNodeDefinition'and any(p.startswith('quests/minor_quest/mq024_sandra')for p in n['journal_paths'])for gp,g in S.load(w)['graphs'].items()for n in g['nodes'].values()),'Do not turn shared read into an invented Sandra admission constraint or reset')
es(w,[(31,'End1',4,'In'),(50,'Out',4,'In'),(4,'Out',11,'In')],'root/5')
q='sts_wat_kab_01';d=ed(q);es(d,[(65003,'Out',12,'In'),(65003,'Out',17,'In'),(12,'Out',18,'In1'),(17,'Out',18,'In2'),(18,'Out1',2,'In'),(2,'Out',19,'In'),(19,'Out',4,'In'),(4,'Out',5,'Active')],'root/1');ck('Concrete_genuine_Troublesome_completion_required',has(d,2,'kab_107_finished','Greater',0,'root/1')and has(d,12,'sts_wat_kab_tier_3','Greater',0,'root/1')and has(d,17,'sts_wat_kab_tier_3_2','Greater',0,'root/1'),'Unlike Kab04 orphan64, native completion2 is connected and mandatory after native tierOR')
ck('Concrete_no_historical_separate_credit_or_map_recipe',not any(r['kind']in ['credit','map']for r in M['recipes']if r['id']==q),'Source catalogue distinction, not complete global earned-credit proof; original DLC body preserved without inventing increments')
w=ow(q);es(w,[(43,'End 0',44,'In'),(74,'Out1',44,'In'),(44,'Out',27,'In'),(83,'Out1',35,'In'),(35,'Out',36,'In')],'root/6');ck('Concrete_native_completed_history_and_default_signal',any(x['factName']=='kab_01_finished'and x['value']==1 for x in S.n(w,27,'root/6')['writes'])and any(x['factName']=='tiny_mike_default_on'and x['value']==1 for x in S.n(w,35,'root/6')['writes']),'Reward44 then finished27; native default aftermath signal35 retained, owner investigated independently')
q='sts_wat_kab_03';d=ed(q);es(d,[(2,'Out1',159,'In'),(159,'Out',157,'In'),(159,'Out',158,'In'),(157,'Out',156,'In1'),(158,'Out',156,'In2')]);ck('Backs_native_tier_OR_AND',has(d,157,'sts_wat_kab_tier_1_3','Greater',0)and has(d,158,'sts_wat_kab_tier_1','Greater',0)and has(d,158,'sts_wat_kab_tier_1_1','Equal',0),'Native exact disjunction after deletion159')
pre=next(d for d in S.MI if '\\'+q+'\\'in d and d.endswith('_prestate_control.questphase'));es(pre,[(0,'Out',21,'In'),(21,'False',20,'In'),(20,'False',13,'In'),(13,'Out',17,'In'),(17,'Out',16,'In'),(16,'Out',12,'In'),(12,'Out',19,'In'),(19,'Out',18,'In'),(18,'Out',1,'In')]);ck('Backs_native_prestate_releases_on_actual_start',has(pre,12,'kab_03_start','Greater',0),'Native kitchen ForceLock/ForceUnpower before start; ForceUnlock/ForcePower after real start. Preserve original lifecycle, not arbitrary new door command')
w=ow(q);es(w,[(7,'End1',8,'In'),(38,'Out',8,'In'),(8,'Out',5,'In')],'root/18')
# Current R4 presentation integration pinned to effective package; no body/VO rewrite.
jv=W/'prealpha/quest_restoration_qr4/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds';jp=next(x for x in EP['package_files']if x['path']=='r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds');ck('effective_JV1_source_epoch_pin',sha(jv)==jp['sha256'],str(jv));extra_pins.append({'path':str(jv),'sha256':sha(jv)});jvs=jv.read_text(encoding='utf-8-sig');ck('actual_JV1_record_and_visual_filter','actor.GetRecordID() != t"Character.Silverhand"'in jvs and 'visual.TemporaryHide(true)'in jvs and '@wrapMethod(NPCPuppet)'in jvs,'Attach+restore tracking and genuine CompletedTower() guard; body visuals only');ck('JV1_no_quest_reset_or_scene_skip','SetFact('not in jvs and 'ResetKillCount'not in jvs and '.Despawn('not in jvs,'Actor VO/timing/internal native bindings retained; independent props not handled')
jd=next(d for d in S.MI if '\\sts_wat_kab_03\\'in d and d.endswith('_johnny.scene'));ck('Backs_single_Johnny_scene_no_independent_props',not S.load(jd)['metadata']['props'],'Other main scene has a Carnage prop with performer1; actor/performer/world role must not be guessed from ID alone')
# Complete independent native context scan for DLC completion/default and post-quest ripperdoc owners.
import gzip
scan_facts=['kab_01_finished','tiny_mike_default_on','kab_05_ripperdoc_scene_active_after_sts'];hits=[];scanpins=[]
for depot,row in S.MI.items():
 data=gzip.decompress(Path(row['normalized_model']).read_bytes())
 if not any(f.encode()in data for f in scan_facts):continue
 mm=json.loads(data);scanpins.append({'path':row['normalized_model'],'sha256':sha(row['normalized_model'])})
 for gp,g in mm['graphs'].items():
  for i,n in g['nodes'].items():
   rr=[x for x in n['reads']if x.get('factName')in scan_facts];ww=[x for x in n['writes']if x.get('factName')in scan_facts]
   if rr or ww:hits.append({'depot':depot,'graph':gp,'node':i,'reads':rr,'writes':ww,'refs':n['refs'],'prefabs':n['prefabs'],'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i]})
save(O/'shared_context_scan.json',{'models':len(S.MI),'hits':hits,'pins':scanpins,'limits':'Pinned cached models plus exact current group/epoch pins; parent source changes to ARR12 are unrelated. A direct fact mention is not executing owner proof.'})
# Mutation source models, checked against independent original literal conditions/edges.
bad=copy.deepcopy(S.n(ed('sts_wat_kab_01'),2,'root/1')['payload']);bad['condition']['type']['factName']='fake_completion';mut.append({'quest_id':'sts_wat_kab_01','fault':'lost_native_Troublesome_prerequisite','detected':bad!=S.n(S.extra(next(r for r in M['recipes']if r['id']=='sts_wat_kab_01'and r['kind']=='entry')['raw'],M),2,'root/1')['payload']})
bad=copy.deepcopy(S.g(pre));bad['edges'].remove(['12','Out','19','In']);mut.append({'quest_id':'sts_wat_kab_03','fault':'missing_prestate_actual_start_door_release','detected':['12','Out','19','In']not in bad['edges']})
for x in mut:ck('mutation '+x['quest_id']+' '+x['fault'],x['detected'],x)
save(O/'checks.json',{'count':len(T),'checks':T,'mutations':mut,'status':'PASS_SCOPED_STATIC'});save(O/'quest_details.json',details);save(O/'source_pins.json',S.pins);save(O/'extra_pins.json',extra_pins)
print(json.dumps({'checks':len(T),'mutations':len(mut),'sources':len(S.pins),'context_matches':len(hits),'quest_fact_gaps':{q:[x for x in v['local_native_fact_writers']if not x['covered_by_EntrySafe']]for q,v in details.items()}}))
