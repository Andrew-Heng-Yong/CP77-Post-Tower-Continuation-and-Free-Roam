"""Emit G06 adjudications from the bounded investigation, never runtime resources."""
from pathlib import Path
import sys,collections,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha
V=H/'verification_02';T=read(V/'tests.json');assert T['failed']==0
assert not (H/'results.json').exists(),'Preserve issued findings'
E=['../../verification_02/source_pins.json','../../verification_02/graph_evidence.json','../../verification_02/scene_evidence.json','../../verification_02/tests.json']
def c(status,proven,approved=(),remaining=(),extra=()):return dict(status=status,proven=list(proven),approved_differences=list(approved),remaining=list(remaining),evidence=E+list(extra))
Q={}
Q['mq005_alley']={
 'entry':c('APPROVED_DEVIATION',[
  'Exact CR1 selected owner SHA C037E2C9…75A6AF4F is retained. Actual private owner0→400Ready→401NativeRevision→402.Inactive guard→403Started→405.In1 native_owner;405.Out1→404OwnerFinished→1. The historical Happy Together donor title is wrong: serialized identity is mq005_alley, Only Pain.',
  'S23 Poll arms the existing SideJobPilotS1.RestoreFresh after two eligible ticks, HS1 admission, current root Inactive and ready/revision/no-issued receipts. RestoreFresh refuses an already-enabled saved adapter; Poll re-runs Preflight before writing Request1. It adds no second street controller.'
 ],['Private post-Tower rehosting after genuine ending cleanup; the exact current CR1 repaired Inactive guard is preserved.'],['LIVE_ONLY: ArchiveXL registration firing and live scheduler ordering are not observed.']),
 'eligibility':c('PASS',[
  'Native minorquests parent19 inherits q001_done>0→q005_done>0→q101_enable_side_content>0. All three are present in actual402 AND and S1 NativeEligibility. Current root must be Inactive, wanted_level0 and seven native encounter/scene facts zero, including admission-of-guilt/full-story/block-punch flags.',
  'Script UntouchedStage checks all six native quest/phase/objective/description entries Inactive and no delayed journal changes; Preflight also requires POI Inactive/Active, Tower/2079/main-game-killed/EP1-killed, own Ready1/NativeRevision1 and Request/Started/RewardClaim/RewardAck/ReplayRefused/OwnerFinished/Fault0. Completed, Failed and Active roots are rejected by actual serialized402 negative fixtures.'
 ],remaining=['LIVE_ONLY: Actual historical HS1 certificate and player eligibility are not read from a save; PASS concerns these exact static admission predicates.']),
 'communications':c('PASS',[
  'Bounded native MQ005 main/combat/alley/passout and private S1 dependency closure contains zero holo_/audio_ request or acknowledgement reads/writes and zero Phone/SMS nodes. Alley uses direct scene Start_in and Wrapup_in; no external holocall listener/acknowledgement is required by these local resources.'
 ],remaining=['LIVE_ONLY: Voice dialogue, presentation, scene interruption and barks require engine observation.'],extra=['../../verification_02/communications.json']),
 'ownership':c('CONDITIONAL',[
  'Private native_owner keeps exact root #mq005_pr_alley and root init→main→cleanup lifetime. Native parent19 itself has no extra instance prefab. All native node identities/payloads are preserved except the combat depot relocation and reviewed cleanup conditions; native cleanup commands and AND join14 survive.',
  'The saved adapter stores enabled/schema/stage/inflight/fault. Restored faults unsupported/interrupted queue states; enabled prevents requeue. Request/Started and OwnerFinished receipts do not reset native progress. Cleanup receipt is emitted after native deactivation join, not used as a replacement owner retirement command.'
 ],remaining=['CONDITIONAL: q307 killed flags plus untouched journal are admission evidence, not proof of every old saved descendant retiring. No current saved owner tree or transition fixture was decoded. Native bugfix phases CYB-592021/CYB-648297/CYB-688402 were inventoried; their old saved execution/adoption is not proven.']),
 'progression':c('PASS',[
  'Private combat normalizes exactly to pinned native mq005_combat (21 nodes). Every unchanged native main/nested node and edge is compared, not merely counted. Retained routes include CombatFromInterruption/Combat_out→4, StreetKidSuccess_out→6, Ignored_out→7, CorpoKilledInCrossfire→19 and wrapup player_attack_corpo_out→38→37.',
  'Native root/3/6 police departure, root/3/40 trigger/wanted-level arbitration and failure39.True→15.Failed remain unchanged. Reward/cleanup changes are completely enumerated in native_current_diff.json; no additional native graph delta exists.'
 ],remaining=['LIVE_ONLY: Combat AI, Streetkid eligibility, scene choices and vehicle departure success are not certified by static connectivity.']),
 'presentation':c('OPAQUE',[
  'Alley scene retains native actors0..5: three Police_Officer community actors at #mq005_com_alley, Corpo at #mq005_com_corpo and car spawners #mq005_spwn_police_car_002/001. Native scene declares11 workspots/14 instances; passout declares Guy spawnDespawn and3/3 workspots/instances. Their pinned resources and private binding are retained.',
  'Root #mq005_pr_alley and all native actor/camera/workspot/depot literals are inventoried. Keeping a NodeRef string is explicitly not resolution of its world target.'
 ],remaining=['OPAQUE: Exact world placements, community definitions, spawner targets, workspot/camera target definitions and localization/provider resolution are not decoded/proven by this local graph batch.'],extra=['../../verification_02/dependencies.json']),
 'journal':c('PASS',[
  'Native journal paths/payloads are preserved. Alley scene515→97 input0:3 succeeds check_on_corpo,97→99 input0:1 activates talk_to_corpo; root success418→240 and424→698 retain0:3. Main11 receives Succeeded only after reward/ack; ignored active quest39.True→15.Failed remains native.',
  'No root/objective reset is added to admit a completed or failed save; script admission requires all six original entries Inactive.'
 ],remaining=['LIVE_ONLY: Journal rendering/tracking and exact player state remain unobserved. Journal target content/localization is outside the proven socket/payload parity.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Both native reward routes37.Out and5.End_Out now converge400 claim==0→401RewardClaim1→native9 QuestRewards.mq005_done→402RewardAck1→native11.Succeeded. Claim1 goes403ReplayRefused, with no reward route. Native scene cash alternatives644 mq005_money_no_intimidation and658 mq005_money_intimidation remain unchanged.',
  'Native cleanup10/15 are OR(exact native condition, guarded completed-police-left departure). Alternative requires own Request/Started/RewardClaim/RewardAck1, no Fault/ReplayRefused/OwnerFinished, mq005_done1/police_left1/police_done0, CleanupDeparture1 and outside #mq005_tr_big. Script arms it only after completed native journals and five safe >=500m horizontal samples. Original deactivation commands feed AND14 then445CleanupJoined→output; no forced done/door/AI replacement.'
 ],['S1.1 documented bounded completed-police-left cleanup fallback; research assessment/live_result and docs/gig_pilot_r1_check.md are pinned. Historical successful fixture is scoped to its observed route.'],['CONDITIONAL: Reward TweakDBID pointers are preserved, but cash/XP/item definitions and engine exactly-once delivery are not proven. Post-repair reload, alternate outcomes and visual actor absence remain separate from historical getter evidence.']),
 'persistence':c('CONDITIONAL',[
  'Saved system field names, resource depots and existing node IDs are unchanged in QR3. RewardClaim/Ack and OwnerFinished are monotonic receipts; RestoreFresh and Restored reject replays/interrupted unsupported schema states.',
  'Documented S1.1 fixture adopted already-running cleanup waits and retained reward1/1. The report explicitly notes CleanupEntered0 can occur because old saved waits predate instrumentation; this is not treated as proof of missing cleanup or grounds to replay setup.'
 ],remaining=['CONDITIONAL: The historical S1.1 observed fixture is not every QR3 save transition. Old owner field/resource identities across actual saved descendant trees and all interrupt/save points require fixtures. File rollback is not save rollback.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Native root/instance support, combat copy, alley/passout scenes, S1 script and S23 automatic call site are source pinned. Local decode has no dangling graph handles/edges. CR1 selected corrected donor hash is independently checked; the known stale Active-root mutation is rejected.',
  'Native bugfix resources are inventoried as separate original owners, not silently copied into a new Tower owner. Shared Safe/Profile and HS1 admission calls are retained; no arbitrary NPC/device/encounter reactivation was introduced.'
 ],remaining=['CONDITIONAL: Shared saved leases and original bugfix/root cleanup lifetimes were not decoded from a current save. Opaque world bindings and full transitive animation/voice/localization assets remain unresolved. No additional dependency owner was manufactured.'],extra=['../../verification_02/dependencies.json'])}
