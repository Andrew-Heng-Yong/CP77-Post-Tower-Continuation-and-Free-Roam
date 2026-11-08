from pathlib import Path
import sys,json,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha
V=H/'verification_02';T=read(V/'tests.json');assert T['failed']==0;assert not(H/'results.json').exists()
E=['../../verification_02/source_pins.json','../../verification_02/graph_evidence.json','../../verification_02/guard_fixtures.json','../../verification_02/tests.json']
def c(status,p,a=(),r=(),extra=()):return {'status':status,'proven':list(p),'approved_differences':list(a),'remaining':list(r),'evidence':E+list(extra)}
Q={}
Q['mq007_smartgun']={
 'entry':c('APPROVED_DEVIATION',[
  'Current S23 fresh boot enters exact native minorquests21/MQ007 In1 after original q001_done>0→q005_done>0→q101_enable_side_content>0 ancestors and final1100 recheck. Fresh follows native pickup2→mode4→return5, with the native ambient/equip sibling retained.',
  'Resume boot has the same retained original ancestor payloads, but target21 is private resume_owner. Its selected root nodes0/1/3/5/7/11/12 are exact native payloads; all retained nested graphs/edges are exact. Only0→5.In1 replaces completed pickup/mode4 route; the original pickup2, mode4, debug8 and pickup cleanup10 are absent. It continues at the authored root4.Out1→5 seam.'
 ],['Existing bounded post-Tower fresh and source-reviewed post-mode resume adapters; no arbitrary mid-dialogue/mid-reward restart.'],['LIVE_ONLY: Registration activation and actual saved descendant scheduling are not observed.']),
 'eligibility':c('CONDITIONAL',[
  'Fresh actual1001/1002 require all six original journal entries Inactive, zero mode/counters/done/owner-known/reacquisition/stash flags, original Skippy inventory0, own Permit1/Issued0/Finished0/Fault0 plus genuine Tower/PA2/U9. Existing gun and progressed counters are rejected; native original conditions remain inside the referenced resource.',
  'Resume actual1001/1002 require ModeTalkConfirmed1, own freshIssued0/resumeIssued0, 50-defeated1/50-maimed1, exact lethal11/nonlethal51/total95, opt_A0, owner-known0, no native done/reacquisition/stash/interruption and original Skippy inventory>=1. Native return83 retains AND SideQuest_Standalone content token, two game days, inventory and no driving/passenger/vehicle transition.',
  'Current serialized initial resume journal root is Inactive only. Historical base_a_v2 assessment says Inactive OR Failed, but that is stale for the corrected current source. Current terminal-state fixtures reject Failed/Succeeded; no historical Failed prose authorizes reopening them.'
 ],r=['KNOWN_HELD_SEAM: Progressed counts97/100 or missing ModeTalkConfirmed do not satisfy exact11/51/95. This known unsupported seam remains conditional, not a newly discovered repair or permission to reset counters/history. The owned confirmation is not inferred from the pre-conversation 50 fact.',
 'CONDITIONAL: Matching post-mode saved ownership/history evidence and current content-token context are absent. Native return token is preserved; actual engine context eligibility is unproved.']),
 'communications':c('CONDITIONAL',[
  'Native MQ007 phase and four scenes contain no positive holo_/audio_/phonecall_ request/acknowledgement protocol. Skippy speech/display uses the native gun scene/ambient mechanism, not a missing external holocall listener. Reused SC3 resource hash exactly matches the earlier audited E9A06A80…156B19.',
  'Later no-AI Regina contact messages belong to separate original bugfix root/14: done>=1→context/office wait→variant→root/14/3 journal5/6/7 Active for about_what_happened,techie_took_skippy,want_him_back→re_acquiring_done1. Neither S23 fresh/resume target creates this original corrective owner.'
 ],r=['CONDITIONAL: Original bugfix14 saved/executing owner and later no-AI message/variant delivery are not proved post-Tower. Message presence is not controller activation. Existing historical ambient speech/equip observations do not certify Regina delivery or retrieval.'],extra=['../../verification_02/communications.json']),
 'ownership':c('CONDITIONAL',[
  'Story resume keeps native ambient3/equip11/12, exact return5 and cleanup7 owner boundaries. It does not restart pickup or completed mode talk. Fresh/resume are disjoint by neutral versus exact progressed counters and inventory, with freshIssued0 required on resume.',
  'Current S23 Ready blocks fresh/resume indices1/8 while SC3 Claimed1/Stopped0; SkippyAmbient requests the existing SC3 stop for fresh/resume/story takeover. SC3 is the previously reviewed persistent ambient owner, whose unchanged hash reuses prior evidence. No ambient rebuild or repeated log/wiki investigation occurred.'
 ],r=['CONDITIONAL: Actual native/SC3/default-Regina saved leases and stop/adoption order are not proven by guard fixtures. Private guards and driver advisory Permit are not an engine scheduler simulation. Later native bugfix14 ownership remains separate and unresolved.']),
 'progression':c('PASS',[
  'Every selected resume native node payload and retained nested edge is compared to pinned native MQ007, including full return5. Native equip loop11→3,3.TurnOff→12→3 remains; native5.Out1→7 cleanup and5.RetroSkipCleanup→1 remain. Fresh delegates the original complete MQ007 resource.',
  'Return/51.Out1→13.Succeeded→10 QuestRewards.mq007_done→66 mq007_done1→62 checkpoint remains exact, followed by native office-departure106. The copied return body uses authored Regina scene/actions and does not synthesize mode, owner reveal or acknowledgements. The 50-conversation is omitted only on the bounded resume route where owned history is required.'
 ],r=['LIVE_ONLY: Mode conversation, current timer progress, weapon behavior, Regina choices and scene scheduling are not gameplay-proven.']),
 'presentation':c('OPAQUE',[
  'Return scene keeps native Skippy/Reggie/Daisy/SkippyVoice acquisition declarations, Reggie spawnSet #reggie, four workspots/seven instances and authored entries/sections. Native gun display, reaction, about-killing and pickup scenes are pinned; existing JV1/R4 presentation policy is unchanged.',
  'Existing SC3 resource reuses the prior audited source exactly. Native source references and declarations are inventoried without calling them resolved world/actor definitions.'
 ],r=['OPAQUE: Regina office placement/default ownership, display/voice/workspot/camera/localization target definitions and all transitive assets are not resolved here. Historical hologram/speech observations do not cover the return presentation.'],extra=['../../verification_02/scene_inventory.json','../../verification_02/dependencies.json']),
 'journal':c('PASS',[
  'Fresh/resume admission protects all root/phase/deliver/description/put-down/talk-Regina entries; each Succeeded child negative fixture refuses. Current initial roots require Inactive. Existing1004 Failed→1005Active branch is behind current Inactive preclaim, not a general supported Failed reset route.',
  'Copied native return/51→13.Succeeded and exact native delivery objectives remain; private1010 observes actual Succeeded before1011Finished. It does not create journal success independently of Regina/return actions.'
 ],r=['LIVE_ONLY: Guard-to-journal engine transitions and current saved state are not evaluated; rendered journal definitions/localization remain outside path parity.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Original return/10 QuestRewards.mq007_done follows native delivery-phase51 and root13.Succeeded; done66 and checkpoint62 follow reward. Native cleanup7 is exact and original outside-office106 remains. No wrapper grants a second weapon/reward or forces completion.',
  'Native two-game-day wait is retained at return83. Earlier elapsed-time summaries are not used to replace this timer or invent its already elapsed duration. Later no-AI variant/messages are governed by separate native bugfix14, not assumed to execute from S23 completion.'
 ],r=['CONDITIONAL: Exact reward/item definitions, once-only engine delivery, saved timer adoption, later Regina retrieval and native corrective-owner execution need additional evidence. No return/retrieval live proof was reused from ambient success.']),
 'persistence':c('CONDITIONAL',[
  'Saved S23 MQ007/MQ007_RESUME, SC3 and selected original node/resource identities are retained. Private Issued prevents repeat entry; no native kill counters, mode, quest progress, item or reward facts are reset to fit the seam.',
  'The prior recorded total97/missing confirmation and later total100/lethal16 are historical unsupported examples, not a current save read. Static fixtures reproduce refusal for total97 and missing confirmation. No confirmation fact was written and no unsupported seam widened.'
 ],r=['CONDITIONAL: Exact-stage saved owners, old-version transition fixtures and one-time receipt delivery around claim/return/reward/cleanup remain unproved. Historical mode-talk statement is not a saved mod fact.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Pinned native MQ007 root, expression reset, gameplay comments, four scenes, current fresh/resume boots, resume owner, SC3 and original bugfix resource are inventoried. All decoded local graphs have no structural errors. Prior SC3 source assessment/provider observations are reused by exact owner hash and explicitly retain their age/scope.',
  'Original return token/vehicle/inventory gates, Regina office NodeRefs and native cleanup remain; no shared phone studio is inferred as necessary to gun speech. Driver has explicit story-priority ambient stop and old-owner stop rules.'
 ],r=['CONDITIONAL: Native bugfix14 execution, Regina/default leases, current token context and world target definitions remain unresolved; literal references and old archive-provider scans are not blanket current provider proof.'],extra=['../../verification_02/dependencies.json'])}
