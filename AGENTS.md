# AGENTS.md — Post Tower Continuation and Free Roam

Latest 2026-10-29 BETA ZIP FOUR-FOLDER LAYOUT:
User requests only archive/bin/r6 plus readme, containing AI cleanup guide,
manual cleanup guide and supporting hash JSON; remove all other ZIP extras.
Supersedes older TowerContinuation-folder and patch-script packaging below.
Current readme has exactly AI_CLEANUP_INSTRUCTIONS.md,
MANUAL_CLEANUP_INSTRUCTIONS.md, FILES.json and OBSOLETE_FILES.json.55entries:
51unchangedcore+4referencefiles. No scripts, release notes, persistence baseline,
contract, oldZIP or backup in ZIP. Required Atelier edit remains explicitly
documented in manual guide with original/corrected hashes. Applying the documented
edit to reviewed original reproduces exact CO1 hash5743CDCD...; PASS. AI guide
points to manual section, not missing scripts. No oldZIP/backups required.
ZIP SHA F3FFEEED127532FF9F3DB5B4BCBB364FA673A9A50F519AF106D9E6D87030D7AE,
10127545bytes, same dist/v0.2.0-beta path. Fullreadback/CRC+filehashes PASS.
Staged package also has only four folders. Native game/save files untouched.
Canonical builder tools/package_release_020_readme.py. Historical revision
scripts must not be rerun. release/package-v0.2.0-beta.json records current proof.
No publication or Gitpush.

Latest 2026-10-29 BETA CLEANUP REVISION: AI GUIDE, NO OLD ZIP, NO BACKUP:
User explicitly removed cleanup-script requirement, then said no old ZIP and
no backup. Supersedes older beta installer/rollback instructions below. Current
beta ZIP contains AI_CLEANUP_INSTRUCTIONS.md and OBSOLETE_FILES.json (124 known
obsolete paths with accepted hashes from recorded manifests; no current51path
overlap). AI deletes only exact path+hash matches with native LiteralPath after
containment/link checks, without backups; changed/unknown files remain. No old
ZIP needed or bundled. Install-OpenBeta.ps1 removed from source and package.
Required CO1 remains as Apply-Atelier-Compatibility.ps1, Atelier-only with no
cleanup or backup creation. Four patchfixture cases pass (original, patched,
absent, unknown), and ZIP readback passes.51core+8helper/docs=59entries.
Current ZIP SHA2700AAC4AAEF0392417053DE7499EC1BEBD11586264322F7167B25C549DC4E0B,
10213741bytes. Same dist/v0.2.0-beta download path. No backup of revised ZIP
created; old prepared ZIP replaced as requested. Actual game/saves untouched.
INSTALL.md, release notes and README explain asking AI to read the included
cleanup guide. Future update filenames remain stable/drop-in Replace. No push
or publication. Validation now tools/test_release_020_cleanup_02.py; previous
test_release_020.py forwards to current tests (fixtures require fresh directory).

Latest 2026-10-29 OPEN BETA 0.2.0 PREPARED; VD1 USER LIVE PASS:
User confirms Viktor door fixed and resumes beta0.2.0 preparation. Later user
correction: Atelier compatibility fix is REQUIRED, not an optional patch. Beta
installer automatically applies/verifies exact CO1 when Virtual Atelier is
present; unsupported Atelier bytes refuse. User requires stable installed names
for future drop-in/Replace updates, documented in release/INSTALL-v0.2.0-beta.md.
Only outer ZIP is versioned; all51installedTower paths and Atelier target retained.
Prepared dist/v0.2.0-beta/Post-Tower-Continuation-and-Free-Roam-v0.2.0-beta.zip,
10213245bytes,58entries=51core+7management/docs. SHA256
E9A4C1FD1FA53DAEE626239FEDD69C389A80D87B58357D1C5EC295EAECDAD934.
ZIP full readback PASS; fourinstallerfixturecases/16actions PASS: clean,
clean+requiredAtelier, alpha114retired+Atelier, unknownAtelierrejection; original
fixturebytes/rollback preserved. Source/package/core installed hashes matchVD1.
Release manifest and1564resource/script compatibilitybaseline under release/.
Knownissues: possible missingassets/minoractions, misconfigured sidejobentries,
documented progressedSkippyMachineGungap. No knownfatalbugs is user report.
Futuremodsavecompatibility is release commitment; actual future successor tests
remain required and are NOT claimed passed. No further gameplaytestrequest.
No gameinstall/save/fact edits, game launch, Gitcommit/push/tag or publicrelease
by beta preparation. Installed payload remainsVD1 with CO1. No need rerun75GB
wholearchivehashes for packaging unchanged files. No public beta URL yet.
tools/package_release_020.py and tools/test_release_020.py reproduce preparation;
existingdist must be preserved. release/package-v0.2.0-beta.json and
release/validation-v0.2.0-beta.json record results.

Latest 2026-10-29 OPEN BETA HELD; VIKTOR CLINIC VD1 INSTALLED, LIVE PENDING:
User first requested preparing Open Beta with no known fatal bugs, possible
missing assets/minor actions, misconfigured side-job entries, and future save
compatibility. User then explicitly held that work to fix Viktor's clinic door.
Confirmed symptom is AFTER Tower, in free roam. No Open Beta artifact or public
release created. VD1 candidate_02 adds one native ForceUnlock owner for exact
q115_dvc_ripperdoc_room_door, omitted by existing R11 (which handles three other
doors). All1563 LC4 members preserved, total1564; same51paths, archive+XL only.
18guards include existing17 R11 world gates plus PA2Finished1; one-time claim,
loaded wait/recheck and unload/guard-loss rearm.89serialized checks/262144guard
combinations PASS.133archive fresh census: native phase/scene single, sector
basegame+EP1 only, newprivate depotfree. Native sector WK9.1 DynamicBaseClass
decode limitation; no sector edit. Current112sources exactly match WA3compile.
EndGame62 read-only did not contain historical entityID PS entry; no live door
state captured.6deploymentfixtures/20actions incl5interruptedrollbacks PASS.
Actual gameclosed Validate/Install/Verify/ValidateRollback PASS.52managedfiles
match;307savefiles/names/bytes unchanged. Current installed is VD1. Full51path
unreleasedZIP SHA ADA69E9D0AF95E2B836BD0914D7E9F4E3F7BEF09782F46506AD8F2B7B5EC2E62.
Rollback VD1 FIRST beforeLC4: gameclosed prealpha/viktor_door_vd1/deploy_01.ps1
-Action ValidateRollback then Rollback; recovery/viktor_door_vd1_01. Fileundo
NOTsaveundo. Physical opening/streaming/reload LIVEUNVERIFIED. No further test
request. Selected assessment candidate_02/assessment_01.json.
No game launch, questfact/save edit, Gitpush or release. See
docs/viktor_door_vd1_20261029.md and prealpha/viktor_door_vd1/candidate_02.

Latest 2026-10-28 SKIPPY VANILLA/WIKI AUDIT; NO FIX:
User requested read-only comparison of current Skippy restoration with vanilla
and Cyberpunk Wiki. Fresh 133-archive census found single providers for six
native MQ007 resources and four private SC3/S23 resources, no overrides;
installed S23/archive hashes match LC4, SC3 owner byte-exact. SC3 equip loop
matches native source and prior live downing-line/hologram report. Aim-only
autofire and nonresponsive jump prompt match vanilla. Draw frequency and reload
speech remain unmeasured/unverified. Concrete S23 Machine Gun gap: installed
MQ007_RESUME requires mod ModeTalkConfirmed1 and exact lethal/nonlethal/total
11/51/95; historical ManualSave-23 has total97 and fact absent, later run total100.
These saved/observed states cannot match the exact captured seam if retained;
current save not decoded. Wiki says about8 days from mode change; copied native
return phase node83 waits2game days from phase start plus other gates. No
elapsed-time reconciliation or live Regina/reacquire proof. No implementation,
install/game/save/fact write or test request. Evidence
docs/skippy_vanilla_wiki_review_20261028.md and
diagnostics/skippy_vanilla_wiki_audit_20261028_01/assessment_01.json.

Latest 2026-10-28 LC4 CREDITS-TO-SETUP COVER INSTALLED; LIVE PENDING:
User authorized implement+install. Candidate_02 under prealpha/credits_cover_lc4
changes only combined archive phase final_boards: Q307 guard before node27
instant black, same guard after27 suppresses original node28 instant reveal;
nonTower false branches retain28. Node27 credit notification and current
CreditsRolling->Started/fadeout->CoverReady181->fadein176->control path
untouched. New fact PTFRLC4_CreditsBlackHeld is owned diagnostic. Full51path
ZIP with only1 changed production file, archive1563 members/1562unchanged.
Graph13checks, exact112source compile reuse, 5newarchives no collisions,
5fixture deploymentcases incl4interruptions PASS. Actual gameclosed Validate,
Install,Verify,ValidateRollback PASS.301savefiles/names/bytes unchanged.
Installed archive SHA D6C1D7949C935BD567B81FB1011827D7313048DEAFDA68CB29B2A9D4250B091D.
ZIP SHA 56AB77B32CA382FFBF693853CF1D08C3112C84F7C66780F30461AD5884719FF4.
Rollback LC4 FIRST gameclosed via prealpha/credits_cover_lc4/deploy_01.ps1
-Action ValidateRollback then Rollback; recovery/credits_cover_lc4_01.
File rollback NOT saveundo. Watched/skipped first-frame LIVE UNVERIFIED. No
assistant game launch/fact/save edit/Git push/release. docs/credits_cover_lc4_20261028.md.

Latest 2026-10-28 CREDITS-TO-SETUP CAMERA FLASH INVESTIGATION; NO FIX:
User put Skippy aside and reports brief credits staging-world/Afterlife view
after credits close before setup cover. Fresh133archive three-depot scan:
expected PTFR/native phase providers only, one native menu. Installed4 scoped
hashes matchWA3. Current shared final_boards27->28 instantfadein exposes world;
setup awaits CreditsRollingfalse twice100ms thenStarted140/fadeout141250ms.
Popup Required waitsStarted. Candidate: guardedQ307 black after callphase return/
cut beforevideos notification, suppress28reveal onlyownedTowerhandoff, preserve
nonToweroriginal and cancellationrelease. Keep181CoverReadywait->176nativefade
release->PA3control beforefullsetup; holdingnativefadeuntilsetupdone deadlocks.
Native credits menu isAffectedByFadeout0; no rendered-frame proof. Skip path
native7black is later undone by28; nativeUI/scheduler ordering remainsunmeasured.
PrecloseUIbridge fallback onlyifresidualskiprace; Codeware ShowPopup isasync and
not atomiccover. No implementation/install/game/save/fact writes/testrequest.
docs/credits_transition_cover_20261028.md and diagnostics/credits_transition_cover_20261028_01.

Latest 2026-10-28 SKIPPY RECORDED-LOG INVESTIGATION; NO FIX:
User requested investigation from recorded logs. Snapshot ends19:58:31Toronto;
87SC3 status rows have no Stop/Stopped1 or fresh/resume/storytrue. Restored
27Oct11:17-11:25 has9Active entries (first+8reactivations), same claimed owner.
Later13:59 reload starts15s/26s are11s apart versus native30s rearm; conditional
cooldown explanation, not proof of selected/suppressed dialogue. Pre starts
11:44:21/11:45:01 are40s apart. Interruption high in both worlds; no per-line
selection/playback telemetry. Correction:11:20:33 clears dialogue-interruption,
NOT reload as prior runtime review stated. Historical proof retained.28Oct no
mq007fact changes/Active1 in capture; persisted claim+Active0 is wait-compatible,
not new failure proof. Installed S23 unchanged sinceSC3; archive/XL matchWA3;
5packed MQ007/Skippy resources unchanged by readback proofs. No new full winner
census. One-time story and restored reload speech remain unverified; no fix,
install/game/save/fact write/push/test request. docs/skippy_restoration_log_review_20261028.md
and diagnostics/skippy_restoration_review_20261028_01/assessment_01.json.

Latest 2026-10-28 WA3 + COMPUTER CO1 USER LIVE PASS:
After the combined candidate_02 installation, user reports "both fix worked as
expected." Interpret as user-confirmed WA3 NPC support and CO1 in-game computer
compatibility in their recent run. Evidence
prealpha/world_support_wa3/candidate_02/user_live_observation_01.json. The
user did not itemize individual NPC families, all296 owners, staged NPC-versus-
NPC fights, excluded24 progress-gated families/group1013, or save/reload.
Installed hashes,301 unchanged saves and rollback readiness remain as recorded
below. Do not request more game tests based on this report; no new install,
game/save/fact write, Git push or release was performed for this update.

Latest 2026-10-28 WA3 + COMPUTER CO1 INSTALLED; LIVE PENDING:
User explicitly requested installation. Selected candidate_02 under
prealpha/world_support_wa3 installed while game and launcher closed. Full51
Tower paths remain; one existing VirtualAtelier SetupNewTab.reds is the CO1
compatibility component. Exactly4 files replaced in a guarded52-path
transaction. 296 new passive support owners/421 community bindings, plus4
environment variants and1 greeting, join238 preserved WA2 owners. 351 new
archive resources; all1212 WA2 resources unchanged, total1563. Full112 REDS
compile incl CO1 PASS; independent owner10469 checks, private sector19780
checks,128archive winner/collision scan, 26 deployment fixture actions incl7
interruption rollbacks PASS. Actual Validate/Install/Verify/ValidateRollback
PASS and all301 save files/names/bytes unchanged. Unreleased51-path ZIP SHA
D050D8B4B7EF1E73C140748C43A5E29A24BBB5DF4D91138643FDA51FDBCF957C.
Recovery recovery/world_support_wa3_02. Roll back WA3+CO1 FIRST with game
closed via prealpha/world_support_wa3/deploy_02.ps1 -Action ValidateRollback
then Rollback; file undo is NOT save undo. Installed assessment
prealpha/world_support_wa3/candidate_02/installed_assessment_01.json. No game
launch, save/nativefact writes, Git push or public release. Gameplay LIVE
UNVERIFIED. 24 additional families with native progress/lifetime facts and
unreadable core group1013 withheld; actual scripted NPC-versus-NPC fights not
restarted. Previous "not installed" blocks below are historical, superseded.

Latest 2026-10-28 WA3 COMPREHENSIVE PRIVATE SUPPORT BUILD; NOT INSTALLED:
User reiterated continue fix, including NPC-versus-NPC fights. Native review
found Northside convoy and Charter Hill guards/bots fight controllers, but their
combat commands are tied to vehicles, faction attitudes, loot and progression;
do not restart those fights from an idle actor. Root then found 481 quest
notifier triggers in 222 new core sectors and 126 in 94 additional CE sectors.
These can reach existing native encounter consumers, so new support copies
filter them; 1246 also filters two automatic vehicle previews. Specs:
combat_review/filters_core_spec_01.json and filters_additional_spec_01.json.
Comprehensive private build source_comprehensive_09 has 315 sectors and one
streaming block, retaining 5,514 workspot placements. Independent
private_sectors/verification_comprehensive_01.json PASS 19,780 checks of
retained node definitions, opaque placement bytes, variant index relocations,
descriptor identity and file hashes. Group1013 is excluded because WolvenKit
9.1 cannot parse its native DynamicBaseClass worldNode; DO NOT promote its
unfiltered original to a new owner. Previous partial source_comprehensive_01
through_08 are rejected evidence. Existing WA2 resources remain unchanged.
Still needed: reconcile 315 filtered sectors with core/additional owner manifests,
native admission/lifetime gates for additional families, recook owner phases,
full112-source compile including CO1, fresh128archive winners, full51-path ZIP,
combined52-path deployment fixtures, actual closed-game install/verify/save
preservation. Current installed remains WA2. Three agents hit account usage
limit on 28 Oct; root continued the sector build. Do not claim live NPC fix.

Latest 2026-10-28 WA3 + COMPUTER CO1 COMBINED INSTALL AUTHORIZED:
User now explicitly authorizes installing the completed NPC successor with the
in-game computer fix included. This supersedes the earlier dont-install request.
Finish vanilla support review, full current-input compilation, archive readback,
winner checks and deployment/rollback fixtures before installing game-closed.
Include selected computer_overlay_co1 candidate_02; preserve external mod bytes
except its explicitly reviewed SetupNewTab.reds compatibility change. Capture
save hashes immediately before deployment and verify unchanged afterward. Root
owns actual deployment; agents build/review only. No game launch, fact/save
writes, Git push or release. Current installed remains WA2 until verified deploy.

Latest 2026-10-28 WA3 COMPREHENSIVE NATIVE NPC SUPPORT REQUEST; DO NOT INSTALL:
User requests implementing all possible NPC support types, including party
workspots, using vanilla as reference. Explicit follow-up: "dont install".
Build/audit/compile/package/fixture validation only; keep game installation at
WA2. Do not ask to close the game or capture saves for deployment. Work under
prealpha/world_support_wa3. Reopen prior ambient/audio/conversation exclusions
with concrete dependency review; audit beyond477combat-event refs, including
16district community routines and other native world roots. Preserve all1212
WA2 resources and existing owners/receipts. No native encounter reset/reward
replay. Stage full51-path successor. Runtime agent owns new support manifest/
Baseline mapping; native agent outsidefamilies/conversation/actions; validation
agent packaging/independent review+private160/161preview-spawner filtering;
root reviews existing200/202/210/461 environmentalvariant support.
User added NPCItemsForV_EdgerunnerItems, NPCItemsForVAtelier, VirtualAtelier
archives during audit; current128archives/112REDS inputs rather than125/64.
Use fresh winner checks and exact full compiler inventory, do not modify those
external mods. Currentparty193diagnostic and WA2installation remain below.

Latest 2026-10-28 PARTY193 MATCHED RUNTIME IDLE; READ-ONLY DIAGNOSIS:
User explicitly requests CET tests for a mixed hostile/neutral party; this
authorizes read-only command tests for this investigation despite the prior
general no-test-request constraint. Both entries share13790632485457691133:
goon_m entity9007047 and junkie_f10101731. Both live workspot/scene/combat=false,
active AI commands0. Command probes BOTH fixedIDs eachrun; duplicate pasted
sets are not four actors. Positions match native group193 dance workspots
ganger_010 (headphones dance) and ganger_002 (nightclub dance), respectively,
within0.000006m. Exact community hash -> Coastview root/28/33, prefab
cs_goons_rave_party_openworld_prefabLHWSZBA, quest_567b9ed4e0fd9ed5 sector.
No W3/WA2 owner for193; earlier ambient conversation/audio review exclusion.
Source11checks:60prefabnodes/21AIspots; all5communityentries'21unique spots
mapinside; goon_m12, junkie_f8. Player-trigger conversation is separate;
previewspawner spawnOnStart0/alwaysSpawnedfalse. Strong missing-support cause,
not yet repair-proven; no new resource-winner scan or repair/install/game/save
writes in this diagnostic. Current installed remainsWA2. Evidence
diagnostics/party_idle_20261028_01/native_review/assessment_01.json and
runtime_observation_01.json. No further sample needed from these two actors.

Latest 2026-10-28 WA2 BROAD ACTION SUCCESSOR INSTALLED; EXPANSION LIVE PENDING:
User confirms BA1 prototype works and requests all affected NPCs. Audited237W3
owners+240otherCErefs and168externalphases. WA2 adds5shooting controllers
(172173246250289),20nativevehicle radio/light/door controllers and250support.
ExistingBA1group179+all237W3resources/receipts unchanged. Newsupport total238.
Vehicleevents onceperReady lifetime, nativeNotReadyonlyrearm; no globalsafety
bounce replay. Shooting preserves full safetycut+nativecombat loops. Explicit
246foursecurityref rebind,256twoReady/NotReadyrefs,319Spawnedref; exact registry
names/counts preserved.2503line Baseline mapappend,64sourcefreshSCC PASS.
Independent295actionchecks+supportcrosscheck PASS; all1212archivemembers read,
1186oldbyteunchanged,68modarchive newresource0collisions. Full51paths replaces
archive+XL+Baseline only.23fixtureactions incl6interruptedrollbacks PASS.
Actual gameclosed Validate/Install/Verify/ValidateRollback PASS;
301savefiles/names unchanged. Userliveproof onlyBA1; WA2expandedruntimeunverified.
Source130/306 no currentcommunity/supportbinding; statefulmount/storysecurity/
attitude/scene/fullencounteroperations withheld with exactdispositions, NOT
allNPCgameplayclaim. Do not request moreingametests. No launch/save/nativefact
edit/Gitpush/release. Final candidate_01/assessment_01.json under
prealpha/world_actions_wa2. ZIP SHA 005971C576A5CC3788C434332F315595C528758F6D6B90FFAB95A52C641BCE91.
Rollback WA2 FIRST gameclosed via prealpha/world_actions_wa2/deploy_01.ps1
-Action ValidateRollback then Rollback; recovery/world_actions_wa2_01.
Fileundo NOT saveundo. docs/world_actions_wa2_20261028.md.

Latest 2026-10-28 BA1 USER LIVE PASS; BROADER ACTION RESTORATION REQUESTED:
User reports "the prototype works" and requests applying the action-controller
fix to all NPCs. This confirms the matched group179 BA1 result on their fixture;
speech, full streaming and save/reload were not separately itemized. BA1 remains
installed. Broad native action-owner census of237W3 owners and remaining240CE
rows started under prealpha/world_actions_wa2. Preserve BA1 and all existing W3
owners/receipts; no blanket Reactivate/ResetKillCount or arbitrary AI writes.
Latest logs pinned diagnostics/world_actions_wa2_live_20261028_01. Build full
consolidated successor after exact per-controller identity/lifecycle review;
do not generalize one group's live pass to all NPC families.

Latest 2026-10-28 BA1 BOTTLE ACTION CONTROLLER INSTALLED; LIVE PENDING:
User requested missing NPC action-controller fix. BA1 adds ONLY isolated native
Coastview group179 root/28/14/61, preserves existing W3 owner/receipts and all1185
prior archive members. New private resource retains32nodes43edges; only10native
communityrefs fully qualified to spawner8640981183263935109. Native random delay,
goon2/goon3 selection,7s shooting,combat targets/cuts and NotReady preserved.
15Tower/support gates plus one-time claim; whole-loop loss cut includes pending
Ready/timers, then gated rearm. No encounter Reactivate/ResetKillCount, prefab,
native/W3 fact or REDS changes. Independent46checks32768guardstates5negative
controls PASS. Environment28checks locate targets71/72 and security79/81 in
default/exterior_-33_-30_0_0, Exterior level0 questPrefabNodeRef0;125archive
census no mod override. Speech origin remains unbound; this is ONLY group179.
Full51-path successor replaces combined archive+XL;1186members,68modarchive
newdepot no collisions. Exact64-source CC1 compilation reuse;20fixture actions
incl5 interrupted rollback cases PASS. Actual gameclosed Validate/Install/Verify/
ValidateRollback PASS,301savefiles/names unchanged. Current installed BA1.
Recovery recovery/bottle_actions_ba1_01; rollback BA1 FIRST with gameclosed via
prealpha/bottle_actions_ba1/deploy_01.ps1 -Action ValidateRollback then Rollback.
File rollback NOT save undo. ZIP SHA
6348515E7103D45AB07A0EB006507CDD52F6335419AD25C5B7EB2D1DD285DFB5.
Manifest SHA B1E381553E2D2DD062BA01ED77465E08EC61DED2C2FF890F5AD732975C70FD9F.
Evidence prealpha/bottle_actions_ba1/candidate_01/installed_assessment_01.json,
native_review/assessment_01.json,environment_review/assessment_01.json.
docs/bottle_actions_ba1_20261028.md. Shooting/speech/streaming/save-reload LIVE
UNVERIFIED. No assistant launch,save/nativefact edits,Gitpush or release.

Latest 2026-10-27 SKIPPY POST/PRE LOG COMPARISON; READ-ONLY, NO FIX:
User requested compare recent post-ending Skippy run with pre-ending reference,
without implementation. Latest CET capture ends14:00:26 Toronto; report
diagnostics/skippy_post_compare_20261027_01/comparison_01.md. Post-ending
13:56 SC3 Claimed/Entered1,13:59:08 Active1; pre-ending11:43:58 towerfalse
SC3 Claim/Entry/Active0. Both windows log aiming and reload fact transitions,
enemy counters, dialogue and holo interruption flags. Post total97->100,
reload starts13:59:15/26; pre total94->98, reload starts11:44:21/11:45:01.
Post rapid_interrupt transition absent in latest window, pre had one. User
confirmed pre-ending reload/draw/aim-only lines and matching holo, but gave
no direct observation for this recent post run. Logs cannot prove speech or
hologram rendering, draw frequency, or equivalent line selection. No game,
save, native fact, installed mod, or source fix changes for this comparison.

Latest 2026-10-27 CC1 COASTER CUTOFF INSTALLED; WILSON/MOVING HEAT DIAGNOSIS:
User requested remove post-Double-Life one-time Jean entry. CC1 successor now
installed at SAME51 paths, replaces ONLY combined archive and S29 REDS; archive
1185 members, only MQ006 private entry resource changes. Both graph entry guards
and S30 fact table require q105_done0, which blocks new Jean post-Double-Life
admission. Existing issued owner progress, separate repeatable ride, SC3 Skippy
and W3 owners unchanged. Source64 SCC PASS, semantic2guard+3script-line diff
PASS,68archive one expected winner,20fixture actions incl5 interrupted rollback
PASS. Actual Install/Verify/ValidateRollback PASS,301 savefiles/names unchanged.
Full unreleased ZIP SHA B6E8A9BFCCB7EE39FF7F0D38CB89F1169E04C82C3CD5D25E5DF2504041F7E290.
Assessment prealpha/coaster_cutoff_cc1/candidate_01/assessment_01.json.
Rollback CC1 FIRST with game closed: prealpha/coaster_cutoff_cc1/deploy_01.ps1
-Action ValidateRollback then Rollback; recovery/coaster_cutoff_cc1_01. File
rollback NOT save undo. No assistant launch/fact/save edits/push/release.
New-load live behavior PENDING. Wilson usercurrent Entered1 but active0 and
call counts0; native q101_done wait4gamehours then outsidequestarea+content
gate. Native owner entry time unlogged, so delay failure not established.
MovingHeat journal Failed4 with accepted1/started1/active1/done0, consistent
with but not proof of pre-Tower acceptance and Tower failure. No quest/fact fix.
S22 accepted-message adapter source requires ROOT Inactive1 in both rows;
only its first phase may be Failed4. Current root Failed4 therefore does not
match S22 source; direct S22 Inspect/issued receipt still pending. Do not
restart/reset without exact native owner and reward/vehicle safety review.
docs/coaster_post_doublelife_20261027.md and
diagnostics/wilson_q304_20261027_01/assessment_01.json.

Latest 2026-10-27 USER ORDERS JEAN POST-DOUBLE-LIFE ENTRY REMOVAL; CC1 STAGED:
User explicitly chooses remove post-Double-Life one-time Jean entry, preserve
current save/repeatable coaster. CC1 candidate_01 in prealpha/coaster_cutoff_cc1
adds q105_done==0 to both MQ006 entry graph guards and S30 script fact-range;
native q105_complete writes q105_done after Judy main chain. Other resources
unchanged; archive1185, full51 paths, changed archive+S29 only. Full64-source
SCC PASS; semantic two-guard/3-script-line diff PASS; 68-archive single PTFR
winner PASS. Fixture deployment testing in progress; NOT YET INSTALLED. Game
process last checked closed. See docs/coaster_post_doublelife_20261027.md.
User live CET: Wilson S23 Entered1/Finished0,mq011_active0/done0, call
start/end count0/0; native root q101_done ->4 in-game hour delay -> outside
quest area/MinorQuestAndSts -> intro/active. Owner entry timestamp unknown;
not proven stalled. Pre-ending different load at12:07 showed two start/end
calls, not current restored call. Moving Heat S24 journal Failed(enum4),
accepted1/started1/active1/done0; fresh adapter protects. User hypothesis
accepted before Tower plausible; exact fail transition unbound. Diagnostics
wilson_q304_20261027_01/assessment_01.json. No fact/save edits.

Latest 2026-10-27 COASTER POST-DOUBLE-LIFE HANDLING + CURRENT S23/S24:
User completed Double Life then played Jean Love Rollercoaster due to mod. S30
post-Tower one-time wrapper intentionally permits fresh MQ006 after vanilla's
availability window. Copied minorquests parent retains q001_done>0,
q005_done>0 (q005 is Heist), q101_enable_side_content>0; no Double Life upper
bound. Fresh journal/native facts, owner exclusion, repeatable gate protect
duplicates; JC1 permits mq006_ride_no_quest0..1 and leases finale dialogue via
PTFRWORLD_Coaster_QuestOwns. SC1 removed14 Johnny finale dialogue events;
SC3 retains. User gameplay report supports availability, not exact reward/reload.
User CET S23 mq011 Wilson ready/permit/issued/finished1/1/1/0 fault0,
currentMatch/safe true: issued owner, call delivery unproven. S24 q304 Moving
Heat1/0/0/0 fault0 currentMatchfalse/safetrue, root journal state4=FAILED;
fresh adapter protects it. Earlier S22 accepted-message save not necessarily
same current branch. See docs/coaster_post_doublelife_20261027.md.

Latest 2026-10-27 MATCHED POST BOTTLE ACTION GAP:
User POST_MATCH9007073/spawner8640981183263935109/goon2: workspottrue,
scenefalse/combatfalse/forceShootfalse/holdPositionfalse/count0. Group179
Ready0/Request0/Claimed1/Entered1/Hold0. Ready/Request clear after claim by design;
do NOT reset receipts. Pre matched pause had holdPositiontrue/count1 and user
observed repeated firing/pauses. Native omitted phase61 supplies hold+shoot:
source and matched runtime support action-controller gap, not missing prefab
admission. One post sample, no fresh30s observation; speech still unbound.
Review isolated action owner compatible with persisted W3 owner, exact refs,
targets, duplicates, combat/NotReady cuts and reload before successor. Never
restart full encounter Reactivate/ResetKillCount. No repair/install or AI writes.
Evidence diagnostics/bottle_shooting_20261027_01/matched_post_observation_01.json.

Latest 2026-10-27 PRE GOON2 IDENTITY AND PAUSE CONFIRMED:
Combined BOTTLE_PRE_MATCH confirms9007073/spawner8640981183263935109/goon2,
forceShootfalse/holdPositiontrue/count1. User clarifies firing bursts, pauses,
then resumed fire. False sample is normal pause-compatible, not broken behavior
or evidence of permanently distinct shooter/nonshooter roles. Next exact post
spawner+entry capture with workspot/scene/combat/AI and group179 owner receipts.
No need further pre samples. Source shooting omission remains; live post pending.

Latest 2026-10-27 PRE AI SHOOTER/NONSHOOTER CLARIFICATION:
User attributes forceShoot=false/holdPosition=true/count=1 to a non-shooter,
and forceShoot=true/holdPosition=true/count=2 to a shooter. Outputs contain no
identity; earlier command hardcoded9007073. Do not assume same-actor samples or
assign new result to goon2 without combined identity+AI capture. Next capture
actual pre shooter with one look-target read, persistent spawner/entry and AI.
Native review complete21checks: root/28/14/61 32nodes43edges absent from W3
three-node owner. Selection is RANDOM goon2/goon3, not strict alternation.
Source omission matches symptom; matched post runtime pending; speech unbound.
No game/save/AI writes or install. See docs/bottle_shooting_20261027.md.

Latest 2026-10-27 BOTTLE SHOOTER SPAWNER MATCHED; POST CAPTURE PENDING:
Directpre-ending stubquery succeeded: actor9007073 spawner8640981183263935109
entrygoon2. W3manifest03 AND installedBaseline map to group179/PTFRWW2_179_,
Coastview native root/28/14 shooting_openworld_002 prefabPFINICQ, community
cs_goons_shooting_com;#ce_pac_cvi_112_com, quest_fee7188755b56c93.streamingsector.
Group already supported, NOT a newly omitted owner. Earlierrestoredlog11:42:36
Request179 only; exact postactor+workspot/scene/combat+Ready/Request/Claimed/
Entered/Hold pending. Needcompare same spawner/entry, not assumeentityIDcrosssave.
Native action/dialogue dependency review delegated read-only to skippy_stop_trace,
evidence diagnostics/bottle_shooting_20261027_01/native_review. No newinstall or
quest/AI writes. docs/bottle_shooting_20261027.md. User permits commandtests.
Initial source trace: native root/28/14/61 separately commands ShootAt forgoon2/3;
W3 group179 supportowner restores aimworkspot but noShootAt graph. Sourcegap
matches symptom; not yet live command-proven/repaired. Before changing saves,
capture actor9007073 AIForceShootCommand/AIHoldPositionCommand/count3samples
~8s apart (CETclosedbetween); then exactpostmatch+ownerreceipts. NoAIcommandwrites.

Latest 2026-10-27 PRE-ENDING BOTTLE NPC IDENTIFIED; SKIPPY LIVE REFERENCE:
User captured bottle shooter record Character.cvi_scavenger_grunt1_ranged1_nova_ma,
entity9007073, pos(-2107.72265625,-1901.9067382813,7.6898651123047), workspot=true,
scene=false,combat=false; user saw shots and heard lines pre-ending. Second
look-target query returned nil, so spawner/entry are still pending. Next read-only
command uses CreatePersistentID(EntityID.FromHash(9007073ULL), stub component)
directly, with null guard; no repeated look-target dependency. Don't treat entityID
alone as cross-save community identity or infer exact prefab from coordinates.
User ALSO explicitly confirms pre-ending Skippy reload remarks, draw remarks,
aim-only shot/comment and matching hologram (answer all). Currentmodsetup remains
installed; NOT clean-unmodded test. Log11:43:58 tower=false andSC3Claimed/Active0,
then aiming11:44:15-19, reload11:44:21-23+11:45:01, interrupt11:44:25-11:45:22,
native total94->98. Do not claim logs transcribe speech; live observation from
user. Restored reload/draw-frequency concerns remain separate/unresolved.
docs/skippy_preending_reference_20261027.md; pinned logs and user_observations_01
under diagnostics/bottle_skippy_preending_20261027_01. No game/save/fact writes.

Latest 2026-10-27 BOTTLE-SHOOTING NPC FOLLOW-UP; PRE-ENDING CAPTURE REQUESTED:
User reports an ambient NPC shoots bottles and speaks pre-ending, but the same
NPC only aims without shots/lines in the restored world. User is currently in
the pre-ending world and explicitly ready for console tests. This supersedes
the earlier no-in-game-test request for this investigation. Begin with read-only
target identity/position/workspot/scene/combat and persistent spawner/entry.
No actor identified or comparison captured yet. Match exact spawner+entry before
selecting native prefab/scene dependencies or proposing a repair. Current SC3
includes W3; do not assume restoring prefab workspots also restored every action
or dialogue controller. No broad community/AI/fact resets are authorized by the
diagnostic request. Historical commands in CET scripting.log use GetLookAtObject,
IsActorInWorkspot and GetConstAccessToPSObject; CET dofile is unavailable.

Latest 2026-10-27 SC3 PARTIAL LIVE PASS; TRIGGER REVIEW, NO INSTALL:
User reports downing-enemy lines and matching hologram expressions now work.
Also reports aim-only "reason for firing unknown", near-every-draw lines,
no observed reload reactions, and no response to "jump to confirm". Current
51 SC3 hashes match. Latest11:14-11:25 Toronto session shows SC3 claim/entry,
repeated equip/unequip Active toggles without Stop, reload/aiming native fact
transitions and native enemy count95->97. LatestManualSave-23 confirms SC3
Claimed1/Entered1/Active1/Stop0/Stopped0, bothS23storyIssued0, oldSC1Stopped1.
Fresh125archive census has single native winner for root/comments/reset/scene;
root/comments/reset match old donors, reaction scene matches reviewed donor.
Independent reviews find aim fact deliberately requests weaponShoot before
random Autofire commentary; native draw has four-outputIgnoreAllUsed with only
one speech path. Original parent also restarts comments on unequip, so this
is not a demonstrated SC3 frequency regression. Reload waits2.5s plus equipped/
Tier1/no-competing-section gates and two-output randomizer, one speech path;
30s rearm. Actual missed reload gate/reason not logged; audible reload unverified.
Jump line is nativeAutofire variant:4.905s section then cleanup, no jump response.
Exactprop SceneScreen, exactwidget CustomAnimationsGameController, six animation
callbacksNone; no authored input/confirmation continuation. Entity/two widgets
also single native winners/nooverride. No demonstrated trigger bug to patch.
No successor/install/game launch/nativefact/save edits/push/release this review;
51installed files and301save files byte-identical. Current remains SC3. Do not
ask in-game tests/commands. One-time quest and reload still LIVE UNVERIFIED.
Evidence diagnostics/skippy_triggers_20261027_01; docs/skippy_triggers_20261027.md.
Selected runtime verification_02, scene assessment_01;46source/log/UIchecks PASS.
Review assessment_01.json SHA
9816091C4E359CFDD2D6F5BDB879A5E774BD772E57352B54D1162BBE80FA8DA8.
Native equivalence is NOT restored-game runtime proof for every reaction.

Latest 2026-10-26 SC3 SKIPPY EQUIP LOOP REPAIR INSTALLED; LIVE PENDING:
User confirmed SC2 still has no Skippy combat lines/hologram. SC2 log22:52:10
and read-only ManualSave-23 show old Ambient Claimed1/Entered1/Stopped1/Stop0.
SC1 incorrectly treats native unequip TurnOff as permanent owner termination;
SC2 requires Stopped0 and cannot recover this saved state. SC3 preserves old
receipt/resource and requires old retirement before entering a distinct private
owner with the exact native equipped wait -> ambient -> TurnOff -> equipped loop.
Active old owner must acknowledge Stop; unclaimed old owner is blocked/cancelled.
One-time S23 quest priority cuts the whole new loop, including its pending wait,
and waits for new Stopped receipt. No native quest/counter/mode/item/reward reset.
Selected prealpha/skippy_ambient_sc3/candidate_02; native candidate_02. Both
candidate_01 resources REJECTED due WolvenKit DeepCopy shared-socket duplication,
NEVER installed. Direct native object preserves6graphs/68nodes/73edges;
74payload/guard checks and independent88assertions/17guardcases/3negativecontrols
PASS. Same script hash reuses64-source publicCodeware1.21.1 SCC PASS.
Full51-path successor replaces ONLY combined archive, XL and existing S23 REDS;
1185members=1184byte-unchanged+new SC3 owner. Fullreadback/68archivecollision and
4native dependency winner checks PASS.20recorded fixture actions incl5interrupted
rollbacks PASS. Actual gameclosed Validate/Install/Verify/ValidateRollback PASS;
all51hashesmatch,301savefiles/names byte-identical. Recovery
recovery/skippy_ambient_sc3_01; rollback SC3 FIRST with gameclosed via
prealpha/skippy_ambient_sc3/deploy_02.ps1 -Action ValidateRollback then Rollback.
File undo NOT save undo. Full unreleased ZIP SHA
0644159D08F51568A3F15AFC9A360348B3838B9CF9686E6B826C8CCC78D35547;
manifest AF2B50683688B8D15425F6DE90067539B7D5842B52E940A36974BD16E6BB5DAD.
No assistant launch/save/nativefact edit/Gitpush/release. Speech, hologram and
one-time quest LIVE UNVERIFIED. Do not ask further in-game tests/commands.
docs/skippy_ambient_sc3_20261026.md; current installed SC3 supersedes SC2.
Final candidate_02/assessment_01.json SHA
FEE1DFEF7A220B7AF1D188B1698164A7F54CB1B0CC4AF4D0705D24D5475612DB.

Latest 2026-10-26 SC2 SKIPPY AMBIENT ADMISSION INSTALLED; LIVE PENDING:
User reported Skippy combat lines still silent under SC1. Latest SC1 ArchiveXL
log confirms private ambient phase merged; Skippy reload fact changed, but no
SC1 owner-entry telemetry existed. Saved ManualSave-23 has exact Skippy item,
95 native Skippy enemy counts and no S23 one-time owner issued. SC1 driver
could defer on unrelated HS1/Common/BodyPolicy/overshield gates. SC2 narrows
ambient admission to completed Tower, living player and released gameplay;
progressed Skippy state does not depend on snapshot/transaction quantity while
equipped. Fresh gun retains snapshot/item priority for one-time quest. Native
private inventory and story-owner exclusion/stop guards remain. Stage-change
ModLog PTFR_SkippySC2 added; no fact reset or reward/Regina branch requested.
Full 51-path successor changes ONLY existing PTFR_SideJobsS23.reds; combined
archive/XL and 48 others byte-identical to SC1, retaining coaster Johnny VO
removal. 64-source public Codeware compile PASS, 20 deployment fixture actions
incl five interruption rollbacks PASS. Actual closed-game Install/Verify all51/
ValidateRollback PASS. Recovery recovery/skippy_coaster_sc2_01; rollback SC2
FIRST via prealpha/skippy_coaster_sc2/deploy_01.ps1 -Action
ValidateRollback/Rollback with game closed. Unreleased full ZIP SHA
6C78604BB0CD14FD8444912B61C118AC40231DDA64EA035469C4E42F037D9948.
Initial 301-file save baseline was taken while user still playing: ManualSave-23
three files and user.gls changed at22:48:59-22:49:00 before22:49:36 install
receipt; other297 unchanged. No save overwrite, assistant game launch/fact edit,
Git push or release. Live lines/hologram and untested Skippy quest PENDING;
do NOT claim fixed until observed. docs/skippy_coaster_sc2_20261026.md and
prealpha/skippy_coaster_sc2/candidate_01/save_comparison_02.json. Do not ask
user for further in-game test commands under standing user constraint.

Current production packaging rule (user request, 2026-10-26): keep future fixes
in a successor of the consolidated package. Replace affected files at their
existing install paths and remove superseded paths; do not pile separate hotfix
overlays into the game folder. Archive previous versions in the workspace for
debugging and rollback. Add an installed file only when a distinct engine
resource or script module requires it. Check the full manifest, compilation,
resource winners, save preservation and rollback before installing a successor.
See README.md and docs/full_consolidation_v1.md.

Latest2026-10-26 SC1 SKIPPY AMBIENT AND COASTER VO SUCCESSOR INSTALLED; LIVE PENDING:
User reports hostile NPC animations restored under W3 and requests Skippy combat
one-liners/hologram plus no Johnny VO on Love Rollercoaster. Skippy one-time
quest remains UNTESTED. SC1 rehosts ONLY original MQ007 ambient node3 behind
owned Items.mq007_skippy, Tower/safety and S23 handoff gates; no pickup, mode,
counter, journal or reward replay. Native Skippy inner six graphs/68 nodes/73
edges compared after binary cook. The private MQ006 finale removes all14 Johnny
scnDialogLineEvents,14 debug symbols and2 persistent references;60 other
dialogue/271 scene events and section durations/5 JC1 quest-own conditions
preserved. Separate repeatable coaster scene has0 dialogue events. Full51-path
successor adds one archive member=1184; replaces ONLY combined archive, its XL
and existing PTFR_SideJobsS23.reds.64-source public Codeware1.21.1 SCC PASS;
all1184 packed members read back;68-archive collision scan has only expected
old MQ006 PTFR winner.20 fixture actions incl5 interrupted rollbacks PASS.
Actual closed-game Validate/Install/Verify/ValidateRollback PASS;301 savefiles
byte-identical. Unreleased ZIP SHA
DEA168F87D3D074BF71780C7CA6E50642851314B55EBABC5EE310739448DD504.
Recovery recovery/skippy_coaster_sc1_01. Roll back SC1 FIRST, game closed,
using prealpha/skippy_coaster_sc1/deploy_01.ps1 -Action ValidateRollback then
Rollback; file undo is NOT save undo. W3 remains previous production package.
No assistant game launch, save/fact edits, Git push or public release. Gameplay,
reload, and one-time Skippy quest are live pending; do not claim live fix. See
docs/skippy_coaster_sc1_20261026.md and prealpha/skippy_coaster_sc1/candidate_07.
Current installed SC1.

Latest2026-10-26 W3 AMBIENT WORKSPOT SUCCESSOR INSTALLED; NEW GROUPS LIVE PENDING:
WW1 Pacifica car-goon group patrol resumed after user dismounted; only this one
group has live proof. W3 extends W2 from206 to237 exact native combat-event
prefab owners (245 spawner IDs), NOT 237 NPCs. The31 Rancho Coronado native
authored `/#rancho_coronado` and registry `/rancho_coronado` prefab resources
were extracted and byte-compared per group; original authored owner/community
pairing retained. Private Rancho phase has31 owners/496 bounded gates; full
64-source SCC with public Codeware1.21.1 PASS. Combined archive1183 winning
members=W2's1182+one new phase; all readback, zero new-resource collisions in
68 installed archives. Full51-path unreleased ZIP SHA
FDC18332867CADD84A6FC0ACE22E0FDF491B696173DBA8EF7A78ACF7ED29508D.
Actual install replaced ONLY combined archive, its XL and existing Baseline
REDS; no new game paths.20 fixture actions incl5 interrupted rollback cases,
actual Validate/Install/Verify/ValidateRollback PASS,301savefiles unchanged.
Previous3 files in recovery/world_workspots_w3_01. Rollback W3 FIRST with game
closed via prealpha/world_workspots_w2/deploy_w3_01.ps1 -Action
ValidateRollback/Rollback; file undo NOT save undo. Then W2 rollback only if
needed. W3 does not establish all-NPC patrol:240 other combat-event source
rows and courier/scene/quest/non-combat families remain outside verified scope.
No assistant launch, save/fact writes, Git push or public release.
docs/world_workspots_w3_20261026.md; source/proofs under
prealpha/world_workspots_w2/candidate_04. Current installed W3.

Latest2026-10-26 W2 AMBIENT WORKSPOT SUCCESSOR INSTALLED; BROAD LIVE PENDING:
User reports WW1 probe05 Scav car-goon patrol resumed after dismount. Read-only
gamelog shows 3matched actors, owner Request then Claimed/Entered1; one-group
live pass only. W2 reviewed477 native combat-event prefab refs:206 exact
source-matched support owners admitted,31 Rancho path mismatch and240 other
rows withheld. Counts are prefab refs/owners, NOT NPCs. Nine new private quest
phase resources hold205 additional original prefabs; the proven WW1 resource
and saved claim facts are preserved byte-exact. Admission requires a living
streamed actor with exact native community spawner/active entry and two
settled safe samples; no native combat reactivation/reset/AI role writes.
Full51-file successor, combined archive1182members=1172old+10new, same51
game paths. Installation replaced ONLY combined archive, archive.xl and
existing PTFR_RestorationBaseline.reds, removed all3 temporary WW1 files.
64-source SCC on publicCodeware1.21.1 PASS;205 graph readbacks/3280 gate
assertions,69-archive collision scan(only expected retired WW1 probe hit),
23fixture actions incl6 interrupted rollbacks PASS. Actual closed-game
Validate/Install/Verify/ValidateRollback PASS;301 save files unchanged.
Recovery recovery/world_workspots_w2_01. Rollback FIRST with game closed via
prealpha/world_workspots_w2/deploy_01.ps1 -Action ValidateRollback/Rollback;
file undo NOT save undo. Full local unreleased51-file ZIP SHA
9931A611F7E2DAF73CB13DF0C78A0A27CE5A49F4324C0A387418B6ED3A312A52.
Assessment prealpha/world_workspots_w2/assessment_01.json. No assistant
game launch/fact/save edit/Git push/release. NEW205 owner patrol/reload LIVE
UNKNOWN. El Coyote actors, GIM courier and separate NPC families remain
unbound/not claimed fixed; user forbids further in-game test requests. W2 is
NOT a verified all-NPC repair. See docs/world_workspots_w2_20261026.md.

Latest2026-10-26 WW1 LIVE PASS; W2 BROAD AMBIENT REPAIR IN PROGRESS:
User reports exact Pacifica car goons resume patrol after dismounting from
motorcycle with probe05. Read-only gamelog18:28:31-50 shows admission waiting
while mounted, then eligible3, native prefab owner requested, and
Request/Claimed/Entered/Hold=0/1/1/0. This confirms only CVI116 owner entry and
user-observed patrol recovery, not every NPC family. Pinned log
diagnostics/world_npc_idle_20261026_04/gamelog_probe05_live_success.log SHA
23A822597915AE70BBDC2D42CC89D136D9E7B54C65B9CCC83E600A8373C145E5.
User now requests main fix for all NPCs; scope interpreted as post-Tower
nonquest ambient hostile behavior. Do not request further in-game tests.
Broader 477-ref offline census is NOT an allowlist. New W2 audit_01 found237
resolved support-shaped owner candidates/240 excluded; static NodeRef mapping
245 community hashes including WW1 exact hash. Native owner binary validation
found31 Rancho Coronado path mismatches (`/#rancho_coronado` authored versus
registry `/rancho_coronado`); do NOT use those registry paths as owners. Read-only
exact-native-resource lookup found all31 real authored sectors; they still need
decode and classification. W2 has NOT built/compiled/installed a production
successor. Current install remains JC1 51 paths plus WW1 three-path temporary
probe05. No assistant game launch, fact/save edits, push or release. Eventual
production update MUST be a full 51-path consolidated successor removing the
three probe paths, with save-compatible owner migration, manifest/readback,
collision, compilation, rollback and save-preservation checks. Sources
prealpha/world_workspots_w2 and docs/world_hostile_idle_report_20261026.md.

Latest2026-10-26 WW1 PROBE04 LIVE NEGATIVE; PROBE05 INSTALLED, LIVE UNKNOWN:
User reports the exact Pacifica car-goon Scavs remain idle under installed WW1
probe04. Do not call the ambient issue fixed or ask for more in-game tests.
Read-only game logs confirm REDscript compiled and ArchiveXL merged the private
quest phase, but do NOT prove owner entry, Ready=1, actor admission or workspot
activation. At the exact Scav location, the activity log reports player
scene/dialogue=true/false during ordinary play; probe04 rejected scene=true.
This is a plausible gate error, not a confirmed complete cause. Probe05 changes
only the probe REDS file to reject active dialogue instead, and emits ModLog
PTFR_WW1 stage transitions (attach, near/Ready, waiting, candidates, request,
receipt). Archive and XL are byte-identical; JC1 51 production paths unchanged.
65-source public Codeware SCC PASS, 4 installer interruption/rollback fixtures
PASS. Actual game-closed Validate/Install/Verify/ValidateRollback PASS. All 301
save files byte-identical across install. New script SHA
53923E0F1E1F6A760ABFA3FF6278B50B5882A4B51A2394DE4764038ACB68D8EB.
No assistant game launch/fact/save edits/push/release. Current install is JC1
51 paths plus 3 temporary WW1 probe paths; PROBE05 runtime result UNKNOWN.
Assessment diagnostics/world_npc_idle_20261026_03/assessment_01.json.
To remove probe with game closed, rollback probe05 FIRST via
prealpha/world_workspots_ww1/deploy_probe_05.ps1 ValidateRollback/Rollback,
then probe04 via deploy_probe_04.ps1 ValidateRollback/Rollback. Production
ambient fix still requires a new 51-path consolidated successor removing all
probe-only files. See docs/world_hostile_idle_report_20261026.md.

Latest2026-10-26 WW1 SCAV WORKSPOT PROTOTYPE INSTALLED; LIVE UNTESTED:
User explicitly requested install of temporary additive prototype after
clarifying prototype may add files; eventual TOTAL production fix must return
to51consolidated paths and remove every probe-only path. Selected
prealpha/world_workspots_ww1/probe_04 adds EXACTLY3 game files: one archive,
one archive.xl, one REDS script; none of JC1's51 paths replaced. Source
candidate02 nativeprefabowner has16guards/4negativecontrols; standalone script
adds player-load startup hook, noNPC hook, and bounds original living Scav
spawner/entry+two settled safe samples.65-source SCC with publicCW1.21.1 PASS;
one-resource readback,68-installed-archive zero collision, ZIP3 hashes PASS.
deploy_probe_04.ps1 six interruption/rollback fixtures+preexisting refusal PASS.
Gameclosed actual Validate/Install/Verify/ValidateRollback PASS; all51JC1 files
hashmatch.301save files before/after byte-identical. Recovery receipt/ZIP at
recovery/world_workspots_ww1_probe_04_01; rollback FIRST when gameclosed:
prealpha/world_workspots_ww1/deploy_probe_04.ps1 -Action ValidateRollback,
then -Action Rollback (removes only3 exact probe files). ZIP SHA
1214D5CEFA35F6A80264900AF7DDDA60F5928829170D3A15B9F63226D051E5F1.
Installed assessment prealpha/world_workspots_ww1/probe_04/installed_assessment_01.json
SHA FA9203120D310D60E10C4D311C3E20E24731F2C2BCC0F8860DA268669DBA31EA.
No assistant game launch/fact/save edits/Gitpush/release. Ambient movement,
runtime owner entry and reload NOT live verified; user forbids further in-game
test requests. The total fix still needs per-group safe eligibility and the
51-path successor; this prototype covers ONLY original CVI116 Scavs.

User packaging clarification (2026-10-26): the temporary single-community
Scav workspot PROTOTYPE may use additive installed files for diagnosis. The
TOTAL production ambient fix must return to a 51-file consolidated successor,
with all prototype-only paths removed. The local additive WW1 probe04 is
three distinct engine files (archive, ArchiveXL registration, REDscript),
now installed at the three additive paths above. Probe03 lacks guaranteed startup
and is historical only. Probe04 adds one PlayerPuppet load hook and no NPC
wrapper; 65-source public-Codeware compilation, one-resource archive readback,
68-archive collision scan, three-file ZIP readback and installed JC1 51-file
hash check PASS. Do not present it as the total fix or a public release.

Current investigation constraint (user, 2026-10-26): continue the hostile-NPC
ambient-behavior investigation with multi-agent work allowed, but STOP asking
the user for in-game tests. Use existing source, logs and saved evidence.
The earlier pending pre/post AI-role CET request is superseded by this rule.

Latest2026-10-26 OFFLINE HOSTILE NPC WORKSPOT TRACE; NO INSTALL:
Three-agent source/save/world audit maps3savedCVI116Scavs' usedSpotIds exactly
to3human spots in original #ce_pac_cvi_116 quest prefab. Actualcommunity spawn
area remains separate defaultworld. Native owner root/28/18 PhaseInstancePrefabs
WAS OMITTED byWA1, which copied onlyPhaseGraph: negativeWA1 doesNOTreject missing
prefab ownership. Saved sampledAI StoryTierGameplay, nullmount/unmount,notalerted;
native idle tree selects/moves/uses communityspots withoutAIPatrolRole.
Exact24nodeprefab has2previewcars spawnOnStart0/alwaysSpawnedfalse,triggeronly
notifier,noauthoredreset; workspotscurrentEP1unpaused.57native+68modresource
winnercheck0modoverrides for7exactresources. Savedprefabhandleropaque/identical;
aggregate23->0savedworkspots NOT exactruntimeactivationproof. Cause remains
strongsourcecandidate, no gameplayfixclaim. Local WW1 exact-group persistent
prefabowner prototype only; no Reactivate/ResetKillCount/nativefact/AIrolewrites.
CompletedTower16guards+readback/4negativecontrolsPASS; existingmodule admission
scaffold64sourceSCCpublicCW PASS. NOT installed/packed/registered;51JC1paths
VerifyPASS. Full473owners/477refs inventoried;385refsresolve374unique paths,
353sectorsdecoded,21absent,92unresolvedrefs.254support-shaped,87ambientreview,
10otherreview,2auto-spawnprefabs(CVI07/CVI09)withheld; NID08hascorpses+savearea.
CensusNOTallowlist; automaticspawn/listener/alias hazards requirepergroupreview.
Selectedlocalownerprototype candidate_02; compiledadmission03(noNPCwrapper,
boundednearbylookupatoneexactsite)64sourcesPASS. User forbids in-game test asks.
Evidence diagnostics/world_npc_idle_20261026_02; prototype prealpha/world_workspots_ww1;
docs/world_hostile_idle_report_20261026.md corrects earlierWA1 interpretation.
Finalassessment01SHA38B609AD0C1B1E92D7EC0682DEB67077C3277D9DDC83F58B3950F1D3B81CE0E7.
All16districtowners share fresh-proven Tower-retired ancestry; courieractor9016721
and exactElCoyoteactors stillunbound, notclaimedfixed. PrototypeNOTdeployableZIP;
do notinstallsourcefolder. No launch/install/save/fact/push/release thispass.

Latest2026-10-26 WA1 HOSTILE NPC PATROL TEST NEGATIVE; JC1 RESTORED:
User confirmed exact Pacifica Scav record/spawner13399962301655001666/entrygoon1
patrols pre-Tower, animates in place post-Tower; detection/combat work,
pedestrians/traffic normal, time unpaused/no dilation. Native combat-event
parent ends with Tower, but community active pre/post. Scoped Codeware
ActivateCommunity changed group but idle remained. WA1 rehosted only vanilla
#ce_pac_cvi_116 loop in private gated phase inside same51-path package;
1172 old archive resources unchanged, 1 new; XL+archive replacements only.
64-source SCC,1173-member readback, semantic 11-node/12-edge preservation,
67-archive collision scan,38 installer fixture actions PASS. Actual Install/
Verify/ValidateRollback PASS; user set PTFRWA1_TestRequest on disposable
post-ending load and reports STILL IDLE. Thus native loop reinstatement NOT
sufficient; no production ambient fix. WA1 Rollback PASS, current JC1 all51
paths Verify PASS. Game auto-rewrote AutoSave-18; test slot archived under
recovery/world_combat_wa1_01/test_autosave_18 and original3files restored
from byte-verified pretest backup. 300/301 baseline save files now hash-match;
only user.gls changed by game (no original byte backup; current archived).
No assistant game launch, quest/kill fact changes, Git push or release.
Docs docs/world_hostile_idle_report_20261026.md and docs/world_combat_wa1.md;
workspace candidate prealpha/world_combat_wa1/candidate_04. Subsequent offline
audit above supersedes the request for more live AI comparisons and identifies
omitted native prefab ownership. Do not blanket restart16 district CE roots
or repeat failed activation/loop test. JC1 production install remains.

Latest2026-10-26 JC1 JEAN LOVE ROLLERCOASTER REPAIR INSTALLED; LIVE PENDING:
User's post-Tower S30 Inspect ready1/permit0/issued0/finished0/fault0/entered0,
baselineFreshtrue, eventually safetrue; only blocker
mq006_ride_no_quest1 expected0. User had not ridden. Other MQ006 done/repair/
repeatable/PTFR-owner facts all0. Native MQ006 graph sets noquest1 when opening
standalone route BEFORE ride, so S30 guard was too strict. JC1 admits0..1 in
both private entry guards and S30 FactMax0; all other safety gates retained.
Private finale's five native noquest conditions instead test own
PTFRWORLD_Coaster_QuestOwns==0, so one-time story lease1 selects Jean dialogue.
Native saved fact remains1; no CET/save/fact rewrite. Full51-file successor
replaces combined archive+S29 REDS, no added game paths.1172 archive members
readback; only2 resources changed; scene has exact15 value diffs in5 conditions;
64-source SCC with public CW1.21.1 PASS;38 deployment fixture actions incl6
interruptions PASS. Two changed resources have0collisions among67other mod
archives. Initial actual stage-copy denied by sandbox; both game
files stayed RC2, rollback PASS, interrupted backup archived separately.
Elevated retry installed; Verify all51 and ValidateRollback PASS;301 savefile
hashes unchanged. No assistant game launch/Git push/release. Complete ZIP SHA
6AC85EA6A325DF78FEA39101C4313C4EAE39B17B676E74E0F2EF59316E36C431.
Evidence/source prealpha/coaster_jean_jc1/assessment_01.json
SHAB52D0DC4ABF87245A998CBFCEBACD027412B35FD80CA983C33F1AB382ADE8555;
doc docs/coaster_jean_jc1.md.
Rollback JC1 FIRST via prealpha/coaster_jean_jc1/deploy_01.ps1
-Action ValidateRollback/Rollback; backup recovery/coaster_jean_jc1_01.
Interrupted rolled-back backup recovery/coaster_jean_jc1_interrupted_01.
File rollback NOT save undo. NEXT user cold-load same save, S30 Inspect,
Jean introduction/repair/ride/finale/reward/reload, watch duplicate owner/cart.
Current installed JC1; live route pending.

Latest2026-10-26 RAYMOND-PATTERN AUDIT OF ALL RESTORED ENTRY OWNERS; NO INSTALL:
User requested similar issues across all restored quests. Read-only screen of
81selectedsidejob+80gig roots,144distinct current RC2 owner resources; all51
installed PTFR package hashes match.21owners have any time condition; only
MQ040(12h,USER quest returned after SkipTime) and MQ028 EveryBreathYouTake(2d)
have substantial mandatory Issued->Entered game-time waits.12other owners use
two-tick settle/recheck.80gig entry owners have no time condition in their
private owner graph (8U10 use other receipts; external/native progress unproven).
Current native MQ018 KillingInTheName writes started/active before message phase
but S29 fresh guard requires0; MQ028 writes started before call but S29 requires0.
Both are SOURCE candidates for inactive-journal partial-owner deferral; no live
matching failures. Steven ShowMustGoOn has nested66h invitation branch when
biomonitor_ana0; copied fallback root Inactive/fact0, prior timer origin unknown.
SexOnWheels3d follows reactivated journal; possible repeat unproven. S30 trio
early fact ordering rechecked, no analogous persistent wait established. Static
entry audit does NOT explain11 missing icons or certify gameplay/reload.
No assistant game launch/install/save/fact/public release. Matrix161 and pinned
assessment diagnostics/raymond_pattern_audit_20261026_01/assessment_01.json
SHA6272B540AB03C3B622DB5450D7F43882F60401FF3710A44E621BDB1A4DED7C25;
docs/raymond_pattern_audit_20261026.md. Current RC2 remains installed.

Latest2026-10-26 RC2 RAYMOND LOCAL TEST REPAIR INSTALLED; ENTRY LIVE PASS:
User reports Pepe+Valentinos/corpo physically present but idle after Tower.
Captured mq040_active1/done0/pepe_intro0/gangers_done0/barman_default0/
PTFRB0STPEPE_OwnerActive0; S29 fresh guard expected active0. Original native
owner liveness still unproven; q307_main_game_killed fact not decisive. RC2
admits active1 only with owner/barman off and original progress guards, two
settled ticks. Private MQ040 active1 branch skips setup spawns and enters native
bar phase; active0 path unchanged. Full CR1 successor51paths;2 existing install
files replaced (combined archive+S29 REDS),2 private resources changed of1172;
all30 CR1 repairs retained.64-source SCC PASS, graph/guard/0-collision/readback
checks PASS,38fixture actions PASS incl6 interruption points. Actual closed-game
Install/Verify/ValidateRollback PASS;301 save files unchanged. Previous files in
recovery/raymond_rc2_01. First sandbox-denied attempt made zero game changes;
rolled-back receipt retained recovery/raymond_rc2_interrupted_01. Full unreleased
51-file ZIP SHA EC133E6CF8CC3A56196D95309B0B4F3E7462538A6B385EFB79D331736B28F8B7.
No assistant game launch/save/fact/public release. First user post-install
Inspect: ready/permit/issued/finished1/1/1/0,entered0,currentMatchtrue.
Private owner had passed admission but copied vanilla parent still runs 12h
game-time delay after Heroes. User skipped12h and reports quest came back on
their current fixture: ENTRY LIVE PASS only. Dialogue/completion/reload and
duplicate-scene checks still PENDING; current installed RC2 left untouched.
Future successor may skip repeated wait for proven active1 setup, but none
installed. Rollback FIRST via prealpha/raymond_rc1/deploy_03.ps1
-Action ValidateRollback/Rollback, game closed. File undo NOT save undo.
docs/raymond_rc2.md; prealpha/raymond_rc1/candidate_03 selected;
candidate_01 REJECTED_UNSAFE, candidate_02 historical failed workspace build.

Latest2026-10-26 FAST TRAVEL BLACKOUT LOG REVIEW; NO FIX/INSTALL:
User live report BuranSt->ElCoyote ~13:22-13:25: world+menus black, input/audio
still active. CurrentCR1 all51hashesmatch. Captured37logs/sources under
diagnostics/fast_travel_blackout_20261026_01. SCCsuccess; LC3Ready13:21:53,
source then released/Drop, no latercoverlog; visualteardown NOT logged/proven.
Facts13:23:47/13:24:04 and IFP pause/vehicle logs continue; RED4ext orderlyexit
13:25:05-08. No newcrashreport. IFP0.2.0DLL refused incompatiblepatch, separate
CETlogic logs; notdemonstratedcause. WindowsSystem13:15-30 NoMatchingEventsFound.
CauseUNCONFIRMED; stuckfade/loading/UI candidate, renderingfault notexcluded.
Needreadonlyfasttravelloadingcompletion/UI-fade/popup/playerstate at reproduction.
No assistant game launch, installed/save/fact edits or rollback; do NOT claim
CR1causal or fix by blindfade/factclear. docs/fast_travel_blackout_20261026.md.

Latest2026-10-26 CR1 CONSOLIDATION REPAIR INSTALLED; LIVE PENDING:
User requested implement fixes and excluded identifying11 missing markers.
Three independent agents reviewed donors, semantic checks and Raymond safety.
CR1 candidate_01 explicitly restores ALL30 conflicting corrective donors from
verified preconsolidation backups; do NOT reuse historical overwrite-order build.
Restores Yoko/Viktor choices, Wilson gun dispatch+lease acknowledgement, Fred
boxing+FS1, Bullets rearm, Dennis issued guard, shared phone cleanup49root+6inline,
S25 Delamain receipt/S22 exclusion and native admission guards. Other reviewed
conflicts H10/mirror, PA6 Rogue lipsync index and U10 retaliation gates restored.
S30 trio/48scene lipmap/SR1 visual and MQ058/runtime guards retained. Same51paths;
ONLY combined archive replaced;1172members=30repaired+1142byteunchanged,50other
files unchanged. No new overlay/resourcepaths. All1172readback/67otherarchives
zero collisions; independent2057assertions/30groupsPASS plus S30negativecontrol;
full64sourceSCC with publicCodewarePASS. deploy_02.ps1 38fixtureactions incl6
interruptions/partialstage recovery PASS; deploy_01 failed nullargument fixture
only, NEVER realinstalled. Actual Validate/Install/Verify/ValidateRollbackPASS.
All51installedhashes match;498unaffectedfiles incl295saves/names unchanged.
ArchiveSHA BDDAE9BB742041B74B10B2C2F814C286BD4C740452E517835952968B1B59BC31.
Manifest02SHA B93D40F32706B8106570FB27B0139B44C554558473D80771C98FA22F508CFD73.
Full51ZIP prealpha/consolidation_repair_cr1/candidate_01/dist/
Post-Tower-Continuation-and-Free-Roam-CR1-unreleased.zip SHA
E50D2A253107953C3FBB5426D01D4563CE1B9983C3786CF5EFBB00CAFBA9A75E.
Previousfull51 in candidate_01/archived_previous; actual backup/receipt in
recovery/consolidation_repair_cr1_01. RollbackCR1 FIRST beforeS30 using
prealpha/consolidation_repair_cr1/deploy_02.ps1 -Action ValidateRollback/Rollback,
game closed. Fileundo NOT saveundo. No assistant launch/fact/save/framework edit
or Gitpush/release. Gameplay/rewards/reload and serialized-owner migration pending.
Raymond partialowner NOT patched: q307_main_game_killed has2writers/different
retirement targets, no capture acknowledgement that original MQ040 owner stopped.
No forcedfacts/Pepe release/secondowner/customCodeware. MQ018/MQ028 unconfirmed.
docs/consolidation_repair_cr1.md; candidate_01/assessment_01.json SHA
0587BFB8578A54D7B4DA6BDA719C3EF7264107824D5A05F4D31B9FFFA822B631.
Use successors.

Latest2026-10-26 ALL81 SIDEJOB ENTRY/PHONE AUDIT; NO INSTALL:
User explicitly approved multi-agent audit and clarified ALL restored sidejobs.
Final cohorts A27+B29+C22+S30three=81 unique roots; full78 prior entry census,
61 original entry owners freshly decoded. Current51 package hashes and all1172
installed archive payloads match S30 candidate_02; zero collisions67other mods.
CRITICAL source discovery: consolidation build_archive_02 iterates ascending
archive inventory and overwrites repeated depots;37 overwrite events affect30
distinct paths, ALL30 current choose last/older donor rather than first repair.
Fresh donor/current decode proves known repairs lost. Earlier claim of preserved
internal winners/equivalence WITHDRAWN; hash/readback/compile pass alone missed it.
Lost Yoko779 component choices, Viktor351/840 debt options, Wilson gun-order
dispatch and quest-release acknowledgement, Fred fresh-boxing native scene
selector, Bullets1021 rearm, Dennis1003 issued acknowledgement, S25 Delamain
65020 receipt; common cleanup72->23 root nodes loses49 +6inline courier nodes,
17character contacts+NCPD cleanup branches. Scoped phone listeners still exist;
ordinary call completion/saved global native cleanup separate and liveunknown.
13older resources reintroduce Failed alternatives plus missing native sibling/
root rechecks, BUT runtime HS1/current-root/sibling guards survive: NO blanket
failed replay/duplicate reward/corruption claim. SR1 S29 seven-message correction,
runtime Delamain adoption and MQ058 End Quest receipt still present.
Raymond captured handoff gap now pinned from existing CETlog2473-2494/2513-2526:
rootInactive+mq040_active1, S29baselineFresh true/currentMatch false, Pepe owner0.
Old native owner liveness unknown; do NOT clearfacts or issue secondowner.
MQ018/KillingInTheName and MQ028/EveryBreath source-only partial-state candidates;
GunMusic/BurningDesire/AdayInLife activefacts accepted by their bounded adapters.
19->8 map report remains11 unidentified marker difference, not11 proved failures.
Existing latest fallback original78:49Inactive22Succeeded6Failed1Active; not
current-live/save-ancestry assertion; HS1 still excludes3S30 IDs. All499 protected
files incl295savefiles unchanged; no game launch, install, fact/save edit,
compile, rollback, push or release. Final diagnostics/sidejob_entry_phone_audit_
20261026_01/assessment_01.json +coverage_81_01.json/csv; use phone_entry matrix27_02,
messages assessment02, entry_state cohort22_phone_entry02/coverage78_02.
docs/sidejob_entry_phone_audit_20261026.md. Future repair must reconcile ALL30
donors explicitly in SAME51-path consolidated successor; no overlay/fact reset.
Current S30 rollback chain remains unchanged. Other housing/mirror/Rogue/
retaliation donor deltas recorded, NOT full gameplay-audited by this sidejob pass.
Supplement: retained Heroes S27 package route is R6.2-excluded/HS1-absent,
normal new admission blocked; prior Issued owners preserved. Dedicated runtime
table scan finds no other extra selected-sidejob adapter; S21 wider list is
diagnostic. scope_reconciliation_02.json records this without whitelist changes.

Latest2026-10-26 S30 THREE SIDE JOBS INSTALLED; LIVE PENDING:
User authorized whitelist promotion and restoration of Love Rollercoaster
`mq006_rollercoaster`, Shape of a Pony `mws_se5_07`, and Career Opportunities
`mws_wat_08_trauma_drama`; River's Motorbreath `mq057_motorbreath` explicitly
held/excluded. R6.2 broad selector now 80 gigs+81 side/minor jobs=161 entry
implementations; prior HS1 snapshot still has original158 IDs, so S30 uses
two settled current journal/fact/vehicle samples for its three new IDs and
does not claim generic active-progress resume. Corrected S30 candidate_02
successor has SAME51 install paths; actual install replaced ONLY combined
archive, its XL, and existing PTFR_SideJobsS29.reds. Older candidate_01
workspace-only missed Pony's `#johnny` camp workspot and had an unnecessary
shared-instance split; DO NOT use it. Candidate_02 copies 4quest phases,
5scenes,7Johnny workspots with private paths; all16 serialized/readback exact,
4native phase graphs exact after reversing private refs, scene cast/dialogue
retained, Johnny workspot effect hubs muted/initial equip cleared, no scoped
Johnny standalone VFX/equip events. Existing JV1 actor mesh hide retained;
live rendering not yet proved. English lipmap44->48 using4 native donors;
Career scene had no native map. Archive1153->1172 winning members, 1152
old members unchanged, one lipmap replaced,19 new resource paths; zero
collision in67other installed archives. Full64-source SCC with public Codeware
PASS. Static asset592/entry111checks,17 installer fixture actions PASS.
Actual Validate/Install/Verify/ValidateRollback and full51 installed file
hashes PASS. 295 current savefiles/names byte-unchanged; no assistant game
launch/fact/save writes or new GitHub Release. Recovery backup
`recovery/sidejobs_s30_02`, rollback FIRST when game closed via
`prealpha/sidejobs_s30/deploy_02.ps1 -Action ValidateRollback/Rollback`;
file rollback NOT saved-game undo. Full local unreleased ZIP
`prealpha/sidejobs_s30/candidate_02/dist/Post-Tower-Continuation-and-Free-Roam-S30-unreleased.zip`
SHA42AF01F1CD3B4D0E6F11990EDBF22B1A138335311D8C48EB3DD8E5744BD20F07;
NO GitHub push/release this turn. Gameplay marker, actor visibility, original
rewards and save/reload LIVE PENDING. docs/sidejobs_s30_20261026.md.

Latest2026-10-26 USER LIVE PASS ON PUBLIC CODEWARE:
User reports all previous fixes they tested worked and combined PTFR runs with
untouched public Codeware1.21.1. This is direct user-reported live acceptance of
their current fixture, not an exhaustive route-by-route/fresh-transition/save-
upgrade proof; no individual quest list or new log supplied. Do NOT require
custom Codeware for PTFR. All9 official Codeware files were byte-verified at
installation; isolated64-source SCC with stock script PASS. Existing local
rollback preserved. No assistant game/save/fact writes or new GitHub Release.
CHANGELOG/README/core-updates/consolidation docs updated; push source/docs only.

Latest2026-10-25 PUBLIC CODEWARE 1.21.1 INSTALLED; USER LIVE TEST PENDING:
Official ZIP `diagnostics/core_updates_20261025_01/downloads/Codeware-1.21.1.zip`
SHA7CEA413C39BBA6DEA15DE558E95BB0E04F63AF3D3CB35C6D854ED65382FD41A7.
All9 Codeware package files compared; prior local install differed ONLY at
`red4ext/plugins/Codeware/Scripts/Codeware.Global.reds` (two-line PR65 return).
Isolated combined64-source SCC with exact unmodified public Global.reds PASS;
PTFR has no Reflection.Call usage. Game closed; replaced ONLY Global.reds, old
SHA9736FEBC... backed up in `recovery/public_codeware_v1_21_1_01`; public
SHA83CEBFDA... installed. Validate/Install/Verify/ValidateRollback PASS; all9
installed Codeware files now match official ZIP. No PTFR/archive/framework-other/
save/fact/cache edit or assistant game launch. Public-package cold load and
restored-quest test USER PENDING. Rollback FIRST via
`prealpha/full_consolidation_v1/deploy_public_codeware_01.py Rollback`, game
closed; file undo NOT save undo. Source/audit/proof under
`prealpha/full_consolidation_v1` and
`diagnostics/public_codeware_install_20261025_01` (ignored local evidence).

Latest2026-10-25 OFFICIAL NAME AND REPOSITORY RENAME:
User confirmed official public name Post Tower Continuation and Free Roam and
renamed GitHub repository to Andrew-Heng-Yong/CP77-Post-Tower-Continuation-and-Free-Roam.
Reader-facing documentation and distribution filename use the official name.
Legacy PTFR/TowerContinued/TowerContinuation code, resource, save and published
asset identifiers remain unchanged for compatibility. Renamed distribution ZIP
`prealpha/full_consolidation_v1/candidate_01/dist/
Post-Tower-Continuation-and-Free-Roam-v1.zip` has same 51 entries and SHA
2A148EDF7D99AF9ECCE433959BD23F012E80BAAA764D2F5578C848C8B1AED86D.
Naming update does not edit installed game files, saves, facts or frameworks.
Consolidated build remains locally installed; gameplay acceptance pending.

Latest2026-10-25 FULL ALPHA+FIXES CONSOLIDATION INSTALLED; LIVE PENDING:
USER requests minimum production-install file count incl alpha; prior green flag
to install production persists. Current full PTFR stack127 files consolidated to
51: 25archives->1,23ArchiveXL->1,76REDS->46,2CET+1TweakXL retained.
46REDS is tested safe minimum:45named modules+one global group; one-file-all
fails REDscript parser at second module. One ZIP `prealpha/full_consolidation_v1/
candidate_01/dist/Post-Tower-Continuation-and-Free-Roam-v1.zip` SHA
2A148EDF7D99AF9ECCE433959BD23F012E80BAAA764D2F5578C848C8B1AED86D.
Includes all117 last-alpha manifest files plus10 later installed, incl SR1; no
development CET helpers or generated runtime data. Combined archive1153 winning
resources byte-exact,37internal override winners preserved, zero external mod
archive collisions. XL742 phases+13 streaming+en-us lipmap preserved. Full SCC
inclEquipmentEX PASS; compiled E4D48E6C629379A8ADB8DA471FE08457FABBF1E70B1A12CD1FEF8FB3D9A4FFF9;
decompiled normalized661977-line multiset matches prior compiled build. ZIP
51paths readback PASS. Installer `prealpha/full_consolidation_v1/deploy_02.ps1`
25fixture actions incl five interruption rollback points PASS; deploy_01 historical
rollback edge case fixed in successor02, never run on real game. Actual Validate
READY/Install/Verify/ValidateRollback PASS. 124retired paths absent,51new hashes
match;289savefiles unchanged. Old127 archived `recovery/full_consolidation_v1_01/old`.
Rollback FIRST `deploy_02.ps1 -Action ValidateRollback/Rollback`; file undo
NOT save undo. No game launch/runtime fact/save edit/public publication; gameplay
startup, Tower handoff, reload, sidejob/gig behavior LIVE PENDING. No claim of
production gameplay acceptance yet. Source/proofs in `prealpha/full_consolidation_v1/
candidate_01`; doc `docs/full_consolidation_v1.md`. Future fixes update combined
file and archive the replaced version in workspace, not add install overlays.

Latest2026-10-26 SR1 THREE-FILE PRODUCTION-LAYOUT LOCAL INSTALL VERIFIED:
USER authorized install after requesting fewer files and versioned old-file
archival. Consolidated candidate `prealpha/sidejob_repair_sr1/production_01`
REPLACES existing S29 archive, archive.xl, REDS only; ZERO added game files.
Original S29 archive194members ->199: 185 byte-exact unchanged, nine repaired
replacements, five new resources (cross-owner Yoko/Bullets/S25 plus KOLD private
workspot and English lipmap). Existing XL quest list verbatim + lipmap stanza.
Old three files archived workspace `production_01/archived_previous` and verified
rollback backup `recovery/sidejob_repair_sr1_production_01`. No zzzz SR1 overlays
in game folder. Production ZIP contains ONLY 3 replacement paths, SHA
E79E4E04FAE4ED01E98BEF4669FFBC69F509E0FEB1C333745C1DA4077C8765BF;
it is existing-install update, NOT standalone/full-mod/public release.
199-member pack/readback PASS, XL append-only PASS, prior94-source SCC PASS,
17 production fixture install/verify/rollback/interruption actions PASS.
Actual Validate READY; Install SR1_PRODUCTION_INSTALLED_LIVE_PENDING; Verify
VERIFIED; ValidateRollback ROLLBACK_READY. Manifest SHA
3E168655E2DFC9C58AB347F088F34AE9698A91C7B99DCE4F7F235C4979233043.
Installed hashes archiveC6E962CC336C2BA9AD93A1CC0C73B2894483657BC2C6B430CCCB1A711D2CCE41,
XL5926BE9AA5E5F78230507FA5483554899595B77A812CD1A4CE3ADF74B75903AB,
REDSD1CDF5F27B1C2625581A6CE9A58D90965BFEF94D2E1105651B7400EA364565CB.
No launch/save/fact/publicrelease writes; gameplay still live pending.
Rollback FIRST for SR1: `prealpha/sidejob_repair_sr1/deploy_production_01.ps1`
actions ValidateRollback/Rollback. Fileundo NOT savedgameundo. Historical
candidate_02 overlays workspace-only. Broader installed alpha still71 PTFR
archive/XL/scripts; alpha release manifest117 files. Full-mod consolidation
SEPARATE; do not claim SR1 ZIP standalone. docs/sidejob_repair_sr1_production.md.

Latest2026-10-26 SR1 SIDEJOB REPAIR STAGED; NOT INSTALLED:
USER asked implement fixes based on side-job audits; prior do-not-install instruction
retained. Selected `prealpha/sidejob_repair_sr1/candidate_02/package` has 5 files:
core six-resource archive, seven-resource visual archive `Visual2`, 44-scene
English lipmap archive+XL, and replacement S29 REDscript. Core repairs Yoko
This Corrosion choices, Bullets Zane rearm, MQ058 End Quest receipt, Delamain
predecessor-message guard and duplicate phone-owner protection/adoption.
Visual fixes Sweet Dreams' two elevator smoking calls using scene-local muted
workspot at same marker; same scoped policy for Don't Lose Your Mind, Killing
in the Name, Freedom, KOLD MIRAGE; KOLD exact native workspot private copy
changes only eventFilter Default->Mute. Sinnerman orphaned ember event removed.
Six core graph comparisons, full94-source SCC inclEquipmentEX PASS compiled
C9DBE0E6458A31F1B8F9CE4A568D201CE98C6C070F9F92AD6D91ABC941852744.
Visual serialized-baseline preservation and 44 lipmap donor/config checks PASS;
all 3 archives packed/read back; 17 fixture deployment/rollback actions PASS;
real installer read-only Validate READY. Manifest SHA
84E82D3E15E1917369E49CB85B45849204E809C8B6C80A10A54AA690F394C529;
assessment SHA 976CE9AE54490BBD3C977373953CDC40CDC3DBD09210FB52178A5B7C212F8229.
No game/save/fact/framework/public-release writes or launch. `Visual.archive`
earlier staged candidate excluded; use `Visual2.archive`. Historical failed
workspace candidates retained; selected manifest names only. Installer
`prealpha/sidejob_repair_sr1/deploy_01.ps1` defaults Validate; do not invoke
Install without renewed user instruction. Live all gameplay pending. Direct
original-scene Johnny cigarette equip in Shot by Both Sides/Beat on the Brat:
Glen, Johnny VFX policy risks, Nix/Viktor phone, Cassius tattoo, 4 gig phone
omissions, non-English lipmaps unresolved. `docs/sidejob_repair_sr1.md`.

Latest2026-10-25 SECOND VANILLA SIDEJOB AUDIT; NO INSTALL:
USER requested continue sidejobs ONLY, every missing detail, parallel agents.
Three cohorts audited all78selected jobs (27/29/22) with per-job entry/owner,
dialogue, phone, items/objectives/rewards, world/VFX, cleanup, follow-up and
save/resume evidence or explicit unknown. Combined matrix
diagnostics/restored_audit_20261025_04/combined_78_01.{json,csv};
docs/sidejob_vanilla_audit_20261025_r2.md. TWO new source findings:
CA1 Bullets/Zane P2: copied vanilla default owner omits25/26 shop rearm loop;
encounter cleanup restores default_on but copied owner terminated, private
ZaneDriver gated by QuestOwns lease held through8h SMS/reply chain. Shop/menu
downtime source-inferred, LIVEUNTESTED. Exact cohort_a/bullets_service_01.json.
MQ058 Where Eagles Dare LOW: wrapper64000 listens Out1 but native child only
returns End Quest; PTFRFinished receipt writer65007 cannot get declared output.
Native done/journal/cleanup run before return, no selected downstream consumer;
not claimed reward block. Exact cohort_c/mq058_receipt_01.json.
Existing SweetDreams cigarette/smoke, ThisCorrosion Yoko, Delamain SJ1/SJ2,
Sinnerman dangling prop, English lipmaps, Cassius and Johnny VFX risks remain.
Bullets johnny_spawn_fast normal route and HappyTogether teleportVFX source
risk, not observed visible defect. SQ024 presumed missing vehicle-hacking helper
CLOSED: native inline20nodes/28edges; KOLDMIRAGE dedicated Nix scene intact;
Fred/Viktor/Brendan/BurningDesire/MachineGun/Prophet candidates closed by
guards/callers. Seven of eight extra Johnny world anchors resolved; no exact
named cigarette action in seven, one finale sector decoder unknown; shared
transition selection unknown. Snapshotfixture post_ending_fallback, NOTactive
save;49Inactive/22Succeeded/6Failed/1ActiveSweetDreams selected roots.
561protected game/save files rehashed unchanged; no game launch, install,
fact/save/framework/publicrelease edits. Gameplay/reload rewards/UI still
LIVEPENDING. Root assessment diagnostics/restored_audit_20261025_04/
assessment_01.json SHA437FC9B37C2A32D7A24CC8C5C865EF74B2C9473A038733A7C58EEAF05024520C.
Inputs/proofs pinned; use successors.

Latest2026-10-25 SIDEJOB VANILLA AUDIT / SWEET DREAMS CIGARETTE; NO INSTALL:
USER says keep auditing against vanilla; reports visible Johnny cigarette in
SweetDreams elevator. Parallel review authorized from continuing audit. Source
chain confirmed: mq036_scavengers elevator_in1048->149->158 uses world anchor
#mq036_ws_johnny_exit, not scene workspotInstanceId. Current world resolves to
native johnny__stand_ground_cigarette__idle__01, Default filter; exactclip
johnny__stand__lh_cigarette__aggressive__01 equips crowd_cigarette_i_stick left
hand +smoke/ember. Existing private copy is Mute but world route bypasses it.
JV1 hides actor visuals only, retains voice/timing; independent items uncovered.
Six selected world calls/fivejobs: SweetDreams158+1073, KOLDMIRAGE318,
KillingInTheName292, DontLoseYourMind298, Freedom178. Different workspots can
share sameclip. Only SweetDreams USER-observed; others source gaps, no agentplay.
Additional3normal native equip calls/twojobs: ShotByBothSides apartment330
(keycard; nativeunequip1423), bunker4733(conditionalbothdead); BeatBratGlen602
(firstcomment). Glen itemhash101279751730=Items.cigarette_i_stick; other2
127721248826=crowd_cigarette_i_stick. Total9calls/7jobs NOT9livebugs/orphans.
Freedom429 Johnny_corpses alias retains johnny_appear_glitch; exactnamefilter
misses Silverhandaliases. Actualeffectvisibleuntested. HappyTogether4teleport/
Bullets1spawnFX furthercandidates; notcountedconfirmedvisiblebugs.
NEW SJ3 HIGH ThisCorrosion/Yoko integration missing: q305root/4 sets talkready17,
objective31; trigger45 then component_ready wait8. PrivateYoko779 choices4-7
impossible+disconnected, regularentry4 cannotreach writer620. AlternateStart1
1324 can, but no restoredcaller; no YokoQuestOwns writer/S29handoff. Two agents
independentlyconfirm; liveuntested. Need scopedquestconversation, not forcedfacts.
Compared89privatephases/6711commonnodes,89rootcontexts; approvedchangesonly.
62scenevariants/61currentdonors:2506retaineddialogueevents+allstores exact;
266changedanimationmutes allJohnny.134private scenes/236props/16669events;
selectedscope152scenes=49private+103native,20nativeJohnny scenes freshlyread.
18/22worldanchors resolved,13workspots/51anims;47959sectors screened.92modheaders
zerooverridefor103native-scenes+10worldsectors.2selectedDelamainanchors decode
unknown;4fortunetellerclips unresolved; nativeworld/transition candidates remain.
Older derivedSweetDreams apostrophe artifact NOTinstalledtextbug. Use freshUTF8.
Final root cross_verify_visuals_02, sidejobs/yoko_corrosion_02, dialogue/checks_02.
No implementation/compile/install/launch/fact/save changes.561protected incl289
saves unchanged, no save additions/removals. Priorphone/lipmap/Delamain/SQ023/
Cassius issues remainopen. Evidence diagnostics/restored_audit_20261025_03:
assessment_01.json SHA985C278AACC7385C3E740B5D632D0B4BB30FE351A134B1783C7E5321D5C4FF50;
manifest2999B68A78A3E75ABF21C77DDD5DF6ECD0C6074109BEF2C9188D3087B885D3CD.
301evidencefiles pinned;use successors. visual_routes_01.csv/json checklist.
docs/sidejob_vanilla_audit_20261025.md. All unobserved rendering/rewards/reload
remain livepending. No recovery/install chain changes; audit-onlyhold retained.

Latest2026-10-25 PARALLEL RESTORED SIDEJOB/GIG AUDIT; NO INSTALL:
USER explicitly authorizes multi-agent audit. Three reviews plus independent
main cross-check complete. Three NEW source issues; no live symptom claims:
SJ1 HIGH: S29 Don't Lose Your Mind requires seven legitimate Epistrophy phone
history entries Inactive while requiring predecessor Succeeded; native gates
65003/65004 and runtime Paths12 agree. Retained S22/S25 branches activate these
messages. Conditional on history, NOT every completed Epistrophy save blocked.
SJ2 MEDIUM: S25 persistent Delamain controller94 is sibling of content100;
finish does not cut94 or WRITE shared SupportIssued receipt. S22 excludes S25;
S29 may start another controller if sequel/idle gates pass. SJ1 can mask this.
No observed duplicate call, reward or corruption. Repair both together later.
SQ023 MEDIUM: restaurant section635 ember event2514459860119400448 still targets
performer12802=prop50 (removed Johnny cigarette); installed props0-47. Reachable
conservatively via cigarette_in. Engine effect unknown; NO crash claim.
Actual owner coverage80gigs (72U9/8U10),78sidejobs via94routes. Corrects prior
BigInJapan/Prophet/Sinnerman owner misattribution. Remove none/0/empty external
resource sentinels BEFORE pruning inline fallback:14 false prunes corrected,
199 real external fallbacks pruned. Prior aggregate reachability not re-certified.
17currentnative parents/219embedded resources/115selected bindings accounted;
no graph drift. Roads07/TreatingSymptoms12 follow-up producers and gates retained.
134scenes/41818binding+1729animation-ref checks;46S29scenes/4954quest payloads/
331player-camera events preserve semantics. 206stale auxiliary metadata refs
are candidates, NOT206gameplay bugs. 8371runtime path/class pairs/232tables valid;
four reachable stored path candidates inherited from current native nodes.
Known4gigphone contacts/44Englishlipmaps/Nix-Vik conditional returns/Cassius
purchase issue remain open; JD1 live checks pending. No fixes/compile/install/
game launch/facts/save edits.561protected incl289saves unchanged. Static audit
does NOT prove all actors, rewards, active-save resumption, reloads or gameplay.
Final diagnostics/restored_audit_20261025_02/assessment_01.json SHA
2FBDE625E031A7C4847776F9414327880466F374B75280C92387B3D82B66A527;
manifest B55993654BDD7E2EA1C9D1E4A08EB586DD352D11EDC2BF987D042C863DF2C92E.
coverage_158_01.csv/json replace prior owner mappings. Main cross_verify_03,
journal_review_02/journal_native_review_02, complete_02 final; earlier verifier
and report-link attempts workspace-only. Evidence pinned; use successors.
docs/restored_audit_20261025_parallel.md. No recovery/install chain changes.

Latest2026-10-25 SECOND RESTORED QUEST AUDIT; NO INSTALL:
USER requests all restored sidejobs/quests audit. All158 selected entries
(80gigs/78sidejobs) have installed static journal bindings; NOT gameplay proof.
92modarchives inventoried;1044winning PTFRquest/scene resources plus1709native
traced=2753resources/204114nodes,176425conservative reached,742injectedowners
including services/activities. Additional EP1cleanup read confirms inline paths.
51phone requestfacts audited;6lack restored listeners. NEW source omissions:
NastyHangover KarlGinsky audio; DesperateMeasures PedroAimar audio;
SpyintheJungle MarkBana audio+Janet holo. Controllers AND cleanup absent.
Original baseinit Karl140/Pedro141; cleanup497/496. EP1init Janet20/Mark21;
cleanup inline79/81 guarded80/82. No claimed live reproduction or universalblock.
Nix/Viktor phone-return branches also lack support; normalinperson separate,
actual entry context/quest-blocking impact UNPROVEN. Original init130/96,
cleanup494/354. Meredith retained farewell is not oldholocall branch;
Daniels inlinecleanup present. Avoid false positives from filenames alone.
134winning scenehashes unchanged; prior44Englishlipmap omissions remainopen.
LegacyS1seat badindices dormantoptin; doNOTarm. JD1 installed LIVEPENDING.
Seven unmatched ports +absentSQ024vehiclehacking backgroundphase inherited
native candidates, NOT confirmed PTFRregressions. Seven courier subdependencies
indexedpresent but not recursively reviewed; activity outside158selectedscope.
Static traversal overapproximates conditions/timers/outputs; arbitraryactive
resume,excludedancestorcoverage,worldinteractions,rewards/escrow/reload LIVE
PENDING. No general allquestswork claim.561inputs incl289saves unchanged.
No game launch/gamewrites/save/fact/framework/publicrelease/installchanges.
Evidence diagnostics/restored_audit_20261025_01/assessment_01.json SHA
7FAEB79A858C531777EA3CA45AC06D9DDA78179AA84492712282C87207962013.
Final final_review_01 +reach05/model05 (fallbackpruning applied in finalreview),
coverage158CSV/JSON, phoneaudit01, EP1cleanup_proof02. Inputs/proofsPINNED;
use successors. native04 partialfailedworkspaceextract; native05+ successors
used. No failed output installed. docs/restored_audit_20261025.md.
Next authorized scope was AUDITONLY; earlier lipmap installhold remains.
Future repair original scoped phoneboot+cleanup, preserve queued requests and
existing owners; never restart global initializer or force quest facts.

Latest2026-10-25 JD1 JUDY DOOR / DENNIS PHONE INSTALLED; LIVE PENDING:
USER reports upstairsJudydoorunlocked; Dennisnoincomingcall,proceededbytalking.
Explicitapproval installtwofixes. HousinghadnostrictJudyprivateentrancelock.
JD1 exactupstairsdooronly; outsideclose/lock, ownlockreleaseforinsideegress;
nativeinterioranchor+pathboundtocurrentworld; unknowndefer,thresholdmargin.
Visualopen suppression synchronizesPSfirsttoavoidrecursiveUpdateDeviceState.
MQ038 originalcallsretainedbutDenniscontroller/cleanupmissing. Log19:49:20
start_activate1withoutstart. Newonce-onlynative106handler; freshMQ038wait1003
requiresreceipt. ExistingPTFR-ownedunfinishedresume permitsqueuedrequest,
noquestrestart/factclear. NativeMQ038holdsmanualinterruptuntilcall_out: existing
listenerbootstrapmustnotwaitonthatflag; setup/resetguardsretained. Original
cleanup439/303 appendedbehindownreceipt; old69nodepayloads unchanged.
Fourfiles: HousingPurchaseoneTickline replacement; addJudyDoorJD1+archive+XL.
Threearchiveresources:1newphoneboot,2PTFRoverrides; noofficialoverrides.
Full94sourceSCCinclEquipmentEXPASS; 27803offlinechecks+14installeractionsPASS.
Install/Verify/ValidateRollbackPASS;721protectedincl289savesunchanged.
Noassistantlaunch/manualfacts/framework/lipsync/publicreleasewrites.
Finalnative_02/tests_02,compile_04; sources/proofsPINNED,usesuccessors.
ManifestB9B0A332D3177FD80E40AF684AE369F43412CD24AF4330302AFD62B5D286D3C6.
Assessmentprealpha/judy_dennis_jd1/candidate_01/assessment_01.json SHA
AB09FE7D7E06CFD5FE7A7FB649BF84AA72D1DF66673FAE749425504C69233B22.
RollbackJD1FIRSTbeforeS29/S23/H5:prealpha/judy_dennis_jd1/deploy_01.ps1
-ActionValidateRollback/Rollback;recovery/judy_dennis_jd1_01.
FileundoNOTsaveundo; retainpreJD1saveforremovingnewphoneowner.
NEXTcoldloadprivateJudylock/insideexit/reload; Dennisnextnativecall/end/interrupt,
earlierfixtureforalready-passedcalls. AllLIVEPENDING. docs/judy_dennis_jd1.md.
USER nowrequests anotherbroadmissingdependency auditofrestoredsidejobs/quests.

Latest2026-10-25 ENGLISH LIPSYNC AUDIT; USER SAYS DO NOT INSTALL YET:
Stefan Englishvoice/body work, mouthstatic. CurrentEnglish lipmap registers
originalscene17020050437040647170, NOT private17166679345968396119; Stefan
voiceTag1624173162010259716 andall29usedlineclips present. NoJohnny adaptation
onStefanscene. Confirmedregistrationomission; gameplayrepairNOTtested.
Userbroadensaudit+NOINSTALL. 134winning/136entries/24PTFRarchives inspected,
91modarchivesresourceindex; nocustomlipmapconfigs. 44scenes/122actorbindings
missingnativeEnglishregistration:30S29+10main+2S25+1RoguePA6+1U10. Bindings
NOTuniqueNPCs; retainedbranchreachabilityunproven. Johnnyvoicealiasesexcluded.
114facialassets/1377event-referencedlines/rigsallpresent; zeroadditionalinvalid
actorrefs/animationindices/missingdirectanimationresources/unresolvedlineIDs.
245additionalRID/dynamicindicesPASS. SevenunusedNix/Mateoscreenplayclipsnotbugs.
Nativeandroid/Delamainbackoffice/podsoldiercaseslackNPCmapinoriginaltoo,excluded.
SeparateknownlegacyStreetkidS1seatIDs0,1,3 stillbad; gateEnabled1, superseded
opt-in, currentruntimeflagunknown; doNOTarm. Noinstalledchanges/game/save/facts.
91PTFRarchive/configfileshashunchanged. Preliminaryone-sceneSL1 workspaceONLY
prealpha/stefan_lipsync_sl1/candidate_01; packednotinstalled, nofull/liveclaim.
Preferconsolidatedfuturemappingrepair; USERhasNOTauthorizedinstallationyet.
Evidence diagnostics/stefan_lipsync_20261025_01/assessment_01.json SHA
D964375963C7012B6A0E9A7AFFE53D8EED5998044152D3CF5B6F24BA56FE4830;
finalinstalled_audit_01/analysis_02+clip_audit_01/line_checks_02. Full44CSV;
docs/lipsync_audit_20261025.md. FinalsPINNED,usesuccessors. Englishonlychecked;
initialanalysis01Johnnyaliases/unusedlinesovercount correctedin02.

Latest2026-10-25 ORIGINAL UV/VTK RESTORED; NEW-STACK VISUAL TEST PENDING:
USER restoreuv/vkt. Verified/reversedcosmetic03->02->01 usingoriginalinstallers.
UVmapping now34C90A065970E9D23A58E1E6222E7C97D7E7ED47973735226A2FB6B12719FCBC;
VTKhead nowA910A12A16EE8D2DE0E0FA82756C08495CD1514B3715168BF898F6CABB8EF138.
All11installedfiles match originalZIPs:UV4.1,VTKBody3.4,Head3.1,ExtraTextures1.0.
Restoresfemalehead/bodyUVmappingand3VTKheadgeometryresources;otherassetsunchanged.
Validate/3ValidateRollback+Rollback/Verify/ValidateUndoPASS;770protectedincl289
savefiles unchanged. CapturedCURRENTclosed-gamebaseline afterusercache/save
changes; earlierinstallcachebaselinewasstale. Newframeworks+EquipmentEX1.2.10+
PTFRpreserved. Noassistantlaunch/save/facts/frameworkchanges. Previousvisualpass
wasWORKAROUNDS;originalUV/VTKwithnewofficialstack LIVEPENDING. Inputs/proofs pinned.
Manifest1DDBB21CA6A56312ED8815E7486B42F4291EC736DEE1493488C7B8347D69DA05.
Evidence diagnostics/uv_vtk_restore_20261025_01/assessment_01.json;
docs/uv_vtk_restore_20261025.md. ToREINSTATEworkarounds useNEW restore_01.ps1
-ActionValidateUndo thenUndo;backup recovery/uv_vtk_restore_20261025_01.
Old03/02/01receiptsnowROLLED_BACK. FileundoNOTsaveundo. USERalsorequestsupdate
check:publicUVlisting4.1;liveUV/VTKpagesadult-content-gated;USERreportsnoupdate
needed. OriginalUV/VTK restoration reverified;770protected unchanged, no rewrite.
No newer cosmetic download/install in restoration. NEXTcoldloadappearance.

Latest2026-10-25 EQUIPMENTEX1.2.10 INSTALLED; LIVE PENDING:
USER downloaded NexusZIP and requestsinstall, superseding self-install plan.
Source Equipment-EX6945 1.2.10 ZIP SHA
BD3628AF0851AF4CC5083E40F890E9E7423305CB7E3017F48F9E06A8BC6B6E17.
3replacements:EquipmentEx.reds,EquipmentEx.Global.reds,redsUserHints TOML.
Archive/XL/license byteidentical retained. NewrequirementsCW1.21.1/AXL1.28/
TXL1.12 match justinstalledframeworks. Full93sourceSCCinclEquipmentEX PASS,
compiledD0C7F643A7601B96F71D3B02C069E57F2F3258E7E66A07F88817FA0B5DA0954B.
ActualcompiledchangesONLYEquipmentEx.Version +3CompatibilityManager minimum
versionconstants;allotherclasses/savedfields unchanged.14installerfixturesPASS;
Validate/Install/Verify/ValidateRollbackPASS;762protectedincl283saves unchanged.
No game launch/saveedit/facts/PTFR/framework/cosmetic changes. EquipmentEX is
OPTIONALforPTFR,installedasuserexistingoutfitmod. candidate01 proofs PINNED.
Manifest1268D6C252702E6FF6AE1C388336DB59AEFE857776B4B10413618DA60A053787.
Evidence diagnostics/equipmentex_20261025_01/assessment_01.json; rollback via
diagnostics/equipmentex_20261025_01/install_01.ps1 -ActionValidateRollback/
Rollback;backup recovery/equipmentex_20261025_01. UndoEquipmentEX BEFORE
downgradingOct25frameworks to avoid minimumversionfailure. FileundoNOTsaveundo.
NEXTcoldstartWardrobe/outfits,thenS29followups. LivebehaviorPENDING.

Latest2026-10-25 FIVE ESSENTIAL FRAMEWORK UPDATES INSTALLED; LIVE PENDING:
USER installthem; EquipmentEX USER handles separately after Chrome access denied.
Official RED4ext1.31.0(+winmm),Codeware1.21.1,ArchiveXL1.28.0,TweakXL1.12.0,
ModSettings0.2.22for2.50 installed. Five official ZIP published SHA256 PASS.
Codeware DLL official; Global.reds retains ONLY earlier PR65 two-line empty
Variant fallback, absent upstream. GlobalSHA9736FEBC39BF88AD920068737BA6BBD0B
C78F39D3E785FB629558E39AAAF990B. AXL official SDK5246e659 preserves slot450/
tag4E0,CMesh220,StatIDTypeint8 and emptyparts guard; no older SDK regression.
CET1.38/redscript0.5.32/DQC3.3.1/EquipmentEX1.2.9 retained; RHT held outside.
Full93sourceSCCinclEquipmentEX PASS;146PTFRclasses unchanged;212classeswith
persistentfields retain schemas;51Codeware class names retained. CompiledSHA
9AE65E63F6E164814BB23605E2426B10C6FF95A89E5B2257F1FC69FB66852CE3.
23replacements+2newAXLfiles;14installerfixtureactions PASS. Validate/Install/
Verify/ValidateRollback PASS;740protectedincl283savefiles unchanged. PTFR S29/
CF1/H6/HS2/H5/FS1,cosmetics/settings/Persistent/caches preserved. No game launch,
saveedit/manualfacts/publicreleasechanges. Initialcandidate01 assertionfailed
workspaceonly;candidate02 finalinputs/proofs PINNED,use successors. Manifest
5650192109AFB6564C785FA6EB64817FDDB97544FED47E39C9665D8C0356C75D.
Evidence diagnostics/core_updates_20261025_01/assessment_01.json;
docs/core_updates_20261025.md. Recovery FIRST for framework stack:
diagnostics/core_updates_20261025_01/install_01.ps1 -Action ValidateRollback/
Rollback;backup recovery/core_updates_20261025_01;THENOct24/SDK230/olderPR63.
FileundoNOTsaveundo. NEXTuser addsEquipmentEX,coldstart/checkModSettings/setup/
outfitdisplay,thenS29followups. New framework live behavior PENDING.

Latest2026-10-25 ESSENTIAL MOD UPDATE CHECK; NO INSTALL:
Live GitHub API/Nexus now show SIX newer releases: RED4ext1.31.0 (24Oct),
Codeware1.21.1 (25Oct21:05Z; 1.21.0 earlier same day), ArchiveXL1.28.0,
TweakXL1.12.0, ModSettings0.2.22, EquipmentEX1.2.10 (Nexus25Oct21:07).
Installed remains RED4ext1.30/CET1.38/redscript0.5.32; CW PR63+65 reports1.20.6,
AXL PR31+SDK229/230+PR32guard reports1.27.5; TXL PR22 reports1.11.5;
ModSettings PR33+34 reports0.2.21; EquipmentEX1.2.9. Hashes match prior receipts.
CET1.38/redscriptstable0.5.32/DQC3.3.1 current. RHT1.3rc3 unchanged/held.
ModSettings0.2.22 requires RED4ext>=1.31,AXL>=1.28,redscript>=0.5.32.
CW1.21.1 fixes mixed streaming-sector versions/scripted ink event propagation;
AXL1.28 fixes potential ent-patching crash. Author release claims, NOT new-stack
PTFR compile/live proof. Latest web caches initially lagged CW/MS; API/tag pages
confirmed hotfixes. Future install must retain local-patch comparison/rollback.
Read-only check; no downloads/install/game/save/fact changes. Evidence
diagnostics/core_updates_20261025_01/upstream_check_01.json and installed_01.json.

Latest2026-10-25 S29 REMAINING18 SIDEJOB ENTRY POINTS INSTALLED; LIVE PENDING:
USER requests remaining18 then tests follow-up quest trees. Added16native job
owners/18journals (3Sinnerman oneowner),7phoneboots,194resources. Coverage80/80
gigs+78/78sidejobs=158/158ENTRYIMPLEMENTATIONS, NOTgameplay/resumeproof. Full
native delays/AND-OR gates/choices/rewards/escrow retained. ScopedVenus excludes
Pickup money/corpse/cat branches; Delamain starts afterEpistrophy with original
sequel; Corrosion breadcrumb excludes equippedCanto reactions. Corpo actual
wst_ep1_02; OneWay parentSTS_EP1_07. Nix/Pepe wait actual service release;
6newphonecontacts+sharedS22Delamain claim, currentS27cleanup extended. Private
Johnny presentation retains actors/IDs/voice, strips own visualevents/props,
mutes ownworkspots and splits sharedbinding; no official-resource overrides.
Fresh-only2observations+native recheck; existingIssuedneverreset. BaselineActive/
Succeeded/Failed denied; unsupportedunfinishedDEFER, no restart. HS1catalogue
140detailed/18rootonly andfingerprint/savedfieldsunchanged; one readonlyFreshS29
method added. 4files:3add(archive/XL/REDS),1replaceSnapshotStateHS1. Combined93
sourceSCCinclEquipmentEX PASS;17664nativechecks/14installeractionsPASS.
13836othercompiledclasses andall13838existingsavedclassschemasunchanged.
Validate/Install/Verify/ValidateRollbackPASS;703protectedincl283savesunchanged.
No assistantlaunch/manualfacts/save/framework/publicreleasewrites. CF1,H6/HS2,
H5,FS1 preserved. Buildnative_04/runtime_06/compile_04 andproofsPINNED;successors.
Earlierfailedworkspacecandidates correctedbeforeinstall. Manifest
973B6786717643457B45206456FB4D84D462159394A7672B7129C6C9932D901A.
Assessmentprealpha/sidejobs_s29/candidate_01/assessment_01.json; docs/sidejobs_s29_playtest.md.
RollbackS29 FIRSTbeforeHS2/HS1/olderphonecleanup:prealpha/sidejobs_s29/deploy_01.ps1
-ActionValidateRollback/Rollback;recovery/sidejobs_s29_01. FileundoNOTsaveundo.
NEXTcoldloadpreS29postTowerfixture; normalprerequisites/calls/delays/followups,
nativechoices/rewards/inventoryescrow, newmanualslot/reload.LIVEPENDING.

Latest2026-10-25 CF1 LOCAL REPRODUCTION LIVE PASS:
USER "fixed". Log16:21:32T1000/16:21:33PainDistributor:CF1nativecleanupguard
executedforboth,CD1exactitem/dataID/hash/seedunchanged,qty1->1,parts2->2with
identicalpartIDs/seeds/slots,equippedslotempty,bothresult1. Ready16:22:07,
elapsedSim42.312500;nonewCD1FAIL/result-1inthisattempt. Confirmslocalfixof
reproducedstopandpreservationforbothrecords, includingnativeeffectorroute.
InstalledCF1hashmatchespinnedsource. Runtimecompile16:14:25PASS. Evidencecopied/
hashverifieddiagnostics/alpha_cyberware_20261025_01/local_pass_01/assessment_01.json
SHAD702E467DE4387C3ACB3DB26906D84314E3B29641DE17217720E41E2CA72D141.
DoNOTrepeatbasicendingrepro. Remote tester/manualsave-reload/exhaustiveeffect
cleanupNOTverifiedbythisrun. No newinstall/runtime/save/fact/publicreleasewrite.
ExistingCF1/CD1sources/proofs/rollbackchainretained; docs/cyberware_cf1.md.

Latest2026-10-25 CF1 CYBERWARE PRESERVATION FIX INSTALLED; LIVE PENDING:
USER reproducedbeforethugq307 withbothSkeletonIDsverifiedequipped. CD1at16:04:56
T1000exactinstanceqty1->0/readbackfalse,slotempty;2partsBEFORE. Maskpasses;
Painnotattemptedafterlatch. StockSkeletonOnInsertion->PowerUpCyberwareEffector;
nativeRemoveSlotGLPsbeforeclearslot->UninitializedeletesenhancednoSideUpgradeItem.
Runtimeexact-itemlossconfirmed; nativesource/datapathmatches, directCF1logNEXT.
Noevidencebodymodcause; absenceofallbasecompanionsNOTproven. CF1ONEaddedREDS
CyberwarePreservationCF1:wrapeffectorUninitialize, skipdeletionONLYsameowner/data,
boundedSkeletonslot,exacttransientPTFRremovalID+activeDenied. Allothercallsnative.
Existingnativeunequip/statcleanup/conservationfaults/returns/savedfieldsunchanged.
Retainexistingadvancedinstance;nogrant/recreation/baseconversion/faultclear.
SCC92inclEquipmentEXPASS compiled69048139F144775725FADF354506BB475C1CCE21746BC0B6646D5C649C5A574A.
Compiledreadback13836otherclassesunchanged(normalizemethodorder/generatedIDs),
allpersistentfields/originalremoval/fallbackunchanged;14installerfixtureactionsPASS.
Verifier01methodorderassertfailed,02PASSwithoutcodechange. Validate/Install/Verify/
ValidateRollbackPASS;696protectedincl277savesunchanged. Noassistantlaunch/facts/
save/framework/archive/publicreleasechanges. H6/HS2/CD1/H5/FS1retained.
Manifest759A188913CEFC7E0D1B452F00CFEE195FEB221AC4819FE3D7BF916C4D1FF3FD.
Assessmentprealpha/cyberware_cf1/candidate_01/assessment_01.json SHA
6ECB083B73E883F4AAAE24F687E3B9A038C0457BF04A625F281CD8DFDD7A73A5.
Sources/proofsPINNED;usesuccessors. Evidencealpha_cyberware_20261025_01/local_repro_02.
RollbackCF1FIRSTbeforeCD1/olderR1:prealpha/cyberware_cf1/deploy_01.ps1
-ActionValidateRollback/Rollback;recovery/cyberware_cf1_01. FileundoNOTsaveundo.
NEXTcoldloadoriginalprefailfixture,bothSkeletonsequipped,CF1logs+CD1parts/qty
conserved/results1,Ready,removed-effects/newmanualslot+reload.LIVEPENDING.
docs/cyberware_cf1.md. PriorSkinreadbackwrong;actualSkeletonsuserconfirmed.

Latest2026-10-25 CD1 REPRO SLOT-CHECK CORRECTION:
USER beforethugsceneq307, liveR1 mode0/activefalse/pending0/faultfalse. PTFR
restrictionNOTblockingatthatmoment; priorcompleted-saveinferencewasincorrect.
BothAdvancedT1000Legendary2/AdvancedPainDistributorLegendary2 stockequipArea
161463225742 resolvesMusculoskeletalSystemCW(Skeleton), NOTIntegumentary(Skin).
Assistantpreviouslygavewrongskin-slotreadback; its3emptyIDsDONOTprovefailed
targetequip. NEXTcheckactualrecord-derivedarea/skeletonslots. Sharedvariant
prereqHumanityAvailableexists; failureNOTproven. Earlierlocalrunstilldidnotlog
targetremovals. Evidence diagnostics/alpha_cyberware_20261025_01/equip_area_03.json.
No runtime/save/fact/installationchanges; testerconservationfailureunresolved.

Latest2026-10-25 H6/HS2 USER LIVE PASS + RELOAD PERSISTENCE CONFIRMED:
After H6/HS2 install user reported "it works", then confirmed persistence after
the requested manual-save/reload check. Record paid H10 ownership/interactions
and successful reload as USER-REPORTED PASS for this fixture. Exact slot and
postreload balance were not supplied; no new log/save inspection this turn.
No claim of exhaustive housing/other-save/locale coverage or unrelated CD1 fix.
Documentation only; pinned build/install evidence and rollback chains unchanged.
See docs/h10_h6_snapshot_reload_hs2.md. No further repetition of this test needed.

Latest2026-10-25 CD1 LOCAL REPRO PASSED SETUP; TARGET REMOVALS NOT EXERCISED:
User session15:31:47-15:40:30 Toronto on confirmed2.50; scriptscompilePASS,
normalshutdown. Ready15:37:38 elapsedSim42.968750. CD1 onlyremovedMaskCWPlusPlus
andAdvancedSmartLinkLegendary successfully; quantities/partidentities conserved.
NoCD1FAIL/result-1/SetupStopped inthissession. CET loggedfourtargetEquipRequests,
butneitherAdvancedT1000Legendary2 norAdvancedPainDistributorLegendary2 entered
CD1removal. SubmittedrequestNOTproofequipped; refusalvslaternativeendingremoval
undistinguished. TesterfailureUNRESOLVED; thisrunNOTnegative reproduction of
targetremoval. CD1installedhashesunchanged. Evidencecopied/hashverified under
diagnostics/alpha_cyberware_20261025_01/local_repro_01/assessment_01.json.
NEXTverifyactualskin-slotsafterequipBEFOREending, or testerreproducewithCD1.
Noassistantlaunch/runtime/save/fact/installchanges; H6/HS2/otherchainsretained.

Latest2026-10-25 H6 H10 SERVICES + HS2 RELOAD CRASH FIX INSTALLED; LIVE PENDING:
USER H5dialogue/doorPASS; ownediconappearsafterleave/return;NOinteriorprompts.
Auto19/Auto2 copies/hashverified diagnostics/h10_services_20261025_01/inputs_02.
BothHousingRecordstate3,one25000debit219342->194342,Entitled/AccessApplied1.
H10PReady1;Enabled/Active/Interruptedabsentserialized,NOTassertedlivezero.
H10sceneabsentinstances;Auto19nearaptincludesWilsonscene. OldH10admissionbehind
general!IsEntityInScene+10tickthrottle; sourceblockerconsistentlogs, exactlive
predicateNOTrecorded. H6movesONLYsameH10permission/revocationblock to1secpoll;
ambientscene->actualdialogueguard. Combat/workspot/mount/tier/savelock/tokens/
location/nativeack/idle/entitlementretained. Noownerreset,replay,debit,sceneedit.
H6oneBaselineREDS SHA5D03F0FF9E6E6C521C7A1FC6A9F0DBBAA892461C9A850F5194BEE72D9CB5DED0.
USERAuto2loadcrash15:18:10BEFOREinstall. Dump7bb890copySnapshotRowHS1.facts
inRowJSONfromCET,index150/count179/sourceheader0. OldCanExportsavedready/frozen;
load/restore raceinferred,clearingwriterunidentified. HS2simcallbackserializes
16rows/tick totransientJSONcacheafterattachment;CETreadscompletedcacheonly,
attached/pregamegate;restore/detachinvalidate. Savedfields/format/origin/admission/
fileverification/ackunchanged. TwofilesSnapshotStateHS1+snapshotLua replaced.
HS2SCC91/30checks/14installeractionsPASS;H6SCC91/53checks/14actionsPASS.
BothValidate/Install/Verify/ValidateRollbackPASS;protected679/680incl265saves
unchangedatdeploy. Userloadchangeduser.glsbeforeclosedbaseline;save-slotfiles
unchanged. InitialH6CLIstringoperator/testparsererrorsfixedbeforepackaging.
LaterOTHERtaskCD1twofileschanged,verifiedreceipt;combined91sourcecompile04PASS
SHA1AB2995A3D18E1F6F2A13E0E1EF6A8D753C679544A81F0A1B1B63E0A44629115.
Noassistantlaunch/manualfacts/save/archive/framework/cache/publicreleaseedits.
Assessment diagnostics/h10_services_20261025_01/assessment_02.json SHA
B490D16C17BBDDED57BCAAE6E68DF55284B0A513E199A9DAD0278335299431A2.
Finalsources/proofsPINNED;usesuccessors. H6FIRSTbeforeolderBaseline rollback:
prealpha/h10_h6/deploy_01.ps1 ValidateRollback/Rollback;recovery/h10_h6_01.
HS2FIRSTbeforeolderHS1snapshot:prealpha/snapshot_reload_hs2/deploy_01.ps1 same
actions;recovery/snapshot_reload_hs2_01. Disjointtargets;HS2undo restoresunsafe
exporter. FileundoNOTsave/paymentundo. H5/FS1/CD1chainsseparate. NEXTAuto19paid
nearH10coldload,prompts,newmanualslot/reload;Auto2crashfixture.LIVEPENDING.
docs/h10_h6_snapshot_reload_hs2.md. Immediateiconrefreshnotchanged.

Latest2026-10-25 CD1 LOCALLY INSTALLED AT USER REQUEST; REPRODUCTION PENDING:
Installed ONLY the two existing CD1 diagnostic scripts, EquipmentHooks.reds and
StartupCoverLC1.reds. Hashes match pinned diagnostic ZIP; all removal guards,
returns, native call, profile transactions, saved fields and readiness retained.
CurrentH5/FS1 stack compiled91sourcesinclEquipmentEX PASS SHA
9C07BDB0A24D3D850063BC7D0A98615FF681B05DA0EF3B76242AE88732B0BFA6.
14realinstallerfixtureactionsPASS. Validate/Install/Verify/ValidateRollbackPASS;
679protectedfiles incl265savefiles unchanged. Game/launcher closed throughout;
no assistant launch, CET command, save/fact/archive/framework/publicrelease edit.
Recovery FIRST for these files: prealpha/cyberware_cd1/deploy_local_01.ps1
-Action ValidateRollback/Rollback; backup recovery/cyberware_cd1_local_01.
Local proofs build/local_install_01; manifest SHA
DC6CD1D231FD73E647DD6EBE2CF4A2CE3B9357A86EE8C12345352A4262C990CC.
Original tester ZIP/proofs remain pinned. Diagnostic-only, NOT a gameplay fix.
NEXT user reproduces on disposable untouchedpreending save, preserves gamelog
CD1 BEFORE/AFTER/FAIL rows before another launch. FileundoNOTsaveundo.

Latest2026-10-25 CD1 ALPHA TESTER CYBERWARE STOP DIAGNOSED; PATCH NOT INSTALLED:
Tester alpha/pre-ending log has AdvancedT1000Legendary2 result=-1 twice and
AdvancedPainDistributorLegendary2 result=-1 once, each immediately before cover
SetupStopped. Five preceding implant removals conserve item/parts. Camera/control
ack1; native arrival/optics/housing faults0/0/0. Confirmed R1 conservation latch;
missing item vs quantity vs part-count vs identity/slot NOT distinguished by old
log. Body mod reported; game probably2.5, exact loadout/patch unconfirmed. No proof
of item destruction or body-mod cause. CD1 diagnostics-only two-file alpha overlay
adds bounded pre/post item/part/quantity logging and all-six-fault popup/status.
Original native removal/control flow/guards/returns and saved fields unchanged;
compiled removal equivalence after removing log calls PASS. Full90source SCC
inclEquipmentEX PASS B99B66B86D1CF9C7589E8621D20CA854B6428ED449AA4DF32AEF1CE83671D3ED.
ZIP dist/cyberware-cd1/PTFR-CD1-diagnostics-for-alpha.zip SHA
989E5B3E196698F6B872CC2EC3E35A854DB9D7F67EA6E6532B806229B80EEEF8; readbackPASS.
NOT gameplay fix; tester must reproduce once from untouched pre-ending save and
return gamelog CD1 rows. No local install/launch/save/fact/framework/archive or
public-release writes. CurrentH5/FS1 remain installed. OriginalalphaZIP unchanged.
Sources prealpha/cyberware_cd1; proof build/candidate_01; evidence diagnostics/
alpha_cyberware_20261025_01/assessment_01.json. docs/cyberware_cd1.md. Rollback on
tester closesgame/restores2originalalpha files; fileundoNOTsavedgameundo.

Latest2026-10-25 H5 EXPLICIT H10 DIALOGUE PURCHASE INSTALLED; LIVE PENDING:
USER requests conversation-style choice instead of automatic activation.
H5 actor-free native scene attaches onScreen to exactH10door;3.5m activation/
5m indication. English Buy25000/Notnow; inactive insufficient-funds row.
No proximityShow; oldH3Show/callback+olddevicehandler inert, duplicate action
removed. Native entryONLYchoice+Ready0watch; explicitbuyONLYRequest1writer;
cancelwritesCancel1. UI consumes/disarms BEFORE unchanged HousingState.Purchase.
Attach/reset clears stale UI requests, eligibility/source/quote rechecked;
Notnow/refusal suppressuntilleave/reapproach. No automaticdebit/retry/refund.
EntirecompiledHousingState, Price,Location,Popup(DLC),Website,Map,Doorunchanged.
Existing lock/egress/payment/receipt/schema/paidservices/FS1 preserved.
5files:replaceHousingPurchase/HousingDevices;addHousingDialogueH5.reds,newH5
archive+XL (2unique resources,nooverrides,noactors). Noexistingarchive/framework
or save edits; no launch/manualfacts/publicrelease. Full91sourceSCCinclEquipmentEX
PASS compiledB7BEA2FF79DF6320D81727427746909C377FE7026EA735E0DCC9771DAF98FAC4.
64offlinechecks+14actualinstalleractionsPASS; Validate/Install/Verify/
ValidateRollbackPASS;674protectedincl265savefilesunchanged. Initialtestassert
scopedtoH10UI becauseunchangedwebsiteguardretainsinfoPopup; nofailedcodeinstalled.
Manifest8208BD53DCE5DB41E4D885CD3F3628FA491D9111E3515C4DD71EC02D31628AC9.
Assessmentprealpha/h10_h5/candidate_01/assessment_01.json SHA
9AC52AD8B9EF7A42842CDB30C3926526C1BF78FBF7AC7F9EF3410F26B2F9EC86.
Sources/proofsPINNED;usesuccessors. H5rollbackFIRSTbeforeolderhousingUI:
prealpha/h10_h5/deploy_01.ps1 ValidateRollback/Rollback; recovery/h10_h5_01.
FileundoNOTsave/paymentundo;keep preH5save forremovingnewnativeowner.
NEXTcoldloadunpaidpostTowerfixture,doorchoice/cancel/nocharge/reapproach/buyonce/
unlock/icon/services,newmanualslot+reload. Placement/input/transactionLIVEPENDING;
Englishonly,otherlanguagesuntested. docs/h10_h5.md. FS1livealso stillpending.

Latest2026-10-25 FS1 FRED PRIVATE SCENE RANGE REPAIR INSTALLED; LIVE PENDING:
USER requests fix after scene-source investigation. Fred requires V for real
spoken dialogue; cast/scene unchanged. Existing S25 fred.questphase ONLY changed:
ordinary scene admission<8m/departure>12m from original Fred reference; NPC
spawn/despawn remains original100m loading-marker lifecycle. Freshboxing
Issued1/Fault0 retains original50m admission/100m departure and scene300.
All original IDs/types retained. Nodes4/5 conditions updated;5.Out->400;new
400farbranch/401cutONLYprivate3+pending4/402nearORfarwait/403farbranch, then
rearm4+5 onreturn. Oldsavedwait5 canreachrelease withoutparentrestart; engine
savedconditionresumption/actorrelease LIVEPENDING. No300cut,spawnreplay,factreset,
saveedit,reward/quest/H10change. Fred.scene and mainarchive unchanged.
S25archive beforeDDCDA373...,afterFABEC35F7E3EFB0A017798C0F464FD17762F8206C2EDA344780C7A3A44B35E24.
FredphaseDF55D1C3725EDC1D9009F017E8D44679B6F718982E84C51BB47224C7672B94A0.
25otherresourcesbyteexact.702offlinechecksincl162conditioncases+14actual
installerfixtureactionsPASS. Validate/Install/Verify/ValidateRollbackPASS;
675protectedincl265savefilesunchanged;116otherPTFRfilesunchanged. No launch,
manualfacts,framework/REDS/newcompile/publicrelease. Initialbuild01 Clear alias
consolefailure WORKSPACEONLY; build02/candidate02final, pinned, use successors.
ManifestAC3BBE9A1DEB88FCAB27EBE831415F75224545ED587A08675361F52E3F160507.
Assessmentprealpha/fred_scene_fs1/candidate_02/assessment_01.json SHA
AA76BE4781ABF2DE409FFD236C2CF6181789509945FA4DC1E8332AC8C9026BC5.
RollbackFS1 FIRSTbeforeolderS25: prealpha/fred_scene_fs1/deploy_01.ps1 actions
ValidateRollback/Rollback; backuprecovery/fred_scene_fs1_01. FileundoNOTsaveundo;
preFS1fixture neededifrollingbacksavewithnewnodes. NEXTcoldloadAuto15,H10,
Fredtrade/smalltalk/leave/return,newmanualslot+reload. docs/fred_scene_fs1.md.
Fredsourceattribution remainsstrongcandidate, notdirectenginecallstackproof.
H10 explicit dialogue-style purchase remains separate pending work.

Latest2026-10-25 SCENE MEMBERSHIP INVESTIGATION; NO RUNTIME CHANGES:
Strongest source candidate is restored Coach Fred private fred.scene, NOT a
manually set quest fact. Auto15 exact depot hash in SceneSystem instances and
inspectionServices; Auto16/17 absent, their instances blobs byteidentical.
Fred Entries/Exits/SceneRequests=2/1/1 ->2/2/1 ->3/2/1; wrapperOwnerActive1
throughout. Matching-position load logs Auto15 scene=true, Auto17 scene=false.
Installed scene playerActor1=V/contextPlayer; service route1->96->choice3 plus
NPC workspot99. Owner starts scene <50m from Fred; exits >100m from loading
marker. S25 owner301 selects private branch unless freshboxingIssued1/Fault0.
Scene9BE6FC14..., S25phase06DE4B05... extracted from current installed archives.
Strong evidence, NOT direct runtime owner-table/callstack proof; other saved
scene records changed. Do not claim all scene=true episodes caused by Fred.
Keep H4 purchase-only guard repair; no global scene reset or blind actor removal.
117installed files match release;265savefiles unchanged. No launch/deploy/facts/
save edits. Evidence diagnostics/scene_membership_20261025_01/assessment_01.json;
docs/scene_membership_20261025.md. Inputs/proofs pinned; use successors.
At that time public documentation used the former name; the later official-name
decision above supersedes it. Legacy file IDs, URLs and
published assets retained. H10 dialogue-style purchase implementation
still separate pending work.

Latest2026-10-24 H4 PURCHASE GUARD REPAIR INSTALLED; LIVE PENDING:
USER H3forsaleiconvisible, stillnopurchaseinteraction. FreshH3logs 18:44-18:59
repeateddoor=true entrance=true released=true nativeUI=true popup=false,
high=1 tier=1 scene=true dialogue=false combat=false. No purchaseconfirmation
request. OriginalHousingState.SafeActor rejectsIsEntityInScene, soCanPurchase
neverallowsH10offer eveninfreecontrol. ThisisOBSERVEDFIRSTblocker; otherlater
gatesNOTruledout. H4changesONLYHousingState.reds; newPurchaseSafeActor duplicates
alloriginalSafeActorchecks EXCEPTambientIsEntityInScene. CanPurchase+readonly
PurchaseBlockH3 usenewguard; MigrationContextretainsoriginalSafeActor.
OriginalcompiledPurchase/singledebit/receipt/entitlement/reconcile/publish/
saved-schema unchanged. H3popup/icon/H2lock+insideegress/services/Wilson,
allframeworks/archivesunchanged. Noautomaticdebit, refund, reset, save/factedit.
InstalledStateSHA9E05BA53C51C0614CF167EDAF75D529CDAECA2FF4D1FEC93C725A4D19B91336B.
Full90sourceSCCinclEquipmentEX PASS compiledSHA
528E0F1BC7A23A6F7CA13BECDC7108C9D8309CCB76FDC65AD3B740B801B1ED78.
33code/readback+265savechecksPASS;14realinstallerfixtureactionsPASS. Validate/
Install/Verify/ValidateRollbackPASS;672protectedincl265savefilesunchanged.
Auto15copy/hashverified recovery/h10_h4_diagnosis_01; originalunchanged.
Noassistantlaunch/manualfacts/publicrelease. ManifestSHA
6304F826E3C68BC040B06F723FC28E8EEF1B3CE0D19C81F4BC213B9F94D4501A.
Assessment prealpha/h10_h4/candidate_01/assessment_01.json;finalsources/
proofsPINNED,usesuccessors. RecoveryH4FIRST beforeH3/H2/older:
prealpha/h10_h4/deploy_01.ps1 -Action ValidateRollback/Rollback,backup
recovery/h10_h4_01. FileundoNOTsaveundo. NEXTcoldloadpostTower fixture,
approachH10privateaptdoor, expectnativeYesNo25000,cancel/reapproach,
onecharge/ownedicon/door/services/reload. LIVEPENDING. docs/h10_h4.md.

Latest2026-10-24 H3 H10 NATIVE PURCHASE CONFIRMATION/MAP ICON INSTALLED:
USER H2doorlocked/nooffer; requests purchasableinsteadownedH10icon. ClosedH2
session normalshutdown18:26:41; doorresolved18:20:20 interiorDistance-9.245326,
NOofferlog. ExactblockerNOTisolated; pivotrange/custompopup/playerguardcandidates.
H3 nativeDoortrigger/SideOne/SideTwo overlapORold3.5m fallback; rearmoutsideall
volumesAND5m. Exactdoor/localplayerbindingretained. H10nowGenericMessage native
YesNo25000 viaPopupsManager lifecycle; token/serialconsumedbeforeexistingH1
Purchase. Cancel/OK/stale/duplicatecallbacksnodebit; DLCpopupclassunchanged.
HousingStateONLYreadonlydiagnosticmethodadded; alloriginalcompiledpayment/
SafeActor/entitlement/reconcile/publish/schema methodsunchanged. H2unpaidlock,
insideegress/paid-onlyservices/Wilsonleaseunchanged. Noarchives/frameworkedits.
OriginaljournalPOI points_of_interest/safehouses/v_room reactivatedforSALE;
exactjournalhashselectsoriginalmappin; unpaidZzz05_ApartmentToPurchaseVariant,
paidApartmentVariantfromdurableEntitled. No duplicate/newpins/publicFTchanges.
TransientcachedIDresetonreload; missscan5ticks; nolargescaneverytickafterfound.
3files: PurchaseE0AAE026..., State3E1F0FD4..., ADD EntranceH3 5D2021BE....
Full90sourceSCCinclEquipmentEX PASS; compiledB4A3A91E4D7338E12CFEE2336C207A9A8305F308965CB7917A40C0B05EB1B3AE.
50code/readback+259savechecks,14actualinstallerfixtureactionsPASS. Validate/
Install/Verify/ValidateRollbackPASS;659protectedincl259savefilesunchangedduring
deployment. InitialcaptureprecededUSERAuto14rotation/user.glschange; finalclosed
baselineused. Auto13/14backedupseparately recovery/h10_h3_diagnosis_01/02; original
savefilesnotedited. Nolaunch/manualfacts/publicrelease. H3liveUI/purchase/icon/
services/reloadPENDING; noverifiedrootcauseclaim. Earlierannotationexperiments
failedCLIonly; nofailedcodeinstalled. Finalcompile_04/tests_01/deployment_tests_01.
ManifestB752E44C6CAE87F14D8C6322C3CA78373DB350B19E3F5A0258C3B97F1FDD9231.
Assessment prealpha/h10_h3/candidate_01/assessment_01.json SHA
AC1CFB513809C4341373785B82ADC5AFFD84E9D5F15E503D84981080E1385D1F.
Finalsources/proofsPINNED;usesuccessors. RecoveryH3FIRSTbeforeH2/HS1/olderhousing:
prealpha/h10_h3/deploy_01.ps1 -Action ValidateRollback/Rollback; recovery/h10_h3_01.
FileundoNOTsaveundo; savedPOIpresentationmaypersist. NEXTcoldloadsamepostTower,
checkforsaleicon/nativeconfirm/cancel/reapproach/singledebit/ownedicon/services,
newmanualslot/reload. ReadonlyHousingPurchaseUI.StatusH3(); docs/h10_h3.md.

Latest2026-10-24 H2 H10 DOOR/PURCHASE + WILSON LEASE INSTALLED; LIVE PENDING:
USER confirms unpaid homes need NOservices; privateH10door MUSTblockentryuntilpaid.
PriorLC3nowliveReady17:49:09/42.5simsec, normalshutdown17:53:46; loadingloopPASS,
NOTH2payment/vendorpass. Auto11/12unpaidHousingRecords; all6filesbackedup+hashchecked
recovery/h10_h2_diagnosis_01. H1intentionallyleftdoorsusable; customaction lacked
declaredchoice metadata. H2nativePaymetadata+onceperapproachpopup atEXACTh10door,
25000explicitconfirm, cancelrearmsafter5mexit. Originalsingledebit/receipt/schema
unchanged; NOunpaidservices. OwnprivateDoorPSlockflagpersistent; open/lock/visual
routesguardedonlyunpaidexactH10. Outsidecloseswith0.75mthresholdmargin; inside
saveegressallowed; onlyownlockreleasedafterpayment/egress. Liveforward+bedanchor,
inactiveprefabfallbackCURRENT2.5nativepoint(-1377.66956,1275.32336,123.554993),
corrected19bitnode5665/sourcebound; unknowngeometrydefer. No public/liftdoorlock.
WilsonAuto11/12QuestOwns1/Released1/Near0; Issued/Enteredabsentserialized, runtime
checksrequired. S23reservedvendorBEFOREnativeparent/contentwait; exactsavedwait
notdecoded. H2newleaseAFTERparents, sameoriginalIDs/guards/child/rewards; saved
oldwait1011stillpreparent. Eightnewnodes/fivereroutes; nativeReleased/body-idle
ackrequired. One-timelegacyreservationreleaseguardedbynewLeaseRequested0,
Issued/Entered/Finished/Fault0+bodyidle/nativeattention/genuineending guards.
BaselineNearnowrespectsQuestOwns soordinarybodydrains; noactor/questrestart.
ONLYmq011privatewrapperchanged,33otherS23resourcesbyteexact; archiveSHA
7289DF77E4EAE2FE8133C8AF7003E6536CA645C5D696849DD4D50DE68E5AE83B.
6files:4replace(Devices/Purchase/Baseline/S23archive),2add(DoorH2/WilsonLeaseH2).
89sourcefullSCCinclEquipmentEX PASS; compiledSHA
600B092B4A952D1AB2B13FF56570E8BA0CC60BB7CC6B911B515F3D0A257AB804.
92offlinechecks+14actualinstalleractionsPASS; Validate/Install/Verify/
ValidateRollbackPASS;653protectedincl259savefilesunchanged. Framework/cosmetic/
mainarchive/H1archive/HS1unchanged; noassistantlaunch/saveedit/manualfacts/release.
Finalnative_02/compile_04/tests_02/deployment_tests_01; firstnativebuilder cyclic
Equals overflow WORKSPACEONLY, successorReferenceEquals PASS. Finalsource/proofs
pinned;usesuccessors. ManifestC037EC9A47079C974C1E26A6F1F622C62B225591D37FBADA9102A24E2510382B.
Assessmentprealpha/h10_h2/candidate_01/assessment_01.json SHA
A2B91550B3F1CFA4552A632467E0C538177CCE214015C8DA497F6726B4FD09E9.
RecoveryH2FIRSTbeforeLC3ORS23: prealpha/h10_h2/deploy_01.ps1 -Action
ValidateRollback/Rollback;backup recovery/h10_h2_01;fileundoNOTsaveundo.
NEXTcoldloadexistingpostendingfixture,canceloffer/lockedentry,reapproachconfirm/
singlecharge/access/services; insideegress,newmanualsave/reload,WilsonTrade.
AllH2livebehaviorPENDING; docs/h10_h2.md. Privatecandidates/backupsGitignored.

Latest2026-10-24 LC3 EXIT REMOVAL/10-11 LOOP REPAIR INSTALLED; LIVE PENDING:
USER removeexitoption, setuposcillates10/11.17:32sessionprofileall27ranks+HP150,
housing/nativefinishedack,finalchecks41.31simsec;45alternations~1s. Normalshutdown
17:33:39: passesSC1crashpoint, NOTfullstartup. H1Tick1s CanPurchase->SafeActor
requires!InScene; PurchaseReady startsV-acquiringscene; Ready0watcherexits;
nexttickrestart. Oldpurchasedfactadmitsremoteowners. Source-provenfeedbackmatches
logcadence; oldcombinedcontrolpredicateNOTexactfailingtermliveproof.
LC3Esc/cancelhint+actionremoved, includingfault/timeouttext. PublicLeave(epoch)
retainedinertforAPIcompatibility. NativeinputblockerandALLreadinesspredicates+
1scontinuousstabilityretained. No elapsedbypass/fakeprogress/forcedfacts.
HousingPurchaseUI offers+Show requireGameplayReleased; offersalsorequireexisting
exactentrancevalidator.4purchase-scenes playerActorsremoved(unused),1debugsymbol
eachremoved;all5executablenodes/edgesunchanged. Noactorrefsremain;13otherarchive
membersbyteexact inclSC1services+savedowners. Payment/ownershipreceiptsunchanged.
3REPLACEMENTS StartupCoverLC1.reds,HousingPurchase.reds,H1archive SHA
4D4CB40E745F9508F97F1A2A0F2D09DD02E0AD527BEC1A4D1B874AA647F55208.
Addedfinalheartbeatarrival.Status/bodySafe/4purchaseactivefacts diagnostics.
Full87sourceSCCinclEquipmentEXPASS,compiledSHA
8BFB147CEAE835E16CFF8A2D27EE0EC20583A9BF4A867CBCD455A5075E674069.
73offlinechecks+14actualinstalleractionsPASS. Validate/Install/Verify/
ValidateRollbackPASS;647protectedincl253savefilesunchanged. Nolaunch/saveedit/
manualruntimefacts/framework/mainarchive/cosmetic/publicreleasechanges.
Evidenceprealpha/loading_cover_lc3/candidate_01/assessment_01.json SHA
F20FA4A3B729FDD19C16C809910596BC9F5BA667576557C3D2F3017F09D8CE5F;
manifest4DDCD26E63E6B251137271B7B36B94588AF2D5243DFF4660B68C0844A8210593.
Finalsources/proofspinned;usesuccessors. candidate_*Gitignored.
NEXTcoldloadsamefixture,coverrelease/control/noEscaction; newmanualslot+reload.
Actor-freepurchasechoice/confirm/cancel/paymentLIVEpending; exactcontrolcause
ifstillblockedloggednow. docs/loading_cover_lc3.md. RecoveryLC3FIRSTbeforeSC1OR
LC2 (overlapsboth): prealpha/loading_cover_lc3/deploy_01.ps1 -Action
ValidateRollback/Rollback,backup recovery/loading_cover_lc3_01. FileundoNOTsaveundo.

Latest2026-10-24 SC1 STARTUP CRASH REPAIR INSTALLED; LIVE PENDING:
USER crashwhilecovervisible41percent5/12. Actual17:07:29dump nativeoverflow:
410592809 entries*24=9854227416. UnwoundSceneResourcehash831467AE67C510EA
matchesH1 corpo_purchase.scene. NPCcount0/playercount1 butplayerActorId3;
native2c9a3c passesID,2c9f30 subtractsNPCcount/indexes176byteentry. Dumpindex3
readswrongdefinition; actualplayerfacialcount0. Confirmedourprunedsceneindexbug,
NOTprofile/cover/driverblamefromlastlog. NineH1scenesallnondense:4purchase,
4services+Kerryearnedservice. Remaplocalactor/typedperformerrefs; remove18stale
actor-debugsymbols.458IDchanges; nodeIDs/edges/payment/conditions/ownerresources
preserved; noexcludedNPCrestoration/savedownerreset. OnearchiveREPLACED:
00000000_TowerContinued_Housing_H1.archive beforeE8F4F535...,after
76A4DE057573AE13CB698AED6E757454A07D95DBC00A94F9D5F63DA484CBDA07.
9privatesceneschange,8othermembersbyteexact. Audit89installedTowerscenes:
9H1fixed; legacy streetkid_seat_s1/seat.scene also nondense, untouched/notcrash,
reachabilityunverified.1531native/semantic/indexchecks+14actualinstalleractions
PASS. Validate/Install/Verify/ValidateRollbackPASS;636protectedincl241savefiles
unchanged. NoREDS/framework/cache/mainarchive/gameplayfact/savewritesorlaunch.
LC2livepositive:opaqueprogressUI/nativefade/camera/control/BodyReliccomplete;
HS1verified158row post_ending_fallback JSONexport. NOTpreendinghistory/livefull
startup/profile/housingpass; fullspeedunmeasured. Samefailedattemptfixturecold
loadNEXT; newmanualslot+reload afterready. PrioractiveH1scenesavereloadpending.
Evidenceprealpha/startup_crash_sc1/candidate_01/assessment_01.json SHA
86428B5CB8D52079FF6F903ED06C08BD07277CF134222EEB1E00B82363C81FDF.
Manifest4B5413220CD8906FECE5AB4E5C1103E49BDDD464B26568B90D1D0387046EDD54.
build_02/tests_01/cause_02 final; build_01 missingreadbackdirectoryfailedonly
workspace; opcodeasserttranscriptioncorrectedbeforePASS. Finalproofspinned,
usesuccessors. candidate_*Gitignored; no publicrelease. docs/startup_crash_sc1.md.
RecoverySC1FIRSTbeforeolderH1: prealpha/startup_crash_sc1/deploy_01.ps1 -Action
ValidateRollback/Rollback; backup recovery/startup_crash_sc1_01. Restoresknown
defectiveH1indices. CoverrecoverychainLC2->LC1->HS1separate; fileundoNOTsaveundo.

Latest2026-10-24 LC2 STALL REPAIR/PROGRESS INSTALLED; LIVE PENDING:
USER >2min coverstall, requestslogs/fix/progressbar. 16:30-16:38 sessionnormal
shutdown; LC1logonlytwo stagechanges, NOTproofsimulationpaused. Actualnative
180 resetsCoverReady0 then181ONE-SHOTCondition falsehasnoedge; laterUIackcannot
resume. LC2 changes181sameID toPauseCondition waiter, True->Out successor176;
allothernodepayloads/615resources/current2.5lighting preserved. Noending/teleport/
camera/transactionreplay. Nativeinputblockerretained; noaddedpause/tier/status.
OpaqueUIanimationcompletionack replacesSimTimefirstframe dependency; epoch/
visibilityguards retained. 12actualcheckpoints progressbar, refundcounterstext,
100onlyfullbarrier+1simsecondstable. 5engine-secondheartbeats includefacts/wait
reason+engine/simelapsed. 120engine-secondwarning retainscover/exit; noautounlock.
SECONDconfirmedblocker: currentenum194 vsold189 validators. Nativebase+EP1audit
448records,1626existingfieldsmatch; Coolroster37->42,CentralMilestone3prereqgone.
Bind3catalogues toexactnewdata incl5newCoolrecords, retainnewperks/no newbans.
Profilepolicy/fingerprint/savedfields/APIs/refundbodiesunchanged. NOsilent189array
reindex orfaultedtransactionreset. Stuckold181savedownerNOTreplayed: retryretained
pretransitionorknownpostendingfixture, notnewsavefromfailedcover.
Installed5REPLACEMENTS: StartupCoverLC1,BodyCatalogue,RelicCatalogue,ProfileDefinition,
mainarchiveCFB7F613EC15A934B74984B4C26392E7B4B7AC0A38B2C24067C69A395ACF2744.
Full87sourceSCCinclEquipmentEXPASS; finalcompile_02SHA
781D4E6272F6F20F1F62E69DE1C0466F2605DFB66D7E6D5CF379D748DB6C25A9.
1011offlinecompiled/native/cataloguechecks+14actualinstallerfixtureactionsPASS.
Validate/Install/Verify/ValidateRollbackPASS;625protectedincl235savefilesunchanged.
Noassistantlaunch/saveedit/manualruntimefacts/framework/cosmetic/publicrelease.
Finalsource/proofspinnedprealpha/loading_cover_lc2/candidate_01; usesuccessors.
compile_01pre-shortererrortext; changes_01intermediatecoverhashNOTfinalmanifest.
Manifest8C57D77865F0D8D0E7654DCA33D4927BFDD4EA66ACC4EA8853D6E530FC5801B5.
AssessmentD00E8FC059B09C5A835EEF453EEE92D1013417AE966D89C2E7A5878162CBF95E.
RecoveryFIRSTprealpha/loading_cover_lc2/deploy_01.ps1 ValidateRollback/Rollback,
backuprecovery/loading_cover_lc2_01; THENLC1->HS1->older. LC2undoalone restores
LC1knownloadingbug; removeLC1nexttoreturnHS1main2FC245. Neveroldcrashingsector.
FileundoNOTsaveundo; core/cosmeticchainsseparate. docs/loading_cover_lc2.md.
NEXTcoldloadretainedpretransitionorAuto8/9,newmanualslot; bar/inputs/firstframe/
Esc/snapshotexport/profile/housing/world/quests/fullreveal/save+deathreload LIVE
PENDING. No measuredspeedup. Progressbarischeckcount,NOTtimeestimate. Vikdoorseparate.

Latest2026-10-24 LC1 LOADING COVER/SCHEDULING INSTALLED; LIVE PENDING:
USER requests cover untilsetupcomplete andfasterdeployment. Installed17files:
14existingREDS replacements+2newLC1REDS+currentmainarchive replacement. No
framework/cache/savefileedits orassistantlaunch. All606protectedincl229saves
unchanged. Core/cosmetic stackretained. Existing savedfields/APIs preserved.
PTFR.LoadingCoverLC1 usesbaseCodewareCustomPopup, opaque/inputblocking, NO
InGamePopup time dilation/modalcontext/statusrestriction/tier/cameraoverride.
Cover waitsverifiedHS1 snapshot, arrival/optics, cyberware, Body/Relic/profile
transactions+ledger+actualHP, housing/relationships, H10geometry+entitledservices,
entrydispatch/nativehandoff,8adapterclassificationpasses, freshcontrol+1sstable.
Unknown/unsupported/prerequisiteblockedquestsDEFER, notinfinitewaitforremoteactors.
NewU9requests/unissuedS2/S22/S23/S24/S25/S27/S28/U10permits/OnlyPainactivation
helduntilrelease; existingowners/progress/rewardsretained. Completedreloadreads
savedprofile/body/housing/handoffreceipts; validatesledger/HP/cyberware without
demandingnewrespec/holster/combat exit. Weapon/combat/vehiclepathLIVEPENDING.
Esc requestsMAINMENU, keepsblockeruntildetach; neverunlocksunfinishedgameplay.
180simsecondwarningdoesNOTsucceed/clearfault. Pendingpopupservice+epochs prevent
oldattachmentack/duplicatequeue; actualinput/nonpause/firstframe/liveQA pending.
Nativefinalboards adds180ownCoverReady0 and181waitCoverReady1 before176native
fade; preservesPA3fade/Tier1/controlorder, oldpayloads/timeoutcuts and615other
resourcesbyteexact. Mainnow
9D9AF716B78187B2A02790CB9B57D6C87E953D9790D57513888991AAC5C2CBCC;
finalboards4A52C9A4D7C73F4074052EE220BFC3E631DB830477D163FECAA16F9940102536.
LightingB56A759A...current2.5 retained; q307ending/camera/teleport unchanged.
Body/Relic refundopportunities0.25s onlywhenwarmup0/noqueued/inflight; other
profileonlystage2 removes4tickthrottle. Nativeadmission/ledger/transactionbodies
retained; Bodysettling>=4elapsedseconds; Entry>=3ssafe. Entryreadiness0.25s
separatefrom5sdispatch. H10retry1suntilgeometryack. 27rankopportunities27->6.75s
isSOURCEESTIMATE20.25slessdelay, NOTmeasuredtotal. PTFR_LoadingLC1stageelapsedlogs.
FullSCC87sourcesinclEquipmentEX PASS; compiled
127B94A076D754380F27EFFED1E257A9AAFB71D1E536E5686FE69FDCD3439AE5.
129offlinecompiled/native/preservationchecks+14realinstallerfixtureactionsPASS.
Validate/Install/Verify/ValidateRollbackPASS. Finalscriptcandidate_04/compile_02,
tests_01/deployment_tests_01; nativecandidate_02/native_01. Earliercandidates
historical; changes_01intermediatehashesNOTfinalmanifest. Sources/proofsPINNED,
usesuccessors. Evidenceprealpha/loading_cover_lc1/candidate_04/assessment_01.json
SHA3483E2795B58BD3B3FDC3736B4347CB3F2A72555DC7117B0146B0F29D2EF5188.
Manifest23053BDD80CBBD26B44CA2756E2830082A388C4492364E36C6687EBBC7A49337.
RecoveryFIRSTprealpha/loading_cover_lc1/deploy_01.ps1 -Action ValidateRollback/
Rollback, backuprecovery/loading_cover_lc1_01; restoresHS1+working2FC245mainwith
currentlighting; THENHS1/olderTowerpackages. NEVERobsoletecrashingarchive.
FileundoNOTsaveundo. Core/cosmeticrecoveryseparate. No publicrelease/commit.
NEXTcoldloadretainedAuto8/9,newmanualslot: coveropaque/noinputleak/setupadvances,
Escmainmenu; fullsetuprelease; save/reloadnorefund/reward/lossreplay. Separate
normalendingneededfornativehandofffirstframe; completedcombat/vehicle/deathreload
alsoLIVEPENDING. docs/loading_cover_lc1.md. Vikdoorstillseparateunresolved.

Latest2026-10-24 HS1 SNAPSHOT/FALLBACK INSTALLED; LIVE PENDING:
USER explicitly accepts currentpostending snapshot when no preending snapshot
exists. This supersedes blanketunknownhistory denial, NOT completion/reward/
owner preservation or resume-not-restart. Never label fallback asprehistory.
Oldprobe saveembeddedonly; newPTFR.HistorySnapshotHS1 stores158selectedroots,
140detailed/18rootonly, NOnewrestorationcoverage. Two-passboundedread captures
ordinaryworld; recentsettledcutoff freezespre_ending. Missingvalidfrozenbaseline
aftergenuineTowercompletion capturesONCE post_ending_fallback. Unstable/unknown/
completed/failed baselines denynewadmission; supportedactiveprogress preserved,
unsupportedresumeDEFER. U9requiresfullfreshstate/factchecks; nativeguardsretained.
Family accepts recordedq103Succeeded+done+rogue fromacceptedbaseline; doesNOT
setfamilyPreTowerCompleted. Noexcludedparentreplay or genericrecursivecoverage.
CET PTFR_HistorySnapshotHS1 writesverifiedJSON initsownmodfolder. Savepayload+
filenamebinding authoritative; missingfile reexportsSAVEDpayload, notnewstate.
Differentfile preserved; nogloballatest/import. Fileackrequiredbeforeadmission.
TenREDSreplacements+state/dataREDS+CETinit additions=13filesinstalled. Existing
savedfieldidentities/APIs retained. Initialstartupcycle bypass usesverified
snapshot+genuineending/nativearrival/control/camera; nodevcertificatefabricated.
ScopedFault2continuation validatesexactfailednativebranch, recordsownreceipt,
clearsONLYPTFRPA2_Fault2; existingprofile/housing/arrivalcontinue. Finished1only
afterallrequiredacknowledgements. Noending/teleport/camera/transactionreplay,
no native story factsetters. Otherfaults untouched. Actualcurrentfinalboards
AB65019B... boundtomain2FC245..., failure160hasnooutgoingedges; oldwaiterscut.
FullSCC85sourcesinclEquipmentEX PASS; compiledSHA9A991411...; compiledcritical
predicates/schemas/474arrays/316stringschecked.21offlinechecks+14realinstaller
fixtureactionsPASS. Validate/Install/Verify/ValidateRollbackPASS;608protected
incl229savefilesunchanged. Noassistantlaunch/savefileedit/manualruntimefacts.
Manifest57A86058601DDA771A77BD13076FBE9389967449505E3ADDFD3AD6459E7CFFE4.
Evidenceprealpha/history_snapshot_hs1/candidate_01/assessment_01.json SHA
A6B8748A84B292657FE867851033B74F50B58706E86D2CB57F2349EE7EFE5259.
Finalcompile_04/tests_02/readback_01/native_check_01/deployment_tests_01 current;
changes_01 intermediateafterhashesNOTfinalmanifest. Finalsources/proofsPINNED,
usesuccessors. candidate_* andprivateevidenceGitignored. No publicreleasechange.
RecoveryFIRSTprealpha/history_snapshot_hs1/deploy_01.ps1 -Action ValidateRollback/
Rollback, backuprecovery/history_snapshot_hs1_01; THENolderTowerscriptpackages.
JSONfilespreservedbyrollback; fileundoNOTsaveundo. Core/cosmetic/L1chainsseparate.
NEXTcoldloadretainedpostendingAuto8/9,newmanualslot, checkGetMod("PTFR_HistorySnapshotHS1").Status(),
JSONorigin/ready/frozen/exported, profile/housing/quests, save+reloadwithoutreplay.
Precutofftraversal/serialization/CETcallbacksexistonlyofflineproofsLIVEPENDING.
Auto6/7arelate2079, NOTprecleanupcapturetest. Nonpausingcover/refundspeed/Vikdoor
STILLSEPARATE; no measuredspeedup. docs/history_snapshot_hs1.md; mutablepolicy
pointerupdated, pinnedR6.1selectionbytesunchanged; selected158/implemented140.

Latest2026-10-24 CORE/COSMETIC USER PASS; STARTUP INVESTIGATION ONLY:
USER reports no crash/freeze/missing models/textures after latest patches.
14:18 session normalshutdown14:26; core0823FB99/CodewareGlobal02C3D252,
UV C46F73/headE0E132 retained. NOT startup/housing/quest-restoration pass.
109Towerfiles still match expected inclmain2FC245;229savefiles unchanged.
Confirmed startupcycle: lateending Restored freezes unknownhistory; Activated
requires endingObserved/certified OR alreadyPrepared/Finished; profile/housing
needed to produce Prepared neverstart. BothretainedAuto8/9 Fault2, controls/
camera/opticsready, entryonlyfrozen serialized. Unknownhistory staysunknown.
Separatecoreinitializationauthorization fromquestcertification; no devadmission.
Fault2nativewaiters werecut; clearingfactalone cannotresumeoldowner. Needbounded
continuationwithoutending/teleport/camera/refund/housingtransactionreplay.
Bothfixtures14Body+5Relic+8otherblockedranks=27 one-secondrefundopportunities,
NOTmeasuredliveduration. Five-seconddispatchthrottlealsodelaysreadiness.
Proposeacknowledgedshortticks+event-drivenready checks, preserveelapsedsettling.
NativePA2blackoutheldTier5/deadlockedTier1; keepPA3nativeuncoverbeforechecks.
Proposemodownednonpausingcoveroverrunningworld; CodewareUIcandidateexists,
inputcapture/menu/time/firstframe/reloadbehaviorstillrequiresliveprototype.
Readybarrier=profile/housing/localworld/camera+eligibilityclassified; unknown/
unsupportedquestsdefer, remoteactors/unownedH10servicesdonotblockforever.
Viktorclinicdoorseparate. NOstartupimplementation/build/install/launch/factwrite.
Evidence diagnostics/startup_logic_20261024_01/assessment_01.json SHA
576C22D154F7C249B1CEA759CF4BDE3C66CA9921FD8C2295F6675F6A8E6A7A9D;
docs/startup_logic_20261024.md. Audit11sourcechecksPASS; finalinputs/proofspinned,
usesuccessors. NEXTimplementationsequenceinreport; beta/savecontractretained.
Rollback/core/cosmetic/Towerrecoverychainsunchanged; no new recovery package.

Latest2026-10-24 CORE UPDATE RECHECK; TWO UPSTREAM PATCHES INSTALLED:
USER explicitly approves Nexus/GitHub downloads and core installs. No newer
official releases found: RED4ext1.30/CET1.38/redscript0.5.32/EquipmentEX1.2.9/
DQC3.3.1 current. TweakXL22 and ModSettings33+34 heads unchanged, retained.
ArchiveXL current PR31+SDK229+SDK230 retained; add ONLY PR32 empty partsOverrides
guard in customization cloning. FullPR32 SDK lacks current229 mesh layouts;
not wholesale installed. WorldStreaming source matches31, NOT new regression.
ArchiveXL DLL before53AE211F... after
0823FB99B45AE16519BE196E491F5CB3998BBD08475621967B5BE80D4476E2BF.
Codeware PR63 retains DLL/types/APIs; backport PR65@39a6856c two-line explicit
emptyVariant return. Codeware.Global.reds beforeDCC24988... after
02C3D2529C3E7143E4E6D1D562134F6CC56A1281F8E617D1A4DFAB0ADFAD1A45.
LOCAL patches, NOT new official releases/fullPR32/full2.5compatibility proof.
MSVC/xmake build+AMD64/exports PASS;10759 source checks, one substantive block
plus two generated timestamps. FullSCC83sources inclEquipmentEX PASS; compiled
Reflection fallback readback PASS. Initial assertion syntax/timestamp mismatch
corrected in successors; compiler itself passed, no failed output installed.
Validate/Install/Verify/ValidateRollback PASS;660protected incl223saves unchanged.
UV C46F73/headE0E132/Tower2FC245 preserved; caches/Persistent/settings unchanged.
Nexus35697 bundle hidden by moderation; public GitHub sources used. RedHot held.
Evidence diagnostics/core_updates_20261024_01/assessment_01.json; final proofs
and package pinned; use successors. No assistant launch/save/fact/Tower writes.
Framework recovery FIRST core_updates_20261024_01/install_01.ps1 actions
ValidateRollback/Rollback, backup recovery/core_updates_20261024_01; THEN SDK230
clothing_freeze installer; then older framework recovery. Cosmetic03->02->01
and Tower L1 recovery separate. Journal/hot-reload limitations remain.
NEXT cold load same inventory save, check head/body and white hospital shirt
without original overwrite. Clothing freeze resolution STILL LIVE PENDING.

Latest2026-10-24 BODY TEST3 USER PASS; CLOTHING FREEZE SDK230 TEST INSTALLED:
USER bodyrestored, equippingwhitehospitalshirtFREEZE(cannotclose/tabout), NOT
reportedcrash. EquipUI/exactitemrecordunknown. Processabsentwhenchecked; logs
no normalshutdown, no newcrashreport/dump. Windowseventsno matchingGPU/hang
entry inchecked3h, NOTproofGPUexcluded. Preservevisiblehead/bodyworkarounds.
InstalledArchiveXLPR31hadoldITransactionSystemFindSlotData0x448/visual-tag
lookups; localclothinghandlerscallthem. PR32reports2.5hangfromoldlookup;
SDKPR230correctsFindSlotData0x450 etc. Stronglead, NOTuserfreezerootcauseproof.
BuiltisolatedPR31@5f7dc882+ONLYSDK230headerpatch@b985c06f;10759sourcefiles
compared,onlyotherchange2generatedVersion.rcbuildtimestampdefines. Product
still1.27.5; distinguishhash, NOTnewofficialrelease/fullPR32compatibility.
MSVC14.44/xmakereleasePASS; AMD64DLL/3exportschecked. SandboxedC1902failed,
samecodeunsandboxedbuildPASS; earlierpath/timestampassertfailuresretained.
InstalledONLYred4ext/plugins/ArchiveXL/ArchiveXL.dll:
before2F16D9BD6B8CBF22AA004DEA198A9F8B7C4F7621CEC921682F8BA412E08EE002;
after53AE211FE55833537101F492EE7C0C6802B39B6DCB1A19CDE68570F756D9AFD4.
Validate/Install/Verify/ValidateRollbackPASS;635protectedincl223savesunchanged.
Evidence diagnostics/clothing_freeze_20261024_01/assessment_01.json. Sources,
build/package/deployer/proofsnowpinned;usesuccessors. Noassistantlaunch/saveedit/
fact/Tower/otherframeworkwrites. UV C46F73/headE0E132workaroundsretained.
NEXTusercoldloadsameinventorysave,checkbody/head,trywhitehospitalshirtwithout
overwrite. FreezeFIXLIVEPENDING; no fullgarment/2.5compatibilityclaim.
FrameworkrecoveryFIRSTclothing_freeze_20261024_01/install_01.ps1 -Action
ValidateRollback/Rollback, backup recovery/clothing_freeze_sdk230_20261024_01;
onlythenolderframeworkrollback. Cosmeticundo03->02->01stillseparate; L1unchanged.

Latest2026-10-24 HEAD TEST2 USER PASS; FEMALE BODY UV TEST3 INSTALLED:
USER confirmshead/faceANDarmsvisible, restofbodymissing. Test2femaleheadUV
disable restoredhead withstockgeometry; implicatespatch/frameworkinteraction,
NOTproofofUVpackagealonebug. OriginalVTKheadgeometrywithUVoffSTILLuntested.
Test3 changesONLY!!!_UV4.xl: removesfemale7mesh+1morphtargetmappingpaths,
10lines2groups; retains2malegroupsbyteexact. Femaleheadpatchstaysoff.
BeforeSHA 7D635F2F78EBC8E861FED6B457A5030E8EF4747552603834BBFCCF7F002DD2A2;
afterSHA C46F73C586602ED4A08382F6DFF3CEB233248A2543D87A4AE1916AD3140880CD.
VTKheadE0E132stockgeometrytestretained; allbodyarchives/arms/nailsunchanged.
Validate/Install/Verify/ValidateRollbackPASS;635protectedincl223savefilesunchanged.
Evidence diagnostics/missing_head_20261024_01/assessment_03.json; test_03 prior
userpositiveheadresult/logs/build pinned,usesuccessors. BodyLIVEPENDING.
RecoveryFIRSTinstall_03.ps1 -Action ValidateRollback/Rollback restoresheadvisible
test2UVconfigfrom recovery/missing_body_uv_test_20261024_03. Fullcosmeticundo
03THEN02THEN01; donotbypasshashguards. Tower/L1recoveryseparateunchanged.
Latest12:16RED4extlogendsafterSCCsetupwithoutshutdownmarker; NOTnormalshutdown
proof. Nolaunch/saveedit/fact/framework/Towerwrites. NEXTcoldloadsameinventory
savechecktorso/legsANDheadwithoutoverwrite; texturealignmentalsoLIVEpending.

Latest2026-10-24 HEAD TEST1 FAILED; FEMALE UV HEAD PATCH TEST2 INSTALLED:
USER AutoSave7cutscene andothersaveinventory stillmissingface. Geometryexclusion
aloneNOTfix; VTKinteractionsNOTruledout. Latest12:12RED4extnormalshutdown.
Test2 changesONLY!!!_UV4.xl: removes2linefemaleheadmapping,4othergroupsbyteexact.
BeforeSHA 34C90A065970E9D23A58E1E6222E7C97D7E7ED47973735226A2FB6B12719FCBC;
afterSHA 7D635F2F78EBC8E861FED6B457A5030E8EF4747552603834BBFCCF7F002DD2A2.
Test1E0E132geometryexclusionREMAINSinstalled; now2cumulativecosmeticfilechanges.
Validate/Install/Verify/ValidateRollbackPASS;635protectedincl223savefilesunchanged.
Evidence diagnostics/missing_head_20261024_01/assessment_02.json; test_02 has
usernegativeevidence/logs/build. Finaltest2sources/proofs pinned; usesuccessors.
Recoverytest2 install_02.ps1 -Action ValidateRollback/Rollback restoresUVconfig
from recovery/missing_head_uv_test_20261024_02. Fullcosmeticundoalsoinstall_01
restoresVTK. Tower/L1recoveryseparateunchanged. Nogame/save/fact/frameworkwrites
exceptoneXLconfiguration; nolaunch. NEXTcoldloadsameinventorysave/checkface;
cutscenereplayunnecessary, nooverwrite. Rootcause/fixstillLIVEPENDING.

Latest2026-10-24 MISSING HEAD: VTK GEOMETRY ISOLATION INSTALLED; LIVE PENDING:
USER sameappearanceworkedbefore2.5; missingheadincutscene/inventory/thirdperson.
89archiveinventory: onlyVTKreplacesstandardfemaleh0mesh+2morphs. h0mesh/morph
both27591vertices; no internalh0mismatch. he morph53954 vs referencednativehe
12393firstchunk isconcern, NOTprovenmissing-skinrootcause; embeddedbasecaveat.
UVdefaultpatch doesNOTreplaceexistingnonnullrenderblob perinstalledsource.
Onefiletest vtk_VanillaHD_Head_xBaebsae.archive omits3headgeometryresources,
retains3seam/material/textureassetsbyteexact. Noreserialization/frameworkchange.
OriginalSHA A910A12A16EE8D2DE0E0FA82756C08495CD1514B3715168BF898F6CABB8EF138;
testSHA E0E132BC3D3755259A53977D3461F44AA27DBD15119CF2FCB79DB481C7FFCACB.
Validate/Install/Verify/ValidateRollbackPASS;635protectedincl223savesunchanged.
Evidence diagnostics/missing_head_20261024_01/assessment_01.json; scripts/pins
retain,usesuccessors. RecoveryONLYthiscosmeticfile: samefolder/install_01.ps1
-Action ValidateRollback/Rollback, backup recovery/missing_head_test_20261024_01.
Tower2FC245/L1recoveryunchanged. Nolaunch/saveedit/factwrite/publicrelease.
NEXTusercoldloadAutoSave6,checkinventoryheadwithoutoverwrite. NOTverifiedfix.

Latest2026-10-24 CORRECTED PRE-ENDING AUTOSAVE BACKUPS:
USER clarified wanted latest2 BEFOREendingcompletion, notpostending8/9.
SelectedAutoSave7(11:29:13Toronto, takewalkwithMisty)andAutoSave6(11:24:50,
returnDelamain); neitherlistsq307finished, bothtrackThingsDoneChanged.
All6filescopied/hashverifiedbefore+after; originalsunmodified. Recovery:
recovery/pre_ending_autosaves_20261024_01/{AutoSave-7,AutoSave-6,receipt.json}.
Thesearelate2079endingfixtures, NOTpreTowerpoint-of-no-returnhistoryproof.
Postending8/9backupsretainedseparatelyasfaileddeploymentfixtures. No game edits.
Evidence diagnostics/pre_ending_autosaves_20261024_01/receipt.json; Gitignored.

Latest2026-10-24 DEPLOYMENT TEST BACKED UP; STARTUP REGRESSION DIAGNOSED:
USER reachedH10afterending/cameraOK/freeroamOK; H10geometry/vendors/2079scenery
visible. FAIL no profile nerf/no restoredquests/H10interactions/housingrules;
Viktorclinicdoorunopenable; headmissingincutscene/inventory/thirdperson(eyes/teeth).
AutoSave8(11:36Toronto)and9(11:41)copied+all6fileshashverifiedto
recovery/deployment_test_20261024_01; originalsunchanged. SavedatSHA8 D9536740...
9 D14A7DD8...; fullhashesreceipt.109/109TowerfilesmatchlatestexpectedinclL1
main2FC245...; usertraversedendingwithrebasedsector, normalshutdown11:42:51.
Thispassesobservedload/arrival, NOTfullL1lightingvisibility/modcompatibility.
BothsavesPTFRPA2_Fault=2 preparationtimeout; ControlReady/CameraAligned/OpticsReady1.
SavedPreAlphaEntryonlyfrozen=true; Profile/Bodypersistentfieldsdefault/omitted;
Housinginitialized5unknownhistoryslotsbutnotactivated. InstalledH1disablelate
fixture+ActivatedrequiresendingObserved/certified/ALREADYcompletedhandoff:
freshlatecutoffloadcannotinitializeprofile; housingwaitsprofile; watchdogfaults.
Rootissupportedbyactualsources+savedstate; NOTmissinginstallation/compilerfailure.
QuesthistoryunknownmustNOTbeinventedbyreenablingdevelopmentadmission; futurefix
separatespostendinginitializationfromquesteligibilityandboundedfault2continuation.
Noforcedfacts/replayteleport/cleararbitraryfaults/resetprogress. ThingsDoneChanged
disappearance+q307completedmetadataNOTrestorationproof. DoorSEPARATE:Save9front/
inner/rearRequests1Ready1 meansactionsissued, NOTphysicalunlockedproof. Headcause
unisolated; VTK/UV2.5mesh-morphcompatibilitylead, NOTIFPblameorverifiedfix.
Evidence diagnostics/deployment_test_20261024_01/assessment.json SHA
C7A6B0007EBEA0EAE933BAF775AF9956823E3E1205F4449B87B0D5F524E6FDE6.
No game/save/cache/fact/installation/launch/agentchanges; NOrepairinstalled.
RecoveryFIRSTlighting_rebase_25_20261023_01 unchanged; oldcrashingarchiveprohibited.
Backups/diagnosticsexcludedfromGit. Publicprealphastillold; nopublicbetaclaim.

Latest2026-10-23 L1 CURRENT2.5 WORLD REBASE INSTALLED; LIVE PENDING:
User PASS ManualSave-10 withothermodsrestored andoldsectoromitted. Latest23:21
RED4extlog normalshutdown; actual83-sourceSCCsuccess.130restoredhashesverified;
originalManual10unchanged. RedHotToolsheld; IFP Lua2.1.4starts butoldnativeheight
plugin skipped(incompatibleruntime). ArchiveXLJournalhook837162664failure remains.
Followuprebased12R8lightingaliases onto CURRENTep1_1_nightcity sector D0C015BA...
Currentsectorversion68: 4539placements1631nodes; nodeindex19bitsat0x70, NOTold
uint16at0x78. WolvenKit9.1oldbufferparser silentlymisreads4512indices; doNOT
serializeitsparsedNodeData. Readonlynamedcooked-type adapters+rawcorrectedindex
usedforinspection.10lights fullpayloadmatch;2meshplacementsuniqueexacttransforms
nowworldCookedStaticMeshNode. Nativecookedmeshbytes preserved, visibilityLIVEpending.
Rawpatchonly12zero globalNodeIDs +12existingNodeRefstrings; offsets/CRCs updated.
2537nativechunks61otherbuffersbyteexact;4539placementreadbacks,88lightpayloads
unchanged;615otherTowerresourcesbyteexact. Noquest/script/owner/savefactchanges.
InstalledmainarchiveSHA 2FC245B128EFD1E6DEC9B6CF38FC037490578EC252E120FD40C57D24EFDDF255;
rebasedsectorSHA B56A759ABCA6F86FBF7E2C61016E0F87D995ECA3E99EFBFFA253B69AEE6A311B.
Validate/Install/actualhash/ValidateRollbackPASS;651protectedincl217savesunchanged.
Evidence diagnostics/lighting_rebase_25_20261023_01; recoveryFIRST itsinstall.ps1
-Action ValidateRollback/Rollback restoresWORKING55D53E...sector-exclusionarchive
from recovery/lighting_rebase_25_20261023_01, NOTobsoletecrashing6B9AAE...archive.
NEXTsameManualSave-10load withoutoverwriting; laterpostTowerlightingvisibility.
Nolaunchbyassistant; nofullgameplay/betacompatibility/newpublicreleaseclaim.
Priorpassedload evidence save_load_other_mods_restore_20261023_01/live_result_01.

Latest2026-10-23 SAVE-LOAD CRASH ISOLATED; OTHER MODS RESTORED, LIVE PENDING:
ManualSave-10 pre-ending cabride: vanilla/core-only USER PASS; Tower+core
CRASH; disabling13XLworldblocks stillCRASH; excludingONEobsoleteofficial-sector
override USER PASS; restoringall13XLworldblocks alsoUSER PASS. Latestlog normal
shutdown. OldR8 exterior_-25_18_0_0.streamingsector override caused observed
loadcrash; installedmainarchive now615retainedresources byteexact, sectoromitted.
Current TowerContinued_PreAlpha.archive SHA
55D53E8040656FFD0CE90420637C2EF6220C6E492AB5BA8D05AFA694D7AD10FC;
originalXLrestoredSHA CD75C3446C74B4D57F94AD19B0A130B84E214BBED9BD2FDEDD4AE6D798A59544.
Oldsector supplied12R8lightingaliases; compatiblecurrent-sector repair STILL
needed. q307_ending_board nativebytes unchanged; donotblindlyrebuildq307.
Othermods130missingfiles restoredhashverified, inclcustomnail,CET,IFP,ModSettings;
RedHotTools native+CET remainheld.83scripts matchpriorfullSCCproof; norerunneeded.
522protectedfiles unchanged incl217saves; noassistantlaunch/saveedit/factwrite.
NEXT manuallyloadsameManualSave-10 withothermods; doNOToverwriteoriginalsave.
Currentevidence diagnostics/save_load_other_mods_restore_20261023_01;
rollbackonly130additions via its restore.ps1 -Action Rollback, receipt in
recovery/save_load_other_mods_restore_20261023_01. DoNOTbulkrestoreoldmainarchive
fromrecovery/release: it reintroducescrash. Publishedprealphapackage stillold;
norebuiltlighting/fullcompatibility/newreleaseclaim. Allpinnedoldproofsretained.

Latest2026-10-23 HOUSING H1 INSTALLED; BETA SAVE CONTRACT; LIVE PENDING:
USER wants beta with initial postTower t=0 state complete; permits incomplete
questrestoration/bugs but requires beta saves usable by futurestable. This
SUPERSEDESolderdevelopment-savecompatibility-notrequired foractualreleasedbeta.
H1 implements ordinary5home loss once; H10 repurchase25000,4DLC6currentnative
prices/prereqs. ExplicitUIconfirmation+exactreceipt, noautocharge/retry/refund.
Sharedstashcontents/nativepurchasehistory/earnedkeys/questprogresspreserved.
HomePOIs/privateFT/services gated; publicdoors/egress preserved, NOTallphysical
doorslocked. Websitepurchase/nativePayroutes guarded. Kerrygenuinefriend/romance
accesssoleexception; currentTower322SetVarmanagers containnoearnedfactclearing.
NoKerryactor/quests/romancefabrication. Relationship7/10/13mirrorsSuspended1,
unearned20onlysuspended;4homePOIsinactive,9exactrelationshipstash/wardrobe
paths incl4typednomadcampstashvariants. Existingactionsfinish; nownerrestart.
Twooldmodownerconditionsonly(H10gate2,Judywait7/13), IDs/edges/payloadsotherwise
retained.17resources6boots,5fileADDS2REDSreplacements,0officialoverrides.
Stable PTFR.Housing HousingState/HousingRecord v1:19savedfields5fixedproperty
slots;13oldtypes88fields/catalogues/bootpaths preserved. Unknownhistoryunknown.
Futurestable MUSTretaincontract/ownerIDs andtestretainedbetasaves; no replay
loss/payment/refund/reward/questprogress. No claimunbuiltstablealreadytested.
Integration03 disablesnewlatefixtureauto-admission; onlyacknowledgedfinished
handoffcontinuation allowed, NOTnewgigcertificate. Workingarrival/camera kept.
Housing/relationshiplossack gatesreveal; unpaidH10doesnotdeadlockstreetreadiness.
Finalprealpha/housing_h1/build/h1_02/build.json SHA
14A2AFAC82F6B3A64E0441CEF8990DE0CFF10E97F54CC8EDFE25847C1D154C81;
archiveE8F4F535A9A24B8C080360D68C8993B19EDE12366118284E5A9CE683A0CA523E.
Componentsnative06/runtime04/purchase10/integration03; pack03.1820native,
336runtime160purchase32integration1206independentscene411Kerry60Panamsource,
226compatibility52compiledbodychecks;20actualpackageinstall/rollbackcasesPASS.
FinalfullSCCwithEquipmentExPASS; scopedCLIPASS. EarlierH1syntax/Booloperator
failureswereWORKSPACEONLY; SCCdisplayederrorUI, neverinstalledfailedH1.
PreferCLIpreflightbeforeSCCtoavoidfailurepopups; fullCLIEquipmentExrestriction
isnotfullSCCfailure. Supersededbuilds/proofsretained.
ClosedValidate/Install/actual7hashes/ValidateRollbackPASS;717protectedunchanged
incl215savefiles5cache. Nolaunch/saveedit/manualruntimefactwrite/frameworkedit.
Allfinalbuilds/sources/tools/tests/reports/receiptsNOWPINNED: use successors.
RecoveryFIRSTprealpha/housing_h1/deploy_01.ps1 ValidateRollback/Rollback with
recovery/housing_h1_01, THENS28/U10/S27/DT1/S26/S25older. FileundoNOTsaveundo.
Evidence research/housing_h1/assessment_01.json; docs/housing_h1_playtest.md;
docs/beta_release_contract.md. NEXTcoldloadsameworkingbranch,newmanualtestsave;
normalpurchase/cancel/funds/homeactions/Kerry/relationship/cold+deathreload.
SeparateactualpreTowerending+betatosuccessorsavefixturesneededbeforepublicbeta.
No newquestcoverage:80gigs60side=140/158bounded;18sidejobsremainunimplemented.
Otherinitialstate/releasechecksnotdeclaredcomplete. PublicbetaNOTpublished.

Latest2026-10-23 S28 FOUR SIDE JOBS INSTALLED; LIVE PENDING:
USER selectedCodeware63/skippedfurtherTOOLtests/resumedrestoration, thenexplicitly
approvedframeworkstackandS28afterautomaticapprovalreviewblocks. PriorS28
workspace-only/noinstall statusSUPERSEDEDforthispackage. InstalledSpaceOddity,
EzekielSawTheWheel,Highwayman,ImInLoveWithMyCar boundednativebeginnings.
Completed/earnedunfinishedprogress/existingowners/items/vehiclespreserved;
unsupportedresumeDEFER, no restart/reset/rewardreplay. Immediate3nativeREDSpreds
recheckdurablevehicleownership/localplayer+exactloadedHooncratekeyquantity0;
unknown/unloadedcrateDEFER, normalwarehousevisitmayberequired. Originalnative
quests/choices/rewards/prerequisitesretained. PrivateJohnnyworkspotsanchoredto
originalworldnodeswithanimationprop-events muted; dialogue/JV1preserved.
Finalprealpha/sidejobs_s28/build/s28_01/build.json SHA
625C89CC165815C572051D081548056FF356C04FFDBD1DE25C5F45A5FCE77433;
archive5D2BDCBAD16A7B7A5D6290888BE000993ECBADD122E00321349254FEE1BE2B76.
Componentsencounters08/vehicles05/runtime03;20resources4boots,3ADDS0replace,
0official/modoverrides.342nativepayloadchecks1912policycases; fullSCC78installed
sourcesincludingEquipmentEx/36arrays/3completepredicatebodiesPASS.63official
resources/87installedarchives/0collisions;96realbuilddeploycases115checks0skip
UNSANDBOXEDPASS. Independentencounter157/vehicle480+266casesPASS, notliveproof.
Currentjournalmetadata61pathsverified;only2exactunusedmappinenumsnormalized
metadata-only;no journalshipped. Fullrawbytesseparatelyboundtocurrentarchives.
ClosedValidate/Install/actual3hashes/ValidateRollbackPASS;716protectedunchanged
incl215savefiles5cache;25workingpackagefilesverified. Framework18afterhashes
rechecked. NOgame launch/saveedit/runtimefactwrite/newtooltestcampaign.
Finalsources/builds/tests/compiler/auditor/deployer/receiptsNOWPINNED;successors
forchanges. Evidence research/sidejobs_s28/assessment_01.json SHA
0EDB2D62B83EC72F4D3C02BD9C126BA714FAADCF7BDAE72747A1F1C9CA015D65.
RecoveryFIRSTprealpha/sidejobs_s28/deploy_02.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s28_01,THENU10/S27/DT1/S26/S25/older. Frameworkrollbackseparate
research/framework_pr63_01/deploy.ps1 -Action Rollback. FileundoNOTsaveundo.
Coverage80/80boundedgigs+60/78side=140/158;includesconditionalFamily, NOTallstage/
currentbranch/liveproof.18selectedsidejobsstillnoaddedimplementation. GlobalR6.1/
Heroes/BrendanpolicyenforcementandH10startup-speedworkremainseparate;H10unchanged.
NEXTnormalcoldlaunchsameworkingpostTowerbranch,newmanualtestsave; noendingreplay
orforcedfacts. Nativecalls/scenes/devices/rewards/workspots/reloadLIVEPENDING.
See docs/sidejobs_s28_playtest.md. Olderdiagnostic/statusentriesbelowarehistorical.

Latest2026-10-23 FRAMEWORK PR63 INSTALLED / S28 RESUMED:
USER selectsCodewarePR63, explicitlyskipsfurtherTOOLtests, continuesrestoration.
Afterautomaticreviewrejection USER explicitlyapproves exactexperimentalstack:
Codeware63@6ef34ff0,TweakXL22@fee3a94,ArchiveXL31@5f7dc88,officialredscript0.5.32.
ThisSUPERSEDESearliernoframeworkinstallationinstructionforthisapprovedpackage.
BuiltMSVC14.44/xmake3.1.2;onlybuildconfigpin tiltedcore.mimalloc2.2.4.
Installed18changedfileswithbackup recovery/framework_pr63_01/receipt.json;
allinstalledhashesmatch;6cache/Codewarepersistentfilesunchanged. RED4ext1.30.0
alreadyinstalled,retained. NOgameplay/tooltest/launch/save/factwrites.
Sources/package/deployer research/framework_pr63_01. Rollbackusesdeploy.ps1
-Action Rollback, guardedagainstlaterfilechanges. EarlierU10modrecoveryunchanged.
ArchiveXL31journalextension/hotreloaddisabled upstream;NOTfullmodcompatibilityproof.
S28restorationresumed;encounters08currentdonorsbound,vehicle/runtime/aggregate
successorsinprogress. NO S28install yet. Continueactualmodbuildchecks;doNOTrestart
tooltestcampaign. Preservecompleted/earnedprogress;unsupportedresumeDEFER.

Latest2026-10-22 REDSCRIPT FAILURE ROOT CAUSE; DIAGNOSTICS ONLY:
USER asks investigate currentcompilerfailure/potentialsolutions. Currentcache
REDS/version14 is structurally valid at checkedheaders/tables/strings. Newextra
12byteheaderdescriptor shiftsstringdata104->116. Stable0.5.31 sequentialreader
ignoresactualoffset, misreadsfirststringoffset757935405 into2523537bytebuffer,
causingEOF BEFOREmodcompile. Source-bound research/redscript_2_5/binary_reader_01/
diagnosis_01.json. Preview22 respects offsets, compiles+readsbackminimalSmoke,
BUTwriter drops new2509884byte/209157entrytable andflags2->0. Extra tablepurpose/
engineacceptanceUNKNOWN; neither safe nor runtimebroken proved. NOpreviewinstall.
Controls: stable+oldcache passes Codeware1.20.3AND1.20.6; preview+oldcache both
fail9access/visibilityerrors; preview+currentcache adds24duplicate-methoderrors.
LatestCodewarealone NOTsolution. Currentcache callbacksignatures differ from
Codeware; sharednames NOTproofcachepollution. 78installedsources isolatedpreview
fail125964diagnostics, mostlyrepeatedFactFinderstructconstructor. Workspace-only
syntaxexperiment7files/62892constructor+14spacingchanges reduces to167errors;
NOTcompletedmigration/productionpatch. Need compatibleformatreader/writer plus
frameworkAPI compatibility; stablebackport ispotential, notbuilt/testedsolution.
Alltests workspace-only; no game/save/cache/framework edits orlaunch. Preserve
oldcache ONLYascontrol, neverrestoreitovernewgame. S28encounters07 prepared,
vehicle01 zero-dispatchprototype; neitherinstalled. RecoveryU10firstunchanged.

Latest2026-10-22 PATCH2.5 COMPATIBILITY INVESTIGATION; S28 NOT INSTALLED:
USER requests more selected sidejobs, then supplies official Edgerunners2
Patch2.5 announcement and asks impact. S28 targets SpaceOddity/Ezekiel/
Highwayman/ImInLoveWithMyCar. Workspace candidates only; no new coverage claim.
Steam updated current game after U10 validation: build26133166,39/57official
archives changed length; scriptcache/tweakdb changed. Internalexe3.0.5813403
is NOT marketingversion; officialannouncement callsupdate2.5. Earlier U10/
oldercompile/nativeproofs remain historical, NOT current2.5compatibilityproof.
InstalledstableCLI/SCC cannot read currentcache. Workspace-only preview22
reads it but compilationfails Codewareduplicate methods+olderPTFRsyntax;
NO successful currenttoolchain/fullcompile. No installedframeworkreplacement.
Official current mq003/default_dialogs/q101Takemura bytes differ; nativeagent
scopedgraphcomparison finds mq003graph/dinersubtree unchanged, broaderbinding
stillpending. WolvenKit8.20 fails some updatedworlddecode/extraction; verified
official9.1 console downloaded workspace-only for successor diagnostics.
Vehicleownership/worldpresence/Johnnyworkspot checks remain incomplete.
Preservecompleted/earnedprogress/owners; unsupportedresumeDEFER. No resets,
save/factwrites/game launch/S28install. Newpatchquests NOT automaticallyselected;
Tarotextension needs Misty-policy review. NativeThingsDoneChanged cabfix needs
comparison before altering working H10handoff/camera. No startup speedfix.
Evidence research/sidejobs_s28/review/environment_change_01.json,
review/tooling_preview_22/probe.json,review/preview_compile_probe_01/assessment.json.
Recovery U10first unchanged; do NOT follow older coldlaunch/test guidance as
evidence of currentcompatibility. Complete compatibility checks before newinstall.

Latest2026-10-22 U10 EIGHT GIG ENTRIES INSTALLED; LIVE PENDING:
USER requested restoreall8andapprovedparallelagents. Psychofan/GoingUpOrDown/
GustavoOrta/Ladrillo/RaceToTop/Scrolls/FamilyHeirloom/GreedNeverPays nowhave
boundednativebeginningpaths. Completed/earnedprogress/existingownerspreserved;
unsupportedunfinishedDEFER, NOrestart/reset/rewardreplay. Nativefixertiers,
prereqs/choices/devices/rewardsretained. SixexactQuestitemzero guards intyped
CreateQuery runtime+immediatenativechecks; unknowninventorydefers.
FamilyHeirloom requiresgenuinePRETowerGhostTowncompletion. Newpersistentwitness
observescompletedq103+nativefacts intwosettledpreTowerpolls; NObackfill/devfact.
ExistingpostTowersaveswithoutthatwitnessDEFERFamily, notall8currenteligibility.
Familyexactembeddedafterphasepackagedprivateinclcontext; nativeDanretained.
PsychofanscopedJohnnyprops/workspotsadapted; voice/dialog/timingkept,JV1unchanged.
Ladrillo/Greedtwooriginalretaliationselectors restoredwithinexistingU9controller,
ownStartedgated; nativeidlequeue/serviceReady/Issued guards, NOownerrestart.
42resources28boots,3fileADDS0replace,1modretaliationoverride0officialoverrides.
Finalprealpha/gigs_u10/build/u10_02/build.json SHA
3819C27855AC161252ED0846A02028C8B4D6F0EBF3D46E14E5C451F535401C66;
archive2DD9DEC6814817086D88CD4DD9B6979E49FDEC02D15864779EE36A8CE276C64B.
Componentsnative06/presentation03/runtime02,contract02.1445nativepayloadchecks,
3532policycases,1522independentreviewchecks; scopedCLI/fullSCCEquipmentEx+88arrays
PASS.104nativebyteexact+2journalmetadata+2Arroyovariants,106depotcomparisons;
Arroyoonly2knowncookingPlatformfields differ,ALLusedgraphs/contextsame.86archives,
62ALLXL,42packedreads107freshrawdecodes284buildpins.106deploycases125checks
UNSANDBOXEDPASS0skip; earliersuperseded/failedproofsretained. Finalsources/builds/
tests/compiler/auditor/deployer/receiptsNOWPINNED; use successors forcodechanges.
ClosedValidate/Install/actual3hashes/ValidateRollbackPASS;712protectedunchanged
incl215savefiles5cache,22workingfilesverified. Nolaunch/saveedit/runtimefactwrite.
RecoveryFIRSTprealpha/gigs_u10/deploy.ps1 ValidateRollback/Rollback with
recovery/gigs_u10_01,THENS27/DT1/S26/S25/older. FileundoNOTsaveundo.
Coverage80/80boundedgigentries(includesconditionalFamily),56/78side=136/158~86%;
NOTallstage/currentbranch/liveproof.22selectedsidejobsstillnoaddedimplementation;
globalR6.1enforcement/Heroes/Brendanpolicyworkunchanged. H10unchanged,NOSPEEDFIX.
NEXTcoldlaunchsameworkingpostTowerbranch,newmanualtestsave,normalnativegates;
noendingreplay/forcedfactsneededforregression. Livecalls/devices/rewards/Johnny/
retaliation/savedownerreloadpending. See research/gigs_u10/assessment_01.json
anddocs/gigs_u10_playtest.md. Manual PTFR.GigsU10.GigsU10 Status()/Inspect(id).

Latest2026-10-22 USER RESUME POLICY / RESTORATION SPEED TARGET; STATUS ONLY:
USER confirms H10arrivalFIXED. Preserveworkinghandoff/camera; doreviewstartup
latency so playerneednotstandholstered/still/menusclosedabout1min. Durationis
USERobservation, NOTprofiledfixed60stimer. Targetbackgroundpreparation+bounded
work-specificsafetygates; donotblindlyremovecombat/scene/ownerchecks. NOspeedfix
implementedthisturn. S27warmup3x1s+stableSafe samples/sharedBodyPolicyobserved,
NOTproofthatS27causeswholeminute. Needcriticalpathtimingbeforepatch.
USER nowwantsunfinishedjobsCONTINUEprogress, NOTrestart. ThisSUPERSEDES17OctS26
sidejobrestartpolicyandrestarttextinR6/R6.1/olderdocs. Completedpreserve,
unstartednativebeginning, unfinishedresumeearnedobjectives/choices/items/rewards.
UnsupportedresumeDEFER, nosilentrestart/reset/rewardreplay. Existingrestorations
preserved; notgenericresumeimplementation orbroadergigfreshness/replayauthority.
ExcludedprerequisiteBEFORETowercompletionruleunchanged. CURRENTpointerrecords
policyoverridewhilepinnedR6.1bytesremainunchanged.
Coveragecomparison:R4installed72gigs+58boundedside roots(S25:52,S27:+6).
IntersectR6.1=>72/80gigs,56/78side (Heroes+Brendandumpsternolongerselected).
128/158installedboundedcoverage81%;8gigs22sideNOnewimplementation. NOTallstage/
gameplayverification; notinventinstalledcoveragefromnewwhitelist. General5tracks
implemented:userfunctionalpassesNCPD157POIs,courier,airdrops,cyberpsycho17,
repeatablerace4routes. Allindividuals/rewards/recurrence/reloadNOTfullytested.
Statusbasedoninstallrecords,NOTnewactualfilehashaudit. No runtime/game/save/
fact/install/launch/agents. RecoveryS27firstunchanged.

Latest2026-10-21 USER PREREQUISITE CLARIFICATION R6.1 POLICY ONLY:
Excluded requiredparent/ancestor mayqualifyselectedchild ONLYifgenuinelycompleted
BEFORETowerwithcorrectoutcome. Unfinished/neverstarted/unknownpre-endinghistory
BLOCKchild. Noexcludedparentrestore/forcecompletion/backdating/devcertificate.
SelectedparentscanprogresspostTowernormally; preservenativeAND/ORrequirements,
sharedresourceNOTautomaticdependency, childowncast/profile/outcomechecksremain.
Existingowners/completedrewardsprotected; noautomaticcancellation/reset.
R6finalclaimwasTOOBROAD:1903checksNOTfullrecursivedependencycoverage; stillneeded.
Countsunchanged80gigs78side; R6.1correctsOneWayorAnotherparentRoadstoRedemption
sts_ep1_07 cleanup writeswst_ep1_09_active1, NOTPrototypeintheScraper. Complete
handoff/runtimeproofstillpending. CURRENTpointer ->
research/gig_restoration/lore_whitelists_v6_1_dependencies.json SHA
4BDB18F026F0B8ABFB9E7EEA595057A1FEC27E023DEE79A572BF8F20D4E57B6D.
R6pinnedbytespreserved; successorsource dependency_clarification_01.py.
Docs/roadmap/alpha policyupdated. NOgame/save/fact/install/launch/agentchanges.
RuntimeenforcementNOTinstalled; recoveryS27firstunchanged.

Latest2026-10-21 FINAL WHITELIST R6 SELECTION AUDIT CLOSED; NOT INSTALLED:
USER authorizes list edits/finalaudit. R6 broader target80gigs78side=158,
30adds(8gigs22side),1removeBrendandumpster vsR5. Alternateconservative34+29=63,
no newstrictadds.227reviewedrecords=158INCLUDE51EXCLUDE18SEPARATE_SCOPE;
188othercataloguerootsoutsidegig/sidejobselection.0open selectiondecisions.
CURRENT research/gig_restoration/lore_whitelist_current.json ->
lore_whitelists_v6_final.json SHA
3B9E2C558BD70A9C62CA059D1AE9E64D06627F32ED8E20D20D214F9FF842598F.
R5/R4 pinnedinputs unchanged; NO installedgenerator/admission/config rewrite.
Retain4excludedlivecharacters Misty/Panam/Judy/Kerry; Johnnyvoice/invisibleactor
only, noindependentprops/takeover/Relicrevival. BasicKiroshi wasALREADYexplicitly
approved: Nitroselectedunderexistingexception, no newimplantpermission. Personal
LinkMQ018router/Connect+MQ058wiredminigame supported; nodeck/autowinpermission.
Nitroproxyreturn/liveprofilepending. FreedomYorinobuarchivalownership canretime
inbroadmode, NOTfixedpoliticsreset. DelamainTowercabbranchesnativefate0/1/2;
sequelonlyunresolvedoriginalidentity, NOTundoexistingreset/merge/destruction.
BrendandumpsterexcludedconservativelyBody3vsEASYcurve/wait; liveplacedoverride
unmeasured, NOTprovenliveimpossibility. LaterBrendanselectedONLYearnedearlier
completion. MoneyForNothingexcludedthisrelease: noverifiedBody3obstacleroute,
noinventedthreshold; neverusewrongwst_ep1_08merchantcontroller. WaterRunsDry/
DirtySecondHandsexcludedearlieroperation.30addsfullregistry/docs catalogued.
KerryhouseSOLEretainedaccess/home,no removal/repurchase/noKerryquests/spawn.
H10repurchase25000,otherownedapartmentsrepurchasenormalprice. Completedstays;
unfinishedsidejobrestartONCEtarget, generalmigrationNOTimplemented; gigfreshness
separate. Existingowners/completedrewardsprotected. HeroesS27newadmissionDENIAL
andfreshBrendanpolicyenforcementSTILLpendingseparatepatch; DONOTremoveS27.
Cuckoosceneref/EP1followupowners/Viktorservicelines areimplementationwork,
notopenlistdecisions. PreserveClaireembeddedhelperwitness. Noendlessre-audit;
onlynewuserpolicy/materialnewevidencechangesfinalselection.1903identity,
membership/targetednativechecksPASS, NOTliveproof. Sources/scripts/outputspinned
byresearch/whitelist_final_r6 assessment+verification; no overwrite/rerunbuilder.
Search20resultURLs4streams3fetchedexcerpts; nativefilesprimarytechnical.
Docs/ROADMAP/playtestpolicyupdated; allgame/save/fact/cache/installwrites0,
noagents/launch. RecoveryS27firstunchanged. See docs/whitelist_final_r6.md.

Latest2026-10-21 R5 RECHECK / CONTINUED INVESTIGATION ONLY:
Re-screen129R5rows72gigs57side/943questsceneresources; noNEWconfirmedexcluded
participantinboundedroutes, NOTfullcast/gameplaycertificate.23hitfilesclassified:
15presentationreuse,2sharedTarotdonors,1prefabID,1historicalmention,1draft,
1Polishfalsepositive,1actualmention,1Viktorservicehold. R5SHAunchanged.
FortunateSonPanam3db_dbdrafts mapen_usRaffenShivlines; FreedomPressPeralez2drafts
mapmedia/veteranlines. DoNOTexcludeoneditorstrings. ProphetPanamnewroleisactual
en_usmention, timingcaveatNOTcast. StadiumHolt-targetlinesnotfixed-electionproof;
FifthColumnjournalactualelectionseason, alreadybroadonly; timingreviewremains.
BrendanfreshprofileHOLDforverification: officialmq037_dumpster EASY Athletics,
nativeAthletics=>Strength+SkillcheckBonus,attribute_checksEasylinear4/4/10at
1/3/40. Body3zerobonusbelowtemplatecurve. MQ037root/19:7DemolitionPerformed
wait->13Succeeded;34ForceEnabledNOTskillbypass. Placedoverride/livebonus/value
notcaptured. SprayPaint/Coinfreshfamilydependency; preserveearnedcompletion.
NoBodyraise/GorillaArms/factbypass/ownerreset. ViktorMisty/Relicservicechoices
stillreachabilityhold; PaidInFullboundeddebtseparate. Cuckooscenegapstillunknown;
ClaireexternalnamedgapNOTinvalidatepriorS27embeddedhelperaudit.
MoneyForNothingwikiwst_ep1_08IDcontradictedbynative merchant/body/hoboevent;
NEVERdispatch08asKatyastash. Targetscenejournalwritesfound;fullstash/deviceowner
stillpending. OneWayparent32/33etc:09onlywst_ep1_09_active==1gateconfirmed,
NOTcompleteparenthandoff; Corporewardownerpending. Prior21proposalsretained,
0newpromotions/R6/install. Kerryhouseexceptionunchanged. HeroesS27admission
enforcement/generalunfinishedrestartSTILLpending; recoveryS27firstunchanged.
Evidence research/whitelist_recheck_20261021; docs/whitelist_recheck_20261021.md.
1944integrity/nativeassertionsPASS, NOTliveproof. Search20slots4streams3fetches.
LegacyPowerShellextractfailedbeforeoutput, supportedrerunpassed; genericEP1graph
helperdanglingendpointrejected, NOTusedascompleteproof. Noagents/game/save/fact/
launch/install/whitelist/pinnedsourcechanges.16rowsfollowup; othersNOTcertified.

Latest2026-10-21 CONTINUED WHITELIST REVIEW / KERRY HOUSE POLICY ONLY:
USER Kerry house is sole home/access NOTremoved in futurehousingphase. Preserve
existingaccess, no removal/repurchase; NOTKerryquest/romance/spawn permission.
Otherhomes loss/repurchase/Toweroutcomes unchanged; H10 25000, othersnormalprice.
ROADMAP andalpha_playtest_tasks updated; housingimplementationstillfuture.
17rowsrevisited:13conditional+3profileholds+FamilyHeirloom. Recommend6morebroad
sidecandidates: TheseBoots/SmallMan/Sinnerman/ThereIsALight/TheyWontGo/ThisCorrosion.
Combined21proposals=8gigs13sides;7conditionalremain. NO R6/runtimeadmission/install.
Dan/mq023Johnny/q000Kirk missingrefs resolvedofficially; noexcludedcast inthose.
SQ023Judyhits3workspotrefs NOTactor. ThisCorrosionnative root/4:19inventoryOR
Haunted_Gun/Deck exactly1 ->38Succeeded; equipmentchecksdownstream, notcompletion
prereq. Onlyearnedcomponent/recipe, noCantoequip/profilebypass/rewardduplication.
PersonalLinkallowed: KillingName stillactualrouter/profilehold, notblanketdeckban.
MQ058directlyreferencedscene_test exists; testnameNOTcutproof. Nitrointerface,
FreedomYorinobutimeline, SweetDreamsinventory, DelamainToweridentity and3EP1
followupowner/devicegates stillpending. Noexcludedprerequisitereplayforunlock.
37officialextracts incl2historicalStoutversions NOTindependentseeds;185scoped
quest/sceneresources allindexedrefsresolved, NOTcompleteworld/device/liveproof.
Evidence research/omitted_jobs_audit/review_02; docs/whitelist_review_followup_
20261021.md. 420source/policy/completionpathchecksPASS, NOTgameplay; initial
roadmapwordingassertionfailure retained andcorrected. Search20slots4streams/
3fetchedexcerpts; nativefilesprimarytechnical.
Noagents/game/save/fact/launch/install/pinnedsourcechanges. R5Heroes/S27runtime
enforcement andgeneralunfinishedrestart STILLpending. RecoveryS27firstunchanged.

Latest2026-10-21 NON-WHITELIST SCREEN ONLY, NO ADMISSION/INSTALL:
USER asks screen omitted content for possible additions. 415nativejournalroots,
129R5matches,98omitted candidate/reward/category records screened. 15recommended
candidate additions=8gigs+7sidejobs;13conditional;41remainexcluded/outcomeholds;
others profile/timeline/category/unproven. NO R6 or whitelist/runtimechanges.
Recommendgigs Psychofan/GoingUpOrDown/GustavoOrta/Ladrillo/RaceToTop/Scrolls/
FamilyHeirloom/GreedNeverPays. Sides Raymond/SpaceOddity/Ezekiel/Highwayman/
KoldMirage/ImInLoveWithMyCar/EveryBreath. NOTallbranches/profile/restartcertified.
Error404fixedHoltPeralezcampaign NOTadmitted. Zenchain dying2souls+Mistyfollowup
excluded; notclaimingMistyinall4. PsychofanKerryphotos/items NOTactor. Nitro
nativeandroidreplacer needsprofileaudit; ThisCorrosioncraft!=equip,conditional.
EarnedHeroes/Kerryprerequisites mayremain, NEVERreplayexcludedjobtounlockanother.
51/98seeded;396finalscopedresources;422officialextractsincludingoldversions,
final03excludesversionsasindependentseeds. FamilyHeirloomDanreferenceunresolved
locally, NOTprovenabsentgame. Fullrowreasons/limits research/omitted_jobs_audit/
assessment_01.json,docs/whitelist_omissions_audit_20261021.md. Search70slots/
66uniqueURLs5workstreams; hostilefetchedpageignored. Noagents/game/save/fact/
launch/install/pinnedsourcechanges. R5enforcementHeroesS27stillpending; general
unfinishedrestartstillpending. ExistingrecoveryS27firstunchanged.

Latest2026-10-21 MISTY EXCLUSION / WHITELIST R5 AUDIT ONLY:
USER Misty shouldbeexcluded afterTower; same wholejob optional/live scene/call/
message rule asPanam/Judy/Kerry, BOTHtimevariants. KeependingMisty scene and
acceptedZetatech/Viktorworld; noMistyrespawn/Esotericashopreopen. Historical
mentions/archival/prerequisite-only NOTparticipation. Newresearchwhitelist
research/gig_restoration/lore_whitelists_v5_misty.json supersedes R4selection;
R4pinnedbyteskept. Heroes removedbroad(72gigs57side129total); strict34+30unchanged.
SupersedespriorCoyoteHeroesrecommendation: package-onlyisNOTwholejobexception.
Screenall130R4rows/961nativequest-phase-scenes; nootherconfirmedMistyconflict.
PaidInFull root/21debtroute noMisty; sharedmq033tarotrepairdonor isfalsepositive.
Viktorstock+S25readback stillcontains present-tenseMisty-helping line: service
dialoguelorereviewpending, NOTPaidexclusion/liveplayproof. Heroes3actualscenes
castMisty. FoolonHill alreadyexcluded, nowadditionalMistyreason. RaymondNOTadded.
12additionalofficialresourcesextracted; Cuckoo'sNestmissingconnectedscene and
Claireexternalhelper absentbyname/FNV57archives. Claireembeddedhelper already
S27audited; Cuckoo gap remainsUNKNOWNnotMistyproof. Notfullcastcertification.
Evidence research/activity_cast_policy_r5/assessment_01.json+audit_03.json.
IMPORTANT installedS27Heroespackage admission STILLenabled; R5researchfile
isNOTruntimeenforcement. NextseparatepatchdenyNEW Heroesadmission, safelyhandle
alreadyIssuedowners withoutreset, preservecompleted/rewards/Claire/sharedphone.
DoNOTremovewholeS27archive ormodifypinnedcode. NOgame/save/factwrites/install/
launch/agents. ExistingrecoveryS27firstunchanged. Generalunfinishedrestart still
pending; thisauditdoesnotimplementit.

Latest2026-10-21T18:58Z EL COYOTE SIDE-JOB AUDIT ONLY; NO INSTALL:
USER asks audit after conditional ElCoyote restoration request. MQ040 Raymond
Chandler Evening absent BOTH R4 variants; no explicit named rejection found.
Conditional addition recommended: Pepe/Cynthia plot, supporting Johnny; no
excluded cast found in8linked quest/scene resources+6scoped phone resources.
Native parent Heroes done>=1 THEN12gamehours; preserve both. JV1 recognizes
spawnDespawn Character.Silverhand but independent Johnny cigarette/lighter
performer769/actor3 NOTcovered: source-backed presentation risk, NOTlivebugproof.
Pepe B0 and Mama sharedservices need safe release/reacquire, native contacts/
Pepe+Cynthia phone controllers/cleanup/rewards. Historical mq040_active1/done0
and Pepe default_off do NOTprove current ownerliveness. No genericrestart.
Heroes remains broad-ignoregap whitelistONLY;9native scenes noJohnny/excluded
participant. Panam string is reusedanimation, NOTactor. S27package already
installed; funeral/sharedMama/Misty/Viktor/Padre/Pepe ownership stillpending.
RecordedHeroesSucceeded preserved. 41officialresourcesextracted, closures8/14,
126structural/castchecksPASS (notgameplay),96sourcepins. InitialwrongJohnny
record-fieldcheck retained; finalverify02 followsselectedspawnplan correctly.
Evidence research/coyote_sidejobs_audit/assessment_01.json + verification_02.json.
NOwhitelist/game/save/fact/pinnedcodechanges. No agents/launch. S27recoveryfirst
unchanged. Futureimplementation needs explicitwhitelistaddition andperjob
fresh/restartadmission; latestunfinishedrestarttarget remainsunimplemented.

Latest2026-10-21T15:56Z S27 NEW NATIVE BEGINNINGS INSTALLED; LIVE PENDING:
USER Dogtown functionalpass recorded; DT1 unchanged. USER more sidejobs+parallel.
New Claire original5root storyrace family and Heroes PACKAGE outcome only.
Completed/Active/Failed/progressed protected; allfresh nativeguards retained.
Latest target unfinishedrestart remains NOTimplemented, not revoked. Sacrum
parallel encounter persistence and oldS2ownerretirement lack safe resetproof.
Original SQ024 phase has connected embedded vehiclehelper root/53/55 (20nodes,
28edges); retained, no missingresource substitution. Nativecontact/prereqs and
B0Claire/R1 sequencing retained. Heroes originalq005outcome/package/key/bike/
reward/Mama service; NO funeral/sharedNPC branch. Native Mama+Claire phones,
issued-gated cleanup appends to CURRENT S24cleanup, no customcounterrepair.
JohnnyJV1 unchanged. ActualInactive+freshfacts/journals+stableCommon/Safe; only
ownedPermit runtimewrites, no genericreset/saveedit/payout/restart. Quietruntime.
Latest Auto4/Manual23 metadata and priorlivecapture show bothfamiliescompleted:
protectedcontrols, NOTnewentryfixtures. No new entries expected there.
3fileADDS0replace,6modresources5boots,1modcleanupoverride0officialoverrides.
373nativechecks19158policycases,scopedCLI/fullSCCEquipmentEx14arraysPASS.43official
byteexact+2journalvariants613metadata paths,85archives61ALLXL,6packedreadbacks,
157sourcepins44freshrawdecodes. StrictIDnormalization onlyresolved/numeric
TweakDBID; independentbitwiseCRC+typedcomparison44reads/1284IDs/21negativePASS.
IndependentClaire228/Heroes105/support30+1320cases/deploy95checksPASS.
89deploymentcases104checksUNSANDBOXEDPASS0skip incljunction/interruptedinstall.
Finalprealpha/sidejobs_s27/build/s27_03/build.json SHA
BD3A829AFDCED97D9986C39D5673A67DA1F5D6774724DA1C7C1575FC33A66A6A;
archiveFC33D4CBFDA8AC881AEA80D0D1CBAE0E0398F42E93BC9D00F50CD73BBCA16C6F.
ComponentsClaire03/Heroes03/support03/runtime04; contractsClaire03/Heroes05.
Finalsources/builds/tests/compile/audit/deployer/receiptsNOWPINNED; successors
forcodechanges. Earlierfailures/supersededbuilds retained, no livewritesbefore03.
UNSANDBOXEDclosedValidate/Install/actual3hashes/ValidateRollbackPASS;709protected
unchangedincl215savefiles5cachefiles,17workingfilesverified. No launch.
RecoveryFIRSTprealpha/sidejobs_s27/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s27_01,THENDT1/S26capture/S25/older. FileundoNOTsaveundo.
Evidence research/sidejobs_s27/assessment_01.json; docs/sidejobs_s23_playtest.md.
NEXTcoldlaunchsameworkingpostTowerbranch,newmanualtestsave,menusclosed20s:
regressiononly. Freshroutesneedgenuinelyunstartedbranch; noforcedfacts, noending
replayforcurrentregression. Manual PTFR.SideJobsS27.SideJobsS27 Status()/Inspect
07_nc_underground/sq018_jackie. IssuedNOTliveproof. Livecalls/races/package/
rewards/Johnny/reload/freshendingpending. CassiusS26 unresolved,separate.

Latest2026-10-21 USER DOGTOWN PASS / S27 SIDE-JOB EXPANSION STARTED:
USER says "downtown stuff has been restored" in DT1 context; record functional
Dogtown USER pass, not inferred all-lane/deepdistrict/reload proof. Separate
research/dogtown_dt1/live_result_20261021.json; pinned DT1 unchanged.
USER requests more sidejobs and explicitly permits multiagent. S27 new paths:
Heroes family, Claire story-family dependency, first bounded unfinished restart.
Latest target remains completed preserve; unfinished restart beginning ONCE;
neverstarted original beginning. Do not claim S25 already implements restart.
Prior restored owners, rewards, Tower/Johnny/restrictions stay protected until
an audited targeted migration exists. No blind wholequest/prefix reset.
S26 capture has no report in installed helper at initial check; no fabricated
live journal/owner observations. Gameclosed question pending; no install yet.
Recovery remains DT1 first, then S26 capture/S25/older.

Latest2026-10-18T02:43Z (17Octlocal) DT1 DOGTOWN CHECKPOINT INSTALLED; LIVE PENDING:
USER gameclosed+parallelapproved; Barghest shooting no wanted, courier vehicle
blocked at militarized gate. Stock EP1 openworld phase13 owns gate; Tower cuts
that owner. Its root/105 native security/29guard combat branch raises Heat_3
when wanted<3. New single owned boot DIRECTLY references original controller,
not copied/replaced gate logic. Native vehicle/pedestrian lanes, scans, combat
lockdown/reopening, guards/security retained; genericDriving admits courier cars.
2fileADDS archive+XL,0replace/officialoverride/REDS/CET. GenuineTower/PA2/profile,
EP1kill,earnedq302,unblockedgate,no wanted/combat,offsite guards; Issued before
dispatch. Original content-unfreezing trigger retained: dispatch offsite is NOT
guaranteed execution timing. Only new writes ownReady/Issued, no prevention or
nativequest reset/courierabort/saveedit. BroaderDogtownwanted NOTproven repaired;
no source-backed global blocker found. Existing19vendors/services unchanged.
Potentialterminal/summon/ambient utilities audited, NOTblindlyrestarted.
Finalprealpha/dogtown_dt1/build/dt1_03/build.json SHA
DCBADE10445AA213BC2E7422CFB60A001D73FD9C4521C6A1B22C302332B8708E;
archiveB04F110320C566652D9DE5B3E4ED85279F7AF8576496F48897887DF6800D07EF.
Componentgate06;64aggregatechecks55admissioncases;16graphs699nodes;4official
byteexact,84archives60ALLxlpins,1packedreadback/CRC46314;61gate+58deployreview
checksPASS.35deploycases46checksUNSANDBOXEDPASS incljunction. Earliergate/audit
failed/supersededbuilds retained; no live writes until final03. FinalDT1source/
build/test/auditor/deployer/receiptsNOWPINNED; successorpaths forcodechanges.
UNSANDBOXEDclosedValidate/Install/actual2hashes/ValidateRollbackPASS;707protected
unchangedincl215savefiles5cache/settings;10workingfilesverified. No launch.
RecoveryFIRSTprealpha/dogtown_dt1/deploy.ps1 ValidateRollback/Rollback with
recovery/dogtown_dt1_01,THENS26capture/S25/older. Fileundo NOTsaveundo.
NEXTsameworkingpostTowerbranch,newmanualtestsave,insideDogtownAWAYcheckpoint,
no combat/wanted,menusclosedbriefly; normal lane+scan/courier crossing, separate
guardcombat/lockdown/reopen, deeperDogtownwanted, coldreload. Noendingreplay.
Read-only PTFRDT1_GateReady/Issued; Issued NOTliveproof. Evidence
research/dogtown_dt1/assessment_01.json; docs/alpha_playtest_tasks.md DT1section.
S26Cassius/sidejobrestart remains separate PENDING; all previous gameplay kept.

Latest2026-10-18T02:01Z (17Octlocal) S26 DIAGNOSTIC INSTALLED; REPAIR PENDING:
USER's new3categories below remain targetpolicy; NO restart implementation yet.
Cassius shopOPENS. Stock TheGig completion accepts possession ofYakuzaTattoo OR
AdvancedYakuzaTattoo, NOT installation; nativeCassius wareAdvancedYakuzaTattoo
quantity1/free, onlygenerationprereq sq_q001_add_reward>0 already1 in frozen save.
R1inventory-onlypurchase path exists; actualstock/UI failure unresolved. No
speculative itemgrant/restock/nerfbypass/NPCduplicate or questreset performed.
New2fileADD CET PTFR_SideJobsCaptureS26 init.lua/data.json ONLY. ManualArmCassius
registers3quietobservers onnormalVendor/RipperDoc events, reads existingstock/UI
fields orUnknown; NOlazyGetStock/GetVendorObject/GetBuyingPrice. No callbacks
registeredonload. Capture autoStops, reads58roots/740journal/2936factrows plus
ownerfacts and2variant-safe inventoryqueries; two samples/entity.hash stability.
Ownerfacts NOTnativegraphliveness; currentitems NOTpayoutledger. No resetAPI.
37capture+30probeLuaJITcases,7serviceinventorytests,67independentreviewchecks,
20deploymentfixturesUNSANDBOXED PASS. All58serviceaudit rows/332sourcepins;
existingWilson/Viktor/Fred/Zane/Nix/Bill integrations preserved, notduplicated.
Heroes/Claire gaps remain. Candidate nextboundedrestart Sacrum: distinguish
unissued fromsavedS2owner, auditlocalworld/loot reset and targetedretirement
acknowledgement BEFORE replay. CapturedoesNOTsolve engineownerretirement.
Finalprealpha/sidejobs_s26/restart/build/capture_04/build.json SHA
07D6D4494D31633FB9A870C2449B8CC3760445C7F723EB0F5166D83206A06F6A.
init.lua SHA74D08E42E1D8F8B1932A2E71321D00E8C1AC13101C7BEF2BA43AB3F5F6C23BBF;
data.json SHAFCABF6AC14AB00D08739C8411A0A32E8D523DB8A71EC4EC3AB87C3DE5857E1A3.
Sources/build/test/probe/deployer/receipts NOWPINNED; use successor paths for
changes. Superseded01..03 retained;04 fixesnativeEntityIDuserdata stability.
ActualUNSANDBOXED closedValidate/Install/ValidateRollbackPASS;703protected
unchangedincl215savefiles+5cache/settings;8workingS25/S23/S22/S2filesverified.
NO gameplayfile replacement, launch, saveedit, factwrite or reset. RecoveryFIRST
prealpha/sidejobs_s26/restart/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s26_capture_01 (moves2files,keepsreports), THENS25/older.
NEXTlaunchSAMEworkingpostTowerbranch, noendingreplay. BeforeCassiusshop:
print(GetMod("PTFR_SideJobsCaptureS26").ArmCassius())
CloseCET, normalshop->Hands->tryrewardifvisible->closeshop, then
print(GetMod("PTFR_SideJobsCaptureS26").Capture())
Readnewcapture_s26_*.json ininstalledhelperfolder; Unknowns mustremainUnknown.
Evidence research/sidejobs_s26/assessment_01.json andcomponent assessments.

Latest2026-10-17 S26 POLICY CHANGE / INVESTIGATION IN PROGRESS, NOT INSTALLED:
USER explicitly supersedesInactive-only: whitelisted completed sidejobs remain
completed; started-but-unfinished restartfrombeginning; neverstarted startfrom
beginning. Asked about currentrestoredjobs, USER reiteratedthese3categories.
Restart is a one-time restoration/migration, NOTrestarton everyload/death.
Need retireexistingowners and audit exactnativefact/journal/item/reward effects;
doNOTzero wholeprefixes/globalphonefacts or duplicate reward/item payouts.
Newrequest also requiresquest-relatedworldNPCinteraction/service dependencies,
notjustNPCspawn/marker. USERapprovedparallelsubagents+gameclosedthisturn.
USERconfirmsTheGig/Cassius objective, shopOPENS but free rewardmissing/blocked.
Ozobseparate USERcompleted; latestsavefactmq035_done1+S23Finished1 confirms
nativecompletionflag, NOTallreward/reloadproof. Cassiuscontrolleralreadyenabled
andran; blanketNPCrespawn isNOTsupportedfix. SnapshotAuto17+2logs byteexact
research/sidejobs_s26/live_20261017_01; saveSHA
235C0C34F25343A4D0592B1D22EB385CB486500100DC79436A84749D2A63BEFF.
Metadata tracks sq_q001_wakako/wakako/02_reward; factreportresearch/
gig_restoration/sidejobs_s26_auto17_20261017_01.json: CassiusReady/Enabled/
OwnerActive1,Entries/Exits2,SceneRequests1,default_on/met1;Wakakocash1,
sq_q001_active/add_reward1,doneABSENTnotlive0. Nojournaldecoderclaim.
S25installed/pinnedunchanged; recoverySTILLS25first. S26agentworkseparated into
cassius/restart/services; maincoordinatescapture/integration. No runtimepatch,
restart, nativefactwrite, saveedit or launch performed fornewpolicy yet.

Latest2026-10-16T15:41Z S25 INACTIVE-ONLY EXPANSION INSTALLED; LIVE PENDING:
USER explicitly approved parallel subagents/gameclosed. Latest rule: ALL NEW
activations require actual Inactive root; alreadyIssued restorations/progress
remain intact. S22/S23 unissued runtime+native preflights narrowed, S1 saved
request bypass closed. Failed/Active/Succeeded/Unknown not newly admitted.
Inactive alone NOTfreshness/reset authority; native perjob progress/item/child
guards retained. Five new freshowners cover19R4roots: TheGun/PaidInFull/boxing
(6)/HumanNature+TuneUp+Epistrophy(10)/Prophet. Overall52/58boundedroutes, NOTall
stages/livepass. Heroes+5Clairestoryroots pending; repeatableR1 untouched.
Claire connected native vehicle-hacking phase absent byname/FNV in official
archives, NOTcut/replaced. Heroes sharedservice ownership unresolved. Aaron
partialSMS stillPARKED. Current frozen capture all5progressed/completed =>
regressioncontrols, NOT19newentries. No forcedfreshfixture or save/factreset.
Original native calls/gameplay/rewards/prerequisites retained; Gun uses bounded
order/shop/reward slice, OMITSoldfirstmeetprop/attention staging toretainB0actor.
Paid restores2nativeViktordebtchoices guarded bynewowner. Fred existingowner
selectsnativeintro forfreshboxing; no duplicateactor. Delamain nativecontact51,
existingcleanup retained, excludedsequel omittedafteroriginalreturn/reward.
Prophet fresh/resume mutuallyexclusive; passive started/active0..1 allowedonly
withallactualsermon/donation/progressfresh. JohnnyJV1voice/bodyhidden unchanged.
26modresources/5boots/20modoverrides(17policy+Fred/Wilson/Viktor);0official.
3fileADDS+2backedupREDSreplacements(S22/S23). ExistingS24cleanup unchanged.
4194native/structurechecks36826policycasesPASS; scopeddependencyCLI+FULLgameSCC
includingEquipmentExPASS; compiledS25/S22/S23arrays35/24/168+S2diagnostics kept.
53officialbyteexact+2journalvariants metadata750paths;83archives59ALL*.xl,
26packedreads5CRCIDsPASS.271sourcepins60componentJSONwitnesses25rawDatareads
(17policy+8services),independentreviewsPASS.107deploycases130checksUNSANDBOXED
PASS0skip. EarlierEquipmentExCLIrejection, sandboxjunctiondenial, superseded
01..03proofbindingbuilds retained;04allproofsbindfinalmanifest. No gameplay
resourcechangesfrom03; archivepackmetadata differs. No oldinstalledmainreruns.
Buildprealpha/sidejobs_s25/build/s25_04 SHA
5884AEB720E9AF6272A277F3750497B3C46021C165C2C3D10B1B56711F3AF6E6;
archiveDDCDA37330E056342D6F0C4C4245596323809CAD4DA10ED73258113875149C33.
Components policy01/services06/families03/prophet01/runtime02. AllS25source/
build/test/compiler/audit/deploy/receiptsNOWPINNED; successors forcodechanges.
UNSANDBOXEDclosedValidate/Install/5actualhashes/ValidateRollbackPASS;698protected
unchangedincl215savefiles5caches/settings;8workingfilesverified. No launch.
RecoveryFIRSTprealpha/sidejobs_s25/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s25_01,THENS24/S23restoration/capture/S221/S22b/older. Fileundo
NOTsaveundo. Evidence research/sidejobs_s25/assessment_01.json; docsS23rollout/
playtestS25section. ColdlaunchSAMEworkingpostTowerbranch,newmanualtestsave,
menusclosed20s forregression. Freshlive tests needgenuinelyunstartedbranch;
noendingreplayneededforcurrentregression. ManualPTFR.SideJobsS25.SideJobsS25
Status()/Inspect(id),quietruntime. Livefresh/rewards/Johnny/reload/endingpending.

Latest2026-10-16T14:33Z S24 UNSTARTED SIDE-JOB BATCH INSTALLED; LIVE PENDING:
USER approved parallel subagents and gameclosed. New7freshroutes ONLY:
HappyTogether/Violence/Spellbound/TheGig/ShotByBothSides/NoEasyWayOut/MovingHeat.
All existing S23/S22/S2/S1 owners/progress and JohnnyJV1 kept unchanged. Aaron
partial-SMS repair remains PARKED. No blanket58start/historycertificate/reset.
Actual Inactive roots+objectives/messages+perjobzero/passivefacts+oldunused+
stableCommon/Safe admit fresh only. Unknown defers. Original perjobparentwaits,
gameplay/scenes/calls/rewards retained; scoped native AddContact payloads.
Current frozen capture ALL7 already progressed/completed => protected controls,
NOT7newjournalentries on that branch. No factreset or fake fresh fixture.
NewLizzy/R3NO native phone controllers + gated native cleanup append to CURRENT
S23 cleanup, nohistoricalstart/end/done equality, no counterrepair. R3NO audio
busyflags included. Native Nix default_on servicehandoff retained. Fresh/old
resume exclusivity audited across native MQ306/Q304 phase+scene failure paths.
10modresources/9boots/7adapters;3fileADDS0replace, onlymodcleanup resourceoverride;
NOofficialoverride. 10143aggregate native/structurechecks+14227policycasesPASS.
FullCLI/SCCEquipmentEx+49compiledarrays/bodyreadbackPASS.100officialbyteexact
resources + metadataONLY basecookedjournal two exact archive-specific variants;
372usedpaths/classes, independent553variantchecksPASS. Journals NOTshipped;
wholejournalbyteequivalence NOTclaimed.82archives+58ALL*.xl pins,10packedreads,
9CRCIDsPASS. All87deployfixtures/102checksUNSANDBOXEDPASS,0skips/gamewrites.
Compilerproofbindscomplete.redsidentityset/includeconfig+roots/CLI+SCC binaries.
Final build prealpha/sidejobs_s24/build/s24_02 SHA
4753F0B47749FC061F437D95654EA9282EB3C14EEBD38908CB75084C3B0BD116;
archiveSHA15A7CDE8A4E7780E41B4AF8A1979F1154EECB95B9CCF380A0777342DBD750417.
Components base_04/ep1_02/services_02/support_02/runtime_02. Earlier superseded
builds and initial journalvariant audit failure preserved. All finalS24sources,
builds/tests/compiler/auditor/deployer/receiptsNOWPINNED; noinstalledmainreruns
or edits. Furtherchanges need successorpaths. Docs/evidence may be extended.
UNSANDBOXEDclosedValidate/Install/actual3hashes/ValidateRollbackPASS:697protected
unchangedincl215saves+5caches/settings,7workingS23/S22filesverified. No launch.
RecoveryFIRSTprealpha/sidejobs_s24/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s24_01,THENS23restoration/capture/S221/S22b/older. Fileundo
isNOTsaveundo. Evidence research/sidejobs_s24/assessment_01.json; playtest
docs/sidejobs_s23_playtest.md S24section. ColdlaunchsameworkingpostTowerbranch
forregressiononly,newmanualsave,menusclosed20s. Freshgameplay requiresgenuinely
unstarted separatebranch; noendingreplayneeded forcurrentregression. Manual
PTFR.SideJobsS24.SideJobsS24 Status()/Inspect(id), runtimequiet. Livecalls/SMS/
NPCs/rewards/Johnny/reload/freshendingpending. TheGun/PaidInFull/Heroesfresh
deferredserviceownership; ProphetfreshdefersexistingS23overlap. Notallfreshjobs.

Latest2026-10-16 USER PRIORITY CHANGE — UNSTARTED SIDE JOBS FIRST:
New work targets R4-whitelisted unstarted side jobs. KEEP all previous restored
content, owners and progress, including S23/S22 partial-progress routes. Do not
disable/rollback/restart them. Further partial recovery, including missing Aaron
SMS, is PARKED, not fixed. Johnny voice/body-hidden policy unchanged.
Inactive alone is NOT unstarted: captured Skippy/Prophet have progress; seven
Inactive boxing/Delamain children are under active families. Per-job native
objectives/facts/items/rewards/owner guards determine fresh admission. Passive
initialization is not automatically player-started; absent saved facts not live0.
Reuse installed fresh paths first; audit missing fresh-family entries separately
from snapshot-specific resume coverage and completed-root protection. Completed
jobs on current branch stay completed; do not reset to create fresh test fixtures.
ROADMAP/docs/sidejobs_s23_playtest.md updated. Scope/audit only, NO new runtime
patch/install. S23 pinned sources/builds/recovery below remain authoritative.
Read-only ManualSave23+7logs copied under research/sidejobs_s23/
aaron_live_20261016/snapshot_01, sources unchanged; S23 installed3hashes match.
Saved Skippy ModeTalkConfirmed1/RESUME Permit1/Issued1; no repeat opt-in needed,
not proof of later conversation. Aaron root owner Issued1/Entered1. Stock q307
pickup removes contacts except Viktor/Reed; S23 Aaron reply slice omitted stock
contact-add. Strong source-backed missing-contact hypothesis, NOT live contact
API proof (opaque journal offset4 not validated). Keep this lead for later.

Latest2026-10-16T02:10Z S23 FULL-WHITELIST FAMILY EXPANSION INSTALLED; LIVE PENDING:
USER explicitly approved parallel subagents, ran Capture(), confirmed gameclosed.
Stable capture research/sidejobs_s23/live_20261016_01/capture.json SHA
47084A3833CFE507D184A19CDD1276215A15F917F6B97AA4130E6A6E6919748A:
58 R4 roots =33Inactive/6Active/18Succeeded/1Failed; repeated samples settled,
matched, unknown0. No generic restart/history certificate. Current whitelist+
Failed OR Inactive; future preTower Inactive certification remains separate.
S23 supplies24 bounded routes/25 remaining journalroots;9Inactive roots use
existing S1/S2/boxing/Delamain families. Active6/completed18 remainprotected.
34mod-ownedresources/29boots,3fileADDS0replace. Onlymodresourceoverrides are
currentS221cleanup and B0Wilsonowner; noofficialoverride. Preservealloldinstalls.
Native per-job gameplay/scenes/calls/rewards retained; Johnny JV1 unchanged.
NoEasyWayOut resumes exact AaronSMS/intimidate outcome,3journalreactivations;
clinic/choices/priorrewards retained. Extra livephonejournalguards mustmatch,
unknown defers. OtherMQ306seamsnotimplemented. S221Epistrophyuserpasspreserved.
New native Frank/MrStud/Ozob/Sandra/Wilson controllers feedexistingglobalphone;
busyflags checked, NOT historicalstart/end equality. Cleanup appendsafterS221.
Zane/Wilson/Bill B0ownership coordinated; Steven defers toexistingU9SpyJungle.
OnlyPain bridge calls EXISTING publicRestoreFresh afterstableCommon/Safe guards;
original preflight+one-shot state authoritative, no duplicateowner/certification.
USER confirms Skippy50-enemy conversation DIDoccur. Newseparate RESUME owner
requires PTFRS23_MQ007_ModeTalkConfirmed=1 explicitCEToptin onmatchingtestsave;
default0 protects ambiguousnativehistory. Fresh/resume nativeguards disjoint,
freshIssued0 required; exact11/51/95 counters andcapturedjournal/modefacts.
No pickup/modeconversationreplay orcounter/item/mode reset. Originalreturnnode5,
ambient3/11/12,cleanup7 unchanged. Native2game-daydelay RESTARTS, notoldremaining
timerreconstruction. No immediatejournalpromise; Inspect byPTFRS23_MQ007_RESUME.
1210aggregate native/structurechecks+9501policycases; preservedbaseA351/1841proof.
FullCLI/SCCEquipmentEx+compiled168arrays/bodyreadbackPASS.112officialbytechecks,
81installedarchives+57ALL*.xl identity/hashpins,34packedreadbacks,29CRCIDsPASS.
74deploymentcases89checksPASS no skips; initialsandboxjunctiondenialretained,
fullUNSANDBOXEDworkspace rerunPASS. Reviewcaught staleXLproofgap; finalbuilder/
audit/deployer bindcompleteXLsetbeforeinstall. Initialcompileverifierapostrophe
escape mismatch corrected/rerun; earlierfailed/supersededbuilds retained.
UNSANDBOXEDclosed-gameValidate/Install/actual3hashes/ValidateRollbackPASS:
694protectedunchanged incl215savefiles+5caches/settings,4workingS22filesverified.
No launch/saveedit/settings/cachewrite. Runtimequiet; manualStatus/Inspect only.
Buildprealpha/sidejobs_s23/build/s23_02 SHA
84A8FB28CCAD8E209D6D3C32899E91116ECD2137B099E0A1D1A2AB8DBBFBB5DE.
ArchiveSHA A24A4BEF165833F38E04F7BF20698E45F9E516C150358518C981C768DFDBD1CB.
Finalcomponents base_a_v2/resume_02,base_b/base_b_02,ep1/ep1_07,support/support_02,
runtime/runtime_04. AllS23source/build/tests/compiler/audit/deploy/receiptsNOWPINNED;
no installed-main reruns or edits. Use new successorpaths forfurtherchanges.
RecoveryFIRSTprealpha/sidejobs_s23/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s23_01,THENS23capture/S221/S22b/older. Fileundo isNOTsaveundo.
NEXTcoldlaunchSAMEworkingpostTowercapturedbranch,newmanualtestsave,menusclosed
20s. Nativeprerequisites/timers meanNOT58immediateentries. Skippyownedoptin cmd
in docs/sidejobs_s23_rollout.md; deferredtestlist docs/sidejobs_s23_playtest.md.
Liveinteractions/rewards/Johnnyvisibility/reload/alternateprogress/freshending
remainpending. FamilycoverageNOTallpartialseams/livepass. Noendingreplayneeded.

Latest2026-10-16T00:51Z S23 FULL-WHITELIST CAPTURE INSTALLED; RESTORATION EXPANSION PENDING:
USER "quest seems to be working" afterS221: initialEpistrophyfunctionalUSERpass
recordedresearch/sidejobs_s221/live_result_20261015.json; NOTall4cars/finalreward/
reload/freshendingproof. USERthenrequestsallquests: currenttargetALL58R4sidejobs,
notmainstory/excludedquests. Sevenexistingtop-leveladapters+theirchildbranches
areNOTall58/allstages. ExistingS221/S22/S2/S1.1gameplayfilesunchanged.
Newcoverageauditresearch/sidejobs_s23/coverage_01.json; parent/entryreviewonly,
NOTadmission. ReadAutoSave0factswithoutwrites:mq306clinic/ripper/Angieprogress
positive, enemy_spawn_counter20. Restartwoulddiscardmaterialprogress. Missing
serializedfactsNOTlivezero; nojournalbyteinterpretation. Needliveobjectives to
chooseNoEasyWayOutresume; remainingfamiliesstillneednativeentry/service audits.
S23captureONLY2additionsCET PTFR_SideJobsCaptureS23/init.lua+data.json; manual
Capture() readsall58roots/740journalrows/2932factrows,2samples+settlementchecks,
reportsMissing/Unknownexplicitly,uniqueJSONreports. Nocallback/poll/spam/native
writes/save/autoload. All58detailcataloguesnowpresent,includingmq306,mq015,mq026;
notcompleteexecution/item/rewardhistory. No newquestownerorrestorationinstalled.
19LuaJITcases/19deploymentfixturesPASS;initialPowerShellarrayprecedencefixture
bugfixedBEFOREinstall, sandboxjunctiondenialpreserved,fullUNSANDBOXEDrerunPASS.
GameclosedUNSANDBOXEDValidate/Install/ValidateRollbackPASS;689protectedunchanged,
215saves+5caches/settings;4workingS22fileshashverified. No launch.
Buildprealpha/sidejobs_s23/capture/build/capture_02 SHA
DB5C2529D306B312047757A8A06D94607525710556C630B1A9BB17B34051F524.
Capturebuilder/Lua/tests/deployer/build/receiptsNOWPINNED; no edits/mainreruns.
S23audit.py/extract_missing.ps1arepreparationtools; extractednative01pinnedbycapture.
RecoveryFIRSTprealpha/sidejobs_s23/capture/deploy.ps1 ValidateRollback/Rollback
withrecovery/sidejobs_s23_capture_01 (moves2files,keepsreports),THENS221/S22b/older.
NEXTusercoldlaunchSAMEworkingpostTowerbranch; CET
print(GetMod("PTFR_SideJobsCaptureS23").Capture())
thenreadnewcapture_s23_*.jsonintheinstalledhelperfolder. Noendingreplay/factreset.
Readcapture+auditper-familyboundariesbeforeactualfullrollout; no blanket58start.
Optionalparallel-agentquestionunanswered; noagentsusedthisturn. Userprevious
parallelpermissionwasolderbatch; awaitfreshreplyratherthanassumefrompreselection.
See docs/sidejobs_s23_rollout.md. FullwhitelistrestorationNOTcompleted.

Latest2026-10-15T23:43Z S22.1 EPISTROPHY PHONE-GATE PATCH INSTALLED; LIVE PENDING:
USER requested patch after readonly diagnostics: S22progressMatch/safe/permit true,
SupportReady1/SupportIssued0/Issued0/Entered0; all57busy/resetflags0, only main
Delamainstart/end7/2 andsad0/1 blocked. Native sadincoming scene increments
active_count NOTstart_count; nativecontroller hasno history-count conditions.
DoNOTcallmain7/2 provenbenign or zero/repair counters. Stockcleanupunchanged.
One backed-up replacement of000_TowerContinued_SideJobs_S22.archive, noadds,
scripts/XL/injectionIDs/graphconnectionsunchanged. Fourpreflightnodes(1002/1003
in support+owner) remove16history-equalityeach; keep57busyflags+allCommon,
progress/journal/Permit/Issued guards. Sixotherresourcesbyteexact,1145other
payloadnodesunchanged. No nativecounterwrites/ownerrestart/rewardreplay/reset.
Originalnativephonecontroller+cleanup remain; journalactivationstillafteradmission.
3/7 completedcars protected; otherthreeS22jobs USERjournalentrypass ONLY.
5464policycases/4userregressions/57officialbytes/81archiveaudit/8packedreadbacks
PASS;47deploycases65checksPASS. First sandboxfixture run failed atjunction
creationpermission;fullUNSANDBOXEDworkspace rerunpassed,none skipped.
Gameclosed verifiedUNSANDBOXED;Validate/Install/ValidateRollbackPASS;85other
packagefilesverified,688protectedunchanged incl215saves+5caches/settings.
Buildprealpha/sidejobs_s221/build/s221_01 SHA
F154F3C4C1F17F07E24B4BCE66D210079F5370757F91D88B88B8A9ADE2953B76;
installedarchiveSHA D60EBBC7346F4FFFF0C08F301FEA360D59CAB503D84CFF6039E40ACADEB40E78.
S221sources/build/tests/auditor/deployer/receiptsNOWPINNED; no reruns/edits.
RecoveryFIRSTprealpha/sidejobs_s221/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s221_01, THEN S22b recovery/sidejobs_s22_02, S21/S2/older.
DoNOTusealreadyrolledbackrecovery/sidejobs_s22_01. No launch/save/settings/cache
writes. Evidence research/sidejobs_s221/assessment_01.json+live_20261015_01.
NEXTcoldlaunch SAMEpostTowersave usedforscreenshots, onfootmenusclosed10s;
EpistrophyexpectedActive3/7, remainingcar nativecall/interaction. No endingreplay,
forcedfacts/counterbalance/Issuedreset. SameS22Inspectcommand(labelunchanged).
Savedpauseconditionrehydration,actualcalls/cars/finalreward/reloadstillLIVEpending.

Latest2026-10-15T21:10Z S22 HARDENED PROGRESS RESUME INSTALLED; LIVE PENDING:
LatestUSER currentwhitelist+(Failed OR Inactive)postTower; futurewhitelist+
InactivepreTower. Halfwayprogresspreserved; unsupportedstagesNOTsilentlyreset.
Capture58=35Inactive/0Active/18Succeeded/5Failed. Fourboundedresumeadapters:
TheGigafterWakakocash(00/01Succeeded,02pending); Boxingintrocomplete/no-bout;
Epistrophy3/7(sad/mean/suicidalSucceeded); MovingHeatacceptedSMS/firstdoor.
NoEasyWayOutONLYrootcaptured;41journal108factcataloguereadybutnativestageunknown,
NOadapter. NOTall58/otherpartialstates. S2Sacrum/StadiumautomaticcurrentInactive
admissionnowusesCommon; oldfreshness/history/certificate/data/FailedDetailskept.
NewquietruntimeonlyownedPermitwrites,2stableticks,safe/profile/Common+journal
settled; nativepreflight+Issuedbeforeexactjournalwrites+protectedstateack.
No nativeprogressreset/oldrewardreplay/certfabrication/ownerrestart. JohnnyJV1
unchanged. Originalgameplaypayloads/scenes/rewardskeptatboundedauditedseams.
Delamain3doneownersskipped+nativeANDseeded; fourremainingoriginal; returnscanner
rewardkept,excludedsequel134omitted. Nativecontact51(all8identities)once; C1mod
cleanup appends438/302after600/601; no globalU9restart. Root/scanphase/objective
reactivatedexplicitly,5briefingobjectives+3completedrootsSucceededpostchecked.
Hardeningrequires sad_mounted0; only124Out1finalrewardcuts142/114/147watchers.
Firsts22_02brieflyinstalled20:59thenrecoverablyROLLEDBACK21:00beforeagentlaunch;
3addsretainedrecovery/sidejobs_s22_01,oldS21restored. DoNOTrepeatthatrollback.
Oldsourcesrestoredbyteexact/preserved; superseded06uninstalledretained. Successor
toolkitprealpha/sidejobs_s22b,delamain_v2/build/delamain_07,runtime_v2.
Finalbuildprealpha/sidejobs_s22b/build/s22_03 SHA
0BEC19BF535031E465DA85F4864A2D0E4CAE15AB462DA1DFBC9E0AE8C024A08C.
1069payloadchecks/3156policycases/57officialbytes/80archiveaudits/8packedreadbacks/
5CRC IDs/combinedCLI/fullSCCEquipmentEx/189compiledarraysPASS;68deploycases92checks.
UNSANDBOXEDclosedValidate/Install/ValidateRollbackPASS:3adds1backed-upreplacement,
82priorpackagefilesverified,685protectedunchangedincl215savefiles5cache/settings;
old/newinstallationprotectedmaps0differences. No launch/saveedit/settingswrites.
Sources/builds/tests/tools/receiptsNOWPINNED; no mainreruns/edits. RecoveryFIRST
prealpha/sidejobs_s22b/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s22_02,THENS21/S2/R1/P1/D1/N22/N21/C1/N2/N1/FO1/PA6/older.
NEXTcoldlaunchSAMEworkingpostTower58-jobcapture-save,notending/latestslotblindly;
offsiteonfootmenusclosed10s,journalshouldpreserve3/7+acceptedSMS/cashhistory.
ManualPTFR.SideJobsS22.SideJobsS22 Status()/Inspect(id); noforcedfacts/fixture.
IssuedNOTgameplayproof; currentMatchmayfalseAFTERnativeprogress. Prompts/rewards/
reload/Johnny/freshendingpending. Docs/sidejobs_s22_playtest.md; evidence
research/sidejobs_s22/{assessment_01,install_result_20261015}.json.

Latest2026-10-15 S22 CURRENT POLICY CORRECTION / WORK IN PROGRESS:
USER current whitelist + (Failed OR Inactive) POST-Tower; future whitelist +
Inactive PRE-Tower. Halfway-done jobs resume preserved progress, choices and
completed rewards. Do not silently restart unsupported stages or fabricate history.
This supersedes Failed-only entries below. S21 installed unchanged until S22
validated/deployed. Captured S21 report:58 roots,35Inactive/0Active/18Succeeded/
5Failed; TheGig,BeatOnBrat,Epistrophy,MovingHeat,NoEasyWayOut. Actual resume
adapters being prepared in prealpha/sidejobs_s22; NOT all58 implemented.
Live log frozen research/sidejobs_s22/live_20261015_01. No native save writes.

Latest2026-10-15T19:17Z S21 DIAGNOSTIC/AUTH REPAIR INSTALLED; FAILED REPLAY NOT IMPLEMENTED:
USER currentR4whitelist+postTowerFailed, preferpreservedprogresselseboundedrestart;
futurepreendingunstartedcertificationseparate. DoNOTaskrestartchoiceagain.
58roots/38planninggroups audited;3existingfreshadapters,0failedreplayadapters.
S21 ONEbacked-upscriptreplacement,0adds/archives/ownerchanges. ExistingS2native
freshness/history/one-shotguards+oldDataS2suffixunchanged. ManualFailedReport()
andFailedDetails() read58actualnativejournalroots, onlyFailedgetsdetail;55bound
catalogues657journal/2751factrows,3noDetailCoverage. Unknown/unsettledreported,
notinferred. postTowerReady contextONLY,notadmission. No automaticreport/spam.
OptionalEnableFreshFixture("DISPOSABLE_SAVE") onlyfresh2-jobtestauth,NOTcurrent
Failedpolicy. NeverrunitforFailedrestoration. Defaultsfalse; certificatesnotchanged.
2374checks/922cases,combinedCLI/fullSCCinclEquipmentEx+38scopedreadbacks/165detail
arraysPASS;47deploycases64checksPASS. Build02largeFactNamesdecompileinvalid
offset51105rejected;03uses55smallhelpers. Earlierverifierformatfailurespreserved.
GameclosedUNSANDBOXEDValidate/Install/ValidateRollbackPASS;82priorpackagefiles
verified;685protectedunchangedincl215savefiles+5cache/settings. No gamelaunch.
Buildprealpha/sidejobs_s21/build/s21_03 SHA
07BCE846A36A434D667CB46953B0DC51A462F4E22C28D5B8A3291DD5DFF2BFCB;
installedscript68947EA168C7F3A3AD589BB8E568AF6EF4E1B54F62EB8ACE8190E339F8582C1F.
S21source/build/tools/tests/receiptsNOWPINNED; no mainsrerun/overwriting.
RecoveryFIRSTprealpha/sidejobs_s21/deploy.ps1 ValidateRollback/Rollbackwith
recovery/sidejobs_s21_01,THENS2/R1/P1/D1/N22/N21/C1/N2/N1/FO1/PA6/older.
NEXTloadSAMEworkingpostTowerS2testsave(notlatestslotblindly), manualreadonlyCET
print(Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS2.SideJobsS2"):FailedDetails())
theninspectCETlog. Noendingreplay/forcedfacts/fixtureenable/newsave neededforcapture.
This is PARTIALprogress, NOTallfailedrestored. Useactualcapture+sourceaudit to
chooseperquestresume/restart; protectsuccess/siblings/rewards/Johnnyvoicebodyhidden.
Evidence research/sidejobs_s21_failed/install_result_20261015.json,inventory01/02,
resume_evidence_01.json; livecapture/gameplaypending. ExistingS2Freshmonkauthfault
isnotFailedroot; stockTowerfailsActive,notliterallyeveryInactiveunfinishedjob.

Latest2026-10-15 SIDEJOB POLICY CHANGED; S21 PREPARATION ONLY:
USER currentruleR4whitelist+actualpostTowerFailed=>restore; futurewhitelist+
actualpreendingunstarted. USER prefersresumeprogresswherepossible,elserequest
restart. DoNOTreimposepreTowercertificateoncurrentfailedroute; keepfuturehistory
separateandneverfabricate. Success/succeeded-sibling/outofwhitelistprotected.
58titlesONLY3freshadapters(S1OnlyPain,S2Sacrum/Stadium);0failedreplayadapters.
Stockq307pickup62/63/102/128/132 failsActivejournals,notallInactivequests; shared
MQ025/SQ025/SQ024/MQ037 ownersneedgrouping. FullSQ025contains excludedcontent.
Read-onlyinventory01/02+replay_boundaries+policy_20261015 underresearch/
sidejobs_s21_failed. No genericjournalreset/nativefactwipe/wholeparentrestart.
LiveS2reportSacrumReady1Permit0Issued0Freshtrue,certfalse/devfalse=>authblock;
NOTFailedmonkroot. PA1DevelopmentArmedfalsecanmeanPA1certifiedtrue,notonly
missinglate-endingflag. Newprealpha/sidejobs_s21 preparedexplicitfresh-fixture
auth+readonly58Failedreport; NOTfailedrestoration. Build01authonlyworkspace
supersededbyplanned02diagnostics; NOINSTALLYET. PriorS2/pinnedfilesunchanged.
CurrentrecoverySTILLS2first. NeednativeFailed/progressreportbeforeperjobroute.

Latest2026-10-15T18:19Z S2 INSTALLED; LIVE PENDING:
USER gameclosed+install. UNSANDBOXED closedcheck/Validate/Install passed.
3additions0replace (archive/XL/SideJobsS2.reds),80priorpackagefilesverified;
683protectedunchanged incl215savefiles+5caches/settings. Actual3hashes match,
ValidateRollbackPASS. No launch/saveedit/settings/cachewrite. Same s2_02 SHA
6B3FB20725472BA85C6F210B9EDE0B8681509039B09FE5ED12581CEF6959ABE6.
All S2 source/build/tools/tests/receipts NOWPINNED; no oldmainreruns/overwrites.
RecoveryFIRST prealpha/sidejobs_s2/deploy.ps1 ValidateRollback/Rollback with
recovery/sidejobs_s2_01,THENR1/P1/D1/N22/N21/C1/N2/N1/FO1/PA6/older.
Separate research/sidejobs_s2/install_result_20261015.json supersedes earlier
blockedstatus; assessment/build01/fixturefailurehistoricalpreserved. Current
docs updated. NEXTcoldlaunchAutoSave10level48,13:32:21,15Oct2026 (NOTAuto11
Viktorending). Source3filesstillbyteexactbackup;SHA D6C44B57A4E79F54FDE02B7709B4FB9FC3054E2CCF1E8D8322BC2F216E6F3185.
Newmanualtestsave,menusclosed10s; Inspect mq032_sacrum andmq008_party. Stadium
done1/agreed1 muststaycompleted,NOTa missingmarkerbug. Sacrumsampledabsentfacts
NOTlivezero; runtimeentrychecksdecide. Nativeprompt/dialogue/Johnnyvoicebody/
reward/ambient/prevention/reload/freshending pending. No furtherwhitelistrollout.

Latest2026-10-15 S2 BUILT/VALIDATED, NOT INSTALLED; GAME RUNNING:
USER starts sidejobs and explicitly confirms Johnny voice/bodyhidden existing
approach (invisible actor for voice/timing allowed). Firsttwo mq032_sacrum and
mq008_party nativeparents/directstockphases, no owner/scenes/reward rewriting.
New separate S2 capture/certificate at actualpreTowercutoff; missinghistorynever
certified. Existing PA DevelopmentArmed route2 explicitlyuncertified. Native
doubleguard checks route1/2+Permit, Tower/PA2/U9, journals/progresszero before
Issued. Stadium passive active/comm_on0..1 accepted, nativeincrement may1->2;
audited readerszero/positive,cleanup exact0. prevention_system_offmust0. Original
parentgateskept; no fullminorroot/ambientkill-resetroot; S1OnlyPainunchanged.
Build prealpha/sidejobs_s2/build/s2_02 SHA
6B3FB20725472BA85C6F210B9EDE0B8681509039B09FE5ED12581CEF6959ABE6.
3plannedadds0replace:archive+XL+SideJobsS2.reds.20parentpayloads/387negative/
1431policy755cases/25officialbytes/79modarchives/2packedreadbacks PASS.
CombinedCLI/fullSCCEquipmentEx+28scopedcompiledmethod/datachecks PASS.
59deploycases71checksPASS fixture20261015T180408274765Z. Initialhelperimport
fixturefailurepreserved/fixed/fullrerunpass; s2_01supersededpreserved. Newsource/
build/test/evidence now frozen; do not rerunoldinstalledmains or overwrite02.
LiveValidate hit lockedTweakXLlog; UNSANDBOXED GetProcess foundCyberpunkPID6988
running since15Oct13:43:28. SandboxGetProcessfalse-negative! ALWAYSunsandboxed
closed-process/liveinstallerchecks. NOInstallcalled/no game/savechanges/launch.
NEXTuserclosegame, UNSANDBOXED prealpha/sidejobs_s2/deploy.ps1 Validate,Install,
ValidateRollback withbuild/s2_02 andNEW recovery/sidejobs_s2_01. Currentrecovery
STILLR1first(notS2),thenP1/D1/N22/N21/C1/N2/N1/FO1/PA6/older.
AutoSave10level48 13:32:21 15OctpostTower; SHA
D6C44B57A4E79F54FDE02B7709B4FB9FC3054E2CCF1E8D8322BC2F216E6F3185.
3filebyteexactbackup research/sidejobs_s2/fixture_auto10_20261015,originalunchanged.
Stadiumdone1/agreed1=>completedcontrolpreserved; SacrumfactabsentNOTlive0.
Auto11newerViktorendingstage NOTtestfixture. Source/externalauditsandassessment
underresearch/sidejobs_s2; docssidejobs_s2_playtest.md. Actualprompt/voice/body/
reward/ambient/prevention/reload/queuedpermit/freshending pending. Other56R4
candidates notallimplemented (oldOnlyPainalreadyseparate). UserR1passrecorded.

Latest2026-10-15 R1 USER PASS / S2 SIDEJOB WORK STARTED:
USER reports race test passed using Johnny's car; no Johnny appeared. Functional
USER pass only, exact route/all4/payout/voice/repeat/reload not inferred. Separate
evidence research/races_r1/live_result_20261015.json; pinned R1 unchanged.
USER now requests sidejobs, reiterates Johnny voice stays/no visible model.
Audit first candidates mq032_sacrum and mq008_party; old S1 Only Pain preserved.
58 R4 candidates != installed adapters. Production needs actual preTower fresh
history; postTower development incomplete-as-unstarted stays uncertified. New
additive S2 history needed; old R3/U9 definitions and snapshots stay pinned.
S2 not yet installed. Recovery still R1 first. No game launch this turn.

Latest2026-10-15T00:32Z R1 REPEATABLE RACE INTERACTIONS INSTALLED; LIVE PENDING:
USERrequestsrestore raceinteractions; correctedgameclosed. P1userreportscompleted,
functionalPASS recordedresearch/cyberpsycho_p1/live_result_20261014.json; NOTall17/
rewardvariant/reloadproof. PreserveP1 andexplicitdisposablefixture unchanged.
R1native mq056 repeatableracesONLY, noClairesq024storyreplay. Originalparent
quest_bugfixing root/3:75 sq024_done>0 ->74.Intro_in retainedasbootunlock.
3ownedresources boot/controller/main; 2fileadds0replace, noofficialoverride.
Controllerallnativepayloads/edges kept exceptnode9mainref. Mainentrytestsdelivered
contacts/announcer_mq056/mq056_hook/01_hook2 ActiveOR Succeeded ->nativehub23;
elseoriginal3game-dayinvitationroute. Noresendforsavedinvitation; noforcedtimer.
Nativefourwaitinginteractions/races/rewards/finish/prevention/rearm unchanged.
Tower/PA2/profile+Issued0+noactiveoldracephases/busyfacts admitonce; no resets,
started-racemigration orhistorychanges. JohnnyexistingJV1visualpolicyunchanged;
livebody/voice/propsverificationpending. NoREDS/CETmodule/poll/spamadded.
1053copiednativepayloadchecks/60negativeadmissions/4resumestates/19officialbytes/
78installedarchiveaudits/3packedreadbacks/CRC45086 PASS;31deploycases41checks.
InitialtestharnessfixedwrongsceneIDassumption,fullpassbeforeinstall; buildunchanged.
GameclosedUNSANDBOXEDinstall;78priorpackagefilesverified/675protectedunchanged
including209savefiles+5caches/settings. Actual2hashes+ValidateRollbackPASS.
Buildprealpha/races_r1/build/r1_01 SHA
864A40BDE6F27A44DFCFFE4DF6AE443EE9BABA97654B473C4DE27D4F6498882C.
R1source/build/tools/tests/receiptsNOWPINNED; no installed-mainreruns/edits.
RecoveryFIRSTprealpha/races_r1/deploy.ps1 ValidateRollback/Rollbackwith
recovery/races_r1_01,THENP1/D1/N22/N21/C1/N2/N1/FO1/PA6/older.
NEXTcoldlaunchNORMALworkingpostTower save,preferuntouchedpreP1testbranch;
CityCenterstartonfoot->nativewaitprompt/grid. Noendingreplay/forcedfacts.
IssuedNOTpromptproof; all4/finish/payout/abort/repeat/reload/freshendingpending.
Evidence research/races_r1/assessment.json; docs/races_r1_playtest.md. No launch.

Latest2026-10-14T23:45Z P1 CYBERPSYCHOS INSTALLED; LIVE PENDING:
USERrequests restoration+onecompletedpsycho/reward test; gameclosed confirmed.
17originalfresh-onlyparentslices: localstart/finish0,journalInactive,total0..16,
genuineTower/PA2/U9/N1 guards; nativegates/mainphases/scenes/calls/rewards kept.
NativePOIActive afterfreshrecheck; no syntheticmarkers. Completed17 preserveditself.
Nativeglobalreporter resume: no oldintro ifintroDone; armONLYfuturecountmilestones
toavoidduplicatejournalincrements; alreadyTalkActive resumesnativeReginamaps.
Native12hfinalcall delayretained(restarts,notoldtimerreconstruction). Original
regina_bugfixing phases7/8 restorecontainerlock/unlock+lootjournalcompletion.
Normalclaimedrewardnotrefilled; no started-sightingmigration/counterrepair.
ExplicitGetMod("PTFR_CyberpsychoP1").Test("DISPOSABLE_SAVE") ONE-USEfixture:
requiresdone17/mq043done1/reward1,bothrootsSucceeded,journalcount17,unusedP1owners.
NativeResetKillCount+Reactivate(Respawnaliasvalue3)twolocalLtMowercommunities;
localjournal/message reset,2onscreenvisitedfalse,count16/killed0,mq043handoff0,
singleReginacrate RemoveAll/ReInit fromstockretrofix payload. NOplayeritemgrant,
retrofixflagwrite/autosave/load. TestNPC/device/rewarddelivery UNVERIFIED. Discard
testbranch; no 'freshhistory' claim. NativeJV1audio/bodypolicyunchanged, quietCET.
AutoSave1level48,17:56:55,14Oct2026 Dogtownhotel trackssts_ep1_08_start ispostTower;
readonlycount17/killed6/mq043done1/reward1/LtMowerfinished1. SavSHA
1305016A84A5887B2F073ADBA703910DDF565D681A2E6CDC278E83800DC74649.
3filebyteexactworkspacebackupresearch/cyberpsycho_p1/checkpoint_before_install.
Livejournalstate/counter stillcheckedbycommand, absentfaultfieldsNOTlivezero.
223nativepayloadchecks/554negativeadmissions/306countercases/LuaJITPASS;
57officialbytes/77installedarchives/noresourceorCRCcollision;33deploycases43checks.
GameclosedUNSANDBOXED4adds0replace;74priorpackagefilesverified,669protected
unchangedincl209savefiles+5caches/settings. ValidateRollbackPASS. No launch.
Buildprealpha/cyberpsycho_p1/build/p1_07 SHA
105F80B28823891695D315B5322ABC98AD7E982780B20DEBF826CB9B3BE616E8.
P1sources/build/tests/tools/receiptsNOWPINNED; preservefailed/superseded01..06.
RecoveryFIRSTprealpha/cyberpsycho_p1/deploy.ps1 ValidateRollback/Rollback with
recovery/cyberpsycho_p1_01,THEND1/N22/N21/C1/N2/N1/FO1/PA6/older.
NEXTcoldlaunchAuto1above,NEWmanualsaveBEFOREcommands,Test thenStatus; closemenus.
TestResetDone1/Preparing0/Entered1 areNOTNPCproof. LtMowerinKabuki, nonlethal,
readclues+report=>17;12gamehours->Reginacall/office/rewardloot. CrateReadywaits
streaming. Refusal:sendtext/status,doNOTforceguards. Docs/cyberpsycho_p1_playtest.md
andresearch/cyberpsycho_p1/assessment.json. Genuinefreshending/all17/reloadpending.

Latest2026-10-14 PREENDING GIG MAP REFERENCES PRESERVED:
USER requested saving4screenshots forLATERgigspawncomparison, notanalysisnow.
Byteexactcopies+SHAmanifest underresearch/gig_map_references/pre_ending_20261014;
sourcesretained. Userstatespreending; exactsave/history/filtersunknown. Noimage
analysis/markerinventorydone. FewpostTowermarkers aloneNOTstockparityproof.
Nativefixerbatchtiersretained; legitimateprogression vs restoredtier/whitelist
blocking needsactualstateevidence. No quest/fact/runtime/savechanges thisturn.

Latest2026-10-14 D1 USER AIRDROP FUNCTIONAL PASS:
USER reports "airdrop worked" after suppliedsa_ep1_30TPcommand. Recordfunctional
USERpass, NOTexactcrate/loot/reward/all15locations/newsave-reload/freshendingproof.
Priorcooldowntarget/counter5/5 screenshot doesNOTprove naturalprogression: userdid
notanswerwhetherbefore/afterprovidedSetFactStrtest. No confirmedtimerstall/fix;
leaveworkingD1unchanged. RepeatUNFORCEDcycle+reload remain deferredchecks.
Evidence research/airdrop_d1/live_result_20261014.json supersedes installation
livepending forreportedfunctionalityONLY. Documentationonly, no runtime/save/
settings/cachewrites orlaunch. Installedpinnedbuilds/recoveryorderunchanged.

Latest2026-10-14T21:19Z D1 DOGTOWN AIRDROPS INSTALLED; LIVE PENDING:
USER N22 scanners allvisible+work, C1 carstealingworks: separateUSERfunctional
passes recorded, NOTexhaustive157/rewards/secondcycle/reload/freshendingproof.
D1 adds2files/0replacements; mod-owned stockairdropcontroller+one-shotboot.
All172nativepayloads/nestededges unchanged; soleedge23False3Intro->17In uses
existingrepeatpause/cooldownroute, nointroreplay.15ordinarylocationphases original;
mq304subcontrollergateskept,no sidejobroot. Native5realminute startupcooldown,
NOTpreTowerremainingtime reconstruction. Lifetime/reward/uniquehistorynotreset.
GenuineTower+PA2Finished+EP1availability+D1Issued0+testloop0+mq304active0+
counter==rewardcounter preventsoldbacklogpayout; recheckbeforeissue. No allactive0
gate: Auto9has38active1 AFTERTower; ordinaryselector doesnotuseit asliveness.
Oldflagsnotcleared,no interrupted-dropmigration. Existingnativepaused/location/
variantgatesretained. No scripts/poll/CETspam/Johnnycastscenes inboundedclosure.
172payload+57negativeadmissions+19officialbytecomparisons+2packedreadbacks+
CRC18469/76archive0collisions PASS.31deploycases41checksPASS; d1_01typedId
buildfailureand2fixturehelpererrorspreserved;fixedbeforeinstall. NoREDSchanges.
GameclosedUNSANDBOXEDinstall,actualhashes+ValidateRollbackPASS;72priorpackage
filesverified,667protectedunchanged incl209savefiles5caches/settings. No launch.
Buildprealpha/airdrop_d1/build/d1_02 SHA
E8CA7D65ADB25650DF99FEA2555A8A0462B2EC60FB577C4693BE44B2BB5C07BC.
Sources/build/tools/tests/receiptsNOWPINNED; no mainreruns/overwrite.
RecoveryFIRSTprealpha/airdrop_d1/deploy.ps1 ValidateRollback/Rollback with
recovery/airdrop_d1_01,THENN22/N21/C1/N2/N1/FO1/PA6/older. Seeassessment.json
underresearch/airdrop_d1 anddocs/airdrop_d1_playtest.md. NEXTcoldlaunchCURRENT
postTowerworkingcourier/scannersave, roamDogtown~5realminutes+localtriggers,
lootonecrate;laterrepeat/newsave-reload. NOTallmapicons/Issuedproof. Noendingreplay.
Auto15newestmetadata tracks preendingBeforeTomorrow; PTFRFinishedabsent, NOTa
verifiedpostTowerfixture(absencenotlivezero);doNOTrecommendblindly. Auto9postTower
readonlyprobe SHA4239ED680E1970223F474B01FA3FB689139998D877294AB333BC79176F3DD412 unchanged.

Latest2026-10-14T20:38Z N22 MARKER-ONLY REPAIR INSTALLED; LIVE PENDING:
USERcontinueafterN21diagnosis. ONEscriptreplacement,0adds; noarchive/ownerchanges.
SamePTFR.NCPDRepairN21.ScannerRepairN21 class+154table+ownedfacts retained.
Phase-1=systems/entry/delayunavailable, -2=savedPOIlookupfalseaftervalidsystems.
Activate fallbackONLYjournalInactive1+phase-2+independentfinishfactsnonempty,
AFTERgenuineTower,N2IssuedEXACT1,MapAcknot1,allterminalfacts0. Existingreturned
Completed/invalidphase,Active/terminal/unknownJ,unavailablesystemsblockfallback.
Normalvalidphasepathunchanged; laterActiveack+3attempts/session unchanged/quiet.
No syntheticmarker/nativefactreset/rewardcredit/questrestart. Fivewithoutindependent
finishfacts(cpz16,lch05/14/15,nid14)NOmissingrecordfallback;normalpathunchanged.
SixN21supplementPermitpathsUNCHANGED andstillneedseparatecare; thisdoesNOTfix
everyunfinished/partialprogresscase. PriorWestbrookuserpassretainedseparately.
24576policycases+153positivefinishwrites+exact15unchangedmethods/tablePASS.
CombinedCLI/fullSCCEquipmentEx+compiledbodyreadbackPASS. n22_01temporaryarray
compileerrorpreserved; n22_02fixedwithlocalvar.46deploycases63checksPASS,
initialsandboxjunctiondenialpreserved;fullunsandboxedWORKSPACErerun0skip.
GameclosedUNSANDBOXEDatomicreplacementwithbefore/displacedbackups; actualhash+
ValidateRollbackPASS;666protectedunchangedincl209savefiles5caches/settings;
71otherpackagefilesverified. No launch/saveedit/settingschange.
Buildprealpha/ncpd_marker_n22/build/n22_02 SHA
F57C149F7F3CD1850DD0EFA01FD5B7D9AFA0B0B680DBAF7F19957A972AD5788F;
installedscriptSHA8F4DDBF69C7BA62984B6236EEF9461EF16AC4D639D1FB50CDFE0C3FCB121BEB3.
N22sources/build/tests/compiler/deploytools/receiptsNOWPINNED; no mainreruns.
RecoveryFIRST prealpha/ncpd_marker_n22/deploy.ps1 ValidateRollback/Rollback with
recovery/ncpd_marker_n22_01 (restoresN21script), THENN21/C1/N2/N1/FO1/PA6/older.
NEXTcoldlaunchAutoSave9level48,14:20:26,14Oct2026 SHA
4239ED680E1970223F474B01FA3FB689139998D877294AB333BC79176F3DD412reverified;
originalbackupresearch/ncpd_n21_live_20261014/snapshot_03/AutoSave-9.
Closemenus20s,checkpreviouslysparsemaps; optionalnewlyvisibleencounter. Noending
replay/forcedfacts/ownerrestart. Laternewsave/reload. Livevisibility/API/newsave/
freshendingpending. Evidenceresearch/ncpd_marker_n22/assessment.json.

Latest2026-10-14 N21 LIVE WIDE-VISIBILITY FAILURE; DIAGNOSIS ONLY:
USER Watsonlooksfull, WBR/CCT/HEY/STD/PACstill1-2icons; visitedoneWBRscannerworks.
RecordoneencounterfunctionalUSERpass, NOTcompletion/reward/reload/fullWatsonproof.
Gameclosed; frozen5logs+AutoSave9threefiles snapshot_03 under
research/ncpd_n21_live_20261014. Earlier01/02 partiallogcopies retained (badlogpath).
CompilePASS14:12:31;14:13ArchiveXL154N2+6N21merges; all6installedhashesmatch.
Auto9level48,14:20:26,14Oct2026 SHA
4239ED680E1970223F474B01FA3FB689139998D877294AB333BC79176F3DD412.
SavedN2Issued128/154; MapAck24. Regionissued/ack: BLS24/0,CCT10/0,HEY19/0,
PAC11/0,STD21/2,WAT31/21,WBR12/1. IssuedNOTallobjects/renderproof.
All6supplementRequest1,Permit/Deniedabsent(absenceNOTlivezero). N21sourcePhase
requiresSavedPOIlookup beforejournalActive; missingrecord=>-1=>noactivation or
supplementpermit. All24AckhashespresentinrawMappinSystem_POI; mostissuedmissing
hashes, manywerepresentpreTower. Strongmissing-record/circular-gatesupport,
NOTliveAPIresult/validatedbinaryPOIdecoder. Rawjournaloffset4mostly1outsideWAT;
stillnotnewlyvalidatedstateparser. NativeWatsonexplicitentryActive explains
workingpattern; otherprefixesphaseonly. ma_jpn_20_start0->1at14:20:49AFTERsave,
consistentwithWBRreport, notprovenexactvisitedID/completion. No needrepeatplaytest.
NEXT repair scopedentryactivationforissuedunfinishedinactivePOIs withoutrequiring
preexistingmarkerrecord; auditcompletion/unknownhandling, noownerrestart/native
progressreset. Factless/supplementadmissionseparate. No runtimepatchthisturn;
N21stillinstalled/pinned, recoveryN21firstunchanged. No launch/save/settings/cache
writes. Evidenceassessment_01.json; livevisibilityFAILsupersedespendingnotes.

Latest2026-10-14T18:08Z N21 SCANNER ACTIVATION REPAIR INSTALLED; LIVE PENDING:
USERcontinueauthorizesrepair.3additions/0replace,existingN2+C1/N1unchanged.
QuietREDS154N2IDtable nativeChangeEntryStateActive onlyafterN2Issued1,finish0,
JInactive/Active+savedPOIphase1/2/3;unknownwaits,Completed0/terminalblocks.
No syntheticmarkers/phasechange/rewards/nativefactreset. MapAckafterlaterActive
sample,max3attempts/session;reloadresetslocalattempts/epochnotownership.
6newnativeparent-sliceowners(nooverrides) shareN2Issued. hil02/03/04+rcr07
startfactsprovenunconditionalINITIALIZATION, beforeplayertrigger; supplementary
requiresstartEXACT1+finish0+unfinishedPOI. OldN2requiresstart0,disjoint.
Originalentrywriteskept(hilstartmayincrement1->2),notmanuallyreset. CPZ16/NOK05
no startfacts: supplementonlyPOIDiscovered2ANDoldPermit0;oldN2only1/3disjoint.
OldDeniednotcleared;newinjectioncanhandleoldrefusal. AlreadyIssuednorestart.
Stockgameplayrefs/parentgates/ports/rewards/cleanupunchanged. Other15saved-start
candidatesremainprotected;NOTgenericpartialmigration/allunfinishedPASS.
InitializerflagNOTcertifieduntouched: persistedpartialworldbehaviorlivepending.
73nativepayload/1272modelnegativecases/191officialbytecomparisons/6packedreadback
PASS,75archiveaudit0collisions,6CRCidschecked. CombinedCLI/fullSCCEquipmentEx+
bodyreadbackPASS.39deploycases49checksPASS. GameclosedUNSANDBOXEDinstall,
actual3hashes+ValidateRollbackPASS;664protectedunchangedincl209savefiles5cache/
settings,69priorpackagefilesverified. No launch/saveedit/forcedfacts.
Buildprealpha/ncpd_repair_n21/build/n21_01 SHA
9D04D0B257FF92A0A8318CBF6F2138CCE50F718607373A2E6078136446FBECE4.
Source/build/test/compiler/resourceaudit/deploytools/receiptsNOWPINNED,no reruns.
RecoveryFIRST prealpha/ncpd_repair_n21/deploy.ps1 ValidateRollback/Rollback with
recovery/ncpd_repair_n21_01,THENC1/N2/N1/FO1/PA6/older. Evidence
research/ncpd_n2_missing_20261014/repair_install.json;docs/ncpd_n2_playtest.md.
NEXTcoldlaunchAuto8level48,12:10:04,14Oct2026;SHA A7A55B53FAE56E8EB70485711A9B9BBE8DE3159DCC34E9C7F62ABDCABC59A12B
reverifiedunchanged. Closemenus20s,inspectsameCCT/HEY/WBRmaps+realencounter.
OptionalreadonlyCET PTFR.NCPDRepairN21.ScannerRepairN21:Inspect("ma_cct_cpz_01").
Noendingreplay/StartAll. Preserveoriginalfixture,newsave/reloadlater.
LivePOIAPIavailability/visibility/gameplay/payout/reload/freshendingallPENDING.

Latest2026-10-14 N2 MISSING SCANNERS DIAGNOSED; NO PATCH AUTHORIZED/INSTALLED:
USER many missing in3maps, explicitlycomparedpreending confirmsmissing. CHECK
request only: gameclosed, no launch/runtime/save/settings/cachewrites. Frozen
10logs in research/ncpd_n2_missing_20261014/live_01 (includes5oldArchiveXLrotations).
Latest13:30runcompilePASS;154uniqueN2merges each13:32/13:35;3installedhashesmatch.
Stockq307_01_pickup root/10node105 bulkActive->Inactive allminoractivityPOIs.
N2retains92phase-onlystartup prefixes;88alsohaveNOPOIentrystate nodeincatalogued
nativeowner. All12CCT/19HEY/21WBRprefixesphaseonly;Watsonexplicitentrystate
explainsN1notcoveringthispattern. Confirmedsourceomission+matchingusersymptom,
NOTperIDliveexecutionproof. No newerN2session save; Auto8predatesN2installation.
ReadAuto8SHA A7A55B53FAE56E8EB70485711A9B9BBE8DE3159DCC34E9C7F62ABDCABC59A12B
andPONR1SHA EF33668CE43C62FAF3104B8068601BE8E6146807418A58BCDD8E8DA752EDD9B6,
samelineage;unchanged.19N2candidatespositiveStart/noSerializedPositiveFinish,
currentfreshguardblocks;hil02/03/04alreadypositivebeforeTower. NOTproofnever
visited/neverprogressed; missingfactNOTlivezero. RawPOIjournaloffset4 pre2/post1
retainedasrawdiffONLY, NOTvalidatedparser/POIphase. No currentIssued snapshot.
NEXTifuserasksfix: scopednativeentryactivationforadmittedunfinishedowners,
guardalreadyIssued compatibility separately; separatelyauditstarted-incomplete
resumption. NOglobalgroupactivation/forcedstartfinish/Issuedreset/duplicate
reward. C1/N2/N1installed/pinnedunchanged. ExistingC1-firstrecoveryorderretained.
Evidencefindings.json+source_assessment_01.json+save_facts_01/02.json innewfolder;
docsN2/alpha/roadmapupdatedregression, NOTlivepass. No extraendingreplay needed.

Latest2026-10-14T17:19Z C1 EL CAPITAN COURIER RESTORATION INSTALLED; LIVE PENDING:
USER defersN2test; requests carstealing. Nativecourier-only ep1sandboxparent
25nodes, originalmain/retrofix/cleanup/restartedges anddirectstockrefs; notbroad
EP1root. Sevenregionvehicleloops, delivery/hacking/challenges/rewards/unlock
counts/cooldowns, eligibleintro+laterMuamarstory nativegates kept. Completed
stories notreplayed; partialpreTowerdelivery/intro/outro NOTmigrated. Entry
genuineTower+PA2Finished+U9+nativeEP1availability, idleactivity/retrofix, saved
Issued0; recheckbeforeissue. Nativeentryready_to_start1 retained, NOTexactold
cooldownreconstruction. Lifetimecounts/rewardfactsnotcleared.
OriginalDanielsphonecontroller addedonce; usesU9globalphone/interruptowner.
OneMODresourceoverride gig_phone_u9/fixer_cleanup extendsN1version AFTERall8
fixers+NCPD, keepsalloldpayloads/timeout/edgesexcept424->new600/601->6. Original
EP1Danielsbalancecondition84/inline83 rebased600/601; nounrelatedcontacts/global
EP1resetservice. 00_C1prefixfirstwins over0_N1/mainarchive;modlistabsent.
NativeJohnnycourierscene usesCharacter.Silverhand matchedbyunchangedJV1;
voice/timingkept/bodyhidden existingpolicy. Actualnewscenevisualpasspending.
No runtimeREDS/CET/newlogging, scanner/race/airdrop/cyberpsychogameplaychanges.
59payloads75negativeadmissions220officialbytecomparisons3packedreadbacks,
2CRCIDschecked74installedarchivesaudit; expectedonly2priorversionsofmodcleanup.
33deploymentcases43checksPASS. No redscriptcompile required (no scriptchange).
GameclosedUNSANDBOXED2adds0replace;662protectedunchanged incl209savefiles5caches/
settings,67priorpackagefilesverified. Actualhashes+ValidateRollbackPASS. No launch.
Build prealpha/courier_c1/build/c1_02 SHA
9B288F31B94437FCF23D10F7996E101FDEEE5274036B196C1E014AEF1A0ED6B7.
Archive00_TowerContinued_Courier_C1.archive SHA
DD7C93B26B73B5D498302BA8F633E5B54B32F53B51F53F9637A94706A6CB9EF5.
Sources/build/test/deploytools/receiptsNOWPINNED; no mainreruns/overwrites.
c1_01supersededpreserved. RecoveryFIRST prealpha/courier_c1/deploy.ps1
ValidateRollback/Rollback with recovery/courier_c1_01, THENN2,N1,FO1,PA6,older.
NEXTwhenuserready coldlaunchAutoSave8level48,12:10:04,14.10.2026 (sameN2fixture),
savSHA A7A55B53FAE56E8EB70485711A9B9BBE8DE3159DCC34E9C7F62ABDCABC59A12B
reverified. Savedintrofinished1,deliveries/jobs1, sampledactive/mounted0;
missingfactsNOTruntime0. Existingbackuprecovery/ncpd_n2_fixture_20261014/AutoSave-8.
Noendingreplay/StartAll/forcedfacts. Travelnaturally, vehiclecontract/map/journal/
call/delivery/payout/nextcycle/newsave-reload; stocklocalspawn notallmapicons.
Docs docs/courier_c1_playtest.md; research/courier_c1/assessment.json. Issued is
NOTlivevehicleproof. N2testdeferredNOTpass; allC1gameplay/freshendingpending.

Latest2026-10-14T16:43Z N2 CITYWIDE NCPD EXPANSION INSTALLED; LIVE PENDING:
USER "the activities works, now restore all ncpd scanners": N1userfunctionalPASS,
exact3type/completion/call/counter/reloadcoverageUNSPECIFIED. SeparateN1live_result.
N2adds154nativeowners, leavesN1threeunchanged;157stock-connectedPOIs across7regions
(114GangWatch/26HiddenStash/17Outpost), NOT157newiconsforanysave. Fourunwiredjournal
entries kab04/kab11/kab14/hil05_01 notactivated; boundedminoractivitygraphaudit,
notglobalproofunused. Onlyfreshnativeprogress; no partialmigration/certifiedhistory.
Originalgameplayrefs+inlineowners, nativeparentgates/ports/cleanup/retrykept;
Badlandstier9,CPZ15/16cleanup,CVI11setup/ANDwait,CVI13Out2,Kab06Resetpreserved.
CommonTower+PA2Finished+N1/U9support; savedIssued0, actualstart/finish0 rechecked
afterstockwaitsbeforeentry. LCH14/15sharefinish14; useindependentnon-resetstart
factsinstead ofsharedfinishguard; nativepayloadnotfixed/rewritten.
CPZ16/NOK05missingstartfacts: ONEquietnewadmissionreds reads nativeSavedPOIphase
viaGetPointOfInterestMappinSavedState(CastUint32(journalentryhash)). Onlyowned
Permit/Deniedwrites. Default/Undiscoveredaccept; Completed/Discovered/invaliddeny;
missingdefer. API/callercompiled, actualliveavailabilityUNVERIFIED; nounknownfresh.
No newdispatcher/token/resetcontroller, noN1cleanupoverride, no markers/reward/
counterrepairs, no nativefacts/journalreset, cyberpsycho/race/sidejob/giguntouched.
17briefingsalloriginalncpd_dispatcher_holo; Johnnyexistingpolicyunchanged.
1132nativepayloads+2947negativeadmissions,191officialbytecomparisons,154packed
readbacks,73installedarchives0overrides;154CRCIDschecked;Kab05_id1resolves1collision.
PTFR+CodewareCLI/fullSCCincludingEquipmentEx+bodyreadbackPASS.38deploycases48checks
PASSboundtoliveinstaller. Earlierbuild/harnessfailurespreserved; n2_04superseded.
GameclosedUNSANDBOXED3adds0replace;659protectedunchanged incl209saves+5caches/settings,
64priorpackagefilesverified; actualhashes+ValidateRollbackPASS. No game launch.
Buildprealpha/ncpd_scanners_n2/build/n2_05 SHA
DE4A625A6EE5158D5DEB17B4E0A61229F012566D64207680BC302AA8C17EF4AF.
N2sources/build/catalog/test/compile/deploytools/reports/receiptsNOWPINNED.
No installedmainrerun/overwrite. RecoveryFIRST prealpha/ncpd_scanners_n2/deploy.ps1
ValidateRollback/Rollback with recovery/ncpd_scanners_n2_01; thenN1,FO1,PA6,older.
NEXTcoldlaunch AutoSave8level48,12:10:04,14.10.2026 debugma_wat_lch_01_start;
savSHA A7A55B53FAE56E8EB70485711A9B9BBE8DE3159DCC34E9C7F62ABDCABC59A12B.
3filebyteexactworkspacebackup recovery/ncpd_n2_fixture_20261014/AutoSave-8;
originaluntouched. ExistingN1ownercontinues, notreset. NCPDfilteron, inspectseveral
districts/actualencounter; new-save/reload. Noendingreplay/StartAll/forcedfacts.
Docsdocs/ncpd_n2_playtest.md; assessmentresearch/ncpd_scanners_n2/assessment.json.
All154gameplay/edgecases/newsave-reload/freshendingintegrationremainpending.

Latest2026-10-14T16:00Z N1 NCPD SCANNER PILOT INSTALLED; LIVE PENDING:
USER requests scanneractivitynext. Implemented THREE fresh-only LittleChina
nativeowners ma_wat_lch_01 OrganizedCrime /02 Assault /03 ReportedCrime.
NOTcitywide rollout, NOTcertifiedpreTowerhistory, no partialprogressmigration.
Stockdistrict slices retainPOI/tier/sidecontentgates; directORIGINAL gameplay
refs (02inputIn2), evidence/rewards/prefabs/scenes/departurecleanup unchanged.
OriginalchildOut1->Watsonachievement+1->nativeachievement manager preserved;
no manualpayout/creditrepair. Nooutputterminateswrapper beforechildcleanup.
GuardgenuineTower+PA2Finished+U9Support; native start/finished0(+01AVstart0),
one-shotsavedIssued0. Recheckafterstockwaits beforePOI/owner;changedstateRefused.
AddedoriginalNCPDdispatcher77 plusstockminorroot24ma_tokenloop; initialtoken0,
phoneidle+balancedNCPDcounts(nohistoricaldone0requirement). ExistingU9global
phone/resetownerNOTrestarted. OneMOD-OWNEDresourceoverride gig_phone_u9/fixer_cleanup:
original334+466insertedafter332/464bef468; all8oldcontacts/timeout/resetretained.
Nativebriefingcastdispatcheronly; noJohnnychange. No broadroot/cyberpsycho/
race/gig/sidejob reset, script/CETadd orconsoleoutput. Userempty-markerIDunknown;
source-supportedmissingowner NOT runtimecauseproof. catalog_v1structuralONLY.
54nativepayloads+134negativeadmissions,12officialbytecomparisons,5packedreadbacks,
4CRCinjectIDs;72existingarchivesbound,soleexpectedcleanupcollision(mainarchive),
0_prefixfirstwins/modlistabsent.32installerfixtures42checksPASS; initialtest
syntaxerrorfixedbeforepass. No redscriptchanges/compilationrequired. No launch.
Gameclosed UNSANDBOXED2adds0replace;657protectedunchanged incl209saves+5cache/
settings/PA6+GD2+FO1; actualhashes+ValidateRollbackPASS. Previouspassesuntouched.
Build prealpha/ncpd_scanner_n1/build/n1_01 SHA
4A5490C9F5F1AC4997BBC308EF2BC0FB6C77F7376ED6CCECDC6A1C6762764EAC.
Sources/build/tests/deployer/reports/receiptsNOWPINNED; no oldmainrerun/overwrite.
RecoveryFIRST prealpha/ncpd_scanner_n1/deploy.ps1 ValidateRollback/Rollback with
recovery/ncpd_scanner_n1_01, THENFO1,PA6,older. File rollback notsavedgameplayundo.
NEXTcoldlaunch AutoSave-6 level48,11:14:31,14.10.2026 savSHA
EEB8EC10B5162A332E88239E18E83D096BD98E6FC6602771B0D758E0B45BBAFA;
3filesbyteexactworkspacebackup recovery/ncpd_n1_fixture_20261014/AutoSave-6.
MissingserializedcandidatefactsNOTlivezero; runtimeguardsauthoritative.
Closemenus10s, enableNCPDmapfilter, testrealenemies/evidence/call/completion/
onecredit/cleanup/newsave-reload andcompletedcontrols. Noendingreplay/StartAll/
forcedfacts. Instructionsdocs/ncpd_n1_playtest.md; assessmentresearch/ncpd_scanner_n1.

Latest2026-10-14 FO1 WAKAKO USER PASS:
USER reports "it worked and verified behavior against pre ending world".
Screenshot shows seatedWakako normalFprompt andWestbrook/husbandsdialoguechoices.
Recordbasicinteraction+userpreendingcomparisonPASS, NOTall7office/fullstockA-B/
exit-revisit/reload/gig-phonecoexistence/Reginareward/freshendingpass. Exactslotnot
restated. PreserveworkingFO1; no repeatbasicWakakotestrequired. Separateevidence
research/fixer_offices_fo1/live_result_20261014.json; checklistupdated.
Documentationonly; no runtime/save/settings/cachechange, no launch/install/test
mainreruns. FO1sources/build/tests/receipts remainPINNED; recoveryFO1firstunchanged.

Latest2026-10-14T14:57Z FO1 FIXER OFFICES INSTALLED; LIVEPENDING:
USER confirms onlyWakako visited: idle/nointeraction; otherssuspectednotverified.
Sevennative defaultowners(Wakako/Dakota/Dino/ElCapitan/Padre/Regina/MrHands),
sixexactrootslices+nativeloops; HandsdirectoriginalDogtowndefaultphase. Original
scenesunchanged; defaultprefabsbehindgenuineTower+PA2Finished+U9supportissued.
Noforceddefault_on: Wakako23setteromitted,19spawnwait->20availabilitywait;
existingpositivepermissionrequired. Reginaintro/tier/NCPD/gigcreditbranchesnot
copied; completedpsycho/report/rewardfactsnotreset. Originalnativeguard
ow_psychos_reward_collected retained. Defaultplayerinitiatedcallalternatives
remainnative; existinggigphoneownersnotrestarted. No newCET/reds/polling/logspam.
Auto5 10:20:26 14Oct2026 level48 read-onlysample:handoff/support1, all7default_on1;
savSHA DF29E8F9DF88A01F4D9521E6645180F356D557DF7ECFD0D66D69D599E1D6BBD9.
AbsentserializedfactsNOTlivezero. Stockmissingowner explanation source-supported,
notruntimecauseproof. 160nativepayloads/edges+120negativeadmissionsPASS;14official
resourcesbytecompared/71installedarchives0targetoverrides;7archivepackedreadbacks
andindependentCRCcollisionchecksPASS.29deploycases39checksPASS; initialharness
rootescaperelativepathbugfixedandfreshfullsuitepassed, priorfixturespreserved.
Gameclosed UNSANDBOXED2adds0replace,59PA6+GD2preserved,655protectedincl209savefiles,
5cache/settingsunchanged. Actualhashes+ValidateRollbackPASS. No gamelaunch.
Buildprealpha/fixer_offices_fo1/build/fo1_01 SHA
6B1916854E50AFB0EC0B4BC607A7BB9A420BE88CF5632613901781CF13A2F440.
FO1builder/tests/deployer/build/reports NOWPINNED; no mainreruns/overwrite.
RecoveryFIRSTprealpha/fixer_offices_fo1/deploy.ps1 ValidateRollback/Rollbackwith
recovery/fixer_offices_fo1_01 (moves2addsrecoverably), THENPA6/olderrecovery.
NEXTcoldlaunch currentpostTowersave (checkedAuto5timestampabove), visitWakako,
talk/exit/leave-return, NEWsave/reload. Other6offices/gig-callcoexistence/fresh
endingintegrationpending. Noendingreplay/StartAll/forcedfacts/resetrequired.
Evidence research/fixer_offices_fo1/assessment.json; docs/alpha_playtest_tasks.md.

Latest2026-10-14T01:29Z PA6 LOG-FIRST H10 ACTIONS/ROGUE/QUIET REPAIR INSTALLED:
USER loadedpreending/skippedcredits, waitedstreet1min: cameraFIXED,H10furniture
restored, Emmerick+Clairework,4gigmarkersvisible. NoH10interactions; approachRogue
crash. USERasksquietconsole and explicitlylogfirst. Userpassesareseparatefrom
allgeometry/allgigs/reloadcoverage. Frozen16logs/settings/crashfiles45MB byteexact
research/postending_pa6/live_20261014T011540242Z; no source/savewrites orlaunch.
LivecompilationPASS20:46:48; sixhandoffflags1/opticsall1/fault0. FourmainPOIactive
agreesreported4markers; leavegigsunchanged. PA5traces149transition+36restoration+
6maprows whilealreadydone; 142gigModLogrows2passes, NOTendlessrestorationfailure.
H10liveactions1/0/0/0 untiltraceendsat elevatorz46; AutoSave0Ready1,Enabledabsent
(absenceNOTlivezero),5geometrypairs1. Oldactionpermissionneeded20mupstairssafe
5spoll; patch permits sameunchanged30factguards+posthandoffoffsiteaftergeometry.
Native IsInside#mq000_tr_vs_apartment AND!IncomingCall STILLprecedesActivescene.
EntrywaitsH10ActionsArmed(permission,NOTActive), no circularstreetwait. Exactlater
promptblockerunmeasured; currentfixlivepending, no purchase/entitlementwrites.
Roguecrash21:08:55 WRITEAV,NOTOOM. Dumpkind7/tablecount2/capacity2/request2,
playeractor1/lipsync2,badrefcounterat table+2*16 verified. LocalR8scene retained
duplicate[Rogue,Rogue,V]. One-resoverride removesduplicateslot1 andrebasesV2->1;
all47nodes/dialogue/audio/actors/workspots unchanged. Nativecompactionmechanism
inferred, exactoutofboundsproven. Same-second missingrogue.anims warning; no
inventedresourcepathfix. LiveRoguestability/lipsyncdeliverystillpending.
QuietCETdefaultnoverbosepoll/trace; manualgettersunchanged; optionalTrace(60),
TraceStop/TraceStatus. Twoownedfaultnoticesonce; per-gigModLogremoved ONLY,
retry/results/safetyunchanged. UnrelatedFactFinder Day...logsnotmuted.
PA6gameclosed UNSANDBOXED3backed-up replacements(CET/Entry/Baseline)+1add
0_TowerContinued_RogueLipsync_PA6.archive.59actualhashes/ValidateRollbackPASS;
651protectedunchanged incl209savefiles+5cachefiles/settings/GD2/mainarchive/
PA5optics;55oldpackagefilesunchanged.70sourcearchivehashesbound/revalidated,
onlybaselineRogueresourcecollision;0_prefixfirstwins,modlistabsent. Noownerreset.
CombinedCLI/fullSCC/readback+96integrationchecks,29Rogue/99H10/51LuaJITcomponent
checks,51deploymentcases86checksPASS. Indepreviews clearedpriority/rollbackgaps.
Build prealpha/postending_pa6/build/pa6_02 SHA
BE71C5AC4D2F9267AFD97DE65B85136033427A2EEAEB42B505A833853004A299.
PA6sources/build/tools/tests/receipts NOWPINNED; no mainsrerun/overwriting.
Recovery FIRST prealpha/postending_pa6/tools/deploy.ps1 ValidateRollback/Rollback
with recovery/postending_pa6_01(returnPA5+GD2), THENPA5currentrecovery, thenolder.
Evidence research/postending_pa6/assessment.json +live_result.json; docstopcurrent.
NEXTcoldlaunch AutoSave-0 level48,21:08:28,13.10.2026 atAfterlifeapproach,
samecrashattachedsavSHA5204FB67C16A8E5988A7948C10B52D53BC6DA850DECEE44CC56156FFA24C2FD9.
Noendingreplay/StartAll/forcedfacts. Safestreetmenusclosed10s, verifyquiet +H10()
actionsArmedtrue, thenRogueapproach/conversation andH10insideprompts. Actualnewsave/
reload andfreshendingintegration pending; preserveAuto0fixture. GameNOTlaunched.

Latest2026-10-14T00:25Z PA5 OPTICS/H10 REPAIR INSTALLED; LIVE PENDING:
USER requests investigate+fix postending zoom/focus, missing earlierH10work and
onlyJeopardyvisible. Gameclosed UNSANDBOXED4backed-up replacements+5adds;
58actualpackagehashes/ValidateRollback PASS,635protected unchanged including
200savefiles+5cachefiles/settings. Mainarchive+XL/GD2/49priorpackagefiles unchanged;
no launch/saveedit/settings/cachewrite. New small2resourceopticsarchive required;
no repeatedfullconsolidation, old mains/receipts preserved.
Camera uses exactstockmq000section660 playercamera resetFov/resetDof event,
overrideFov/overrideDof false (inactivepayloadFOV51 NOTforcedsetting). Scoped
one-shotowner/native10swatchdog, actualPA4alignment+safepostcredits admission,
4stablefiniteopticssamples after nativeoutput; no globalDOF/FOVoverride/reload.
Works existingFinished1Auto19 throughindependentpoll; reloadresetspermit/samples
only, neverownership. Opticalcause remainsHYPOTHESIS; nativeoutput/finiteFOV
NOTvisualDOFproof. ExistingPA4input/spawn/GD2darkness fixes preserved.
H10same24resources, oldcorridor OR safeposthandoffoffsite200mXY/75mZ acquisition;
existingsequential5geometryowners, noownerreset/entitlementwrites. Freshhandoff
waits geometryack beforePrepared; oldFinished1 supported independently. Existing
interactionstartupstillnearapartment. Priorverifiedscope apartmentlayers/actions,
NOTentirepubliclobby/atrium/elevators; broaderreportedinteriormissing stillneeds
visualconfirmation ifpersists. Housing25krepurchase notimplemented.
GigsdiagnosticsONLY: actualPOI/mappin/parent/journal getters, noquestmutation,
no forcedtiers/counters/visitedfacts/restart. Reported1icon remainsUNRESOLVED.
53accepted!=53visible; fourmainowners previouslyobserved. Added boundedCETtrace
180samples/222items max, H10/GigSummary every5, GigVisibility every30.
CombinedCLI/fullSCC EquipmentEx+bodyreadback,135integration/LuaJIT checks,
67camera/158H10/22gigcomponent checks,53deploymentcases98checks PASS offline.
Independentreviewcleared threefoundinstaller/reportbindingissues afterfixes.
Earliercandidate01compile typequalificationfixed; supersededbuilds preserved.
Build prealpha/postending_pa5/build/pa5_03 SHA
5638C911EE19D89EEDB14B3FBF824B51B358E390D05AA7C63203E1F5E06900CA.
PA5source/build/tools/testmains/reports NOWPINNED; no reruns/overwrite.
Recovery FIRST prealpha/postending_pa5/tools/deploy.ps1 ValidateRollback/Rollback
with recovery/postending_pa5_01 (returnsPA4+GD2), THENexistingGD2/PA4 recovery.
Evidence research/postending_pa5/assessment.json; docs/pre_alpha_clean_run.md.
NEXTcoldlaunch AutoSave-19 level48,19:31:18,13.10.2026, savSHA
F63366A9CE209E8BD599D46B0DDB381A4196E90DCF76C0CDACEA17F468E8499C unchanged.
Closemenus/holster30-45s atstreet, inspect actualcamera/H10apartment. CET
PTFR_PreAlpha.Optics()/H10()/GigVisibility() getters. NOStartAll/forcedfacts/
wholeendingreplay neededinitially. Newsave/reload andfreshendingregression pending.

Latest2026-10-13 POSTENDING OPTICS/H10/GIG REGRESSION DIAGNOSIS, NO NEW PATCH:
USER reports zoom/shallowfocus afterending, onlyJeopardy marker, and earlierH10
restoration absent; clarifies BUILDING INTERIOR, notpurchase/ownership. Treat
missingpreviousrestoration as integrationregression, not intendedrepurchaselock.
PA4logs19:28:26 onward sixflags1/fault0, active/FPPtransformsaligned, IFPnative.
PA4checksposition/directionONLY; no FOV/zoom/DOFreset/check. StoredFOV100/DOFtrue
unchanged; onlysettingsdelta QuickMapFilter4->16 (notrenderedfilterproof).
Stockcreditsscenenormalexits have playercamera resetDof/resetFov1; skipcutswhole
phase. Retainedopticaloverride plausible, NOTconfirmed; future scopednative
reset+measurecandidate, no hardsetFOV/globalDOFdisable/repeatedActivate/reload.
H10layers+baseline included/Readyregistered. Auto19 level48,19:31:18,13Oct2026
Exactcomparison24membersfrom6frozenH10archives ALLbyteidenticalinPreAlpha;
installedBaselinealsoR1byteidentical. PriorverifiedscopeVapartmentgeometry/
interactions, notwholepubliclobby/atrium/elevators; userbuildinginteriorreport
retainedasreported. Evidence h10_package_compare.json; don'tclaimomittedfiles.
savSHA F63366A9CE209E8BD599D46B0DDB381A4196E90DCF76C0CDACEA17F468E8499C
readonly: all6H10Ready1,BASEReady1,apartment_on1; no serializedgeometryacquire/
interactionEnable acknowledgements(absenceNOTlivezero). Oldgeometryadmission
onlyupstairscorridor z122.87+-5/XY60m, cannotactivatefromnewstreetspawn. Handoff
PrepareddoesNOTcheckH10. Exactliveblocker/priorcorridortimeunknown. Physical
interiorfailureseparatefromstillunimplemented25krepurchasesystem.
LatestU9dispatch72IDs:53accepted/10entrySafe-refused/9terminalpreserved;51parent
entries,4mainentries(FifthColumn/LifesWork/Jeopardy/TygerAndVulture),2EP1parents
pending. Accepted!=visible. All4mapwrappersentered; nativePOIActive precedesmain
entry. Missingvisitedfacts gateLATERdiscovery, donotclaimtheycauseallmissingicons.
No currentglobalphone/legacyrefusal. Keepreported1marker distinctfromliveproof
ofonly1owner; remainingnativegates/renderedmapstatus unresolved. No forcedtiers.
Evidence research/post_ending_regression_20261013 with frozen5logs/settings,
camera/h10/gigs reports; gigs_probe_v2 corrects draftv1grouping, usev2only.
GD2darknessuserPASS retained separately; PA4input/spawnPASS notfullopticspass.
No game/runtime/save/settings/cachewrites orlaunch. Installedbuildsmainspinned.
CurrentAuto18 wasoverwritten19:19:08; older13:16fixtureidentitymustNOTbeassumed.

Latest2026-10-13 GD2 USER GRAPHICS RESULT PASS:
USER reports "the problem is gone now" after GD2installation/stockcomparison.
Recorduser-reported graphicsresolution with currentGD2; retainworkingGD2+PA4.
No needrepeatending/vanillaA-B immediately. Exactloadslot/continuouspath/no-reload/
map/postcredits coverage notrestated; doNOTinventthese orclaimfullalpha/reloadpass.
Resultsupports practicalbenefit, NOTproofoforiginaleffectleak/modcausality.
Stockloopprovenance andofflinecomparisonlimits unchanged; rootcauseunconfirmed.
Evidence research/graphics_investigation_20261013/gd2_live_result.json.
Docs/evidenceonlythisturn; no runtime/save/settings/cachewrites orlaunch.
Installedsource/build/tests/receiptsstayPINNED; doNOTrewritehistoricalpendingreports.

Latest2026-10-13 STOCK-vs-MOD COMPARISON; CAUSE STILL NOT VERIFIED:
USER asks verifycause bycomparingstock/mod. Read-only audit14localofficialarchives
and69installedmodarchives,57targetkeys eachwithoneofficialsource. No overrides
ofq307parent/07thugs/08Misty/09crowd scenes+phases/cleanup ororiginaldizzy/exposure.
Onlyrelevantdirectoverrides: preexistingending_board/final_boards +NEWGD2stairsFX.
Bothboards preserveall25/30originalnodepayloads+stockskipcutrouting. Deltasat
CreditsRolling(PONRloadsuppression) andpostcreditsclosedhandoff, notstandupflow.
Explicitcorrection:5->5.5injuryloopandnoauthoredBreakareSTOCK, NOTintroducedby
PreAlpha. GD2deliberatelychangesstockduration; workaroundcandidate, notconfirmed
stock-parityrepair/rootcause. Actualeffectexecution/resourceuseunmeasured.
CompiledsceneFXstoresRUID/mask/placement, notseparatelybakedloop/timeline.
All427XLphaseinjectionsEP1root, nodirectq307sceneinjection. Actual13blocks31
descriptors:26visual/workspotvariantsdefaultoff withemptybaseranges;5unvaried
registry/areametadataonly. Misty4/Zetatech29communityentriesinactive-on-start.
TargetedMistyworld/light/timeactionscompletiongated; PA4/JV1/etcgatesrechecked.
DO NOTsay modinert/everythingstockuntilcredits: owners/registers/callbacks exist
beforehand andsavedworld/runtimeinteractionnotexcluded. Nocausalmoddeltafound.
No launch, modtoggle, patch,save/cache/settingschangeoroldpinned-mainrerun.
53PA4files+GD2hashreverified,GD1absent. Evidencegraphicsinvestigation
stock_comparison_{assessment,overrides,scene_flow,injections}.json.
VerifiedcausewouldneedcontrolledruntimeA/B withcompatiblebaseline, GD2separate
fromoriginalmodcondition; NOTperformedorauthorizedformoddisablingthisturn.
Do notlabelsame-filecomparisonasvanillalivepass, ordemandanotherfullendingrun
justtoreconfirmuserobservedonset. ExistingGD2installation/manualtestremainpending.

Latest2026-10-13T21:31Z GD2 FINITE STAIRS-EFFECT CANDIDATE INSTALLED; LIVE PENDING:
USER requests investigate+implement after clarifying reload BEFOREgettingupbeside
Misty preventsgraphicsfault. GD1negative/withdrawn; PA4camera/spawnPASS untouched.
New source-backed suspect EARLIER q307_falling_down_stairs.effect: native20s root,
holdloop5->5.5s holds contrast0.5 plus vignette/chromatic plateaus. Thugs scene
plays playerbound effect on3alternatebranches; no explicit instanceBreak/Kill
found in bounded thugs/parent/Misty audit. Nativeautomaticteardown UNKNOWN;
doNOTclaim confirmedleak/cause. No supportedgenericrendererreset found.
GD2removesONLY loopmetadata, correspondingLoopMarker andfirsttrackref; all4visual
payloads/curves/RUIDs,5track shells and20s recoverytail retained. Intentional
finiteinjurylook durationchange, NOT stockparity. Resourceoverride appliesanycaller;
not exhaustivecalleruniquenessproof. No scene/graph/script/shader/settingschanges.
Q307_EC86member audit foundno alteredmemberpayload/globalpostprocessculprit.
IFP remainedsceneblocked throughfailure; no supportedmodcallbackcause found.
Gameclosed UNSANDBOXED1archiveaddition/0replacements; actualhash+ValidateRollback
PASS. All53PA4packagefiles and635protectedentries unchanged incl197savefiles,
5cachefiles+UserSettings. No launch/save/reload/cache/driver changes.
Build prealpha/graphics_gd2/build/gd2_01 SHA
0CF9EA01F20D36916AFAA3EC7E90D305923092601CCA005099538216C0B12201.
Archive TowerContinued_StairsFX_GD2.archive SHA
03851DAA463B50FD78E2049C8A1ACDF04041E13C78B0538DCCC1955734768BDD.
21artifact/readbackchecks+independentreviewPASS;28deploymentcases/93checksPASS.
Initialsandboxjunctionskip preserved; fullunsandboxedWORKSPACEfixtures0skip.
GD2source/build/tools/testmains/reports/receiptsPINNED; no rerunsafterinstall.
RecoveryFIRST prealpha/graphics_gd2/tools/deploy.ps1 ValidateRollback/Rollback
with recovery/graphics_gd2_01, BEFOREchanging/recoveringPA4. Movesonlynewarchive
recoverably; GD1consumedrollbackmustNOTrerun. GD1absencerequiredfornewGD2install.
NEXTcoldlaunch ORIGINALAutoSave16 level48,22:47:33,12Oct2026 LeaveViktorclinic;
originalsavSHA51EE74B3EF3CB7872A27AD2C8619FD05BF7B5AB53FB9A84BFA0113555F012F69
reverified. ContinueTerry/Misty standup/walk/crowd WITHOUTmidrunreload/resets/
settingschanges; inspectworld/map. No CET/fullgigtestneeded. Auto17/18healthy
reloadcannotprove prevention; doNOTaskusercheckpointtimingagain. Improvement
wouldsupporteffectinvolvement, NOT proveoriginalcleanupcause. Livebenefitpending.
Evidence research/graphics_investigation_20261013/gd2_install_assessment.json;
docs/pre_alpha_clean_run.md topcurrentsection supersedesolderdiagnosticsteps.

Latest2026-10-13 USER CHECKPOINT TIMING CLARIFIED:
USER explicitly answers "Before getting up beside Misty", notfinalgoodbye/crowd.
Treat this as observed test timing; doNOT ask samequestionagain or override it
using sitting0 alone. Exactserializednode and linkageofthatobservation to
newestAuto17 remain unverified; retain rawfacts/logs withoutclaiming poseproof.
Reload BEFORE reportedstandup prevents subsequentvisualfault peruser; strengthens
earlier accumulated/reconstructedstate hypothesis, notspecificcause orcacheproof.
GD1withdrawn/PA4working unchanged. Documentationonly; no newgameplaytest/reset/
automaticreload/runtimepatch authorized orperformed thisclarificationturn.

Latest2026-10-13T20:36Z GD1 LIVE NEGATIVE; DIAGNOSTIC RECOVERABLY REMOVED:
USER reports dizziness suppression didNOTfixgraphics. New save beforereported
Vstandupdialogue +reload fixes. This weakens q307_dizzy-as-solecause, notabsolute
exoneration: renderedoverride/activeeffectexecution notinstrumented. Reload
points tosession/reconstructedstate, NOTproof corruptedshadercache/missingcleanup.
Gameclosed ValidateRollback/Rollback with recovery/graphics_gd1_01 PASS: moved
onlyaddedGD1archive torecovery,53PA4files/635protectedentriesunchanged; no save/
settings/cachechanges. GD1 no longerinstalled; rollbackreceiptconsumed, doNOT
repeatrollback/reinstallfailedcandidate. GD1pinnedbuild/tests/historypreserved.
PA4camera/spawnPASS unchanged. Latestlog16:31:42 forcedcheckpoint,16:31:44
q307_cutscene_load,16:31:46 start/together; afterreload startagain16:33:16.
Earlierq307_08_misty_sitting1->0 at16:27:51. NewAuto17metadata objectiveTalkMisty;
exactrelation touser's "beforestandup" wording unconfirmed, asknonblocking.
No newruntimepatch orautomatic save/reload. NewAuto17(level48,16:31:42,13Oct,
TalkMisty)3filesbackedupbyteexact underreload_before_standup; savSHA
48D9BC942B1A94934E7BADE33263C8BA966DA99221AF246CFA44A8290EA881D7.
Readonlyfacts talking[1]/sitting[0],cutscene_start/load+sampledPA2-4ABSENT(notlive0).
Exactserializedscenenodeunparsed. Sourceauditcomplete:nofixjustified. Twoopening
section6FOV/DOFeventsfinite, no standupcamera/exposuretriggerfound; expiry/reload
behaviorunmeasured. Q307_EC isworldlightingprefabvariant, NOToldr7WLC03scope.
No supported finalexposure/LUT/DOFstack/activeworldvariantgetterlocated. NEXT
clarifycheckpoint; laterpairedsameviewCamera()/activeFOV+screenshots faultyvs
reload, notanotherblindreset. No immediateendingreplayneeded. Evidence
native/reload_differential_assessment.json. Frozen3logs
gd1_live_failure_20261013; resultgd1_live_result.json undergraphicsinvestigation.

Latest2026-10-13T20:17Z GD1 SINGLE-EFFECT GRAPHICS DIAGNOSTIC INSTALLED:
USER approved reversible q307_dizzy suppression. AddedONLY
archive/pc/mod/TowerContinued_DizzyDiagnostic_GD1.archive, noXL/scripts orreplacements.
One depot ep1/fx/quest/q307/q307_dizzy.effect: clear3visualevents+trackrefs,
retain5native tracks/40.0625s/rootmetadata. Applies toanycallerofthisresource;
notexhaustivecalleruniquenessproof. Emptytracknativeprecedent but no wholeempty
analogue found; validserializedno-op NOT liveengineproof. Diagnostic, NOTfixed.
Gameclosed UNSANDBOXED install, actualarchiveSHA D9611EBEFC6D5213EC89E1334929B36944552A9AA602BA651A229AC738B7726E.
All53PA4files and635protectedentries unchanged incl197savefiles/5cachefiles/settings.
14artifact/readbackchecks+independentreviewPASS;26deploymentcases/82checksPASS.
Firstsandboxfixture junctiononlyskip preserved; fullunsandboxedWORKSPACErerunPASS.
No launch/settings/cache/driver/savewrites or oldpinned-mainreruns. PA4livepassintact.
Buildprealpha/graphics_gd1/build/gd1_01 SHA91F071FF3DE187AC89829048A6828103863A4A57ADA649D5CAD85424E9D643F3.
GD1sources/build/testmain/deployer/reports/receiptPINNED; no reruninstalledbuildmain.
Recovery ONLY prealpha/graphics_gd1/tools/deploy.ps1 ValidateRollback/Rollback
with recovery/graphics_gd1_01; movesaddedarchive recoverably. RollGD1back BEFORE
changing/recoveringPA4. ActualValidateRollbackPASS; no existingfiledeleted.
NEXTcoldlaunchoriginalAuto16 level48,22:47:33,12Oct2026 LeaveViktor. OriginalSHA
51EE74B3EF3CB7872A27AD2C8619FD05BF7B5AB53FB9A84BFA0113555F012F69 reverified.
PlayCONTINUOUSLY throughTerry/Misty standup/walk/crowd/credits, inspectworld/map;
no midsave-reload/reset/settingschange/questskip. Normaldialogueskip allowed.
Auto18INVALIDcomparison becausereloadalready suppressesfault. Normaldizziness
overlay intentionallyabsent. Improvementimplicateseffectorinteraction, not45s
field/missingcleanup/cachecause. Ifcrashstop. No CET/gigtestneeded.
Evidence research/graphics_investigation_20261013/gd1_install_assessment.json;
docs/pre_alpha_clean_run.md newtopsection. Graphicscause/livebenefitstillUNCONFIRMED.

Latest2026-10-13 GRAPHICS NEXT DIAGNOSTIC PROPOSED, NOT INSTALLED:
Bounded followup finds native q307_dizzy PLAYERpostprocess effect0/instance0,
performer2049=#player, playedonce3.551s into q30708section6. Finite40.0625s,
no loops, unusual colorgradebegin45s; not proven enginebug. No explicitlater
kill in localscene is NOT missingcleanup proof. Event has NOsavefield; do not
transfer risinglight save0 reasoning. Adjacent dizzy_wakeup24s normaltrackends
doesnotestablish enginehandling. Testable candidate, not diagnosis.
NEXT requires USERAPPROVAL: separatelyreversible single-effect suppression A/B;
no build/install yet. Mustcontinuousreplay from Auto16(level48,22:47:33,12Oct,
LeaveViktor) beforeeffectstart. Auto18 reloadalreadysuppressesbug, falsecontrol.
No forcedglobalFX/weatherreset/cachedeletion/settingschange/autosave-reload.
See research/graphics_investigation_20261013/next_diagnostic.json.
PA4firstfullhandoff+HP150tracepassed; usercamera/spawnPASS unchanged.

Latest2026-10-13 PA4 USER SPAWN/CAMERA PASS; GRAPHICS ONSET REVISED:
USER says post-ending respawn and camera fixed/working as expected. Record live
spawn+camera PASS in research/pre_alpha_camera_pa4/live_result_20261013.json;
no new getter supplied, so exactfacts/fullprep/newsave-reload/death/fullalpha NOT
inferred. No repeatedcamera test needed. InstalledPA4/pinned artifacts unchanged.
Graphics: USER now locates onset AFTER Vstands up and walks withMisty towardcar,
persists afterending; creditsHOLOCALLS UNAFFECTED. Saving/reloading into thatscene
SUPPRESSES visualbug. This supersedes finalcrowdshot-only onset assumption and
previous interpretation of creditscreenshot. Bothoptionsdumps remain faulty-state
samples. Focus continuous q307_08_misty transition vs reload-rebuilt state, not
assumed corruptshadercache. Native source has node1013 PLAY q307_light_animated
on q307_misty_rising entity withsave0. Sourceauditcorrects timing: section229,
BEFORE standup choice18; local8m light0->350 over180s/nonloop, notglobalpostprocess.
save0 not reloadproof. See graphics_investigation_20261013/native/misty_walk_onset_assessment.json.
NOT confirmedcause or permission to patch/stop it. Runtime/settings/saves/cache
unchanged; no autosave/reloadautomation. Graphics unresolved separately.
LATEST tracecorroboration: first15:32camera farfromV -> oneactivation -> alignment;
15:33:35 all6handoffflags1/profileComplete true/fault0, HPstat/pool150 at15:33:30.
Second15:50camera works but closedwhileprofilepending; notsecondfullpreppass.
Frozen3logs+live_trace_result_20261013.json in research/pre_alpha_camera_pa4;
no completedsave/reload or graphicshealth inferred. No repeatedcamera test.

Latest2026-10-13 GRAPHICS ONSET CLARIFIED BY USER:
Normal before Misty crowd/haze; consistently starts at that scene after game/PC
restarts. BOTH GameOptions dumps were at broken scene, NOT healthy/broken A/B.
No need repeat Auto16 baseline just to establish user's already-reported normal
before state. Prioritize scene-triggered state/render/resource interaction;
not proof of shader corruption or exclusion of repeatable renderer/driver issue.
Middle stock exposure02-12 now extracted to NEW workspace evidence; scalars
range0.65-1.15, only exposure+loopmarker tracks. No nativeFX patch justified.
Installed49REDS audit finds no admitted globalvisual/time/Johnny/PA4 action during
normal q307active crowd; preending callbacks do exist, so not whole-mod inertproof.
Bounded source pass complete: SH11on65.1s, finalcamera/exposure13at91s,
SH2_A+SH11off97.181s, sectionends99.433s. No missingcleanup established.
See graphics_investigation_20261013/onset_followup.json and native/scene_onset_assessment.json.
Cause stillunconfirmed; no runtime/config/cache/save writes.
Clarification pending whether fault ends with shot or remains in credits/map.
PA4 camera live test remains deferred by user.

Latest2026-10-13 GRAPHICS INVESTIGATION; NO CAUSE/FIX CONFIRMED:
USER defers PA4 camera test, requests graphics investigation now. Gameclosed;
runtime/saves/settings/drivers/caches unchanged, no launch or pinned-main reruns.
Two CET dumps11:36/13:15:15: GI/shadows/eye-adaptation/tonemapping enabled,
forcedexposure -1/-1/false; saved HDRoff/gamma1/RT/PT/DLSSDoff/DLSSAutoTransformer.
Only logged option difference RTXDIAnalyticLightCount99->124. No recent shader
failure in available logs; old OOM and recurring RHToccluder warnings not causeproof.
616-resource mod has no shader/material/texture/LUT/env resources. MistyLighting
normal activation requires completedTower, cannot explain precompletioncrowd
via its normal runtime path. Stock q307crowd exposure13 has EXPLICIT STOP at
scene embeddedquestnode8594 (play0); VFX-only scan missed it. Effect13scale0.9;
do NOT claim missingcleanup or patch it on present evidence. Runtimeexecution
unmeasured. 67otherarchive metadata audit no confirmedglobalrenderer culprit.
Evidence+frozen2logs/settings: research/graphics_investigation_20261013/assessment.json.
Diagnosis unresolved; no speculative cachedelete/settingsreset/driverreplacement.
LATER minimal comparison: coldlaunch Auto16 level48 22:47:33,12.10.2026,
LeaveViktor; inspect clinic/world/map WITHOUT progressing toMisty. Compare Auto18
level48 13:16:51,13.10.2026 aftercrowd ifneeded; same settings. Auto16 stillinside
q307, not cleanpreTowercontrol. User history-only question pending (earliersaves
affected?). No immediate playtest demanded. PA4installed/livepending unchanged.

Latest2026-10-13T17:57Z PA4 SCOPED CAMERA HANDBACK INSTALLED; LIVE PENDING:
USER bothblendresetcommandsFAILED, rebootdidnotfixgraphics; requests camera
investigation+implementationFIRST, shaderdeferred. Nativeq307boardALREADYcuts
creditsphase onskip; allfivecreditsscenes selectexternalcameras(blendinonly).
Staleselectedexternalcamera is supportedHYPOTHESIS, notprovenenginecause.
PA3controlcheckdefinitelylackedactiveviewvalidation; sceneCameraEnabledtrue
andplayerScene=false NOTownershipproof. IFPlogreturnednativeatPA3release,
notimplicated/disabled. PA4onlyArrivalreds+CETinit2backed-upreplacements;
archive/allother51packagefilesbyteidentical, no graph/shader/settingschanges.
AfterAuthorized/creditsclosed/CoverReleased/H10/Tier1/safelocalpossession,
ifmisaligned andvalidFPPnearV: markPTFRPA4_CameraRequest1 THEN nativeFPP.Activate
(0,false)ONCE. No highpriority/globalSceneCameradisable/possessionreset, no failed
blendcommands. Fourconsecutivemeasuredactive/FPPalignment samples->CameraAligned1
thenControlReady1; fresh8samplesafterPrepared->Reveal. Requestpersistencemodel
preventsreplay; actualnativeefficacy/mouseinput/savepersistenceNOTverified.
Alreadyalignedskipsactivation(request0/aligned1valid). Badtransform waits/faults
underunchangednative60/180swatchdogs; no repeatedactivation orsave/reloadautomation.
Actual53packagehashes+ValidateRollbackPASS;597protectedentriesunchanged including
185savefiles+5cachefiles. CLI/fullSCCEquipmentEx/readback,34artifact/model/LuaJIT
checks(64admissioncases/20mutants),38deploycases/58checksPASS. Firsttestharness
mutantmissedduplicateStatusanchor; fixedharness, successfulfullrerun. Initial
sandboxjunctionfixturedenied; fullunsandboxedworkspacefixturererunPASS.
Candidateprealpha/camera_pa4/build/pa4_02 BuildSHA
8CD6316A136BC46F5BE040C40D9886F3EED612FA9DF045C24A8D8A1A343E54FD.
PA4sources/build/tools/testmains/reports/receiptsPINNED; pa4_01supersededpreserved.
RecoveryFIRSTprealpha/camera_pa4/tools/deploy.ps1 ValidateRollback/Rollbackwith
recovery/pre_alpha_camera_pa4_01, THENPA3, THENPA2/PA1ifneeded.
NEWexactusefulfixture USERforcedAutoSave18 level48 13:16:51,13.10.2026 AFTERcrowd;
userconfirmscreditsreplay, metadatastillWalkwithMisty. Readonlyfactsq307active1,
2079/killed/cutsceneStart/load/shot11clean1; done/finished/PA2factsABSENT(notlive0).
SavSHA7F6A9D621BAEAC273AF83C8289479876808645365E69BF2B377D67515EAD2D37.
3filebyteexactbackup+failedPA3/CET/IFPlogsfrozenunder
research/pre_alpha_camera_pa4/live_pa3_and_checkpoint; activeoriginaluntouched.
NEXTcoldlaunchAuto18, skipcredits,closemenus/holster, verifyactualmouse-look/walk
atH10. Ifstuck BEFOREreload print(GetMod("PTFR_PreAlpha").Camera()) andStatus().
NoTerry/Mistyreplay/manualreset/gigStartneeded. Fullhandoffall1/fault0 pending.
Manual23readonlyfactsControlReady1/DR13/FreeRoam1 but Finishedabsent; priorreload
lateEndingTestfalse remainsseparateunresolvedadmissionissue, NOTfixedbyPA4.
Shaderissueexplicitlydeferred. Seedocs/pre_alpha_clean_run.md currenttopsection.

Latest2026-10-13 PA3 USER CAMERA FAILURE + CLOSER CHECKPOINT PRESERVED:
USER skippedcredits, cameraonlystuck; saved/reloaded, camerarecovered and H10TP
confirmed. No manualArrivalcommand; automatictrace captures11:38:04cover1/tier1/1,
11:38:05control1/activatedtrue, fault0. Preparation remained0, profilequeued with
combat/menu gates. Reload11:38:41 then lateEndingTestfalse/activatedfalse through
lastsample; do notautomate save/reload before auditing admission persistence.
camera-enabled=true before/after is NOT ownership evidence. PA3blackoutorder and
TP pass thistrace; actualcamera/fullhandoff stillFAIL/unresolved. Graphicsdump
at11:36:00 exists, no shaderdiagnosis/fix. USER prefers camerareset, asks preMisty
crowd checkpoint; automatic save/reload NOT approved/installed.
Gameclosed. Active save metadata inspected: closest existing AutoSave-16,
level48,22:47:33,12.10.2026,LeaveViktor/q307_viktor_start. Screenshot clinicexit
stairs; BEFORE Mistyencounter, NOT immediatelybeforefinalcrowdshot. Read-only
parse q307active/2079/mainkilled/ep1killed1; done/finished/cutscene/PA2facts absent
(absence not livezero). Byte-exact3filebackup made ONLY workspace
recovery/pre_misty_checkpoint_20261013/AutoSave-16; hashes+limitations checkpoint.json.
SavSHA51EE74B3EF3CB7872A27AD2C8619FD05BF7B5AB53FB9A84BFA0113555F012F69.
Originalsave/runtime/cache untouched. No exactscene-state fabrication or new
in-gamecheckpoint. Asyncuserchoice earliercheckpoint vs exactcrowd pending.
Targetednativecamera candidate research ONLY; NO PA4/reset patch installed.

Latest2026-10-13T12:59Z PA3 HANDOFF-ONLY REPAIR INSTALLED; LIVE PENDING:
USER prioritizes handoff, defers shader issue. PA2 trace strongly supports native
blackout/readiness self-block; exact engine internal cause not instrumented.
PA3 changes ONLY final_boards graph and Arrival observer: unconditional native
fade-in0.5s -> settle1s -> Tier1 -> PTFRPA3_CoverReleased1 BEFORE readiness waits.
Existing control predicate and60s/180s watchdogs unchanged; preparation is now
VISIBLE, success no secondfade. All83PA2nodepayloads kept,4nodes added; exact
7added/3removed edges,615of616archive resources byte-identical. No forcedfacts,
stateclear/save/reload, ending-scene/shader/cache/settings changes or migration.
Observer exposes gate reason, fixes stale waiting-after-fault status. API/class
and PA2facts retained; Arrival label PA3, unchanged Entry/CET may still sayPA2.
Gameclosed UNSANDBOXED2backed-up replacements/0adds;53actualhashes/rollback
validation PASS;576protected entries unchanged incl164savefiles+5cachefiles.
OriginalManual10SHA62742BF7... unchanged. HP150/Body3/Relic/perks/JV1/gig scripts
unchanged. Build prealpha/handoff_pa3/build/pa3_01 SHA
AAC05EBBED94A72B8B7AAD03CE9EC8033483691E574EE80D681287B9899228AC.
CLI+fullSCC EquipmentEx/readback,40artifact/regression/model checks,35deployment
cases/55checks PASS, not live proof. Initial fixture harness had malformed-count
test using3of2files; fixed to1of2, fresh fullsuite PASS; prior evidence preserved.
PA3source/build/tools/test mains/reports/receipts PINNED; no installedmain reruns.
Recovery FIRST prealpha/handoff_pa3/tools/deploy.ps1 ValidateRollback/Rollback
with recovery/pre_alpha_handoff_pa3_01; THEN oldPA2 recovery, THEN PA1 if needed.
Evidence research/pre_alpha_handoff_pa3/assessment.json. NEXT originalManual10
level48,22:04:51,20.09.2026,MeetViktor; finish ending/skipRoguecredits. Briefcovered
teleport thenvisibleH10 preparation, menusclosed/holstered. Arrival expects
1/1/1/1/1/1 coverReleased1 fault0; verifyactualwalk/look/HP150 thenNEWsaveaway/
reload norepeat. No failedPA2postsnapshot migration. Shader investigation deferred.

Latest2026-10-13 PA2 LIVE HANDOFF FAILED; NEXT TEST SUSPENDED:
USER stillstuck, visualcorruption begins Misty crowdscene and later map.
Frozen currentrun logs: research/pre_alpha_transition/live_failure_20261013.
Actualcompile PASS08:17:28; all53installedhashes stillmatch PA2candidate03.
Trace H10position at08:33:12, Teleported1at08:33:18; tier/high5/5 throughout
readinesswait until08:34:18. At08:34:19 Fault1/failurefadein coincides tier1/5,
then08:34:20 tier1/1. Control/prepared/reveal/finished stay0; coordinatorstopped.
Strong evidence nativeblackout/readiness ordering self-blocks; NOT fixed by
longertimeout orforcedControlReady. Need endnativefade beforeTier1 readiness,
or separatelyverified visualonlycover. Exactnativeinternalcause notinstrumented.
Laterpositionmoves~2.28m; not proof camera/inputworks. USER clarificationpending.
Finalwaitingmessage stale afterfault; watchdogalreadyfinished. StaleMistyjournal
consistent withrestorationneveractivated. Shader/cache/GPU/othermodcause UNKNOWN;
Mistyvisualsymptomreported BEFORE PA2branch. Do notblamecamera-enabled=true alone,
deletecaches, forcefacts or broad-disablemods. NoPA3patchinstalledthisturn; PA2
remainsinstalledandpinned. Gamealreadyclosed, noextraendingreplay/testneedednow.
Changes onlyread-onlyinspection +frozen evidence/documentation; no runtime/save/
cache/settingswrites. Next newrevision blackfade ordering +separaterenderdiagnosis.

Latest2026-10-13T03:34Z PA2 CREDITS/H10 HANDOFF REPAIR INSTALLED, LIVE PENDING:
USER PA1 run skipped credits during Rogue, stuck at Afterlife/unable to move;
nerf effective. USER explains old completed Manual11 clinic location followed
Viktor credits segment and recalls reload helping. Exact scene/control cause
NOT instrumented/proven. Native q307 board already cuts its credits scene phase;
do not claim missing cut as confirmed. PA1 safe-before-arrival gate insufficient.
PA2 preserves all old graph payloads and splices only2final_boards edges after
existing closed-credits/genuineTower guard: native fade/scoped cleanup/H10 player
teleport(no heal/no globalfasttravel) thenTier1 forceEmptyHandsfalse. Observer
requires H10position+Tier1/HighLevel1/noScene/noMovement/workspot/dialogue/phone
locks before publishing FreeRoamActive/DR13, then existing accepted FullNerf and
initial nativegig admission, then rechecks controls and fades in. Native60s/180s
watchdogs uncover/report fault instead of endless blackout;180s is maximum to
allow serial refunds, not fixeddelay. No forcedsave/reload/PONR, no factresets.
This is a fade-covered retained-session transition, not an engine loading UI.
Gameclosed UNSANDBOXED4replacements/0adds,53actual packagehashes PASS,
568protected entries unchanged including158savefiles+5cachefiles. Manual10hash
62742BF7... unchanged. No new savefoldercleanup. HP150/Body3/Relic/perk/JV1/native
gig content and other615archive resources unchanged. Baseline PA1 kept pinned.
Build prealpha/transition/build/pa2_candidate_03 SHA F3B5F705B51F65E1533822F076BFDEE45C6E06D4E9E41F2D886950F3442A568E.
CLI+fullSCC/readback,71artifact/source/LuaJIT/model checks,39deploymentcases/
67checks PASS. Actual ending/fade/player input/streaming/reload LIVE UNVERIFIED.
Recovery FIRST prealpha/transition/tools/deploy.ps1 ValidateRollback/Rollback
with recovery/pre_alpha_transition_pa2_01, before older consolidated PA1 recovery.
PA2 source/build/tools/test mains/receipts now PINNED; do not rerun installed
builders/tests or reuse old per-version recovery. Evidence assessment under
research/pre_alpha_transition, install receipt in exact recoverydir; read-only
bounded CET trace uses PTFR_PreAlpha Arrival()/Status(). NEXT coldlaunch ORIGINAL
ManualSave-10 level48,22:04:51,20.09.2026,MeetViktor/cabride_start; finish ending,
skip during Rogue again; verify H10foot/camera/HUD/HP150 then NEWsave away/reload
no repeat teleport/refund. No Manual11/already-postcredits save migration.
If stalled send Arrival/Status/Profile; no oldStartAll/forcedfacts/reload workaround
before capturing diagnostic. Broadsidejobs/otheractivity/housing remain pending.

Latest2026-10-13T02:28Z PA1 CLEAN LATE-ENDING REHEARSAL INSTALLED, LIVE PENDING:
User explicitly requested one consolidated mod, recoverable game-mod/save-folder
cleanup, a Things Done Changed source save, and the new postcredits H10 spawn.
ONE active TowerContinued_PreAlpha.archive+XL, PTFR_PreAlpha script/CET folders,
owned tweak.52retained archives->616resources/427injections, byte-exact except
reviewed phone support wrapper.240oldPTFRunits+49savefolders recoverably moved;
only ManualSave-10 active(level48,22:04:51,20.09.2026,MeetViktor/cabride_start).
Original savSHA62742BF7E77451D5498AB724EEECD10CD2E35AFEF3442361D67A29BBDD486B3B.
Recovery: recovery/pre_alpha_clean_20261013T022533186Z incl retained10backup.
Postaudit53installed/299protected/2479archived hashes PASS; no save-byte/cache
edits or permanent deletion, unrelated mods/frameworks preserved. Only recovery
prealpha/tools/deploy.ps1 -Mode Restore -RecoveryRoot exactdir; old perversion
rollback/tools no longer apply to consolidated layout. Installed sources/build/
tools/reports now PINNED, no reruns against changed installation.
Entry arms in actual q307active2079 beforecompletion, uses explicit DEVELOPMENT
incomplete-as-unstarted after credits (NOT certified2077history). Also implements
separate genuinepreTower72snapshot/freeze/certified dispatch, still liveuntested.
Postcredits Completed+safe -> ONE original H10 streetspawn native TeleportToNode
(-1432.13672,1261.04565,23.0654984) -> observedarrival -> existing FullNerf profile
HP150/Body3/Relic/implantperks -> current72 nativegig autodispatch. Saved stage
prevents repeat arrival after ordinary reload/death; no entitlement/autosave.
Phone removes16unsupported historical counter-equality checks from admission,
keeps actual transient/setup/legacy/lifetime checks and original reset cleanup.
No native counter reset. All native gameplay/calls/reward/tiers retained. Profile
clone adds3readonly getters only; physicalR3.3 unchanged. Retired old pilots/
ActivityState auto/CETinterlocks; OnlyPain stays dormant. Broad sidejobs/other
activity/housing not newly implemented; fullalpha still pending.
CLI+fullSCC EquipmentEx+decompiledbody readback PASS;16entry/99LuaJIT/893phone/
1087arrivalmodels and24deploymentfixtures PASS, not live proof. Current build
prealpha/build/20261013T021845834Z; manifestSHA11BFC077C181A0B2BA5FACA10B105C92D1D4AEE81692BDF72BAEBC034F738FA3.
Evidence research/pre_alpha_clean/install_audit.json; docs/pre_alpha_clean_run.md.
NEXT coldlaunch onlyManual10, verify lateEndingTest=true, finish normalending/
credits, no oldStartAll/factreset commands. Check H10street foot/camera/HUD,
profileautomatic, gigsfilter/call/journal, NEWsave awayfromH10/reload norepeat.
Initial smoke needn't complete gigs. TruepreTowerhistory/fullalpha tests later.

Latest2026-10-12 USER INTEGRATED ALPHA ROADMAP + HOUSING REVISION:
Alpha must include all approved gigs, sidejobs and compatible other activity
categories, all previously restored world/services, accepted nerf profile and
full deployment from a genuine pre-ending world. Current gig-only U9 is one
workstream, not the whole alpha. Actual preTower history/auto dispatch pending;
no ending replay until full entry criteria ready. See ROADMAP Phase10 and
docs/alpha_playtest_tasks.md. Nerf stays DONE; alpha adds integration regression.
NEW arrival requirement: after normal Tower/credits cleanup, one-time safe
street placement in front of H10 in retained2079 session; no ownership grant or
repeat teleport on load/death. Planning only, NOT implemented/installed here.
LATEST housing rule: ALL previously owned ordinary apartments lose ownership
after Tower and require repurchase. H10 costs €$25,000 (2x mod-defined €$12,500
reference price); other previously owned ordinary apartments use normal purchase
prices, with no increase. Neverowned normal purchase rules unchanged;
relationship homes not sold/outcomes preserved.
H10 is the starting home, not an ordinary purchase listing; do not use the
renovation fee as its price. Housing runtime NOT implemented; no runtime/save writes.
Readonly baseline search: ManualSave17 level48 21:02:06 25.09.2026 SHA035EED1F...
has Towercomplete/no recorded sampled legacy ownership, BUT historical phone
counters differ and currentU9 idle guard can refuse. Manual20 stayswithdrawn;
Manual17 is development candidate, NOT preendingalpha fixture/liveadmissionproof.
Evidence research/gig_restoration/u9_baseline_save_search_20261012.json.

Latest2026-10-12 EVENING U9 LIVE STARTUP BLOCKED, baseline correction:
Enginecompile PASS; CETregisteredtrue/preflight11of11/Probe delivered/faultempty.
Recorded StartAll attempts queued0. 20:35:33 had60legacyrefusals+12terminal;
20:36:35 had53phoneIdle refusals+10entryunsafe+9terminal, USER says that phone
attempt was an extremelyoldsave, NOT current blocker. 20:37:44 againlegacyfalse.
NEW readonly ManualSave20 audit(SHA0E531F...unchanged) finds
PTFRB5_TierRequest1,PTFRB5_H1_Started1,PTFRB5_H7_Started1/OwnerFinished1.
Thus prior Manual20 recommendation WITHDRAWN: pre-U6/U7 alone insufficient,
olderB5tier/uncompletedH1 state conflicts. No factreset,installchange or savewrite.
Checklist top corrected. NEXT find existing postTower baseline before all oldgig
restoration tests; endingreplay only fallback from pre-old-test preTower save.
Replayingending does not byitself clear modownership. Productionauto stillnot
connected; don't demand endingalpha now. User mayclose without newsave/testing.

Latest2026-10-13T00:24Z: U9 ALL72 CAST-WHITELISTED GIG DEVELOPMENT BATCH INSTALLED
gameclosed UNSANDBOXED:12additions,0replacements;2575protectedfiles unchanged,
including152savefolderfiles. No save/cachewrites; HP150/Body3/Relic/JV1 unchanged.
72originalentry wrappers DIRECT original gameplay/scenes/rewards,66nativecredit,
25earnedtiers,94mapbranches,11prestatecompanions. Eight originalfixercontrollers,
one originalinterrupt/resetservice; scopedcleanup omits nonfixers and unrelated
EP1globalreset handshake (explicit adaptation, not fullglobalparity proof).
One sharedEP1late-tiergate. Native gangretaliation:6independentlyadmitted flows,
1cancelowner,11ownedselectors,3excludedstartupedgescut,13whitelistedwriters.
No historicalpendinggang reset/consumption; matching safe dependency required.
Manual20 maelstrom/tygerpending can REFUSE Heisenberg/CatchTyger/Bloodsport before
queuing; not autoretry. Alreadycompleted affected gigs remain completed.
User excludes sidejobs/NCPD/carcontracts/otherworldactivity and accepts NO devsave
migration. Production preTower captured-unstarted auto ADMISSION NOT CONNECTED.
All72 implemented, NOT all72simultaneouslyadmitted or LIVEVERIFIED. Native tiers,
terminal/progressed state, oldowners and pendingconsequences still govern entry.
Combined CLI+fullSCC EquipmentEx/newU9body+bytecode readback PASS; one known old
ActivityDefinition.FactNames code-decompiler gap explicitly isolated, unchanged.
1799nativepayloads/326graphs/73maininputs/185negativecontrols,174LuaJIT interlock
cases and13deploymentnegative/recoverycases PASS. Initial sandbox fixture could
not createjunction; full unsandboxed WORKSPACEfixture rerun PASS. No liveU9test.
CET11legacyentryhooks +globaldefaultfalse Ready/Probe guard additive, no oldscript
replacement; harmlessProbe NOT proof ofall11callbackdelivery. Do not mixoldStart.
PIN allU9component/combined mains/source/build/tests/receipts. No builder/test
reruns afterinstall. Current recovery ONLY tools/deploy_gig_batch_u9.ps1
ValidateRollback/Rollback; recoverably moves12adds, then load PRE-U9baseline.
Evidence research/gig_restoration/gig_batch_u9/{manifest,tests,deployment_tests,
install_receipt,assessment}.json. ManifestSHA60FDB58AD3778DF50E3E18714C02543CB5F150887DF787E36E5862ED3F558778.
NEXT deferred playtest docs/gig_batch_u9_playtest_tasks.md; coldlaunch ORIGINAL
ManualSave-20 level49 16:32:18 11.10.2026 SHA0E531F... (NOT Manual21/U7/U8save).
Runtime also checks olderB5/B7tier/pilotowners; baseline is candidate, not proof
allguards pass. NativeGigsU9.StartAll(DISPOSABLE_SAVE) once, closemenus15s, read
InspectAll/TierStatus/DependencyStatus +GigPhoneU9.Inspect +CETguard Status.
Gigsmapfilter ON; journal may wait approach/briefing. Representativeperfixer,
calls/gameplay/reward/credit/cleanup/newsave-reload/retaliation/Johnny/HPchecks
documented; no needplay72 orreplayTower now. Finalfixerrewardsidejobs deferred.

Latest2026-10-12 USER scope: next batch ALL WHITELISTED GIGS ONLY. No sidejobs,
vehiclecontracts,NCPD,cyberpsychos/otherworldmissions. User approves parallel
subagents and postpones broader gameplay to nextweek. No need development-save
migration/backcompat; retain duplicate-owner/reward protection, clean baseline.
U8 LifesWork finalcleanup USER PASS: finished1/root3/creditDone1/Heywood2/fault0;
previousreload completion/credit persistence passed, no extra count. No need
repeat old pilot checks before offline implementation. U9 under construction,
NOT yet installed; docs/gig_batch_u9_playtest_tasks.md is draft until receipt.
Do not mark unplayed gigs verified. Existing runtime/saves untouched so far.

Latest2026-10-12: U8 Life'sWork USER Inspect before/afterreload identical:
ready/request/entered/finished1/1/1/0,root3,terminaltrue,creditDone1,Heywood2,
fault0. Completion/nativefixercredit persistence PASS; cleanup NOT yetacknowledged.
entrySafefalse expected aftercompletion. Original openworld root/2 node32 waits
ONE GAMEDAY from debriefjoin58, then33 requires outside initialvolume, native
device/spawncleanup and43 outside debriefscene before output/OwnerFinished.
Consistent with delayedcleanup, not proof of current serializedwaitingnode.
No extra count on reportedreload; calls/moneypayout not independently established
bygetter. Evidence native_heywood_u8_reinstall_1/live_lifes_work_result_20261012.json.
NEXT current completed-Life'sWork save, leavearea/skip24gamehours/closemenus then
Inspect again; NO restart/StartAllrepeat/replay/forcedfacts. PreserveManual21.
Docs/evidence only, no runtime/save/cache changes; otherU8gigs/tiers pending.

Latest2026-10-12: U8 startup USER PASS after exact reinstatement: "done test,
no crash, able to see these" + screenshotd34cc883 shows visible green gigicons.
Installed4hashes still match reinstallreceipt. No per-gig names/owners inferred
from unlabelled icons, no Inspect data supplied. Does not prove allseven gameplay,
nativecredit/tiers/cleanup/persistence or priorOOMcause. Record separate
native_heywood_u8_reinstall_1/live_startup_result_20261012.json; old evidencepinned.
NEXT continue current session, NO restart/StartAllrepeat needed: test LifesWork
ifavailable, Padrebrief/journal/objectives/completion/payout/debrief, then
NativeHeywoodU8.Inspect("sts_hey_gle_06"). Later separateNEWsave/reload after
cleanup; preserve Manual21. This turn docs/results ONLY, no installation change.

Latest2026-10-12T22:14Z: USER attributes crash to PC memory exhaustion and explicitly
requests SAME U8 back, superseding withdrawal/no-unchanged-reinstall instruction.
Exact U8 REINSTALLED gameclosed UNSANDBOXED from verified recovery copies:
3adds/1newbacked-up B7replacement,2364protected unchanged,4actualhashes and
ValidateRollback PASS. NO build/test-main reruns or source/gameplay changes;
original tests/receipts/withdrawal/crash evidence PINNED unchanged. No directsave/
cache/settings changes. U7/U4/JV1/HP150 dependency hashes and Manual21 unchanged.
New receipt native_heywood_u8_reinstall_1/install_receipt.json. CURRENT recovery
ONLY tools/reinstall_native_heywood_u8.ps1 -Mode Rollback; old U8rollback already
consumed and historical. Newreinstaller/receipt PINNED. User memory attribution
is not independently verified cause/resolution or a new livepass; no baseline
success inferred. NEXT coldlaunch ManualSave-21(level49,16:47:20 12.10.2026),
ifloads U8StartAll(DISPOSABLE_SAVE) once, closeCET/menus15s thenInspectAll.
No U7/U4/U6Start or B7batch. Resume original U8 test, stocktiers retained; stop
and inspect new crash ifload fails. Allseven newgig livechecks still pending.

Latest2026-10-12T21:58Z: U8 WITHDRAWN after USER ManualSave21 load exits.
Two localcrashes17:53:36/17:55:48 BOTH Assert D3D12MA:Outofmemory,
gpuApiDX12Error.cpp136,Loadingworld. Actualredscriptcompile PASS; all24U8XLentries
merged. Not proof of a questbranch crash or fullVRAMcapacity: lastreportRTX3070
total8018MB/used3300MB,RTfalse. U8causality UNKNOWN pending same-save A/B.
No unrelated protected runtimeasset changes sinceinstall. Manual21 SHA2467361D...
unchanged before/afterrecovery. Frozen7logs under native_heywood_u8_crash; assessment
distinguishes allocatorassertion from cause. No settings/driver/othermod changes.
Existing pinned deploy_native_heywood_u8.ps1 ValidateRollback then Rollback used
gameclosed UNSANDBOXED;3U8adds moved recoverably, B7previousdispatcher restored;
2340protected unchanged,4recoveryhashes/U4/U7/HPcheckpointfix hashes PASS.
Recovery dir native_heywood_u8/recoverable_20261012T215834353Z; no permanentdeletion,
directsave/cachewrites. U8source/build/tests/originalassessment/receipt PINNED;
do not rerun/reinstall U8 unchanged. It is NOT currently installed or livepassed.
NEXT ONE coldlaunch unchanged ManualSave-21(level49,16:47:20 12.10.2026), same
settings, NO commands/Start/batch/save; wait~30s ifloaded thenclose/report. Ifcrash
stop, inspectnewreport. Baselineload needed before speculative U8patches/graphics
changes. Previous U8seven-gig testing below is SUSPENDED. U7normalcompletion/
cleanup/reload and HPfix passes remain valid. Otherfamilies/production pending.

Latest2026-10-12T21:07Z: USER continue -> U8 NATIVE HEYWOOD EXPANSION INSTALLED
gameclosed UNSANDBOXED:3adds(archive/XL/reds),1backed-up B7dispatcher replacement;
2300protected unchanged,actual4hashes/backup/ValidateRollback PASS. Seven new
whitelisted entries: LifesWork,FifthColumn,TightLeash,OldFriends,EyeForEye,
LordGiveth,HotMerchandise. Original parent/prelude retained and DIRECT original
main/gameplay/scene/call/reward/cleanup refs; no original gameplay packed/changed.
Existing U7phone/support and U4Jeopardy untouched, no second initializer/contact.
24resources=7entry+6nativecredit+4earnedtiers+7nativePOIbranch slices. Original
credit success/failure routing preserved; HotMerch watcher14 has NO outgoing
counteredge in inspected loop, no compensation. Tiers4/7/10/11 retain stock
delays/messages/content/additivefacts/q103guard; only untouched branches admitted.
Selected mapleaf inputs rebased past foreign POIwrites; nativevisited/outcome/
discovery/outside checks kept. No excluded gig activation/credit/forcedtiers.
U8 explicit DEVELOPMENT incomplete-as-unstarted admission, NOT certifiedhistory.
Incomplete progressed runtime shape deferred for unsupported continuation, no
reset. Production history auto still pending. Ownedfacts/nativegraph progress
persist; no custompayout/rewardledger. Old B7 NEW Restore for7IDs disabled;
existing oldowners untouched; unfinishedlegacy/tierowners defer U8. Otherfixers
notexpanded; U7interrupt edgecases/finalreward/productionhistory/fullalpha pending.
Exactnode/edge/interface/rootmetadata checks,177guards/48mutants/20serialization
MODELS,24packedreadbacks/YAML/collision,CLI+fullSCC EquipmentEx/readback,
4filefixture7refusals PASS; new7 gameplay/markers/tiers/reload LIVEPENDING.
Evidence research/gig_restoration/native_heywood_u8/{manifest,tests,
deployment_tests,install_receipt,assessment}.json. PIN source/build/tests/mains/
receipts; NO reruns afterinstall. Recovery ONLY deploy_native_heywood_u8.ps1
for4currentfiles then PRE-U8save; old U4aggregate recovery historical on replaced
B7 until U8 recovered. ProfileHP150 checkpointfix/JV1/U7/U4/U3 bytes unchanged.
NEXT docs/native_support_u7_check.md NEW TOP U8section: coldlaunch ManualSave-21,
level49,16:47:20 12.10.2026, StartAll(DISPOSABLE_SAVE) once, closemenus15s then
InspectAll/TierStatus, Gigsfilteron. Test LifesWork if accepted; no U7/U4/U6Start/
B7batch/forcedfacts. Later tiers may remain locked under stock counts+whitelist.

Latest2026-10-12: U7 USER normal Jeopardy completion/debrief/credit/cleanup and
follow-up save/reload PASS; repeatedInspect creditDone/base/current1/0/1,
root/start/done/OwnerFinished3/1/1/1, phone3/3,setup0/0,interrupt/forceReset0/0.
Read-only ManualSave-21 corroborates OwnerFinished1,CreditDone1,heycount1,phone3/3;
metadata timestamp16:47:20 12.10.2026,level49,savSHA2467361D... unchanged afterread.
Evidence u7_completion_audit/manual21_facts.json and native_support_u7/
live_result_20261012_completion.json. No arbitrary serializedowner proof; full
interrupt/recovery routes untested. USER HP R3.3 checkpoint fix confirmed; separate
profile_hp_reload_r3_3/live_result_20261012.json. No repeat tests required for those
passed checks. Old pinned reports retain historical livepending status.

Latest2026-10-12 HP RELOAD R3.3 INSTALLED gameclosed UNSANDBOXED: ONE backed-up
ProfilePhysical.reds replacement,0additions,2259protectedfiles unchanged;
actualhash/backup/ValidateRollback PASS. USER Jeopardy completed + postcompletion
Padre call PASS after death/checkpointreload; no U7credit/cleanup/newsavereload
getter yet, so those remain pending. User reported HP reverted after checkpoint.
Source-confirmed old first-unsaved-HP gate used BodyPolicy.Safe (combat/weapons/
phonecontent block). Consistent with symptom, not an instrumented rootcause proof.
R3.3 only separates alreadyapproved HP readiness: live attached local player,
nonreplacer, defined stats/pools, positive valid maxima. No combat/holster/phone
gate for cap; death/loading pause pending-clamp budget. Existing optin/profile/
stage/mode guards, own unsaved modifier and negative single-request clamp intact.
No persistent schema, FullNerf/migration/refund/Body3/Relic/stamina/profile/gig/
U7/phone/save/cache changes. Existing restorehook creates new physical instance.
CLI+fullSCC EquipmentEx/readback,exactdelta+oldinvariants,384admission/768readiness/
64feedback-reload MODELS and6negative deploymentcases PASS; enginecheckpoint
test PENDING. Evidence research/restriction_profiles/profile_hp_reload_r3_3;
repair source build/ProfileHpReloadR3_3/ProfilePhysical.reds. Old redscript source/
reports pinned; new installed main tools/reports also PINNED, no reruns.
Recovery ONLY tools/deploy_profile_hp_reload_r3_3.ps1 for this physicalscript;
originalR3aggregate recovery historical for replacedpath. No gameworld rollback.
NEXT docs/profile_hp_reload_r3_3_check.md: load kept completedJeopardysave IF saved,
otherwise normal alreadyHP-enabled postTowertestsave; no gig replay/Start. After
3sec gameplay measureHP150 withweaponallowed, then death/LoadLastCheckpoint and
Measure again. Ifwrong GetStatus, don't rerunrefunds. User may close afteroutput.
Optional U7Inspect from retained completedJeopardysave to verifycredit/cleanup.

Latest2026-10-12T19:30:42Z USER continue -> U7 NATIVE SUPPORT INSTALLED gameclosed
UNSANDBOXED:3additions(archive/XL/reds),1 backed-up U6script replacement;
2236protectedfiles unchanged,4actualhashes+backup+ValidateRollback PASS.
Four modowned resources: guarded entry, original initializer16node Padre-only
slice, original parent3node resetloop, original Jeopardy completioncredit slice.
Direct ORIGINAL Padre/interrupt/Padrecleanup phases/scenes untouched, not packed.
Initializer124 cleanupref/socket narrowed to Padre In42/Out42; other retained
payloads/edges original. Parent34 reference scoped; parent Input socket verified.
Native TERMINATING reset_out kills old controller before stock reset_in re-entry;
initial entry uses In1, no forcedcleanup. Shared native interrupt service manages
global phone restrictions/setup as stock; not zero global effects. Othercontacts
not started. Source-backed ending shutdown, idlebalanced and unusedU6/U4 admission;
not arbitrary saved-owner introspection. U6Start now refuses; existing U6owners
not migrated/cut, U7 refuses them. U6originalsource/archive/XL/receipts pinned.
Credit root2/4 native0->8(rey06finished>0)->3(hey_sts_counter+1) copied EXACT;
owned U4Started arms onebranch; extra ownCreditDone observation only. No payout
rewrite, compensation, wholecountloop or historicalcredit replay. U4gig unchanged.
Native earnedtiers/final rewards still separate (Manual20count0->1 belowfirst4).
Exactdelta/interface/native lifecycle checks,71entrycases/3graphmutants+badinput,
YAML/collision14709/packed4,CLI+fullSCC EquipmentEx/readback,4filefixture5refusals
PASS; gameplay/phoneinterrupt/recovery/credit/persistence LIVEPENDING. Evidence
research/gig_restoration/native_support_u7/{source_review,manifest,tests,
deployment_tests,install_receipt,assessment}.json. Recovery ONLY
tools/deploy_native_support_u7.ps1 for4currentfiles; U6aggregate recovery historical
whileits scriptreplaced. Reload original PRE-U6/U4save afterrecovery; cannotrewind
world/newsavecredit. PIN U7sources/builders/testmains/artifacts/receipts; no reruns.
No directsave/cachewrites, originalManual20 SHA0E531F... unchanged. U4/U3/U5/JV1/
HP150Body3Relic untouched. NEXT docs/native_support_u7_check.md: coldlaunch ORIGINAL
ManualSave-20(level49,16:32:18 11.10.2026), U7.Start(DISPOSABLE_SAVE), closemenus5s,
Inspect issued1/fault0, then U4.Start once and COMPLETE Jeopardy normally incl
Padrebrief/debrief/payout. Leavearea/Inspect creditDone1/base0/current1/root3/
done1/phoneidle/ownerFinished1 aftercleanup; separateNEWsave/reload checks no repeat.
No U6Start/batch/forcedfacts. Notallgigs/productionhistory/fullstockparity/alpha.

Latest2026-10-12T19:07:49Z: U6 NORMAL PADRE BRIEFING USER+TRACE PASS. USER saw
incoming popup, heard call and received text. Frozen188rows/175.812sec/one stable
session/0gettererrors: request consumed, queue serviced, IncomingCall->pickup
reject=false->StartCall->EndCall; start/end acknowledgements observed, counters
1/1->2/2 once, final shared setup idle/ended1/callActivefalse. Three same-frame
pickup callbacks are NOT three-call/duplicate-owner proof. Text after normal
call is stock routing. Jeopardy rootActive2/start1/finished0/Heywoodcount0/fault0.
Actual3U6 installed hashes and U5 logger match receipts. Evidence native_padre_u6/
live_result_20261012T190453Z.json + frozen trace SHA0D1CBB3F...; pinned assessment,
build/tests/receipts untouched, no main reruns/runtime install/fact/save/cache writes.
Normal briefing check CLOSED: no immediate completion/newsave/restart needed;
USER MAY CLOSEGAME, preserve original pre-U6 snapshot. U5 does not log U6ownfacts;
no direct serialized-owner/U6persistence proof. NEXT audit original shared phone
interruption/recovery and restore stock fixer credit before full completion test.
Otherfixers/rejection/interruption/U6reload/history/fullrollout still pending.

Latest2026-10-12T17:55:38Z USER continue -> U6 ORIGINAL PADRE CONTROLLER TRIAL
INSTALLED gameclosed UNSANDBOXED:3additions(wrapper archive/XL/reds),0replacements;
2213protected files unchanged,actual3hashes+ValidateRollback PASS. One7node entry
wrapper directly references ORIGINAL padre_holocall.questphase In1; original
controller/scene not copied/packed/edited. ArchiveXLnode5862 collisionchecked.
Original lifecycle source: base root106->109->107 TERMINATING output on
before_tomorrow Succeeded; q307root16->18->17 CUTS servicephase6 containing
initializer5. U5 trace showed unserviced request. Entry requires completedTower,
terminal before_tomorrow/native killedflags/debugreset0, unencounteredJeopardy,
idle balanced incoming/outgoing phone state; native counters preserved, not
forced1/1. Own Request/Permit/Issued/Fault one-shot tracking; epoch callback guard.
This is source-backed lifecycle admission, NOT arbitrary serialized-owner query;
othermods independently restarting initializers unsupported. No globalphone
initializer/reset or othercontact starts; shared interruption service NOT restored.
Customwrites only PTFRU6_Padre namespace; originalnativecontroller owns stock
protocol. U4/U3/U5/JV1/HP150Body3Relic and originalManual20bytes unchanged.
Exact wrapper/reference/guards/nativeparent audit,153entrybalance+one-shotmodel,
realYAML/packedreadback/collision,CLI+fullSCC EquipmentEx+readback,3filefixture/
4refusals PASS; livevoice/scene UI/dependency/interruption/persistence UNPROVEN.
Evidence research/gig_restoration/native_padre_u6/{manifest,tests,
deployment_tests,install_receipt,assessment}.json. Currentrecovery ONLY
tools/deploy_native_padre_u6.ps1 moves3U6filesrecoverably; reloadoriginalPRE-U6save,
not laterphoneowner save. Priorrevisions untouched. PIN U6 builder/test mains,
source/artifacts/receipts; no reruns afterinstall. No directsave/cachewrites.
NEXT docs/native_padre_u6_check.md: coldlaunch ORIGINAL ManualSave-20(level49,
16:32:18 11.10.2026), armexistingU5, NativePadreU6.Start(DISPOSABLE_SAVE), closeCET/
menus/holster5sec, Inspect expectsready/request/issued1/1/1 fault0. Then unchanged
NativeJeopardyU4.Start, approach/answer, wait40sec orfinishlongercall, stoptrace.
NO gigcompletion/newsave needed; usermaycloseafter. Issued!=call-success proof.
Stockfixercredit/globalphoneinterrupts/fullrollout/productionhistory stillpending.

Latest2026-10-12 U5 TRACE RESULT:260rows/254.65sec/manualstop/one stable session/
0gettererrors. USER no incoming call, yes text; pre-ending callpopup works per
USER (not separately traced). Original U4 entered19.808s; rey06start/rootActive
106.950s; Padre request+rejectable1 at107.023s, clears137.030s (30.006sec).
During31recorded request-window rows phoneEnabled/callingEnabled/availabletrue,
callActivefalse,shared setupactive/started/interrupted0;queue0,start/endcounts1/1
unchanged,start_done/rejected0. Strong evidence native incoming Padre controller
unresponsive/missing/stopped; exact serialized owner absence NOT proven. Matches
source30s unanswered fallback, not initial mute shortcut/user rejection.
At149.34s a SEPARATE outgoing Player->Padre PhoneSystem request occurs then8s
timeout; do not confuse with gig incoming call. Proves TriggerCall/timeout hooks
delivered at least once, not pickup or every pulse. Frozen trace SHA4F5238F5...,
actual installed U5hash still receiptmatch. Evidence padre_phone_u5/
live_result_20261012T173450Z.json and frozen live_trace; predecessor source/tests/
receipts unchanged. This audit workspace evidence/docs ONLY, no game install/
fact/save/cache writes. No more immediate test/completion/newsave needed; user
may CLOSEGAME. Next repair exact native shared Padre phone dependency with
lifetime/duplicate-owner checks, preserve native scene/UI/routing, no globalphone
reset or text workaround. Stock fixer credit/fullrollout still pending.

Latest2026-10-12T17:20:51Z: U4 USER startup/journal/written Padre briefing PASS:
entered1,rootActive2,rey_06_start1,done0. User heard NO Padre voice call. Screenshot
start_activate1/rejectable1 proves original prebrief scene entered; it did not take
initial mute shortcut. Stock scene273 waits30s,280 idle/content guard,286/284 clear
rejectable/request ->254 rejected_out ->native written brief. Fits symptom, NOT
proven cause/absent handler. Config fixer_briefs_and_debriefs=false, dialogue100.
U5 GETTER-ONLY diagnostic INSTALLED gameclosed UNSANDBOXED: ONE additive CET
PTFR_PadrePhoneU5/init.lua;2189protected files unchanged,hash+ValidateRollback PASS.
No native controller, phone/fact/quest/journal/reward changes, no save/cache writes.
ManualSave-20 original SHA0E531F... unchanged. U4/U3/JV1/profile unchanged.
Explicit Arm() records frame-change facts plus1s heartbeat, optional Observe
OnTriggerCall/OnPickupPhone/OnPhoneTimeoutRequest, public phone getters; Stop()/
Status()/Sample(). Stable hash+epoch on ticks/callbacks; abort load/rootloss,
UNKNOWN getter errors, bounded128events, disk failure disables; max5min. Not
armed automatically. Frame sampling may miss intraframe pulses; registration
return is NOT hook delivery proof.33LuaJIT cases+recoverablefixture4refusals PASS,
not engine proof. Native Padre controller/cleanup/scene extracted read-only.
Evidence research/gig_restoration/padre_phone_u5/{source_review,tests,
deployment_tests,install_receipt,assessment}.json. Recovery only new
tools/deploy_padre_phone_u5.ps1 moves logger recoverably, leaves traces/gameplay.
PIN installed U5 mains/source/tests/receipts; no reruns/overwrites. Next short
test docs/padre_phone_u5_check.md: coldlaunch ORIGINAL ManualSave-20(level49,
16:32:18 11.10.2026), NOT Jeopardy-started snapshot; Arm before U4 Start/approach,
answer if offered, wait40s then Stop. No completion/newsave needed; maycloseafter.
Do NOT duplicate/reset phone handlers from final zero facts. Stock fixer credit,
phone parity, production history admission/fullgig rollout still unfinished.

Latest2026-10-12: U4 ORIGINAL JEOPARDY PILOT INSTALLED gameclosed UNSANDBOXED:
3additions(wrapper archive/XL/reds),1backed-up B7 dispatcher replacement;
2165protected files unchanged,actual hashes+ValidateRollback PASS. Read-only
ManualSave-20 audit: level49 metadata16:32:18,11.10.2026; sav SHA256
0E531F856D4233C9C339F45C29405E590861F40B7918CFA082F736BF64D51096
unchanged. Padre tier rey1_1=1 serialized; no matching Jeopardy start/outcome/owned
facts found, absent!=livezero. Jeopardy is whitelisted; source-native tier eligible
candidate, not offline certified fresh/history/owner proof.
One wrapper retains original Jeopardy parent tier/POI/prelude, directly references
stock main questphase (main/openworld/combat/scenes/calls/rewards unchanged).
New owned instance, NOT resurrected serialized owner. Native Padre phone handshake
fact names source-verified; shared phone/fixer-credit services NOT yet repaired.
Start explicitly DEVELOPMENT: incomplete whitelisted postTower assumed unstarted;
rootSucceeded or rey_06_finished excludes completion, unreadable root refused.
Eligibility is SEPARATE RuntimeEntrySafe: current entry must be inactive/no local
progress and no copied/pending owner. Other incomplete stages report development
eligible but need cleanup/continuation adapter, NOT rejected for missing history.
No preTower snapshot/certification writes or new production automatic dispatcher.
Production unstarted-only rollout remains pending; don't call U4 all-policy/allgig.
B7 copied Jeopardy new requests disabled; existing queued/started copied owner
refuses U4. OtherHeywood requests deferred while U4Permit orStarted unfinished.
U3 Shark queue fix/profile/JV1 bytes unchanged. Collision+realYAML/packedreadback,
exact wrapper delta,admission models,CLI+fullSCC EquipmentEx/compiledreadback,
fourfile recoverablefixture/fourrefusals PASS; native engine LIVE PENDING.
Evidence research/gig_restoration/native_jeopardy_u4/{manifest,tests,
deployment_tests,install_receipt,assessment}.json, save audit manual20_u4/facts.json.
Current4file recovery ONLY tools/deploy_native_jeopardy_u4.ps1; predecessor U3
aggregate recovery historical on replacedB7 until U4 recovered. Recover files
then reload ORIGINAL PRE-U4 snapshot, not U4-running/newsave with copied owner.
PIN U4 mains/build/evidence, no reruns afterinstall. No directsave/cache writes.
NEXT coldlaunch ManualSave-20 identified above; once:
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeJeopardyU4"):Start("DISPOSABLE_SAVE"))
closeCET/menus,holster,safe15sec then same system Inspect(). Expect tiertrue,
request1 and entered1 if all runtimeguards clear. First test startup/native Padre
brief/journal only; DON'T complete gig yet, stock fixer-credit still unresolved.
If refused send output; no forcefacts/B7OverrideAll/replay. No save needed yet.

Latest USER2026-10-12 ADMISSION CLARIFICATION (supersedes older started/resume
restoration policy): Restore ONLY whitelisted gigs; Johnny visuals hidden, voice
retained. PRODUCTION restores only gigs UNSTARTED before Tower, determined from
the actual pre-Tower captured state. Completed and already-started gigs are not
production restoration candidates. Missing pre-Tower history is unknown, never
invented or certified from post-Tower evidence. DEVELOPMENT on a post-Tower save
assumes all INCOMPLETE whitelisted gigs are unstarted for admission. This is an
explicit testing assumption, not actual history and not permission to replay
completed gigs. It supersedes fresh-only historical proof requirements for this
development route; do not reject merely because pre-Tower evidence is missing or
post-Tower state cannot establish historical freshness. Runtime initialization
must still safely handle existing graph/scene/objective state and prevent duplicate
owners/rewards; the assumption is not evidence that those live states are empty.
Do not silently classify a confirmed completed gig as incomplete, grant rewards,
force stock tiers or reset unrelated facts. Native stock tier/entry/lifecycle
semantics remain the target. Development assumptions must stay separate from
production history capture/eligibility and never overwrite certified snapshots.
Current unfinished U4: ManualSave-20 read-only facts audit completed, hashes
unchanged; Jeopardy selected provisionally with native Padre tier present.
redscript/PTFR_NativeJeopardyU4/NativeJeopardyU4.reds is an UNBUILT/UNINSTALLED
draft whose Fresh predicate still requires revision for this policy. No U4 native
wrapper/build/install exists yet. Resume from this draft, not an installed feature.
U3 remains the latest installed gameplay-script revision; U2 logger unchanged.

Latest2026-10-12T16:16:45Z: U3 QUEUE-LOCK REPAIR INSTALLED gameclosed UNSANDBOXED:
two backed-up script replacements(U1+installed B7 dispatcher),0additions,
2164protectedfiles unchanged,actual hashes+ValidateRollback PASS. Correct earlier
diagnosis: sample Watson4/tier1,1_1,1_4=1/1/0 is NOT evidence of missing tier owner.
Stock reggie root161 waits wat_sts_counter>=11 ->209->210->211->212->231->162
sets tier1_4. Do NOT force11 or set tier1_4. Shark is not eligible in this snapshot;
earlier permit1 only meant mod safety checks, not native tier readiness. Native
Regina phone request0 means handler still untested, NOT confirmed absent.
Actual defect repaired: U1 request previously reserved Watson while waiting tiers,
preventing other B7 Watson requests needed for progression. U3 Poll now includes
EXACT native tier predicate in Permit. B7 only defers new otherWatson requests if
U1 unfinished AND Permit1 orStarted1. CopiedShark remains disabled; oldUnused,
freshness,WatsonIdle and runtime safety guards intact; same class/API/fact schema.
Queued U1 can wait while another eligible Watson owner runs; U1 cannot take Permit
while that owner is unfinished. Started U1 remains exclusive until OwnerFinished.
Native graphs/archives/XL/phone/counter/reward/tier facts unchanged. This does NOT
install native tier service/fixer-credit repair or establish full stock parity.
Two-source exact delta,256queue models,CLI+fullSCC EquipmentEx/compiledreadback,
twofile recoverablefixture/fourrefusals PASS; live pending. First offline SCC run
mistakenly supplied staged scripts twice and displayed user error popup. Confirmed
SYM_REDEFINITION same staging path; test setup corrected, full recompile PASS.
Failed log preserved; no failed artifact installed, game log priorcompile PASS.
Evidence research/gig_restoration/native_queue_u3 incl frozen pre_repair_u2_trace.
Current two-script recovery ONLY tools/deploy_native_queue_u3.ps1; predecessor
U1 aggregate recovery historical until U3 recovered first. U1 archive/XL and U2
logger still pinned/unchanged; U2 installer prior-U1-hash check now stale for U3,
do not force its aggregate recovery without accounting for U3. Preserve all old
evidence. New U3 mains PINNED, no reruns afterinstall. No cache/directsave writes.
No immediate gameplay required. Next choose a genuinely native-tier-eligible gig
for original-graph/phone test, or restore stock earned progression via eligible
gigs; do NOT force Shark unlock merely to test it. Shark Status displays U3 and
permit0/entered0 at these tiers; Start unchanged if original unsaved snapshot.
No allgig/alpha/nativephone/completioncredit proof. Profile/JV1 unchanged.

Latest2026-10-12T15:45:29Z: USER continue stock direction -> U2 dependency AUDIT
and GETTER-ONLY logger installed, NOT a new restoration adapter. Eight official
resources extracted unchanged. Source establishes q307 root/6 starts base phone
initializer (Regina node84); root16 before_tomorrow Succeeded ->18->17 cuts service
phase6. Static lifecycle does NOT prove which handler currently survives. Do not
duplicate Regina controller or globally reset phone facts from idle zero flags.
Shark stock prebrief needs Regina request/queue/start_done/end_done handshake.
Stock completion credit is street_stories_new_fixer_loop root/2/5 nodes0->3->25:
kab_06_finished>0 then wat_sts_counter+1. Whole loop restart could recount completed
gigs; restore exact applicable native branch, not custom gameplay/accounting.
Separate native Shark prestate owner touches service/security/mail/doors and is
outside U1 main; current prestate/service overlap unresolved. No branch installed.
U2 installs ONE additive CET PTFR_StockGigAuditU2/init.lua, gameclosed UNSANDBOXED;
2143protected files unchanged, actual hash+ValidateRollback PASS. Eight actual
LuaJIT mocked cases + recoverable fixture/four refusals PASS, NOT engine evidence.
Logger reads facts/journals/U1getters/position/money/epoch; no gameplay mutations.
Failed getters UNKNOWN; unstable session not logged; disk errors disable logging.
Evidence research/gig_restoration/stock_shark_u2/{inventory,source_review,tests,
deployment_tests,install_receipt,assessment}.json. All four installed U1 hashes
unchanged; prior pinned artifacts untouched. U2 recovery ONLY
tools/deploy_stock_shark_u2.ps1 removes logger recoverably and preserves logs;
does not replace U1 four-file recovery. PIN U2 main tools/evidence afterinstall.
NEXT coldlaunch original POST-Tower PRE-B7 OverrideAll/PRE-any-Shark snapshot;
exact filename unknown, do NOT invent. U1 Start("DISPOSABLE_SAVE") ONCE, closeCET/
menus,holster,safe15sec; approach native Shark encounter if accepted/eligible.
Check native briefing/journal only, no completion required. Then
print(GetMod("PTFR_StockGigAuditU2").Status()) and report whether Regina called.
Logger captures automatically. If refused, send output, no forcedfacts/replay/
B7OverrideAll. No save needed for firstcheck; preserve original snapshot. Native
dependency repair/fullstockparity/allgigs remain pending. Profile/JV1 unchanged.

Latest USER2026-10-12 CLARIFICATION: Faithful STOCK execution is the objective,
NOT minimizing copied files. Copy/paste of original graphs is explicitly acceptable
and preferred where practical; direct references are an implementation option,
not a requirement. Reproduce stock gig handling, lifecycle and dependencies.
The intended activity-restoration differences are ONLY whitelist admission and
Johnny projection hidden with voice retained (existing cast whitelist still applies).
Do not replace normal fixer calls with text-only routes, change native quest flow,
rewards/progression/cleanup, or introduce a shared replacement graph template as
design improvements. Prior text reroutes/custom accounting are historical workarounds,
not approved stock-equivalent final behavior. Minimal restoration bookkeeping and
entry safety may prevent duplicate owners/rewards or wrong-target actions, but must
not invent alternative gameplay. Preserve completed/failed state and existing
fresh/resume/replay intent rules; no blanket resets. This clarification concerns
activity architecture; character nerf/profile rules remain unchanged. U1 is only
a feasibility experiment, not a mandate to eliminate copies or a completed stock
restoration. Full native dependency handling still needs audit/live verification.
This clarification changes docs only; no new build/install/save/cache mutations.

Latest USER2026-10-12: RESTORATION TARGET IS STOCK GAME BEHAVIOR. Reuse each
gig's original quest graphs and required stock dependencies; do not redesign
gigs into a shared graph template or add optimizations for their own sake.
Per-gig native graphs may span main/gameplay/openworld phases, embedded graphs,
scenes and shared fixer/district handlers. Restore dependencies needed for stock
briefings/objectives/rewards/progression/cleanup; minimal safety/entry interlocks
are not a replacement for stock behavior. U1 experiment below is NOT stock-parity
proof. Future work must not treat missing native fixer credit as acceptable final
behavior or add alternative story logic merely to avoid repairing dependencies.

Latest2026-10-12T15:07:57Z: USER approves native-resource reuse trial. U1 INSTALLED
gameclosed UNSANDBOXED:3 additions(wrapper-only archive/XL/reds),1 backed-up B7
runtime dispatcher replacement;2139protectedfiles unchanged,4actualhashes and
ValidateRollback PASS. One small parent/prelude+entry wrapper points DIRECTLY to
stock Shark main phase; original gameplay/openworld/scenes/calls/rewards/cleanup
untouched and NOT packed/copied. This starts a NEW instance of original definitions,
not proven resurrection of the old serialized running owner. Native tier guards
retained. Generated node39533 collision-free against installed inventory; realYAML,
packedreadback, exact wrapper payload delta, CLI+fullSCC EquipmentEx and compiled
readback PASS;4file recoverable fixture/5refusals PASS, NOT native engine proof.
B7 Restore Shark disabled while U1 installed, new otherWatson dispatch deferred
during U1; existing pending/started Shark or otherWatson ownership refuses U1.
No globalfact reset, journal setter, custom payout, fixer-credit bridge or history
invention. Stock phone-handler availability and missing district counter owner
are KNOWN TEST QUESTIONS, not worked around. Profile/JV1/G1/G2/G3/S1/M6 unchanged.
Evidence research/gig_restoration/native_reuse_u1/{manifest,tests,deployment_tests,
install_receipt,assessment}.json. Recovery ONLY tools/deploy_native_reuse_u1.ps1
for4currentfiles. Prior B7 source/build untouched; do not run predecessor aggregate
installers against its replaced runtime script. PIN U1 build/verify/test mains;
no rerun afterinstall. No directsave/cache deployment writes. Recovery must reload
original PRE-U1 snapshot, not continue U1-running save with copiedShark enabled.
NEXT livecheck: coldlaunch POST-Tower snapshot BEFORE B7 OverrideAll and before
any Shark request, preferably after successful G2/G3 checks. Exact filename unknown;
do not invent slot/time. Do NOT use latest pending-Watson batch snapshot. CET:
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeReuseU1"):Start("DISPOSABLE_SAVE"))
closeCET/menus,holster,safeoutsideencounter15sec; same system Inspect()/TierStatus().
Firstcheck startup + nativebrief/journal only; no needcompleteyet. Ifrefused send
getters; no forcedfacts. Gameplay/reward/fixerprogression/cleanup/newsave-reload
remain pending. Not allgigs/stockparity/alpha-ready. New user stock-spec direction
does not itself authorize replay of completed/failed gigs or dropping safety.

Latest2026-10-12T14:36:57Z: USER requests SHARK IN THE WATER collision fix ONLY.
B7.2 INSTALLED gameclosed UNSANDBOXED under standing approval:1 additive alias
archive +1 backed-up FamilyB7 XL replacement,2138 protectedfiles unchanged;
2actual hashes+ValidateRollback PASS. Original Shark boot path hashes to generated
ArchiveXL nodeID1, colliding with native ep1.quest startnode1. Pinned 1.27.1 primary
source algorithm and independent bitwise CRC agree. Alias boot_b7_2.questphase
hashes55205, absent from5native root IDs and252installed ep1-root registrations;
252entry inventory matches latest observed merge list (251merged+1collision).
One packed alias resource BYTEIDENTICAL to original B7 Shark boot (SHA A5882A...);
original B7 archive unchanged. FamilyB7 XL changes ONE path only, other75bindings
byte/semanticunchanged; no same-owner duplicate registration, node/fact/journal/
reward/history/native-tier edits or scriptcompile. Existing startup for this owner
failed entirely (live Ready/Queued/Request/Started/Finished0,rootInactive1); no owner
migration/replay/forced facts. New archive path build/SharkB7_2. Real YAML parser,
exact76bindings/packedreadback/knownCRCvector+independent252paths/5negativecases,
2file recoverablefixture/7refusals PASS; engine acceptance/gameplay remains PENDING.
Evidence research/gig_restoration/shark_b7_2/{collision_review,tests,deployment_tests,
install_receipt,assessment}.json. Recovery ONLY tools/deploy_shark_b7_2.ps1 for2
current files; B7.1 and original B7 aggregate recovery historical on replaced XL.
Recovery returns old collision and cannot rewind running/new-saved owners. PIN new
build/helpers/tests/output/receipts; no installed main reruns. No save/cache writes;
original recovery snapshots preserved. All original5B7nonXLfiles+S1/J1/JV1/M6.1/
HP150Body3Relic/R11/bar unchanged. Next coldlaunch SAME postTower test snapshot used
for last screenshots; B7.Override("sts_wat_kab_06","DISPOSABLE_SAVE") once, closeCET/
menus/holster/safe15sec, B7.Inspect sameID:Ready1/noarchive-not-ready expected;
native-tier/prelude wait stillpossible, NOT forcedunlock. No fullgigcompletion
needed for injection check. Other activation/tier/Wakako lock/started support and
11pending adapters OUT OF SCOPE. Current broader partial result:3new Heywood owners
running(LifesWork,FifthColumn,Jeopardy), manytier/prelude waits and H1blocksWakako;
NOT nominal allgig restoration/alpha proof. New55gameplay/history-ending/replay
pending; implemented IDcoverage unchanged61/72, not all72 restored.

Latest2026-10-12T13:55Z: USER reports only old gig markers/empty journal, requests
fix. CONFIRMED B7 STARTUP FAILURE: ArchiveXL09:38:46 rejected FamilyB7.archive.xl
line3col81 illegal map value. Original PowerShell renderer collapsed path/parent/
input onto one line; prior offline tests omitted real YAML parsing. Not a map-filter
or missing-restart explanation for this batch. Preserve original B7 evidence as
historical, NOT successful native initialization. B7.1 CONFIG-ONLY FIX INSTALLED
gameclosed UNSANDBOXED under standing approval: ONE backed-up XL replacement,
0 additions/removals,2119 protectedfiles unchanged; actual hash+ValidateRollback PASS.
New canonical XL build/GigFamilyB7_1; original bad B7 artifact remains pinned.
All76 exact manifest boot bindings (55gig+21earnedtiers) parsed with pinned local
YamlDotNet16.0; old malformed file rejected,11invalid variants rejected; onefile
recoverablefixture/7refusals PASS. Installer reparses actual target. No archive
rebuild, script recompile, quest logic, R3 history, cache or save writes. Five other
B7 deployed files byteunchanged; S1/J1/JV1/M6.1/profile150Body3Relic/R11 unchanged.
Evidence research/gig_restoration/family_b7_1/{startup_failure,tests,deployment_tests,
install_receipt,assessment}.json. Recovery ONLY tools/deploy_gig_family_b7_1.ps1
for this XL; original B7 aggregate installer historical on replaced XL. File recovery
restores KNOWN-BAD predecessor and cannot rewind runtime/newsaved world. Pin new
prepare/helper/tests/installer/output/receipts; do NOT rerun installed main builders.
NEXT coldlaunch latest postTower test snapshot used for failed batch, run once
print(GetMod("PTFR_GigFamilyB7").OverrideAll("DISPOSABLE_SAVE")), closeCET/menus,
holster/safe15sec. Inspect sts_bls_ina_11 should show Ready1 (no archive-not-ready);
native tiers/legacy owner deferrals still valid. Native approach/brief controls fresh
journal entries; no quest completion necessary just to test initialization. New55
engine initialization/gameplay/reload still PENDING,61/72covered IDs unchanged,
11unsupported/started expansion/allcompletedreplay/history-ending alpha pending.

Latest2026-10-12T01:53:35Z: USER corrects prior marker interpretation: activation
and marker handoff already worked; missing icons were disabled map marking.
Treat those milestones as USER-reported PASS, not independent renderer proof;
no more marker-only tests. USER requests whole-whitelist restoration expansion.
B7 INSTALLED gameclosed UNSANDBOXED under standing approval:55 NEW fresh native
gig adapters,6 existing adapters unchanged =61/72 covered IDs, NOT all72 restored.
11 pending:9 Dogtown companion owners, ForMySon multi-input lifecycle, CuckoosNest
legacy missing-scene reachability. No new started/replay routes; completed/failed
preserved; existing3 resumes remain. NewCET PTFR_GigFamilyB7.OverrideAll("DISPOSABLE_SAVE")
dispatches all72 with explicit pending/preserved/deferred outputs. PlanAll getter-only;
RestoreAll/new auto requires frozen certified R3 fresh history. Missing old facts/
PlayingForKeeps baseline stay unknown; NO history schema/cutoff/fingerprint changes.
R3 only adds B7FreshHistory getter; old methods and persistent fields identical.
Native encounters/prefabs/devices/scene choices/cleanup copied, supporting Johnny
voice/JV1 unchanged. Shared fixer calls use authored rejection/mute/content-block
text paths. Per-native-node reward/achievement claim/ack guards; own quest-fact queue,
request,started,finish and counter ledger persist without resizable slot arrays.
One fixer credit after native rootSucceeded+finished fact+owned payout Ack, independent
of long-lived aftermath cleanup; interrupted credit claims quarantine without retry.
21 native earned-tier fragments, B5 Wakako tiers reused, no global counter loops or
final fixer rewards. Original tier/prelude gates preserved; legacy region ownership
may defer requests. GettingWarmer uses active Wakako binding/counter despite hey ID.
FlyingDrugs foreign Minefield POI edge bypassed; CouncilwomanCole foreign GuineaPigs
ambient-cleanup entry detached. Other exact native prelude operations retained.
CLI+fullSCC EquipmentEx/persistence readback;18580 original node payloads/1040 graphs/
exact edges/packed245resource readback,6LuaJIT cases/240interruption models,6file
recoverablefixture/7refusals PASS, NOT engine gameplay or end-to-end ending proof.
5additions(archive/XL/2reds/CET),1backed-up R3 replacement;2093 protected unchanged;
6actual hashes+ValidateRollback PASS. Evidence research/gig_restoration/family_b7.
Only tools/deploy_gig_family_b7.ps1 recovers these6 files; older B6/R3 aggregate
installers historical on R3 path. PIN B7 builder/compiler/tests/receipts: no main
reruns or rebuilding installed evidence. Original saves/cache untouched. File
recovery cannot rewind loaded/new-saved world. Next convenient coldlaunch latest
postTower TESTsnapshot, B7.OverrideAll then closeCET/menus/holster/safe15sec; keep map
Gigs enabled; native tiers and approach triggers govern visibility/journal. Need
no repeated marker pilot. New family gameplay/reload/accounting remain LIVE PENDING;
fullalpha/11remaining/started expansion/completedreplay/history migration pending.
S1/J1/JV1/profile150Body3Relic/R11/bar deferral and M6.1 bytes unchanged.

Latest2026-10-12T01:11Z: M6.1 distant H1 map visibility USER SCREENSHOT PASS.
After ServicePoint filter hid gigs, USER Dynamic views show Gigs/Thievery at
target CharterHill building; Custom with Gigs enabled also shows icon. Frozen
118rows/113fallbacktrue-root1-attempt1 rows/0errors, same owned/nativeIDs;
H1stage3/root1/unfinished/no payout,totals2/4 unchanged. Owned visibleFlagfalse
persists; do not equate this getter to world-map rendered visibility. Actual
installed M6.1 hash matches receipt. Evidence markers_m6_1/map_visibility_result_20261012.json
and frozen trace; predecessor assessment/build/tests/receipt unchanged. Native
vs owned per-icon identity and overlap not independently hit-tested; journal
activation/trackinghandoff/removal/H1completion remain unproven. USER also reports
CityCenter race icon visible: separate visibility observation ONLY, no race-owner
restoration/playability proof or race implementation by M6.1. No new runtime code,
installation/cache/save writes. Visibility test CLOSED; no further immediate test,
restart or new save needed, user may CLOSEGAME. Later H1 native encounter/gameplay
when convenient, not mandatory during laggy remote session. Counts/profiles/native
adapters/recovery unchanged; current marker recovery deploy_markers_m6_1.ps1 only.

Latest2026-10-12T00:48:34Z: USER missing CharterHill H1 icon -> M6 LIVE FAIL,
then requested fix. M6.1 INSTALLED gameclosed UNSANDBOXED under standing approval:
ONE backed-up replacement GigMarkersM6.reds,2074protected files unchanged;
actual+backup hashes and ValidateRollback PASS. Current marker recovery ONLY
tools/deploy_markers_m6_1.ps1; B6 aggregate installer historical on replaced M6
path. All pinned predecessor assessments/builds/tests/receipts preserved; do NOT
rerun installed mains. New evidence research/gig_restoration/markers_m6_1.
Frozen195row prefix has188 false-native-handoff rows,0getter errors. User map
has no icon; internet reference is NOT gameplay evidence. Active/visible native
registration does not prove map rendering; prior H1 near-origin acceptance also
possible but actual nativeposition was not logged. Keep one owned static approach
marker while approved owned unencountered Want predicate remains true; native
registration no longer removes it. Native journal Active/terminal or lost owned
eligibility releases marker. Track transfer only from manually tracked own marker
to nonzero-position active QuestMappin. Own class+ID guards; epoch/purge/warmup;
up to3 EMPTY-handle registration attempts, issued handle retained awaiting ack.
Expanded read-only getter logs own/native flags/phase/XYZ and disclaims renderer
proof. No facts/journal/objective/native owner/reward/history/cache/save writes.
CLI+fullSCC EquipmentEx/persistence readback,11eligibility+5registration checks,
one-file recoverable fixture/7refusals PASS; actual renderer/handoff LIVE PENDING.
Approach marker may have generic Thievery caption and waypoint tracking; journal
stays empty until native encounter. Brief overlap with streamed native POI remains
possible until journal activates. No new gig adapters or B6gameplay proof; Jpn02
already completed in latestsave so cannot fresh-test there. NEXT low-effort check:
restart game, load ManualSave-20 (16:32:18,11.10.2026,level49), closeCET/menus15sec,
open map with gigs enabled at H1 CharterHill location. No TP/override/replay/newsave
needed. Getter GetMod("PTFR_FreshGigsB6").Marker("sts_wbr_hil_01") expected M6.1
fallback=true/root1. No need complete a gig. Original snapshot remains recovery.
6gigadapters/66pending/allcompletedreplay absent, NOTall-gig/fullalpha. B5.1/R3/
G1/G2/G3/S1/J1/JV1/profile150Body3Relic/R11/bar deferral byteunchanged; no commit.

Latest2026-10-11T21:01:04Z: USER yes -> B6/M6 INSTALLED gameclosed UNSANDBOXED
under standing approval:5 additions(B6archive/XL/reds/M6reds/CET),2 backed-up
replacements(B5reds/R3reds),2047protected unchanged; actual7+backuphashes and
ValidateRollback PASS. Current recovery ONLY tools/deploy_fresh_gigs_b6.ps1;
olderB5.1/B4 aggregate installers historical forreplaced B5/R3 paths. Preserve
all predecessor/current receipts/tests/evidence; do NOT rerun installed mains.
Adds fresh-only WeHaveYourWife(jpn02), native originalprefab/escort/combat/scenes/
cleanup preserved; Wakako native authored text alternatives, owned payout/account
guards and independent current baselines/one fixer credit reuse earned B5 tiers.
Separate persistent singleB6slot; tested two-slot B5 schema/recovery unchanged.
B5 ONLY OtherOwnerIdle fixes japan_town path and observes B6 Request before root
activation. Concrete activeWestbrook ownership defers, not sampleH1 prerequisite.
R3 addsB6 dispatch/getter/history predicate; immutabledefinition/fingerprint/
savefields/capture/cutoff unchanged; missing oldfacts NOT invented. M6 session
static approach fallback for3reviewedfreshgigs only: Tower/ownRequestStarted1/
unfinished/fault0/rootInactive/POIActive; officialsectorpositions. Native active
visible noncompleted marker nearlocation or questactivation removesfallback;
epoch/warmup/ownclass+ID checks, nofacts/journal/objective/globaldiscover writes.
FullCLI+SCC EquipmentEx/readback,252nativepayload/16graph exactdeltas,4050source
predicate cases/15625lifecyclemodel transitions/72accountmodels/7actualLuaJIT
cases,7file recoverablefixture/7refusals PASS, NOTengine/renderer/payment/saveproof.
Evidence fresh_b6/{assessment,manifest,source_review,tests,compile_result,
deployment_tests,install_receipt}.json. No cache/directsave deploymentwrites.
6gigadapters/66of72pending;1sideadapter;allcompletedreplay absent, NOTfullalpha.
Game maystayclosed while remotePC laggy. NEXT convenient coldlaunch latestNEW
test snapshot, closemenus/CET15sec, distantH1map check WITHOUT TP/override/replay;
getter GetMod("PTFR_FreshGigsB6").Marker("sts_wbr_hil_01"). H1gameplay/B6live
later; B6 cannot run while H1/sharednativeowner unfinished. Never forcefacts/
replayH7. Originalsnapshot recovery; files cannotrewind loaded/newsaved world.
G1/G2.1/G3/S1.1/J1/JV1/profile150Body3Relic/R11/bar deferral/B5archiveXL+CET
byteunchanged. No commit; new owner/marker live check stillpending.

Latest2026-10-11T20:34:43Z: B5.1 legacyadoption + separateNEWsave/reload USER+
GETTER PASS. User clarifies first repeat loaded original legacy snapshot, so
re-adoption there EXPECTED; then createdNEWsave/reloaded, bothvolatiledetailsblank.
Frozen242rows/159legacyadoption/68finalpersistedrows/zeroerrors: H7stage4/OwnerFinished1/
reward+account+CounterAck1/base1/3; H1stage3/Request+Started1/uncompleted/no credit;
totals2/4/Tier2_Ack1 unchanged, nativehil07_finished1/hil01_finished0. Actual3
installedhashes stillmatch B5.1 receipt. Evidence fresh_b5_1/reload_pass_result_20261011.json
and frozen trace; hash completecapturedprefix, NOT mutablewholelog. Tested reload
milestone CLOSED; not decoded savebytes/all interruption paths/full coldprocess
restart/R3endinghistory or H1gameplay proof. No further immediate liveaction/restart
needed; USER MAY CLOSEGAME. DoNOTreplay H7 or forcefacts/re-run overrides forproof.
Evidence/docs only thisaudit: no runtimeimplementation/install/cache/directsave
writes; all pinned predecessor/current assessments/tests/receipts preserved, no
main reruns. Currentrecovery remains ONLY deploy_fresh_gigs_b5_1.ps1 for3current
replacements; file recovery cannot rewind loaded/newsaved world. Next reviewed
offline marker/family work while USER remoteplaylags; H1gameplay/batchlive/R3history/
67othergigs/allcompletedreplay/fullalpha stillpending. Priorprofile/adapters unchanged.

Latest2026-10-11T20:19:48Z: USER fix -> B5.1 PERSISTENCE REPAIR INSTALLED,
gameclosed UNSANDBOXED under standing approval. THREE backed-up replacements
(B5reds/R3reds/B5CET),0adds;2028protected files unchanged; actual3+backuphashes
and ValidateRollback PASS. Evidence fresh_b5_1/{assessment,compile_result,tests,
deployment_tests,install_receipt}.json; preserve predecessor B5 success/failure
traces/tests/receipt and newly pinned B5.1 mains. No builder/oldcompiler/test reruns.
Compiled persistence flags added to6FreshSlotB5 and5ActivitySnapshot members;
membertypes/schema/R3 methods/catalogue/fingerprint/capture/cutoff unchanged.
Old lost R3 baseline NEVER reconstructed or recertified; existing fault/unknown
guards kept. Future actual ending-history/save serialization still LIVEUNPROVEN.
After4tick warmup/stablejournals, ONLY zeroed B5 slots adopt existing OWN native
Request/Started/outcome/payout/account/baseline/credit acknowledgements. Adoption
onlyassigns script tracking: no native request/restart/spawn/journal/reset/payout/
repeatedackcredit. Ambiguous unacknowledged fixer changes quarantine stage5 without
native Faultwrite; no resend. Existing nonzero/inflight slots untouched byadoption;
original interruption guard remains. Proven running accounts use existing Poll;
acknowledged credit can reassert only idempotent own earned-tier request ifmissing.
No inferred purelyqueued intent without nativeRequest. CET batch stableEntityID.hash
fix, real entity/epoch/backend failures stillcancel; logger nowreads hilXX_finished.
CLI+fullSCC EquipmentEx/readback11markers,13824source-derivedledger evaluations,
9actualLuaJITboxed-ID/cancellation cases,3replacementrecoverablefixture/7refusals
PASS; NOTnative serialization/adoption/batch/gameplay proof. Archive/XL/G1/G2/G3/
S1.1/J1/JV1/profile150Body3Relic/R11/bar deferral unchanged;0cache/directsavewrites.
NEXT SHORTcoldlaunch NEWtestsave fromfailedreload, closeCET/menus/unpaused10sec,
Inspect both: H7stage4/counterAcktrue/base1/3/reward+account1/1; H1stage3/start1/
no payout orcredit yet; totals2/4 ifnointerveningearnedprogress. NOoverrides/H7replay/
H1gameplayneeded. Then another separateNEWtestsave/reload/Inspect confirms persistent
tracking without legacyadoptionmessage. Retain original/new recovery snapshots;
ifrefused sendInspect/Sample, neverforcefacts. Current3file recovery ONLY new
deploy_fresh_gigs_b5_1.ps1; earlier aggregate installers historical onreplacedpaths.
Native/newsaveeffects notrewound byfiles. Distantmarker/H1gameplay/67gigs/allreplay/
automaticendinghistory/fullalpha stillpending. No commit until usefullivepass.

Latest2026-10-11T20:09:01Z: B5 NEWsave/reload USER+GETTER FAIL. Frozen210rows,
all210 show both slots stage0/zero baselines/counterAckfalse, zero gettererrors.
H7 native Request/Started/OwnerFinished/reward/account/CounterAck1 and baselines1/3
SURVIVED; totals2/4 and Tier2_Ack1 unchanged. H1 native Request/Started1 survived,
but stage0 disables PollSlot/accounting monitor. Do NOT replay H7, rerun overrides
or complete H1 before repair. USER MAY CLOSEGAME; preserve original/new snapshots.
Confirmed source omission: all6 FreshSlotB5 members lack persistent, enclosing
slots array alone is persistent. Documented nested serializer behavior matches
reset; exact savebytes/schema values NOT independently decoded. R3 ActivitySnapshot
has same member pattern: separate production-history audit needed, not proven loss
here and NEVER manufacture missing pre-ending evidence. Evidence fresh_b5/
reload_failure_result_20261011.json + frozen trace; hash capturedprefix only.
Actual5installedhashes still match receipt. NO runtime fix/install/native/cache/
directsave writes; earlier H7 route PASS/pinned builds/tests/receipt preserved.
NEXT scoped persistence repair plus adoption from existing owned B5 acknowledgements
without reissuing owner/payout/credit; independently audit R3 persistence. B5 batch
identity false-refusal/distant discovery still unresolved,67gigs/allreplay/alpha
pending. No immediate gameplay needed, particularly on laggy remote connection.
Prior adapters/profile150Body3Relic/R11/bar deferral unchanged; B5 recovery only.

Latest2026-10-11T19:55:50Z: B5 H7 TygerAndVulture success-route USER+GETTER PASS.
Frozen666row complete prefix/111stage4rows/zeroerrors: native OwnerFinished1,
reward/account/CounterAck1, independent fixer1->2 and achievement3->4 once,
Tier2_Ack1; no later observed countergrowth/ackreset/fault. Actual5installedhashes
match receipt. Evidence fresh_b5/live_result_h7_20261011.json + frozen trace;
hash covers captured prefix, NOT mutablewholelog. H1 UntilDeathDoUsPart gained
earned nativeTier eligibility and progressed queued1 ->nativeStarted/stage3 once
menus closed; its root stillInactive1. H1 gameplay/completion/payout UNPROVEN.
USER reports no journal/map marker until teleport: POI alreadyActive19:35:46Z
while far (1422.535,-749.186,48.84), native questActive19:37:27Z near entrance
(-75.25,-324.19,-0.543). Native POI state is NOT map visibility proof; distant
discovery unresolved, do not call it fixed or normalize missingmarker as intended.
B5 OverrideAll stillFAULTY: tostring(EntityID boxedobject) identity comparison
false-refused before requests; direct R3 Override hil07/hil01 fresh commands
accepted. Older B4 uses stable .hash; no hotfix/install done, use per-ID workaround.
DoNOTrerun pinned B5/predecessor builder/compiler/testmain, no code/game/cache/
directsave/deployment writes by this audit; existing profile/R11/bar deferral intact.
USER MAY CLOSEGAME; optionally preserve progress in separate NEWtestslot first,
never overwrite originaltest snapshot. No further immediate live action needed.
NEXT reload that newslot, Inspect both; H7 remainsstage4/account+reward1/1/
counterAcktrue/totals2/4/fault0, H1 queued/running without duplicate credit/fault.
Then H1 native gameplay, plus narrowly reviewed batchidentity/discovery repair
when requested. No H7 replay/reset/forcefacts. Unknown certifiedFreshHistoryfalse
under explicitoverride staysunknown. H7 reload/alternate routes/exactcashXP/
automatic endinghistory/other67gigs/allcompletedreplay/fullalpha remain pending.
World/newsaveeffects notrewound by file recovery; currentrecovery ONLY B5installer.

Latest2026-10-11T14:10:16Z USER continue -> B5 TWO FRESH GIGS INSTALLED
gameclosed UNSANDBOXED under standing approval:4 additions(archive/XL/B5reds/
getterbridge),1 backed-up R3 dispatcher replacement;1970 protected files unchanged;
5actualhashes+ValidateRollback PASS. Native fresh-only TygerAndVulture(hil07) and
UntilDeathDoUsPart(hil01), NOT all-whitelist restoration:5gig adapters/67of72pending,
1existing side adapter, ALLcompletedreplay absent. Native3resources/job/prefab/
spawn/device/itemhand-in/localscenes/choice/outcome/departure preserved;4shared
Wakako call entries use authored text, native payout alternatives singleclaim/ack.
Completion snapshots independent fixer/achievement baselines, native achievement+1
then one guarded fixer+1; no samplecounter/equality gate or globalcounterloop.
Separate earned Wakako tierfragment count2/5/7/8 incl native delay/content/Rogue
conditions; skips existing messages/positiveflags, newflags absolute1. No welcome/
default/NCPDtier/finalreward owner restart. Two queued fresh owners serialize;
H1 waits native eligibility and H7 cleanup (native4gamehours/departure retained).
Fresh roots+all children Inactive/localfacts0/no existingdatabank/no competing
cluevendor required, no terminalPOI reset. Interrupted/drifting/unacknowledged
mutations fault without retry/reset/compensation. Missing deadref alone nothardgate.
R3 persistentshape/definition/fingerprint/capture/cutoff unchanged; dispatcher adds
B5branches/automatic calls. H7 scene facts missing from immutable R3history remain
UNKNOWN: automatic H7 refuses, explicitfresh supported. NO history invention or
migration. Old B4 catalogue/bridge byteunchanged stillnamesB5pending; use new B5
bridge or R3per-ID methods. OverrideAll B5 dispatches TWOnewfresh only, not all72;
RestoreAll B5 requests FIVEimplemented gig adapters only, no side job activation.
Player/session/backend errors cancel remaining requests withoutretry, notundo.
CLI+fullSCC EquipmentEx/readback/349nativepayloads/29graphs/59guardmutants/
1264abstractcases/10actualLuaJITcases/5filemixedrecoverablefixture+7refusals PASS,
NOT enginebinding/gameplay/payout/persistence proof. Evidence fresh_b5/{source_review,
manifest,compile_result,tests,deployment_tests,install_receipt,assessment}.json.
Recovery ONLY tools/deploy_fresh_gigs_b5.ps1 for5currentfiles; B4/G3/S1/R3 aggregate
recovery historical on replacedR3 untilB5recovered. Newly pinned B5 builder/compiler/
test mains mustNOT rerun. No direct save/cache deploymentwrites; loadedworld/newsave
effects notrewound by file recovery. Preserve originaltest snapshot. G1/G2.1/G3/
S1.1/JV1/J1/profile150Body3Relic/R11/baridledeferral byteunchanged, no commit yet.
NEXT coldlaunch disposable Tower fresh snapshot; B5 OverrideAll("DISPOSABLE_SAVE"),
close CET/menus/holster/safe, complete TygerAndVulture, inspect payout/account/credit/
earnedtier and native cleanup, then H1 gameplay. NEWtestslot/reload afterterminal.
Ifrefused/fault send fullInspect, NEVERforce facts/items/replay. Automatic ending
history/fullalpha/other67gig adapters/separate Dogtown companion owners pending.

Latest2026-10-11T04:34:39Z USER all-whitelisted-gigs request -> B4 PARTIAL
BATCH DISPATCHER INSTALLED gameclosed UNSANDBOXED under standing approval:
2CET additions(init/catalogue),1 backed-up R3 replacement;1940 protectedfiles
unchanged;3actualhashes+ValidateRollback PASS. All72 v4 broader gigs mapped;
1071official resources +3external scenes,215phase refs/1401graphs/354scene refs;
mainowner bindings72, phase/scene closure69+3explicit gaps;2crowdCommunitydecode
gaps retained. Closure is NOT full cast/world/stage/reward certification. New
72overlay adds PlayingForKeeps, not R3history; NO baseline migration/invention.
R3 definition/fingerprint/persistentfields/cutoff and oldautomaticdispatcher
unchanged; only public RestoreGig(id)+read-only BatchEpoch added. Gig-only batch
doesnot activateS1. PlanAll getter-only+diagnosticlog; RestoreAll requires R3
certifiedhistory; OverrideAll("DISPOSABLE_SAVE") delegates exactoldresumeguards.
Terminalnative roots/facts preserved; unsupported owners named PENDING_ADAPTER;
sessionepoch/load/disk/backend errors cancel withoutretry, notundo issuedrequests.
CLI+fullSCC EquipmentEx/readback,21actualLuaJITcases,3filemixedrecoverablefixture/
7refusals PASS, NOTenginebatchbinding/gameplay proof. ZEROnewnativegigadapters:
still3gig+1side adapters;69 of72gig adapters pending, allcompletedreplay absent.
DO NOT CALL THIS ALL-GIG RESTORATION OR ALPHA-READY. Evidence batch_b4/assessment,
source_review,manifest,compile_result,tests,deployment_tests,install_receipt.json.
Recovery ONLY tools/deploy_gig_batch_b4.ps1 for3currentfiles; earlier G3/S1/R3
aggregate installers historical on replacedR3 dispatcher. Pinned installed B4
builders/compiler/test mains must NOT rerun. G3native/JV1/J1/S1.1/profile150Body3
Relic/R11/bar-idle deferral byteunchanged; no directsave/cache deployment writes.
NEXT implement fresh-gig owner family + independently earned fixer-tier progress,
not restart global completioncounterloop. Separate Dogtown companion owners.
Known pending started: Empathy/TalentAcademy/TreatingSymptoms; Empathy captured
get_clubSucceeded3/getserver+avoidcombatActive2/start1/weapons_deposit0 requires
continuation, skip prior loot/start/prebrief. Missing deadref alone nothardgate:
audit reachability. No further immediategame test needed solely fordispatcher;
gamecanstayclosed until useful native-familybuild. Never claim all72restore from
batchlogs/catalogue/source/compiled/mock success. File recovery cannot rewind a
loaded world or NEWsaved snapshot; preserve originaltest recovery snapshot.

Latest2026-10-11 USER NEW SAVE/RELOAD G3 PASS; getter04:04:48Z corroborates
unchangedstage4/prepared4/OwnerFinished1/reward+account1/1/counterAcktrue/
totals1/1/J3/3/3/fault+replay0, volatile detailcleared, errors0. Evidence
minefield_g3/reload_result_20261011.json; prior frozen363row trace/result and
installedbuild/tests/receipt preserved. This closes tested early success-route
milestone incl USER Johnny voice/no-model; NOT allroutes/decodedsaveproof/full
coldprocessrestart/automatic endinghistory/allactivity/fullalpha proof.
NO further immediate livetest/restart needed; USER MAY CLOSEGAME. No newinstall/
code/cache/save writes; next reviewed per-owner/batch restoration expansion.
4adapters/124others/allcompletedreplay remain pending; prior builds/profile/R11/
bar-idle deferral unchanged. Do not replay or force facts to retest completion.

Latest2026-10-11: G3 SUCCESS ROUTE USER+GETTER PASS; USER confirms Johnny
worked as expected (voice/no visible model for this route). Frozen completed log
prefix035136:363rows/86stage4rows/zero gettererrors; owned request/start -> native
reward+account1/1, counters0->1 once, native OwnerFinished1 thenstage4. Journal
root/phase/findcar Succeeded3/3/3; fault0/replayRefused0, no later observed counter
growth.17JV1trackedrows/max39rootvisualcomponents corroborate target processing,
NOT independent renderer/audio proof. Five actualinstalledhashes matchreceipt.
Evidence minefield_g3/live_result_20261011.json + frozenlive_trace_20261011.jsonl;
hash of complete captured prefix, not mutable whole live log. Source/receipt/
build/tests untouched; no new installation/cache/save writes or builder rerun.
Preflight localFacts/journalfalse EXPECTED aftercompletion; uncertified history
remains unknown under explicit override. NEWTESTSAVE/RELOAD STILL PENDING: save
separate NEWslot, reload, Inspect sts_bls_ina_07; expectstage4/ownerFinished1/
reward+account1/1/counterAcktrue/currentCountAch1/1/fault+replay0. No replay or
force facts. No process restart required for this check; once resultpersists,
user mayclosegame. ExactcashXP attribution/failure/otherbaselines/sharedrole
exclusiveownership/otherJohnnyappearances/automatic endinghistory unproven.
4adapters/124others/allcompletedreplay pending, notfullalpha. Next reviewed
per-owner/batch expansion AFTER finalreloadcheck. Allprevious acceptedbuilds/
profile150Body3Relic/R11/bar deferral preserved.

Latest2026-10-10T20:04Z: MINEFIELD G3 EARLY FIND-CAR CONTINUATION INSTALLED
20:03:26Z gameclosed UNSANDBOXED under standing approval:4 additions(archive/XL/
G3reds/getterlogger),1 backed-up R3 dispatcher replacement,1883 protectedfiles
unchanged;5 actualhashes+ValidateRollback PASS. Evidence minefield_g3/{manifest,
compile_result,tests,deployment_tests,install_receipt,assessment}.json. Recovery
ONLY tools/deploy_minefield_g3.ps1; old R3/S1/G2 installers historical for replaced
dispatcher. Preserve new pinned evidence; no main builder/compiler/test reruns.
Original physical prefab + native chase/vehicle/delivery/failure/cleanup retained;
inert boot behind one owned request. Skip initial ready/start/brief/checkpoint,
skip body-investigation comment if scan alreadydone. Existingcar skips damage;
new activatedcar gets absolute authored visualdamage, not accumulation/HP reset.
Dakota uses native debrief texts, shared phone paths and foreign RadarLove
antenna-car cleanup detached. Six exact shared patrol commands gain entered-path
flags; clearrole only flagged+spawned target, NOT proof of current exclusive AI
role ownership. Native cleanup timing, AI behavior and alternate paths UNPROVEN.
Native payout claim/ack once; independent fixer/achievement baselines snapshotted
at completion handoff, native achievement+1 then one guarded fixer+1. No fixed
sample totals or G1 dependency, no incidental boot counter equality. OtherActive
Badlands ownership defers/refuses garage/patrol/accounting overlap; no global
fixer loop/tier/finalreward restart, no completed replay/reset/compensation.
R3 immutable shape/schema/definition/fingerprint/cutoff unchanged; new history
uses exact15 early pre-ending journalstates+14 captured nativefacts. '#' facts
excluded from global R3 snapshot: readiness checked LIVE by G3, not invented
baseline proof. Existing old autoAttempted saves need explicit override. Command:
GetMod("PTFR_ActivityStateR3").Override("sts_bls_ina_07","resume","DISPOSABLE_SAVE").
CLI+fullSCC EquipmentEx/readback,26graphs/447nativepayload comparisons/exactdeltas,
24guardmutants/7240abstractcases/7LuaJIT getterchecks,5file recoverablefixture/
7refusals PASS, NOT engine gameplay/presentation/payment proof. NEXT coldlaunch
postTower original preG3 snapshot, override, closeCET/menus/holster/outcombat/
vehicle/workspot; findcar, escape, deliver and follownativeobjective. Check Johnny
voice remains/model absent (JV1 still LIVEPENDING); completion/payout/counters,
departure+native3gamehour cleanup, separate NEWtestsnapshot/reload then Inspect.
If refused send Inspect, never force facts/replay. Original snapshot is recovery;
file rollback cannot undo loaded/new-savedworld effects.4adapters/124otherpending,
allcompletedreplay/automatic endinghistory/fullalpha remain unproven. G1/G2.1/
S1.1/J1/JV1/profile150Body3Relic/R11/bar-idle deferral byteunchanged. No commit
until useful livepass. No claim allgigs/sidejobs restored.

Latest2026-10-10T19:27Z: Next candidate Dancing on a Minefield G3, visible PRE
find-car stage backed by stable R2 pair; 10 native resources decoded, 3 owners/
26 graphs/3 scenes pinned in minefield_g3/source_review.json. Initial additive
start/ready and physical node264 accumulated vehicle damage must not repeat;
Dakota shared-phone/reward, chase/car state and Badlands accounting audit pending.
Comments casts supporting Character.Silverhand, no independent props/live
Panam/Kerry/Judy. JV1 PRESENTATION CANDIDATE INSTALLED19:24:58Z gameclosed
UNSANDBOXED:1 redscript addition,0replacements,1883protected unchanged; actual
hash+ValidateRollback PASS. Exact Silverhand + completedTower only; native
IVisualComponent.TemporaryHide true, NPC wrapped attach + weakref 0.1sec polling
(idle1sec), epoch-safe restore; audio/animation/actor lifetime/AI untouched.
No quest/fact/journal/reward/save-field/cache writes. CLI+fullSCC EquipmentEx/
compiledreadback,16384predicate+287lifecycle model cases, recoverablefixture/
5refusals PASS, NOT renderer/audio engine proof. Independent props/externalFX,
appearance flash and actual voice/no-model remain UNPROVEN; exact record only,
no takeover/other records promise. Evidence research/johnny_voice_jv1; recovery
ONLY tools/deploy_johnny_voice_jv1.ps1. Do NOT rerun pinned tools after install.
G3 NOT IMPLEMENTED; still3adapters/125pending/allreplay unimplemented. No new
immediate live test/restart; game canstayclosed until useful combined G3 check.
Rite/S1.1/J1/profile/R11/bar deferral unchanged; old evidence preserved.

Latest2026-10-10T19:08Z: G2.1 USER+GETTER TRACE LIVE PASS for baseline3 exact
resume route. Journal visible, native recording/escape Succeeded; account/counter
ack18:55:11Z and Watson/achievement3->4 once observed. Reward initially0/0,
then1/1 at18:59:00Z after leaving; native physical OwnerFinished1/stage4 at
19:03:09Z after USER skippedtime. USER new-test-save/reload reports unchanged
stage4/prepared4/ready+started+finished1/reward+account1/1/counteracktrue/
totals4/4/fault+replay0/J3/3/3. Volatile detail blank afterreload expected.
Frozen733row getter snapshot18:43:31..19:08:01Z,0errors,146stage4rows;
no later observed ack reset or counter growth. Snapshot hash in
research/gig_restoration/rite_g2_1/live_result_20261010.json. Three installed
hashes stillmatch receipt. Existing saved boot guard adopting new baseline3
now demonstrated on this route. Unknown preendinghistory staysunknown under
explicitoverride; G1 completed/ownedacks remain0, no G1 prerequisite needed.
ExactcashXP/alternate routes/visualcleanup/baseline4/concurrency stress/cold
process restart/automatic endinghistory remain unproven; userreload not
independently decoded save serialization. No fullalpha claim:125other adapters/
allreplay/general earnedtiers+finalreward/G1-at4/presentation+R4migration pending.
No additional immediate livetest/restart needed; user may CLOSEGAME.
Next reviewed per-owner/batch expansion and safely generalized admission under
latest safety-only gate policy, no unsolicited implementation this result turn.
NO newinstall/code/cache/save changes; evidence/docs only. Preserve pinned
G2.1 assessment/build/tests/receipt and newtrace; no predecessor main reruns.
Current3file recovery remains ONLY deploy_rite_g2_1.ps1. S1.1/J1/profile/R11/
bar deferral unchanged. Original pre-test snapshot retained as recovery point.

Latest USER2026-10-10T18:42Z — SAVE WORKFLOW CLARIFICATION: user states existing
save snapshots are not altered; the game creates a NEW save later. Mod restoration
operates on the loaded in-memory world/journal/facts and save-local script fields,
not by editing source save files. Native saving later serializes that session
into the new snapshot. Original pre-test save is the recovery point: reloading
it discards later session changes; file rollback alone does not rewind a loaded
world or an already-created newer save. Distinguish deployment disk writes,
runtime in-memory mutations and later native save creation in reports. Do not
describe restoration as modifying the original save file or irreversible across
all prior saves. Preserve original snapshots; no direct save-file writer, deletion
or forced overwrite is authorized. This records the USER's new-save workflow,
not a verified guarantee that native autosave/overwrite slots can never be reused.
Safety gates still prevent crashes and unintended behavior in the current/newly
saved world; existence of an older recovery snapshot does not permit duplicate
rewards or unsafe owner actions. DOCUMENTATION ONLY; installed build unchanged.

Latest USER2026-10-10T18:39Z — FUTURE ADMISSION POLICY: widen gates to the
largest safely supported state range. Runtime safety gates exist ONLY to prevent
crashes or unintended mod actions/output (including corrupt journal/world state,
duplicate owners/items/rewards, repeated counters, wrong-target writes and
unacknowledged saved mutations). Do NOT treat a particular test-save counter,
another pilot's completion, exact unrelated facts or unfamiliar-but-safe state
as a requirement merely because it matched the initial sample. Each hard refusal
must identify a concrete unsafe operation or an actually unsupported execution
path that could cause unintended behavior; give actionable diagnostic output.
Prefer deriving current stage/baseline, skipping already-applied work, idempotent
operations and safe per-stage continuations over blanket refusal. Unusual state
without such a risk should warn, not block. Still audit unknown execution paths
before allowing mutations: wider admission is NOT blind resets, reward replay,
forcing native story/tier facts, bypassing essential owner/device prerequisites,
or manufacturing pre-ending history. Explicit whitelist/profile and fresh/resume/
replay selections remain user-intent policy, separate from technical safety
checks; this request does not change their approved content. Future adapters and
revisions must apply this rule and replace unnecessarily save-specific gates
when safely generalized. DOCUMENTATION ONLY this turn: installed G2.1 and its
3/3-or4/4 restriction are unchanged; no new build/install/test/game/save writes.
Pinned receipts/tests and next disposable G2.1 live check remain unchanged.

Latest2026-10-10T18:34:40Z: USER G2 refused3/3, stage0/enabledfalse/start0,
keycard1/localFacts+staticJournaltrue/J4/4/4; empty active journal EXPECTED,
no restoration mutation. USER requests fix. G2.1 INSTALLED gameclosedunsandboxed:
THREE backed-up replacements(G2archive/G2reds/G1reds),0adds/removals,
1864 protected files unchanged; actual3hashes+ValidateRollback PASS.
Matching3/3 OR4/4 now admitted without artificial G1 completion prerequisite;
all exact preclinic/item/outcome/tier/history guards retained. Only TWO packed
condition payloads changed from G2; native180nodes/edges/reward/cleanup same.
G1/G2 read-only WatsonAccountBusy getters use existing persistent fields/ownfacts;
both direct Restore methods refuse other outstanding/unknown account before
enable/journal writes. Queuedstage1/Request0 blocks. Unacknowledged Poll rechecks;
fault/interrupted/orphan/stale disabled metadata stays blocking, no forced reset.
Accounting releases only stage3/4 supported journal/notinflight, persistent
counterack+all native finish/account/reward acks; native cleanup can continue.
G2 exact3->4 or4->5 bridge once; G1 original3-only admission/bridge unchanged.
R3 dispatcher/savefields/fingerprint/cutoff unchanged; NO deferred auto retry
or generic batching. G1-after-G2 at4 NOT implemented. Bothcompilers/fullSCC
EquipmentEx/J1/S1.1, packedreadback/180native payloads,60guardmutants/2771
abstractcases/source-linked getter eval, getterLua and3file recoverablefixture/
13refusals PASS, NOTengineproof. No game-save/cache writes at deployment.
LIVE PENDING: coldlaunch disposable Tower preclinic3/3 (or4/4), R3 nid05 resume
override, closeCET/menus/holster/safe wait, native clinic/download/escape/debrief,
record payout/separate save-reload. No concurrent Watson gigs/NCPD completion.
3/3 becomes4/4, or4/4 becomes5/5; reward/account1/1/counterack. Native cleanup
3gamehour/departure conditions unchanged; do NOT force OwnerFinished/stage4.
If refusal send full Inspect, incl nid02 if accounting busy. S1.1/J1/R4/
profile150Body3Relic/R11/bar deferral unchanged. Threeadapters,125others/all
replay and ending/history alpha stillpending. Evidence rite_g2_1/assessment+
tests+receipt. ONLY deploy_rite_g2_1.ps1 for3current replacements; priorG2/G1
aggregate recovery historical on replacedpaths. File recovery cannot undo
savedgameplay. Preserve predecessor/new pinned builds/tests/receipt; no rerun
mains/rebuild after install, no commit until livepass.

Latest2026-10-10T17:19:33Z USER proceed -> RITE G2 INSTALLED gameclosed,
unsandboxed:4 additions(archive/XL/reds/getterlogger),1 backed-up R3 dispatcher
replacement,1844 protected files unchanged;5 actual hashes+ValidateRollback PASS.
EXACT pre-clinic started continuation only, NOT fresh/replay. Native prefab
embedded26/#sts_wat_nid_05_steetstory/IN-OUT preserved, OW2/combat22 copies;
180 native nodes checked, only allowlisted edges/two phase refs changed. All3
scenes no Johnny/Panam/Kerry/Judy; Royce fact read unchanged. Skip prior initial
checkpoint/door ForcePower/prebrief/start/description, Enemy9 two shard injections
and keycard grant. Require EXISTING keycard100486752765 exactly1, captured post
journal4/4/1/1/4/1/2, nonterminal POI, native tier and own unused guards. Require
G1 finished/reward1/1/CounterAck1, Watson+achievement4/4: no simultaneous G1/G2
counter3 admission. Native achievement add1 own claim/ack, exact Watson4->5
bridge once/readback/inflight; native reward163539604770 own claim/ack. Native
PersonalLink/3sec download/combat/retaliation/cleanup retained; authored text
debrief, no global phone/tier/final-reward/root restart. OwnerFinished only after
native physical OUT; no forced cleanup setter. R3 persistentfields/definition
71+57/fingerprint/cutoff unchanged; auto G2 requires certified exact7journal+
7fact baseline, old/unknown not fabricated. Override nid05 resume skips ONLY
history; fresh/replay still refuse. Other125 adapters/all replay pending, not
combined-alpha-ready. G1/S1.1/J1/R4/profile150Body3Relic/R11/bar unchanged.
CLI+fullSCC EquipmentEx/J1/S1.1 readback, packed4resources,34 guardmutants/
565abstractmodels, LuaJIT/getteronly,5file recoverablefixture/7refusals PASS,
NOT engine/payment/persistent-world proof. Next coldlaunch DISPOSABLE Tower
save with G1 accounted and Rite preclinic, R3 Inspect then Override("sts_wat_nid_05",
"resume","DISPOSABLE_SAVE"), closeCET/menus/holster/safe; normal clinic/link/
escape/debrief, separate save/reload. No concurrent Watson jobs. Native cleanup
waits3gamehours then outside starttrigger; stage3 immediately after completion
NOT failure proof. If refused/fault send full Inspect, NEVER forcefacts/items.
Evidence research/gig_restoration/rite_g2/assessment.json+tests+receipt. Recovery
ONLY deploy_rite_g2.ps1 for5files; prior S1/R3 recovery historical on dispatcher
path. File recovery cannot undo saved effects. Preserve pinned G2 build/tests/
receipt; doNOT rerun predecessor mains or rebuild installed artifacts. No commit
until livepass; presentation/R4 migration/history-ending alpha still unproven.

Latest2026-10-10T15:57Z USER CAST POLICY R4: Supporting Johnny VOICE stays,
visible projection does NOT; Johnny-central/personal-story/takeover/Relic-ability
jobs excluded. Entire jobs with Panam/Kerry/Judy live participation excluded,
including optional scene/call/message branches. Historical mentions/recordings
and completed prerequisite association alone do not count as live cast; unknown
full-cast/branch coverage still refuses runtime admission. Retained Johnny voice
is an explicit gameplay compromise, NOT canon engram survival; do NOT revive
Johnny/Relic or ending facts. Both lore variants updated in NEW preserved-version
research/gig_restoration/lore_whitelists_v4_cast.json: aware34gigs/30side,
broader72gigs/58side. Added PlayingForKeeps/NoEasyWayOut/Spellbound/ProphetSong;
removed DazedAndConfused(optional Judy messages) and IllFlyAway(native Panam
blocked-job message), whole job even if some routes omit the participant.
Targeted revision, NOT exhaustive cast certification or runtime activation.
Voice-only adapter NOT implemented/tested. Installed R3 observation schema,
fingerprint/71+57 selection, TWO adapters and all saved history remain unchanged;
do not regenerate predecessors to switch lists. Future explicit reviewed
selection/history migration must not invent pre-ending proof. Independent R4
14policy/source checks PASS,8protected inputs and14installed files unchanged.
Initial test-ID/class assumptions corrected against exact stock journal/message
types; preserved tests_initial.json. No new adapters/install/game/save writes or
live test/restart. Next RiteOfPassage exactresume audit remains unchanged. R4
evidence research/activity_cast_policy_r4/assessment.json+tests.json. Preserve
S1.1/J1/G1/profile150Body3Relic/R11 and bar deferral; no combined-alpha claim.

Latest2026-10-10T15:28:24Z: USER continue -> B1 OFFLINE batch/owner source audit.
128 IDs partitioned (62basegigs/9DLCgigs;57sidejobs in six planning groups),
not owner census/admission. Seven owners reviewed;14new source-regression tests
and252fact-model cases PASS;14current installed files hash-match latest receipts.
Ten sidejob fact-source bindings remain unresolved across the planning groups.
ZERO new adapters/install/game/save/cachewrites;126other adapters/allreplay remain
pending. Three Kabuki fresh candidates have failed captured local tier alternatives;
no tier/debug/POI forcing, POIs not captured. ShootToThrill needs phone/prize/stash
audit; DayInLife shares sq024 vendor and passive mq013active cannot mean player
started; Bullets MAINscene hasJohnny and followup. Not whitelist removals.
NEXT exactresume target RiteOfPassage(nid05), USER-visible/paired started stage:
pre2/2/1/1/2/1/2 ->post4/4/1/1/4/1/2,start1/finished0/combat0. Correct prefab
owner embedded26(9nodes,#sts_wat_nid_05_steetstory,inputIN), streetstory2(117),
combat22(54); all3actualscenes noJohnny, clinicreadsq003roycedead unchanged.
Catalogue ordering is NOT owner hierarchy: provisional B1closure was incomplete,
corrected current lifecycle_review_r3.json, regression pins3resources/3scenes.
Must stillaudit safe resume entry/prebrief skip, recording/device/profile access,
native reward/additiveachievement/fixer-counter once, retaliation/cleanup before
runtimeimplementation. G2 Override NOT supported yet. One Kab102crowdcommunity
raw preserved/decoder rejects defaults; unknown, notempty; no tooling bypass.
Evidence research/activity_batches_b1/assessment.json+tests_r2.json. No newlive
test/restart needed; gamecanstayclosed. S1.1/J1/G1/R3definition/profile/R11/bar
unchanged; preserve predecessor pins; do NOT rebuild installed S1 tools.

Latest2026-10-10T14:57:32Z: S1.1 cleanup USER+GETTERLOG LIVE PASS. Cold session
starts stage3/Departure0/OwnerFinished0; by14:56:44Z native waits1/1,
deactivated1/1,Joined1,OwnerFinished1 ->stage4.34row captured complete logprefix,
25releasedrows/zeroerrors; rewardClaim/Ack ALWAYS1/1, journalstates unchanged
3/3/1/1/3/3, fault0/replayRefused0. Prefix hash (not mutable wholelog) in
research/side_job_cleanup_s1_1/live_result_20261010.json. Existing savedwaits
adopting revised conditions now demonstrated on this route; entered0 expected
because cleanup started before added entry instrumentation. No directfinished
setter or quest/reward replay. Original dynamicreference blocker remains inferred,
notexactnode-stateproof. Visual actor/car absence, exact cashXP, postrepairstage4
save/reload, alternate routes, productionhistory/endingtransition unproven.
No additional immediate livetest; user may save separatetestslot and closegame.
Next reviewed restoration batches/per-owner audits;126other adapters/allreplay
stillpending, notfullalpha-ready. S1.1/J1/profile/R11/bar unchanged; no newinstall.
Preserve pinned assessment/tests/receipt; do not rerun predecessorS1tools.

Latest2026-10-10T14:51:31Z: USER departed; getterlog confirms up to757.386m
from mq005 waypoint, ownerFinished0 after distant departure. Earlier nearby-only
explanation INSUFFICIENT. Completion/journals/reward1/1 persist. Exact active
native node UNDECODED; dynamic actor/car distance dependency is plausible, not
proven sole cause. USER requests fix, game closed. CLEANUP S1.1 INSTALLED
unsandboxed: THREE backed-up replacements (S1archive/pilotreds/getterlogger),
0adds/removals,1827 protected files unchanged; actualhashes+ValidateRollback PASS.
Only root/4 waits10/15 gain OR(originalcondition, guardedfallback); original
outside mq005_tr_big retained. Fallback only completed owned police-left route,
schema1/stage3/notinflight/Tower/request/start1/fault0/reward1/1/mq005done1/
policeleft1/policedone0/quest+phase+corpo objectives Succeeded; five consecutive
safe samples>=500 horizontal metres from source waypoint arms own Departure1.
No directOwnerFinished/stage4 shortcut, rewards/reset/restart/vanillafact/journal
writes. Native actor/car deactivation ANDjoin terminal remains responsible.
Six own ack nodes instrument entered/waits/deactivated/joined; persistent script
fields unchanged, volatile samplecounter resets onrestore. Boot/combatbytes
identical, R3/XL/J1/profile150Body3Relic/R11/bar deferral unchanged. CLI+fullSCC
EquipmentEx/J1readback,110originalnodes/equality,16guardmutants/7629abstractcases,
3file recoverablefixture/7refusals PASS, NOT engineproof. Existing activewaits
adopting modified definitions on reload LIVEUNPROVEN. Next coldload COMPLETED
test save >=500m away, closeCET/menus/holster/outcombat/vehicle/workspot10sec,
Inspect mq005_alley: expectedOwnerFinished1/stage4/reward1/1; otherwise sendfull
cleanupS1.1 fields. DoNOTfreshOverride/replay/forcefacts. Game canremainclosed
untilthatcheck. ONLY deploy_side_cleanup_s1_1.ps1 for3file recovery; oldS1
installer/receipt historical forreplacedpaths; pinnedS1tests/builds unchanged,
predecessors preserved under newaudit. File rollbackcannotundo savedcleanup.
J1 EMPTY-title USER-pass10/10; selectedquesttitle not separately reverified.
No new activity adapters or combinedalpha readiness. No commituntil livepass.

Latest2026-10-09T19:49:48Z: JOURNAL LABEL J1 INSTALLED with game closed
unsandboxed. One new redscript, zero replacements;1799 protected files unchanged,
actual hash and ValidateRollback PASS. Empty post-Tower details title now uses
localized UI-PanelNames-JOURNAL, only when no current quest is selected after
native root initialization. Stock quest_log widget contains authored "For Whom
the Bell Tolls" sample; native empty-panel init never replaces it. Native Setup
and selected quest titles unchanged; no facts/journal/tracking/save-field/cache
writes. Ten completed-Tower facts read-only gate; pre-Tower native pass-through.
Both compilers/fullSCC EquipmentEx/readback,8192 predicate-model cases and
one-file recoverable deployment fixture/5 refusals PASS, NOT visual engine proof.
Next cold-launch check empty page says Journal, then select completed Only Pain
and confirm its title. Recovery ONLY tools/deploy_journal_label_j1.ps1; preserve
pinned research/journal_label_j1 tests/receipt, no rerun compile after installation.
S1 USER+LOG pass: encounter/dialogue, mq005_done1, main rewardClaim/Ack1/1,
quest/phase/talk Succeeded, preserved after USER save/reload. Exact cash/XP amount,
alternate routes, cold restart and automatic pre-ending history unproven.
ownerFinished0 is NOT failure proof: last logged post-completion distance from
start waypoint <=34.015m; native cleanup waits >=50m/out of focus plus outside
big trigger/>150m from cars. Leave several hundred metres next session, inspect;
do NOT force completion or cleanup facts.126 other adapters/all completed replay
still pending. Profile/R11/bar-idle deferral unchanged; no combined alpha claim.

Latest USER2026-10-09: G1 R3 override restored gig (USER-pass, not independent
completion/reload proof); authorizes next representative side-job implementation.
ONLY PAIN S1 INSTALLED19:20:25Z gameclosedUNSANDBOXED:4 additions(archive/XL/
S1reds/getterlogger),1 backed-up R3 ActivityState replacement,1777protectedfiles
unchanged.5 actualhashes+actual ValidateRollback PASS. Own native owner/combat
copies behind inert no-prefab request gate; original #mq005_pr_alley binding,
127native nodes/scene/dialogue/combat/departure cleanup retained. Native scene
cast3officers/corpo/2cars+Player; noJohnny. No test .quest(debuglifepath/godmode).
Source normal admission q001done>0/q005done>0/q101_enable_side_content>0 kept;
S1 fresh ONLY:6journalentries Inactive,7encounter/scene facts0,POIInactive/Active,
completedTower+archiveRev1+no wanted+ownunused flags; no terminal/progress resets.
No manualjournalwrites; native encounter activates children on approach.
Owned one-shotrequest/inflight/epoch/faultjournal; main completionreward native
Claim/Ack, scene monetaryrewards unchanged (not separately instrumented/proven).
Automatic S1 additionally needs pre-ending availablePOI/source-audited pristine
stage proof, sampledtwice inownhistory; new persistent sideFreshObserved defaults
false inold saves; cutoff may onlydowngrade. Definition/schema/fingerprint andold
persistentfields unchanged. Old history does NOT manufacture new freshness proof.
R3 Override("mq005_alley","fresh","DISPOSABLE_SAVE") nowdelegates S1; resume/
replay andotherunsupportedadapters refuse. G1 exactresume unchanged;126other
adapters andALLcompletedreplay pending. Notfullrestoration/endingalpha-ready.
Bothcompilers/fullSCC EquipmentEx/readback,26guardmutants/47270abstractadmission
cases,4Lua logger checks (cdata/diskfailure),3resource packedreadback, mixedfile
fixture/recoverablerollback/7refusals PASS; NOT engineproof. Nextcoldlaunch
disposableTower save, Inspect/Override OnlyPain, closeCET/safe wait, followmarker
inVistaDelRey, nativechoices/combat/completion/departure, separatetestsave/reload.
Ifrefused sendInspect; neverforce facts or completed replay. S1 logs every2sec
getteronly underPTFR_SideJobPilotS1. Only deploy_side_pilot_s1.ps1 for5file
recovery; oldR3installer/receipt historical for replacedstate file. File recovery
cannotundo savednativeeffects; preservepretestsave. No cache/save deploymentwrites.
Evidence research/side_job_pilot_s1/assessment.json+receipt/tests. DoNOT rerun
predecessor-pinned R3test/installer nor rebuildS1overinstalledevidence. Profile
HP150/Body3/Relic/chrome/R11/baridledeferral unchanged; no commituntil livepass.

Latest USER follow-up2026-10-09: pre/post71 audit DONE. Both complete/stable
native snapshots:16:46:31Z PRE/16:46:55Z POST,970entries+1447facts each,
zeroerrors/drift/delayed.9completed(inclG1 nowSucceeded),5started cleanup,
56inactivejournal candidates NOT proven fresh/nativeunlocked,1ambiguous
DesperateMeasures: arr_12_fail_loop_start1 both, actualfailed0 both; monitor
name is NOT failure proof. live_pair.json + live_pair_summary_20261009.json;
runtime_admitted0. No rerun needed, gamecanstayclosed.
USER explicitly now requests production pre-ending SAVE-LOCAL history and
post-ending CMD OVERRIDE for BOTH gigs and sidejobs, including optional
completed replay for testing/userchoice. Will replayending/firstalpha ONLY
after gig+sidejob restoration ready. This supersedes preserve-completed ONLY
for explicit per-activity replay override; DEFAULT still preserves completed,
rewarded and genuinefailures. Override history != universal technical/story/
profile bypass. Per-activity replay adapter required; no blanket reset/rewards.
ACTIVITY HISTORY R3 FOUNDATION INSTALLED17:16:06Z gameclosedUNSANDBOXED:
THREE additions(2reds+thinCETbridge),0replacements,1759protectedfiles unchanged,
actual3hashes+ValidateRollback PASS. research/activity_state_r3/install_receipt.json;
ONLY deploy_activity_state_r3.ps1 for exact3file recovery.71gig+57sidejob
exactjournalIDs,1695unique entries+2192factreads; nativefactsourced47/57side,
10sourcebindings pending (doNOTinferfreshfromjournalonly). Save-local own
struct states/optional/tracked/objectivecounters/facts/schema/CNamefingerprint.
Double stable ordinary-world samples,5sectimer and selectedjournal invalidation;
q115/q307PONRlistener freezes lastclean sample ONLY age0..6/ready/nodirty.
Latepostload cannot manufacturebaseline; unknown freeze uncertified. Saved
fingerprint/shape/cert mismatchfaults, no migration/resnapshot/replay. Freeze
listener timing/actualserialization/reload/performance LIVEUNPROVEN; no official
ending patches or native fact/reset writes. Auto after genuinely completedTower
dispatches ONLY existing exactG1 continuation; other127 adapters pending.
Commands via GetMod("PTFR_ActivityStateR3"):Status(),CaptureBeforeEnding(),
Inspect(id),RestoreSelected(),Override(id,mode,"DISPOSABLE_SAVE"). Override
onlyG1+"resume" supported, skipsbaseline ONLY; backend exactstage/outcomes
retained. "fresh"/"replay" and allside adapters REFUSE withoutmutation.
COMPLETED REPLAY IS NOT IMPLEMENTED. Do NOT present installedfoundation as full
request/alpha-ready/allactivity restoration. CLI+fullSCC EquipmentEx/readback,
14guardmutants/752models/4Lua bridge checks,3filefixture/4refusals PASS; NOTengine
proof. G1/profile150Body3Relic/R11/baridles unchanged. Do not rerun generation/
compile/test main over pinned installedevidence. Next remaining work per-owner
fresh/continuation/replay adapters incl representative SIDEJOB, no new live
request or endingalpha yet. No commit without livepass.

Latest USER 2026-10-09: G1 "everything worked", then requests all gigs and
chooses broader71 whitelist (ignore_two_year_gap), preserving completed/rewarded
and genuine failures; prior starts continue ONLY where saved stage is supported.
This broadens requested gig work beyond the single G1 exception; no blanket
restart, tier forcing, reward replay or side-job policy change is authorized.
G1 trace515rows (15:43:52Z..16:01:06Z) records quest/phase/inside/authorization/
van/delivery/exit Succeeded, finished1/fail0/delivery2, RewardClaim/Ack1/1,
CounterAck1, Watson3->4 once, fault0, foreigncvi02 Inactive/required/untracked.
OwnerFinished0 near dropoff: native departure/cleanup gates still pending,
NOT proven failure; independent cold-reload/failure/exactcashXP trace absent.
See pilot_r1/live_result_20261009.json. G1 four installed hashes unchanged.
R2 maps ALL71 exact native journals/resources,970entries+1447facts. READ-ONLY
BATCH AUDIT INSTALLED 2026-10-09T16:33:00Z gameclosed UNSANDBOXED: TWO CET
additions/zero replacements,1582 protectedfiles unchanged,actualhashes and
ValidateRollback PASS. Receipt rollout_r2/audit_install_receipt.json. Restores
ZERO new gigs; no game/save/story/cache/activation writes by audit.10offline
audit cases and2filefixture/4refusals PASS, nativebindingLIVEPENDING. Never
claim whitelist restored from catalogue/source/mock success. Next user runs
GetMod("PTFR_GigAuditR2").Capture() once in matchingPREending baseline and
once in currentPOSTTower, eitherorder; keepCETopen/standstill until COMPLETE
stable before changingworld. Then gamecanclose, no save needed. Analyzer
tools/analyze_gig_rollout_r2.py classificationonly/runtime_admitted_count0.
Per-gig unlock/start semantics/cast/hazards/stage/reward/counter review required
before restoration adapters. Only deploy_gig_audit_r2.ps1 for exact2file
recovery; preserve current tests/receipt and G1 pinnedartifact. Character
implant-focused150/Body3/Relic/R11 unchanged; baridles deferred. Prior docs-only
holds below historical; latest71 request authorizes implementation after guards,
not fact/reset bypasses. Standing auto-install remains subject gameclosedcheck.

Latest USER 2026-10-09 explicitly requests choose one of six visible PRE-ending
gigs, IMPLEMENT AND INSTALL. Many Ways to Skin a Cat G1 is selected as ONE
opt-in started-stage continuation exception; strict fresh-only remains default
for other jobs. This supersedes docs-only/no-install/ManyWays-hold instructions
below ONLY for G1. G1 INSTALLED 2026-10-09T14:35:10Z gameclosed UNSANDBOXED;
four additions/zero replacements, 1719 protected files unchanged, four actual
hashes + ValidateRollback PASS. Receipt research/gig_restoration/pilot_r1/
install_receipt.json. Preserve pinned build/tests/receipt; do not rebuild over
installed evidence. Live path/payment/reload
still pending; no whitelist-wide pass or automatic save activation. New boot
gate has NO prefab binding; native_owner behind Request preserves original
#loc_sts_wat_nid_02_streetstory binding. Native gameplay/parallel owner/cutlinks
kept; play input only inside+content token, no start/brief/loot repeats. Foreign
cvi02 journal node replaced transparent relay, native text debrief fallback,
native reward claim/ack, one guarded Watson3->4 bridge. Exact observed stage
admission, persistent no-replay journal. Four addition-only files, no vanilla
replacement/profile/R11/cache/save changes at deployment. Use ONLY scoped
tools/deploy_gig_pilot_r1.ps1 after checks+unsandboxed game-closed verification.
Standing automatic installation approval applies. File rollback cannot undo
saved quest effects; disposable pre-test save required. See pilot assessment
and docs/gig_pilot_r1_check.md. Bar NPC idles remain deferred.

Latest USER pre-Tower journal screenshots supersede tier-fact candidate guesses.
VISIBLE ACTIVE GIGS: Dancing on a Minefield, A Lack of Empathy, Talent Academy,
Treating Symptoms, Many Ways to Skin a Cat, Rite of Passage. Each has an active
objective in the pre-Tower journal; under approved fresh-only rule, none of
these six may be restarted post-Tower. Visible side quests include Epistrophy,
Motorbreath, Small Man Big Mouth, No Easy Way Out, The Gig, Judy message,
Tomorrow Never Knows, Fool on the Hill, Beat on the Brat, The Gift. Do not
infer unseen activities from these crops. Race to the Top is NOT shown in the
user's available-gig screenshots and is withdrawn as next pilot; do NOT ask
the user to run its CET probe on this basis. Its source tier1/save audit remains
historical research, not availability proof. No gig implementation/install.
To restore one of the visible started gigs would require the separately chosen
less-strict continuation rule, not an inferred fresh pilot. Preserve profile/R11
and bar-idle deferral. See research/gig_restoration/race_to_top_assessment.md.

Latest gig correction: Serial Suicide (`sts_cct_cpz_01`, Dino/Corpo Plaza) is
NOT the first pilot. Exact root path requires `sts_cct_cpz_tier_2>0` OR
`debug_sts_start>0`; tier-one node has no path to its owner. Inspected saves
record tier1 but no stored tier2/debug gate. Read-only CET pre/post snapshots,
including two agreeing post runs, show 11 selected journal entries Inactive and
local start/finish0, but probe read tier1 not tier2. Freshness is supported;
normal native unlock is NOT. Do not force tier/story facts or implement CPZ01
under fresh-and-eligible policy. Broaden candidate search beyond bounded32.
See research/gig_restoration/fresh_candidates/assessment.md. No gig runtime,
game, save or story writes. Preserve current profile/R11 and deferred bar idles.

Latest USER POLICY supersedes prior resume work: default quests/gigs are FRESH
SELECTED ONLY. Unfinished activities started BEFORE ending become/remain Failed
and unavailable; preserve completed/rewarded and genuine failures. Explicit
selection+compatibility+native eligibility+audited freshness required. Map discovery,
auto-Active journal or absent/zero facts alone do not prove fresh; unknown refuses.
Cutoff is ending boundary, NOT each reload: legitimately fresh postTower starts
may continue/save/reload. No q307 interference or blanket main-story failure sweep.
Possible LESS-STRICT mode may later allow selected prior starts for playability;
not active/implemented, opt-in/stage handling needed, no blanket reset/reward replay.
ManyWays is EXCLUDED on tested saves (start1/combat1); next audit another fresh
pilot, NOT its resume adapter. Keep prior captures/JSON/source findings historical
and unchanged. Canonical ROADMAP quest-and-gig-eligibility +assessment/save_audit/
PROJECT/checklist aligned. DOCS ONLY; no build/install/save/runtime changes or new
live test. Preserve current profile/R11 and bar-idle deferral.

Latest gig follow-up: v2 captures2026-10-09T00:20:00Z/00:20:21Z (Oct8local)
COMPLETE,22native states+25facts each/zeroerrors. PRE/POST classifiedbyfivefacts,
notlabels. ManyWays root/phase/inside2->4; tenotherobjectives1->1; completed
lch05/cvi02 remain3, foreignobjective1/required/untrackedunchanged. POI1both:
doNOTclaim thispair provesmarkerhiddenbyTower. OnlysixTowerfacts differ; current
start1/combat1/finished0/fail0 unchanged. Consistentcleanup, notexactancestry/
ownerresumption/paymentproof. Current live_probe.lua externallychangedto1byte d
at20:20:36local; PRESERVED, notrunnable. Both loggedcommands hashmatchtestedv2
withLF320A348D365815274A5E5445F4C46708DF31E7C96DEDCAC41882765A7D7CA7DE;
logsneverexecuted. Historicalv1/38testrecord unchanged. Newanalyzerrevisionfilter
and12offline testsPASS; live_pair_v2_20261009.json andresume_stage_20261009.json.
25sourceedgespinned: normalIn1 repeatsadditivestart/glossary, checkpointbriefing,
worker003shardinjection. Native retrofix279->50Succeeded SKIPSunfinishedinside.
Hub79 alsodoorForceOpen/vanlocks, notsafeentryproof. No newlive test;gamecanstay
closed. Next offlinegameplay/community/PS/van/loot/death audit before guarded
resumeimplementation. No gigimplementation/install/savewrites;12restriction
hashesunchanged, R11/bar-deferredpreserved. Read updatedsave_audit.md/ROADMAP.

Latest 2026-10-08 live gig probe: user ran PRETower then POSTTower. CET records
23:37:35Z and23:39:21Z confirm order via Towerfacts despitebothlabelsPOST_TOWER.
22exactentries resolve, hashes/IDs/optional/tracked read;25factreads successful.
Both start1/combat1/finished0/localfail0, tiers1, Watson3; notuntouched. All22
state reads UNKNOWN from OUR v1 EnumInt type assertion, not nativequestfailure.
CET EnumInt routesUint64; existingP2normalizescdata. Probev2 converts ONLY state
cdata->bounded0..4number and retains rawenum/type; no64bitIDconversion.38LuaJIT
checksPASS incl v1failure reproducer and0..4signed/unsignedcdata. V2notliveyet.
User needs rerun updated research/gig_restoration/live_probe.lua on pre/post,
eitherorder, no label editrequired whenTowerfactsconsistent. No installrequired;
no gameplay/savewrites. Oldprobe+24testrecord retained. Read live_pair_v1_20261008
and live_probe_v2_validation.json. Never inferstatefrom failed getter/opaquebytes.

Latest 2026-10-08 follow-up: user says proceed after read-only save-audit proposal.
READ-ONLY AUDIT completed, no gig implementation/install/activation. AutoSave-12
and ManualSave-6 postTower Body3; PointOfNoReturnSave-1 matching IDs baseline;
ManualSave-9 newer PRETower different PONRid. All4 parse+save/metadata hashes
unchanged. ALL4 nid_02_start=1 and combat_triggered=1; finished/fail/delivery
ABSENT, not assertedzero. Corrects early commentary prematurely claiming no
start. ManyWays NOTuntouched; HOLD new-start pilot, preserve stage. Tierboth1,
Watson3/Hands4; lch05/cvi02 terminal1. Opaque journal raw+4 differs2->4 on
quest/phase/inside, NOT decodedstateproof. 3savedjournal samples unchanged.
Read research/gig_restoration/save_audit.md and evidence. Getter-only one-line
live_probe.lua (22journal/25facts),24LuaJITmock checksPASS, NOTlive. User next
loads disposable postTowerAuto12/manual6 then PONR1baseline and pastes command;
no installation needed. Don't invoke TowerJournal repair-capable methods.
All12 installed restrictionhashes match; R11/profile150/Body3/Relic unchanged,
baridlesdeferred. Research/probe tools only; no savewriter/game/cache changes.

Latest 2026-10-08: user accepts character nerf milestone and prioritizes GIGS
FIRST activity RESEARCH. No gig implementation/install/activation/save writes.
Read research/gig_restoration/assessment.md and its linked lifecycle/fixer
evidence; candidate details in research/activity_gigs_candidates/candidate_evidence.json.
Tower can bulk-fail Active gig journals/hide POIs before base-root termination;
Failed alone cannot distinguish genuine failure from Tower cleanup. Preserve
completed/rewarded/genuinefailed; old in-progress needs stage provenance, never
blanket restart. Global streetstory/fixer loops risk repeated additive counters
and final rewards. Scoped first candidate Many Ways to Skin a Cat(nid02) has
3 reviewed non-Johnny casts and PersonalLink objective, NOT proven safe: device/
Body3 access, saved stage, phones/reward/reload and connected cross-gig journal
OptionalProperty node92 require audit. PlayingforKeeps/GuineaPigs haveJohnny;
Empathy has story/service overlap. Research titlejoin73baseentries NOT census.
No runtime/game/save/cache edits; all12 installed restriction hashes verified.
Keep implant-focused150/Body3/Relic/chrome policy and R11; baridles deferred.
ROADMAP/checklist now gigsfirst. Standing installation approval applies only
to separately requested implementations, not this research. No live claims.

Latest 2026-10-08T19:46:28Z: IMPLANT-FOCUSED PROFILE R3.2 INSTALLED under standing
approval with game closed unsandboxed. User preserves strict profile, relaxes
ONLY other-tree physical bans; explicitly keeps Body3/allBody blocked, Relic
closed, HP150. Five strict JSON files byte-unchanged. profiles/active.json selects
tower_implant_focused revision1 fingerprintEA4423FBE8A6DF1A3977417061BB8E582522C4EA9DFACCA5BC92F3906EDFD7D0.
93allowed/95blocked: other53 vsold74; reallows19Reflexes+2Cool physical/dependency
perks. AirKerenzikov/quickhack/smart/cyberware+dependency bans kept; RoadWarrior
wholemixed+LuckyDay dependency kept. Directstamina/chrome/smartadapter unchanged.
Exact strictv1/100 orv2/150 ->newprofile onrestore ONLY enabledstage1..4,
notinflight,oldID/hash/HP/ordered74 andexactnewdefinition/subset. Changesonly
profileID/blocked/HPtarget/revision/fingerprint; no stage/snapshot/counter reset,
noVitals optin, rankrestore/pointgrant/refundreplay/faultrepair. Stage2 continues
remainingnewbans; stage4 acceptsordinaryperkrepurchase. Oldcounters historical.
No activation of unused FullNerf saves. Unknown/inflight/faulted stillrefused.
TWO backed-up R3 definition/policy replacements,0adds/removals,1487othertracked
files+5cacheDBhashes unchanged.10otherrestrictionscripts byteidentical.Receipt,
actualhashes,ValidateRollback PASS in profile_implant_r3_2. ONLY scoped installer
deploy_restrictions_profile_implant_r3_2.ps1 forrecovery; olderR3/R3.1 historical
forthesepaths. File rollback doesnot revert savedprofile; preservepreupdatesave.
CLI+fullSCC inclEquipmentEx/compiledreadback PASS;768state+768repeat/606partial
transitions/10232postswitchranksteps/20guardmutants, new514allocation+16913rank
model andoldstrictmodel PASS.15definitiontests pre/postPASS;2filefixture+18
refusals PASS. NOTengineproof. No save/story/cachewrites. Read assessment.md
in profile_implant_r3_2 and docs/restriction_profile_r3_check.md. No commit until
livepass. Never rerun predecessor-pinned test/fixturemain after installation.
R11/world untouched; baridles stilldeferred.

Latest 2026-10-07T22:42:04Z: user changes maxHP to150; standing auto-install
approval used. HP R3.1 INSTALLED gameclosed unsandboxed: TWO backed-up replacements
(R3 ProfileDefinition.generated/ProfilePolicy),zeroadditions/removals;1460other
trackedfiles+5cache/DBhashes unchanged. Actualhash/receipt/ValidateRollback PASS
under research/restriction_profiles/profile_hp_r3_1. Only this scoped installer
for recovery; oldR3 sevenfile installer is now historical for these two paths.
Profile revision2 fingerprint117BF6C7A6E0FE29A4E64C7A0583DB9E3A9914D5FE8C42F82637D5D6DB8DE1E1.
Exact reviewed v1/100 ->v2/150 metadata upgrade onrestore for enabledstage1..4,
notinflight,oldID/hash/HP/selection andnewdefinition exact. Changes ONLY saved
HPtarget/revision/fingerprint. No stage/snapshot/refundcounter reset, noVitals
opt-in, no clearingfaults. HP-active saves adopt150 nextload; noVitals staysOFF.
All remaining10restrictionfiles inclphysicaladapter unchanged; no perklist/
stamina/whitelist/smart/worldchanges. Future unknownrevisions stillfailclosed.
CLI+fullSCC inclEquipmentEx/readback PASS;288savedstate+288repeat/64HP150cases,
10guardmutants+oldperkmodels PASS, NOTengineproof.13definitiontests pre/post
install PASS;2filefixture recovery+18refusals PASS. No save/story/cache writes.
Retain pre-update disposable save: file rollback does NOT downgrade a savedv2
fingerprint. Do not rerun predecessor-pinned tests/fixtures against newinstall.
Docs/checklist now150. FullNerf command unchanged. Bar idles still deferred.

Latest 2026-10-07T22:10:52Z: user explicitly requests implement/install.
MODULAR PROFILE R3 INSTALLED gameclosed unsandboxed: THREE backed-up replacements
(R1 CyberwarePolicy, R2 BodyPolicy/DevelopmentHooks), FOUR R3 additions, zero
removals; 1439 other tracked files+5 cache/DB hashes unchanged. Actual hashes,
receipt and ValidateRollback PASS in research/restriction_profiles/profile_r3.
Use ONLY deploy_restrictions_profile_r3.ps1 for seven-file recovery; prior
predecessor-pinned installers/tests are historical. Never rerun R3's predecessor
test/fixture after installation without accounting for the receipt.
Profiles JSON now build-time compiled, NOT hot-loaded. Strict schema1/revision1
fingerprint995DFBEA743A4FD89745DA7A5F880B033057D6AF470C57546C305E8DD17E31A1.
116 blocked/72 retained: existing Body33/Relic9 journals unchanged, separate R3
journal native-refunds selected other74 leaf-first, actual purchased ranks only.
R2 persistent fields/reset/sale/Same/IncludeRelic unchanged; R3 waits legacy
stage4, snapshots legitimate subsequent progress, exact synchronous rank/Primary
ack before counters; drift/interruption/profile mismatch fault without replay.
Native capacity/slot admission, empty allSkeleton/Skin incllocked, emptyHands2;
one owned normal Casius relocation into emptyHands1 preservesquantity/parts.
BothHandsoccupied waitsplayer. Exact stock BuiltDifferent missing91068214685
binding returnsNone ONLY ownsale/level0/matchingabsence; no inventedpackage.
188 fullrecord/tier/prereq/level/package checks; obsoleteenum purchaseblocked,
nonzeroobsoleteownership refusesactivation. All selected forceBuy+UI guarded.
HP100 owned unsavedmultiplier with readback/poolack; one negative-only correction
perchange, no replay/refill/foreignmodifier removal. Quarter-second feedback,
NOT instantaneous hardenginecap proof. Stamina no DIRECT changes; refunded
perks can remove vanilla stamina benefits. Smart ban also underCyberwareOnly:
ownedHasLink/lockcountzero, nativeShootStraight beforefire/attach, handlerfalse
inclvehicle, ownedweaponflagcleanup. Native homing/foreignflag coexistence and
HP currentpool/buffs/reload LIVE UNPROVEN; compiled calls are not effect proof.
No profile autoactivation from install: CET R3 ProfilePolicy.FullNerf() includes
HP; FullNerfWithoutVitals() excludes directvitals. OldR2noVitals delegatesR3.
After novitalsstage4 FullNerf enablesHP only; no backwardsHPtoggle added.
GetStatus()/Measure()/GetAudit(), stage4completion, disposable pretestsave.
CLI+fullinstalledSCC inclEquipmentEx+compiledreadback PASS;12 guardmutants,
514otherallocations/23775ranksteps/2056repeats/74interruptions,48HP/64scope/32hand
models plus oldBody/Relic models PASS.13definitiontests PASS pre/postinstall.
7filefixture/recoverablerollback+31refusals PASS. All models are NOT game runtime.
No save/story/cache writes or activation. Read docs/restriction_profile_r3_check.md
and profile_r3/assessment.md. AcceptedR11/otherworld untouched; baridles deferred.

Latest 2026-10-07T21:27:12Z: user clarifies Casius permission is COSMETIC ONLY;
smart targeting must remain banned. Prior no-practical-SmartLink claim was too
strong: empty equip packages are NOT effective-runtime proof. BOTH exact Casius
items remain allowed; functional denial takes priority, targeting adapter NOT
implemented. User explicitly approves all69 proposed other-tree bans plus the
five remaining smart-targeting perks: other74 +Body33 +Relic9 =116 blocked,
72 retained of188 exposed modern perks. All8 smart-branch perks blocked; keep
EyeintheSky/ForceKillCypher and four optional sustain perks. No numeric stamina
change; future final maxHP100, clamp without healing, not base100+buffs.
MODULAR SOURCE DEFINITIONS CREATED, NOT RUNTIME INTEGRATED OR INSTALLED:
profiles/tower_strict/profile.json references separate vitals/nerf_rules/
cyberware/perks files, exact13 cyberware records and72-perk whitelist, compact
source-pinned188 catalogue. Installed ban remains Body/Relic42, others146 not
yet refunded. Whitelist shorter for expanded116-vs72, blacklist shorter for
current42-vs146. Unknown/changed perk catalogue refuses BEFORE mutations;
unknown cyberware denied installation with ownership retained. Profile ID,
revision,resolved hash and journal must be save-local; explicit migration,
no repeated Body/Relic refunds, no automatic JSON activation/hot-reload.
tools/validate_restriction_profile.py +test_restriction_profiles.py:13 test
methods inclnegative/schema/path/dependency checks PASS; runtime_ready=false,
--require-runtime exits3 intentionally. Eight installed restriction hashes
unchanged. No runtime/game/save writes, no new installer. See profiles/README.md
and research/restriction_profiles/modular_profile_v1/validation.json.
Next runtime work: loader/journal extension, owned100HP/no-free-heal adapter,
functional smart-targeting denial (NOT just perks/UI), native other-tree refund
guards inclsafe Hands-slot2 tattoo relocation forAmbidextrous, unresolved Built
Different level91068214685. Auto-install approval remains for tested requested
runtime implementations, not claiming source JSON is a working deployment.
Historical other_perk_policy.json classifications/pins deliberately preserved;
profile is latest approved selection. R1/R2.2/R11 preserved; bar deferred.

Latest 2026-10-07T21:08:57Z: user chooses future MAX HP100, no stamina change;
numeric vitals NOT implemented/installed this turn. Live Measure screenshot:
Body3, HP368/368, stamina100/100, Primary15, Relic9, overridesOFF. Relic tile
absent screenshot matches intended fullhide, NOT rank/effect/reload proof.
Native prechip: neither tile; chip acquired/preSongbird tree: inactive Johnny
placeholder; unlocked: Relic tree. Active FullNerf hidesboth; preTower unaffected,
no storyfact writes. New OTHER-PERK INSPECTION ONLY: 146 actual treeentries
(Int38/Tech34/Ref37/Cool37), obsolete Cool_Right_Perk_3_3 excluded. Proposed69
wholeperks (48 cyberware/dependency +21 physicalFullNerf), NOT userapproved or
implemented. Keep otherattrs/skills/XP. Five smarttargeting perks need explicit
tattoo exception decision; keep EyeintheSky+ForceKillCypher utility. Optional
sustain4 (Parasite,CreepingDeath,ActofMercy+Pounce) not silently banned. LuckyDay
included only byAllThingsCyberdependency; LeadAndSteelwholeban forcesordinary
bladechildren too. Proposedcounts NOT actual purchased refunds. Native capacity/
slot guards matter; approved tattoo inHands slot2 blocksAmbidextrousrefund until
safe relocation, no force/delete. BuiltDifferent levelhash91068214685 unresolved
must auditbefore implementation. Exact IDs/descriptions/prereqs/classification:
body_stats_design/other_perk_policy.json/.md; fresh treeaudit+stockDBhashes match.
InstalledRelic4 hashes unchanged, no runtime/game/save writes. Automaticinstall
approval applies to requested implementations, not this requested recommendation.

Latest 2026-10-07T20:40:51Z: user explicitly requests install and grants standing
approval to automatically install future requested fixes after checks pass;
do not ask redundant install confirmation. Still verify game closed unsandboxed
before writes; if running, stop deployment without killing it. This approval
does not expand feature scope or authorize save/story edits.
RELIC R2.2 INSTALLED gameclosed unsandboxed: TWO backed-up replacements
(BodyPolicy/DevelopmentHooks), TWO additions (RelicCatalogue/RelicMenu), zero
removals,1422 other tracked files+5 cache/DB hashes unchanged. Exact installed
hashes/receipt and actual ValidateRollback PASS; workspace fixture install and
recoverable rollback+23 refusal cases PASS. Receipt/backup under relic_r2_2.
Use ONLY deploy_restrictions_relic_r2_2.ps1 for these four-file recovery; original
R2/R2.1 receipts are historical for the replaced paths. File recovery cannot
reverse saved refunds. No runtime activation/save/story/cache writes, no live
Relic pass. Cold launch disposable completed-Tower save; same FullNerfWithoutVitals
command explicitly includes Relic in old Body-only save without replaying Body
refunds; close CET/safe wait, GetStatus stage4, Measure. DirectHP/stamina unchanged.
Read docs/relic_restrictions_r2_2_check.md. Preserve source/tests/receipt pins;
do not rerun predecessor-pinned tests/installers against updated installation.
R1/Casius/costfix/R11/world work preserved; bar idles deferred. Supersedes
NOT INSTALLED below. Automatic install preference does not auto-activate saves.

Latest 2026-10-07T20:30:45Z: user says Body "seems to be working", requests
all Relic perks removed, explicitly chooses refundpoints+blockperks and adds
"also close off relic entirely". BODY partial USER-pass: screenshot Body3,
Attribute available17, Primary available15; console refunded14 Body ranks/17
Attribute points, stage3 unsafe-wait. NOT stage4/vitals/reload proof.
RELIC R2.2 WORKSPACE IMPLEMENTED/OFFLINE PASS, NOT INSTALLED. Same FullNerf
command on fresh activation includes Relic; old Body-only saves explicitly call
same command -> IncludeRelic, never replay completed Body refunds. Schema1 old
fields retained, new relicEnabled defaultsfalse; installation alone no mutation.
Stage1-3 requires unchanged journal; stage4 mustBody3/ranks0 then fresh snapshot
of current nonBody progress->stage3 only. Epoch invalidates queuedoldsteps.
Native system SellNewPerk,9 stockone-rank Relicperks/6dependencies,3 milestones
refund3 each+6 childrenrefund1 each (15 max), Espionage.spent unchanged. Safe,
chrome settled+emptyArms slot guard avoids Jailbreak's Monowire part-removal
branch. Exact snapshot acknowledgement then counters/UI; faultno replay. No
forcedselling/manualpointgrant/Relicfact/globalreset/HPstaminapoolwrites.
Relic UI: hidescategory+Johnnyplaceholder, hidescategorypointdisplay,5-tabcycle,
directopen/delayedinit/intro denied whileactive; no ep1_tree_unlocked writes.
Backend inclforceBuy+UI purchase guards; NoNerf existingpass-through unchanged.
Tests relic_r2_2/tests.json: CLI+fullSCC EquipmentEx,compiledhelpers,16native
anchors,13 sourcemutants,2560 allocation/stage+7680repeat+9interrupt+6wrongdelta
cases,overflow/drift/scope/46menu models+originalBody models PASS,NOTruntime.
2 replacements BodyPolicy/DevelopmentHooks +2 additions RelicCatalogue/RelicMenu;
R1+BodyCatalogue unchanged, installedR2.1/R1/R11+cachehashes unchanged. No game/
save/story writes. NO newinstaller/fixture yet: next explicitinstallapproval,
unsandboxedclosedcheck,scoped2replace2add deployment+fixture required. Do not use
old R2/R2.1 installer against changedworkspace or overwrite historical evidence.
Read relic_r2_2/assessment.md and docs/relic_restrictions_r2_2_check.md. Bar deferred.

Latest 2026-10-07T19:59:34Z: user explicitly says "install the fix". Cost fix
R2.1 INSTALLED gameclosed unsandboxed: ONE backed-up DevelopmentHooks replacement,
zero additions/removals,1407 other tracked files+5 cache/DB hashes unchanged.
Actualhash0BF91CD59E8D8414ED57BF44DED0067FED847CDAD0BFB4B85462E678A6316D6D
verified; predecessor49D3BB837704DA60F2A2B300D991025B7A01EC0E9ABA2FB59621A41760317DAB
backed up under body_cost_r2_1. Installreceipt+actualValidateRollback PASS;
workspace fixture install/recovery+12 refusal cases PASS. Only scoped
deploy_restrictions_body_cost_r2_1.ps1 for this file recovery; olderR2/R1
installers and R2 original receipt are historical for DevelopmentHooks.
No runtime activation/save/story/cache writes. No live cost/refund/catalogue/
effect/UI/reload pass yet. Cold launch disposable save, FullNerfWithoutVitals,
close CET/safe wait, GetStatus then stage4 Measure. HP/stamina logic unchanged.
Originaltests/receipts preserved; do not rerun predecessor-pinned tests against
patched installation. OtherR2/R1/R11/world work unchanged; bar idles deferred.
Supersedes NOT INSTALLED below. See docs/body_restrictions_r2_check.md.

Latest 2026-10-07T19:53Z: live R2 command compiles/resolves but refuses BEFORE
refund. Snapshot valid=true Body/effective20 spent47 free0 perkFree0 costsOK=false.
User curve trace and CET15:39:40-0400 confirm level5=1.00038397, other4..20=1.
Raw Float equality was WRONG: native GetAttributeNextLevelCost casts toInt32.
WORKSPACE correction only DevelopmentHooks.PTFRR2CompatibleBodyCosts: bounded
finite raw value then identical Int32 conversion, require effectivecost1.
Candidate0BF91CD59E8D8414ED57BF44DED0067FED847CDAD0BFB4B85462E678A6316D6D.
NOT INSTALLED; installed49D3BB837704DA60F2A2B300D991025B7A01EC0E9ABA2FB59621A41760317DAB
and allotherR2/R1/R11 receipt paths unchanged. No game/save/story writes.
body_cost_r2_1/tests.json PASS: observed-value regression,13 scalar boundaries,
1377 invalidcost-perlevel cases,8 costmutants +16 historical guardmutants,
original accounting models, CLI+fullSCC inclEquipmentEx, compiledcast readback.
Historicalvalidator normalizes only costmethod; newmethod independentlychecked.
NOT live cost/catalogue/refund/UI/effect/reload proof. DirectHP/stamina untouched.
Next install needs authorization+unsandboxed gameclosed and scoped ONE backed-up
DevelopmentHooks replacement/fixture/receipt; do NOT rerun predecessor-pinned
R2 installer or overwrite historical tests/receipt. No new installer prepared.
Read body_r2/assessment.md and docs/body_restrictions_r2_check.md. Bar deferred.

Latest 2026-10-07T18:39:02Z: user explicitly says "install". BODY R2 INSTALLED
with game closed (unsandboxed): ONE backed-up R1 policy replacement + THREE R2
additions, zero removals,1371 other tracked files + five cache/DB hashes unchanged.
Receipt body_r2/install_receipt.json; four actual installed hashes and actual
ValidateRollback preflight PASS. No runtime/save/story writes or live test.
Normal+Advanced Casius now both installed; original R1 receipt is historical for
the replaced CyberwarePolicy path (current D9CF279E8FB15BA2319CB6CFBB1D2B1E71656B691986D202D9F89CEA95D3CBD1),
other R1/R11 files unchanged. Do not rerun predecessor-pinned build/install tests
against the changed installation without accounting for the current receipt.
Cold launch disposable completed-Tower save, use FullNerfWithoutVitals(), wait
safe gameplay, GetStatus stage4, then Measure(). No automatic Body activation;
permanent Body3/refund requires this explicit command. Numeric HP/stamina layer
still NOT implemented; read-only measurement only. Runtime refund/effect/UI/
save-isolation tests remain pending. The prior nil error was observed BEFORE
installation: R2 directory and receipt were both absent, not a runtime R2 fail.
Only deploy_restrictions_body_r2.ps1 file rollback; it cannot undo saved refunds.
Use docs/body_restrictions_r2_check.md. Other world work unchanged; bar idles
still deferred and Santiago untouched. This supersedes pending-install below.

Latest 2026-10-07T16:13Z: user authorizes implementation, selects Body3 + all
purchased Body perk ranks refunded, ongoing Body/perk purchase block, and says
nerf is irreversible (NO restore/reverse-refund API). BODY R2 WORKSPACE READY,
NOT INSTALLED; async install approval still pending. Read body_r2/assessment.md
and docs/body_restrictions_r2_check.md. Opt-in only, no automatic Body mutation;
CET PTFR.RestrictionsR2.BodyPolicy.FullNerfWithoutVitals(), GetStatus(), Measure(),
GetAudit(). Enables existing cyberware policy, waits for settled exact removals,
then one synchronous native SYSTEM SellNewPerk rank per owned request/tick with
owner/UI events, dependency-safe; native ResetAttribute(Strength)->3 only after
all Body ranks0. Primary unspent+1/rank, spent unchanged; Attribute balances
transfer oldBody-3 once. Exact persistent progression journal/schema/epoch and
readback; in-flight reload or unexpected drift faults without compensation or
replay. Same compares other attrs, ledgers, 189 modern ranks, skill levels/XP,
legacy ranks. Unit-cost/overflow/stock33/41/31-dependency and cross-tree guards.
Body purchase inclforceBuy, pre-grant AttributeBuy and busy global-respec UI
guards; unrelated purchases blocked ONLY during stages1-3. No Level/Solo/XP/
Relic/inventory/facts writes. Existing R1 NoNerf gate behavior unchanged; never
restores refunded progression; completedjournal refuses another refund after
external reinvestment. HP/stamina direct modifiers/pool writes absent; four
stable-max samples + current/max/stat readout. Numerical endurance layer NOT
implemented pending requested baseline/targets; do not claim full numeric nerf.
Three R2 additions + one R1 replacement (Casius allowlist +2 readonly methods),
no new bridge file. R1 policy candidate D9CF279E8FB15BA2319CB6CFBB1D2B1E71656B691986D202D9F89CEA95D3CBD1.
CLI + installed SCC/all dependencies incl EquipmentEx/compiled readback PASS;
16 source mutants,1188 abstract allocations,3564 repeat/load,84 interrupted,
20 drift,64 policy cases PASS, NOT runtime proof. File deployment fixture +12
negative cases PASS; actual read-only ValidateInstall protects1357 files+5caches.
tests.json + deployment_tests.json pin code/installer. No actual install/save
writes. Use ONLY deploy_restrictions_body_r2.ps1 after explicit install approval
and unsandboxed game-closed check; file rollback cannot reverse saved progression.
Original R1/R11 receipts unchanged; accepted world/bar-deferred/Santiago unchanged.

Latest 2026-10-07T14:58:29Z: user requests RESEARCH on new HP/stamina values and
reducing/refunding Body and Body perks. No runtime implementation/install.
Read research/restriction_profiles/body_stats_design/assessment.md and source_checks.json.
Fresh installed-base decompile:56 exact function bodies + native signatures;
stock audit33 Body perks/41 possible ranks/31 internal acyclic dependencies,
tiers4/9/15/20. These are catalogue totals, NOT user refunds. Health/Stamina
max stats distinct from current pools; RequestSettingStatPoolMaxValue REFILLS,
does not set numeric max. Prefer owned runtime refs; group IDs can stack, no
broad saved-modifier removal/Force-Unforce temporary layer. Max/current pool
stacking, same-value foreign modifier retention and no-free-heal LIVE UNPROVEN.
Body=Strength. Native ResetAttribute(Strength) ->3 refunds old-3 across both
Attribute balances; arbitrary target needs scoped transaction. SetAttribute+
AddDevelopmentPoints alone is accounting-incomplete. Refund actual modern Body
ranks via queued SellNewPerk leaf-first, preserve owner/UI events (Adrenaline
rank3 clears Overshield); decay transient cleanup still unproven. Relock ONLY
zero-rank ineligible perks; stale-unlock purchase path skips threshold check.
Solo max60/tiedAttribute0; preserve skills/XP/other trees/Relic/inventory.
True refunds are persistent, not reversible NoNerf overlays after points are
respent. Need save-local migration/ack journal, no replay refunds or stale-build
restore. User must choose numeric targets, buff policy, all-vs-ineligible Body
perks and reinvestment/cap before implementation. No global reset/build/quest
fact writes. R1/R11 receipt hashes unchanged; Casius extension still uninstalled.

Latest 2026-10-07T13:14:36Z: user explicitly whitelists BOTH Items.CasiusTattoo
and Items.AdvancedCasiusTattoo. WORKSPACE ONLY, NOT INSTALLED. Exact one-line
CyberwarePolicy Approved extension; 13 IDs total with unchanged eleven Basic
Kiroshi records. No item swap/grant/effect edit or vanilla-requirement bypass.
Together Forever/Yakuza/SmartLink/Faceplate remain restricted. Both Casius stock
equip packages empty; counterpart points normal->Advanced, NOT proof of a
cosmetic-vs-SmartLink split or live effect absence. Screenshot block cause still
unproven; Advanced was already allowed and owned item ID not supplied.
tools/test_restrictions_casius.py: exact delta, original R1 invariants, four
mutants, full staged installed-dependency compile incl EquipmentEx, compiled
13-ID readback PASS. See tattoo_whitelist_r1_1/tests.json. Installed three R1
hashes and original receipt/tests unchanged; zero game/save writes. Existing R1
installer is addition-only and expects original source hashes: do not use it to
deploy this candidate. Next install needs a backed-up one-file replacement and
its own receipt/rollback, game closed. Other accepted work remains unchanged.

Latest 2026-10-07T04:39:49Z: user explicitly requested implement/install.
Cyberware Restrictions R1 INSTALLED game closed unsandboxed: THREE additions,
zero replacements/removals,1341 tracked restoration/tweak files + five cache/DB
hashes unchanged. Receipt and actual rollback preflight PASS under
research/restriction_profiles/implementation_r1. Default automatic Cyberware Only
at genuine completed-Tower/direct-return markers; save-local mode2 NoNerf. Exact
11 BasicKiroshi upgrade records + AdvancedCasiusTattoo allowed; PersonalLink/
BaseFists/Splinter untouched. Faceplate all3 tiers restricted/normal unequip.
One exact removal/tick after load+gameplay guards, force=false, once/item/load;
part-retention wrapper scoped to own exact removal, quantity+partID/slot readback,
fault latch. Native effects/arms/quickhack cache still LIVE PENDING. Both UI equip
overloads, backend, restore chain, prepayment/replacement, use/heal/equip actions
and hotkey assignment guarded. Separate browsable lock styling; Face/Hands mixed.
Explicit buy-only popup/callback, no auto-install; buyback selling price; original
vendor/funds/wearable checks; unrelated item callbacks isolated. No stock edits.
Installed scc compiler with EquipmentEx/all enabled scripts+dependencies PASS;
headless candidate compile,7 source mutants,64 abstract cases, compiled symbol
readback and workspace install/recoverable rollback PASS, NOT runtime tests.
First compiler timestamp error fixed by workspace cache+timestamp copies; no cache
deployment. Use docs/cyberware_restrictions_r1_check.md on disposable saves.
CET: Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR1.CyberwarePolicy")
methods Enable(), GetStatus(), GetAudit(), NoNerf(). Enable verifies true ending,
changes no story facts; modes refuse menu changes. No save-file writes or build
reset; FullNerf not implemented. R11/Zetatech unchanged; Santiago unchanged;
bar idles deferred. Only deploy_restrictions_r1.ps1 rollback for these additions.
Do not claim live conservation, UI/transaction, reload/save isolation or % gain.

Latest 2026-10-07T00:29:01Z: cyberware-ban RESEARCH ONLY. User wants automatic
application on post-Tower activation (not first ripperdoc), plus alternative
command for existing post-Tower saves. Explicitly remove equipped Faceplate;
retain owned items and approved stock Basic Kiroshi/Johnny tattoo/Personal Link.
Restricted slots must look blocked but remain browsable; user permits buying
restricted implants into inventory, never installation. No command exists yet.
Read research/restriction_profiles/ban_design/assessment.md. Fresh installed
base decompile matches10 prior selected files;28 source anchors/3 Faceplate
records/both DB hashes/3 installed R11 receipt hashes PASS, NOT runtime tests.
Native SetLocked also blocks category navigation; use separate policy display.
Stock MaskCW/Plus/PlusPlus lack UnequipBlocked, but UI bans EyesCW unequip;
exact normal backend request/readback proposed, active effects/parts unproven.
BuyNotEquipable confirmation still reaches auto-equip callback: explicit buy-only
intent required. Check both occupied-slot overloads, prepayment and replacement
before old-item deletion. Preserve EquipmentEx restore chain and save isolation.
No runtime/build/install/game/save writes; source cache Git-ignored, only audit
tool/docs/artifacts updated. Santiago unchanged; remaining bar idles deferred.

Latest 2026-10-07T00:14:56Z: user explicitly permits Johnny's tattoo and stock
Basic Kiroshi Optics. Whitelist md/json now approve Tattoo: Johnny's Special
(Items.AdvancedCasiusTattoo) and Basic Kiroshi at model level; no Tier1-only cap
requested, exact upgrade mapping still pending. This supersedes no-stock-model
approval and utility-only custom optic requirement below. Keep Kiroshi stock
effects; no unrequested stat stripping. Together Forever and Faceplate remain
separate/pending. User policy is not new canon/runtime proof; retain audit limits.
Simple coprocessor civilian-information functions are hypothetical discussion,
not a new approved item/slot or implementation request. Personal Link retained.
Only design/status docs changed; no build/install/game/save writes. Santiago
investigation unchanged; bar idles remain deferred.

Latest 2026-10-07T00:05:28Z: user selects STRICT Tower whitelist; empty
categories okay. Personal Link is built-in, not selectable; preserve it outside
the category list. research/restriction_profiles/whitelist.md/json cover all10
categories: no stock model approved yet; utility-only private Basic Kiroshi is
PROPOSED, NOT CREATED. No Tier1/passive/zero-capacity auto exemption. Candidate
stock DB audit proves Kiroshi camera/damage effects and YakuzaTattoo HasSmartLink;
Johnny/Casius tattoo empty packages conflict with public descriptions, effective
behavior/parts/overrides need verification. Never imply all unclassified models
are canonically unsafe or run this empty design list as installed config.
User reports Santiago Molina absent. Exact hey_spr_ripperdoc_01 owner was
excluded from simple ripperdoc cohort (receptionist+defeat branch); coverage-gap
inference, live gate/survival/cause unproven. See research/santiago_molina/
assessment.md. No fix/build/install/game/save writes. Bar idles remain deferred.

Latest 2026-10-06T22:45:56Z: user confirms R11 Emmerick movement+rearm,
Rogue dialogue/glow and hologram removal USER-pass. No cold-reload/general
stability or crowd-corruption causation inference. Remaining bar NPC idle work
is explicitly DEFERRED; current priority is Phase6 restriction RESEARCH ONLY.
Read research/restriction_profiles/assessment.md and three evidence audits.
Authored q307 permits personal link/simple coprocessors, warns ANY combat
implant unsafe; high-load/capacity-only policy is insufficient. No numeric
Body/HP/stamina canon found in scoped resources. Equipment research identifies
occupied-slot preview, prepayment/replacement and save-restore bypasses; backend
IsEquippable alone insufficient. Preserve inventory/parts/progression, no build
reset or broad modifiers/effects removal. Recommend Cyberware Only first with
No Nerf pass-through; Full Nerf scope/numbers and Relic mechanical policy remain
decisions. Complete record/effect/variant catalogue and refresh current2.31
source provenance before implementation. No candidate/build/install/game/save
changes; no percentage gain. Retain R11 installed files and safe rollback rules.

Latest 2026-10-06T19:13:43Z: R11 INSTALLED with explicit user approval and
game closed (unsandboxed). Three backed-up replacements, zero additions/removals,
1307 other tracked files unchanged. Receipt, exact installed hashes and actual
rollback preflight PASS in research/afterlife_world/interactions_r11. R10 user
reports one completed visit without crash, but Emmerick still failed; NOT general
stability or R5 causation proof. Its74-row trace proves playerScene=true revoked
EContinue before proximity, ERequests stayed0; exact Claire ownership correlated
only. R11 Emmerick scene is NPC-only (dense actor0), same five nodes/root motion;
admission distinguishes passive player scene from actual dialogue/cinematic,
mount/workspot/rewind/token lock. Retains exact anchor/quaternion/inside/<=5m,
watchdog and existing actor. Rogue uses byte-exact reviewed R9 dense0/1 local
47-node scene + native interruption, paired-dialogue permission, scene-owned
gold Play/Break and bounded owned cleanup; no live appearance request. Actual
dialogue/eye-glow/step-aside/stream/reload remain LIVE PENDING, not engine proof.
User now explicitly REMOVES live face changes and hologram dancers: R5 reduced
to inert persistent-schema shim, catalog unused; exact10 original tube entries
retire-only,112 legacy node IDs retained +10 post-Deactivate migration setters.
No Reactivate; cold/110 saved-node/150 guarded migration/stream models PASS.
Nine/13 archive payloads + XL/diagnostics unchanged; Claire/R2 density/Nix/
Zetatech/boothR6 and named presence preserved. Real compile, packed readback,
actor-reference mutants,512 integrated +914 Rogue predicate cases,19 Lua checks
and install/rollback fixture PASS. No save/story writes or percentage gain.
Use docs/afterlife_interactions_r11_check.md on disposable no-save cold launch.
R11 rollback ONLY: R10-quarantined interactions with dancer retirement retained,
face shim retained; do not use earlier rollbacks or restore crashing R8/R9.
R9 crowd attachment corruption writer remains unknown. Read R11 assessment.

Latest2026-10-06T18:50:56Z: R9 LIVE FAIL/CRASH; user requests fix/install and
explicitly approves disabling livefacechanges+Rogueadapter: "Yes—prioritize
stability". R10 SAFETY BUILD INSTALLED gameclosedunsandboxed, FOUR backed-up
replacements,zeroadditions,1290 othertrackedfilesunchanged. Receipt/actualhash/
rollbackpreflight PASS under interactions_r10. Newcrash142725 is exe+0x1d9779,
entHardAttachment jacketvtable+4; roottransformexactlymatches ordinarycrowd
female10029921 in4samples, NOTRogue. CorruptingwriterUNPROVEN; R9actorindexfix
stillvalid. R5appearanceadmission/update harddisabled, dispatchremoved; persistent
prefs/catalog/schema/counts preserved, duplicatesmayreturn. Roguepresencekept;
runtimeadmission/effectsdisabled, samepathscene actor/action-freeStart1->End2,
in/local_out IDs retained +ownerinterruptionops cleared. Dialogue/glowDEFERRED.
Emmericktriggergeometryprovenintact; replacesunprovennativecommunitydistance
with exactruntime<=5m PTFRAL10_ENear, retainsanchor/quaternion/workspotguards.
ExactentryblockerUNPROVEN. Automatic1sstatus/facttrace nowinstalled; diagnostic
privateworkspot/failedCETbindingprobes removed.11/13archivepayloads+XL unchanged.
Compile/exactdeltas/26negativeconditions/19Lua/fixturePASS; no livecrashstability
oranimationproof. PreserveClaire/R2/Nix/holograms/Zetatech/boothR6; no%gain.
Use docs/afterlife_interactions_r10_check.md, disposablepretestsavepreferred.
R10rollbackONLY restorespreR8archive/XL+recoverablyremovesinteractiondriver;
KEEPSR10face-suspension+diagnostics. Do notrestoreR8/R9 orre-enableR5speculatively.
Read interactions_r10/assessment.md andcrash/evidence.json. This supersedesR5
preservation below only for explicittemporarysuspension, notpopulation/type.

Latest2026-10-06T14:35:03Z: user requested "fix and install it again". R9
INSTALLED game closed (unsandboxed): TWO backed-up replacements (R1 archive +
same R8-named runtime), zero additions,1277 other tracked files unchanged.
Receipt interactions_r9/install_receipt.json; hashes/actual safe-rollback
preflight PASS. Rogue dense cast0/1,43 obsolete holo references removed BEFORE
100 player/packed-reference remaps2->1/513->257. Independent actor auditor
rejects actual crash layout/header-only fix/three stale-ref mutants; dump lookup
now index0. Emmerick restores sequential inside->native<=5m->anchor gates,
quaternion absolute-dot readiness and detailed stage/status diagnostics. Exact
R8 entry blocker remains UNPROVEN; this is a bounded candidate, not live pass.
11/13 R8 archive payloads + XL unchanged, existing5-node entrance scene retained.
Compile/packed bytes/45node50edge/27negative saved-condition/fixture rollback
PASS. Claire/R2/R5/Nix/hologram/Zetatech/boothR6 preserved; no story/save writes.
Use docs/afterlife_interactions_r9_check.md for disposable no-save cold launch.
Animation/dialogue/glow/stream/reload still pending; no % gain. SAFE rollback
via deploy_afterlife_interactions_r9.ps1 returns PRE-R8 R7 archive/R2 XL and
recoverably removes runtime; NEVER normal-rollback to crashing R8. R8 backups
are forensic only. Do not use older rollback scripts. Read R9 assessment.

Latest2026-10-06T05:43:42Z live R8 FAIL + CRASH. User: Emmerick did not step
aside, then crash. Inspector proves same9016685 reached PTFRAL8_Entrance and
authored start(-1458.485,1026.330,16.793); six audit samples05:42:58–05:43:38
are in_workspot=true/in_scene=false. Entry activation/movement worked; exact
EStart/trigger blocker unknown, no request counters captured. Quaternion sign
flip is equivalent rotation, not proof of facing error. Crash report014342:
Cyberpunk2077.exe+0x545d0b read0x34; minidump confirms ordinary actors1/player1,
requested player index1(out of bounds), null definition, actual player actorId2.
R8 Rogue removed holo actor1 but retained playerId2 and packed references:
same native actor-index failure already documented in streetkid S3. R8's exact
delta test INCORRECTLY asserted the invalid playerId2; offline PASS insufficient.
Last crash observer(-1428,1014,18) within Rogue admission radius. R8 remains
installed with exact hashes; NO rollback/replacement performed in this report
turn. Recommend R8-only rollback pending user authorization; preserve R2/R5/
R6/Claire/Nix/holograms/Zetatech. Do not ask user to relaunch unsafe R8 for more
traces. Read interactions_r8/live_failure_20261006.md before next work.

Latest2026-10-06T05:31:43Z: user explicitly requested IMPLEMENT AND INSTALL.
Afterlife Interactions R8 INSTALLED, game closed (unsandboxed): two backed-up
R1 archive/XL replacements + one runtime addition,1261 other tracked files
unchanged. Exact installed hashes and actual rollback preflight PASS; receipt
research/afterlife_world/interactions_r8/install_receipt.json. Existing private
Emmerick now has authored start spot + copied trigger, guarded phase return and
five-node native two-step scene to R7 endpoint; no new actor. Rogue private
47-node local-only dialogue adapter keeps eligibility/history/local animations
and scene gold-eye events; removes holo actor/phone teardown, preserves Tower
appearance. Native32-node owner + exact-resolver permission driver,20s Emmerick
scene watchdog, departure latch and owned effect cleanup. Eight prior archive
payloads unchanged; Claire USER-pass/R2/R5/Nix/holograms/Zetatech/boothR6 preserved.
Offline exact-delta/packed readback/redscript compile/256 abstract guard-stream
cases/three-file fixture rollback PASS. These are NOT engine animation proof.
LIVE PENDING: leave bar fully, re-enter for step-aside; approach Rogue for local
choices/eye glow, depart/return. Use docs/afterlife_interactions_r8_check.md.
Private scene acquisition, phase movement, native/runtime load ordering, saved
reload and visual parity remain unproven. No % gain. Rollback R8 only; do not
run earlier R1/R2/R7 rollbacks against this installed archive.

Latest2026-10-06 follow-up: Claire dialogue available USER-pass. Emmerick must
react to entry by stepping aside; new Inspector confirms private9016685 at R7
entrance02 endpoint, NOT reaction/idle-loop proof. Source audit identifies exact
5-node emmerick_entrance scene: root-motion two-step4533ms from entrance/node84
to entrance02/node97, triggered by inside+<=5m with exit/rearm owner. R7 parks
at endpoint and lacks this controller; don't play movement from wrong endpoint.
Rogue local scene entry1 starts136 eye_glow_gold +235 holo-tag mute ->choice4;
private ambient actor lacks scene owner, explaining both missing dialogue/glow.
Local route55 nodes still shares phone-end handshakes: requires reviewed private
local-only adapter, not blanket default_dialogs/q103/sq031 replay/permanentVFX.
Read interactions_r8/assessment.md/audit.json. SOURCE AUDIT ONLY, no new runtime
fix/build/install; all12 Afterlife paths unchanged. Preserve Claire/R2/R5/Nix/
hologram/Zetatech and R6; no % gain or repeated scanner request needed.

Latest2026-10-06T04:52:24Z: user completed pre-Tower observations and explicitly
authorized implementation+install. Emmerick R7 INSTALLED game closed (unsandboxed),
ONE backed-up R2-based archive replacement, zero additions,1247 others unchanged;
installed hash and actual rollback preflight PASS. Receipt emmerick_r7/install_receipt.json.
Only private spot78 + its persistent/metadata transform now match observed vanilla
entrance02/node97: infinite stand-around04 with12 weighted gestures/recent-repeat4.
Private q005 phase LABEL retained for save/controller compatibility; identities,
quotas/appearance/graphs unchanged,8/10 archive payloads byte-identical. Preserve
R2/R5/named/hologram/Zetatech and boothR6. Use docs/afterlife_emmerick_r7_check.md;
live motion/placement/return/reload pending, no % gain. R7-only archive rollback.
Capture041947Z has16 post-Tower+81 pre-completion rows, NOT a single baseline;
175 observed IDs across both is NOT census. Four booth actors:9/10 post samples
in workspot/outside scene,47/47 pre samples in both; R6 visual pass still absent.
User confirms same booth variants and visually empty tubes PRE-Tower; do not
undo accepted hologram/R5 or install deferredR4. Claire retains full vanilla
conditional service scene; exact optional-choice parity unresolved. Rogue private
ambient actor has no dialogue owner; scene-controlled glow/local dialogue adapter
remains separate work, NOT fixed by R7. Read baseline_r7/assessment.md and capture.

Latest2026-10-06T04:16:48Z (00:16 Toronto): user approved "install pls".
Booth R6 INSTALLED with game closed (unsandboxed); TWO backed-up replacements,
zero additions,1231 protected files unchanged. Exact installed hashes and actual
rollback preflight PASS. Receipt: research/afterlife_world/booth_r6/install_receipt.json.
R5 type/appearance USER-pass and R2 density/named/hologram/Zetatech preserved.
LIVE PENDING: cold launch disposable no-save visit, three seated/one standing,
90s sustained routine/alignment check via docs/afterlife_booth_r6_check.md.
No animation/entry/interrupt/return/reload pass or percentage gain. R3 failure
not yet proven fixed. R6 rollback restores only two backed-up R3 files; never
remove all R3 additions or roll back R1/R2/R5. Supersedes NOT INSTALLED below.

Latest2026-10-06: user says NPC type problem FIXED; record R5 appearance/type
USER-pass without save/reload/first-frame inference. Animation complaint is
explicitly the FOUR BOOTH actors. New40-row03:54:59–04:00:11Z trace confirms
standing->workspot->exit/table rise, no despawn proof. Source R3 has~11s delay;
active idle branches finite (merc_02 only3–5s). R6 BUILT/OFFLINE PASS, NOT
INSTALLED: four private workspot copies change only idle-sequence2 loop flag;
four private spot resource refs, three R3 payloads unchanged,93 exits retained.
Runtime exact-anchor direct idle admission0.5–1.25s modeled after readiness;
0.25s polling,35cm/15cm anchor bound, ordinary walk fallback, same guards/
timeouts/cancellation/max3 requests. Three native random gesture lists remain;
merc_02 retains quieter lean270 idle. No count/appearance/actor/scene changes.
Exact-source compile with Codeware+unchanged R5 and workspace two-replacement
backup/rollback PASS. No game writes or actual install receipt; next explicit
install approval+unsandboxed game-closed check, deploy_afterlife_booth_r6.ps1.
Read booth_r6/assessment.md/tests and docs/afterlife_booth_r6_check.md. R3 failure
remains open pending live R6 alignment/loop/interrupt/return/reload. Preserve
R2/R5/Rogue/Nix/hologram/Zetatech; no % gain, no broad AI reset.

Latest2026-10-05T19:47Z: user said "implement and install". Afterlife Faces R5
INSTALLED game closed (unsandboxed), TWO script additions, zero replacements,
1216 protected files unchanged; installed hashes/actual rollback preflight PASS.
Receipt: research/afterlife_world/faces_r5/install_receipt.json. Four original
q005 random crowd entries only, exact native PS spawner+entry ownership;
23/36/7/6 disjoint verified leaf-face pools for unchanged17/22/7/4 slots.
Same-face aliases count once; shared outfits allowed. Native random selection
confirmed, but R5 deliberately changes collision selection/appearance weights.
Queued reservations and one bounded post-ATTACH appearance request per actor,
not a pre-render guarantee or periodic reroll. Mod-owned persisted ID/role
preferences; detach release, unknown/overflow/competing ownership fail closed.
Real compile/source/guard/allocation/delayed-ack model and workspace install/
rollback checks PASS. Live callback/PS/readback/render/return/reload PENDING.
Read faces_r5/assessment.md and docs/afterlife_faces_r5_check.md. No fact/AI/
population change; R2/Rogue/Nix/hologram/Zetatech untouched. Four fixed booth
skins/routines EXCLUDED: R4 still deferred, R3 live failure remains. No % gain.
Rollback only R5's two additions recoverably; no R1/R2 rollback. This supersedes
the no-implementation status and pre-spawn-only plan immediately below.

Latest2026-10-05 user explicitly requests NO REPEATED FACES for probabilistic
ordinary Afterlife appearances; shared outfits accepted. Supersedes earlier
no-uniqueness restriction, not count/role/story protections. Native executable
chain verifies distribution-enabled community picker randomizes the record
pool (not proof of independent per-NPC rolls/global uniqueness). Official pools
29/29/8/6 map to26/25/7/6 conservative head/skin signatures; CP-male08_1/08_2
share a face despite different names. Four-pool source matching50/50 passes,
not live census/visual guarantee; child resolution, one unknown male head,
female phase67-vs-record29 precedence, fixed residents and live overrides open.
Read appearance_rules/assessment.md, audit.json and face_capacity.json.
NO runtime uniqueness implementation/install; R4 fixed-four still deferred.
Next verified pre-spawn face reservations + lifecycle, not visible skin polling
or global record edits. Ten installed Afterlife hashes unchanged; R3 routine
failure and accepted density/named/hologram/Zetatech passes preserved.

Latest2026-10-05 user correction: focus appearance SPAWN/SELECTION RULES and
probabilistic variants, not assigning skins to individuals. R4 fixed-four
appearance candidate is DEFERRED, NOT INSTALLED; do not deploy it as this fix.
Audit actual phase/template/record appearance pools and native distribution;
record/slot type selection is distinct from appearance selection. Source pools
29/29 generic and8/6 cyberpunk have distribution enabled; numeric weights,
draw independence/seed failure and repeat suppression unproven. No arbitrary
no-duplicates policy or density/type changes. Use batch appearance/community
evidence, not another individual-skin patch. See appearance_r4/assessment.md.
R3 routine live failure remains; installed files and all accepted passes intact.

Latest2026-10-05 follow-up: R3 LIVE FAIL. User observes two sitting/one standing/
one on table, then two walk toward wall and disappear. Both traces briefly
enter workspots then exit while Ready/World/Local stay1. All four objects still
resolve later: visual disappearance is not proven despawn. Inspector confirms
merc_04/scene1 ID10029983 uses appearance merc_01, source requires merc_04.
User requests repeated-appearance repair including another unidentified group.
Four exact booth appearance-only R4 candidate + corrected read-only diagnostic
OFFLINE PASS, NOT INSTALLED. No AI/routine change, pool/density edit or spawn.
All ten installed Afterlife receipt paths unchanged. Read appearance_r4/
assessment.md, tests.json and live_r3_evidence.json. Need other group's exact
Inspector identity; routine alignment/exits/visibility unresolved. Do not repeat
root screenshots/unchanged test or claim R3 passed. Preserve accepted R2 and
named/hologram/Zetatech. No percentage gain. Supersedes live-pending below.

Latest2026-10-05T15:25Z: user approved install. Afterlife R3 INSTALLED with
game closed (unsandboxed check), FOUR ADDITIONS, zero replacements,1180 other
tracked files unchanged. Installed hashes and actual rollback preflight PASS.
Receipt: research/afterlife_world/idles_r3/install_receipt.json. Existing
R2 density/Rogue/Nix/holograms/Zetatech preserved. LIVE PENDING: cold launch,
disposable no-save visit, booth expected three sitting/one standing, then
bar-wide walk/30s candidate observations using PTFR_Afterlife_Behavior_Audit.
Use docs/afterlife_idles_r3_check.md. Dispatch is not animation proof; exact
resolver, broad coverage, interruption/return/reload unproven. No percentage
gain. R3 rollback only removes its four additions recoverably; no R2/Nix undo.

Latest2026-10-05 R3: user explicitly requests four booth idle fixes + bar-wide
idle audit. Candidate BUILT/OFFLINE PASS, NOT INSTALLED. Four original exact
community-entry actors, scene1 three sitting/one standing; four private exact
workspots, no community entries/spawn/phase/appearance changes. Native34-node
guarded readiness + interruptible bounded redscript commands via vanilla exact
EntityReference resolver (empty/ambiguous fails closed). Preserve R2 density,
Rogue/Nix/holograms/Zetatech. 88negative/16stream/88race/source/redscript/11Lua
checks and workspace-only four-addition install/rollback fixture PASS. New
read-only bar-wide diagnostic;57 source roster rows NOT people/census. Existing
logs do not prove all other NPCs healthy or broken. Read idles_r3/assessment.md
and tests.json. Next approve install, verify game closed outside sandbox, then
docs/afterlife_idles_r3_check.md. No actual preflight/receipt/live pass or
percentage gain. Earlier investigation-only restriction superseded for this
requested narrow implementation, not blanket crowds/scenes/story/save writes.

Latest2026-10-05: user confirms "crowd density is fixed" after R2 installation.
Record R2 crowd-density USER-pass; preserve it plus hologram visibility,
Rogue/Nix presence and accepted Zetatech work. Do not repeat basic crowd-density
checks or change population quantities speculatively. No exact live census,
migration fact value, repeated return/fast-travel, saved reload or natural-ending
pass was supplied. Four old scene-owned booth NPC routines remain unresolved;
this result does not fix them. Details: population_r2/assessment.md. No new
game writes or roadmap percentage gain from this confirmation.

Latest2026-10-05T14:49Z: user explicitly approved install. Afterlife population
R2 INSTALLED with game closed: TWO backed-up archive/XL replacements, zero
additions,1164 other tracked files unchanged. Receipt/backup under
research/afterlife_world/population_r2/install_receipt.json; installed hashes
match tested candidate, actual rollback preflight PASS. Seven R1 payloads,
Rogue/Nix/Emmerick/dancers and accepted Zetatech preserved; no save/story write.
LIVE PENDING: cold-launch disposable save, depart far enough for old private
spots to unload, require PTFRAL2_Migration2 (stream barrier, NOT actor census),
then return and compare ordinary population. docs/afterlife_population_r2_check.md.
Four scene-owned booth routines remain separate/unfixed. Preserve user's
hologram visibility pass, do not repeat it as a missing-hologram test. No
completeness gain; use R2-specific rollback only, not Nix-undoing R1 rollback.

Latest2026-10-05 follow-up: new afterlife_20261005T143247Z.jsonl is STILL R1:
installed archive/XL hashes match original R1, no R2 receipt or install approval.
User reports holograms FIXED visually; preserve USER-pass without all10/reload
inference. Three sampled vanilla ServiceTubeDancerFemale actors in workspots;
vanilla holograms ARE NPC-based, exact scanner-name parity unverified. Crowd
still excessive, four booth actors still idle. Two sampled old IDs10029981/83
remain out of both workspot/scene. R1 requests26->52/releases26 are dispatch,
not actor counts. See live_r1_result.md new bounded36-row section. No new
runtime/build/install/save writes; await R2 two-file installation approval.
R2 corrects crowd ownership, not these four separately scene-owned routines.

Latest2026-10-05: user authorized implementation; Afterlife population R2
BUILT/OFFLINE PASS, NOT INSTALLED. Read research/afterlife_world/population_r2/
assessment.md, manifest.json, tests.json, deployment_tests.json, preflight.json.
Reuses original q005 background20/66 allocations +5 exact ordinary extras;
71 allocations share70 original spots (crowd_female/mercenary_woman share one).
No new actor identity, record/appearance/quota/density change. R1 26 crowd
acquires now retire-only, same262 IDs/edges; seven other payloads byte-identical.
New4-node gate/244-node owner leases only vanilla4-trigger controller after
genuine Tower, requires q103_done1/active0/q005_done1/plan_finished1, local
occupancy/readiness and original Activate (not Reactivate). Migration retires
old private78-slot crowd then requires full departure/all its spots unloaded
plus recheck; barrier is NOT actor-removal acknowledgement. Wrong/early policy
fails closed.234 saved-node/38 negative/80 occupancy/75 stream/71 race/10 modeled
reload-cycle tests PASS, registry/source/packed-byte checks PASS. Two-file
install/rollback exercised ONLY in workspace fixture; actual six R1 files
unchanged. Real preflight protects1150 others; no game/save/runtime write.
Await install approval; installer defaults ValidateOnly, explicit -Install.
Preserve Rogue/Nix, Emmerick/dancers/Zetatech; no individual merc changes or
claim missing holograms fixed. Use docs/afterlife_population_r2_check.md AFTER
receipt: migration + matched baseline + repeat/fast-travel/reload evidence.
R2-specific rollback restores only2 files; do not use R1 rollback (undoes Nix).
No completeness gain or always-correct live count claim.

Latest2026-10-04: user redirects to NPC amount/type/spawn-rule RESEARCH, not
individual actor fixes or temporary crowd toggles. CONFIRMED R1 policy defect:
q103_done1 in BOTH ManualSave9/AutoSave10; vanilla embedded master routes
0->58->60(cuts node4)->61->7 to embedded q005_afterlife_phase, NOT q103 crowd.
Correct ordinary background20 entries/66 configured slots plus5 directly
activated extras; other scene/named actors conditional, not a fixed total.
R1 adds26 q103-derived entries/78 slots and only retires original q103 entries,
not surviving q005 background. User q103-active-count0 therefore does NOT
exclude overlapping cohorts. Actual visible census/budget still unknown.
Earlier post-q103 node4 and afterlife_default_In claims were WRONG: node4
calls q103_In; node7 calls q005_In. Withdraw merc_01..03 removal proposal.
Read assessment.md population-rules section, population_rules_audit.json and
population_rules_records.json under research/afterlife_world. Source-branch/
quota/66spot/save-hash counterexample audit PASS; R1 population policy FAIL.
Generic male/female records have29 appearance pools/distribution enabled;
preserve type/appearance/slot rules, never deduplicate by record ID alone.
No runtime writes/new build/install/save edits; keep Rogue/Nix USER presence
passes and all accepted Zetatech work. Next design correct-cohort ownership,
matched baseline census and stream/reload invariants; no blanket roots/scenes,
arbitrary crowd cap, repeated active-count test or completeness gain.

Current2026-10-04 (live trace through 2026-10-05T00:34Z): Afterlife R1 partial
USER result: Rogue and Nix present; preserve both repairs. Nix Trade/reload
not established. Four matching booth mercenaries remain frozen, some tube
holograms absent visually, crowd possibly excessive. User reports all ten
dancer entries active and 26 private crowd entries active (groups, up to78
patrons, NOT26 people). Audit identifies frozen q005_afterlife_mercenary_male
outside both workspot and scene; these four were excluded from R1. The earlier
default-input four-to-one treatment is superseded by the owner audit above;
do not replay the whole scene or blindly change these actors. Active flags do not prove
rendering or duplicate-free handoff. Game remains running; no R2 install.
See research/afterlife_world/live_r1_result.md. Next read-only original crowd
entry check, then bounded mercenary/dancer/density diagnosis; no repeat of
accepted presence/Zetatech checks or completeness gain.

Current2026-10-05T00:12Z: Afterlife R1 INSTALLED, live pending. Four additions
plus two backed-up S4/Nix replacements; 1130 other tracked files unchanged,
including accepted Zetatech/R8. Original 10 hologram entries, private ordinary
26-entry crowd (78 max actors), Emmerick exact guard stance, Rogue exact booth
idle with Tower appearance; 80 private actor cap incl Emmerick/Rogue, not 28
actors (28 entries). All private aliases, initially inactive/default-off,
per-entry guarded original-to-private handoff. No full roots/scenes/forced
story facts/save edits. Tiny Mike and old four scene-owned mercenaries excluded.
Nix absent confirmed; pre/post samples both nix_default_on1/mq016_active1.
Removed only extra mq016_active0 mod guard in native wrapper and driver;
15 other S4 payloads unchanged, old wait node preserved. 374 native nodes,
guard/stream/race/source/readback/runtime tests PASS; rollback preflight PASS.
Read research/afterlife_world/assessment.md, tests.json, install_receipt.json.
Use docs/afterlife_r1_check.md for one cold-launch no-save visit and return.
No live presence/animation/handoff/Nix trade/saved-wait/reload proof; no
percentage gain or repeated accepted Zetatech/Claire/mirror checks.

Current2026-10-04: user reports R12 "all worked as expected"; preserve local
population/idle USER-pass without inferring reload, new natural-ending or
persistent Terry death. See population_r12_live_result.md. User prioritizes
Afterlife before further roadmap work: missing dancing holograms/Rogue,
idle Emmerick/patrons, and explicitly Nix COMPLETELY ABSENT. Earlier S4
aggregate smoke report is NOT a Nix pass. Read research/afterlife_world;
original resource comparison and focused repair are in progress. No new
installation is established until an Afterlife install receipt exists.

Current2026-09-28T21:41Z: R11 USER-pass all three doors and four pavement
NPCs. Terry/indoor guard/upstairs staff present but idle/static; user requests
animations and remaining local street residents. R12 installed: three
additions plus one read-only diagnostic replacement,1091 others unchanged.
R11 archive/XL/Terry lifecycle/tweak and R8 byte-identical. Private community
adds27 ordinary residents (31total incl accepted4), private guard/clerk with
original stance/tablet workspots; exact originals deactivated only under
completed-Tower/Applied/readiness guards before private activation. Same
private Terry receives interruptible smoking command; no spawn/death changes.
30private spots, one exact wheelchair, five documented independent-idle
substitutions. No Jim/Misty/new merc/scene drones, scenes/story/save writes.
212node/52negative/31stream/29race/4payload/readback/redscript/Lua checks PASS,
four-file recoverable rollback preflight PASS. Live animations, actor handoff,
alignment and reload NOT proven; no percentage gain. Read access_r11_live_result,
population_r12_assessment/tests/install_receipt in research/misty_viktor_world;
use docs/zetatech_population_r12_check.md. Do not repeat passed doors/four-NPC
or R8 basic checks. Community actor-ID getters returned empty even for visibly
accepted actors; use looked-at workspot state plus user observations.

Current2026-09-28T20:49Z: R10 USER-failed: front/inner doors unchanged,
outer rear locked, counter staff absent, no street NPCs. User confirms the
missing staff means upstairs (not Viktor), and requested street NPCs include
Terry. The guard's source workspot is INSIDE; earlier street-front claims
below are incorrect. R11 installed with game closed: two replacements
(archive/XL), three additions (read-only audit, private Terry tweak/runtime),
1071 other files including R8 unchanged. Two exact private interactive door
entities plus independent front/inner/rear readiness branches; original rear
R2 unlock restored. Original indoor guard/clerk reactivated; four private
street community entries/workspots and separate private Terry clone, no
assault scene or original character edits. Terry lifecycle is session-only;
damage/AI/death/reload unproven. Offline guards/128 stream combinations/30
packed payloads/registry/workspots/redscript/Lua checks PASS; exact five-file
rollback preflight PASS. No story fact/save writes or completeness gain.
Read access_r10_live_result.md, access_r11_assessment.md and
access_r11_install_receipt.json under research/misty_viktor_world. Use only
docs/misty_viktor_access_r11_check.md for one cold-launch disposable no-save
visit. R11 remains LIVE PENDING; R9/R10 routes are superseded. Preserve R8
USER-pass and do not repeat its basic lighting check.

Current2026-09-28T20:02Z: R9 USER-failed: counters proved dispatch, but the
indoor clerk stood still and both reported doors stayed open/noninteractive.
R10 installed as ONE replacement of the R9 archive with game closed;1039
other project files, XL and R8 additions unchanged. It waits for BOTH exact
door refs to stream, closes+unlocks front q307_zetatech_door and corrected
inner q307_zetatech_doors_01, then rearms after either unloads. R9 clerk is
explicitly deactivated; only vanilla post-Viktor q307_alley_extra_01 Zetatech
guard is reactivated at its authored storefront return workspot.50-node/
45-guard/four-stream-case/archive/readback PASS; no original world override,
scene, story fact or save write. Installed hash
5DCEE0D2AA19C80A9A425A3D09D259B900C3BBCA3BE1AE67E5DDE7B0A0AA6FA8.
Live door interaction/rest state and outdoor NPC animation remain pending via
docs/misty_viktor_access_r10_check.md. Read access_r9_live_result, R10
assessment/receipt. Do not claim the R10 repair passed or restore generic
crowds/scene cast; R9 and its check are superseded.

Current2026-09-28T19:04Z: user reports the R8 play test passed; treat the
automatic blue-neon/police-light smoke result as USER-pass, but do not infer
fresh natural-ending, pre-Tower baseline, save/reload or long-session proof
unless separately reported. R9 door/receptionist follow-up installed with game
closed as ONE archive replacement; XL and all five R8 additions unchanged,
1026 other project files protected. It closes then unlocks the exact Zetatech
front door and surviving inner/rear door so their vanilla interactive behavior
can resume, and reactivates only q307_zetatech_clerk at the authored post-scene
idle workspot. No scene, Misty/Johnny/new merc/other community entry, story fact
or save write. Offline archive/readback/39-node/45-guard/92-loading/single-entry
tests PASS; live door auto-close/interaction, single clerk idle, streaming,
release and reload pending. Read access_r9_assessment/receipt and use only
docs/misty_viktor_access_r9_check.md on a disposable save; no repeated R8 test.
Final installed hash is DB2EEDF0C67ACC7762BCC73F45EF2382458CE0385E51B34B0A79F04E4CC7B437;
private AccessRevision!=9 forces one guarded release/reacquire so an already-
active saved R7 controller executes the new actions. Both predecessor and R7
baseline rollback layers are recorded in the receipt.

Current2026-09-28T17:32Z: user explicitly requests automatic activation of
the whole completed restoration after Tower, no lighting opt-in. R8 installed
as five additions; S1's three idle test files moved recoverably,1009 other
project files unchanged. Exact original-sector delta12 aliases/12 nodeRefs:
seven police lights, three pink lights, two pink strip meshes. Five authored
Tower Cold/blue counterparts cloned into private default-off block. Two
auto native phases guard genuine Tower completion and streaming; police also
waits for R7 Applied. Redscript auto drivers arm R7 outside80m when safe,
exact Tower journal reconciliation, and source-None clock recovery. Offline
diff/graph/archive/readback/three-driver lint/installer/rollback preflight
PASS. Live startup, visual blue replacement/police removal, pre-Tower
baseline, natural ending, fresh journal/time, streaming and reload NOT YET
PROVEN. Read research/misty_viktor_world/lighting_r8_assessment.md, receipt,
docs/misty_viktor_lighting_r8_auto_check.md. Do not use S1 commands or claim
completeness gain; one disposable no-save natural-ending test next. If crash,
close game and use exact prepared rollback, no forced facts. Historical S1
and private POC notes below are superseded for installed status.

Current2026-09-28T16:48Z: original-light singleton S1 installed IDLE opt-in,
three additive files, zero replacements,992 prior project files protected.
Exact official-sector delta is only placement3901/3362 QuestPrefabRefHash plus
one appended nodeRef; lamp/variant/story properties unchanged. Native33-node
guarded Show/Hide/Stop controller, package byte-readback and simulator pass.
No original visibility action has run, no live alias/baseline/natural ending
proof, and NO seven-light or pink-to-blue repair yet. Read
research/misty_viktor_world/original_lamp_s1_assessment.md and receipt. Next
one-site disposable pre-Tower baseline then post-Tower Show/Hide/Show/Stop via
docs/misty_viktor_original_lamp_s1_check.md. User need not find blue IDs:
vanilla Tower cyan lights3113–3115/Cold strip meshes3118–3119 are identified.
Do not expand or automatically activate before original alias visual proof;
no completeness gain. Prior private-light note below remains evidence.

Current2026-09-28: user-provided corrected Hide/Show images and 65-row trace
validate visible control of ONE private aliased static-light copy (Ready1,
Hide2, Show3 near target). No Stop in second trace; release/streaming/cold-load
remain unverified. This does not repair or prove aliasing of original police
lamps or hotel neon. Read
research/misty_viktor_world/light_poc_live_result.md. Next singleton
exact-delta original alias proof with baseline/natural-ending validation;
no automatic activation or completeness increase. Earlier inconclusive
first-attempt note below is historical.

Current2026-09-28: first private-light POC live test INCONCLUSIVE. Trace closest
V position9.66m versus3m light radius; one Show dispatched but no Hide because
requests came after node stream-out. User saw no change in original police
residue; POC never targets original lamps. Stop recorded release. See
research/misty_viktor_world/light_poc_live_result.md and corrected one-site
docs/misty_viktor_light_poc_check.md. No original lighting change, automatic
activation or completeness gain. Earlier live-pending note below superseded.

## Project mission

Build a Cyberpunk 2077: Phantom Liberty mod that allows the player to continue free-roaming Night City **after The Tower ending has completed normally**.

The mod must preserve the consequences of The Tower. It is not a rewrite of the ending, a happier ending, or a new 2079 campaign.

The intended flow is:

```text
Vanilla The Tower / q307
        ↓
runs completely normally
        ↓
final scene + credits
        ↓
q307 cleanup genuinely completes
        ↓
retained-session final-board teardown
        ↓
selective sandbox initialization
        ↓
post-Tower free roam
```

The core design rule is:

> Preserve the ending first; restore gameplay second.

---

## Non-negotiable behavioral requirements

### The Tower must remain vanilla

Do not interfere with the ending while q307 is still running.

The following must play normally:

- Viktor
- thug encounter
- Misty
- final cutscene
- credits
- q307 cleanup

Do **not** force q307 facts during the ending to advance the quest.

Previous experiments showed that changing quest facts with CET can alter values without executing the quest-graph transition associated with those values. This can leave saves stuck around intermediate q307 stages.

### Activate only after genuine Tower completion

Preferred integration pattern:

```text
observe q307
    ↓
wait for genuine completion
    ↓
return directly in the retained session
    ↓
run only validated cleanup/restoration
```

Avoid:

```text
replace q307
```

and:

```text
force q307 facts mid-ending
```

Prefer mod-owned resources and external hooks when they provide a reliable implementation. However, minimal patches to official Cyberpunk quest resources are allowed when necessary for a reliable integration point or state transition. Such patches must be evidence-based, narrowly scoped, preserve vanilla execution before the intended hook, and document every changed node/property. Avoid replacing whole vanilla quest flows when a small branch/event/node patch is sufficient.

### Preserve the post-Tower state

The following should remain true wherever technically possible:

- The Tower is completed.
- V survived the Relic.
- Johnny's engram is gone; only noncentral voice-only dialogue is permitted under the user-approved R4 gameplay compromise.
- The Relic storyline is finished.
- V spent roughly two years in a coma.
- Tower relationship outcomes remain intact.
- V cannot return to being the same cyberware-heavy mercenary.
- Existing 2079-related state is preserved where possible.
- `q307_2079` should ideally remain active.

The following must not happen:

- Johnny's engram, visible projection, bodily takeover or Relic powers return. Supporting voice-only dialogue is the R4 exception, not a fact reset.
- Nocturne OP55N1 becomes the active main story again.
- Relic symptoms resume.
- old romance states are blindly restored.
- the selected restriction profile is silently lost or bypassed simply because free roam is restored.

---

## v1.0 target

v1.0 is successful when:

- The Tower completes exactly as normal.
- Credits play.
- The retained post-Tower session returns directly to gameplay.
- No pre-ending/PONR save is loaded.
- V remains cured.
- Johnny's engram stays removed and visible projection absent; only R4-compatible supporting voice may remain.
- the selected No Nerf, Cyberware Only, or Full Nerf profile behaves consistently and persists.
- Tower state remains completed.
- as much existing 2079 state as practical is retained.
- normal sandbox systems work.
- selected non-story activities work.
- post-ending saves can be loaded reliably.

A complete new 2079 world is **not** required.

---

## Scope

### In scope

Core sandbox:

- walking and exploration
- driving
- vehicles
- map
- fast travel if compatible
- apartments
- vendors
- weapon shops
- clothing shops
- bars
- police
- generic combat
- open-world spawning
- saving and loading
- Dogtown access if possible

Potential activity restoration, one system at a time:

1. NCPD scanner activities
2. Cyberpsycho Sightings
3. El Capitan vehicle contracts
4. Dogtown airdrops
5. other repeatable/systemic activities
6. simple gigs that do not depend heavily on Johnny, the Relic, or incompatible story state

Minor 2077-era dialogue inconsistencies are acceptable in optional sandbox content.

### Out of scope

Do not expand the task into a complete post-Tower campaign.

Not required:

- new voice acting
- AI voice replacement
- new cinematic quests
- rewriting Judy/Panam/Kerry/River storylines
- new 2079 NPC dialogue
- complete rebuilding of Night City for 2079
- restoring every unfinished quest
- Johnny-central quests (supporting voice-only dialogue is permitted by R4)
- Relic-heavy quests
- Nocturne OP55N1
- major pre-ending story branches

If the game does not contain enough 2079 open-world content, use the normal Night City sandbox while retaining Tower state wherever practical.

---

## Technical architecture

Prefer mod-owned resources and minimal ownership of vanilla state. A narrowly scoped official-resource patch is permitted under the vanilla-resource policy above when it is the most reliable integration mechanism.

Target split:

### Native quest logic

Use native quest resources for game-state transitions and the post-ending hook.

Optional custom resource:

```text
PostTowerFreeRoam.questphase
```

Responsibilities:

- detect genuine Tower completion
- coordinate the direct retained-session handoff
- launch selective sandbox initialization

Use Deceptious Quest Core only if it proves to be the cleanest compatible production integration point; the direct retained-session design does not require it merely for architectural symmetry.

### redscript / runtime logic

Use runtime logic for persistent behavior such as:

- detect Post Tower Continuation and Free Roam state on load
- enforce cyberware restrictions
- prevent invalid equipment
- restore or reassert required sandbox conditions after reload
- monitor player state
- prevent Johnny/Relic systems from returning

Conceptual behavior:

```text
on player load:
    if PostTowerFreeRoamActive:
        enforcePostTowerRestrictions()
```

### ArchiveXL

Use for mod-owned resources where appropriate:

- custom questphase
- optional notification/localization resources
- journal/debug resources
- related assets

Prefer adding resources over replacing vanilla resources.

### RED4ext

Treat as a runtime/framework dependency where required by the chosen implementation or by dependencies such as Codeware.

### Codeware

Optional.

Add only if the project requires capabilities such as:

- easier player manipulation
- UI access
- world/entity handling
- runtime resource access
- event hooks

Avoid adding it to the first proof of concept unless necessary.

### TweakXL

Optional.

Investigate if it provides a cleaner way to prevent restricted cyberware from being equipped than continuously removing equipment with runtime scripts.

Do not commit to it until tested.

### CET

Development/debugging only unless later evidence justifies otherwise.

Good uses:

- inspect facts
- read game state
- debug
- prototype
- validate hypotheses

CET should not be the core implementation of the released mod.

### Fact Finder

Use during natural Tower playthroughs to observe:

- q307 transitions
- completion facts
- cleanup facts
- 2079-related facts
- world-state changes

Fact Finder shows **what changed**.

WolvenKit and resource analysis should determine **why and where it changed**.

---

## Research priorities

The single highest-priority investigation is:

> Compare normal ending + One More Gig restoration against The Tower cleanup.

Determine:

- what disables the open world during The Tower
- what disables base-game quest systems
- what disables EP1 systems
- what blocks the map/hub
- how normal endings restore gameplay
- which restoration steps are absent from q307
- which missing steps can be safely restored without rewinding the story

Important resources to inspect include:

- `q307.questphase`
- `q307_cleanup.questphase`
- `q307_persistent_content.questphase`
- base-game root quest resources
- Phantom Liberty root quest resources
- ordinary ending resources
- One More Gig resources

Produce a Tower-vs-One-More-Gig transition map before attempting broad sandbox restoration.

---

## Agent working method

### 1. Search before reasoning broadly

Use deterministic search and parsers before asking a model to inspect large amounts of raw data.

Prefer:

- `rg`
- PowerShell
- Python
- Git
- WolvenKit resource extraction
- structured dumps
- dependency/reference maps

Do not spend expensive model context on tasks that can be expressed as exact searches.

### 2. Use vanilla implementations as references

For each mechanism:

1. find working vanilla examples
2. document the relevant resources/nodes/facts
3. reproduce the smallest known-working pattern
4. test it in isolation
5. only then integrate it into the mod

Do not invent REDengine structures when a vanilla example can be inspected.

### 3. Make small, testable changes

Do not attempt the entire free-roam restoration in one change.

Each task should have explicit success criteria.

Preferred unit of work:

```text
hypothesis
→ minimal change
→ build
→ install
→ test
→ inspect logs/state
→ record result
→ commit if successful
```

### 4. Keep research separate from implementation

Maintain clear documentation for:

- observed facts
- inferred behavior
- confirmed behavior
- unresolved hypotheses

Do not present assumptions as confirmed game behavior.

### 5. Keep the repository clean

Do not place full WolvenKit installations, game binaries, or unrelated extracted assets into Git.

Do not commit:

- Cyberpunk game files
- WolvenKit binaries
- large generated dumps unless specifically needed
- save files containing personal data unless explicitly approved
- temporary build outputs that can be regenerated

---

## Recommended repository structure

Create directories only when they become necessary.

```text
tower ws/
├── archive/         # packaged/mod-owned resources if needed
├── quest/           # custom quest resources
├── redscript/       # runtime logic
├── tweaks/          # TweakXL resources if adopted
├── tools/           # local analysis/parsing utilities
├── research/        # extracted findings, maps, structured dumps
├── docs/            # design and testing documentation
├── AGENTS.md
├── PROJECT.md
└── .git/
```

Do not create placeholder directories solely to match this tree.

---

## Useful local research tools to build

Prefer small reusable utilities such as:

```text
tools/
├── fact_search.py
├── quest_index.py
├── resource_refs.py
├── graph_dump.py
├── compare_resources.py
└── filter_logs.py
```

Desired capabilities:

- find readers/writers of a quest fact
- find resources referencing another resource
- compare Tower cleanup to One More Gig restoration
- dump quest graph structure
- identify NodeRef usage
- extract relevant build/runtime errors
- create dependency maps
- diff resource exports

Outputs should be concise and structured so models do not need to ingest entire extracted resources.

---

## Roadmap

`ROADMAP.md` is the canonical detailed roadmap. Keep this file and `PROJECT.md` aligned with it.

### Phase 1 — Reverse engineering (~95%)

The major architecture is understood. One More Gig/PONR rollback is rejected; q305/q306 in-place presentation teardown is the better precedent. Research only questions that block a concrete feature.

### Phase 2 — Direct post-credit return (~95%)

Retained-session return is proven. Convert the experiment into production logic, remove diagnostics, support watched and skipped credits, verify no PONR load, and validate fresh transition plus save/load.

### Phase 3 — Basic free roam foundation (~85%)

Most core sandbox systems already work. Verify the remaining traffic, phone, owned vehicles, fast travel, vendors, apartment services, encounters, Dogtown, and long-session save stability. Do not restart the whole open world.

### Phase 4 — World, interaction, and services (~60%; active)

Selectively reverse demonstrated q307 teardown effects. Current workstreams are:

Reassessed 2026-09-25: H10 normal interactions ~80%, general mirrors/devices
~65%, and vendors/services ~75%. These are planning estimates from the tested
and installed rollouts, not proof of complete site coverage or release quality.
See ROADMAP.md for the remaining validation and deferred cases.

- physical-world restoration with a strict restore/preserve/staging/unknown classification;
- H10 mirror, shower, sleep, sofa, and wardrobe restoration;
- one representative non-H10 mirror/device;
- one representative vendor and its spawn/proximity/trade owners;
- localized 2079-versus-ending-staging classification;
- q307 journal/history cleanup;
- a sandbox-service verification matrix.

Do not restore whole roots, ending staging bundles, or speculative owners.

Vendor classification must follow actual service dependencies, not whether an NPC has a name. Keep public identity, retail category, owner pattern, interaction requirements, and runtime validation separate. Named merchants can use standard trading (Christine is a statically traced example); unnamed merchants can have quest gates. Use `research/b0_vendor_rollout/vendor_restoration_plan.md` for the expanded roster and evidence-labelled treatment plan. Batch only proven matching mechanisms, preserve outcome/stock state and restriction profiles, and count the intended actor group rather than assuming every shop has exactly one NPC.

### Phase 5 — Housing and property continuity (~5%)

Latest user rule: after The Tower, all previously owned ordinary apartments lose
home entitlement and require repurchase. H10 costs €$25,000 (2 × a mod-defined
€$12,500 reference price); other previously owned ordinary apartments use their
normal purchase prices without an increase. Never-owned homes keep normal purchase
rules; there is no 1.5x surcharge. Relationship homes such as Judy's are not
purchasable and must follow Tower outcomes. Preserve geometry/shared stash
contents, gate each ordinary home's services until repurchase and verify persistence.

### Phase 6 — Canonical V restriction profiles (~15%)

Implement three selectable profiles: No Nerf, Cyberware Only (likely default), and Full Nerf. Base the cyberware allow/block table on evidence. Clearly separate Tower-supported consequences from balance choices such as exact attributes, HP, or stamina.

### Phase 7 — Activity restoration (~10%)

Restore and validate one representative owner/activity at a time: NCPD, Cyberpsychos, vehicle contracts, airdrops, repeatable combat content, then selected simple gigs. Classify each as safe, conditional, or incompatible.

### Phase 8 — 2079 content and overlays (~35%)

Plan B0 is the baseline: ordinary persistent Night City plus genuine Tower completion and 2079 logical/media state. Add only runtime-validated localized overlays later.

### Phase 9 — Polish and UX (~5%)

Remove diagnostics, smooth the direct handoff, select the starting location, clean journal/tracking and housing presentation, explain optional profiles, and add compatibility handling. A notification is optional; a mandatory Continue/Main Menu popup is removed.

### Phase 10 — Release and long-term stability (~5%)

Run the complete natural-ending → credits → direct return → normal play → save → quit → reload path and validate ending integrity, sandbox, interactions, housing, all restriction profiles, representative activities, and long-session stability.

### Current priority

Current2026-09-28T15:10:34Z: user explicitly approved install. One-light POC
installed idle opt-in as THREE ADDITIVE files. Receipt:
research/misty_viktor_world/light_poc_install_receipt.json; post-install
hashes match, R7 three hashes and919 protected files unchanged, zero
replacements. Offline31node/45guard/141wait/Lua5.1/payload tests pass;
live rendered glow/Hide/Show/streaming/Stop pending. Use only
docs/misty_viktor_light_poc_check.md on a disposable completed-Tower save,
after dark, quit without saving. No original lights, automatic activation or
completeness increase. Earlier install-block instructions below historical.

Current2026-09-28: user authorized building isolated one-light POC. Build and
offline31-node/45guard/141wait/Lua5.1/exact3payload tests PASS. ValidateOnly
protected919 files with game closed. Installation escalation was rejected
before process creation by auto-review (explicit install permission required;
earlier investigation-only scope cited). No workaround, game write or receipt;
three proposed destinations absent and R7 hashes unchanged. Read
research/misty_viktor_world/light_poc_install_authorization.md. Obtain explicit
approval to install additive archive/XL/PTFR_MistyViktor_Light_POC before retry,
then recheck closed game and hashes. Not installed/live-passed; no original
lights changed, automatic activation or completeness increase. Test route
docs/misty_viktor_light_poc_check.md only after installation succeeds.

Latest2026-09-28: R7 sacks/pallet/palletjack/two trucks USER-restored;
wall-gap report withdrawn as misremembered, not a demonstrated defect or
mod repair.86-row R7 log has acquisition, stable sampled Tower guards while
player present, no Stop/release/reload proof. Read live_r7_result.md.
Investigate exact conditional pink hotel neon/seven residual police lamps;
no new installation authorized by this diagnosis request. Preserve R7 and
all R6 successes, no repeated basic prop/terminal/candle/ped checks. Earlier
wall-gap/new-detail live-pending priorities below are historical.

Lighting investigation2026-09-28 complete, no implementation/install. Read
r7_lighting_readonly_api_audit.md and r8_lighting_targeted_control.md. Exact
WK/Codeware layout: Id0x50 is runtime node pointer slot, QuestPrefabRefHash
0x58 is globalNodeID; all19 target/counterpart slots zero. Generic native
ShowWorldNode path exists, static-light rendering and alias registration
remain unproved. Passive resource observer needs new code/cold load and
would not prove live instances. Proposed next isolated POC: one private
copied static lamp, then mesh; only afterward consider a singleton official
alias-only patch with exact-delta/baseline/ending validation. No guessed ID,
blanket WLC03 swap, global recolor or promised immediate CET hide command.
Positive vanilla precedent subsequently resolved: mq016_02_afterlife.scene
790/792 show0/show1 actual worldStaticLightNode1862/placement2359 in
exterior_-23_15_0_0; full QuestPrefabRefHash plus sector.nodeRefs[26]. Read
r7_showworld_static_light_proof.md/JSON. This supports the narrow mechanism,
not successful new alias registration or live control of our targets.

R7 installed idle opt-in2026-09-28T14:08:51Z: construction six native groups/
18 transforms (16 sacks/pallet/jack), two original Behemoth spawners with
private identities. All18 R6 world resources unchanged; native30-node graph
only revision6->7. Exactsource/readback/45guards/92loading/Lua pass; three R6
files backed up,902 other installedfiles unchanged. Read details_r7_assessment,
installreceipt and docs/misty_viktor_details_r7_check.md. Fullvehicle behavior,
incidental occupants, return/duplicates and controlled Stop remain livepending.
No originalrecord/wholebundle/story/save writes. Neon/policeglow identified
butunresolved: fullWLC03swap includes remotegeometry+q307_misty_risingFX;
individualrefs unproven, no globaldelete/recolor or guessedIDs. Terminal also
USERpassed. Preserve allR6successes; no repeatbasic checks/completenessgain.

R6 live2026-09-28 USERpass candles/policeprops gone, pedestrian crossing
solved; residual police glow remains.303-rowtrace crosses postTower/active
reference/postTower saves, not native release/rearm/coldload proof. Read
research/misty_viktor_world/live_r6_result.md. New supplied references1–3
are vanilla precompletion;4–5modded. Next source-backed construction/cement
props, cyan hotel neon, residualpoliceglow and two parked police trucks.
Gameclosed. R7 notinstalled. No blanketWLC_03_Defaultoff: fullscope includes
remote retainingwall/highway probes. Preserve R6 successes, no identical
basiccandle/pedtest or speculative wall/actors/endingreplay/completenessgain.

Current 2026-09-28: R5 also failed user visual checks; native acquisition is
logged but release remains unobserved. R6 installed idle opt-in13:21:49Z:
actual candle-bearing lighting V_Default OFF/Q307_VV ON,19-member original
q001_holo_scene OFF, original Bradbury & Buran terminal/proxy ON, private
single Tower alley crowd-null area. Exact original Viktor same-type readiness
precedent and native presence/inverted-absence predicate support the guard;
live private-ref resolution/rearm still unverified.30 nodes/45 negative guards/
92 loading cases/Lua pass;16 world resources byte-identical. Three R5 targets
backed up/replaced,888 other installed files preserved. Wall gap still
unidentified; do not add guessed geometry, claim nav repair or repeat the
failed direct q307_hide_misty toggle. No actors/Terry/ending replay/story or
save writes/automatic activation/completeness gain. Read
research/misty_viktor_world/repair_r6_assessment.md, live_r5_result.md and
docs/misty_viktor_repair_r6_check.md; receipt determines installed status.

R3 installed idle2026-09-28T01:27Z: passive Tower street visuals/collision
added to R2 opt-in, preserving existing shop behavior.12 private sectors,
788 placements incl Zetatech logo; three installed files verified,819 prior
project files preserved, R2 rollback backed up. Offline scope/45 guards/Lua
pass, live appearance/overlap/support/return/release pending via
docs/misty_viktor_street_r3_check.md. NOT full dynamic exterior, NOT automatic.
No Terry/ambient NPCs yet; no ending replay, story fact/save writes or
completeness increase. Continue NPC/Terry only after first scene check.

Scope update2026-09-27: user requests full Tower storefront/local street art,
ambient replacement and Terry as a fightable standalone named exception.
Read research/misty_viktor_world/street_restoration_plan.md, selection and
terry_record_audit.json. Terry=Character.q307_thug_01/key81616, original tags
Invulnerable. Use mod-owned clone/lifecycle, never original record edits or
assault scene. No Jim/Misty/Johnny/clerk, whole ending bundles, global crowd
disable, story facts or V restriction changes. Source research only; R2
unchanged, no new build/install/live damage proof or completeness increase.

R2 live2026-09-27: rear door opening and old sign/light-strip removal user-pass;
96-row trace saved under research/misty_viktor_world, live_r2_result.md. Finish
occurred near storefront with Enabled/Applied1, Releases/RestoreRequests0; no
Stop/release inference. No repeated basic door/sign check. Full facade/display,
baseline restoration/re-entry/reload unverified; remains opt-in, no percentage gain.

Latest2026-09-27: Misty/Viktor R2 installed idle21:59:46Z. R1 interior visible,
upper-shop rear door blocked/old sign retained. Exact rear entity has both
q115_misty_door_back/q307_zetatech_doors_02 aliases. R2 unlocks only that door
and removes old neon_hide dressing, preserves four R1 world payloads/XL and145
other files. Known Tower door/sign baseline restored on manual opt-out only
when ownership guards hold; otherwise skip vanilla writes and yield. No full
quest compatibility/synchronous lease claim. Read assessment.md,
access_r2_manifest/tests/install_receipt under research/misty_viktor_world;
R1 backups in receipt. Supersedes prior no-door-write rule only for this target.
One updated combined check, no ending replay/basic interior repeat, no save or
automatic activation/completeness gain; rear access/facade/release live pending.

Current2026-09-27: radio audible/visible memorial sample accepted;90-row log
reviewed, no sampled fact changes. No repeat basic check. User chose preservation
of Zetatech/closed-Misty appearance, not old Misty business or ending replay.
Read research/misty_viktor_world/assessment.md, optin_tests.json, shell_tests.json
and install_receipt.json before changing the installed idle geometry candidate.
Three additive files preserve145 prior project files;842 inert placements,
five original collision nodes, no entities/cast/scene starts/story writers.
Initial signed-range builder error is fixed/readback-tested. Native private
variant and opt-in loop pass45 negative cases; physical support/access and
live block resolution remain pending. Next one docs/misty_viktor_world_check.md
route, no unsafe entry if Registered/Applied fails or floor is visibly absent.
Stop only outside80m; rollback only three receipt paths with game closed. Do
not toggle original q307 bundles, restore Misty/clerk/Johnny, replay endings,
unlock doors or promote counter dispatch to physical-streaming success.

User priority2026-09-27: focused radio scheduler/columbarium display validation
now, before shop world/access. Separate PTFR_RadioMemorial_Audit installed idle;
native stableR6 package and prior diagnostics unchanged. Read
research/radio_memorial_validation/assessment.md, tests.json and receipt.
No observed live-output defect or justified native patch yet; one combined
docs/radio_memorial_check.md route pending. Do not run the old world-audit Start
for this test (it attaches the deferred coaster observer). No fact/save writes,
outcome forcing, q204 restart, gig-radio/altar investigation or completeness gain.

Checklist consolidation completed2026-09-27: read
research/restoration_checklist.md for current cross-system status and
restoration_checklist_audit.json for bounded source checks. Vanilla2.31,
runtime evidence and public wiki coverage were compared; no game/save/fact
mutation. Installed != live-passed; original gate != unknown or deferred.
After the newly requested radio/memorial pass: local Misty/Viktor geometry/access/presentation, then bar
ambient NPC behavior. Do not repeat successful basic service/journal tests
or resume user-deferred work. Automatic journal integration remains open.

User confirmation2026-09-27: journal fix cold-load passed. Manual repair and
persistence accepted for the tested fixture; no repeated basic cleanup test.
Next active task: restoration whitelist/service-matrix consolidation, then
local Misty/Viktor shop world/access and affected ambient NPC behavior.
Automatic journal integration is still production work, not installed.
This supersedes historical provenance-pending and journal-first notes below.

Tower journal manual live result2026-09-27: user reports expected behavior;
two traces confirm three unique native writes (both phases/root) to Succeeded,
all88 entries resolved, no Active progress, no audited facts/other quest-root
changes. Final read-only trace starts/stays Succeeded without Repair. Confirm
cold-reload/save-slot provenance before claiming persistence; automatic
integration not installed. Read research/tower_journal_cleanup/live_result.md.
Do not repeat the successful basic repair or infer Tower history solely from
the screenshot of For Whom the Bell Tolls / No Job Selected.

Tower journal candidate installed idle2026-09-27T01:09:21Z. Read
research/tower_journal_cleanup/assessment.md, manifest and install_receipt.json
before changing it. Two additions preserve686 prior files; native redscript
requests complete only Active progress entries in the exact88-entry Tower
tree, with readbacks, guards and ancestry-specific untracking. CET logs baseline
and invokes explicit request; no journal/fact writes in Lua. Offline compiler/
scope/36 negative guards/ten bridge cases pass. Live hierarchy/HUD/new-save cold
reload and subsequent automatic integration remain pending. Use the single
combined docs/tower_journal_cleanup_check.md route; no ending replay or new
coaster/service tests. No completeness increase from installation.

Misty/Viktor shop world/access and affected ambient NPC behavior are scheduled
for the Phase4 world pass after journal cleanup/whitelist, before restriction
profiles and activities. Begin with known local shop defects and Riot/bar NPC
idling; global AI failure is unproved. Viktor service success is separate from
geometry/2079 presentation. Actual story-scene restoration remains later quest
work; do not replay q307 or restore ending staging to repair shop access.

Next active task2026-09-27: Phase4F q307 journal/history and tracking cleanup.
Use docs/phase2b_p2_run1.md: earlier live repair completed only the take-walk
objective; parent phase/quest remained Active. Read current fixture before
repairing; preserve completed history, unrelated quests and Tower/2079 facts.
No ending replay or q307 restart. Follow ROADMAP.md's refreshed priority list
instead of historical mirror/vendor or now-deferred service next steps.

User deferral (2026-09-27): revisit housing/relationship-home services,
fortune-telling, shooting range, altar actions and gig-radio coordination
when activity/quest work begins. Do not continue these investigations now.
Retain research, housing design and separate evidence statuses; deferral is
not restoration or proof of an intentional vanilla gate.

Coaster gesture deferred by user (2026-09-27): stop gesture investigation and
additional ride tests until the user requests resumption. Retain the installed
crash-free ride/exit and existing rollback; Raise arms motion remains unresolved.
This is a work-priority deferral, not a repair or removal of the action.

Coaster offline follow-up (2026-09-27): bounded listener construction, player
dispatch and original cinematic-crash audits produced no justified repair.
Concrete PlayerUseWorkspot handoff registers a tier request; it does not prove
scene entry/jump consumption. Debug listener creation/queue consumption and
original invalid animation-handle source remain unresolved. User could not
verify resting arms due to camera limits: do not infer invisible body meshes.
Read research/b0_world_interactions/coaster_animation_audit/offline_followup.md.
InstalledR6/crash-free ride and stableR5 rollback unchanged; no new manual test,
speculative flags, debug-setting toggles or completeness increase.

Coaster revision6 live result (2026-09-27T00:13–00:16Z): user reports NO arm
movement, no crash, normal walking after Exit; trace hands5/5 and Return1.
Observer SelfTest PASS/mode8192/12 active attachment attempts still yield0
callbacks. Direct clip entry was insufficient; native clip state remains
unknown. No more identical rides/probe retries or speculative flag changes.
See coaster_direct_entry/assessment.md and saved live trace. InstalledR6
hashes verified; stableR5 backup remains. Gate reset not observed before
player unload; all-zero absent-player row is not a reset. No completeness gain.

Coaster revision6 installed (2026-09-26,23:51:08Z): only entryId2->5 on
cheer nodes558/559; nine other native payloads/registration unchanged,668
other tracked files preserved. Stable revision5 archive/observer backed up.
Observer2 defers until active workspot, verifies actual native enum8192,
self-tests queue and logs callback counts; REGISTERED is retired. Native
audit proves a silent absent-record rejection route, not exact prior cause.
Offline scene/150 graphs/128 guards/Lua/compiler/payload checks pass. Visible
gesture and callback delivery remain unverified; next single combined check
docs/coaster_direct_entry_check.md. Consult coaster_direct_entry receipt and
coaster_animation_audit/native/assessment.md. Do not reinstall old observers,
claim animation fixed or repeat unchanged prior tests. No completeness gain.

Coaster observer live result (2026-09-26): latest trace178 rows, hands5/5,
one normal Return and authorized temporary gate restored0; user still sees
no arm animation. Observer compiled/reports REGISTERED but receives ZERO
callbacks, including native entry/exit. Diagnostic inconclusive; do not classify
clips as played/skipped/missing or request another identical ride. See
research/b0_world_interactions/coaster_animation_audit/assessment.md and saved
live trace. Preserve revision5 ride/exit; resolve instrumentation first.

Coaster animation observer installed (2026-09-26,23:15:55Z): additive read-only
redscript listener plus existing CET logger update; revision5 native archive
unchanged and656 other tracked files preserved. Compiler/Lua lifecycle tests
pass; native callback delivery remains live-unverified. Read
research/b0_world_interactions/coaster_animation_audit/assessment.md and receipt.
Use docs/coaster_animation_trace.md: one Raise arms selection with played,
skipped/missing callbacks, normal Exit, restore the authorized temporary gate
and quit without saving. This is diagnostic, NOT a visual repair. Preserve
the new logger when building a subsequent native patch; the older native
installer receipt contains its superseded hash.

Coaster revision5 runtime follow-up (2026-09-26): six gesture requests/starts,
one normal Return; user confirms no crash and free movement after Exit, but
NO arm animation. Idle0 did not solve visuals. Preserve revision5 as stable
ride/exit rollback; inspect coaster_repeat_gesture/assessment.md and trace.
Requests2 denotes rearm, not a second ride. Do not repeat basic entry/exit
tests alone or claim full coaster restoration; target gesture playback only.

Coaster revision5 (2026-09-26): revision4 first Raise arms silent with1/1
request/start, second press crashes. New dump proves node559's Success0 output
record was missing, triggering one-past-table read. Restore empty Success0 on
558/559 and set enableIdleMode0 for action playback. Idle-mode diagnosis is
inferred with native NPC action precedent; player visuals unverified. Read
research/b0_world_interactions/coaster_repeat_gesture assessment/evidence/
receipt. Exact full-scene delta and callback-coverage checks added. One ride
with two separately offered gestures and normal Exit is live-pending. Do not
retest revision4; retain lipsync correction, no completeness increase.
Revision5 installed22:09:37Z: only coaster.scene changed, nine other native
payloads/registration unchanged,640 tracked files preserved. Offline150 graphs,
128 guards, callback coverage and Lua51 pass; no save modification or live pass.

Coaster combined revision4 (2026-09-26): revision3 Exit crashed after
Finished1/workspot=false, Requests1/Returns0; HandsRequests5/HandsStarted0.
Exit dump proves player lipsync6 versus live table count1. Rebase original
V-only lipsync to0 plus fix two action input stamps; exact full-scene delta
allows only these changes, no exit events/edges altered. Arm-only revision4
below was never installed. Read research/b0_world_interactions/
coaster_hands_binding assessment/evidence/receipt before testing; one cold
disposable ride with one Raise arms and normal Exit remains live-pending.
Do not retest revision3 or claim restored/crash-free from offline checks.
Combined revision4 installed21:19:59Z with game absent: only coaster.scene
changed, nine other native resources/registration unchanged,626 tracked files
preserved. Offline150 graphs/128 guards/Lua51 pass; saves untouched, live pending.

Historical arm-only revision4 (superseded, never installed): revision3 Raise arms no gesture,
HandsRequests4/HandsStarted0. Exact bug: scene randomizer561 still sends input0
to558/559, now CutDestination not In. Two destination ordinals changed to1;
full-scene comparison against revision3 verifies no other edit. Game running;
do not install until closed. Read coaster_hands_binding/assessment.md and any
future installation receipt. Gesture after actual start remains unverified.

Coaster revision3 installed21:01:35Z (2026-09-26): revision2 reached the ride,
then crashed after Hands up. Different minidump fault0x1cf71f, not Streetkid
actor-hole precedent. Only cinematic cheer sections558/559 replaced by native
mounted-player workspot gestures plus private request/start counters; optional
yell tail omitted. Two private workspots retain original male/female rig loading.
Seven other existing native resources/registration byte-identical,612 other files
preserved. Offline checks pass; one cold disposable ride/Hands up/normal Exit
pending. Read research/b0_world_interactions/coaster_crash/assessment.md and
receipt. No return/reload/live crash-fix claim; do not retest crashed revision2.

Coaster revision2 (2026-09-26): installed20:39:47Z after revision1 prompt failed
with temporary gate1, Registered1/Requests1/Returns0/scene=true. Copies only
vanilla cart Activate and broken-clue Hide actions before initial scene launch;
repeat loops do not reactivate. Seven other packed resources byte-identical,
registration unchanged,598 other files preserved; rollback in coaster_fix.
Offline150 graphs/128 negative guards/exact two-action/Lua51 checks pass.
Live repair unverified. Read research/b0_world_interactions/coaster_fix/
assessment.md and receipt. Do not force more story/power/repair facts or claim
gate1 restoration complete; no full mq006 root or Johnny/party restoration.

World-interaction batch2026-09-26: three automatic candidates installed at
18:23:33Z, preserving582 prior tracked files with three additions. Radio media
keeps native scheduling/outcomes and restores radio_on once after the ending
board shutdown; future shutdown respected. Coaster reads original earned gate,
uses40-node standalone V/cart-only scene and private ride bridge, retains
native ride/Exit/StopWorkspot. Memorial controller retains all34 death/outcome
variant actions but removes scanner59 -> Johnny Activate61. No roots/official
replacement/housing unlock/romance reset/new production polling. Offline150
graphs/128 negative guards/dense actor/registration/payload/Lua51 tests pass;
live candidate behavior pending. Read research/b0_world_interactions/batch/
assessment.md and docs/world_interactions_check.md before touching this batch.
Whole-table restoration is partial: paid fortune route/binding, disconnected
range input, actual altar action, gig radio, housing entitlement and relationship
non-mirror utilities unresolved. Do not label unknown implementations gated
or claim synchronous coaster ownership release from QuestOwns. No completeness
estimate increase from candidate deployment.

Dancing result2026-09-26: user reports all tests passed after movement-exit
correction. Preserved live_20260926T174750Z.jsonl confirms Riot Requests2/Returns2
and7th Hell3/3, idle V afterward. Empathy/Totentanz gates0 stayed closed. Native
movement-axis exit, no Stop choice. Available-site actions/exit/re-entry passed;
cold reload/interruption remain unverified. No further basic dance check.

Club dancing installed2026-09-26T17:36:51Z: four automatic guarded public
candidates (Riot/Empathy/7th Hell/Totentanz), twelve native resources and a
read-only test logger; three additions preserve549 previous files. Retain
saved availability, no unconditional vanilla enable writes. Atlantis is q108
memory staging and excluded. Read research/b0_club_dancing/assessment.md and
docs/club_dancing_check.md. Exact scene/graph/actor/cleanup,176 negative guards
and Lua51 checks pass; live available-site actions/repeat passed above, reload
unverified. Future eight-owner
inventory and five direct dependencies: research/b0_world_interactions/
restoration_plan.md. Do not wholesale restart radio/gig/Johnny-bearing owners.

Lizzie's mirror deferred at user request (2026-09-26): physical surface not
identified. Trigger found statically; exact scene/device ownership and live
registration remain unresolved. No installation or further manual search.
Read research/b0_lizzies_mirror/assessment.md before revisiting ID9; it is not
restored or intentionally gated.

Mirror sample result (2026-09-26): IDs4/12/14/15/37 user-reported working on
the supplied five-site route. Do not repeat these basic checks without a new
regression. Durable trace/reload/interruption are not confirmed. Possible
Lizzie's surface found near security room; identify its exact world/trigger
owner from read-only position/entity evidence before restoration.

H10 TV live result (2026-09-26): user confirms seated picture and audio after
media-owner installation; off on Stand is retained vanilla behavior. Normal
playback user-passed, not explicit multi-channel/save-reload/long-session proof.
Read research/b0_tv_media/assessment.md; no need to repeat the basic playback
test. Earlier pending notes below are superseded only for normal playback.

Latest TV follow-up (2026-09-26): media candidate installed16:33:49Z,508 prior
files preserved. First repair restores channel choices, NOT
picture/audio. Guarded media-only candidate built; six unchanged native channel
references, original #tv_content audio/display prefab acquired only behind
post-Tower guards. No broad root restart/tv_on writer/polling. Offline graph,
payload and42 negative guards pass; no live playback pass. Read
research/b0_tv_media/assessment.md and receipt. Future media owner requires
coordination; QuestOwns is not proof of synchronous prefab/callback release.

H10 TV follow-up (2026-09-26): candidate installed16:16Z,493 prior files
preserved. Live tv_on0/tv_apartment1/H10 Active1/Interrupted0
with black/silent screen. One-time native availability repair built; read
research/b0_tv_restore/assessment.md and install_receipt.json before changing.
Exact completion guards plus Applied prevent ending interference and repeated
override of later quest TV shutdown. No root restart or polling. Offline tests
pass; picture/audio and save/reload remain live-pending, not fixed by assertion.

Mirror scope update (2026-09-26): four additive candidates installed at15:45:45Z,
two files,478 prior files preserved. User retains Streetkid features and requests
original companion-home mirror behavior now; whole-home access policy is later
Phase5. Additive new-camp/Judy/Joss/Kerry candidates preserve original scenes,
local gates and camp mirror/wardrobe handshake (not a relationship-unlock fact).
Read research/b0_relationship_mirrors/assessment.md and install_receipt.json.
Offline tests pass; no new-site live/reload proof. Installed coverage
40/44 is candidates, not runtime completeness. Lizzie9 unresolved; ending-only
16/17/18 and Tower hospital excluded. Rental/property mirrors remain Phase5.
No door unlocks, apartment/companion roots or relationship resets authorized.

Latest remaining-mirror rollout (2026-09-26):8 automatic guarded candidates
installed (IDs4,6,12,14,15,19,24,37), two additions preserve476 prior files.
Original complete scene payloads and native leaf edges retained, qualified
local trigger refs, Shady exit handshake namespaced PTFRRM12_Exit. All entry
guards require Tower completion and preserve original availability; no new
polling/CET writers/door unlocks/story roots. BD studio is vanilla one-shot.
Read research/b0_remaining_mirrors/assessment.md before changing this package.
Offline checks pass; new-site live/save coverage is unverified. Controller
coverage36/44 is candidate installation, not full world-mirror completion.
Deferred7,9,10,13,16,17,18,20 and DLC housing owners remain separate blockers.
Red Dirt auto/rearm passed by user and two logged native return cycles; no
forced cold-reload claim. Do not restart completed ordinary-mirror tests.

Latest Red Dirt automatic integration (2026-09-26): installed native bootstrap
sets only PTFRBM42_Enabled=1 after original C5 guards (minus manual permission).
Original C5 owner/resources/registration/counters and one-second loop retained;
no duplicate prefab or new polling. Read-only CET bridge replaces manual helper,
460 other files preserved and rollback backed up. Offline checks pass; live
automatic/repeat/reload pending. Read research/b0_red_dirt_auto/assessment.md.
Do not install the superseded remote-arm helper or restore manual CET writers.
Original exact `sq011_mirror_off ` gate and interruption/suspension remain.

Latest Red Dirt C5 (2026-09-26): user reports tests passed. Preserved
validation_c5_red_dirt/live_20260926T143856Z.jsonl shows one native request/return,
Interrupted0 and clean Stop with idle V. Original helper is still installed;
revision2 remote-arm change is workspace-only. Do not claim automatic
integration, second native re-entry or cold reload from this one-cycle trace.
See research/b0_general_mirrors_devices/assessment.md for the current evidence.

Latest Streetkid automatic step (2026-09-26): revision4 passed user actions and
logged normal return. Automatic repeatable candidate installed with PTFRSKA
native one-second rearm and unused-prompt departure; unexpected interruptions
stay fail-closed. Redscript writes only permission/departure, old S2 CET is
read-only. 403 other files preserved. Legacy resources retained. Consult
research/b0_streetkid_auto/assessment.md and docs/streetkid_auto_check.md.
Automatic/repeat use now user-reported working; reload remains unverified.
No completeness increase. Do not reinstall
old opt-in controllers or clear legacy ownership facts.

Red Dirt C5 is the next single-site opt-in: observed local disable gates0,
no interaction reported. Full native/helper guards and durable logging are
prepared; installation status is in
research/b0_mirror_rollout/validation_c5_red_dirt/install_receipt.json.
Use docs/red_dirt_c5_test.md. Do not force sq011 facts, restore its story root,
or expand other mirrors. Live actions/re-entry are not yet confirmed.
C5 receipt confirms installed idle: three additions, 431 prior files preserved.
First arm refused on scene=true near the working bartender. Helper revision2
is workspace-prepared (remote idle arming, no 50m limit); native resources and
busy guards unchanged. Installation requires game closed and a separate
helper_revision2_receipt.json. See docs/red_dirt_c5_test.md; no live mirror pass.

Latest device follow-up (2026-09-26): original Streetkid S2/S3 probes crashed
from a player actor-index hole left by removing Johnny from the Kerry template.
Both minidumps establish actor3 minus ordinaryCount2 selected nonexistent
player slot1. Typed actor3->2/performer769->513 repair is regression checked;
S3 revision2 live load/return passed with unchanged required facts. Corrected
S2 revision2 nose/normal exit passed, with blank labels and missing glass and
reflection. Revision3 is installed idle: compact/localized choices, scene-owned
glass/Drink, explicit Get up after Fix nose, and narrow local mirror
variant/device cleanup. It preserves 377 other files and backs up revision2.
See `research/b0_streetkid_seat_mirror_s2/assessment.md` and
`docs/b0_streetkid_seat_mirror_s2_test.md`. Do not arm S1 or S3 concurrently.
Revision3 live confirms readable labels, room reflection and clean return;
glass appears only after Drink and V reflection is absent. Both TPP body
definitions remain spawnOnStart0 with no activation branch. Audit minimal body
presentation and initial prop placement; do not copy prologue clothing waits.
Inspect is optional. Full visuals/actions remain unverified;
no automatic integration or completeness increase. Preserve working services.

Latest revision4 follow-up: installed idle with revision3 backed up and 389
other tracked files preserved. Adds matching-body activation/spawn wait/lean270
workspot and explicit normal Deactivate from vanilla patterns, uses public
mirror default appearance, and anchors an always-acquired scene-owned glass
to the verified bar marker using authored pickup/stool transforms. COUCH label
override removed. No prologue clothing waits or story facts. Offline tests pass;
initial glass, current-V reflection fidelity and cleanup need the short test
in the same S2 test document. Do not claim runtime interrupt-body release tested.

Vendor status rule: **restored** means the vendor service works when available,
or is intentionally disabled by original quest facts on the tested save. Apply
this to all vendors, including quest, unlock, death and refusal outcomes. Do not
force a closed vanilla gate merely to make a vendor appear. Track unknown
owners and untested behavior separately.

Latest S4 (2026-09-25): eight automatic service candidates are built for Nix,
Yoko, Mateo, Fingers, Viktor, Karim, Ronald and Bill. Read
`research/b0_story_eight/assessment.md` and `docs/b0_story_eight_check.md`.
Deployment is confirmed by its install receipt. The user reports the eight-site
teleport check worked as expected; detailed actions/return/reload coverage is
unspecified. Offline exact graph/scene, 139 negative guards, 14-script compile,
Lua51 and installation fixture checks pass. Preserve all 95 prior files.
Original/earned gates and death/refusal outcomes remain mandatory. Compatible
service scenes are mod-owned; story starts, rewards and Johnny paths are not
restored. Viktor uses ordinary service presentation without changing Tower
facts/world variants; 2079-specific actor appearance is not claimed restored.
QuestOwns inhibits wrapper startup only, not a tested universal release lease.
Pepe remains gated (default_on=0, mq040_active=1, mq040_done=0); do not clear it.

S4 install receipt now confirms installation with the game closed: four
additions preserve all prior 95 files, giving a 99-file baseline. Do not
reinstall the additive installer or infer a live pass from this receipt.

Latest extension (2026-09-25): S3 automatic Fred/Cassius/Pepe/Charles service
candidates are installed. Four additive files preserve all 91 earlier files.
Two mod-owned scene derivatives exclude incompatible quest-progression choices;
original quest resources and local availability/outcomes remain intact.
Offline graph/scene/13-script/Lua/installer tests pass; combined live first/return
check is next (`docs/b0_story_services_check.md`). Zane is user-reported working,
but lease/reload remains unproven. All-story-vendor restoration is partial:
Nix/Yoko/Mateo/Fingers/Viktor/Karim/Ronald/Bill remain explicitly deferred; consult
`research/b0_story_services/assessment.md` before touching their owners. Do not
copy whole quest roots or treat Suspended/Excluded as synchronous owner release.

Claire compatibility (2026-09-25): read `research/b0_claire/quest_compatibility.md` before related quest work. Native `claire_default_on` already coordinates service shutdown/re-entry. Garage Reactivate precedes default-off; do not blindly transplant Zane's despawn/lease pattern or restart another default-dialogue owner. Static audit found no defect in examined availability paths; live restored-quest concurrency is unverified. Installed Claire package unchanged.

Latest story-service step (2026-09-25): Zane/Jinguji S2 automatic candidate is installed, adding four files and preserving all 87 prior files. Read `research/b0_story_zane/assessment.md` before further mixed-story work. The mod-owned scene changes only the mq030 meeting write; all dialogue/services/earned discounts remain. Future quest restoration must request the mod-owned QuestOwns lease and await actual release before competing ownership. No mq030 root or original scene changed. Offline checks pass; live service/lease/re-entry pending in `docs/b0_story_zane_check.md`. Do not claim generic future-quest compatibility or batch Fred/Nix/Yoko/Viktor from this example without their own route audit. Stadium icons returned spontaneously; the proposed marker commands were never run and no marker repair is justified by that observation.

S1 follow-up (2026-09-25): user reports Dogtown services working but Stadium vendor map icons absent. Preserve working owners. Their copied native graphs already include POI Active nodes; inspect live journal state and map filters before proposing a narrow marker repair. No root restart/global-fact reset. Per-site/cold-reload coverage is unspecified; see `research/b0_special_services/assessment.md`. This supersedes S1 live-pending status below.

Latest batch (2026-09-25): S1 installed 19 automatic Dogtown service-owner candidates (six container-zone, ten Stadium, Farida/Anderson/Odell). Four additive files preserve all 83 earlier files. All original nested payloads/edges/scenes and earned/local gates remain; guards additionally require `q307_ep1_killed=1`. No regional/story root or Johnny Easter egg restored. Offline tests pass; S1 live validation is pending. Next: `docs/b0_special_services_check.md`. The all-special-vendor request is partial, not complete; remaining specific story/survival/entry blockers are in `research/b0_special_services/assessment.md`. Claire is now user-confirmed working, supported by two logged entries/normal requests and one exit; no cold-reload proof. Earlier priority notes below are history where superseded.

Latest extension (2026-09-25): Claire's single-site automatic candidate is installed. Only `default_dialogs`' narrow `root/node4/node19` prefab-owning service phase is copied; original scene, refusal/angry routing, local meeting/default gates and dialogue are preserved. No race/default root or outcome reset. Four additive files leave 79 existing files unchanged. Offline graph/payload, ten-script compilation, Lua and installation checks pass; live first/return/reload remain pending. Next: `docs/b0_claire_check.md`; see `research/b0_claire/assessment.md`. Do not expand to other special vendors yet. Yagami's subsequent user report says all tests passed; reviewed log confirms automatic enable and four native entries/exits, not cold reload. That supersedes its earlier pending first/return status below.

Latest extension (2026-09-25): Yagami Market / `cct_cpz_food_02` is identified from compiled world resources and installed as an automatic candidate. Its exact scene marker has a `_duplicate` suffix; only the new mod-owned scene-node copy changes that reference. Complete vanilla service/local gates are preserved. Four additions leave the existing 75 baseline/bar files unchanged. Offline tests pass; live first/return Trade and reload remain pending. Next: `docs/b0_cpz_food02_check.md`; see `research/b0_cpz_food02/assessment.md`. The preceding bars are user-reported working, without specified complete route/reload coverage.

Current extension (2026-09-25): four ordinary bar owners are installed as automatic candidates on Baseline R1 (`cct_cpz_food_01`, `std_arr_foodshop_01`, `wat_nid_foodshop_02`, `wbr_hil_foodshop_01`). Four additive files leave all 71 baseline files unchanged. Full vanilla scenes and gates remain intact; bar departure defers during drinking/workspot use. Offline checks pass; live actions/return/reload are pending. Next: the combined check in `docs/b0_ordinary_bars_check.md`; do not claim all bars restored or broaden to story bartenders. See `research/b0_ordinary_bars/assessment.md`.

Current implementation baseline (2026-09-25): Restoration Baseline R1 is installed.
Use `research/restoration_baseline/assessment.md` and
`docs/restoration_baseline_r1.md` before changing restored services. Existing
native resource identities are preserved; legacy CET gameplay writers and two
superseded runtime jobs are retired. Build on R1 rather than reinstalling older
opt-in controllers. A combined live save/reload check remains pending; offline
integration/rollback checks passed. The numbered list below is the original
phase priority order, not a claim that already restored H10/mirror/vendor work
must be restarted. Respect the evidence-labelled remaining deferred services.

1. Finish the representative H10 mirror.
2. Map shower, sleep, sofa, and wardrobe.
3. Restore one representative general mirror.
4. Restore one representative vendor.
5. Finish q307 journal cleanup.
6. Produce the q307 teardown inversion/restoration whitelist.
7. Implement repurchase of all previously owned ordinary apartments: H10 for
   €$25,000, the others at normal prices without an increase. Include it in the
   integrated alpha checklist.
8. Define restriction profiles and the cyberware allow/block table.
9. Restore one representative activity or gig.
10. Integrate proven mechanisms into the production post-credit initializer.

---

## Testing rules

Always use disposable test saves.

Recommended save roles:

```text
MASTER
  untouched

TEST_ENDING
  q307 / ending behavior

TEST_SANDBOX
  free-roam restoration

TEST_CYBERWARE
  post-Tower restriction testing
```

Never mutate the master test fixture without a backup.

### Minimum release tests

A release candidate must verify:

- Tower plays normally
- thug scene unaffected
- Misty scene unaffected
- final scene unaffected
- credits work
- direct retained-session return works after watched and skipped credits
- no pre-ending/PONR save is loaded
- free roam starts correctly
- map works
- vehicles work
- saving works
- reload works
- Tower remains completed
- Johnny's engram remains removed and visible projection absent; any retained supporting dialogue passes R4 cast/presentation checks
- the selected restriction profile persists and cannot be bypassed through save/load or equipment paths
- Dogtown works if enabled
- restored activities complete normally
- restored activities do not break save loading or other quests

Long-term save stability is more important than merely getting player control back.

---

## Git discipline

Initialize Git at the workspace root.

Use small commits tied to working milestones or isolated research results.

Suggested commit prefixes:

```text
research:
tool:
quest:
runtime:
sandbox:
restriction:
activity:
test:
docs:
fix:
```

Examples:

```text
research: map q307 cleanup facts
tool: add quest fact reader/writer indexer
quest: add minimal post-Tower completion hook
sandbox: restore map access after continue
restriction: block post-Tower Sandevistan equip
test: document save/reload regression
```

Before committing implementation work:

- build succeeds
- expected game behavior is observed
- logs have been checked
- test result is recorded

Do not hide unresolved regressions in a "working" commit.

---

## Agent reporting format

For implementation tasks, keep status reports concise:

```text
Goal:
What changed:
Files changed:
Test performed:
Result:
Evidence:
Known issue:
Next smallest step:
```

Do not produce long speculative explanations unless specifically requested.

---

## Decision priority

When tradeoffs exist, prioritize in this order:

1. preserve The Tower ending and consequences
2. protect save stability
3. minimize and narrowly scope any official-resource patch
4. restore basic sandbox functionality
5. persist post-Tower restrictions
6. restore optional activities
7. improve 2079 atmosphere

If a feature conflicts with the first three priorities, leave it disabled until a safer implementation is found.
