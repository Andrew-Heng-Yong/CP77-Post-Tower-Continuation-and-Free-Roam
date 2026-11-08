"""Coordinator adjudication; preserve epoch00 findings and publish epoch02 matrix."""
from pathlib import Path
import sys,copy,collections,datetime
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
assert not (O/'checkpoint.json').exists(),'Preserve final adjudication'
p=read(O/'progress.json');q=read(O/'queue.json');rows=read(O/'contract_status_matrix.json')
assert all(g['status']=='REVIEWED_WITH_LIMITS' for g in p['groups'].values())
new_ids={i for g in p['groups'].values() for i in g['ids']};prior=read(W/'prealpha/quest_restoration_qr3/queue.json')
assert len(new_ids)==len(p['completed_quests']) and not new_ids&set(prior['deep_reviewed_ids'])
allow=read(O/'approved_changes_01.json');patch=O/'candidate_01/repair_mq007/patch.json';test=O/'candidate_01/repair_mq007/verification_01/tests.json';review=O/'groups/G10/reviews/MQ007_serialized/verification_01/review.json'
assert read(test)['status'].startswith('PASS') and read(review)['status'].startswith('APPROVED_SERIALIZED')
corrections=[];index=[]
for group,g in p['groups'].items():
 rr=Path(g['review']['path']);assert sha(rr)==g['review']['sha256'];rd=read(rr)
 assert rd['status'].startswith(('PASS','APPROVE','INDEPENDENT_SOURCE_REVIEW_ACCEPTS','NO_NEW_SOURCE_DEFECT','INDEPENDENT_REVIEW_CONFIRMS_ONE_EPOCH00_MISSING_POST_RETURN_CONSUMER')),rd['status']
 res=read(O/'groups'/group/'results.json');tt=res['tests'];tp=Path(tt['path'] if isinstance(tt,dict) else tt)
 if not tp.is_absolute():tp=O/'groups'/group/tp
 assert tp.is_file();checks=res.get('checks',tt.get('count',tt.get('checks')) if isinstance(tt,dict) else None);mut=res.get('mutations',tt.get('mutations') if isinstance(tt,dict) else None)
 index.append({'group':group,'quest_ids':g['ids'],'investigation':str(O/'groups'/group/'results.json'),'investigation_sha256':sha(O/'groups'/group/'results.json'),'tests':str(tp),'tests_sha256':sha(tp),'checks':checks,'mutations':mut,'review':str(rr),'review_sha256':sha(rr)})
 for pin in g['findings']:
  fp=Path(pin['contracts'])
  revision=None
  if sha(fp)!=pin['sha256']:
   rp=O/'groups/G12/revisions/stable_fences_01/revision.json';revision=read(rp)
   assert group=='G12' and pin['id']=='sts_hey_gle_06'
   assert sha(revision['prior_contract'])==revision['coordinator_recorded_prior_contract_sha256']==pin['sha256']
   assert all(sha(x['path'])==x['sha256'] for x in revision['current_frozen_files'])
   prior_doc=read(revision['prior_contract']);current_doc=read(fp)
   assert {k:v['status'] for k,v in prior_doc['contracts'].items()}=={k:v['status'] for k,v in current_doc['contracts'].items()}
   assert not revision['runtime_or_source_epoch_changed'] and not revision['defects_or_repairs_changed']
   pin['superseded_by']={'sha256':sha(fp),'revision':str(rp),'revision_sha256':sha(rp)}
   corrections.append({'quest_id':pin['id'],'change':'Post-completion evidence refinement explicitly supersedes prior hash; reconstructed prior matches original SHA. Status/runtime inputs unchanged.','revision':str(rp)})
  d=read(fp);assert set(d['contracts'])=={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
  item=next(x for x in q['quests'] if x['id']==pin['id']);cs=copy.deepcopy(d['contracts'])
  for stage,v in cs.items():
   assert v.get('proven') and v.get('evidence');v['source_epoch_investigated']=0;v['effective_source_epoch']=2
   v['findings_source']=str(fp);v['findings_source_sha256']=sha(fp);v['independent_review']=str(rr);v['independent_review_sha256']=sha(rr)
   if group=='G02' and stage=='communications':
    v['original_proven']=copy.deepcopy(v['proven'])
    v['proven']=[s.replace('SupportIssued is claimed before fresh native body and mutually excluded from a second S22 fresh listener.','S25 node92.Out forks concurrently into body100.In1 and claim65020.In→listener94.In1; no strict listener-before-body order is proved. The owned claim excludes a second S22 fresh listener after it is written.') for s in v['proven']]
    v['remaining']=v.get('remaining',[])+['LIVE_ONLY: Native body and listener are parallel branches; queued request timing and scheduling are not established by static reachability.']
    v['evidence'] += [str(O/'groups/G06/G02_self_correction.json'),str(O/'groups/G05/reviews/G02.json')]
    corrections.append({'quest_id':pin['id'],'stage':stage,'change':'Supersede incorrect before-body prose with actual concurrent92fanout; preserve original findings.','evidence':v['evidence'][-2:]})
   if pin['id']=='mq007_smartgun' and v['status']=='FAIL':
    v['pre_repair_status']='FAIL';v['pre_repair_proven']=v['proven'];v['pre_repair_remaining']=v.get('remaining',[]);v['status']='CONDITIONAL'
    v['proven']=['The epoch00 missing native post-return consumer is repaired for future supported1101entry events in both wrappers. Exact native bugfix14/3 helper lease, done wait, five-day delay, outside-Regina/content gate, persistent-world variant, three messages and native receipt are retained.','Serialized successor adds only1200ANDguard→1201sharedclaim→1202nativecontinuation→1203ownedfinish and four edges. All old nodes, payloads, sockets, graph edges and saved IDs remain; prior admission/resume seam is untouched.']
    v['remaining']=['STATIC_SCOPE_LIMIT: Previously-entered or already-returned saves do not receive retroactive enrollment or reconstructed elapsed time. Their native timer/receipt/owner transition remains unsupported.','OPAQUE: World descriptor proves persistent container placement, but exact sector/loot contents fail the available DynamicBaseClass/worldNode decoder.','LIVE_ONLY: Engine scheduling, timer/reload persistence, helper teardown, world streaming, SMS display and pickup require gameplay verification.']
    v['approved_differences']=v.get('approved_differences',[])+[allow['resources'][0]['intent']]
    v['evidence'] += [str(patch),str(test),str(review),str(O/'groups/G08/regina_world_01/ownership.json')]
    v['repair']='QR4-MQ007-POSTRETURN';v['verified_resources']=[{'depot':r['depot'],'sha256':r['after']} for r in allow['resources']]
   assert v['status'] in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY']
  item.update({'contracts':cs,'status':'DEEP_REVIEWED_WITH_STATIC_LIMITS','fully_static_verified':all(v['status'] in ['PASS','APPROVED_DEVIATION'] for v in cs.values()),'source_epoch':2,'finding_source_epoch':0,'finding_sha256':sha(fp),'review':str(rr),'review_sha256':sha(rr)})
  if revision:item['explicit_finding_revision']=pin['superseded_by']
  if pin['id']=='mq007_smartgun':item['defects']=['QR4-MQ007-POSTRETURN'];item['repairs']=allow['resources']
  item['remaining']=[{'contract':k,'status':v['status'],'item':t} for k,v in cs.items() for t in v.get('remaining',[])]
# Cross-quest finding discovered by Q04; append to the retained Q01 finding.
mq=next(x for x in q['quests'] if x['id']=='mq044_jakes_vehicle');v=mq['contracts']['shared_dependencies'];v['status']='CONDITIONAL'
v['proven']+=['QR4 G12 traces original bugfix root11/9 initial started_in_main sample→LifeWork finished→one-day corrective MQ044_main route, versus normal minorquests148→150three-days→149wrapper. Current S23 preserves the normal route. Native main5 rejects Active/Succeeded and startup55 writes started1; S23 final1100 checks both started facts0, so two routes alone do not prove duplicate runtime owners.']
v['remaining']+=['CONDITIONAL: Exact native corrective versus normal timer/owner eligibility and saved context are unresolved. No speculative one-day override or additional owner was added.']
v['evidence'] += [str(O/'groups/G12/timing_review_01/evidence.json'),str(O/'groups/G11/reviews/G12.json'),str(O/'groups/G11/reviews/G12_admission_checks.json')]
for item in q['quests']:
 for row in rows:
  if row['quest_id']==item['id'] and (item['id'] in new_ids or item['id']=='mq044_jakes_vehicle'):
   v=item['contracts'][row['stage']];row.update(copy.deepcopy(v));row['quest_id']=item['id'];row['title']=item['title'];row['review_state']='REVIEWED_WITH_LIMITS';row['effective_source_epoch']=2
q['deep_reviewed_ids']=[x['id'] for x in q['quests'] if x['id'] in set(prior['deep_reviewed_ids'])|new_ids];q['deep_reviewed_count']=len(q['deep_reviewed_ids']);q['pending_review_ids']=[];q['new_investigated_count']=len(new_ids);q['static_verified_count']=sum(bool(x.get('fully_static_verified')) for x in q['quests']);q['completed_count']=q['static_verified_count'];q['working_candidate']=str(O/'candidate_01');q['installed_baseline']='PH3 unchanged';q['gameplay_repairs']=prior['gameplay_repairs']+1;q['new_unique_defects']=1;q['new_affected_quest_count']=1;q['changed_resources']=2;q['cumulative_changed_resources_vs_PH3']=4;q['source_epoch']=2
q['checkpoint_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert len(q['quests'])==q['selected_count'] and len(rows)==10*len(q['quests']);assert not q['static_verified_count']
write(O/'queue.json',q);write(O/'quest_status_matrix.json',q['quests']);write(O/'contract_status_matrix.json',rows)
for name,data in [('quest_status_matrix.csv',q['quests']),('contract_status_matrix.csv',rows)]:
 fields=list(dict.fromkeys(k for r in data for k in r));csvwrite(O/name,[{k:r.get(k) for k in fields} for r in data])
write(O/'group_evidence_index.json',{'scope':'Final48deepinvestigations; counts are assertion events, not independent gameplay coverage','groups':index,'investigation_checks':sum(i['checks'] for i in index),'investigation_mutations':sum(i['mutations'] for i in index)})
olddefs=read(W/'prealpha/quest_restoration_qr3/defects_and_repairs.json')
newdef={'id':'QR4-MQ007-POSTRETURN','affected':['mq007_smartgun'],'status':'REPAIRED_FOR_FUTURE_SUPPORTED_ENTRY_STATIC_VALIDATED_LIVE_PENDING','resources':allow['resources'],'source_fault':'Native return emitsmq007_done1 but sole nativebugfix14consumer is enclosed by genuineTower retirement. No private rehost existed.','before_after':str(test),'independent_review':str(review),'limitations':read(test)['limits']}
write(O/'defects_and_repairs.json',{'new_confirmed_unique_defects':1,'new_affected_quest_count':1,'new_changed_resources':2,'cumulative_confirmed_unique_defects':q['gameplay_repairs'],'cumulative_changed_resources_vs_PH3':4,'defects':olddefs['defects']+[newdef],'scope':'Source-confirmed structural fixes/containment, not gameplay certification'})
diffs=read(W/'prealpha/quest_restoration_qr3/intentional_differences.json')['differences']
for x in q['quests']:
 if x['id'] not in new_ids:continue
 for k,v in x['contracts'].items():
  for s in v.get('approved_differences',[]):diffs.append({'quest_id':x['id'],'contract':k,'difference':s,'evidence':v['evidence'],'findings_source_sha256':v['findings_source_sha256'],'source_epoch':2,'new_in_qr4':bool(v.get('repair'))})
write(O/'intentional_differences.json',{'version':1,'source_epoch':2,'differences':diffs,'approval_boundary':'Existing adaptations retain their pinned native/corrected-builder evidence and original limitations. Only MQ007 has new QR4 gameplay changes; prose is not blanket authorization.'})
write(O/'review_resolutions.json',{'status':'SOURCE_CORRECTIONS_INTEGRATED_STATIC_LIMITS_RETAINED','originals_preserved':True,'corrections':corrections,'items':[
 {'id':'S24_PHONE_RACE_REJECTED','resolution':'Actual Pause1003requiresissued1; earlier hypothesis skipped the barrier. No patch.','evidence':'groups/G03/verification_01/hypothesis_correction.json'},
 {'id':'G02_COUNTER_MUTATION','resolution':'Original normalized metadata mutation supplemented with actual rawSetVar mutation and renormalization.','evidence':'groups/G06/G02_self_correction.json'},
 {'id':'MQ007_OWNER_REFINEMENT','resolution':'Initial scope block resolved by exact persistent-world descriptors; nested helper lease retained despite empty outerprefabs. Sector content staysOPAQUE.','evidence':'groups/G10/reviews/MQ007_followup_addendum.json'},
 {'id':'FACTSDB_FIXTURE_BOUNDARY','resolution':'Original reviewer missing-any-fact rejection was conservative simulator policy. Root fixture uses absent scalar0; missing expected0 is accepted. Positive private receipts+futureevent are provenance boundary; no engine missing0 rejection claimed.','evidence':'candidate_01/repair_mq007/verification_01/tests.json'},
 {'id':'MQ044_TIMER','resolution':'One-day corrective and three-day normal routes distinguished; late normal/main guards retained. No proven duplicate runtime owners or guessed timer repair.','evidence':'groups/G11/reviews/G12.json'},
 {'id':'NATIVE_ODDITIES','resolution':'SerialSuicide selfrequest wait retained as native; Cole sibling-community disconnect pinned to prior approvedU9isolation. Neither is a new QR4 repair.','evidence':'groups/G10/reviews/G11.json'},
 {'id':'PROSE_PRECISION','resolution':'Kabuki loss53→65→54, BigRace sq024_05 socket prefix, vendor MR_STUD, End 0 socket, Embedded/Soft normalization and parallel retry ACK assumptions corrected against source. Original evidence retained.','evidence':'group_evidence_index.json'}]})
pending=[x for x in q['quests'] if x['id'] not in q['deep_reviewed_ids']];nextbatch=pending[0]['batch'];counts=collections.Counter(v['status'] for x in q['quests'] if x['id'] in new_ids for v in x['contracts'].values());allcounts=collections.Counter(v['status'] for x in q['quests'] if x['id'] in q['deep_reviewed_ids'] for v in x['contracts'].values())
write(O/'checkpoint.json',{'state':'Q02_Q03_Q04_ALL_DEEP_REVIEWED_WITH_STATIC_LIMITS','selected_quests':len(q['quests']),'newly_deep_reviewed':len(new_ids),'total_deep_reviewed':q['deep_reviewed_count'],'remaining_not_deep_reviewed':len(pending),'fully_static_verified':q['static_verified_count'],'new_contract_status_counts':dict(counts),'deep_contract_status_counts':dict(allcounts),'batch_counts':{b:sum(x['id'] in q['deep_reviewed_ids'] for x in q['quests'] if x['batch']==b) for b in sorted({x['batch'] for x in q['quests']})},'new_unique_defects':1,'new_affected_quest_count':1,'new_changed_resources':2,'cumulative_unique_defects':q['gameplay_repairs'],'working_candidate':q['working_candidate'],'installed':'PH3 unchanged','source_epoch':2,'queue_sha256':sha(O/'queue.json'),'next_batch':nextbatch,'next_batch_quests':[{'id':x['id'],'title':x['title']} for x in pending if x['batch']==nextbatch],'restrictions':'No game/deployment/save/fact/release/Git publication writes'})
p['status']='INVESTIGATIONS_REVIEWED_REPAIR_PACKAGED_FINAL_PROTECTION_AND_ADVERSARIAL_GATES_PENDING';p['repair_epochs'].append(str(O/'source_epoch_02.json'));p['new_defects'][0]['status']=newdef['status'];write(O/'progress.json',p)
print({'new':len(new_ids),'deep_total':q['deep_reviewed_count'],'remaining':len(pending),'new_contracts':dict(counts),'new_defects':1,'investigation_checks':sum(i['checks'] for i in index),'mutations':sum(i['mutations'] for i in index)})