Q['mq008_party']={
 'entry':c('APPROVED_DEVIATION',[
  'Current S2 private root0→1000Ready→1001PA2 wait→original ancestor81/83/84/54/86/80/55/70/73/62/59/47→176 mq008_done>=1.False→1002guard.True→1003Issued→29 native MQ008.In1. Native29 payload matches original minorquests29;29.Out1→1004Finished.',
  'Native MQ008 starts authored setup14 and concurrent hook2/contest3/cleanup monitors/root42 reward pickup. Debug competition6 and afterparty7 entries exist but the private wrapper enters the original In1.'
 ],['Existing bounded post-Tower S2 rehost preserves native body and original parent predicates.'],['LIVE_ONLY: Injection/Permit delivery and native setup execution are unobserved.']),
 'eligibility':c('PASS',[
  'Retained original parent q001_done>0, q005_done>0 and q101_enable_side_content>0 plus native done check176 match exact source. Actual guard1002 requires Tower/PA2/U9, own Permit1/Issued0/Finished0/Fault0,22 original journal entries Inactive and neutral agreed/rules/score/cheat/round/result/reward/combat/left facts.',
  'Own AuthorizedRoute must equal1 OR2, while mq008_active and mq008_quest_comm_on are bounded0..1. Both authorized-route fixtures pass at their allowed bounded state; terminal roots and every Succeeded child refuse. No score, round, cheated or claimed-reward state is reset to admit a used competition.'
 ],r=['LIVE_ONLY: Actual historical route/certificate/current actor context values are not read from a save. Static PASS is limited to the explicitly supported untouched seam.']),
 'communications':c('PASS',[
  'Complete local MQ008 main/hook/contest/cleanup/party-chats/contest-scene closure has no Phone/SMS or holo_/audio_/phonecall_ request/ack facts. Native representative/judge dialogue is direct scene interaction; no external call listener or fabricated acknowledgement is needed by these local graphs.'
 ],r=['LIVE_ONLY: Spoken contest/drinking dialogue, bark timing and interruptions require gameplay observation.'],extra=['../../verification_02/communications.json']),
 'ownership':c('CONDITIONAL',[
  'Native root owns #mq008_pr_6th_street_hood and original root14 activates authored community state, encounter and helper branches. Private29 references that original resource and preserves one native encounter lifetime; it does not replace it with generic NPC spawns.',
  'Original combat11, regular/failure cleanup8 and reward tracker42 coordinate through root AND43; the independent outcome branches retain the original community/radio/item-tag leases. Private Finished follows native output only.'
 ],r=['CONDITIONAL: Allowed active/quest_comm_on0..1 and untouched journals do not prove every old original/community owner retired. Saved original helper/bugfix execution and current actor leases need transition/world evidence.']),
 'progression':c('PASS',[
  'Native hook2 combat_out→11 combat, no_competition_out→8.In1 and quest_fails→8.In2 remain. Contest3 normal→8.In1, quest_fails/v_won_and_left_out→8.In2 and boss offense→11 remain; no branch is flattened into a single success route.',
  'Four actual contest nested round phases3/27/49/70 feed completion receipts102/101/100/99 then107 inputs1..4. Their native mq008_final_score writers increment by1 without resetting. Native result threshold is strictly score>43 at root/42 node16. Scene drink sections77/90/142/156 connect real player_drunk increment writers4264/4267/4270/4273; cheat flags1206/1210/1223/1233 remain authored.'
 ],r=['LIVE_ONLY: Hits/target health, weapon draw, alcohol effects, time limits and scene competition outcomes are engine behavior.']),
 'presentation':c('OPAQUE',[
  'Pinned representative/shooting/party scenes retain native community cast at #mq008_com_representative/#mq008_com_shooting/#mq008_com_6th_street_party. Contest scene declares16 actors,53 workspots/128 instances; party chats10 actors,4/8. Exact scene declarations and root support are recorded.',
  'Original target helper phase107, loot-token actions, drinking sections and combat alternatives are preserved; no unsupported generic shooting-range or idle-actor replacement was introduced.'
 ],r=['OPAQUE: Target/object/spawner placement, rifle/item definition, camera/workspot/animation and scene variant resolution remain unproved. Native internal item name is not a verified display/weapon definition.'],extra=['../../verification_02/scene_inventory.json','../../verification_02/dependencies.json']),
 'journal':c('PASS',[
  'Actual22 original entry/phase/objective/description states are guarded Inactive. Native four shoot/drink objectives, point increments and back-to-representative/results/pickup routes remain in original resources.',
  'Native root/42 sequence waits results, checks score>43, unseals loot, writes mq008_v_wins1, activates17_pick_up_the_reward, waits exact inventory item and succeeds it; result/root success retains original branch selection. Failure/no-comp/combat cleanup remain separate and unchanged.'
 ],r=['LIVE_ONLY: Native objective counters and journal rendering/localization are not certified by static graph structure.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Contest68 mq008_v_wins>0.True→69 QuestRewards.mq008_shooting_win; False→70 QuestRewards.mq008_done. Authored won-and-left route48→85 keeps its original shooting_win pointer. Native root/42 pickup wait7 uses Items.mq008_golden_knuckledusters quantity1 (a legacy internal literal), reached after loot-token unseal3 and reward-unsealed gate2.',
  'Native cleanup has both regular/failure active0/done1, quest_comm_on0, radio_on1 and quest_item_tags_cleaned receipts. Original reward handling, scene cleanup, combat and root43 join are retained; private wrapper grants no reward.'
 ],r=['CONDITIONAL: Actual rifle/item and reward target definitions, amounts, native once-only pickup, community cleanup/streaming and saved reward transitions need evidence. The legacy item string is not resolved to a definitive weapon type here.']),
 'persistence':c('CONDITIONAL',[
  'S2 saved Permit/AuthorizedRoute/Issued/Finished/Fault identifiers and native scene/phase/node identities remain. Guard rejects any score/round/cheat/reward/completion progress; Issued prevents a second private native entry.',
  'No fact/journal reset, synthetic target-health reset, replayed payout or item replacement was added. Existing completion outcomes retain native one-time boundaries.'
 ],r=['CONDITIONAL: Saved competition owners and transition fixtures at drinking/round loss/results/loot pickup/cleanup are not decoded. File preservation is not evidence of saved-state adoption.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Parent ancestor predicates, root hood prefab, hook/contest/cleanup phases, target tally graphs, party and shooting scenes and native bugfix resource are pinned. All local graph handles/edges decode without errors.',
  'Native actor/community/radio/loot-token/item-tag and external item/reward references are inventoried individually. Local phase presence is not treated as complete target or world definition proof.'
 ],r=['CONDITIONAL: Saved old helper/bugfix leases, exact target/rifle TweakDB definitions and current-world asset/provider/placement resolution remain unresolved.'],extra=['../../verification_02/dependencies.json'])}
