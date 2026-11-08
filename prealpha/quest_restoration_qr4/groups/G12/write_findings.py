from pathlib import Path
import sys,collections,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha
V=H/'verification_01';T=read(V/'tests.json');assert T['failed']==0;assert not(H/'results.json').exists()
E=['../../verification_01/source_pins.json','../../verification_01/graph_evidence.json','../../verification_01/tests.json']
def c(status,p,a=(),r=(),extra=()):return dict(status=status,proven=list(p),approved_differences=list(a),remaining=list(r),evidence=E+list(extra))
common_comm=[
 'Current U9 initializer25.Out1→79.In1 owns exact native Padre holocall; shared cleanup468.True→336.In42 invokes exact native padre_cleanup and336.Out42→474. Common U9 support/studio proof is reused by frozen G09 core/source hashes; Padre protocol is independently checked.',
 'Native controller32 consumes start_activate>0→33 increments pending count→34 clears request→35;36 arbitrates idle holo setup→28→10 decrements count→scene0.start. End3→11 clears end request→scene0.end. Real scene acknowledgements are41 start_done1 and42 end_done1; original rejected/interrupted/reset_counter mechanisms remain, with no synthetic acknowledgements or counter reset.',
 'Brief/debrief caller scenes retain native positive start/end producers and done wait/clear. Debrief retry producers are in loops whose acknowledgement listener was already armed by a parallel fork; retry producer need not have a direct path to that wait. Native cut-control cancels retry on real acknowledgement. All10 scene request producers across these two gigs are traced with actual source identifiers.'
]
common_owner=[
 'Private entry retains original selected district node IDs, sockets and copied nested graph; main points to native body. Native district had Embedded resource handles while adapter uses standalone Soft counterparts. All six embedded native bodies compare equal after only explicit handle-flag/platform envelope relocation; native root prefabs, every gameplay node and edge are retained.',
 'Actual entry65002 requires genuine completed Tower, native unused start/terminal facts, U9 support, Request1/Permit1/ParentEntered0/Fault0 and inactive legacy B7/U6/U7 owner receipts. ParentEntered65003 precedes native parent gating; Started65004 precedes main; MainFinished/OwnerFinished follow its output. Credit and map slices claim their own one-time Entered facts.'
]
limits_owner=['CONDITIONAL: Original saved native/private descendants, phase-prefab leases and cross-version receipt adoption are not decoded from a save. Structural original ancestry and unused receipts are stronger than killed flags alone but do not observe live retirement.']
Q={}
Q['sts_hey_gle_06']={
 'entry':c('APPROVED_DEVIATION',[
  'Private entry0→65000Ready→65001Revision→65002guard→65003ParentEntered→native6.In1.6.Out1→62 fans to59 tier_1_1>0 and61 tier_1_1==0 AND tier_1>0; native XOR58→68 POI.Active→65004Started→8 native main. Native output8→65005MainFinished→65006OwnerFinished.',
  'Original district selected payloads and all copied nested graphs are exact after explicit Embedded→Soft body relocation; no new generic gig or forced entry replaces native parent6.'
 ],['Existing U9 bounded post-Tower parent/map/credit rehosting and exact native standalone-body externalization.'],['LIVE_ONLY: ArchiveXL activation and actual parent/tier/trigger execution are not observed.'],['../../verification_01/embedded_parity.json']),
 'eligibility':c('PASS',[
  'Current NativeGigDataU9 identity is discovered from the actual IDs array (index5), not historical quest counts. EntrySafe requires13 listed root/phase/objective/description states Inactive and11 native gig facts0, including alarm/car-segment/complete/end/finished/kill-all/scenes-end/soft/start/succeed/test. Every local native gle_06_ writer is covered by that fact set.',
  'Actual parent tier conditions remain XOR alternatives, not AND: tier_1_1>0 versus tier_1_1==0 AND tier_1>0. Native body12 checks finished before entering gameplay/openworld. POI Inactive OR Active is legitimate; native delivery-car mappin child is not misclassified as an unused-quest prerequisite.'
 ],r=['LIVE_ONLY: Prior entitlement/certificate, actual actor/vehicle state and current tier values are unobserved. PASS is bounded source predicate coverage, not save eligibility.'],extra=['../../verification_01/admissions.json','../../verification_01/journal_omissions.json']),
 'communications':c('PASS',common_comm+[
  'Native openworld root/0 scene175 Start0 has HolocallRET→177 start request, INT→178 end request; End0/rejected_out proceeds174.Active. root/2 debrief21 similarly RET→23 and INT→22, with rejected branch57 and original scene-outside43 retained.',
  'Brief scene66/67 and debrief94/95/268 are actual positive request writers. Retry268 loops through native3.2-second/idle/content-lock conditions, while parallel282 already waits real start_done;282→270 cut→89 clear. No missing-listener race is inferred from the retry branch alone.'
 ],r=['LIVE_ONLY: Actual phone playback, callback ordering, rejection/interrupt queues and studio rendering remain engine behavior.'],extra=['../../verification_01/protocols.json']),
 'ownership':c('CONDITIONAL',common_owner+[
  'Native main owns #sts_hey_gle_06_streetstory and delegates gameplay2/openworld3; no instance-prefab obligation was stripped by the externalization. Native own driver, vehicle, scenes, despawn/departure and cleanup paths remain under this original lifetime.',
  'Padre map0/map1 preserve padre_visited and finished checks, while map1 also preserves its native POI activation. They only run after Started1/MapPermit1 and each own MapNEntered0 latch; existing native mappin state is not reset to admit the job.'
 ],r=limits_owner),
 'progression':c('PASS',[
  'Native gameplay setup→simultaneous encounter/combat→native scene path and vehicle delivery remain unchanged. Openworld root/0 writes original start98, car-segment127, scene-end/finished117/137, and handles prebrief/rejected/interrupted branches; root/1 scene callbacks still write scenes_end/end.',
  'Native root/2 waits actual journal outcome after debrief/rejection.24 tests root Succeeded: True grants5 completion reward→37 gle_06_succeed1 and also2 gle_06_complete1→6 finished1; False takes complete/finished path without success reward/fact. Finished is not incorrectly equated to successful delivery.'
 ],r=['LIVE_ONLY: Native vehicle damage, upload, garage/driver movement, combat and scene choice timing are not simulated.']),
 'presentation':c('OPAQUE',[
  'Main native #sts_hey_gle_06_streetstory root is retained in embedded and standalone counterparts. Native scene cast remains 6thStreet, Repair, Forklift, 6thStreetGanger, Estevez and Jake_Car; first five use findInWorld and Jake_Car spawner. Two native workspots/two instances remain.',
  'Vehicle target, garage, prebrief/debrief world markers, animations, cameras and scene literals are inventoried. No replacement idle actors, generic car or custom reward vehicle were introduced.'
 ],r=['OPAQUE: Exact prefab/sector placement, findInWorld/spawner bindings, camera/workspot/vehicle definitions and current streamed entities remain unresolved.'],extra=['../../verification_01/dependencies.json']),
 'journal':c('PASS',[
  'Original reach_car, delicer_car, entergarage, uploaddata, leave/retrieve/talk/collect_reward/do_not_damage/exit_garage and brief paths remain. EntrySafe protects those13 source states. Native root outcome24 reads Succeeded before reward/succeed; failure is not rewritten as completion success.',
  'Omitted delicer_car/car targets are gameJournalQuestMapPin nodes203/204/210 and original bugfix mappin nodes, not omitted quest objectives. Their native activation/cleanup is preserved; active native map pins are not evidence of a replay defect.'
 ],r=['LIVE_ONLY: Target journal/localization definitions, rendered markers and player objective state remain distinct from preserved path/socket parity.'],extra=['../../verification_01/journal_omissions.json']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Native root/2 reward5 QuestRewards.sts_hey_gle_06_completion is gated by actual root Succeeded; success37 is downstream. Both terminal outcomes retain complete2/finished6 and original debrief, achievement, community/vehicle/scene-outside cleanup. No private second payout is added.',
  'Private credit claims CreditEntered1 before waiting original gle_06_finished>0, then original hey_sts_counter+1 with setExactValue0, then CreditDone1. It is not a counter reset or replay. Main and map/credit ownership receipts remain separate.',
  'Cross-quest timing is explicit: current S23 MQ044 preserves native minorquests148→150 three-game-day route. Original connected LifeWork bugfix9 instead tests mq_044_started_in_main only initially, then waits finished>=1 +one game day and invokes MQ044_main directly. Old OW three-day launch136 was deleted by230; it must not be revived.'
 ],r=['CONDITIONAL: Reward/TweakDB amounts and exactly-once engine delivery remain unproven.','EXACT_TIMING_OWNER_GAP: One-day corrective and three-day normal continuation are not proven equivalent after Tower. The corrective path has no late ownership recheck; blindly rehosting it could overlap current S23/old saved timers. WorkerC independently confirmed this distinction; no timing change or whole-bugfix replay is justified without scoped owner/timer evidence.'],extra=['../../timing_review_01/evidence.json']),
 'persistence':c('CONDITIONAL',[
  'Existing private/node/resource/fact IDs and all native body identities are unchanged. ParentEntered/Started/OwnerFinished, CreditEntered/Done and MapNEntered are preserved one-time receipts; completed/failed native histories and every listed used fact are not cleared.',
  'Native original partial-state bugfixes were inventoried with precise wait/condition routes. They are not all copied into a new owner. MQ044 main/reward/vehicle proof is reused from exact QR3 inputs; new elapsed-time history is not fabricated.'
 ],r=['CONDITIONAL: Exact saved active car/garage/scene owners, older receipt adoption, pending credit and timer transitions require fixtures. Already running MQ044/corrective waits cannot be restarted or shortened as a file-only repair.']),
 'shared_dependencies':c('CONDITIONAL',[
  'G09 shared U9 support proof is reused after exact current common binary hashes match. Padre original initializer/controller/cleanup and real acknowledgements are checked separately. Original district, Padre map and global counter donors are pinned through U9/B7 source manifests.',
  'LifeWork finished versus succeed feeds the actual Jake/Reyes branch in native MQ044. Exact QR3 proof retains earned finished prerequisite, native outcome-based SMS and original reward/vehicle; no fake success is created to select Jake.',
  'The separate one-day corrective bootstrap and deleted OW136 are explicitly investigated in timing_review_01. Native helper presence is not treated as restored execution or timing proof.'
 ],r=['CONDITIONAL: Corrective/normal timer arbitration and saved owner provenance remain unresolved. Native donor provider precedence and all world/TDB target definitions are not newly recertified by historical source presence.'],extra=['../../timing_review_01/evidence.json','../../verification_01/dependencies.json'])}
