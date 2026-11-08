"""Record the evidence-backed racing adjudication; no runtime changes."""
from pathlib import Path
import sys,json
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
source=read(W/'prealpha/quest_restoration_qr2/ancestor_review.json')['inputs'][0]
p=Path(source['source_json']);assert sha(p)==source['json_sha256']
m=Resource(read(p)).normalize();owner=m['graphs']['root/82']['nodes']['5']
assert owner['refs']==[r'base\quest\side_quests\sidequests.questphase']
write(O/'ancestry.json',{'status':'PASS_NATIVE_SOURCE_ANCESTRY','source':source,'native_main_termination':'root106 genuine Tower journal Succeeded ->109 main_game_killed receipt ->107 Terminating','descendant_owner':{'graph':'root/82','node':'5','payload':owner['payload']},'quest_parent':'sidequests root50 owns native sq024; fresh phase100 matches payload with id relocation','scope':'Authored containment/termination, not a live saved-owner capture'})
contracts={}
def c(k,status,proven,diff,remaining,evidence):contracts[k]={'status':status,'proven':proven,'approved_differences':diff,'remaining':remaining,'evidence':evidence}
core=['../../verification_03/source_pins.json','../../verification_03/graph_evidence.json','../../verification_03/tests.json']
c('entry','APPROVED_DEVIATION',[
 'Actual S27 route is0.Out->1.Ready->2.pause->3.recheck;3.False rearms2,3.True->4.Issued->89 two ticks->90 postclaim check.True->92.Entered->93 AddContact->100.sq024_in.90.False reaches terminating91;100.sq024_out->101.Finished. No debug/race-resume input is used.',
 'Current100 phase payload equals independent native sidequests root50 except id50->100, including empty instance-prefab field and exact sq024.questphase reference. Original sidequests31 q101_enable_side_content>0->50.sq024_in is preserved as a positive range in the fresh gates.',
 'AddContact93 equals original sq024.quest node13 payload with id relocation; contacts/marianne is Claire native contact identity. Fresh bounded coordinator provider readback verifies unique original sq024.quest SHA B718DFEA307B8B9BE157CA84023271188A59942407CB7ECF61D815A311A0DA0E.'
],[
 'Established S27 fresh-story adaptation adds genuine Tower/PA2/U9, history/permit, phone-owner and once-only receipts before the unchanged original sq024_in. It does not restore the native standalone/debug entry sockets or overwrite a progressed story family.'
],[
 'LIVE_ONLY: ArchiveXL activation and graph scheduling are not executed by these static checks.'
],core+['../../../../../sidejobs_s27/claire/contract03.json','../../../../owner_gap_readback_01/capture.json'])
c('eligibility','APPROVED_DEVIATION',[
 'Actual guards2/3/90 contain all485 journal path/class/Inactive predicates and five story quest roots. Their native fact bounds match contract03;270+ focused checks include prior Active/Succeeded/Failed roots, missing facts/journal, already-owned R1 and sq024_done refusal. Guards2/3 need Issued0; postclaim90 recognizes Issued1.',
 'Native opening root/92 retains0->deletion8->6(q105_done>0)->7(AND SideQuest_Standalone content token and player outside #sq024_tr_close_to_afterlife)->4(sq024_active1)->1. q105 is an earned prerequisite, never manufactured or bypassed.',
 'Current S27 Read rejects missing/undefined and delayed journals, verifies fact ranges and matching consecutive samples, and delegates historical admission to SnapshotStateHS1.Admits. Its Permit method will not modify an already Issued owner; no circular phone-issued Permit requirement exists in the REDscript fact table.'
],[
 'Fresh-only five-root admission is deliberately stricter than native availability. q101 enablement and q105 completion are retained even though this task does not restore excluded main-story prerequisites. mq057_motorbreath remains held; MQ056 repeatable races are a different native quest.'
],[
 'LIVE_ONLY: Actual earned q105 history, content token availability, all485 journal states and player scene/safety conditions are save/engine inputs. No current eligible fixture is asserted.'
],core+['../../../../../phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS27.reds'])
c('communications','PASS',[
 'Private Claire listener1000->1001.Ready->1002.pause->1003.True->1004.Issued->46.In1 is connected;46 payload exactly matches native holocall_initializers46 and references claire_holocall.questphase. Fresh story admission waits PTFRS27_PHONE_CLAIRE_Issued1 before any authored caller can execute.',
 'Native hook scene312 requests holo_claire_calls_v_start_activate->306 waits matching start_done>0->307 clears it;313 end request->308 wait->309 clear. Native controller0->28.False->9 request clear->21.holo_claire_calls_v_start,2->10->21.holo_claire_calls_v_end; actual scene41/42 write incoming acknowledgements. Outgoing3->30.False->11->21.holo_v_calls_claire_start and4->12->21.holo_v_calls_claire_end reach actual43/44 ack writers.',
 'All four race outgoing caller continuations are traced: Santo Domingo1114->1107->1108/start and1115->1109->1110/end; Badlands1188->1181->1182 and1189->1183->1184; City1437->1430->1431 and1438->1432->1433; final race1188/1189 use matching1181/1183 waits. Native hook INT->30 end/RET->29 start and rejection branches remain.',
 'Shared fixer_cleanup1002.True->1003.In7->Out7->1240 is connected to exact native claire_cleanup. Native cleanup4 compares incoming start/end counts then6 reset-counter->0.end;5 compares outgoing counts then7->1.end;3.Out7 returns. All native messages/choices in city,badlands,Santo Domingo,final and post-Sampson phases remain unchanged native resources. No synthetic acknowledgements or historical counter reset was added.'
],[],[
 'LIVE_ONLY: Phone UI/playback, actual delivered SMS, rejection/arbitration and acknowledgement scheduling require engine execution. Pending calls from an unsupported saved preclaim state are not a newly proved fresh-route defect.',
 'SCOPE: Native controller audio-only branches exist but the inspected SQ024 positive request producers use holo prefixes; unused raw audio branches are not promoted into new bug claims.'
],core)
c('ownership','CONDITIONAL',[
 'Independent native ancestry is main cyberpunk2077 root/82 node5 -> sidequests root50 -> SQ024. Genuine Tower journal success->receipt109->Terminating107 encloses that original main tree. This is explicit authored owner containment, not killed-flag-only proof.',
 'S27 startup and postclaim gates reject five progressed/finished/failed roots and another R1 owner. R1 repeatable boot2/3 instead requires sq024_done>0, neutral mq056 active/prevention/test state, four replay phases not Active, and its own Issued0. It invokes a separate MQ056 native owner, not another story SQ024 owner.',
 'Existing B0 Claire root5 retains exact native default_dialogs root/4 node19 prefab #pr_claire_default. Every original descendant payload/socket and native edge is retained, with edge splits only through owned PTFRB0CLA diagnostic facts. Native quest-role Reactivate96 precedes claire_default_on0 writer111 in garage root/54, and native default service observes that lease flag.'
],[
 'Private S27 story and R1 replay owners retain established scoped admission and saved identities. No old native bugfix tree or arbitrary encounter controller is restarted.'
],[
 'CONDITIONAL: Matching saved executing-owner retirement/adoption and old-version race transitions are not available. Original SQ024 bugfix companions are pinned/inventoried, but their actual saved lifetime after Tower is not inferred from disk presence.',
 'LIVE_ONLY: Native Terminating cancellation, actor handoff ordering and ArchiveXL phase persistence are engine behaviors.'
],core+['../../ancestry.json'])
c('progression','PASS',[
 'Unmodified native SQ024 root5 hook->6 garage;6.Out1->90->9 city;9.Out1->78->8 badlands;8.Out1->77->7 Santo Domingo;7.Out1->43->10 final. Same parallel cleanup branches51/52/53 remain. Garage end_out,city end,badlands failed and Santo Domingo quest_end_out retain original decline/failure path22.',
 'Final10.claire_alive->26->54 cleanup and Sampson escape->117 native prevention split retain original alternatives. Native final messages/root106 branch on sq024_sampson_crashed/dead; no outcome selection or Sampson/Claire fact is rewritten by S27.',
 'All53 initial graph resources plus native default service and original quest source were raw-binary pinned and reparsed. Main race bodies remain native delegated resources, including nested graphs, checkpoint controllers, scene transitions and deliberate native unreachable/deletion-marker branches.',
 'R1 owner is the complete native MQ056 owner with only main resource relocation. Its main preserves every native node/socket/nested graph and all native edges except original0->34, replaced by delivered-invitation gate1000. Active/Succeeded invitation resumes through1001->23; otherwise34 retains native original intro. Native replay/race/prevention-failure loops remain.'
],[
 'Existing R1 invitation-history shortcut avoids replaying a previously delivered SMS and delay. It is not a story restart or an interrupted-race migration.'
],[
 'LIVE_ONLY: Driving AI, checkpoint timing, prevention failures, scene transitions, winning/losing and branching choices are not gameplay-verified.'
],core)
c('presentation','OPAQUE',[
 'Wrapper100 has no instance prefab because the independent normal native parent50 also has none; this is not used to waive descendant support. Native SQ024 inline instance prefabs remain: root92 #sq024_pr_00_afterlife;root26/54 garage+big-race;root51 city-end;root52 badlands-end;root53 garage;root68 final-race. Native garage phase root owns garage+afterlife. Other race/scene/workspot/NodeRef obligations are enumerated in graph_evidence.',
 'Native default Claire prefab #pr_claire_default and complete default service body are preserved with owned diagnostics only. The native make_hackable helper is inline root/53/55 (20 nodes,28 edges,make_hackable_in/un_hackable_in); its zero external ResourcePath is not a missing external phase.',
 'Shared PH3 studio_support payload is pinned and unchanged. MQ056 commentary declares a Johnny community actor; current JV1 presentation script matches Character.Silverhand and hides visual components only after genuine Tower gates, preserving actor/voice/timing. No Johnny takeover or projection-revival change is introduced here.'
],[
 'Existing approved voice-only Johnny compromise and PH3 studio support remain unchanged; JR3 creates no new actors or presentation override.'
],[
 'OPAQUE: PH3 studio sectors have a recorded DynamicBaseClass/worldNode decode limit. World-placement/variant correlation for racing prefabs, car spawners, triggers,splines,cameras,workspots and scene markers is not fully decoded by these graph comparisons.',
 'CONDITIONAL: Actual Character.Silverhand community binding, JV1 visual suppression and independent props/lighting are not fully resolved by script presence; JV1 itself discloses independent props are not covered.',
 'CONDITIONAL: Language-specific lipsync/VO and referenced asset provider/placement resolution remain separate static inputs; graph/reference preservation is proven, all rendering is LIVE_ONLY.'
],core+['../../../../../phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds'])
c('journal','PASS',[
 'All native objective/message/state/mappin writers and their incoming state sockets are retained in untouched native phases. Detailed graph_evidence records every path and writer socket, including all five story roots and conditional race objectives.',
 'Native decline/failure root/22 node8.Out->6.Failed sets quests/meta/07_nc_underground Failed. Native final root/114 node7.Out->6.Succeeded and final-message134.Out->133.Succeeded preserve story completion alternatives. No S27 direct journal write resets history.',
 'Fresh wrapper101 records private Finished only on native100.sq024_out. It records owner return, not a fabricated win. Native authored failure and completion remain distinct.'
],[],[
 'LIVE_ONLY: Native journal auto-propagation, tracking display and delayed state delivery use the engine; no actual player journal was changed.'
],core)
c('completion_rewards_cleanup','CONDITIONAL',[
 'Native completion cleanup root/68 sets sq024_active0 at3->sq024_done1 at4, preserves checkpoint sq024_finished, token release/respawn and default Claire handback. Existing race/community/car/crowd/security/weather cleanup and prevention-failure branches are not replaced.',
 'Exact reward branch pointers remain: root/54 node33 QuestRewards.sq024_finish_big_race; final race root/57/185/116 node50 sq024_win_big_race and nested118 node7 sq024_finish_big_race. Native earlier finish/win rewards and Sampson/Claire vehicle-unlock branches are retained as authored alternatives, not replayed unconditionally.',
 'The private wrapper writes only its own Ready/Issued/Entered/Finished/Fault receipts. It adds no item, money, XP, reward, success fact or original journal reset. R1 retains original MQ056 native repeated-race rewards and cleanup behavior.'
],[],[
 'CONDITIONAL: Exact QuestRewards.sq024_* and MQ056 reward record definitions/values and vehicle entitlement/TweakDB targets are not independently resolved in this graph corpus. Pointer and branch preservation cannot certify actual reward delivery.',
 'LIVE_ONLY: Exactly-once transaction behavior, reward delivery after interruption, saved inventory/car entitlement and cleanup execution require matching runtime/save transition fixtures.'
],core)
c('persistence','CONDITIONAL',[
 'Every current private source resource hash is pinned to unchanged PH3; no saved resource/node/field/path/receipt identity is changed. Story Issued4 precedes entry and Finished101 follows native return; both early gates require unissued, final postclaim90 recognizes issued1.',
 'S27 Restore resets only transient sampling and unissued Permit. Permit/Poll refuse to change Issued owners. Known done/failed/progressed family histories are excluded; R1 accepts only inactive replay phase seams and resumes previously delivered invitation without resending it.',
 'Five actual-data mutation controls catch an admitted Active story root, lost native entry edge, disconnected native phone start continuation, lost shared cleanup continuation and obsolete MQ056 main donor replacing corrected R1.'
],[],[
 'CONDITIONAL: Existing saved native/private descendants, previously interrupted races, old-version adoption and scene/reward transaction boundaries are not decoded or simulated. Unsupported unfinished histories continue to defer; no migration/restart is implemented.',
 'LIVE_ONLY: Save/reload and interrupted-call/drive persistence must be tested on matching fixtures if later authorized.'
],core)
c('shared_dependencies','CONDITIONAL',[
 'Story admission requires U9 supportIssued1/Fault0, B0 Claire Ready+Enabled/no suspension/exclusion, Claire phoneIssued1, native phone idle and mutually exclusive R1Issued0. Actual wrapper call and cleanup edges are verified, not inferred from resource presence.',
 'Entire B0 Claire native service payloads/sockets/edges survive with only owned diagnostic splits. Existing native claire_default_on lease and current script gate are preserved; native q105/content-token prerequisites remain.',
 'R1 main relocation/invitation adaptation is independently compared against complete native MQ056 graphs; its four city/badlands/Santo Domingo/final race and prevention-failure controllers remain original. It does not admit held mq057 or reset historic wins.'
],[
 'Existing PH1 cleanup/listener layers and PH3 shared studios remain installed unchanged; this batch adds no shared controller or new lease.'
],[
 'CONDITIONAL: Full saved B0/quest/phone lease arbitration, native bugfix-companion lifetime, world/shared studio placement and localization resolution remain bounded exactly as ownership/presentation describe.',
 'LIVE_ONLY: Concurrent service departure, phone interruptions and race cleanup streaming cannot be established by static source equivalence alone.'
],core)
Q=O/'quests/07_nc_underground';assert not (Q/'contracts.json').exists();Q.mkdir(parents=True,exist_ok=True)
write(Q/'contracts.json',{'quest_id':'07_nc_underground','title':'The Beast in Me','status':'DEEP_REVIEWED_WITH_STATIC_LIMITS','static_verified':False,'defects':[],'repairs':[],'contracts':contracts,'validation':{'final_tests':'../../verification_03/tests.json','focused_checks':273,'mutations':5,'pinned_binary_inputs':55},'native_vs_current':'S27 references original SQ024; R1 native MQ056 differs only by documented main relocation/invitation resumption; native B0 Claire service body preserved except owned diagnostic insertions','no_repair_conclusion':'No source-confirmed defective route was found. Exact preserved native routes and conservative admission are positively verified; remaining asset/TweakDB/save/engine inputs do not justify a speculative gameplay patch.'})
report='''# Agent A — The Beast in Me / SQ024 and related R1 replay support

All ten contracts investigated. **No source-confirmed gameplay defect; no runtime repair. Not fully STATIC_VERIFIED.**

The S27 fresh story entry reaches exact native `sq024_in` after genuine Tower, native prerequisite/history, phone readiness and once-only checks. Native q101 enablement and q105 completion/token/offsite predicates remain. All 485 journal path/class states are checked, including the five racing-story roots. Native story order, failure/decline alternatives, Claire/Sampson decisions and final messages are unchanged.

Claire's real incoming and four outgoing race caller request/wait/clear paths are connected to native listener and acknowledgements. Shared `fixer_cleanup` condition1002 -> native cleanup1003.In7 -> Out7 ->1240 remains. B0 Claire's native parent prefab and complete local graph survive, with only owned diagnostic edge splits. R1 is a separate native MQ056 repeatable owner requiring earned `sq024_done>0`; its only behavioral adaptation resumes an already delivered invitation rather than resending it. It does not re-admit the story or held MQ057.

[contracts.json](quests/07_nc_underground/contracts.json) has exact nodes, sockets, predicates, positive proofs, approved differences and remaining evidence for each contract. [Final source pins](verification_03/source_pins.json) bind 55 binary resources and raw JSON/model exports. [Graph evidence](verification_03/graph_evidence.json) records 2,855+ handler rows, native branch/state/reward edges, prefab roots and NodeRefs. [Native ancestry](ancestry.json) proves original sidequests containment under genuine Tower Terminating output, with the saved-owner boundary retained.

## Validation

**273 focused checks passed**, including five actual-resource mutation controls. Original native graph bodies, all four outgoing race acknowledgements, all485 journal predicates, local default-service payloads/edges, nested native vehicle-hackability helper, corrected R1 donor and native reward pointers are checked. No gameplay engine or save is simulated. Earlier verification_01/02 snapshots are retained; verification_03 is final. The initial local file name `inspect.py` shadowed Python's stdlib while argparse initialized; it was renamed `exploration_trace.py` before a successful run. No external or runtime file was affected.

Reproduce only into a new directory:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -B 'prealpha\\quest_restoration_qr3\\agents\\agent_a\\verify.py' --output 'prealpha\\quest_restoration_qr3\\agents\\agent_a\\verification_next'
```

The checker refuses an existing output directory. No build/compiler/installer is imported or executed.

## Explicit remaining limits

- World streaming-sector/prefab/variant/NodeRef correlation and known opaque shared-studio placements; graph equality does not prove spatial resolution.
- Language-specific VO/lipsync resolution, Johnny community-record identity and actual JV1 visual suppression/independent props.
- Exact `QuestRewards.sq024_*`, MQ056 reward and vehicle-entitlement data definitions and current providers; authored reward paths and IDs are preserved, delivery is not certified.
- Saved executing-owner adoption, old interrupted races, concurrent actor/service/phone leases and reload/reward boundaries. Actual racing, UI, rendering, interruption and transaction execution are LIVE_ONLY.

All writes are isolated investigation outputs under Agent A. PH3, installed files, saves, releases and common queue remain untouched.
'''
(O/'REPORT.md').write_text(report,encoding='utf-8')
write(O/'result.json',{'agent':'agent_a','quest_ids':['07_nc_underground'],'contracts_file':str(Q/'contracts.json'),'status':'INVESTIGATED_WITH_STATIC_LIMITS','confirmed_defects':[],'repairs':[],'tests':str(O/'verification_03/tests.json'),'dependency_depots':str(O/'verification_03/dependency_depots.json'),'runtime_changes':[]})
print(json.dumps({'quest':'07_nc_underground','contracts':len(contracts),'counts':{x:sum(v['status']==x for v in contracts.values()) for x in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE']},'repairs':0}))