Q['mq021_guide']={
 'entry':c('APPROVED_DEVIATION',[
  'S23 boot claims Issued after actual1001wait/1002check,1007wait/1008check then retained original parent chain through q001/q005/q101-enable/q103_rogue/q104/sq004/sq027_done. Final1100 check.True→1101Entered→8.In1 exact native minorquests8/MQ021; native Succeeded observer1010 only records1011Finished.',
  'Native root2 arms sq027_active0 wait90 and PONR95. After90,115 camp-abandoned.False enters original briefing96; True fails/deactivates through114/100/101/111. The private boot does not skip Bob or force the hospital phase.'
 ],['Existing bounded fresh S23 post-Tower owner retains original Bob/Panam/camp entry graph.'],['LIVE_ONLY: Native owner activation and actual scheduling are unobserved.']),
 'eligibility':c('PASS',[
  'Original parent56 sq027_done>0 (with q001/q005/q101-enable/q103_rogue/q104/sq004 prerequisites) is byte/payload matched. Native90 sq027_active==0 and115 sq027_camp_abandoned>0 arbitration remain; original briefing can signal sq027_failed and take native fail cleanup.',
  'Actual1001/1002 require root plus13 phase/objective/description children Inactive, native active/bob-ending-approached/done/happy-ending0, own Permit1/Issued0/Finished0/Fault0 plus genuine Tower/PA2/U9. Postclaim1007/1008/1100 retain child protection and bounded RootReactivated/Inactive-or-Active pairing. Current initial Failed/Succeeded and progressed children reject.'
 ],r=['LIVE_ONLY: Actual current camp, Bob availability, original history and admission certificate remain unobserved. No native prerequisite is fabricated to make the job available.']),
 'communications':c('PASS',[
  'Local MQ021 native phases/scenes contain no positive holocall request/ack facts. Bob ending is direct native SMS: outcome62 happy-ending selects88 survivor or63 sad-wife community, both→65 send contacts/bob/mq021/mq021_ending_message→67 wait-objective Succeeded→68 read-objective Active→66 real journal-visited wait→47 read-objective Succeeded.',
  'Parallel65→80 waits mq021_bob_ending_approached>0→108 message.Inactive→79 CutSource66 cancels the read wait. Native ending scene51 writes the approached fact. Original bugfix20 separately checks/activates the same message path; its existence is inventoried without assuming current saved execution. No fake read/phone-end fact or missing holocall listener was inferred.'
 ],r=['LIVE_ONLY: SMS notification/read/approach timing and original corrective-handler adoption require engine/save observation. Static message/read/interrupt topology is retained.'],extra=['../../verification_02/communications.json']),
 'ownership':c('CONDITIONAL',[
  'Native briefing owns #mq021_pr_camp and borrows Bob via bob_default_on0 at14; final root/102 cleanup restores bob_default_on1 at7. Hospital meeting/outcome each own both #mq021_pr_hospital and #mq021_pr_camp; combat owns hospital. Empty parent root prefab list is not treated as absence of support obligations.',
  'Native camp-abandoned/PONR failure111 cleanup and normal102 cleanup remain separate original descendants. Private8 delegates whole original owner, preserving saved phase identities and native actor/default-world actions.'
 ],r=['CONDITIONAL: Original saved Bob/Panam/camp/hospital/security/default leases and old corrective-owner execution are not decoded. Kill facts and current journal state do not independently prove retirement.']),
 'progression':c('PASS',[
  'Native briefing96.Out1→103active1→97 hospital→98 combat→99 outcome survives. Combat-escaped98→99.Skip_combat stays distinct; normal99.Out1→110 reward→104active0→105done1→112checkpoint→113→102 cleanup remains.',
  'Medical confrontation scene choice33 preserves let_kill/dont_kill/net options. The net blue-line retains PlayerBuilds.Netrunner CO_GreaterEq MEDIUM with DeviceContentAssignment.mq021; no numeric stat threshold is invented from this record pointer. Happy-ending writers42 and45 are reached from actual item-handoff sections78/84 and246. Outcome62 preserves happy/sad branch selection; no repaired author forces the medical outcome.'
 ],r=['LIVE_ONLY: Actual build/stat assignment evaluation, dialogue, doctor/security mortality, medicine/chip choice and health outcome are not simulated.']),
 'presentation':c('OPAQUE',[
  'Native briefing cast Bob spawnSet #bob plus Wife/Scooter community #mq021_com_nomads,4 workspots/5 instances; hospital Doctor/Security_01/van at doctor/security communities,8/18; ending Bob,1/1. Authored camp/hospital prefabs and exact scene bindings are recorded.',
  'Original actor health/killed/hit/reaction waits, security combat, doctor confrontation and variant actions remain. They are preserved original commands, not newly invented arbitrary NPC reactivation.'
 ],r=['OPAQUE: Exact camp/hospital world targets, current actor leases, health/status/TweakDB definitions, cameras/workspots and medical item/build/localization target definitions remain unresolved.'],extra=['../../verification_02/scene_inventory.json','../../verification_02/dependencies.json']),
 'journal':c('PASS',[
  'Native meeting24/28 and participate32/52, defend4/13, doctor-confrontation, outcome, ending43/44, wait45/67 and read47/68 states and socket transitions remain. Bob message uses actual visited condition66 and approached cancellation79, rather than marking all objectives complete from a private receipt.',
  'Native PONR/camp failure root100/101 and cleanup111 remain separate from native rootSucceeded33 after outcome48. Private observer tracks real root Succeeded; no forced completion or recursive journal reset is added.'
 ],r=['LIVE_ONLY: Current journal states, message read UI and rendered localization/tracking are separate from retained path/socket parity.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
  'Only native root110 grants QuestRewards.mq021_minor_done after actual outcome99.Out1, followed by active0/done1/checkpoint and102 cleanup. Original failed/abandoned root111 exits through94 without taking that normal reward route; no private second award exists.',
  'Native102 restores bob_default_on1 after the authored spawn/world/cleanup sequence. Outcome62 happy/sad communities, Bob send/read/approach cancellation and ending scene are preserved; cleanup does not overwrite the medical outcome.'
 ],r=['CONDITIONAL: Reward record definition/amounts and engine exactly-once delivery remain unproven. Doctor/nomad health outcomes, Bob default owner handback and message/cleanup save transitions require fixtures.']),
 'persistence':c('CONDITIONAL',[
  'Current PTFRS23_MQ021 receipts and native resource/node/field identities are unchanged. Initial untouched histories and neutral outcome flags are required; Issued prevents reentry and final1100 rechecks before native8. Existing Failed-root reactivation branch is not a supported stable Failed admission because current initial guards reject Failed.',
  'Native happy-ending, Bob-approached, done/reward and journal choices remain owned by original graph actions. No user save/fact/history was read or altered to clear the job.'
 ],r=['CONDITIONAL: Saved owner adoption and transition fixtures around briefing lease, combat escape, medical outcome, delayed SMS, reward and cleanup are absent.']),
 'shared_dependencies':c('CONDITIONAL',[
  'Original Bob/Panam predicates, all four MQ021 phases/three scenes, camp/hospital prefabs, current S23/HS1 driver and native bugfix message companion are pinned. Local graph decoding has no dangling handles/edges; real message read/cancel branches have mutation coverage.',
  'Native Netrunner/build assignment, reward, item and actor/world references are kept as exact pointers, not promoted to decoded definitions. Global U9 support remains an outer S23 prerequisite without implying a local call.'
 ],r=['CONDITIONAL: Shared camp/default actor ownership, original corrective-handler saved lifecycle and transitive world/TDB/provider definitions remain unresolved.'],extra=['../../verification_02/dependencies.json'])}