Q['sts_hey_gle_01']={
 'entry':c('APPROVED_DEVIATION',[
  'Private0→65000Ready→65001Revision→65002guard→65003ParentEntered→11 tier phase.In1. Native11.Out1 fans to41 and53; their AND54 feeds49 POI.Active→65004Started→5 native main. Original36→40 POI.Active→Started branch remains as in the district recipe. Main5.Out1→MainFinished65005→OwnerFinished65006.',
  'Target main5 and copied tier11 are exact original district payloads after explicit Embedded→Soft externalization. All four EyeForAnEye body/encounter embedded counterparts retain their gameplay graphs and root support.'
 ],['Existing U9 bounded post-Tower parent/map/credit rehosting and exact native standalone-body externalization.'],['LIVE_ONLY: Actual tier/POI/trigger scheduler execution remains unobserved.'],['../../verification_01/embedded_parity.json']),
 'eligibility':c('CONDITIONAL',[
  'Actual serialized guard protects native start/failed/finished0, genuine Tower/U9, Request/Permit and unused native/private legacy receipts. Current NativeGigData index17 is discovered from source IDs. EntrySafe protects11 listed native journal states and18 listed native facts; every local gle_01_ fact writer is covered, including kill/spare/delivery/offers/dialogue/grapple/failure.',
  'Native tier11 child requires sts_hey_gle_tier_2>0. POI Inactive OR Active is permitted; four delivery/exit child map pins are not treated as freshness requirements.',
  'accept_tucker_offer objective is omitted from EntrySafe. In current bounded native closure its only uses are root/3/15224 reads Active→4.Failed and root/3/18277 reads Active→3.Inactive. No current Active writer is present. This does not demonstrate a source-confirmed eligible replay state, and no guessed guard/reset was added.'
 ],r=['CONDITIONAL: Historical/saved provenance of omitted accept_tucker_offer and external writers is not proven. Original journal-definition/transition evidence is needed before treating its omission as safe for every save or as an actionable defect.','LIVE_ONLY: Current target/worker/car ownership and actual HS1/admission history are not read from a save.'],extra=['../../verification_01/admissions.json','../../verification_01/journal_omissions.json']),
 'communications':c('PASS',common_comm+[
  'Native streetstory root/3 scene209 Start0 has RET→213 start request and INT→214 end request; End0/rejected_out continues106.Active, with scene-outside250/251/252 preserved. root/5 scene21 Start1 uses RET→35 and INT→36; native rejected branch73 selects actual spare/deliver/kill/fail outcome.',
  'Brief scene68/69 and debrief113/114/264 are actual positive request writers. Debrief retry264 has a prearmed parallel real-ack listener and cut cleanup, preserved without adding synthetic callback flags.'
 ],r=['LIVE_ONLY: Phone playback, native rejected/interrupted branch arbitration and UI delivery remain engine behavior.'],extra=['../../verification_01/protocols.json']),
 'ownership':c('CONDITIONAL',common_owner+[
  'Native main owns #sts_hey_gle_01_streetstory and launches original combat11 and streetstory12 plus helper monitors. Streetstory owns original target negotiation, kill/nonlethal/transport, reward and debrief cleanup; no second generic Tucker actor is spawned.',
  'Map0 preserves padre_visited, native finished gate and helper60→50.Active. Credit waits either native finished OR failed through original XOR18; it does not require both mutually exclusive outcomes.'
 ],r=limits_owner),
 'progression':c('PASS',[
  'Native streetstory root3.OutKilled→6 normal completion reward and3.Outdefeted→7 pacifist completion reward both→8→19 finished→9→cleanup5. Separate failed3→25 remains; no branch is promoted to success. Exact target result writers are root/3 kill203,spare204,delivery205.',
  'Native offer/transport phases152/154/182 preserve offer_taken, target/car handling and objective cleanup. Failed190 waits actual Tucker talking1 and native encounter/reaction path before failed9→car_move25. Debrief73 selects actual spared/delivered/killed/failed conditions65..68; original achievement and cleanup remain.'
 ],r=['LIVE_ONLY: Tucker negotiation, nonlethal transport, combat, target mortality and car arrival/reaction timing require gameplay.']),
 'presentation':c('OPAQUE',[
  'Native #sts_hey_gle_01_streetstory root is retained. Encounter scene keeps Enemy1/Worker community actors; Tucker scene keeps community tucker, five workspots/eight instances. Exact scene, target/body/car/garage, prebrief/debrief marker and camera references are pinned.',
  'Native actions/reactions, worker overheads, Tucker dialogue and handling remain under original resources. No arbitrary AI/device command or reset-kill-count substitute was introduced.'
 ],r=['OPAQUE: Exact sector/actor/community/car/body/workspot/camera/animation definitions and current streamed owner leases are not resolved.'],extra=['../../verification_01/dependencies.json']),
 'journal':c('PASS',[
  'Original root/phase/exit/access/get-through/eliminate/deliver/talk/exit-with-body/get-money/brief targets are retained and listed EntrySafe protects their untouched states. Native success and failure outcome routes remain distinct.',
  'Omitted child delivery/exit targets are actual gameJournalQuestMapPin nodes58/61/62/65. Omitted accept_tucker_offer has exact read/cleanup routes recorded, with no current Active writer in the local native closure. No journal state was reset to reduce this uncertainty.'
 ],r=['CONDITIONAL: The old objective’s historical/saved lifecycle remains an admission limitation, separately flagged under eligibility. Journal target definitions/localization and rendered states remain unverified.'],extra=['../../verification_01/journal_omissions.json']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Actual killed route6 grants QuestRewards.sts_hey_gle_01_completion; defeated route7 grants QuestRewards.sts_hey_gle_01_completion_pacifist. Both join native finished19 then original debrief and cleanup5. Failed route25 avoids those success rewards and selects failure debrief. Native source determines target/body/offer outcomes, not private receipts.',
  'Private credit latches CreditEntered before waiting native finished6 OR failed17 at XOR18, then increments hey_sts_counter+1 and CreditDone. Duplicate one-time credit is prevented by existing private entered/done guards; no counter/reward/history reset is added.'
 ],r=['CONDITIONAL: Reward/TweakDB amounts, nonlethal/body delivery world state and engine exactly-once reward/credit/cleanup transitions require fixtures.']),
 'persistence':c('CONDITIONAL',[
  'All existing private and native saved node/resource/fact identities remain. Used outcome/offer/dialogue/grapple facts and listed progressed journals prevent intentional replay; old B7/U6/U7 owners are excluded. Credit/map entry receipts persist rather than re-running payouts on reload.',
  'Original CYB-598725/CYB-646308 companion routes are inventoried as distinct native corrective owners; no whole-bugfix restart or quest/target reset was implemented.'
 ],r=['CONDITIONAL: Saved target/worker/car and corrective-owner adoption, omitted old-objective history and active reward/credit/cleanup transition fixtures remain absent.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Exact original district entry, Padre map branch, global hey counter credit, native body/scenes and current U9 listener/cleanup are pinned. All local decoded graphs have no structural errors. Common studio and owned support proof is reused only by matching hashes.',
  'Every local native quest-prefixed fact writer is in current EntrySafe. Native actor, journal, target/body/car, reward and phone dependencies remain separate; literal references are not promoted to resolved definitions.'
 ],r=['CONDITIONAL: Saved legacy/default/corrective owner leases and historical accept-offer state remain unresolved. Native target/provider/world/TDB definitions require additional evidence; no blanket static/gameplay PASS.'],extra=['../../verification_01/dependencies.json'])}
