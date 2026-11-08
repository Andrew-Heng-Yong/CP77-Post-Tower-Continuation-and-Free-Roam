"""Pin shared hardening, repair decisions and precise remaining limitations."""
from pathlib import Path
import sys,copy,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not(O/'defects_and_repairs.json').exists()
e=read(O/'source_epoch_04.json');a=read(O/'approved_changes_03.json');rows=read(O/'targeted_dispositions.json');pr=read(O/'verification/preservation_01/result.json');assert pr['status']=='PASS'
def pin(p):
 p=(O/p).resolve()if not Path(p).is_absolute()else Path(p);assert p.is_file();return {'path':str(p),'sha256':sha(p)}
units=[
 ('MQ060 actual serialized gates','candidate_01/repair_nitro_01/verification_01/result.json','Native registered predicates vs actual before/after;47/80 mismatches become0; old issued owners retained.'),
 ('MQ060 independent source','worker_a/reviews/nitro_01/review.json','Positive registered root authority, not reverse-reference absence.'),
 ('MQ060 independent serialized','worker_a/reviews/nitro_serialized_gate_01/review.json','Actual candidate binary freshly decoded; exact guard and preserved descendants.'),
 ('CVI04 source controls','worker_a/verification_05/evidence.json','Real scene terminal clears/ACKs, muted path, no global PhoneEndCall dependency.'),
 ('CVI04 independent controls','worker_b/reviews/CVI02/verification_05/review.json','Fresh binary/native donors and active provider marker/community support.'),
 ('CVI integrated','candidate_01/repair_cvi_02/verification.json','Whole approved serialized tree equals actual candidate.'),
 ('Ronald actual fresh readback controls','worker_b/future_check_04/evidence.json','19 inspection models reconstructed from pinned raw readbacks;83 assertions/7 actual document mutants.'),
 ('Ronald packed world controls','worker_b/bar_check_02/evidence.json','Actual modern144-byte setups and native trigger globals; three packed controls.'),
 ('Ronald independent native/packed','worker_c/reviews/ronald_01/verification_02/review.json','306 assertions/64 case fixtures/four controls;73 native nodes, four future arm signals, scoped descriptor/trigger bytes.'),
 ('Ronald namespace','worker_a/reviews/ronald_namespace_03/evidence.json','All134 archive indexes;55 parsed XLs; all825 prior target additions; registration19913 and three depot keys.'),
 ('Ronald integrated preservation','candidate_01/repair_ronald_01/verification.json','Exact fresh typed/packed readback; eight prior repaired resources byte-identical, all old Spy nodes/phone fixes preserved with only Armed edge splice.'),
 ('Career native journal','worker_c/journal_proof_02/result.json','Exact current native equal-state block and processing path; retains saved early-owner uncertainty.'),
 ('Career independent native journal','worker_a/reviews/career_journal_01/review.json','Actual binary JNE→JE mutant and trackQuest0 path; does not certify saved-owner retirement.'),
 ('Cuckoo/Voodoo source','worker_c/remaining_01/result.json','Source-null endpoints, exact stock numeric predicate absence, door/controller mismatch and native Inject/persistent fields.'),
 ('Cuckoo/Voodoo actual controls','worker_c/remaining_controls_01/result.json','Four actual resource-document mutations and one persistent-field byte mutation.'),
 ('Eight UNKNOWN dispositions independent','worker_a/reviews/unknowns_final_01/review.json','Five UNKNOWNs retained; source proof narrows limitations without inventing a repair.'),
 ('Final C applicability','worker_c/final_scope_03/applicability.json','Exact25 source resources/three scripts match canonical04.'),
 ('Exact compile reuse','compile_reuse_01.json','All131 source bytes,134 current compiler/cache/source inputs,46 managed scripts and compiled output equal QR6 fresh compile.'),
 ('Whole archive','candidate_01/rebuild_01.json','Every1577 extracted payload SHA equals canonical source.'),
 ('Preservation','verification/preservation_01/result.json','15716 protected hashes; complete856 game/307 save metadata records;134 compile input pins; preexisting Git diff unchanged.')]
gates=[]
for name,p,scope in units:
 d=read(O/p);gates.append({'name':name,**pin(p),'recorded_status':d.get('status'),'scope':scope,'counts_are_nonunique_assertion_events':True})
write(O/'regression_evidence.json',{'status':'SOURCE_SPECIFIC_REGRESSION_AND_MUTATION_GATES_PINNED','source_epoch':'QR7:04','units':gates,'limits':['Counts overlap; no claim of unique gameplay coverage or summed audit completeness.','All deliberate mutations are private evidence copies; final resource hashes identify the approved unmutated sources.','Prior CR1/PH1/PH2/PH3 fixes are retained through complete source allowlist and old Spy node/edge/native phone preservation. No deployment or gameplay regression was executed.']})
registry=read(O/'shared_evidence_registry.json')
for item in registry['items']:
 if 'path'in item and 'sha256'in item:assert sha(item['path'])==item['sha256']