Q['mq013_punks']={
 'entry':c('APPROVED_DEVIATION',[
  'Private S23 base_b root1000→1001Ready→1002guard→1003PA2 pause→54(q001)→80(q005)→55(q101-enable)→1004recheck.True→1005Issued→1006Entered→17.In1. Native binding17 payload equals original minorquests17. False1004 returns to1002;17.Out1 writes1007Finished.',
  'Native MQ013 In1 enters8 startup, then9 main and10 cleanup. Alternate native debug In2 exists but the private wrapper enters In1; it does not bypass the native startup.'
 ],['Existing bounded fresh-only S23 post-Tower owner replaces the killed original parent while retaining the native entry resource.'],['LIVE_ONLY: Automatic permit delivery/injection execution is not live-observed.']),
 'eligibility':c('PASS',[
  'Ancestor q001_done>0, q005_done>0 and q101_enable_side_content>0 match original parent nodes54/80/55. Native root/8 still waits6 q101_done>0 before the authored startup; the outer enable flag is not substituted for that completed-story prerequisite.',
  'Actual1002/1004 AND require genuine Tower/PA2/U9 support, own Permit1/Issued0/Finished0/Fault0, all eight journal entries Inactive; exact fresh seam mq013_active1 with dealt/punch/combat/punks-defeated/dead-before-scene/far-away/timeskip0 and shopkeeper dead/default/discount0. All root terminal/active and each Succeeded child fixture reject. Script StatesA9/StatesB9 are all Inactive; no journal/fact reset is used.'
 ],remaining=['LIVE_ONLY: Prior mq013_active1 evidence and actual player values/certificate are not inferred; static PASS describes the bounded input seam only.']),
 'communications':c('PASS',[
  'Native MQ013 main, all nested graphs, punks scene and private wrapper contain zero Phone/SMS and zero holo_/audio_ request/listener/ack fact nodes. Actual main14/76/91 direct scene inputs control shopkeeper dialogue/combat; no missing holocall listener is implied by this street encounter.'
 ],remaining=['LIVE_ONLY: Spoken choices/barks and scene playback/interruption require gameplay.'],extra=['../../verification_02/communications.json']),
 'ownership':c('CONDITIONAL',[
  'Native resource owns #mq013_pr_punks. Main7 turns std_arr_foodshop_03_default_on0 before scene14; alive route16 sets discount1 then15 restores default1; dead route17 sets dead1 and skips reward. These original vendor leases are intact.',
  'Private Issued is claimed once before native17; Finished is written only from its output. Actual guards prohibit already-issued and progressed/terminal histories; S23 reads stable journal/fact samples across ticks and HS1 before issuing Permit.'
 ],remaining=['CONDITIONAL: Current saved original encounter/default-vendor execution and shared vendor ownership are not decoded. mq013_active1 plus Inactive journals is an exact admission seam, not independent proof of original descendant retirement.']),
 'progression':c('PASS',[
  'Native entire resource is referenced without modification. Main14.alive→77→16→15→78reward→79→output;14.dead→17→82→output. Combat14 branches to52 combat and85 escape/interrupt monitor;76 combat-scene alive/dead routes join their native outcomes and91 combat_shop preserves the dead route.',
  'Native interrupt cut89 targets scene14/76, far-away85 and cleanup10 remain connected. Per-node/socket source assertions exercise alive, dead, combat, shop combat and terminal cleanup routes; no added completion branch bypasses the native scene.'
 ],remaining=['LIVE_ONLY: Native combat, escape distance, shopkeeper survival and scene outcome timing need live cases.']),
 'presentation':c('OPAQUE',[
  'Pinned native punks scene has shopkeep spawnSet #std_arr_foodshop_03, punk_01/punk_02/customer community #mq013_com_punks and bike spawnSet #std_arr_foodshop_03;9 workspots/15 instances. All entry/exit declarations and resource literals are preserved.',
  'Native resource-root #mq013_pr_punks is retained by the referenced resource. Original world-data/spawn/crowd nodes are not replaced by synthetic idle NPC spawns.'
 ],remaining=['OPAQUE: Shopkeeper/vendor definition, root placement, workspot/camera/animation bindings and current-world actor existence are not established by declarations alone.'],extra=['../../verification_02/dependencies.json']),
 'journal':c('PASS',[
  'Native punks scene retains talk336, description622, decide338/339, deal383/341/951, defeat1415/1416 and talk-shopkeep519/345/1067 actual paths.345→347 input0:3 succeeds root;156→374 input0:4 and11→619 input0:4 preserve failure routes. Mutation removing shopkeeper-dead branch is detected.',
  'Native cleanup root/10 input0 sends POI21.Inactive,4 writes mq013_active0 and3 mq013_done1; no private post-outcome journal rewrite is added.'
 ],remaining=['LIVE_ONLY: Journal definitions/localization and rendered tracking are distinct from retained path/socket parity.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Only the native alive outcome16→15→78 grants QuestRewards.mq013_punks_done; dead17→82 reaches output without that reward. Native default/discount/dead vendor flags remain separate. Cleanup10 preserves mq013_done1, active0, native deactivation/joins and output33.',
  'Private Finished follows native questphase output, with no independent forced reward, synthetic vendor acknowledgement or replay adapter.'
 ],remaining=['CONDITIONAL: The exact reward record definition and engine award delivery are not decoded. Native cleanup geometry/deactivation and vendor persistence need matching live/save fixtures.']),
 'persistence':c('CONDITIONAL',[
  'Current wrapper retains saved PTFRS23_MQ013 Ready/Permit/Issued/Entered/Finished/Fault identities and native resource/node paths. Admission rejects terminal/progressed journals and every used scene/vendor fact; Issued prevents replay. Original vendor outcome receipts are not reset.',
  'Native completion/failure paths, actor cleanup and vendor state writes remain in their original resource, preserving their original owner serialization boundary.'
 ],remaining=['CONDITIONAL: No current saved MQ013 owner or transition fixture confirms execution adoption after save/reload at shop dialogue, combat, flight or reward.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Native parent prerequisites, root punks prefab, shop vendor community, direct scene resources, S23/HS1 permit dependencies and original MQ013 bugfix marker owner are inventoried with exact hashes. All local decoded graphs are structurally valid.',
  'No phone studio owner is needed by this local closure; U9 support remains a global S23 admission prerequisite and is not evidence of a missing local call.'
 ],remaining=['CONDITIONAL: Vendor shared lifecycle and original saved support leases remain unresolved. Literal asset references do not prove transitive definitions/provider precedence or world placement.'],extra=['../../verification_02/dependencies.json'])}
