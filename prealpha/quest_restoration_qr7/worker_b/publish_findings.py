"""Freeze Worker B's bounded source findings. This never selects/integrates a production candidate."""
from lib import *
import csv,io

def main():
 out=H/'findings_01'
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir()
 suite=read(H/'future_check_02/evidence.json');proposal=read(H/'experiments/future_owner_04/NOT_FOR_INTEGRATION.json');markers=read(proposal['markers']);models=read(H/'inspection_01/models.json')
 cases={r['quest_id']:r for r in suite['native_selected_family']};producers={r['quest_id']:r for r in suite['native_producers']};arms={r['quest_id']:r for r in proposal['arming_producers']}
 old=read(W/'prealpha/quest_restoration_qr6/contract_status_matrix.json');oldrows=[r for r in old if r['quest_id']in cases and r['stage']in ['communications','shared_dependencies']and r['status']=='FAIL']
 rows=[]
 for oldrow in oldrows:
  quest=oldrow['quest_id'];c=cases[quest];prod=producers[quest];arm=arms[quest];child=RN.replace('q302_ronald_tree','q302_msg_ronald_'+quest);g=models[child]['graphs']['root']
  sms=[{'node':i,'journal_paths':n['journal_paths'],'notifications':[z['sendNotification']for z in walk(n['payload'])if 'sendNotification'in z]}for i,n in g['nodes'].items()if n['sms']]
  predicates=[{'node':i,'reads':n['reads']}for i,n in g['nodes'].items()if n['reads']]
  proven=[f"Current native producer {prod['depot']} {prod['graph']}:{prod['node']} writes {quest}_done=1; freshly extracted stock raw equals pinned vanilla {prod['raw_sha256']}.",
   f"Native news root/11 listener{c['done']}→preclaim{c['preclaim']}→sent{c['sent']}→pause{c['pause']}→game-delay{c['clock']} preserves two game days; selector{c['standalone']} chooses normal{c['normal_gate']}/alternate{c['alternate_gate']}, each token AND outside, then child{c['child']}.",
   f"True child{c['child']}.Out1→release{c['release']} native pause0→hub{c['terminal_hub']} is retained. Native reply/timeout/outcome graph remains exact stock {child}; notification flags below are not normalized across cases.",
   f"Current B0 root/5 has no native news11/12; its saved scene enrollment1755 remains unreachable. This confirms the old missing-dependency finding; it does not contradict this gig's main Hands/Mark/Ana calls or earlier PH fixes.",
   f"Private serialized04 proposes an actual new future-event writer at existing {arm['intended_depot']} root/50:65002.Out→new65007(positive QR7 Armed)→65003 ParentEntered. Entire old fresh-admission predicate and every old node/payload/socket/other graph remain unchanged.",
   f"Private branch gate checks native done0/sent0 and either ParentEntered0 or QR7 Armed1, then waits the actual Armed1 producer before the native done listener. Old ParentEntered1/Armed0 skips without native writes. Native sent1 and old elapsed clocks are never reset or adopted."]
  if oldrow['stage']=='shared_dependencies':proven += ["Current native quest-sector descriptor1995 leases #q302_pr_bar; exact area_02/closer are native nodes1/3, not an AlwaysLoaded marker. Private serialized marker04 filters75→2 actual trigger definitions, preserves complete outlines/notifiers and every144-byte placement except newglobalID and packed index. New child202 owns only this private prefab; loaded checks220 dominate every listener.","Native additional/persistent Ronald26 owner is beneath EP1 root/10 cut9→additional4; killed10 writes q307_ep1_killed only after the cut. New admission also retains completed Tower/session receipts; no original native owner is restarted."]
  if quest=='sts_ep1_01':proven.append('Native SMS outcome33 tests sts_ep1_01_anderson_dead<1; normal/dead conversations, four real reply listeners22/23/36/37 and both native timeout/choice cleanup branches are unchanged.')
  if quest=='sts_ep1_08':proven.append('Native Spy Ronald greeting20 has sendNotification0, unlike the other selected greetings; the proposal deliberately preserves it. Mark/Ana/Organitopia PH1/PH2/PH3 protocols and Spy outer64999 remain unchanged.')
  rows.append({'quest_id':quest,'title':oldrow['title'],'stage':oldrow['stage'],'status':'FAIL','disposition':'CONFIRMED_BASELINE_GAP_WITH_SERIALIZED_FUTURE_REPAIR_PROPOSED_PENDING_INDEPENDENT_AND_COORDINATOR_GATES','proposed_disposition_if_accepted':'CONDITIONAL_FUTURE_EVENT_SCOPE_ONLY',
   'proven':proven,'approved_differences':[],'remaining':['The canonical candidate has not yet integrated this private proposal; current8 FAILs are not cleared by a nonproduction readback.','Earlier done1/sent1/native-clock states and entered jobs without QR7 Armed history remain deferred. Missing enrollment/contact evidence is not manufactured; current hidden enrollment dialogue is unchanged.','Independent source review, effective provider/namespace/registration checks and coordinator final package preservation remain required.','Actual queue ordering, streaming, notification display, interrupts and cold reload remain LIVE_ONLY.'],
   'evidence':[{'path':str(H/'future_check_02/evidence.json'),'sha256':sha(H/'future_check_02/evidence.json')},{'path':str(H/'bar_check_02/evidence.json'),'sha256':sha(H/'bar_check_02/evidence.json')},prod,arm],
   'specific_native_contract':c,'stock_SMS':{'depot':child,'predicates':predicates,'notification_writers':sms,'edges':g['edges']}})
 assert len(rows)==len(cases)*2
 # Exact baseline failing-before fixture, checked against fresh actual B0 resource and the proposed typed resource.
 current=models[BO];proposed=Resource(read(proposal['json'])).normalize()
 def consumers(m):
  return {q:{'done_reads':[{'graph':gp,'node':i}for gp,g in m['graphs'].items()for i,n in g['nodes'].items()if any(x.get('factName')==q+'_done'for x in n['reads'])],
   'sent_writes':[{'graph':gp,'node':i}for gp,g in m['graphs'].items()for i,n in g['nodes'].items()if any(x.get('factName')=='q302_msg_ronald_'+q for x in n['writes'])]}for q in cases}
 before=consumers(current);after=consumers(proposed)
 assert all(not z['done_reads']and not z['sent_writes']for z in before.values())
 assert all(z['done_reads']and z['sent_writes']for z in after.values())
 regression={'defect':'QR5-RONALD-POST-GIG-NEWS-OWNER','fixture':'Genuine old enrollment/contact and completed Tower, fresh admitted selected gig subsequently writes native done1; native additional ancestor is cut, while current B0 omits news11/12.','before':{'resource':BO,'result':'FAIL_MISSING_ALL_FOUR_CONSUMERS','actual_nodes':before},'after':{'resource':proposal['intended_depot'],'result':'SERIALIZED_FUTURE_BODY_HAS_ALL_FOUR_SOURCE_VERIFIED_CONSUMERS','actual_nodes':after},'limits':'This fails actual baseline and passes actual private readback for the missing consumer property. Registration, full package inclusion, provider precedence, supported-history scope and independent review are separate gates; it is not a gameplay or canonical-package PASS.'}
 save(out/'before_after_regression.json',regression)
 differences=[{'id':'FUTURE_ARMING_4_ENTRIES','change':'Only one new positive private writer65007 after each unchanged native/PTFR fresh admission65002 and before existing65003 ParentEntered; no admission or history reset.'},
 {'id':'SELECTED73_PRIVATE_BODY','change':'Keep exact73 source nodes/edges for four selected SMS; omit native fluff/bootstrap. New admission/wait nodes require actual new entry arming, old entered histories skip. AND67 input5 belongs to omitted fluff, so private terminal is AND4.'},
 {'id':'PRIVATE_TWO_TRIGGER_SUPPORT','change':'Copy only native area02/closer geometry/notifiers/transforms; new private globals and indices, one private Quest descriptor and nested phase lease. NodeLoading220 dominates listeners. No full bar owner or actor acquisition.'},
 {'id':'NO_CONTACT_RENOTIFICATION','change':'Read existing native ep1/contacts/ronald Active; do not re-add or notify a historical contact. Constructor serialization is not the sole semantic evidence; independent C native predicate follow-up is pending at this publication.'},
 {'id':'HISTORY_DEFERRED','change':'Enrollment/sent/pause/timer/journal outcomes preserved. Future-only delta is not a resume adapter for older already-entered or pending states.'}]
 save(out/'intentional_differences_proposed.json',differences)
 save(out/'contract_dispositions.json',rows)
 with(out/'contract_dispositions.csv').open('w',encoding='utf-8',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=['quest_id','title','stage','status','disposition','proposed_disposition_if_accepted']);writer.writeheader();writer.writerows({k:r[k]for k in writer.fieldnames}for r in rows)
 report={'worker':'B_RONALD','baseline_epoch':'QR6:00 = QR5:08/candidate03; affected inputs unchanged through QR7:01','unique_defect':'QR5-RONALD-POST-GIG-NEWS-OWNER','original_fail_contracts':len(rows),'quests':list(cases),'candidate_writes':0,'production_integration_approved':False,
 'proposal_manifest':{'path':str(H/'experiments/future_owner_04/NOT_FOR_INTEGRATION.json'),'sha256':sha(H/'experiments/future_owner_04/NOT_FOR_INTEGRATION.json')},'proposed_old_resources':list(arms.values()),'proposed_new_resources':[proposal['intended_depot'],markers['intended_sector_depot'],markers['intended_block_depot']],
 'checks':{'future_protocol':{'path':str(H/'future_check_02/evidence.json'),'sha256':sha(H/'future_check_02/evidence.json'),'assertions':len(suite['checks']),'actual_document_mutants':len(suite['mutations'])},'current_packed_bar':{'path':str(H/'bar_check_02/evidence.json'),'sha256':sha(H/'bar_check_02/evidence.json'),'assertions':10,'raw_byte_mutants':3}},
 'reproducible_commands':['pwsh -NoProfile -File prealpha/quest_restoration_qr7/worker_b/capture_gig_producers.ps1 -OutputName <fresh-relative-dir>','python -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_bar.py --out <fresh-relative-dir>','python -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_future.py --out <fresh-relative-dir>'],
 'regression':regression,'discarded_experiments':['Enrollment01 only restored genuine optional dialogue conditions/edges; excluded from staged proposal because it alone cannot restore news lifecycle.','Native full11 clone is unsafe: initial done listener can re-clock sent histories; sent checks exist only in cancellation rearm.','Future owner02 lacked actual producer arming and was rejected;03 added actual arming but was superseded by04 explicit trigger-loading guards.','Marker03 rewrote WK Id and changed raw pointer-placeholder0x50;04 preserves it. Earlier failures remain evidence, not certification.'],
 'next_gates':['C independent actual-resource review of frozen04, including contact predicate/registration/arming.','Coordinator only: independently resolve remaining namespace/provider gates, integrate accepted resources and exact XL additions in a fresh successor, serialize/package/read back and preserve every unaffected payload/prior repair.','Keep8 original FAIL disposition lines linked to exact historical deferrals; no source-identical ZIP or install.']}
 save(out/'results.json',report)
 (out/'REPORT.md').write_text('''# QR7 Worker B — Ronald post-gig news

The original four selected gigs still have eight canonical FAIL contracts until coordinator integration. A concrete future-event repair is serialized and source-checked in private outputs; it is awaiting independent review and final package gates.

The proposal adds four private positive arming writers after the existing fresh-admission predicates, a private owner preserving73 exact native selected-news nodes, and only two native trigger copies under a new private lease. It preserves preclaim real seconds, sent-before-clock ordering, exact two-game-day delivery and reply timeouts, native token/outside predicates, real SMS outputs, shared pause/cancel/rearm, original outcomes and notifications. It imports no unrestricted bar, actors, fluff controller, old clock or synthetic enrollment.

The current source producer capture independently matches all four pinned native hashes. The private protocol/readback suite passes81 checks and6 actual JSON mutants; packed marker evidence passes10 checks and3 raw-byte mutants. These are distinct suites and are not gameplay results. `before_after_regression.json` proves the actual baseline lacks all four consumers and the private serialized body supplies them, without pretending unregistered files execute.

Old done/sent/pending-clock states and entered jobs lacking the new positive Armed receipt are held. Missing enrollment/contact history is not created. The optional dialogue experiment is excluded. Engine streaming, queue/interrupt behavior and save transitions remain live-only. Exact source paths, nodes, sockets, hashes, per-gig outcomes and eight per-stage dispositions are in the adjacent JSON/CSV files.

Do not copy these experiments into a candidate without independent review, explicit intentional-difference records, namespace/registration/provider checks and coordinator package preservation gates. No game, save, install, release or Git artifact was modified by Worker B.
''',encoding='utf-8')
 print('Frozen',len(rows),'FAIL dispositions;',len(cases),'source-specific quests; private proposal only')
if __name__=='__main__':main()