new=[
 ('QR7-MODERN-PACKED-NODESETUP','worker_b/bar_check_02/evidence.json','Current2.5 exact pinned raw layout only: stride144, global@0x58, low19 nodeindex@0x70, distances@0x78/0x7C. Typed WolvenKit fields may be wrong even after successful export.','worker_b/check_bar.py'),
 ('QR7-HANDS-ALWAYSLOADED-STATIC-MARKER','worker_a/actor_context_01/evidence.json','CVI selected default holo scene exact marker plus registry/community physical+holo references. Exact provider/descriptor/native ancestry only; no physical FO1 lease inference.','worker_a/verify_actor_context.py'),
 ('QR7-DEFAULT-MEMBER-PREFIX-PROBE','worker_a/default_members_01/evidence.json','Only observed InvalidDefaultValueEventArgs for exact current actors sector. First-N acceptance/refusal proves member names; empty event reflection is not evidence.','worker_a/probe_default_members.ps1'),
 ('QR7-CURRENT-CVI-NATIVE-DONORS','worker_a/current_native_donors_gate_01/evidence.json','Six current unique original native donors equal approved bytes; no inferred actor execution.','worker_a/capture_cvi_native_providers.ps1'),
 ('QR7-RONALD-SELECTED-PROTOCOL','worker_b/future_check_04/evidence.json','Only four selected done producers/news branches and exact stock SMS descendants; no enrollment, fluff or whole bar.','worker_b/check_future.py'),
 ('QR7-JOURNAL-EQUALSTATE-NATIVE','worker_c/journal_proof_02/result.json','Pinned current executable and Career exact Active/trackQuest0 path; same-state state/notification rejection. Does not prove other postprocessing or saved-owner liveness.','worker_c/verify_native_journal.py'),
 ('QR7-CUCKOO-VOODOO-PERSISTENT-TARGETS','worker_c/remaining_01/result.json','Exact selected fields/providers/stock definitions, not global economic-target closure. Record114327022403 remains unresolved, no inferred grant.','worker_c/verify_remaining.py'),
 ('QR7-GENERATED-ID-PROVIDER-NAMESPACE','worker_a/reviews/ronald_namespace_03/evidence.json','Exact parent/input and frozen new depots; all current parsed XL shapes and scopes; no fullworldglobal census.','worker_a/verify_ronald_namespace.py'),
 ('QR7-FINAL-C-SOURCE-APPLICABILITY','worker_c/final_scope_03/applicability.json','Only25 targeted resources and three supporting scripts. No broad promotion of other quests.','worker_c/capture_scope.py')]
for ident,p,scope,script in new:
 item={'id':ident,**pin(p),'applies_to':scope,'source_epoch':'QR7:04'}
 sp=O/script
 if sp.is_file():item['reusable_script']=pin(script)
 else:raise AssertionError(('Missing producing script; no command inferred',script))
 registry['items'].append(item)
registry['status']='PINNED_SHARED_EVIDENCE_WITH_EXACT_APPLICABILITY_AND_UNRESOLVED_DOMAINS'
registry['unresolved_shared_domains']+=['No global effective TweakDB/provider economic/vehicle closure was newly established. Current exact stock numeric record/target gaps remain in five UNKNOWN rows.','No full native/external world-global-ID collision census or runtime private streaming proof.','No all-save original-owner retirement, race-free concurrent-controller or engine persistence certification.']
write(O/'shared_evidence_registry.json',registry)
ld=read(W/'prealpha/quest_restoration_qr6/defects_and_repairs.json');ld['inherited_ledger']=str(W/'prealpha/quest_restoration_qr6/defects_and_repairs.json');ld['inherited_ledger_sha256']=sha(ld['inherited_ledger'])
for d in ld['defects']:
 if d['id']=='QR5-CVI02-EP1-ALTERNATE-HANDS-CONTROLLER':family='CVI'
 elif d['id']=='QR5-RONALD-POST-GIG-NEWS-OWNER':family='RONALD'
 else:continue
 d['QR6_original_finding']=copy.deepcopy(d);d['status']='PARTIAL_PROSPECTIVE_REPAIR_STAGED_STATIC_VALIDATED_WITH_EXPLICIT_HISTORY_LIMITS'
 d['QR7_resources']=[r for r in a['resources']if ('cvi_02'in r['depot']if family=='CVI'else 'sts_ep1_'in r['depot']or'quest_restoration_qr7'in r['depot'])]
 d['blocker']=('Old entered/requested/ambiguous saved owner histories defer; only future fresh EP1 admission repaired. Physical-marker blocker superseded by fresh exact always-loaded provider/registry proof. Actual calls/reload untested.'if family=='CVI'else 'Old entered/done/sent/native pending clocks and missing genuine enrollment/contact are not adopted. B0 subscription1755 remains unreachable; first-contact/enrollment route is explicitly not repaired. Runtime scoped streaming/scheduling/reload untested.')
 ld.setdefault('QR7_partial_repair_families',[]).append(d['id'])