Q['mq002_veterans']={
 'entry':c('APPROVED_DEVIATION',[
  'Private S23 base_a claims1003Issued only after1001wait/1002check;1007wait/1008check then traverse the exact original parent chain81→83→84→54→86→80→55→70→73→62→59→47→76→82→78→89→90→52→53→173.173.False→1100final recheck.True→1101Entered→12.In1 native MQ002.',
  'Private target12 payload exactly matches native minorquests12. A parallel Succeeded observer1010→1011Finished records native outcome; it does not generate completion.'
 ],['Existing bounded S23 fresh rehosting after Tower cleanup; original parent ancestor predicates and native MQ002 resource remain.'],['LIVE_ONLY: Scheduler, native12 execution and observer callbacks are unobserved.']),
 'eligibility':c('PASS',[
  'Original parent requires q001_done>0, q005_done>0, q101_enable_side_content>0, q103_rogue_done>0, q104_done>0, sq004_done>0 and173 mq002_done>=1 False; every retained ancestor payload and edge is compared. Native MQ002 again waits sq004_done and preserves sq027 suspension/arbitration.',
  'Actual1001/1002 require root and six children Inactive, own Permit1/Issued0/Finished0/Fault0, mq002_active in0..1 and deal/broken-combat/done/escaped/escaped-combat/sniper-noticed0. Postclaim1007/1008/1100 require Issued1 and preserve children; root is OR(RootReactivated0+Inactive, RootReactivated1+Active). Stable Failed cannot pass initial guards, so existing1004 Failed-reactivation branch is not a generic failed-history reset.'
 ],remaining=['LIVE_ONLY: Exact saved HS1 admission and actual native prerequisite values remain unknown; positive and negative fixtures are static bounded evaluations, not scheduling proof.']),
 'communications':c('PASS',[
  'No holo_/audio_ producer/listener/ack facts exist in the local MQ002 native+scene closure. Combat native4.Out→20 questSendMessage contacts/carol/mq002_escaped→19 is connected and pinned; missing producer connection mutation is detected.',
  'After completion/cleanup native147 tests journal Succeeded. True→146 camp/fluff; False→152 whose0→2.Active post_veterans/mq002_escaped message→3.Active 02_ch_response choice→output. Original failure/escaped SMS behavior remains; this is direct native messaging, not a holocall awaiting a manufactured acknowledgement.'
 ],remaining=['LIVE_ONLY: Message UI dispatch, notification delivery and post-failure choice consumption require engine observation.'],extra=['../../verification_02/communications.json']),
 'ownership':c('CONDITIONAL',[
  'Native MQ002 resource owns #mq002_pr_factory and nested146 owns #mq002_pr_camp/#mq002_pr_new_camp. Native128 borrows Carol/Teddy/Cassidy and turns their default_on flags0; native102 cleanup restores all three1 after spawning/crowd/world transitions. Their support is retained, not replaced by a root-factory-only assumption.',
  'Native sq027_suspension outputs from121/128→153 wait(camp_abandoned0 AND sq027_active0)→128 reentry are preserved. Private target resource retains native saved paths and all root/nested identities.'
 ],remaining=['CONDITIONAL: Original saved nomad, Panam-camp and generic actor default-owner leases are not decoded. q307 killed flags and active0..1 are not proof these old descendants retired. Native CYB-599403/CYB-599080/CYB-567649 fix-owner adoption also remains unproved.']),
 'progression':c('PASS',[
  'Native root129→128 startup→121 beginning preserves deal to_outcome→123, to_combat→122→123 and separate quest_fails138→139→140→137.Failed. Native ending123.Out1→124.Succeeded→125active0→126done1→143checkpoint→148→102cleanup survives.',
  'Native camp-abandon/PONR path133→151POI.Inactive→134→135Failed/142 cleanup and sq027 suspended retry153 are unchanged. Native scenes deal107 writes mq002_deal_proceeded1,315 increments mq002_deal_broken_combat; combat/ending resources remain exact original references.'
 ],remaining=['LIVE_ONLY: Panam-camp timing, deal/combat choices, failure routes and encounter AI need gameplay.']),
 'presentation':c('OPAQUE',[
  'Native deal scene declares Carol/Teddy/Cassidy spawnSet #carol/#teddy/#cassidy; scavenger community #mq002_com_scavengers, nomads #mq002_com_nomads and van #mq002_com_deal_vehicles.17 workspots/35 instances. Summary uses six native actors and6/17 workspots/instances; combat/fluff retain their exact original cast.',
  'Root factory and both nested camp prefabs are recorded. Scene entry/exit, interruption scenarios, camera/reference-point and resource metadata are pinned; no idle replacement actors were added.'
 ],remaining=['OPAQUE: Target community/spawn/camp placements, character definitions, camera/workspot/animation definitions and actual current actor leases remain unresolved.'],extra=['../../verification_02/dependencies.json']),
 'journal':c('PASS',[
  'Native123.Out1→124.Succeeded and failure140→137.Failed remain distinct. Native root152 activates Carol post-failure message/choice only on147.False. Native128 sets POI active;128/38 suspension deactivates POI and active0 without inventing completion.',
  'Wrapper admission protects all seven original root/phase/objective/description entries; no private generic journal reset exists on the eligible stable-Inactive route. Existing1005 Active branch is gated behind1004 Failed after initial Inactive guards and is not used as evidence of permission to reopen failed jobs.'
 ],remaining=['LIVE_ONLY: Root change between guard ticks and failed branch engine scheduling cannot be excluded by fixtures; no demonstrated faulty stable-state route justifies a speculative patch. Journal definition/rendering remains separate.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Pinned native ending11 End0→26 QuestRewards.mq002_done→10.Succeeded is connected. Root124→125 active0→126 done1→checkpoint→native102 cleanup; native failure137 also clears active/done through the original chain. No private reward grant/replay is added.',
  'Native102 removes encounter actors/vehicles, waits for relevant world states, selects camp via sq027_camp_moved and restores carol/teddy/cassidy_default_on1 through AND44. Native147 then branches successful camp fluff146 or failed post-message152. Wrong reward pointer mutation and missing escape-message mutation both fail the intended checks.'
 ],remaining=['CONDITIONAL: QuestRewards.mq002_done target definition/cash/XP and engine exactly-once delivery are not proven. Cleanup actor deactivation, camp/default-owner restoration and reward/save boundaries need fixtures.']),
 'persistence':c('CONDITIONAL',[
  'Current PTFRS23_MQ002 saved fact/resource/node names and native owner boundaries are unchanged. Issued1 before native entry, final1100 recheck, bounded RootReactivated pairing and Succeeded observer avoid an unconditional replay path; native progress/completion/failure facts remain authored.',
  'Initial Inactive admission and all terminal-state negative fixtures are preserved. No live history, fact, journal or external mod data was changed by this investigation.'
 ],remaining=['CONDITIONAL: Stage/owner/reward transition fixtures are absent for old camp owners, interrupt suspension and save/reload around claiming, outcome, cleanup and Carol messages.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Full local native MQ002 beginning/combat/ending/four-scene closure and original bugfix resources are pinned. Parent prerequisites, root factory, nested camp prefabs and borrowed nomad/default actor dependencies are explicitly inventoried; local graph decoding reports no structural errors.',
  'Native U9-independent direct SMS is retained while global S23 U9/PA2/HS1 requirements remain exact. No missing local holocall or new shared studio was inferred from a string search.'
 ],remaining=['CONDITIONAL: Camp ownership/leases and external native corrective-owner execution require saved/world evidence. Asset literals and catalog presence are not resolution of exact definitions or gameplay.'],extra=['../../verification_02/dependencies.json'])}