names={I.Q[0]:"Life's Work",I.Q[1]:'Eye for an Eye'};rows=[];counts=collections.Counter()
for q,cs in Q.items():
 assert len(cs)==10;p=H/'quests'/q/'contracts.json';write(p,{'quest_id':q,'title':names[q],'source_epoch':'QR3 candidate_01 epoch00','status':'DEEP_REVIEWED_CONDITIONAL','fully_static_verified':False,'defects':[],'repairs':[],'contracts':cs});ss=collections.Counter(x['status']for x in cs.values());counts.update(ss);rows.append({'quest_id':q,'contracts':str(p),'contracts_sha256':sha(p),'status_counts':dict(ss)})
 lines=['# '+names[q]+' — '+q,'','Source-specific ten-contract review; no confirmed new runtime defect or repair.','']
 for k,x in cs.items():
  lines+=['## '+k+' — '+x['status'],'']+['- '+z for z in x['proven']]+['']
  if x['approved_differences']:lines+=['Approved differences:']+['- '+z for z in x['approved_differences']]+['']
  if x['remaining']:lines+=['Remaining:']+['- '+z for z in x['remaining']]+['']
 (p.parent/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
epoch=I.W/'prealpha/quest_restoration_qr4/source_epoch_00.json'
write(H/'results.json',{'group':'G12','quest_ids':list(Q),'quests':rows,'tests':str(V/'tests.json'),'tests_sha256':sha(V/'tests.json'),'source_pins':str(V/'source_pins.json'),'checks':T['total_checks'],'mutations':T['total_mutations'],'shared_checks_reused':T['shared_core']['checks_reused'],'timing_review':{'path':str(H/'timing_review_01/evidence.json'),'sha256':sha(H/'timing_review_01/evidence.json'),'checks':6,'status':'CONDITIONAL_OWNER_TIMER_GAP_NOT_A_BLIND_REHOST'},'confirmed_unique_defects':0,'runtime_changes':[],'source_epoch':{'path':str(epoch),'sha256':sha(epoch)}})
write(H/'approved_differences.json',{'source_epoch_sha256':sha(epoch),'differences':[{'quest_id':q,'contract':k,'difference':d,'source_pins':str(V/'source_pins.json'),'source_pins_sha256':sha(V/'source_pins.json')}for q,cs in Q.items()for k,x in cs.items()for d in x['approved_differences']]})
write(H/'verification_corrections.json',{'runtime_changes':[],'corrections':['Native district embeds gameplay; current adapter uses standalone Soft handles. Six embedded/standalone bodies independently compared, with only resource-handle flags and cooking platform envelope allowed; no gameplay differences suppressed.','Native debrief retry producers use an ACK wait already armed in parallel. Auditor now requires connected fork, live ACK branch and native cut cleanup; direct retry→wait was an invalid assumption.','Native recipe JSON pin is transitive through U9-pinned B7 build_plan for district source; exact source hash validated, not assumed missing.']})
(H/'REPORT.md').write_text('''# G12 — Two Padre gigs

Life’s Work and Eye for an Eye have20source-specific contract dispositions. No source-confirmed runtime repair is justified. The original one-day LifeWork corrective MQ044 fallback versus current three-day normal S23 route is an explicit conditional owner/timer gap; workerC independently checked its initial-only ownership test and deleted old launch136. Blind rehosting/timer edits would risk duplicate owners or lost saved time.

194focused checks,6actual decoded-copy mutations and6timing-route checks pass. Thirty-one primary resources are pinned;38common U9 checks are reused by matching hashes. All six embedded/standalone gameplay counterparts, original parent/tier/map/counter recipes,10Padre request producers, real acknowledgements, cleanup, original target/delivery/reward branches and EntrySafe fact-writer coverage are checked.

EntrySafe’s omitted LifeWork car targets are map pins. EyeForAnEye’s omitted accept_tucker_offer is an objective with only read/cleanup uses in the inspected native closure; no current Active writer was found, so saved historical provenance remains conditional rather than a guessed patch. Neither quest is fully statically resolved. World/TDB/target definitions and saved owner/receipt/engine transitions remain explicit.

Reproduce only into a new directory:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -B 'prealpha\\quest_restoration_qr4\\groups\\G12\\verify.py' --output 'prealpha\\quest_restoration_qr4\\groups\\G12\\verification_next'
```

No runtime/game/save/fact/deployment files were changed. Source epoch00 remains the investigation baseline.
''',encoding='utf8')
print(json.dumps({'quests':len(Q),'contracts':sum(counts.values()),'statuses':dict(counts),'checks':T['total_checks'],'mutations':T['total_mutations']}))
