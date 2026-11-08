from pathlib import Path
import sys,json,collections
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
test=read(O/'verification_02/tests.json');assert test['checks']==167
evidence=['../../verification_02/source_pins.json','../../verification_02/graph_evidence.json','../../verification_02/tests.json']
scripts={}
for name in ['PTFR_SideJobsS2.reds','PTFR_SideJobsS23.reds','PTFR_SideJobsS25.reds','PTFR_B0StoryZane.reds','PTFR_JohnnyVoiceJV1.reds']:
 p=W/'prealpha/phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated'/name
 scripts[str(p)]={'sha256':sha(p)}
write(O/'script_pins.json',scripts)
def item(status,proven,differences=(),remaining=(),ev=None):return {'status':status,'proven':list(proven),'approved_differences':list(differences),'remaining':list(remaining),'evidence':ev or evidence}
sharedlive='LIVE_ONLY: Actual saved owner retirement, interrupted scenes and restore/reload scheduling require matching runtime fixtures; no save was decoded or modified.'
qs={}
qs['mq030_melisa']={
 'entry':item('APPROVED_DEVIATION',[
 'Current wrapper starts1000->1001Ready->1002guard->1003PA2 pause->1010 QuestOwns1->1011 waits B0 released/inactive/outside ->native54(q001_done)->80(q005_done)->55(q101_enable_side_content)->1004 recheck.True->1005Issued->1006Entered.1006 starts18.In1 exact original MQ030 body and temporary vendor helper1020. False1004->1013 QuestOwns0->1002 rearms.',
 'Current18 phase payload equals native minorquests18. Native body0->43 initial encounter->63 Melisa quest->64 cleanup->83 followup messages->1 output is unmodified; second_meeting_in debug/resume entry is not used.'
 ],['Established S23/CR1 adds genuine Tower, U9, settled history and explicit B0 Zane lease handoff to a fresh native entry.'],['LIVE_ONLY: Activation/actual eligible fixture is not observed.']),
 'eligibility':item('APPROVED_DEVIATION',[
 'Both1002 and1004 require root/child journal freshness, native mq030 active/done/failed/kill_scene/maxtac/progress facts neutral, Permit1 and Issued/Finished/Fault0. Automated guards reject Active/Succeeded/Failed root, missing journal, used owner and non-Tower state.',
 'Exact native q001_done>0,q005_done>0,q101_enable_side_content>0 ancestor nodes54/80/55 are preserved. Current S23 Read/Ready uses defined settled journal/facts and repeated matching samples; no native state is reset to fabricate readiness.'
 ],['Fresh-only admission preserves progressed/completed/failed native histories and original prerequisites.'],['LIVE_ONLY: Current player history and safe sampling state are not inspected.']),
 'communications':item('PASS',[
 'Full native MQ030 closure has no positive audio/holo phone request producer. No caller/listener acknowledgement repair is required for this quest. Native face-to-face Melisa/MaxTac scene is referenced unchanged.',
 'Real native SMS is root/83:2->3->4.Active contacts/zane/mq030_follow_up/mq030_01_msg_thanks ->7.Active gossip->12.Active choice;5 waits always choice,24 waits nah choice,29/31 and37/38 retain later response alternatives. Native failed17.True->18->19->20->21.Failed remains. Body does not return until authored followup branch has returned.'
 ],remaining=['LIVE_ONLY: SMS delivery, actual answers and conversation execution remain engine behavior. No phone test is requested.']),
 'ownership':item('FAIL',[
 'Initial handoff is explicit:1010 asserts B0 QuestOwns before1011 waits Released1/OwnerActive0/Inside0; temporary helper1020 and B0 owner5 each bind #pr_cct_dtn_cloth_01 and Activate #zane/zane_jagger.',
 'Confirmed faulty completion route:18.Out1->1007Finished1->1012 QuestOwns0 while1020.Out1->1021 default_on>0->1020.In1 remains armed. Native cleanup makes default_on positive. B0 root2 admits when QuestOwns0,Enabled1,default_on>0, even mq030_done1. Thus an old helper owner and newly admitted B0 owner may structurally overlap after completion.',
 'Current native helper root/1020 node3(default_on<1)->5 mappinInactive->1 Terminating provides a natural retirement acknowledgement. It currently does not observe the private completion fact; baseline retirement regression fails.'
 ],remaining=['IMPLEMENTATION: Root controls the acknowledged-retirement repair after independent review. Agent E changed no runtime resource.',sharedlive],ev=evidence+['../../verification_02/defect_mq030.json','../../verification_02/proposal_mq030.json']),
 'progression':item('PASS',[
 'Native root43 concurrently starts Jinguji community scene17 and waits12 mq030_zane_met>0 before enabling encounter9 active1 then10 default service off. No fresh adapter substitutes the second_meeting input.',
 'Native root63 invokes full Melisa phase, then cleanup64 resets active16,sets done17,restores native default service19 and Zane gratitude47 before original followup83. All native combat/scene/death branches, actor/crowd operations and original nested connections are byte-pinned.'
 ],remaining=['LIVE_ONLY: Cyberpsycho combat, MaxTac arrival and dialogue/performance execution are not simulated. The separate confirmed service-owner cleanup defect is not a native quest branch rewrite.']),
 'presentation':item('OPAQUE',[
 'Native MQ030 root retains #mq030_pr_melisa. Existing B0 and temporary service prefabs, Melisa/Jinguji scenes, actor bindings, NodeRefs and workspots are inventoried and unchanged. Fresh wrapper18 delegates the full native resource, including root prefab obligations.',
 'Recorded native source hashes and raw JSON/model equality establish graph/binding preservation; they do not prove actual world placement or prefab instance retirement.'
 ],remaining=['OPAQUE/CONDITIONAL: Full world-sector placement/variant/camera/workspot resolution and localization references have not been independently decoded. Shared studio opacity is inherited where applicable.','LIVE_ONLY: Visible actor duplication from the source-confirmed lease overlap, crowd/animation/rendering and streaming are runtime observations, not claimed results.']),
 'journal':item('PASS',[
 'Native MQ030 objective/point-of-interest and followup-message state writers retain exact paths and input sockets. Root/43 node24.Out->20.Active marks the encounter POI; root/83 failed17.True branch reaches quest21.Failed.',
 'Wrapper does not reset journals or synthesize success. Native scene/current branch and followup text remain original; wrapperFinished records body return, not fake quest success.'
 ],remaining=['LIVE_ONLY: Engine journal propagation and displayed markers/messages are not executed.']),
 'completion_rewards_cleanup':item('FAIL',[
 'Native scene553->814 grants QuestRewards.mq030_cyberpsycho_defeated;486->817 grants QuestRewards.mq030_testimony_given; original outcomes/record pointers are unchanged. Native root/64 restores default_on and sets done, preserving native actor/security cleanup.',
 'Private cleanup releases B0 lease at1012 before retiring helper1020 or pending rearm1021. This is the confirmed source defect; native gameplay reward nodes do not justify replay/reset or another spawn owner.'
 ],remaining=['IMPLEMENTATION: Root repair should release the lease only after helper natural Terminating output or a completed pending-wait decision; proposed two-decision graph preserves all old IDs.','CONDITIONAL: Exact QuestRewards target definitions/current providers and numeric outcomes remain unresolved.',sharedlive],ev=evidence+['../../verification_02/defect_mq030.json']),
 'persistence':item('FAIL',[
 'All current source hashes and saved node/resource identities are unchanged by this investigation. Issued receipt prevents fresh restart. Existing helper1020/1021 can remain executing when main18 returns, so a saved completed owner can retain the faulty helper/rearm scope.',
 'Proposed model preserves all old parent/helper IDs and introduces only1022/1023. Eight explicit symbolic fixtures cover active helper versus pending rearm, finished0/1 and default_on0/1; already-finished pending scope releases without reentering/spawn flash.'
 ],remaining=['IMPLEMENTATION: Proposed fixtures are not proof that a serialized patch or old saved pause reevaluates correctly; root serialization/readback and later saved transition validation are required.',sharedlive],ev=evidence+['../../verification_02/proposal_mq030.json']),
 'shared_dependencies':item('FAIL',[
 'Confirmed overlap affects B0 Jinguji/Zane default service, not the three QR2 quests. Competing scopes use identical #pr_cct_dtn_cloth_01 and #zane binding. B0 private root2 excludes QuestOwns1 but does not exclude mq030_done1, which is appropriate for restored postquest shop availability.',
 'Correct repair targets temporary helper retirement before lease release, retaining the ordinary B0 owner. It must not permanently hold the lease, force default_on changes, reset story facts or duplicate a replacement service.'
 ],remaining=['IMPLEMENTATION: Root coordinates independent review and actual successor; Agent E proposal is data-only and not an installed/cooked resource.','CONDITIONAL: Shared prefab/world semantics and live lease ordering remain additional limits.'],ev=evidence+['../../verification_02/defect_mq030.json'])}