keys=['entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies']
names={'mq005_alley':'Only Pain','mq013_punks':'A Day in the Life','mq002_veterans':'Gun Music'}
items=[];allcounts=collections.Counter()
for q,contracts in Q.items():
 assert list(contracts)==keys
 obj={'quest_id':q,'title':names[q],'source_epoch':'QR3 candidate_01 epoch00; relevant payloads unchanged','status':'DEEP_REVIEWED_CONDITIONAL','fully_static_verified':False,'defects':[],'repairs':[],'contracts':contracts}
 p=H/'quests'/q/'contracts.json';write(p,obj)
 counts=collections.Counter(x['status']for x in contracts.values());allcounts.update(counts)
 items.append({'quest_id':q,'contracts':str(p),'contracts_sha256':sha(p),'status_counts':dict(counts)})
 text=['# '+names[q]+' — '+q,'','Source-specific ten-contract review. No source-confirmed defect or runtime repair.','']
 for k,x in contracts.items():
  text += ['## '+k+' — '+x['status'],'']+['- '+z for z in x['proven']]+['']
  if x['approved_differences']:text+=['Approved differences:']+['- '+z for z in x['approved_differences']]+['']
  if x['remaining']:text+=['Remaining:']+['- '+z for z in x['remaining']]+['']
 (p.parent/'REPORT.md').write_text('\n'.join(text),encoding='utf8')
