"""Write baseline dispositions. Runtime repair, if accepted, belongs to root."""
from pathlib import Path
import json,sys
W=Path(__file__).resolve().parents[4];A=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
V=A/'verification_02';D=read(V/'defects.json')['defects']
assert not (A/'quests/mq037_brendan/contracts.json').exists()
e=[str(V/'source_pins.json'),str(V/'graph_evidence.json'),str(V/'tests.json')]
def contract(status,proven,remaining=(),approved=(),extra=()):return {'status':status,'proven':proven,'approved_differences':list(approved),'remaining':list(remaining),'evidence':e+list(extra)}
common_entry=[
 'Both selected IDs share exactly one private MQ037 owner: towercontinued\\sidejobs_s23\\base_b\\mq037.questphase SHA E42A7DE2591C367ACD1FCFAFD0D9BA728204034D57CEA0577848445C7C8DD94E. Native minorquests node34 and ancestor predicates54(q001_done>0),80(q005_done>0),55(q101_enable_side_content>0) are exact.',
 'Actual connected wrapper:1000->1001 Ready->1002 pause->1003 PA2 wait->54->80->55->1004 recheck.True->1005 Issued->1006 Entered->34.In1. False recheck loops to1002. Native34.Out1 writes1007 Finished.',
 'SOURCE_CONFIRMED DEFECT QR3-MQ037-EXCLUDED-PREREQUISITE: the native full In1 route is0->34 initializer->10 technician->19 Dumpster->23 girlfriend->25 hooligan->28 final service. It can activate the explicitly excluded Dumpster before either selected sequel. This is a demonstrated authored route with a feasible fresh admission, not a gameplay observation.'
]
common_elig=[
 'Both actual serialized admission predicates1002/1004 require all18 journal entries Inactive, including all five excluded Dumpster entries; all ten MQ037 native progress facts equal0. Completed/failed/active histories and absent journal inputs are refused in focused controls. Setting earned Dumpster root Succeeded causes refusal.',
 'Effective runtime producer is S23 index13: Paths13 and both state arrays exactly match all18Inactive. Read requires known settled values; matching stable samples feed Permit(i,Same(previous,current)&&Ready(i)). Ready checks Snapshot.Admits(primaryID) and common safe/Tower/receipts, but has no MQ037-specific hold. Snapshot Allows admits stable primary root1 or2 and has no earned-Dumpster prerequisite test.',
 'The current final selection explicitly excludes fresh mq037_brendan_dumpster and allows these selected sequels only after genuine earlier completion. docs/whitelist_final_r6.md lines101-111 and the current catalogue contradict this actual all-inactive seam. No old implementation contract grants an exception to that current policy.'
]
common_comms=[
 'Complete pinned native MQ037 phase and its sole referenced scene contain no quest-owned audio_/holo_/phonecall_ request or acknowledgement writes/readers and no decoded questSendMessage/questPhoneCall nodes. This family uses in-person authored scenes, not a missing contact controller.',
 'Scene inputs are retained through exact native references: technician_in,post_kids_dial_in,dumpster_help_in,dump_dial_start_in,help_plz_in,girl_dial_in,hooligan_stop_in,intervene_dial_in,brandan_saved_in,brendan_gone_in,brendan_found_in,bad_news_in. Scene retry/interrupt conditions remain native; no synthetic acknowledgement is added.'
]
common_ownership=[
 'One private native-phase node34 owns the entire family; Spray Paint is nested root/25 and Coin Operated Boy root/28, not independent duplicate owners. Native resource root owns exact #mq037_pr_machine_spot and #mq037_service_point; private parent node34 is payload-identical to native minorquests34.',
 'Native MQ037 bugfix companion D272A7D9610FCE5A0C670A1BCBF30B4A9C4DDA23EF87467105A74759D80150F9 is inventoried with its repair-only alternate inputs. Those one-time corrective graphs were not promoted into a new owner.',
 'QR2 ancestor proof applies to the matching native minorquests tree: genuine Tower journal success -> main receipt109 -> Terminating107 encloses main root/82 node6. This proves authored ancestor retirement, not the executing tree in a particular save.'
]
common_presentation=[
 'Direct native MQ037 delegation preserves32 top-level nodes,all inline graphs,root prefabs and exact scene4ED7F040BFBE1F424825AFF57C33FBB1C007D52D19243475C9543BD84A3514D2. No private scene or actor replacement exists.',
 'Native scene defines Technician,Brendan,Girlfriend,Hooligan,Clerk,Brendan_1 plus player actors,4props,17workspots and43workspot instances. Actual reference preservation includes #mq037_com_characters,#mq037_com_hooligan,#mq037_com_service,#mq037_01_sm_brendan_scenes,#mq037_dumpster and native service-door/shutter/turret/triggers. Six native English lipsync declarations are listed in provider_requests.json.'
]
common_persistence=[
 'QR3 agent C changed no runtime resource,field,node,receipt,installed path or saved fact. Existing13 private wrapper nodes and native resource references stay pinned to PH3.',
 'S23 Permit returns without changing a durable nonzero Issued owner; both preclaim guards require Issued0/Finished0/Fault0. Existing private descendants and native journal outcomes must remain intact. A selected sequel is not permission to reset the excluded prerequisite.',
 'Proposed conservative quarantine changes only1004.True->1005 into1004.True->1008, using the already-existing Refused1 writer. In-memory tests show all nodes unchanged, no fresh reachability to native34 and identical descendant reachability from saved Issued seed1005. This is a proposal, not a serialized or installed repair.'
]
common_shared=[
 'SOURCE_CONFIRMED shared-family policy defect affects both selected IDs. There is only one common admission index13; creating a second dedicated Spray/Coin owner would risk duplicated actors,tokens and native outcomes.',
 'Native root/19 requires real #mq037_dumpster DemolitionPerformed at7 before13 objectiveSucceeded->14 talkActive; talk exit15->17 rootSucceeded->23checkpoint->24 eight-game-hour delay->25 outside-area->26 hideDumpster->Out1. Skipping this by fabricated completion, Body/profile changes or a forced device event is prohibited.',
 'Later earned-history support must review the actual saved stage: current data demand introduced0 and all DumpsterInactive, whereas genuine earlier completion carries introduced/history and completed entries. Merely switching a guard to Succeeded while invoking native full In1 would replay setup and the excluded job.'
]
for quest,title in [('mq037_brendan','Coin Operated Boy'),('mq037_brendan_hooligan001','Spray Paint')]:
 iscoin=quest=='mq037_brendan'
 progression=[
  'The inspected native body itself is unmodified and keeps every authored branch; the adapter defect is selecting its full fresh entry before the excluded prerequisite. Native main chain is19->23->25->28; alternate inputs Introduction,Girlfriend,Hooligan,service_point and bugfix inputs are not used by current wrapper.',
  ('Coin root/28 runs native Theo/brendan_gone -> service quest18.Active->17 first objectiveActive->91 description. Service139 retains clerk-convince/combat/turret branches,objectives,gate commands and kill-token cleanup. Final140 bad_news_out->5 talkSucceeded->6 questSucceeded->11 reward->9 mq037_done1->8 checkpoint.' if iscoin else 'Spray native root/25 starts106.False->109 questActive->86 phaseActive->73 deal-with-hooliganActive->62. Native62 distinguishes threatened/combat/interrupt returns. Deal objective49Succeeded->35 POIInactive->50 talkActive;94->51 talkSucceeded->52 questSucceeded. Painting122 sets vandal_painted1->123 rootFailed and continues native cleanup; no Failed reset is introduced.')
 ]
 journal=[
  'Existing selected quest journal paths, incoming Active/Succeeded/Failed sockets and notifications are native and recorded in graph_evidence.json. The private wrapper writes only owned receipts, never a native journal reset.',
  'Nevertheless its reachable native path6.help_plz_out->22(markerInactive)->16.Active writes quests/minor_quest/mq037_brendan_dumpster, then16.Out->12.Active writes excluded push objective. This violates the current selection even though those are exact vanilla journal nodes.',
  ('Final Coin questSucceeded is root/28/140 node6 and mq037_done writer9 after reward11.' if iscoin else 'Spray success is root/25 node52; native rootFailed is123 after painting writer122. Both exact state paths remain; they are not proofs that this fresh adapter is permitted.')
 ]
 completion=[
  ('Exact native final reward pointer is QuestRewards.mq037_done at root/28/140 node11;6questSucceeded->11reward->9done1->8checkpoint is retained. After final family completion root/32 restores hey_rey_techstore_01_default_on1 and native crowd/spawn state before root1 terminating exit.' if iscoin else 'Spray success/failure routes and cleanup are native:52Succeeded or123Failed; the family later continues to Coin. The inspected Spray nested graph has no separate questGiveReward record; final family QuestRewards.mq037_done remains at root/28/140 node11. No unconditional reward or duplicate item grant was added.'),
  'The physical excluded prerequisite and its native reward/state path are not bypassed. Existing outcomes remain original, but current new-owner admission is unsafe until coordinated repair.'
 ]
 cs={
 'entry':contract('FAIL',common_entry, ['Root must implement/review a conservative new-owner hold or a fully reviewed earned-history adapter; agent proposal is not applied.'],['Genuine Tower/fresh-state receipts are approved generally; inclusion of the excluded fresh prerequisite is NOT an approved difference.'],[str(V/'defects.json')]),
 'eligibility':contract('FAIL',common_elig,['Need exact frozen pre-Tower earned Dumpster proof, later stage/journal/fact seam and original owner review before admitting new selected sequel owners.'],[],[str(W/'docs/whitelist_final_r6.md'),str(V/'defects.json')]),
 'communications':contract('PASS',common_comms,['LIVE_ONLY: Actual in-person dialogue playback, interruption/return arbitration and scene performance are engine behavior.']),
 'ownership':contract('CONDITIONAL',common_ownership,['Saved executing-owner adoption/older private descendant compatibility and native bugfix-controller lifetime require exact saved-state/transition evidence. The unsafe fresh entry is separately FAIL.'],[],[str(W/'prealpha/quest_restoration_qr2/ancestor_review.json')]),
 'progression':contract('FAIL',progression,['Full native progression preserves an excluded earlier job. An earned-history adapter must use a proven later seam without replaying setup or creating a duplicate family owner.']),
 'presentation':contract('OPAQUE',common_presentation,['Static blocker: exact world sector/descriptor resolution for both prefabs and all community,scene marker,device,workspot/spline references has not been fully decoded/correlated.','Static blocker: declared localized lipsync resolution and current binary asset providers need bounded resolution; no absent-provider defect is asserted from reference strings.','LIVE_ONLY: Rendered Brendan/Theo/hooligan actors,variant selection,lip playback and streaming.']),
 'journal':contract('FAIL',journal,['Preserve all completed/failed selected and prerequisite histories. Do not rewrite native journal states to manufacture the permitted earlier completion.']),
 'completion_rewards_cleanup':contract('CONDITIONAL',completion,['Static blocker: QuestRewards.mq037_done target definition/current override/provider values not independently resolved.','LIVE_ONLY: Exact reward transaction/once-only execution across interrupted completion and save/load are not simulated.']),
 'persistence':contract('CONDITIONAL',common_persistence,['Proposed edge quarantine must undergo serialized readback/native graph diff and independent review by coordinator.','LIVE_ONLY: Pre-update input already queued for node1005 and older mid-phase save transition behavior need engine fixtures; no resource rollback is save undo.']),
 'shared_dependencies':contract('FAIL',common_shared,['Conservative new-owner quarantine can prevent the confirmed excluded fresh route while preserving old Issued descendants. Supported later-family restoration remains blocked on exact earned-history seam.'])
 }
 obj={'schema':1,'quest_id':quest,'title':title,'status':'FAIL_CONFIRMED_SHARED_SCOPE_ADMISSION','fully_static_verified':False,'tested_baseline':'PH3','shared_family':'MQ037','contracts':cs,'defects':D,'repairs':[],'tests':[str(V/'tests.json')],'proposal':str(V/'proposed_quarantine.json'),'scope':'Baseline investigation only; root owns any final successor repair and adjudication.'}
 d=A/'quests'/quest;write(d/'contracts.json',obj)
 (d/'REPORT.md').write_text('# '+title+' — QR3 baseline investigation\n\nBoth selected Brendan jobs share one MQ037 native owner. **Confirmed policy/admission defect:** current all-Inactive fresh entry reaches excluded I Can See Clearly Now before the selected sequels. The native quest body is preserved, but this is not an authorized Tower adaptation.\n\n'+ '\n'.join('- **'+k+' — '+v['status']+':** '+' '.join(v['proven']) for k,v in cs.items())+'\n\nSee [exact graph evidence](../../verification_02/graph_evidence.json), [tests](../../verification_02/tests.json), [source pins](../../verification_02/source_pins.json), [defect](../../verification_02/defects.json) and [unserialized quarantine proposal](../../verification_02/proposed_quarantine.json). All remaining static/live-only limits are explicit in [contracts.json](contracts.json). No runtime resource or installed file was changed.\n',encoding='utf-8')