qs['mq032_sacrum']={
 'entry':item('APPROVED_DEVIATION',[
 'Actual wrapper0->1000Ready->1001pause->native hubs81->83->84->1002 recheck.True->1003Issued->4.In1;4.Out1->1004Finished.4 payload exactly matches native minorquests4 and retains native mq032_sacrum resource. No nonlethal/lethal debug entry is used.',
 'Native root31->40 concurrently starts hook32.In1 and Maelstrom33.In1;hook32.Out1->33.hook_done. All original body inputs/outputs remain unchanged.'
 ],['S2 supplies Tower/U9/history/once-only guards before unchanged native beginning.'],['LIVE_ONLY: Actual activation remains unmeasured.']),
 'eligibility':item('APPROVED_DEVIATION',[
 'Actual1001/1002 predicates require native mq032 complete/dead/help/monk1_met neutrality and five bound journal states, Permit1/Issued0/Finished0/Fault0. Tests reject progressed roots, missing input, used owner and non-Tower.',
 'Current S2 policy retains certified/uncertified route distinction. Read resolves missing journal to-1 and SampleFresh rejects unavailable shapes/required states. Poll uses SnapshotStateHS1.Admits plus common/safety gates and grants only AuthorizedRoute1/2; it never pretends current Inactive observations prove pre-Tower history.'
 ],['Established conservative fresh-only S2 route retains original native availability and histories.'],['LIVE_ONLY: Actual captured/certified/current-history route and player eligibility are save inputs.']),
 'communications':item('PASS',[
 'Complete inspected native MQ032 phase/scene closure has no positive audio/holo start/end request producer and no external phase/scene outside this quest closure. Monk hook, rescue and epilogue are face-to-face native scenes, preserved as authored.',
 'No missing phone listener, acknowledgement or cleanup is inferred from the quest title or unrelated controller inventory. No synthetic communication facts are written.'
 ],remaining=['LIVE_ONLY: Dialogue choices, actor speech and UI remain unexecuted.']),
 'ownership':item('CONDITIONAL',[
 'Wrapper binds original minorquests4 payload and full native root prefab #mq032_pr_sacrum. Source ancestry is the genuine Tower-terminated native main/minorquests tree already verified in QR2; current Issued guard prevents fresh duplication.',
 'Native branch ownership is kept within the original root. No arbitrary Reactivate/ResetKillCount or outside fight controller is introduced.'
 ],remaining=['CONDITIONAL: Matching saved original/private descendants and older executing-owner adoption are not inspected.',sharedlive]),
 'progression':item('PASS',[
 'Actual native hook32.Out1->33.hook_done remains alongside initial33.In1.33.Success->34.Success and33.Fail->34.Fail retain nonlethal/lethal and failed rescue epilogue semantics.34.Out1 returns native1.',
 'Native epilogue Success0 andFail2 branches, dead4 condition, scene13/15 outputs and final28.Out2->29(mq032_complete1) are preserved. No choice, mortality or combat branch is flattened.'
 ],remaining=['LIVE_ONLY: Kill/nonlethal classification, rescue interaction and combat/scene completion require actual execution.']),
 'presentation':item('OPAQUE',[
 'Root#mq032_pr_sacrum and full hook/Maelstrom/epilogue/combat scene/workspot/actor/NodeRef tables are pinned and retained. Private wrapper does not waive native root prefab ownership by having no own prefabs.',
 'Native actor/presentation resources remain unmodified; approved voice-only Johnny presentation depends on the existing JV1 policy, not a new restoration of his engram.'
 ],remaining=['OPAQUE/CONDITIONAL: World-sector/prefab/variant placement, camera/workspot and localized asset resolution are not fully decoded here.','LIVE_ONLY: Rendered actors, voice and scene animation behavior remain separate.']),
 'journal':item('PASS',[
 'Original monk quest/POI/objective state writers and Success/Fail input sockets are retained throughout hook, Maelstrom and epilogue. All exact journal paths and incoming edges are in graph_evidence; no wrapper journal writer exists.',
 'The wrapper records Finished only after native body output. It does not mark quest Succeeded independently or clear a failed root.'
 ],remaining=['LIVE_ONLY: Journal propagation/notifications are engine dependent.']),
 'completion_rewards_cleanup':item('CONDITIONAL',[
 'Native Maelstrom scene236->463 grants exact QuestRewards.mq032_done. Native epilogue routes return through original cleanup and mq032_complete receipt29; all reward/corpse/combat/actor cleanup paths remain native.',
 'No new reward/item/counter/reset command is introduced by S2 wrapper. Kill-versus-nonlethal consequences remain authored.'
 ],remaining=['CONDITIONAL: Exact QuestRewards.mq032_done data definition/current overrides and any loot entitlement data are not resolved by graph equality.','LIVE_ONLY: Exactly-once rewards, corpse/actor cleanup and reload transaction behavior remain untested.']),
 'persistence':item('CONDITIONAL',[
 'No saved field/resource/node/name change. Actual Issued1003 precedes native4; both guard nodes require Issued0 and noncompleted history. Original native children retain their saved identity paths.',
 'S2 Restore resets preissue Permit/AuthorizedRoute only and never Issued; current source preserves persisted schema/catalogue/history distinction.'
 ],remaining=['CONDITIONAL: No old-save transition/paused descendant fixture is decoded; current source identity preservation is not save-upgrade gameplay proof.',sharedlive]),
 'shared_dependencies':item('CONDITIONAL',[
 'Current source uses original minorquests hubs81/83/84 and full native body; no shared MaxTac/Zane owner or Prophet/NCPD owner is added for MQ032. U9/common/profile/history dependencies stay required.',
 'Source-confirmed MQ030 lease defect is in a separate service wrapper and does not alter monk progression; no shared-system fix is generalized without evidence.'
 ],remaining=['CONDITIONAL: Shared world and saved-root lifecycle resolution remains bounded; actual engine scheduling is LIVE_ONLY.'])}
