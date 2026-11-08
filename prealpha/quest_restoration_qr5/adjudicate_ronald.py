"""One native news family, independently mapped to all affected selected quests."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
out=O/'adjudications/ronald_01.json';assert not out.exists()
cp=O/'groups/G21/reviews/RONALD/verification_05/review.json';c=read(cp);assert c['status']=='SOURCE_CONFIRMED_ONE_SHARED_RONALD_DEFECT_FOUR_SELECTED_DEPENDENCIES_REPAIR_BLOCKED_PRECISELY'
ip=O/'shared/ronald_family_inventory_01.json';inv=read(ip);affected=set(inv['affected_selected_quests']);assert affected==set(c['selected_affected'])and not inv['unresolved_numeric_references']
family=read(c['family_map']);by={r['selected_quest_id']:r for r in family if r['in_selected_catalogue']};assert set(by)==affected
q=read(O/'queue.json');p=read(O/'progress.json');rows=read(O/'contract_status_matrix.json')
assert all(g['status']=='REVIEWED_WITH_LIMITS'for g in p['groups'].values()if affected&set(g['ids'])),'Apply only after frozen group reviews, avoiding reimport of baseline contracts'
bp=O/'groups/G20/ronald_verification_02/evidence.json';did='QR5-RONALD-POST-GIG-NEWS-OWNER';sources=[str(bp),str(cp),c['family_map'],str(ip),str(O/'reviews/worker_b/G21.json')];changes=[]
for item in q['quests']:
 if item['id']not in affected:continue
 route=by[item['id']]
 for stage in c['affected_contracts']:
  v=item['contracts'][stage];old=v['status'];v['pre_ronald_status']=old;v['pre_ronald_proven']=copy.deepcopy(v['proven'])
  v['proven']+=['Main native gig body, ordinary calls, actual real ACKs, cleanup and prior source-specific checks remain valid. This failure concerns the separate optional Ronald post-gig news dependency. In particular, Spy Mark/Ana phone and door source proofs are not contradicted.',f"Native q302_ronald_tree root/11 done-wait{route['done_wait']} reaches sent-writer{route['native_sent_writer']} ({route['native_sent_fact']}), native two-game-day delivery node{route['delivery_game_delay']} and original news child{route['phase_node']}. Exact preclaim real-time pauses, standalone/token/area gates, real reply/outcome/timeout and pause-release edges are pinned in the family map; no compact route omits their distinct units.",'Genuine pre-Tower q302_done/tree/messages_enabled positive enrollment, native sent0 and a new preserved gig done1 event give an explicit source counterexample. Original ending cut retires additional/persistent native Ronald owner; current B0 omits11/12, its old enrollment writer is unreachable, and indexed private owners/package scripts provide no replacement. Old service-only B0 scope is not an approved exception to selected-gig news parity.']
  v.update(status='FAIL',defect=did,repair_status='BLOCKED_EXACT_BAR_MARKER_LEASE_SHARED_PAUSE_AND_SAVED_TIMER_SCOPE',native_external_branch=route,effective_source_epoch='QR5:08')
  v['remaining']+=['CONFIRMED_BLOCKED_REPAIR: Native root owns #q302_pr_bar; controller11 and SMS children have no physical scene/PIP, but entry area_02_closer and delivery area_02 predicates need an exact host-marker lease. Current B0 outer/nested root has no such lease and pre-dispatch OwnerActive is not acquisition proof. No claim is made that placed markers are absent.','SAVED_TIMER_SCOPE: Sent1 precedes the two-game-day delay and may mean pending or delivered. A fresh-event/sent0/enrolled1 adapter might avoid old timers but still needs source-approved shared pause cancellation/rearm, five-way terminal AND and real response cleanup isolation. No reset, fake sent/enrollment, whole11/fluff replay or unfiltered bar/root import approved.']
  v['evidence']+=sources;v['central_adjudication']=str(out)
  for row in rows:
   if row['quest_id']==item['id']and row['stage']==stage:row.update(copy.deepcopy(v))
  changes.append({'quest_id':item['id'],'stage':stage,'before':old,'after':'FAIL','shared_defect':did})
 item.setdefault('defects',[]).append(did);item.setdefault('central_addenda',[]).append({'path':str(out),'review_sha256':sha(cp)})
d=read(O/'defects_and_repairs.json');assert not any(x['id']==did for x in d['defects']);write(O/'defects_and_repairs_before_ronald_02.json',d)
entry={'id':did,'affected':sorted(affected),'status':'CONFIRMED_REPAIR_BLOCKED_EXACT_BAR_MARKER_LEASE_SHARED_QUEUE_AND_SAVED_TIMER_SCOPE','resources':[],'evidence':sources,'independent_context_review':str(cp),'independent_context_review_sha256':sha(cp),'family_inventory':str(ip),'family_inventory_sha256':sha(ip),'adjudication':str(out),'blockers':c['blockers'],'original_service_scope_is_not_global_exception':True,'not_claimed':['No SMS physical actor/camera/workspot requirement.','No placed-marker absence, blanket save-state inference or runtime delivery proof.','No additional quest/deep count from four nonselected fluff branches.'],'proposal_approved':False}
d['defects'].append(entry);prior_count=len(read(W/'prealpha/quest_restoration_qr4/defects_and_repairs.json')['defects']);new=d['defects'][prior_count:];newaffected={i for z in new for i in z['affected']};blocked=sum('BLOCKED'in z['status']for z in new)
d.update(new_confirmed_unique_defects=len(new),new_affected_quest_count=len(newaffected),new_blocked_unique_defects=blocked,cumulative_confirmed_unique_defects=len(d['defects']))
assert d['new_confirmed_unique_defects']==d['new_repaired_unique_defects']+d['new_blocked_unique_defects']
write(O/'defects_and_repairs.json',d)
q.update(new_unique_defects=d['new_confirmed_unique_defects'],new_affected_quest_count=len(newaffected),new_blocked_unique_defects=blocked);write(O/'queue.json',q);write(O/'contract_status_matrix.json',rows)
p['new_defects'].append(entry);write(O/'progress.json',p);write(O/'repair_queue.json',{'items':p['new_defects'],'source_epoch':8,'candidate':q['working_candidate'],'remaining_blocked':blocked,'installed':'PH3_UNCHANGED'})
write(out,{'status':'ONE_SHARED_SOURCE_DEFECT_FOUR_SELECTED_QUESTS_EIGHT_CONTRACT_SUPERSESSIONS','originals_preserved':True,'changes':changes,'source_pins':{str(x):sha(x)for x in [cp,ip,bp,Path(c['family_map'])]},'native_runtime_package_changes':0,'new_confirmed_unique':len(new),'new_affected_quests':len(newaffected),'repaired':d['new_repaired_unique_defects'],'blocked':blocked,'branch_timing_precision':'08:112=1real second,45sent,115=2game days. 01:114=3real seconds,65sent,119=2game days;137hub. Exact full source routes in family map.'})
print({'new_unique':len(new),'new_affected_quests':len(newaffected),'repaired':d['new_repaired_unique_defects'],'blocked':blocked,'updated_contracts':len(changes)})