names={'mq007_smartgun':'Machine Gun','mq008_party':'Stadium Love','mq021_guide':'Fortunate Son'};items=[];counts=collections.Counter()
for q,cs in Q.items():
 assert len(cs)==10
 obj={'quest_id':q,'title':names[q],'source_epoch':'QR3 candidate_01 epoch00','status':'DEEP_REVIEWED_CONDITIONAL','fully_static_verified':False,'defects':[],'repairs':[],'contracts':cs}
 p=H/'quests'/q/'contracts.json';write(p,obj);s=collections.Counter(x['status']for x in cs.values());counts.update(s);items.append({'quest_id':q,'contracts':str(p),'contracts_sha256':sha(p),'status_counts':dict(s)})
 lines=['# '+names[q]+' — '+q,'','Source-specific ten-contract review. No confirmed new defect or runtime repair.','']
 for k,x in cs.items():
  lines+=['## '+k+' — '+x['status'],'']+['- '+t for t in x['proven']]+['']
  if x['approved_differences']:lines+=['Approved differences:']+['- '+t for t in x['approved_differences']]+['']
  if x['remaining']:lines+=['Remaining:']+['- '+t for t in x['remaining']]+['']
 (p.parent/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
epoch=I.W/'prealpha/quest_restoration_qr4/source_epoch_00.json'
write(H/'approved_differences.json',{'source_epoch_sha256':sha(epoch),'differences':[{'quest_id':q,'contract':k,'difference':d,'source_pins':str(V/'source_pins.json'),'source_pins_sha256':sha(V/'source_pins.json'),'scope':'Existing authorized bounded post-Tower rehosting; no widened progression/history'}for q,cs in Q.items()for k,x in cs.items()for d in x['approved_differences']]})
write(H/'results.json',{'group':'G08','quest_ids':list(Q),'quests':items,'tests':str(V/'tests.json'),'tests_sha256':sha(V/'tests.json'),'source_pins':str(V/'source_pins.json'),'checks':T['total_checks'],'mutations':T['total_mutations'],'confirmed_unique_defects':0,'runtime_changes':[],'source_epoch':{'path':str(epoch),'sha256':sha(epoch)}})
(H/'REPORT.md').write_text('''# G08 — Machine Gun, Stadium Love, Fortunate Son

Thirty source-specific contracts are recorded. No new source-confirmed defect or gameplay repair is justified. Machine Gun's known exact11/51/95 plus owned-mode-confirmation limitation is retained. Native later Regina reacquisition is explicitly assigned to separate bugfix14, whose post-Tower execution is conditional. Older resume Failed-root prose is stale: current initial serialized guards admit Inactive only.

677 checks and seven actual decoded-resource-copy mutations pass across31pinned binaries. Native return nodes/edges, retained parent prerequisites, Skippy ownership/inventory/counter gates, four contest rounds/drinks/score>43/rewards, native Bob/Panam/medical choices and real SMS visited/cancellation paths are covered. SC3 source hash matches its prior audit; no log/wiki/ambient reinvestigation, rebuild or install occurred.

Machine Gun:1APPROVED_DEVIATION,2PASS,6CONDITIONAL,1OPAQUE. Stadium Love/Fortunate Son each:1APPROVED_DEVIATION,4PASS,4CONDITIONAL,1OPAQUE. None fully statically resolved. World/TDB target definitions, saved executing owners and engine transitions remain explicit. Reward/item literals do not certify their definitions or amounts.

Reproduce into a fresh directory:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -B 'prealpha\\quest_restoration_qr4\\groups\\G08\\verify.py' --output 'prealpha\\quest_restoration_qr4\\groups\\G08\\verification_next'
```

verification_01 is preserved; verification_02 adds authorized-route2 and explicit scene declaration checks. No runtime resources changed.
''',encoding='utf8')
print(json.dumps({'quests':3,'contracts':sum(counts.values()),'statuses':dict(counts),'checks':T['total_checks'],'mutations':T['total_mutations']}))