qs['mq026_conspiracy']={
 'entry':item('APPROVED_DEVIATION',[
 'Both S23 historical seam and S25 fresh wrapper use1000->1001Ready->1002pause->1003PA2->1004recheck.True->1005Issued->1006Entered->39.In1 exact native MQ026 body;native39.Out1->1007Finished. Both39 payloads equal native minorquests39. Debug combat/death/conspiracy inputs are not substituted.',
 'Native In1 retains0->3 mq026_started1->103 mq027_50_prophet0->4 mq026_active1, then original debug/trigger/donation/prophecy/cargo/death loop. S25 never fabricates native gates itself.'
 ],['Established S25 fresh and S23 exact captured-seam entries retain original quest behavior with separate owned receipts.'],['LIVE_ONLY: Actual eligible seam/activation is not observed.']),
 'eligibility':item('APPROVED_DEVIATION',[
 'Serialized S23 demands active1,started1,first_conspiracy_done1,lilith_done1,lookat_loop1,stop_preach1 and17 Inactive journal entries. S25 fresh instead requires those completed/loop flags0 while active/started are bounded0..1. All remaining progress/choice/outcome facts remain neutral.',
 'Tests prove both seam dictionaries exclude the other adapter; S23 checks S25FreshIssued0 and S25 checks S23Issued0. Actual reciprocal receipt guards and disjoint native progress predicates prevent the assumed same-seam race; this is not inferred from fact names.',
 'Missing/progressed root, prior owner and non-Tower cases are explicitly rejected. Current S23/S25 producers use defined settled history and repeated samples; no reset/admit of unsupported partial history is introduced.'
 ],['Only the exact approved early seam may resume; unverified other unfinished states defer.'],['LIVE_ONLY: Current donations/prophecies/history state is not read from a save.']),
 'communications':item('PASS',[
 'Complete inspected MQ026 native phase/scene closure has no positive audio/holo phone request producer and no external graph phase/scene reference outside MQ026. Prophet dialogue, donations, nomad confrontation and smuggler/death conversations are native local scenes.',
 'The separately inventoried conspiracy holocall resource is not treated as proof of an active MQ026 call; no missing-listener repair is invented. Original choices and journal/message activation remain native.'
 ],remaining=['LIVE_ONLY: Speech, choice delivery and any engine/UI communication behavior remain unexecuted.']),
 'ownership':item('CONDITIONAL',[
 'Native root retains #mq026_pr_prophet_trigger and inline prophet prefab45. Wrapper39 matches native parent and preserves original body/owners. Fresh and historical wrappers are mutually exclusive in tested predicates and check reciprocal Issued receipts.',
 'Original genuine Tower main-tree termination ancestry is reused; no standalone old bugfix owner or encounter is restarted merely because its resource remains on disk.'
 ],remaining=['CONDITIONAL: Saved actor/old native descendants and owner retirement/adoption at the captured seam are not decoded.',sharedlive]),
 'progression':item('PASS',[
 'Native root initializes started/active then routes through prophet_spawn trigger41, beaten95, disturbed53, local prophecy phase33, cargo36 and death37. combat_out and killed_out branches and native CutControl69 are preserved.',
 'Native done6 follows active5=0 and continues original failed/journal cleanup. Donations, prophecy counters, handover/chip and nomad/smuggler outcomes remain authored; S25 adds no quest progress writer.'
 ],remaining=['LIVE_ONLY: Actual donations, dialogue sequences, cargo ambush/stealth/combat and actor deaths require runtime execution.']),
 'presentation':item('OPAQUE',[
 'Native root#mq026_pr_prophet_trigger plus inline prophet45 and cargo/death prefab/scene/camera/workspot/NodeRefs are retained. Full source pins and graph bindings are recorded, including the shared Kabuki NCPD resource.',
 'Existing JV1 voice-only compromise applies where native supporting Johnny actor resources are referenced; no visual engram/takeover restoration is added.'
 ],remaining=['OPAQUE/CONDITIONAL: World-sector/variant/actor and language-specific presentation resolution are not independently fully decoded. Graph presence/hash equivalence is not placement proof.','LIVE_ONLY: Johnny visual suppression, independent props and scene rendering remain unobserved.']),
 'journal':item('PASS',[
 'All17 bound root/stash/objective/description entries are retained in both admission guards. Original branch state writers and their incoming Failed/Active/Succeeded sockets remain in native corpus, with no private journal reset.',
 'Native failure cases for beaten prophet and cargo/nomad/death choices remain; wrappers record only owned body-return receipts.'
 ],remaining=['LIVE_ONLY: Journal display/propagation and exact player choices are not inspected.']),
 'completion_rewards_cleanup':item('CONDITIONAL',[
 'Native death scene227->230 grants exact QuestRewards.mq026_done; original reward continuation to250/563 remains. Native cleanup5 active0->6done1, CutControl69 and original scene/actor/community cleanup remain.',
 'Private adapters add no rewards, fake acknowledgement or outcome reset. Early native startup idempotent writes are delegated through original In1 only for the specific verified seamed state.'
 ],remaining=['CONDITIONAL: QuestRewards.mq026_done and chip/loot entitlement definitions/current providers are not independently resolved.','LIVE_ONLY: Exactly-once inventory/reward delivery and interrupt/cleanup behavior remain untested.']),
 'persistence':item('CONDITIONAL',[
 'All original private/native identities and receipts are unchanged. Actual reciprocal Issued checks block a second fresh owner, and the tested historical/fresh native progress states are disjoint.',
 'S23/S25 preserve existing Issued owners during Restore/Poll and do not clear native progress. Other partially progressed states are not promoted into fresh eligibility.'
 ],remaining=['CONDITIONAL: Saved executing-owner capture for the historical seam and old-version upgrade fixtures remain unavailable.',sharedlive]),
 'shared_dependencies':item('CONDITIONAL',[
 'Shared Kabuki ma_wat_kab_06 native and N2 private controller are inventoried; N2 admission requires unstarted/uncompleted scanner and its own support/receipt, preserving native payload/fact references. No Prophet patch modifies the scanner.',
 'The exact interaction/ownership between shared world encounter, Prophet phase and NCPD stream is kept visible instead of assuming resource overlap proves a defect. Current MQ030 Zane defect is unrelated and is not generalized.'
 ],remaining=['CONDITIONAL: Full saved and world-placement lease semantics for ma_wat_kab_06 and Prophet actors/loot must be correlated before complete shared-owner certification.','LIVE_ONLY: Concurrent encounter/scanner progression and cleanup arbitration remain unobserved.'])}
