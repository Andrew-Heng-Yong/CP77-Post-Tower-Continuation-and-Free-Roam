"""Update the exact targeted findings; retain the complete prior investigation grid."""
from pathlib import Path
import sys,copy,json,csv,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr7'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not(O/'contract_status_matrix.json').exists()
def pin(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p)}
def csvout(path,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with Path(path).open('w',encoding='utf-8',newline='')as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(dict,list))else v for k,v in r.items()})
e=read(O/'source_epoch_02.json');q=read(O/'queue.json');baseq=read(P/'queue.json');by={r['id']:r for r in q['quests']};oldby={r['id']:r for r in baseq['quests']};updates=[]
bp=O/'worker_b/contract_addendum.json';cp=O/'worker_c/findings_03/contract_updates.json';scopep=O/'worker_c/reviews/enrollment_02/parent_scope_recommendations.json';scopes={(r['quest_id'],r['stage']):r for r in read(scopep)}
for source in [bp,cp]:
 for w in read(source):
  quest,stage=w['quest_id'],w['stage'];old=copy.deepcopy(oldby[quest]['contracts'][stage]);body=copy.deepcopy(w)if source==cp else copy.deepcopy(old)
  body.pop('quest_id',None);body.pop('title',None);body.pop('stage',None)
  status=w.get('recommended_status',w.get('status'));assert status==old['status']
  body.update(status=status,effective_source_epoch='QR8:02',source_epoch_manifest=str(O/'source_epoch_02.json'),source_epoch_sha256=sha(O/'source_epoch_02.json'),prior_QR7_contract=old,QR8_worker_finding={'source':pin(source),'record':w})
  body['evidence']=list(body.get('evidence',[]))+[pin(source),pin(O/'source_epoch_02.json'),pin(O/'candidate_01/package_manifest.json')]
  if source==cp:
   peer=O/'worker_a/reviews/C_five_01/review.json';body['QR8_independent_review']=pin(peer)
   body['evidence'] += [pin(peer),pin(O/'worker_c/reviews/acceptance_03/five_contract_applicability.json')]
   body['QR8_supersession']='Current Voodoo context170 is ContainerManager; QR7 candidate TransactionSystem258 chain is retained only as historical incomplete evidence. Current Cuckoo numeric predicate semantics do not require stock-definition existence at the observed dispatch boundary.'
  elif quest=='sts_pac_cvi_02':
   body['proven']=list(body.get('proven',[]))+w['proven'];body['remaining']=w['remaining'];body['QR8_scope']=w['scope'];body['evidence']+=w['evidence'];body['QR8_no_resume_adapter']='Old entered/request/outcome/saved-controller states remain deferred; no source change to67EE resource.'
  else:
   body['proven']=[s for s in body.get('proven',[])if not s.startswith('Private branch gate checks native done0/sent0')]
   body['proven'] += ['CURRENT QR8:02 root/202 first-case gates200–203 retain sent0 and(ParentEntered0 OR actualArmed1), replacing only done0 with(done0 OR own genuine QR7 Armed1). Original real arm wait and native done>=1 listener remain unchanged.','Actual U9 admission dominates65007 Armed1 before65003 ParentEntered, then the native quest/completion owner. There is no authored dependency requiring NEWS220 to load first; completion can precede first case evaluation while the helper waits. This is source partial-order proof, not a measured latency/save fixture.','Native sent1 dominates the unchanged two-game-day timer; sent0 plus actual future provenance is not adoption of a previously sent clock. Entire root, edges/sockets/PIPs/IDs and73 native protocol nodes remain unchanged. No re-entry edge or root rearm is added.']
   body['approved_differences']=list(body.get('approved_differences',[]))+['QR8-RONALD-LATE-FUTURE-FIRST-EVALUATION: source-confirmed first-evaluation extension only. It can apply to an existing Issued1 helper before the gate without restarting its root.']
   body['remaining']=['FAIL_SUBROUTE: first-time enrollment/menu/physical-owner extension is held. B0 is an intentionally narrow S4 service prototype with native839 options3/4 hidden/disconnected and no explicit original bar prefab lease; it is not a newly broken QR7 news path. Persistent workspot data and possible existing save owners prevent an actor-absence claim.','BLOCKED_HISTORY: old ParentEntered1/Armed0 and native sent1/pending/delivered clocks are not adopted, reset or reclocked. Genuine existing enrollment and Active contact are still required.','PROCESSED_STAGE_BOUNDARY: no explicit re-entry/replay path is added for skipped/processed cases. The intended supported stage is before first gate evaluation; exact saved-handler predicate refresh and old processed-state persistence need transition fixtures.','LIVE_ONLY: actual hook/owner dispatch, private trigger loading/lease/occupancy, queue ordering, native delay/SMS/callback, interruption and cold reload remain unexecuted.','NAMESPACE_BOUNDARY: expanded archive/XL/Bundle/provider checks are bounded. No full external world-global or arbitrary different-parent/named-fact census is claimed.']
   body['failed_subroutes']=w.get('failed_subroutes',[]);body['QR8_enrollment_scope_review']=scopes[(quest,stage)];body['QR8_independent_review']=pin(O/'worker_c/reviews/late_future_02/review.json')
   body['evidence'] += w['evidence']+[pin(O/'worker_c/reviews/late_future_02/review.json'),pin(O/'worker_c/reviews/enrollment_02/review.json'),pin(O/'worker_b/reviews/promoted_source/verification_01/review.json'),pin(O/'worker_a/final_package_01/verification/result.json')]
   body['QR8_supported_late_future_stage']='Genuine Armed1/native sent0, before first corresponding case evaluation. Existing Issued1 at220 is allowed; no root restart or old clock is introduced.'
  by[quest]['contracts'][stage]=body;updates.append({'quest_id':quest,'title':by[quest]['title'],'stage':stage,**body})