write(A/'summary.json',{'agent':'agent_c','quests':['mq037_brendan','mq037_brendan_hooligan001'],'contracts':20,'source_confirmed_defects':1,'defect_ids':[D[0]['id']],'runtime_changes':False,'tests':str(V/'tests.json'),'test_checks':288,'mutation_controls':4,'fully_static_verified':0,'root_action':'Independently review/serialize conservative preclaim quarantine; later earned-history adapter remains an exact blocker, not permission to fabricate history.'})
(A/'REPORT.md').write_text('''# Agent C — Brendan family

Investigated Coin Operated Boy and Spray Paint together across their single native MQ037 owner. Both have ten explicit baseline dispositions in `quests/<id>/contracts.json`.

**One shared source-confirmed defect:** effective S23 producer and serialized guards accept all18 family journals Inactive, including excluded Dumpster. The connected native In1 route then activates that excluded quest before the selected jobs. Current earned completion is refused by the same guards. The final whitelist explicitly requires genuine earlier completion and forbids restoring Dumpster. This is a policy/admission defect, not missing native progression or a measured gameplay failure.

`verification_02/` contains288 focused source checks,4 real in-memory mutation controls,5 raw binary/model pins,complete relevant node/socket/fact/journal/asset evidence and a failing-before/passing-after counterexample. All checks pass as verification of the confirmed bad route; baseline policy compliance is explicitly FAIL. The suggested one-edge quarantine is in-memory only:1004.True->1005 becomes1004.True->1008(existing owned Refused writer). All13 wrapper nodes and old Issued descendants remain intact. Root must independently review and serialize any repair.

Do not add an earned-prerequisite condition then call full native In1: that replays excluded setup. A later earned-history adapter needs a precise original/saved stage,actual completed journal/fact seam and frozen pre-Tower evidence. Already-issued descendants must not be canceled or reset.

Native journal,scene,failure,cleanup and final QuestRewards.mq037_done routes were traced. Exact world placements,localized assets,TweakDB reward definitions and save/engine transitions remain explicit blockers.

Reproduce into a NEW directory:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -B 'prealpha\\quest_restoration_qr3\\agents\\agent_c\\verify.py' --output 'prealpha\\quest_restoration_qr3\\agents\\agent_c\\verification_next'
```

No builder,game,installer,save/fact tool or runtime edit was executed by Agent C.
''',encoding='utf-8')
print(json.dumps({'quests':2,'contracts':20,'defects':1,'runtime_changes':False}))