ld['defects'].append({'id':'QR7-MQ060-REGISTERED-NATIVE-ENTRY-GATE','affected':['mq060_nitro'],'status':'PROSPECTIVE_NATIVE_ELIGIBILITY_REPAIRED_STATIC_VALIDATED_LIVE_PENDING','resources':[r for r in a['resources']if r['id']=='QR7-MQ060-REGISTERED-NATIVE-ENTRY-GATE'],'cause':'Unregistered standalone OR4 donor used instead of positively registered main ancestry OR3 AND carbought_counter>=3. New current gamedef authority proof resolves QR6 source conflict.','before_after':'47of80 actual native condition fixtures differ before;0after. Both pre-Issued guards corrected; all saved IDs/old issued selector paths preserved.','remaining':'Old issued owners retain selector/progress. Native wakeup/save-transition/gameplay not executed.'})
ld.update(source_epoch='QR7:04',status='TARGETED_REPAIRS_STAGED_PROSPECTIVE_SCOPES_STATIC_UNKNOWN_AND_LIVE_LIMITS_RETAINED',new_confirmed_unique_defects=1,new_repaired_unique_defects=3,new_blocked_unique_defects=0,new_affected_quest_count=len({r['quest_id']for r in rows if r['quest_id']=='mq060_nitro'or r['original_QR6_status']=='FAIL'}),new_changed_resources=len(a['resources']),cumulative_confirmed_unique_defects=len(ld['defects']),cumulative_staged_repairs=11,cumulative_changed_resources_vs_PH3=len(set(r['depot']for r in a['resources'])|set(r['depot']for r in a['inherited_repair_resources'])),source_authority_conflicts=[],additional_new_static_unknowns=[],existing_blocked_unique_defects=2)
ld['scope']='Three staged changes: two previously confirmed families partially repaired for future supported histories plus one newly confirmed Nitro donor defect. Counts of staged repairs include earlier containment;11 does not mean11 fully restored quest families. Residual static enrollment/history blockers and inherited continuation blockers remain explicit.'
write(O/'defects_and_repairs.json',ld)
blocked=[{'priority':'HIGH'if r['quest_id']=='sts_pac_cvi_02'else'MEDIUM','quest_id':r['quest_id'],'stage':r['stage'],'status':r['status'],'classification':'RETAINED_STATIC_UNKNOWN'if r['status']=='UNKNOWN'else'PARTIAL_REPAIR_BLOCKED_HISTORY_OR_ENROLLMENT_AND_LIVE_LIMIT','missing_evidence':r['remaining'],'source_evidence':r['evidence']}for r in rows if r['status']=='UNKNOWN'or r['original_QR6_status']=='FAIL']
write(O/'remaining_blockers.json',{'source_epoch':'QR7:04','rows':blocked,'other_limits':'All917conditional/162opaque full-matrix rows remain visible; none is certified by these targeted investigations. Inherited containment/resume blockers remain in ledger.','exact_unknown_followups':pin('worker_c/BLOCKER_FOLLOWUPS.md')})
write(O/'repair_queue.json',{'source_epoch':'QR7:04','status':'THREE_STAGED_PROSPECTIVE_REPAIRS_NO_DEPLOYMENT','implemented':a['resources'],'inherited_repairs_or_containments':8,'remaining_targeted_UNKNOWN':[r for r in blocked if r['status']=='UNKNOWN'],'partial_repairs_with_history_or_enrollment_blocks':[d for d in ld['defects']if d['id']in ld['QR7_partial_repair_families']],'inherited_other_blockers':'All original ledger records are preserved; MQ037 continuation remains explicitly blocked.','prohibited_shortcuts':['No synthetic native ACK/sent/done or Sandra/Delamain counter reset.','No old timer adoption/reclock, contact enrollment fabrication, global pause reset, whole-bar/default-owner clone.','No deploy/game launch/save/fact edit/release/Git publication.'],'runtime_changes_staged_only':a['resources']})
write(O/'evidence_index.json',{'epoch':pin('source_epoch_04.json'),'changes':pin('approved_changes_03.json'),'targets':pin('target_contracts_00.json'),'dispositions':pin('targeted_dispositions.json'),'matrix':pin('contract_status_matrix.json'),'shared':pin('shared_evidence_registry.json'),'regression':pin('regression_evidence.json'),'ledger':pin('defects_and_repairs.json'),'blockers':pin('remaining_blockers.json'),'final_C_scope':pin('worker_c/final_scope_03/applicability.json'),'final_C_checks':pin('worker_c/final_scope_03/shared_checks_inventory.json'),'preservation':pin('verification/preservation_01/result.json'),'package':pin('candidate_01/package_manifest.json')})
print({'status':'SUPPORT_EVIDENCE_LEDGER_AND_BLOCKERS_PUBLISHED','gates':len(gates),'new_shared_units':len(new),'partial_repaired_families':len(ld['QR7_partial_repair_families']),'remaining_UNKNOWN':sum(r['status']=='UNKNOWN'for r in rows)})