for q,contracts in qs.items():
 assert len(contracts)==10
 dest=O/'quests'/q;assert not (dest/'contracts.json').exists();dest.mkdir(parents=True,exist_ok=True)
 defects=[read(O/'verification_02/defect_mq030.json')] if q=='mq030_melisa' else []
 write(dest/'contracts.json',{'quest_id':q,'title':{'mq030_melisa':'Bullets','mq032_sacrum':'Sacrum Profanum / Losing My Religion','mq026_conspiracy':"The Prophet's Song"}[q],'status':'CONFIRMED_DEFECT_PENDING_ROOT_REPAIR' if defects else 'DEEP_REVIEWED_WITH_STATIC_LIMITS','static_verified':False,'defects':defects,'repairs':[],'contracts':contracts,'tests':'../../verification_02/tests.json','scope':'Current PH3 baseline. Root may add a separate repaired-successor adjudication; baseline findings remain immutable.'})
counts=collections.Counter(v['status'] for cs in qs.values() for v in cs.values())
write(O/'result.json',{'agent':'agent_e','quest_ids':list(qs),'contract_status_counts':dict(counts),'tests':str(O/'verification_02/tests.json'),'confirmed_defects':['QR3-E-MQ030-LEASE'],'repairs':[],'runtime_changes':[],'proposal':str(O/'verification_02/proposal_mq030.json'),'note':'Investigation controls PASS; MQ030 current lifecycle regression intentionally FAILS until root repair. No speculative change to MQ026/MQ032.'})
(O/'REPORT.md').write_text('''# Agent E — Bullets, Sacrum Profanum and The Prophet's Song

All30 contracts investigated. **One source-confirmed MQ030 service-owner defect; root controls independent review and repair.** No runtime resource was modified by Agent E.

- **Bullets:** Original q001/q005/q101 prerequisites, native Melisa/MaxTac stages, SMS choices and reward branches are preserved. Confirmed postcompletion lifecycle defect: native body18.Out1 sets private Finished1007 then releases B0 Zane lease1012 while temporary vendor helper1020/rearm1021 remain alive. Both it and B0 node5 bind `#pr_cct_dtn_cloth_01`. The re-admitted B0 guard has no mq030_done exclusion, as expected for normal postquest shop availability. [Exact failing route](verification_02/defect_mq030.json).
- **Sacrum Profanum:** Original parent4, native hook/Maelstrom parallel startup, Success/Fail rescue branches and epilogue/reward routes are preserved. No defect established; actual world bindings, reward record and saved owner transitions remain conditional.
- **The Prophet's Song:** Exact native body39 and fresh/historical seams remain. Guards are mutually exclusive by native progress constants and reciprocal Issued facts. No presumed duplicate-admission patch is warranted. Original Prophet/cargo/death/dialogue/reward paths remain. Shared Kabuki scanner/world ownership still needs saved/placement correlation.

All three inspected native graph closures contain **no positive audio/holo call request producer**. Bullets' real postquest Zane SMS branch is explicitly traced; unrelated `conspiracy_holocall` presence is not turned into a missing-call claim.

## Evidence and proposal

[Final tests](verification_02/tests.json): **167 focused checks passed**, including five mutations and32 binary/raw-JSON/model pins. This PASS describes the investigation controls: the separately named current MQ030 retirement regression is **false**, while the proposed acknowledged-retirement model is true. Earlier verification_01 is preserved.

[Proposal](verification_02/proposal_mq030.json) stops the active helper using its existing native `3 ->5 ->1.Terminating` output before releasing the B0 lease. Separate Finished decisions1022/1023 handle natural helper return and pending rearm; completed pending scope does not reenter/spawn. Eight symbolic fixtures cover active/pending scopes, Finished0/1 and native default_on0/1; all old node IDs remain. It is data-only, not a cooked resource or an accepted deployment. The parent coordinator and a separate reviewer own serialization, independent review and final accepted regression.

Per-quest results are in `quests/<id>/contracts.json`; [graph evidence](verification_02/graph_evidence.json) includes exact node/socket/fact/journal/reward and prefab bindings; [source pins](verification_02/source_pins.json) bind originals/current PH3; [script pins](script_pins.json) bind current producer/lifecycle code.

Reproduce with Python `-B` and `verify.py --output <fresh-directory>` from repository root. Existing output directories are refused. The verifier imports only pure audit parsing utilities, not builders/installers.

No quest is fully STATIC_VERIFIED. Unresolved reward/loot record definitions, opaque/unmapped world/actor/prefab/workspot/variant/localization semantics and exact saved-owner migration remain explicit. Combat, speech, UI, reward delivery, interruption and save/reload execution are LIVE_ONLY. Game, saves/facts, release artifacts, common queue and other agents' output files were untouched.
''',encoding='utf-8')
print(json.dumps({'quests':list(qs),'contracts':30,'status_counts':dict(counts),'confirmed_defects':1,'runtime_changes':0}))