assert len(updates)==18 and len({(r['quest_id'],r['stage'])for r in updates})==len(updates)
keys={(r['quest_id'],r['stage'])for r in updates};affected={'sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12'}
for quest in affected:
 for stage,c in by[quest]['contracts'].items():
  c['QR8_shared_news_applicability']={'epoch':'QR8:02','changed_resource':e['changes'][0]['depot'],'before':e['changes'][0]['before'],'after':e['changes'][0]['after'],'scope':'Only four shared NEWS first-evaluation predicates changed. This quest main/U9/scene/SMS/reward resources and all old ownership identities are byte-identical toQR7.','status_promoted':False,'exact_native_and_source_proof':pin(O/'worker_c/reviews/late_future_02/review.json')}
  assert c['status']==oldby[quest]['contracts'][stage]['status']
for r in q['quests']:
 if any(k[0]==r['id']for k in keys):r['QR8_updated_contracts']=[k[1]for k in sorted(keys)if k[0]==r['id']]
 else:assert r==oldby[r['id']],r['id']
matrix=[{'quest_id':r['id'],'title':r['title'],'stage':s,**v}for r in q['quests']for s,v in r['contracts'].items()]
oldmatrix=read(P/'contract_status_matrix.json');old={(r['quest_id'],r['stage']):r for r in oldmatrix}
comparison=[{'quest_id':r['quest_id'],'title':r['title'],'stage':r['stage'],'original_status':old[(r['quest_id'],r['stage'])]['status'],'final_status':r['status'],'QR8_targeted_update':(r['quest_id'],r['stage'])in keys,'source_or_scope_addendum':('QR8_shared_news_applicability'in r),'first_enrollment_subroute_FAIL':(r['quest_id'],r['stage'])in scopes,'original_matrix':str(P/'contract_status_matrix.json'),'original_matrix_sha256':sha(P/'contract_status_matrix.json'),'final_epoch':'QR8:02'}for r in matrix]
q.update(QR8_status='TARGETED_FINDINGS_AND_FINAL_PACKAGE_FROZEN_READINESS_REVIEW_PENDING',QR8_targeted_contract_updates=len(updates),QR8_new_deep_audits=0,QR8_new_confirmed_late_future_defects=1,QR8_new_staged_repairs=1,QR8_held_scope_extensions=['Ronald first-enrollment/contact/physical-owner'],cumulative_staged_repairs=12,current_compile=str(O/'verification/compile_successor_01/result.json'),independent_package_review=pin(O/'worker_a/final_package_01/verification/result.json'),QR8_partial_order_and_live_boundary='One source-proven first-evaluation defect corrected; no runtime completion/predicate-refresh or all-save claim.')
write(O/'queue.json',q);write(O/'targeted_contract_updates.json',updates);csvout(O/'targeted_contract_updates.csv',updates);write(O/'contract_status_matrix.json',matrix);csvout(O/'contract_status_matrix.csv',matrix);write(O/'quest_status_matrix.json',q['quests']);csvout(O/'quest_status_matrix.csv',q['quests']);write(O/'contract_comparison.json',comparison);csvout(O/'contract_comparison.csv',comparison)
counts=dict(collections.Counter(r['status']for r in matrix));fully=[r['id']for r in q['quests']if all(v['status']in['PASS','APPROVED_DEVIATION']for v in r['contracts'].values())];assert not fully
coverage={'status':'TARGETED_INTEGRATION_AND_REVIEW_SOURCE_COVERAGE_WITH_EXPLICIT_LIMITS','selected':len(q['quests']),'retained_deep_investigations':len(q['quests']),'new_census_or_broad_deep_audits':0,'contracts':len(matrix),'targeted_contract_updates':len(updates),'original_status_counts':dict(collections.Counter(r['status']for r in oldmatrix)),'final_status_counts':counts,'status_changes':sum(r['original_status']!=r['final_status']for r in comparison),'fully_static_verified_quests':len(fully),'remaining_original_target_UNKNOWN':[{'quest_id':r['quest_id'],'stage':r['stage']}for r in matrix if r['status']=='UNKNOWN'],'failed_first_enrollment_subroutes':len(scopes),'failed_first_enrollment_unique_scope_families':1,'scope_rule':'The eight parent records are CONDITIONAL strictly for genuine existing-contact prospective news. First-enrollment/menu/physical-owner subroutes are explicitly FAIL/held; zero parent FAIL is not zero known scope gaps.','engine_binary_correspondence':'SOURCE_CONFIRMED_INSPECTED_METHODS_IN_INSTALLED_DLL_INDEPENDENTLY_REVIEWED','engine_binary_review':pin(O/'worker_b/reviews/A_integration/verification_01/review.json'),'remaining_engine_boundaries':'Actual address resolution/hook installation, native dispatch success, receipt/save serialization, PIP leases and saved condition refresh remain LIVE_ONLY; receipt is attempt bookkeeping, not ACK.','epoch':pin(O/'source_epoch_02.json'),'queue_sha256':sha(O/'queue.json')}
write(O/'coverage.json',coverage)
print({'status':'PUBLISHED18TARGETED_UPDATES_COMPLETE1610GRID','counts':counts,'changed_statuses':coverage['status_changes'],'explicit_failed_subroutes':len(scopes),'fully_static_verified':0})