write(H/'approved_differences.json',{'source_epoch_sha256':sha(I.W/'prealpha/quest_restoration_qr4/source_epoch_00.json'),'differences':[{'quest_id':q,'contract':k,'difference':d,'source_pins':str(V/'source_pins.json'),'source_pins_sha256':sha(V/'source_pins.json'),'approval_scope':'Existing authorized post-Tower rehost or exact documented S1.1 bounded fallback; no claim of engine ownership equivalence'}for q,cs in Q.items()for k,x in cs.items()for d in x['approved_differences']]})
write(H/'results.json',{'group':'G06','quest_ids':list(Q),'quests':items,'tests':str(V/'tests.json'),'tests_sha256':sha(V/'tests.json'),'source_pins':str(V/'source_pins.json'),'checks':T['total_checks'],'mutations':T['total_mutations'],'confirmed_unique_defects':0,'runtime_changes':[],'source_epoch':{'path':str(I.W/'prealpha/quest_restoration_qr4/source_epoch_00.json'),'sha256':sha(I.W/'prealpha/quest_restoration_qr4/source_epoch_00.json')}})
(H/'REPORT.md').write_text('''# G06 — Three street quests

Only Pain, A Day in the Life and Gun Music have thirty source-specific contract dispositions. No confirmed repair is justified. QR3's two repaired resources remain untouched; all G06 work is isolated audit evidence.

382 focused checks and seven mutations passed across 23 pinned decoded resources. Tests cover the CR1 corrected Inactive donor, complete native S1 node/edge delta, exact combat copy, one-time reward receipts, bounded S1.1 departure fallback, native shopkeeper alive/dead/combat branches, Gun Music ancestor prerequisites, native nomad/camp ownership and Carol SMS routes. Scene actor/workspot declarations and actual journal socket transitions were inspected. Native reward pointer preservation does not certify target definitions or amounts.

Each quest: 1 APPROVED_DEVIATION, 4 PASS, 4 CONDITIONAL, 1 OPAQUE. None fully statically resolved: saved owner transitions, world target definitions and reward definitions remain explicit. Static graph consistency is not gameplay proof. The narrow G02 wording/mutation correction is separate in G02_self_correction.json; G02 originals and frozen shared_core remain unchanged.

Reproduce into a new directory:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -B 'prealpha\\quest_restoration_qr4\\groups\\G06\\verify.py' --output 'prealpha\\quest_restoration_qr4\\groups\\G06\\verification_next'
```

verification_01 remains preserved; verification_02 adds explicit native actor/workspot declarations and journal/cash alternative checks. No resource correction was made between runs.
''',encoding='utf8')
print(json.dumps({'quests':len(Q),'contracts':sum(allcounts.values()),'statuses':dict(allcounts),'checks':T['total_checks'],'mutations':T['total_mutations']}))
