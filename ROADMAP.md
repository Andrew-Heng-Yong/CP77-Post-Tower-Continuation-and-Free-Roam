# Tower Continued — Development Roadmap

## Current alpha target

**23 October — S28 four-side-job package and approved Patch 2.5 frameworks installed.**
Space Oddity, Ezekiel Saw the Wheel, The Highwayman and I'm in Love with My Car
now have bounded native entry paths. Completed jobs, earned progress, existing
owners and vehicle rewards are preserved; unsupported unfinished routes defer.
The package adds three files with no resource overrides. Full compilation with
the installed scripts, 63-resource checks and 96 deployment cases passed;
716 protected files, including 215 save files, stayed unchanged. Live gameplay
is pending. See [S28 playtest notes](docs/sidejobs_s28_playtest.md) and
[installation evidence](research/sidejobs_s28/assessment_01.json).

The user selected Codeware PR63 and explicitly approved its installation with
TweakXL PR22, ArchiveXL PR31 and official redscript 0.5.32. Separate tool testing
was skipped as requested; actual restoration compilation passed. ArchiveXL's
journal extension and hot reload remain disabled in that upstream proposal.
S28 recovery comes first with `prealpha/sidejobs_s28/deploy_02.ps1` and
`recovery/sidejobs_s28_01`. Framework rollback is separate under
`recovery/framework_pr63_01`. Bounded selected coverage is now 80/80 gigs and
60/78 side jobs (140/158 total), including conditional Family Heirloom; this
does not certify all stages, current-save eligibility or live behavior. Earlier
Heroes/Brendan policy enforcement and H10 startup-latency work remain separate.

**22 October — U10 eight-gig package installed; live tests pending.**
Added bounded native entries for Psychofan, Going Up or Down?, Bring Me the Head
of Gustavo Orta, Sr. Ladrillo's Private Collection, Race to the Top, Scrolls before
Swine, Family Heirloom and Greed Never Pays. Completed gigs and earned unfinished
progress remain intact; unsupported continuation defers without restarting.
Family Heirloom requires a genuine pre-Tower Ghost Town completion witness.
The new observer can record that before Tower; it cannot invent missing history
on an existing post-Tower save, where Family therefore defers.

Three additive files preserve the working H10 handoff and existing packages.
Native tiers, choices, rewards and service ownership remain in place; exact
quest-item inventory checks prevent accidental fresh admission. Psychofan's
Johnny presentation is adapted, Family's embedded cleanup is included, and two
native retaliation paths are restored within the existing controller.
Full compilation, resource checks, independent review and 106 deployment cases
passed. All 712 protected files, including 215 save files, stayed unchanged.
See [U10 playtest notes](docs/gigs_u10_playtest.md) and
[installation evidence](research/gigs_u10/assessment_01.json).
Recovery starts with `prealpha/gigs_u10/deploy.ps1` and `recovery/gigs_u10_01`,
then S27/DT1/S26/S25 and older packages. File rollback is not save rollback.

**22 October — resume unfinished jobs; reduce restoration waiting.**
User confirms H10 arrival is fixed. Keep that working handoff and camera repair.
The next startup improvement should eliminate the reported need to stand still,
holstered with menus closed for about a minute. Measure the restoration critical
path, separate safe background preparation from scene/phone/encounter activation,
and retain necessary per-operation guards. No measured fixed 60-second timer or
completed speed repair is claimed.

The user now wants unfinished jobs to **continue their existing progress**, not
restart. This supersedes the 17 October side-job restart request and inherited
restart wording in R6/R6.1. Completed stays completed; never-started uses its
native beginning; unfinished resumes its objectives, choices and earned rewards.
Unsupported progress must defer, not silently restart. Existing bounded resume
routes remain useful, but generic continuation is not implemented. Gig freshness
and the excluded-prerequisite pre-Tower completion rule are not otherwise widened.
The current-selection pointer records this policy override; pinned lists remain
unchanged. No runtime patch or installation accompanies this status update.

With U10, installed implementation coverage against the current list is
**80/80 bounded gig entries** and **56/78 side jobs**: **136/158 (86%)**, leaving
22 side jobs. Family's pre-Tower history requirement remains conditional;
these numbers do not mean all eight additions are eligible on the current save.
This counts bounded restoration routes, not complete support for every progress
state or successful playthroughs. S25 covered 52 older roots and S27 added six;
Heroes and the Brendan dumpster job are excluded from the current numerator.
All five tracked general activity categories have installed support and a user
functional pass: NCPD scanners (157 entries), vehicle contracts, airdrops,
cyberpsychos (17 sightings), and repeatable races (four routes). Exhaustive
rewards, repeat cycles, persistence and fresh-ending integration remain unverified.

**21 October — prerequisite policy clarified, R6.1 not deployed.**
For a selected follow-up whose required prerequisite is excluded, that
prerequisite must have been genuinely completed before Tower with the required
outcome. Incomplete or unknown pre-ending history blocks the follow-up. Never
restore, force or backdate an excluded parent to unlock a child. Approved
prerequisites may still progress after Tower normally. Preserve native AND/OR
dependencies and existing owners/rewards. Full recursive relationship coverage
was not proved by the earlier 1,903 checks and remains an admission requirement.
[Current policy](research/gig_restoration/lore_whitelists_v6_1_dependencies.json)
keeps the same 80 gigs and 78 side jobs and corrects One Way or Another's
prerequisite to Roads to Redemption. No installed enforcement changed.

**21 October — final whitelist selection audit closed, R6 not deployed.**
The broader implementation target now contains **80 gigs and 78 side jobs**:
30 additions and one removal from R5. The final 227-record register has 158
included, 51 excluded and 18 separate-scope records; no undecided selection
entries remain. See [final decisions](docs/whitelist_final_r6.md),
[full catalogue](docs/whitelist_final_r6_catalogue.md) and
[current selection pointer](research/gig_restoration/lore_whitelist_current.json).
Implementation and live tests remain separate. Preserve pinned R5/R4 inputs
and existing restorations; do not treat the revised JSON as runtime enforcement.
New Heroes admission and the fresh Brendan dumpster route need a safe successor
policy migration, not removal of S27 or reset of already-issued owners.
Personal Link and the existing Basic Kiroshi exception are retained. Kerry's
house remains the sole retained-home/access exception, without Kerry quests.

**21 October — S27 side-job expansion installed; live tests pending.**
Added original fresh entries for The Beast in Me's five-root story-race family
and Heroes' original package outcome, including native contacts/phone support
and Mama's later dialogue. Completed/progressed jobs remain protected. The
Heroes funeral is excluded by R6; general unfinished-job restart migration
remains pending. Installed Heroes admission has not yet been migrated to R6.
Three additive files; existing restorations, Johnny policy and DT1 preserved.
Full compiler, native resource checks, independent reviews and 89 deployment
cases passed. All 709 protected files, including 215 save files, stayed unchanged.
The latest working branch records both new families completed, so it is a
regression test, not a source of new entries. See [S27 tests](docs/sidejobs_s23_playtest.md)
and [evidence](research/sidejobs_s27/assessment_01.json).
Recovery now starts with `prealpha/sidejobs_s27/deploy.ps1` and
`recovery/sidejobs_s27_01`, then DT1, S26 capture and S25/older. File rollback
does not undo gameplay saved later.

**21 October — Dogtown user pass.**
User reports Dogtown restored after DT1. This records a functional user pass,
not an inferred pass for every lane, deeper-district wanted behavior or reload.
DT1 stays installed unchanged. S27 adds the bounded Heroes/Claire entries above.
The restart policy below remains the target; no blanket reset is installed.

**DT1 Dogtown checkpoint repair — installed 17 October, 22:43 local; live pending.**
The missing post-Tower checkpoint owner controls vehicle/pedestrian access,
scanning, combat lockdown and a native three-star response to checkpoint guard
or security combat. A small new boot now references that original controller
directly. No replacement gate logic, global police reset or quest restart.
Two additive files; all 707 protected files (including 215 save files) unchanged.
Native/package checks, independent reviews and 35 deployment/rollback cases pass.

Next: cold launch the current working post-Tower branch, start inside Dogtown
away from the checkpoint with no combat/wanted, then test normal crossing and an
El Capitán delivery. Test checkpoint combat separately from peaceful passage.
District-wide wanted behavior and other possible missing utilities remain
unverified; existing vendor/activity restorations are preserved. No ending replay.
See [DT1 tests](docs/alpha_playtest_tasks.md#dogtown-checkpoint-regression--dt1-17-october-2026)
and [evidence](research/dogtown_dt1/assessment_01.json).
After rolling back newer S27, DT1 recovery uses `prealpha/dogtown_dt1/deploy.ps1` and
`recovery/dogtown_dt1_01`, then S26 capture and older packages. File rollback
does not undo changes recorded by later gameplay saves.

**17 October policy update — restart unfinished whitelisted side jobs.**
Completed jobs stay completed. Started-but-unfinished jobs restart from the
beginning; never-started jobs use the original beginning. This supersedes the
Inactive-only selection rule below, but is **not installed yet**. Restart must
be a one-time restoration/migration, not a repeated reset on load or death.
Existing owners must be safely retired before replacement; items, rewards,
completed siblings and shared world/phone state need per-family handling.

Quest-related NPC interactions, shops, contact setup and reward delivery are now
part of each restoration's acceptance criteria. Current blocker: Cassius's
shop opens, but The Gig's free reward is missing or blocked. The saved service
controller is running; do not mistake this for a missing NPC spawn or reset
Ozob's completed job. S26 investigation/build work is separate from pinned S25.

**S26 diagnostic installed 17 October local (18 October 02:01 UTC).** Only two
manual CET diagnostic files were added; no gameplay replacement or reset.
Source audit confirms Cassius's reward-generation fact is already set and
the quest needs possession, not tattoo installation. Next: capture one normal
shop visit to distinguish missing native stock from UI/purchase blocking.
All 58 roots have an NPC/service dependency audit; it is not implementation or
live proof. Existing integrations stay in place. Restart implementation remains
pending targeted retirement of previous owners and per-job world/item handling.

**S25 Inactive-only expansion — installed 16 October, 15:41 UTC; live pending.**
New activations now require an actual **Inactive** root, including the old
unissued S22/S23 routes. Already-issued restorations and their progress continue.
Inactive is not permission to reset a progressed job: per-job native guards,
prerequisites, choices and completed rewards remain protected.

Adds bounded fresh entries for The Gun, Paid in Full, Beat on the Brat and its
fights, Human Nature / Tune Up / Epistrophy, and The Prophet's Song: five owners
covering 19 whitelist roots. The Gun uses the original order/shop/reward slice
without replaying first-meet prop staging. Johnny's voice/hidden-body policy is
unchanged. The current captured branch already has progress/completion in all
five families; it must not gain 19 new entries.

The inventory now has **52/58 roots with a bounded route**, not universal-stage
support or 52 gameplay passes. Heroes and Claire's five story-race roots remain
pending: Heroes needs shared-service coordination, and Claire has a connected
stock phase not found in installed archives. Existing repeatable races stay
unchanged. Aaron's missing partial-progress SMS remains deferred.

Compilation, independent review, 36,826 policy cases and all 107 deployment /
rollback cases passed. Three additions and two backed-up script replacements;
698 protected files including 215 saves stayed unchanged. No game launch.
See [S25 playtests](docs/sidejobs_s23_playtest.md#s25-clarification-and-next-batch)
and [current rollout/recovery](docs/sidejobs_s23_rollout.md).

The entries below record earlier batches and policies. S25 supersedes the old
Failed-or-Inactive rule for new admissions; already-issued work is preserved.

**S24 fresh-entry batch — installed 16 October, 14:33 UTC; live pending.**
Adds seven bounded fresh routes: Happy Together, Violence, Spellbound, The Gig,
Shot by Both Sides, No Easy Way Out and Moving Heat. Every previous restoration
and its progress stays intact. Original per-job gameplay, prerequisites, waits,
calls and rewards remain; Johnny's voice/hidden-body policy is unchanged.
All seven were already progressed/completed on the captured test branch, which
must stay protected—not display seven new entries. Fresh tests need a separate
genuinely unstarted branch; no facts or completed quests were reset.
Full compilation, source checks, independent review and 87 deployment/rollback
cases passed. Three additions, zero file replacements; saves/settings unchanged.
The Gun, Paid in Full, Heroes and Prophet fresh expansion remain deferred for
shared service/owner coordination. This is not all fresh jobs or a live pass.
See [S24 test tasks](docs/sidejobs_s23_playtest.md#s24-fresh-entry-batch--live-tests-pending)
and [rollout/recovery](docs/sidejobs_s23_rollout.md).

**16 October priority change — unstarted whitelisted side jobs first.**
Keep every existing restoration and its saved progress; do not roll back S23 or
disable its partial-progress routes. New work now targets missing **unstarted**
entry paths and their native interactions. Further partial-progress recovery,
including the reported missing Aaron message, is deferred, not declared fixed.
Johnny's voice stays and his body remains hidden.

The existing capture's 33 Inactive roots are not 33 proven unstarted jobs:
Skippy and The Prophet's Song have progress, and boxing/Delamain children belong
to already-started families. Check quest-specific objectives, facts, item/reward
history where relevant, and existing owners. Preserve stock prerequisites and
timers; do not force eligibility or reset progress. Pre-Tower certification is
still a separate future integration task.

First reuse and validate installed fresh-entry paths (for example Only Pain,
Sacrum Profanum, Big in Japan, Brendan and Over the Edge). Then fill fresh-entry
coverage gaps: completed jobs on this test branch do not demonstrate support for
their unstarted versions on other saves, and S22's four resume seams are not
generic fresh-family entries. Completed quests on the current save stay completed.
The priority update itself installed no files; S24 is the subsequent batch. See the
[unstarted-first work and test queue](docs/sidejobs_s23_playtest.md#unstarted-first-priority--16-october).

**S23 full-whitelist family rollout — installed 16 October, 02:10 UTC; live pending.**
The stable live capture covers all **58 R4 side-job roots**: 33 Inactive, six
Active, 18 completed and one Failed. New native adapters cover the remaining
families while keeping active/completed roots and the working S22.1 repair
unchanged. No Easy Way Out resumes its captured Aaron follow-up; Skippy has a
separate user-confirmed continuation, with no pickup/mode-conversation replay.
Original prerequisites/delays remain: this is not 58 immediate journal entries
or proof of every partial stage. Main story/excluded quests remain excluded.
See [S23 rollout and recovery](docs/sidejobs_s23_rollout.md) and the
[playtest checklist](docs/sidejobs_s23_playtest.md). Full alpha is still pending
live gameplay/reward/reload and genuine pre-Tower history integration.

**15 October corrected policy — Failed or Inactive; preserve halfway progress.**
Current selection is R4-whitelisted side/minor jobs with an actual **Failed OR
Inactive** post-Tower root. Resume existing stages without replaying completed
objectives, choices or rewards. Unsupported stages remain protected rather than
silently restarting. Future production selection is whitelist plus **Inactive
before Tower**, using separate evidence. Johnny retains voice with body hidden.
S22's four resume adapters and repaired S2 Inactive admission are preserved by
S23. Unsupported partial stages remain guarded; source-level family coverage is
not a live completion claim. See [current policy](research/sidejobs_s22/policy_01.json)
and [the S23 playtest tasks](docs/sidejobs_s23_playtest.md).

**S22.1 Epistrophy phone-gate repair installed; initial user functional pass.**
The Gig, Beat on the Brat and Moving Heat journal entries appeared in the user
test; gameplay remains unverified. Epistrophy's progress matched, but our
historical phone-count equality check blocked native support. S22.1 removes that
check only: 57 busy flags, progress guards, native cleanup and 3/7 completion
remain intact, with no counter writes or owner restart. One archive replacement;
5,464 policy cases, four captured-state regressions, 57 official byte comparisons
and 47 deployment cases/65 checks passed. Saves/settings/caches were preserved.
Recovery now starts `prealpha/sidejobs_s221/deploy.ps1` with
`recovery/sidejobs_s221_01`, then the S22b transaction below. Next: the same
post-Tower test save, journal activation, an unfinished car, and new-save/reload.

**Previous: hardened S22 installation.** Four bounded
progress routes plus S2 Inactive admission; no old payouts or native progress
reset. 1,069 copied-payload checks, 3,156 policy cases, full compilation/body
readback, 57 official-resource comparisons, and 68 installation/rollback cases
passed. All 215 save files and existing caches/settings were preserved. First
S22 install was recoverably rolled back for additional Delamain cleanup before
the hardened revision; its recovery transaction is already closed. Current
recovery starts `prealpha/sidejobs_s22b/deploy.ps1` with
`recovery/sidejobs_s22_02`, then S21/S2 and older layers. Next is a short journal
check on the same post-Tower diagnostic save, not another ending run.

**Historical S2.1 diagnostic/auth repair.** One
backed-up script replacement adds manual native Failed/progress capture for the
58 whitelist roots and an optional, separate fresh-fixture opt-in. Nothing is
automatically reset or replayed. 2,374 source/model checks, full compilation and
compiled-body verification, and 47 deployment cases/64 checks passed. All 82
other package files and 685 protected files (215 saves, five caches/settings)
were preserved; installed hash and rollback validation passed. No game launch.
Next: load the same working post-Tower S2 test save and run `FailedDetails()` as
documented in the [side-job test notes](docs/sidejobs_s2_playtest.md). Use the
actual surviving state plus source audit to select per-job resume/restart routes.
Recovery: **S2.1 → S2 → R1 → P1 → D1 → N22 → N21 → C1 → N2 → N1 → FO1 → PA6/older**.
See [S2.1 evidence](research/sidejobs_s21_failed/install_result_20261015.json).

**Previous: first side-job batch S2 installed; live admission failure.** Sacrum
Profanum / Losing My Religion and Stadium Love use direct original native
owners plus separate fresh-history admission. Johnny's voice/body-hidden
approach is explicitly approved. Compilation, 387 negative native admissions,
1,431 policy checks and 59 installer cases/71 checks passed. Three files added,
none replaced; 80 prior package files verified and 683 protected files unchanged,
including 215 save files and five cache/settings files. Installed hashes and
rollback validation passed; no game launch at installation. After S2.1 rollback,
recovery starts **S2 → R1 → P1
→ D1 → N22 → N21 → C1 → N2 → N1 → FO1 → PA6/older**. See
[S2 playtest](docs/sidejobs_s2_playtest.md) and
[installation evidence](research/sidejobs_s2/install_result_20261015.json).
AutoSave-10 at 13:32:21 on
15 October is the backed-up post-Tower fixture; Stadium is already completed
there and must stay completed. The remaining whitelist is not implemented.

**Repeatable races R1: user-reported functional pass.** The user reports the test
passed using Johnny's car with no Johnny appearing. All-four-route, exact reward,
voice, repeat and reload coverage remain separate. Stock
mq056 controller restored for four race routes, with original unlock, start,
finish, rewards and rearm. Two additive files; no old files replaced. Previously
delivered invitations resume without another SMS; otherwise the native three-day
invitation route remains. See [the R1 playtest](docs/races_r1_playtest.md) and
[assessment](research/races_r1/assessment.json). Offline graph/resource and
rollback checks passed. After removing S2, recovery: **R1 → P1 → D1 → N22 → N21 → C1 → N2 →
N1 → FO1 → PA6/older**. Installed R1 and older artifacts are pinned.

**Cyberpsycho P1: user-reported functional pass.** Completed sightings remain
completed normally; the Lt. Mower/Regina reset stays an explicit disposable-only
test. All-17, reward-variant, reload and full-ending coverage remain separate.

**Previous: Dogtown airdrops D1 has a user-reported functional pass.** Original
repeatable drops/loot/cooldowns are restored through a one-shot post-Tower entry,
without replaying the introduction. No changes to the working courier/scanner
packages. See [the D1 test](docs/airdrop_d1_playtest.md). Recovery order is now
**D1 → N22 → N21 → C1 → N2 → N1 → FO1 → PA6/older**.

**User-reported passes:** N2.2 scanners are visible and work; C1 car theft works;
D1 airdrops work after the supplied drop-zone teleport. Unforced cooldown
progression is not established because use of the earlier fact-setting test is
unconfirmed. Keep D1 unchanged; no timer stall or repair is confirmed.
Exhaustive encounter/reward, second-cycle, new-save/reload and fresh-ending
coverage remains separate. Earlier pending/failure notes below are history.

**Current N2.2 scanner-marker repair installed; live pending.** One script now
reactivates safely admitted unfinished inactive POIs without requiring a saved
marker record first. Archives/owners/table and completion guards are unchanged;
six supplemental startup permissions and other partial-progress cases remain
separate. Compilation, 24,576 policy cases and 46 installer cases/63 checks pass.
Quick test: **AutoSave-9, level 48, 14:20:26 on 14.10.2026**, menus closed 20
seconds, inspect the sparse districts. No ending replay. See the
[current N2.2 instructions](docs/ncpd_n2_playtest.md). Recovery **N22 first**,
then N21/C1/N2/N1/FO1/PA6. This is not yet a citywide visibility/gameplay pass.

Earlier diagnosis:

**Current scanner repair: N2.1 citywide visibility failed.** The user reports
Watson looks restored but WBR/CCT/HEY/STD/PAC still show few markers; one Westbrook
encounter works. Latest save: 128 N2 startup requests issued, 24 marker
acknowledgements. The saved-marker prerequisite before inactive journal-entry
activation is the leading blocker, supported by frozen save data; live API
result remains unmeasured. All 154 N2 plus six N21 resources merged successfully.
Next is a scoped activation-gate repair, not restarting encounter owners or
resetting completed content. No new patch in this diagnostic turn. Other started
encounters still require separate care. See [the N2.1 findings](docs/ncpd_n2_playtest.md).
Recovery **N21 first**, then C1/N2/N1/FO1/PA6. No repeat ending needed.

**Current 14 October: El Capitán courier restoration C1 installed; live pending.**
Original courier-only sandbox branch, district spawns, deliveries, calls,
challenges, payouts, vehicle-unlock counters, cooldowns and cleanup. Native
onboarding and later Muamar mission retain their completion/eligibility gates;
one native Daniels phone controller and its cleanup support the later mission.
Existing Muamar/NCPD/global phone owners are not restarted. Johnny remains
voice-only. No partial pre-Tower contract/story migration or lifetime-total reset.
No console polling, new runtime scripts, or changes to scanner gameplay.

59 native payload checks,75 negative admissions,220 official-resource byte
comparisons,three packed readbacks and33 deployment cases/43 checks pass offline.
Two additions preserve662 files,including209 saves and5 caches;67 prior package
files verified. The only resource override extends the existing mod-owned phone
cleanup, retaining all eight fixers and NCPD. No official resource override.
[Deferred courier playtest](docs/courier_c1_playtest.md): existing AutoSave-8,
level48,12:10:04,14.10.2026. No ending replay. Recovery **C1 first** with
`recovery/courier_c1_01`, then N2,N1,FO1,PA6 and older transactions.
Evidence: `research/courier_c1/assessment.json`.

**N2 citywide scanner expansion installed; initial visibility test found the blocker above.**
The user reports the N1 activities work; exact completion/reload coverage was not
specified. N2 adds 154 stock-connected scanner owners across all seven regions,
bringing coverage to 157 with the unchanged three pilots. Native gameplay,
prerequisites, calls, rewards, district credit and cleanup remain original.
Completed/started activities and cyberpsychos are not reset. No custom markers,
reward repair or console chatter. Two factless-start exceptions use a quiet
saved-POI reader; unknown state defers safely. Not certified pre-Tower history or
partial-progress migration. Four unwired journal entries are not activated.

1132 native payload checks,2947 negative admissions,191 official byte comparisons,
154 packed readbacks,full script compilation and38 deployment cases/48 checks
pass offline. Three additions preserve659 files, including209 save files and5
caches; no prior runtime file replaced. Gameplay coverage of the expansion is
still pending. [N2 playtest](docs/ncpd_n2_playtest.md): AutoSave-8,level48,
12:10:04,14.10.2026; no ending replay. After recovering C1, recover N2 with
`recovery/ncpd_scanners_n2_01`, then N1,FO1 and older transactions.
Evidence: `research/ncpd_scanners_n2/assessment.json`.

**Historical N1 installation record, 14 October: initially live pending.** Three
fresh-only Little China encounters cover all three scanner subtypes. Direct
original gameplay refs, native POI/tier gates, reward/achievement paths and
departure cleanup; one original NCPD dispatcher controller plus the native token
loop. The existing eight-fixer cleanup chain gains only NCPD, without restarting
its global phone/reset service. No completed/started resets, cyberpsycho
restoration, synthetic markers, new scripts or logging. Not a citywide rollout
or certified pre-Tower history integration.

54 native payloads,134 negative admissions,12 official-resource comparisons,
five packed readbacks and32 deployment cases/42 checks pass offline. Two additions
preserve657 existing files including209 saves and5 caches. Gameplay remains
unverified. [Scanner test](docs/ncpd_n1_playtest.md): AutoSave-6,level48,
11:14:31,14.10.2026; no ending replay. Recovery N1 first with
`recovery/ncpd_scanner_n1_01`, then FO1 and older transactions.
Evidence: `research/ncpd_scanner_n1/assessment.json`.

**Current14 October: FO1 Wakako interaction PASS, user-reported.** The user
confirms it works and matches their pre-ending world comparison; the screenshot
shows available dialogue choices. Other six offices remain unverified.
Seven native default-conversation owners now run only after completed Tower
handoff, preserving original scenes, availability, re-entry and reward guards.
No race/NCPD/side-job expansion, new polling script, console chatter or gig reset.
Two additions preserve all59 PA6 files and GD2. Offline160-node equality,
120 negative admission cases,14 official-resource comparisons, archive readback
and29 installer cases/39 checks pass. Separate exit/revisit/new-save-reload,
other offices and fresh-ending integration remain unverified. No repeat of the
passed basic interaction is required. [Checklist](docs/alpha_playtest_tasks.md).
Evidence: `research/fixer_offices_fo1/assessment.json` and
`research/fixer_offices_fo1/live_result_20261014.json`. After removing N1, recover
FO1 with its deployer and `recovery/fixer_offices_fo1_01` BEFORE PA6 and older transactions.

**Historical installation record, 13 October local / 14 October UTC: PA6 Rogue/H10-actions/quiet-logging
repair installed; live confirmation pending.** Latest user run confirms camera
fixed after credits skip, H10 furniture restored, Emmerick/Claire working, and four
gig markers visible. Preserve those passes without promoting them to complete
world/interaction/reload coverage. [Current short test](docs/pre_alpha_clean_run.md)
uses AutoSave-0 at21:08:28, not another ending replay.

Logs-first investigation found H10 action permission unarmed in the sampled
street/elevator portion and a precise out-of-bounds lipsync index in Rogue's
crash dump. PA6 arms the existing apartment-triggered actions safely offsite and
corrects only Rogue's duplicate lipsync reference/index. Verbose CET logging is
off by default, with manual diagnostics and concise fault notices retained.
Gigs are unchanged: four active POIs now agree with the user's four visible markers;
stock tier waits and full-whitelist gameplay coverage remain separate.

Compilation/readback,96 integration checks and51 deployment cases/86 checks pass
offline. All59 installed hashes and651 protected entries verified. PA6 recovery
must run FIRST with `recovery/postending_pa6_01`, returning to PA5+GD2; then use
PA5 and earlier recovery transactions. Installed source/build/tests are pinned.
Whole-public-H10 geometry, €$25,000 repurchase and broader alpha remain pending.
Evidence: `research/postending_pa6/assessment.json`.

**Historical PA3 installation record (superseded by PA4/GD2):**
13 October PA2 trace showed cinematic tier throughout the covered readiness wait;
full gameplay returned only as the timeout/failure fade-in occurred. PA3 releases
the native blackout before requesting/checking full gameplay, then prepares the
profile and gigs with the screen visible. The existing safety checks and timeout
budgets are retained. Two backed-up files replaced; compile/readback,40 regression/
artifact/model checks and35 deployment cases/55 checks pass, not gameplay proof.
Visual corruption remains unresolved and is explicitly deferred by the user;
shaders/caches/settings are untouched. Evidence: `research/pre_alpha_handoff_pa3/assessment.json`.
Installed 12 October local time: one consolidated package containing existing world/services,
72-gig native restoration, voice-only Johnny, automatic accepted nerf profile and
one-time H10 street arrival. The source is ManualSave-10, Things Done Changed,
level48,22:04:51,20.09.2026. Prior cleanup is recoverable; PA3 does not repeat it.
This is a user-requested pre-alpha check, not the full alpha or a genuine pre-Tower
history test: this already-late ending uses explicit development admission.
PA1 live run: user reports nerf worked but skipping credits during Rogue left V
stuck at Afterlife. Earlier Manual11 clinic location reportedly followed Viktor's
credits segment; a reload may have helped, but that workaround is not verified.
PA3 keeps PA2's native placement and before/after preparation checks, but uncovers
the screen before readiness can wait. No automatic save/reload or failed-save
migration. Recover PA3 before the older PA2/PA1 transactions if rollback is needed.

Updated 12 October 2026. The first integrated alpha must include **all compatible
activity categories**, the previously restored world/services, the apartment
repurchase rule, and the accepted character-nerf profile. Gigs alone are not the
alpha. The current gig-only implementation batch remains one workstream within
this broader milestone; side jobs and other activities are now required before
the full alpha begins.

After The Tower and its credits finish, V must return in the retained 2079
session to **the street in front of Megabuilding H10**, not inside the apartment.
PA3 uses the original H10 street spawn and native quest teleport after credits
cleanup, with Tier1/control checks before restoration activation. Physical
footing/streaming, actual input and persistence need live verification; apartment
entitlement is not granted by arrival.

The detailed [alpha playtest tasks](docs/alpha_playtest_tasks.md) cover deployment
from a pre-ending save, actual history capture, watched/skipped credits, H10
arrival, gigs, side jobs, other activity categories, housing, the accepted nerf
profile, existing restorations and persistence. Phase 10 defines entry and exit
criteria. Historical progress notes below do not override this scope.

Latest housing revision: **all previously owned ordinary apartments lose
ownership and require repurchase** after Tower. H10 costs **€$25,000** (2× a
mod-defined €$12,500 reference price); the others retain their normal purchase
prices without an increase. Do not mistake H10 renovation costs for a purchase
price.
This supersedes the former all-apartments/1.5× proposal.

Housing exception (user revision, 2026-10-21): **Kerry's house is the sole retained
home/access exception**. Preserve V's existing access after Tower; do not revoke
it or require repurchase. This does not restore Kerry, his romance or his quests.
Other homes keep the loss/repurchase or Tower-outcome rules below. Housing H1 is
installed; live loss, purchase, services and reload verification remain pending.

Beta target (2026-10-23): complete the initial post-Tower state, permit documented
missing quest restorations and bugs, and support beta saves in the stable
release. This supersedes the historical development-save compatibility waiver
for any released beta. See [the save contract](docs/beta_release_contract.md) and
[housing checks](docs/housing_h1_playtest.md). The stable release must preserve
saved identities and test upgrades against retained beta saves.

Current full-alpha blockers: full side-job/category rollout, live proof of actual
pre-Tower capture/automatic dispatch, apartment entitlement/purchase handling,
and combined integration regression. PA1 corrects the historical-phone-counter
admission gate without resetting native counters; live phone/interruption checks
remain. ManualSave-17 and ManualSave-20 are superseded by the clean ManualSave-10
rehearsal, which still does not substitute for the genuine pre-Tower alpha run.

## Historical progress updates

Latest2026-10-13T00:24Z: U9 GIG-ONLY IMPLEMENTATION/INSTALL COMPLETE; LIVE TESTS
DEFERRED. All72cast-whitelisted entry implementations +8fixerphones, native
credit/earnedtiers/markers/prestates and scoped native retaliation dependencies.
12additions/0replacements; existing mods, HP150/JV1 and saves unchanged.
Offline combined compile/readback/collision/recovery checks PASS, not gameplay
proof. No sidejob/carcontract/NCPD/otherworldactivity rollout; no devsave migration.
Next: follow docs/gig_batch_u9_playtest_tasks.md when user can play, beginning
ORIGINAL ManualSave-20(pre-U6/U7), one available gig perfixer and lifecycle/reload
checks. All72playthrough is not required to continue development; unplayed rows
remain unverified. Historicalgangpending/runtime/tierrefusals documented.
Later: production preTower genuine-unstarted capture integration/automatic
admission and endingalpha; independent finalfixerreward jobs/sidejobs/world
categories stay separate. Do not treat U9 as completed productionending rollout.

Latest2026-10-12: U8 Life's Work final cleanup USER PASS (finished1, root3,
creditDone1, Heywood2, fault0). User approves moving on without individually
playing every gig; deferred tests remain unverified. NEXT BATCH GIGS ONLY,
all72 cast-whitelisted entries assessed together; no sidejobs or worldactivity
expansion. Development-save compatibility/migration not required. Parallel
native gig, exceptional/Dogtown and shared fixer phone work in progress; U9 not
installed yet. Draft checklist: docs/gig_batch_u9_playtest_tasks.md.

Latest2026-10-12: Life's Work completion/native fixer credit and reported reload
PASS: root3, creditDone1, Heywood2 remain unchanged; fault0. OwnerFinished0 still
pending. Original graph waits one game day after debrief, then departure and
scene exit before final cleanup output. Next use current completed save, leave
area/skip24gamehours/inspect; no repeat StartAll or replay. Other gigs/tiers remain
pending. Evidence native_heywood_u8_reinstall_1/live_lifes_work_result_20261012.json.

Latest2026-10-12: Reinstated U8 startup USER PASS, no crash and map gig icons
visible. Allfour installed hashes unchanged. Unlabelled screenshot does not
establish per-gig owner identity or full gameplay/credit/reload success. Next
continue current session with one eligible gig (Life's Work), then inspect its
completion/credit and new-save persistence. No repeated startup test/restart.
Evidence native_heywood_u8_reinstall_1/live_startup_result_20261012.json.

Latest2026-10-12T22:14Z: At explicit USER request, SAME U8 reinstated after user
attributed crashes to PC memory exhaustion. 3adds/1backed-up replacement,
2364protected unchanged,4filehashes and recovery validation PASS; no rebuild,
gameplay/save/cache/settings changes. Crash attribution not independently proven,
no livepass inferred. Resume U8 test from ManualSave-21 after coldlaunch; ifload
fails stop and inspect, otherwise StartAll once and inspect after15s. Current
recovery uses tools/reinstall_native_heywood_u8.ps1, with separate receipt under
native_heywood_u8_reinstall_1; old withdrawal evidence remains historical/pinned.

Latest2026-10-12T21:58Z: U8 WITHDRAWN following two ManualSave-21 loading crashes.
Both report DX12 allocator "D3D12MA: Out of memory"; actual script compilation
and 24 U8 registrations succeeded. U8 contribution is not yet established.
Recovered only U8 via its pinned rollback: three additions retained outside game,
previous B7 dispatcher restored; U4/U7/HP150 and save bytes verified unchanged.
NEXT same-settings cold-launch ManualSave-21 once, no commands or new save,
wait~30s if loaded, close/report. Suspend U8 gig tests and unchanged reinstallation.
Evidence research/gig_restoration/native_heywood_u8_crash/assessment.json.

Latest2026-10-12T21:07Z: U7 Jeopardy completion/nativecredit/cleanup/reload and
HP150 checkpointfix USER PASS; read-only ManualSave-21 confirms saved completion,
credit1 and balanced Padre phone3/3. U8 seven-gig Heywood expansion INSTALLED,
3adds/1B7dispatcher replacement,2300protected unchanged. Direct original gameplay
refs, original native credit/earnedtiers/selected POI branches, existing U7phone;
no text reroute, custom payout, forcedtier or second phone initializer.
Seven new IDs plus unchanged Jeopardy provide eight whitelisted Heywood entries,
NOT allgigs restored or newseven livepassed. Development admission only;
production pre-Tower history integration, finalfixerrewards, otherfixers and full
interruption tests remain. Whitelist may limit attainable stock tier thresholds.
NEXT load ManualSave-21(level49,16:47:20 12.10.2026), U8StartAll once, then
InspectAll/TierStatus and one eligible gig; NEWsave/reload after completion.
Use current TOP U8section of docs/native_support_u7_check.md, not historical
Manual20/U7/U4 startup below. Evidence native_heywood_u8/assessment.json.

Latest2026-10-12T19:30Z: U7 native phone interruption/reset-parent support and
original Jeopardy completion credit INSTALLED;3adds/1U6script replacement,
2236protectedunchanged. Static/compile/package/recovery checks passed, LIVEPENDING.
NEXT complete Jeopardy on originalManual20 via U7 then U4 (no U6Start/batch), check
Padrebrief/debrief/payout/nativecredit/cleanup, then separateNEWsave/reload. See
docs/native_support_u7_check.md. This is one pilot with stock service slices,
not shared gig redesign or all-gig parity. Othercontacts, earnedtiers/finalfixer
rewards, full interruption routes and productionhistory integration remain.

Latest2026-10-12T19:07Z: NORMAL PADRE CALL CHECK PASSED (USER popup/voice/text,
188-row trace native request/start/end/idle release, counts1/1->2/2 once).
No more immediate briefing test, gigcompletion or new save required; mayclosegame.
NEXT audit/restore required original shared phone interruption/recovery handling
and stock fixer-credit dependency, then meaningful full Jeopardy completion test.
U6reload/otherfixers/productionhistory/fullwhitelist rollout remain unproven.
Evidence native_padre_u6/live_result_20261012T190453Z.json; pinned artifacts intact.

Latest2026-10-12T17:55Z: U6 original Padre-controller entry installed,3additions;
all existing runtime files preserved. Native call/scene definitions unchanged.
NEXT call-only live check per docs/native_padre_u6_check.md on original Manual20.
Then audit remaining shared interruption/recovery dependencies and restore stock
fixer-credit branch. U6 is not global phone parity/allgig completion; no further
gig completion or save/reload required until normal call delivery works.

Latest2026-10-12 U5 trace CLOSED: native gig incoming call request remained
unserviced30.006sec, enabled/available phone and idle setup, then stock text
fallback. User confirms pre-ending popup works. Next scoped original Padre
shared-controller lifecycle repair; not another generic approach/marker test.
Do not infer exact serialized-owner absence or globally restart phoneinitializer.
No completion/newsave needed now; stock fixer-credit repair follows phone repair.

Latest2026-10-12T17:20Z: U4 activation/native journal/written brief USER-pass;
audible Padre briefing unresolved. Native prebrief30s no-answer route is a
candidate, not a confirmed dead phone handler. U5 read-only trace installed;
next original ManualSave-20 short approach capture per docs/padre_phone_u5_check.md.
Then repair exact native phone dependency shown by evidence, followed by original
fixer-credit dependency. Do not replace voice with custom text routes or duplicate
shared controller from idle zeros. No gig completion needed for this capture.

Latest2026-10-12: U4 Jeopardy original-resource pilot installed, live pending.
ManualSave-20 (level49,16:32:18 11.10.2026) has its native Padre tier; save unchanged.
Developer incomplete-as-unstarted admission implemented separately from duplicate/
stage safety. Original calls/scenes/rewards intact, Johnny existing voice-only.
NEXT startup/briefing test on that save, no completion yet. Then repair stock
shared dependencies based on evidence. Partial-stage resets, stock fixer credit,
production pre-Tower unstarted-only automatic admission and full rollout pending.

USER2026-10-12 admission update: Production whitelist restoration requires
pre-Tower captured UNSTARTED state; do not restore already-started gigs there.
Development post-Tower route assumes INCOMPLETE whitelisted gigs are unstarted,
without inventing production history. Keep completed gigs excluded and Johnny
voice-only. Next: apply explicit development admission to unfinished Jeopardy U4
and safely initialize stock graph state; no blanket duplicate-owner/reward risks,
native tier forcing or unrelated fact resets. U4 is not built/installed yet.

Latest2026-10-12T16:16Z: U3 queued-owner reservation fix installed. Stock audit
corrects premature missing-tier diagnosis: Shark branch requires counter11, current
save has4. Release queued/ineligible Shark's Watson lock; reserve only when permitted
or actually started, retaining all other ownership checks. No tier forcing or new
native phone/counter owner. Source/compile/recovery checks PASS; live pending.
NEXT select native-tier-eligible original-graph pilot instead of attempting Shark
at counter4. Then verify native briefing/phone and restore missing stock dependency
branches where evidence requires. Full stock progression/rewards still unfinished.

Latest2026-10-12T15:45Z: U2 STOCK dependency audit + read-only trace installed.
Mapped native Regina phone lifecycle/handshake, Shark prestate controller and
exact native kab_06_finished -> wat_sts_counter+1 branch. No native dependency
restarted or custom reward bridge added. Whole fixer-loop restart and duplicate
phone handlers are unsafe alternatives, not required stock behavior.
NEXT short U1 startup/briefing test on original pre-batch/pre-Shark post-Tower
snapshot with automatic U2 logging. Use result to restore missing stock service
dependencies and exact applicable counter/tier/reward branches. Completion,
cleanup/reload and broader stock-faithful rollout remain pending; audit/mock
success is not native parity. Existing adapters/profile/JV1 unchanged.

USER clarification2026-10-12: Prioritize stock-faithful gig restoration, copying
original graphs where practical. Do not optimize away copies or invent a shared
replacement template. Only intended activity changes are whitelist admission and
Johnny rendering off/voice on. Restore stock dependencies for normal calls,
objectives, rewards, progression and cleanup; retain minimal safe entry and
duplicate prevention. U1 is experimental, not a no-copy mandate. Installed builds
unchanged; their non-stock workarounds are not final acceptance criteria.

Latest2026-10-12T15:07Z: U1 native-Shark reuse trial installed, live pending.
USER direction: restore STOCK gig behavior using original per-gig graphs and
required shared stock dependencies. No shared graph-template redesign or extra
optimization. Small entry/interlock wrapper only; no copied gameplay resources.
NEXT: original post-Tower PRE-B7-batch/PRE-Shark snapshot, U1 Start then verify
native activation/brief/journal. Then completion/rewards/fixer progression/native
cleanup/newsave-reload. Original phone handler and district counter dependencies
are explicit unresolved questions; fix stock dependencies if missing, do not
declare partial behavior stock parity. B7/other pilots retained and protected.
Recovery/evidence: deploy_native_reuse_u1.ps1 and native_reuse_u1 audit directory.

Latest2026-10-12T14:36Z: User-scoped Shark in the Water startup collision FIX
INSTALLED (B7.2). Original generated ID1 conflicts with ep1 native start; single
byte-identical alias gives unused55205.1addition+1backed-up XL replacement,
2138protected unchanged; parser/collision/packedreadback/recovery PASS, LIVEpending.
Next targeted coldlaunch readiness check on SAME postTower test snapshot, not
another all-gig completion test. Existing native tier waits may still defer Shark.
Do not bundle activation/tier/Wakako-lock or started-state changes into this fix.
Broader test is partial:3new Heywood owners running, manytier/prelude waits,
Wakako deferred behind H1;11IDadapters/started expansion/replay/history-alpha pending.
Only deploy_shark_b7_2.ps1 recovers current alias+XL; prior XL installers historical.
Preserve pinned evidence and original saves; file recovery never rewinds new saves.

Latest2026-10-12T13:55Z: B7 broad-batch live startup FAILED before phase binding:
ArchiveXL rejected malformed B7 YAML. B7.1 one-file configuration fix INSTALLED;
real YAML parser now validates76exact boot bindings and rejects original/10other
bad variants. Archive/quest logic/history unchanged;2119protected files unchanged.
Next coldlaunch latest postTower TESTsnapshot, run B7.OverrideAll once, closeCET/
menus/holster/safe15sec, inspect readiness/log. No full gig-completion test required
for this bootstrap check; native proximity still governs fresh journal activation.
Do not infer new55 restoration from parser/installation success.61/72IDcoverage,
11exceptions and broader gameplay/reload/started/replay/ending-history work remain.
Evidence/recovery family_b7_1 / deploy_gig_family_b7_1.ps1 (XL only); original B7
aggregate recovery historical on replaced XL. Preserve all pinned predecessor and
new build/test evidence; original snapshots retained, no save/cache modifications.

Latest2026-10-12T01:53Z: Stop marker-pilot loop: USER confirms prior activation and
handoff; absent marking was their filter setting. B7 broad gig-family implemented
and installed55new fresh native adapters,61/72total IDs.55 live gameplay still
unvalidated; no full-restoration/alpha claim.11 remain:9Dogtown companion owners,
ForMySon multi-input owner and CuckoosNest missing legacy-scene reachability. All72
dispatch via PTFR_GigFamilyB7.OverrideAll("DISPOSABLE_SAVE") with explicit coverage;
native tiers/legacy owners may defer, completed/failed never reset.21 earned-tier
fragments added without global counters/final rewards; existing Wakako reused.
R3 certified-history-only getter available; old missing baseline not fabricated.
Next: broad live activation check when convenient (no additional marker pilot),
remaining native-family exceptions and supported started-stage continuations,
then actual pre-ending history/ending transition alpha once coverage is ready.
Do not ask user to complete55gigs just to prove markers; original snapshots retained.
Install evidence/recovery: research/gig_restoration/family_b7 and
tools/deploy_gig_family_b7.ps1. New build requires coldlaunch; no cache/save editing.

Latest2026-10-12T01:11Z: M6.1 distant H1 map-visibility milestone PASSED by
USER Dynamic/Custom-Gigs screenshots plus118row getter snapshot. ServicePoint
filter excluded the icon in the earlier report. No further immediate marker
visibility test/restart/newsave required; user may closegame. Later native H1
encounter and approach-marker handoff/gameplay remain pending. CityCenter race
icon also USER-visible, but race functionality/restoration remains untested.
Evidence markers_m6_1/map_visibility_result_20261012.json. No new code/install;
preserve pinned predecessor/current tests/receipts and current recovery scope.

Latest2026-10-12T00:48:34Z: M6 user map test FAILED despite native registration
flags. M6.1 fix now INSTALLED, one backed-up script,2074protected unchanged.
Owned approach marker waits for native journal activation before releasing;
native IsVisible/IsActive alone no longer hides it. Compilers/regression/rollback
fixture PASS, renderer/handoff still pending. Evidence markers_m6_1/assessment.json.
NEXT brief ManualSave-20 map check after restart and15unpausedseconds, no gig
completion/TP/override/newsave required. Preserve all prior build/test receipts;
current marker recovery deploy_markers_m6_1.ps1 only. B6 Jpn02 already completed
in latestsnapshot, so a fresh gameplay test needs a separately verified suitable
save later. No new adapters;6gig adapters/66pending,allreplay/ending-alpha unproven.

Latest2026-10-11T21:01:04Z: B6/M6 installed/offlinePASS, livePENDING.
Fresh WeHaveYourWife extends Wakako family to3fresh owners (6gigadapters total,
66of72pending); retains native escort/combat/reward/cleanup and earned-tier ledger.
Session approach-marker fallback addresses unstreamed distant native references
without prematurejournal activation; renderer/tracking/duplicate absence unproven.
5 additions/2backed-up replacements/2047protected unchanged/ValidateRollbackPASS;
currentrecovery deploy_fresh_gigs_b6.ps1 only, mains/evidence pinned. No cache/
directsavewrites, B5.1 persistence and R3capture/cutoff unchanged. Game canremain
closed while userremotePC lags. NEXT whenconvenient: latestNEWsnapshot distant
H1map check after15unpausedseconds, no TP/override/H7replay; nativeH1/B6gameplay
later. Do not claim all-gig/fullalpha restoration. Further fixerfamilies/sidejob
expansion/R3endinghistory/completedreplay/categoryrestoration remainpending.

Latest2026-10-11T20:34:43Z: B5.1 legacyadoption + NEWsave/reload tested PASS.
Frozen242rows/68finalpersistent/zeroerrors, H7stage4/counterAcktrue/base1/3 and
H1stage3 retained, totals2/4/Tier2_Ack1 unchanged, volatile detailsblank. Three
installedhashes match; evidence fresh_b5_1/reload_pass_result_20261011.json.
Reloadmilestone closed; NO further immediate gameplay/restart, usermayclosegame.
No H7 replay/override/reset. No install/runtimeimplementation/cache/directsave
writes by audit; all pinned historical evidence preserved. NEXT reviewed offline
marker/native-family work (userremoteplaylags); H1gameplay/batchlive/R3endinghistory/
67othergig adapters/allreplay/fullalpha remainpending, not all-gig restoration.

Latest2026-10-11T20:19:48Z: B5.1 repair installed (3backups/replacements,
2028protected unchanged/actualhashes+ValidateRollbackPASS). Saved nested fields
now persistent; automatic B5 adoption restores onlytracking fromexistingowned
acks, no replay/repeatedcredit. R3 future snapshot fields fixed, no missing-history
reconstruction or protocol change. Batch boxed-IDfalse-refusal repaired withhash.
CLI/fullSCC/readback11markers/13824source-linkedledger/9LuaJIT/fixture7refusalsPASS,
native adoption/newsave serialization UNPROVEN. NEXT short coldload latestNEWtest
snapshot, wait10sec/InspectH7stage4+H1stage3/totals2/4; another separateNEWsave/reload
confirms tracking. NOoverrides/H7replay/H1gameplayneeded. Evidence fresh_b5_1/assessment;
current3file recovery ONLY deploy_fresh_gigs_b5_1.ps1, previouspins preserved.
Then marker/H1gameplay/family expansion;67gigs/allreplay/endinghistory/alpha pending.

Latest2026-10-11T20:09:01Z: B5 reload check FAIL: both script slots resetstage0,
but H7 native completion/payment/account/credit and totals2/4/Tier2_Ack1 preserved.
Frozen210rows/zeroerrors/fiveinstalledhashes unchanged; evidence fresh_b5/
reload_failure_result_20261011.json. Missing nested persistent modifiers identified;
same R3 snapshot pattern requires independent production-history audit (no fabricated
history). NEXT persistence repair + guarded existing-owned-state adoption WITHOUT
owner/payout/credit replay, then short coldload/Inspect check, not H7 replay.
Hold H1 completion: stage0 monitor cannot service accounting. User mayclosegame;
no further immediate live work, no repair/install yet. Preserve previous route PASS
and pinned builds/tests/receipt. Batch identity/discovery/67gigs/allreplay remain open.

Latest2026-10-11T19:55:50Z: H7 B5 TygerAndVulture completion/cleanup/earnedtier
USER+GETTER PASS on tested route:666frozenrows/111terminal/zeroerrors, native
reward/account1/1/fixer1->2/achievement3->4/CounterAck+Tier2_Ack1;5hashes match.
H1 queued ->nativeStarted/stage3 after menus closed proves sequential request,
not H1 playable/completed proof. Distant marker discovery unresolved; USER sees
marker only after teleport/approach though POI alreadyActive. B5 batch boxed-ID
string guard faulty, per-ID direct overrides work; no new repair/build/install.
Evidence fresh_b5/live_result_h7_20261011.json; preserve frozen trace/pinned mains.
Game canclose after optional separate NEWtestsave. NEXT reload/persistence check
then H1 gameplay, plus scoped batch-identity/marker review; don't replay H7.
67gigs/allcompletedreplay/automatic endinghistory/fullalpha remain pending.

Latest2026-10-11T14:10:16Z: Fresh-family B5 installed (4adds/1R3backup replacement/
1970protected unchanged/5actualhashes+ValidateRollbackPASS). Two real fresh-only
native owners: TygerAndVulture and UntilDeathDoUsPart; their initial spawning,
devices/items/choices/outcomes/departure retained. Authored text replaces4shared
call entries; single native payout guard + independent completion-baseline
achievement/fixer accounting. Separate earned Wakako tierfragment thresholds
2/5/7/8 uses native delay/content/Rogue gates, skips existing messages/tier flags;
no global countloop/default/phone/NCPDtier/finalreward restart. H1 serializes after
eligible tier and H7 native cleanup (4gamehours/departure). R3history unchanged,
H7 missing old scene facts remainunknown; explicitfresh override only for H7.
NewB5bridge twofresh/fiveimplemented gig scope; oldB4catalogue unchanged.
CLI/fullSCC EquipmentEx/349nativepayloads/29graphs/59guardmutants/1264abstract
cases/10LuaJIT/recoverablefixture+7refusalsPASS, NOT live gameplay/payout proof.
5gig adapters/67of72pending, ALLcompletedreplay/fullalpha remain absent.
NEXT coldlaunch new useful family test: B5 fresh queue, TygerAndVulture native
completion/independent credit/earnedtier/departure, H1 sequential activation and
gameplay, NEWtestsave/reload. Preserve original snapshot; no forcefacts/replay.
Then expand source-reviewed fresh families and separate Dogtown companion owners;
capturedstarted Empathy/TalentAcademy/TreatingSymptoms still need continuations.
Evidence fresh_b5/assessment.json; currentrecovery ONLY deploy_fresh_gigs_b5.ps1.
Do not rerun newly pinned mainbuilders/compiler/tests. Previous tested builds,
profile150Body3Relic/R11 and baridledeferral preserved; no directsave/cache writes.

Latest2026-10-11T04:34:39Z: All-whitelisted-gig work B4 PARTIAL dispatcher
installed (2CET adds/1R3backup replacement/1940 protected unchanged/actualhashes
+ValidateRollbackPASS).72latest cast-aware broader gigs mapped; R3legacy71+57
history staysimmutable.3existingnativegigadapters only;69of72stillpending and
ZEROnewnative owners thispass. This is NOT all-gig restoration/fullalpha.
Owner binding72/phase-sceneclosure69+3gaps/215phase refs/1401graphs/354scene refs
is sourcecoverage, NOTnativefreshness/cast/initialization/reward safety proof.
CLI/fullSCC EquipmentEx+21actualLuaJITcases+recoverablefixture/7refusalsPASS;
enginebatchbinding unproven. Evidence batch_b4/assessment.json; recovery ONLY
deploy_gig_batch_b4.ps1 forcurrent3files, predecessor aggregate dispatcher recovery
historical. Keep gameclosed: no newstoryplaythrough requested solely fordispatcher.
NEXT implementation order: (1) reusable fresh-gig family with original eligibility,
no prior item initialization repeats, authored phone/text continuity, native one-shot
reward+independentfixer/achievementaccount; (2) earned tier progression without
restarting globalfinished-job countloop; (3) source-reviewed Dogtown main+cleanup+
after-gig companion owners; (4) remaining capturedstarted Empathy/TalentAcademy/
TreatingSymptoms stages. Retain concrete crash/unintended-action-only hardgates,
not sample-specific counters; missing unreachable ref not automatically unsafe.
Existing character/Johnny/journal/Afterlife and deferred baridles unchanged.

Latest2026-10-11: G3 USER NEWsave/reload PASS; getter04:04:48Z corroborates
unchanged stage4/ownerfinished1/reward+account1/1/counters1/1/no faults and
cleared volatile detail. Tested early success-route + Johnny voice/no-model
milestone closed. Evidence minefield_g3/reload_result_20261011.json.
No further immediate test/processrestart; gamecanclose. NEXT reviewed further
per-owner/batch restoration.4adapters/124others/allreplay/automatic endinghistory/
fullalpha pending. No newbuild/install; preserve pinned evidence and priorbuilds.

Latest2026-10-11: G3 success-route native completion/cleanup USER+GETTER PASS,
Johnny voice/no-model USER-pass.363row frozen trace/86stage4rows/zeroerrors,
reward/account1/1, fixer+achievement0->1 once, OwnerFinished1, J3/3/3/fault0.
Fiveinstalledhashes match; no source/installation changes. New evidence
minefield_g3/live_result_20261011.json + frozen trace. NEXT one NEWtestslot
save/reload Inspect to confirm persistence; no replay/process restart needed.
After unchanged terminal result user mayclosegame, then reviewed per-owner/
batch expansion.4adapters/124others/allreplay/automatic endinghistory/fullalpha
stillpending; priorbuilds/profile/R11/bar deferral unchanged. Johnny pass is
tested-route-specific; independentprops/otherappearances not certified.

Latest2026-10-10T20:04Z: Minefield G3 early continuation installed20:03:26Z,
4additions/1backed-up R3 dispatcher replacement;1883protected unchanged; actual
hash+ValidateRollback PASS. Native chase/delivery/failure/cleanup behind own
one-shot owner; initial/brief/damage repetitions avoided. Native text debrief,
guarded shared patrol clears and independent completion-baseline accounting.
R3 history/explicit resume override integrated without schema/definition change.
CLI/fullSCC EquipmentEx/readback/graph/guard/Lua/recovery PASS, engine UNPROVEN.
NEXT combined coldlaunch Minefield gameplay + Johnny voice/no-model + reward,
counter, departure and NEWsave/reload test. No completed replay/blanket resets.
Original preG3 snapshot retained; recovery only deploy_minefield_g3.ps1, pinned
evidence in minefield_g3. Four adapters/124otherpending; no fullalpha/automatic
endinghistory guarantee. Earlier tested adapters/profile/R11/bar untouched.

Latest2026-10-10T19:27Z: Next owner candidate Dancing on a Minefield G3:
stable PRE early find-car stage, supporting Johnny comments, accumulated car
damage/phone/chase/Badlands payment accounting need non-repeating continuation.
Native 10-resource/26-graph/3-scene audit recorded; G3 NOT implemented/restored.
Prerequisite Johnny JV1 visual-only candidate installed (1 addition, no existing
file replacements). Exact Silverhand completedTower root visual components
hidden through native presentation API; actor/voice/animation retained by scope.
Compile/fullSCC/model/recovery pass is NOT live visual/audio proof. Independent
props/externalFX and transient appearance flashes remain unproven. Next finish
G3 owner audit/build/integration, then one combined gameplay/presentation/reload
test; no immediate game launch needed. Still125adapters/all replay pending.

Latest2026-10-10T19:08Z: Rite G2.1 baseline3 resume route LIVE PASS:
native journalsSucceeded, reward/account1/1, one observed Watson/achievement
3->4, native owner release/stage4 after user skippedtime; USER save/reload
preserves result.733row frozen gettertrace/zeroerrors/146stage4rows corroborates
route and all3installedhashes unchanged. No further immediate test/restart;
user can closegame. ExactcashXP/alternate routes/baseline4/concurrency stress/
coldprocessrestart and production endinghistory stillunproven. Next reviewed
per-owner/batch expansion/generalized safe gates, not whole-whitelist restart.
125otheradapters/allreplay/generaltiers+finalReginareward/G1-at4/voice-only
presentation/R4migration pending; no fullalpha claim. New evidence
gig_restoration/rite_g2_1/live_result_20261010.json; pinned builds/tests/receipt
unchanged, no newinstall. Profile/S1.1/J1/R11/bar deferral preserved.

Latest USER2026-10-10T18:42Z: preserve original save snapshots. Restoration
mutates loaded session state; later native creation of a NEW save records it,
without a mod save-file editor. Reloading original is the recovery path; file
rollback alone does not rewind current/new saved gameplay. Report these layers
separately. User's new-save workflow is not an asserted guarantee about native
autosave/overwrite slot reuse. Documentation only; build/test plan unchanged.

Latest USER2026-10-10T18:39Z: future adapters/revisions should admit the widest
safely supported state range. Hard runtime gates only prevent crashes or
unintended mutations/output; avoid sample-specific counters, unrelated pilot
dependencies and blanket refusal of harmless state variation. Generalize stage/
baseline handling, skip prior work and retain exact-once accounting/target/owner
validation. Unknown paths need audit when executing them risks unintended effects;
safe unusual states should warn rather than block. Approved whitelist/profile/
fresh-resume-replay policy remains separate and unchanged. No blind quest resets,
native fact forcing, duplicate payouts or invented history. This is a FUTURE
design rule, not a runtime update: installed G2.1 remains unchanged and its live
test is still next. Preserve all pinned installation evidence.

Latest2026-10-10T18:34Z: G2.1 fix installed after user3/3 refusal, replacing
three backed-up files and preserving1864 others. Rite now supports matching
3/3 or4/4 without requiring G1 completion. Reciprocal read-only accounting
guards block queued/active/unknown G1/G2 overlap before any new journal writes;
native reward/account once-only logic preserved. Only two G2 graph conditions
broadened; all native gameplay/cleanup unchanged. Both compilers/guard models/
recoverable deployment checks PASS, NOT engine proof. NEXT cold-launch disposable
Tower3/3 preclinic save, nid05 resume override, native gameplay/payment/reload.
No other Watson gig/NCPD completion during test. Success totals4/4 (baseline3)
or5/5 (baseline4), reward/account1/1 and counterack; cleanup waits3gamehours.
R3 history/cutoff/definition unchanged; no deferred auto retry, G1-at4 adapter,
generic batching or full alpha.125 other adapters/all replay remain pending.
Evidence gig_restoration/rite_g2_1; only deploy_rite_g2_1.ps1 forthree-file
recovery. Preserve predecessor/current pins. Character/R11/bar unchanged.

Latest2026-10-10T17:19Z: Rite of Passage G2 exact pre-clinic continuation
implemented/installed: four additions, backed-up dispatcher replacement,1844
protected files unchanged; actual hash/recovery validation PASS. Third adapter,
not whitelist-wide restoration. Skips prior briefing, initial door/checkpoint,
keycard and Enemy9 shard grants; existing keycard and exact native stage required.
G1 must already be completed/accounted, Watson/achievement4/4; guarded native
achievement/reward plus one4->5 Watson update. No tier/final-reward/root restart.
R3 ordered71+57/fingerprint/persistent fields and existing adapters unchanged;
certified exact pre-ending stage needed for auto, explicit resume override only.
Both compilers/EquipmentEx/J1/S1.1, graph/guard/Lua/deployment checks PASS, not
engine proof. NEXT cold-launch disposable-save Rite clinic/download/escape/payout,
separate save/reload and native departure cleanup test. Native cleanup has3gamehour
delay; immediate stage3 is not failure proof. If refused send Inspect; no forcing.
125 other adapters, all replay, general earned tier/final reward accounting,
voice-only Johnny presentation, R4 selection migration and ending/history alpha
remain pending. Preserve pinned evidence in gig_restoration/rite_g2; recovery
only deploy_rite_g2.ps1, no predecessor rebuild. Profile/R11/bar unchanged.

Latest2026-10-10T15:57Z: cast policy R4 now permits supporting Johnny voice,
not visible projection, takeover or Johnny-central story. Panam/Kerry/Judy live
participation excludes whole jobs, including optional calls/messages. Both
lore candidate variants revised: aware34gigs/30side, broader72gigs/58side;
this is a targeted source-backed revision, not a complete cast census. See
research/gig_restoration/lore_whitelists_v4_cast.json.14policy/source checks
pass;8protected source inputs/14installed files unchanged. NO presentation
adapter, migration, new restoration/install or live test this step. Installed
R3 still observes the pinned71+57 and supports G1/S1 only. Per-owner adapters
and a reviewed history/selection migration remain required; no fabricated
baseline or whole-root restart. Rite of Passage remains next resume target.

Latest2026-10-10T15:28Z: B1 offline expansion audit recorded in
research/activity_batches_b1/assessment.json. All128 selected IDs grouped, seven
owners reviewed,14 new regression tests/252 fact-model cases PASS;14 installed
files remain hash-identical. Next target: exact early-stage Rite of Passage
continuation, backed by the existing pre/post capture rather than guessed fresh
availability. Three native resources/three scenes reviewed, no Johnny cast.
Safe resume entry, recording/device stage, reward/achievement/fixer-counter and
retaliation/cleanup audit still precede implementation. Bullets needs a Johnny
scene adaptation; Day in the Life has shared race/vendor ownership; Shoot to
Thrill needs contest/phone/reward handling. These are not whitelist removals.
Kabuki candidate local tier alternatives fail on the captured pair; do not force
unlock facts. No new adapter/install/live test this step.126 other adapters/all
replay and production ending/history transition remain pending; game can stay
closed. The earlier provisional B1 catalogue-order closure is superseded by
lifecycle_review_r3.json, which starts from the actual prefab owner.

Latest2026-10-10T14:57:32Z: S1.1 departure cleanup USER+LOG PASS on completed
saved route: waits1/1, native deactivation acknowledgements1/1, join1,
ownerFinished1/stage4; reward1/1 and Succeeded journal unchanged. No immediate
additional live test; user may save separate test slot and close game. Visual
actor absence, stage4 post-repair save/reload and other routes remain unverified.
Next: reviewed restoration batches using shared native-owner patterns, without
assuming all128 jobs are restored.126 other adapters/all completed replay and
production ending/history transition tests remain pending. Evidence:
research/side_job_cleanup_s1_1/live_result_20261010.json.

Latest2026-10-10T14:51:31Z: distant departure test leaves Only Pain owner release
at0 despite completed journal/reward1/1 and757m departure; proximity alone did
not explain it. S1.1 guarded cleanup fallback installed,3 backed-up replacements,
1827 protected files unchanged. Original cleanup actions/conditions retained;
completed owned police-left route can arm alternative outside-trigger branch
after five safe samples>=500m. No reward/restart/journal/fact resets, no forced
finished marker. Branch acknowledgements added. Offline compile/graph/guard/
deployment PASS; cold-load existing completed save needed to prove active waits
adopt revised definitions. Do not replay. J1 empty-title visual USER-pass. Broader
126 adapters/all replay remain pending; full-ending alpha not ready.

Latest2026-10-09T19:49:48Z: Only Pain encounter, native dialogue/completion and
user save/reload passed; exact cash/XP, other routes and distant owner cleanup
remain unverified. Nearby ownerFinished0 is consistent with native departure
gates; do not force teardown. Journal Label J1 installed as one UI-only script:
empty post-Tower page uses localized Journal instead of authored sample title,
selected quests retain native titles. Full compile and scoped install/recovery
checks pass; visual check requires next cold launch. No quest/history/profile
changes.126 further activity adapters and all completed replay remain pending;
combined ending alpha is not ready. See docs/gig_pilot_r1_check.md.

Latest2026-10-09T19:20:25Z: user verifies gig override restored Many Ways;
first representative SIDE JOB owner, Only Pain S1, implemented and installed.
4 additions+1 backed-up R3 dispatcher replacement,1777 protected files unchanged;
actual hashes/recovery preflight, full compilers/native graph/readback and guarded
models PASS, not engine proof. Fresh encounter only, no completed replay or
part-stage reset; native owner/scene/combat/cleanup retained. R3 now dispatches
G1 exact resume and S1 fresh,126 other adapters pending. Pre-ending source-audited
available-encounter proof is saved separately; old history cannot invent it.
Next: cold-launch disposable post-Tower save and run Only Pain fresh override;
test native encounter, completion/departure and separate save/reload. If admission
refuses, inspect rather than forcing facts. Combined ending alpha remains later,
after representative side-job pass and broader restoration. Existing character
profile/R11/bar deferral unchanged. See docs/gig_pilot_r1_check.md (S1 section).

Latest 2026-10-08: user accepts character nerf as complete for the current
milestone and chooses GIGS FIRST for Phase7 research. Installed restrictions
remain untouched; formal release regression is separate. Source research finds
Tower bulk gig-journal failure/POI hiding, root termination and replay-prone
fixer counters. Many Ways to Skin a Cat is the first CONDITIONAL candidate,
not restored; Playing for Keeps/Guinea Pigs have Johnny scenes, Empathy has
story/service overlap. Read research/gig_restoration/assessment.md. Research
only: no activity implementation, install, activation or save/story changes.

Latest 2026-10-08T19:46:28Z: second implant-focused profile implemented and
installed, preserving strict profile source. Body3/Relic/HP150/chrome/smart rules
remain;21 other-tree physical/dependency bans relaxed. Next live check: coldload
eligible strict save, confirm tower_implant_focused stage4 with unchanged points,
repurchase Lead and Steel if desired, test projectile blocking and reload.
Offline/fullcompile, guarded save-transition models and backed-up installation
PASS; no new engine-effect claim. Refunds stay irreversible; no automatic build
restoration. Bar NPC idles still deferred and other world work untouched.

Latest 2026-10-07T22:42:04Z: user's revised maxHP150 is implemented/installed
as HP R3.1. Existing eligible R3 profiles adopt the exact HP-only revision on
load without replaying refunds or enabling no-vitals saves. All other profile
rules unchanged. Offline and actual installation checks PASS; next live target
is HP150, including pool/buff/no-free-heal and reload checks. No new live pass.

Latest 2026-10-07T22:10:52Z: Phase6 strict modular profile R3 IMPLEMENTED AND
INSTALLED. HP100/no direct stamina override, Body3/Relic closure, cyberware
whitelist and expanded116-perk bans now have runtime adapters. Existing refunds
are not replayed; other74 use their own guarded native-sale journal. Offline
compilation/model/deployment checks and actual backed-up installation pass.
Next smallest step: activate FullNerf() on a disposable completed-Tower save,
verify stage4, exact point deltas, HP100 without healing, actual smart projectile
behavior, then cold reload/save isolation. See docs/restriction_profile_r3_check.md.
No live pass or percentage increase claimed. Bar NPC idles remain deferred;
acceptedR11 world behavior is unchanged.

Latest 2026-10-06T22:45:56Z: user confirms R11 Emmerick animation/rearm,
Rogue dialogue/glow and hologram removal USER-pass; no general stability or
cold-reload inference. Remaining bar NPC idle issues DEFERRED by user.
Phase6 restriction-profile RESEARCH is now the priority. First source audit
supports functional combat-implant restrictions, not capacity-only limits or
canonical HP/attribute numbers. Catalogue completion and transaction-safe,
per-save enforcement design precede implementation. Full Nerf choices remain
open. See research/restriction_profiles/assessment.md. No gameplay changes,
installation or percentage increase from this research.

Latest 2026-10-06T19:13:43Z: Phase4 R11 installed after user's R10 no-crash
trial and explicit next-fix/install request. Exact Emmerick player-scene veto
identified in trace; NPC-only movement + safe admission implemented. Reviewed
Rogue local dialogue/gold events restored; live appearance policy permanently
retired and ten hologram dancers retire-only, as now requested. Three backed-up
replacements,1307 other tracked files unchanged; compile/source/guard/migration/
packed-byte/fixture/actual hash+rollback checks PASS. Next smallest step: cold
disposable no-save leave/re-enter, continuous Emmerick step-aside, Rogue choices
and glow, empty tubes, then return; use R11 check. No live success or percentage
gain yet; crash corruption writer still unknown. R11 fallback retains retired
faces/dancers and R10 interaction quarantine. Earlier rollback instructions are
superseded for this installed archive. Preserve accepted density/Claire/Nix/
Zetatech and boothR6 resources; do not repeat their baseline tests.

Latest2026-10-06T18:50:56Z: Phase4 R10 SAFETY ISOLATION INSTALLED afterR9failed.
Userapproved prioritystability: livefaceuniqueness andRogueinteractionadapter
temporarilydisabled, NPCpresence/counts preserved. Newcrash identifiesordinary
crowdclothingattachmentcorruption, writerunknown. Emmerickdistancecandidate +
automaticgatediagnosticsinstalled;4backed-upreplacements/1290othersunchanged.
Offline/compile/hash/rollbackPASS; no liveproof orpercentagegain. Nextsmallest
step disposablecoldlaunch entrance+shortstabilityvisit perR10check; do not
advancefullrestoration/re-enableoptionalpaths beforeisolationresult. R10-only
rollback retainsface-suspension+diagnostics andrestorespreR8interactions.

Latest2026-10-06T14:35:03Z: Phase4 R9 INSTALLED after "fix and install it again".
Two backed-up replacements, game closed unsandboxed,1277 others unchanged.
Corrects confirmed Rogue native actor-index defect with full typed/packed
reference remap and regression tests. Emmerick sequential native gates and
quaternion-based anchor readiness + diagnostics installed; live result pending.
Accepted Claire/density/appearance/named/hologram/Zetatech/boothR6 resources
preserved. Next: docs/afterlife_interactions_r9_check.md focused disposable
visit, then separate stream/reload evidence. Safe rollback returns pre-R8 only.
No roadmap percentage gain; source/compile/install PASS is not engine proof.

Latest2026-10-06T05:43:42Z: Phase4 R8 LIVE FAIL + native crash. Entry phase/start
works for Emmerick, movement scene not observed. Rogue adapter's sparse player
actor index matches confirmed dump fault; offline checks missed engine indexing.
No progress gain. R8-only rollback recommended (not yet performed/authorized
this report turn), then correct actor/reference mapping and diagnose Emmerick
admission separately. See interactions_r8/live_failure_20261006.md; no relaunch
of unsafe R8 for additional traces. Preserve previously accepted fixes.

Latest2026-10-06T05:31:43Z: Phase4 Afterlife Interactions R8 INSTALLED on explicit
IMPLEMENT AND INSTALL request, game closed unsandboxed. Two backed-up archive/XL
replacements + one driver addition;1261 others unchanged. Offline exact-delta,
native structure, redscript compile, packed readback and install/rollback checks
PASS. Implements guarded Emmerick native entry step-aside/rearm and Rogue local
dialogue/gold-eye adapter, excludes phone routes and preserves Tower appearance.
Claire/density/appearance/Nix/hologram/Zetatech/boothR6 unchanged. Next focused
live approach/return check: docs/afterlife_interactions_r8_check.md. Visual
motion/dialogue/glow, private acquisition and reload still pending; no % gain.

Latest2026-10-06 follow-up: Phase4 Claire dialogue availability USER-pass.
Next identified interaction repairs: Emmerick native entry-triggered step-aside
(not R7 endpoint idle alone), Rogue local conversation owner+authored gold eye
effect, preserving private identities/2079 appearance and excluding phone/story
roots. Source audit verifies exact5-node Emmerick scene and Rogue local-entry
VFX; no new runtime build/install or percentage gain. All12 Afterlife hashes
unchanged. See interactions_r8/assessment.md; further scanner IDs not required.

Latest2026-10-06T04:52:24Z: Phase4 Emmerick R7 INSTALLED with game closed,
explicit user authorization, one backed-up archive replacement and1247 other
files unchanged. Exact source/payload checks + fixture rollback + actual installed
hash/rollback preflight PASS. Private entrance routine/transform now matches
observed vanilla entrance02, infinite12-gesture weighted idle; counts/identity/
phase label preserved. Next60–90s focused live check in afterlife_emmerick_r7_check.md.
No motion/return/reload pass or percentage gain; R2/R5/named/hologram/Zetatech/R6
remain intact. Baseline_r7 documents mixed16post/81pre samples and user-observed
pre-existing booth duplicates/empty tubes. Separate next work: reviewed local
Rogue dialogue/glow adapter, then evidence for Claire optional-choice parity;
do not reset history, replace Tower appearance or restart story/dialogue roots.

Latest2026-10-06T04:16:48Z: Phase4 Booth R6 INSTALLED after explicit approval.
Game closed, two backed-up replacements,1231 other files unchanged; installed
hashes/actual rollback preflight PASS. Next focused90s booth animation/alignment
check, then separate interruption/return/reload proof. No live pass or % gain.
R5 appearance/type and R2 density/named/hologram/Zetatech passes remain intact.
Use docs/afterlife_booth_r6_check.md; receipt under afterlife_world/booth_r6.

Latest2026-10-06: Phase4 R5 appearance/type USER-pass; no saved-reload inference.
Four-booth animation R6 BUILT/OFFLINE PASS, NOT INSTALLED. Evidence-backed finite
idle branches and~11s R3 startup delay addressed by private looping resources
and guarded exact-anchor admission. Three native random lists retained; fourth
pose remains quieter. Two-file backup/rollback fixture passes, game unchanged.
Next explicit install approval and unsandboxed closed-game check, then focused
90s booth observation via docs/afterlife_booth_r6_check.md. R3 live failure remains
open; preserve accepted crowd density/R5/named/hologram/Zetatech. No % gain.

Latest2026-10-05T19:47Z: Phase4 Afterlife Faces R5 INSTALLED after explicit
implementation/install approval. Two additive scripts; game closed,1216 other
files unchanged, hash/rollback preflight PASS. Four random ordinary entries
get unique source face reservations with unchanged quotas/roles; different
faces/shared outfits. Supported post-attachment correction, NOT proven
first-render uniqueness. Source/compile/lifecycle-model/deployment checks PASS;
live readback/render/return/save-reload PENDING. See faces_r5/assessment.md and
docs/afterlife_faces_r5_check.md. Preserve accepted R2/named/hologram/Zetatech;
four fixed booth skins/routines excluded, R4 deferred and R3 failure open.
No percentage gain. Supersedes the unimplemented status immediately below.

Latest2026-10-05: Phase4 appearance target now explicitly requires different
faces under random selection; shared outfits accepted. Native randomized
distribution verified; name uniqueness is insufficient. Source face capacity
for four ordinary pools matches50/50 allocations, not people/visual/live proof.
Pre-spawn face reservation/lifecycle integration remains unimplemented; R4
fixed-four deferred. Preserve quantities/roles/accepted passes and open R3
routine failure. See appearance_rules/assessment.md; no percentage gain.

Latest2026-10-05 scope correction: Phase4 Afterlife appearance work targets
native probabilistic selection/distribution rules, not per-NPC skin overrides.
Fixed-four R4 candidate DEFERRED/not installed. Preserve record/slot mix and
R2 density; establish actual pools/fallbacks/distribution before changing rules.
Random repetition alone is not duplicate-entity proof. R3 routine failure remains
open; no percentage gain. See appearance_r4/assessment.md.

Latest2026-10-05 follow-up: Phase4 Afterlife R3 LIVE FAIL: two seated/one standing/
one on table, then two visually disappear after walking toward a wall. Objects
still resolve; actual despawn unproven. Confirmed merc_04/scene1 appearance
merc_01 instead of authored merc_04. Four-entry appearance-only R4 candidate
and corrected read-only diagnostic OFFLINE PASS, NOT INSTALLED; routine defect
and second photographed repeated-appearance group unresolved. Need that group's
Inspector identity before widening repair. See appearance_r4/assessment.md.
All installed Afterlife files unchanged; preserve R2 density and prior passes.
No percentage gain. Supersedes R3 live-pending notes below.

Latest2026-10-05T15:25Z: Phase4 Afterlife R3 INSTALLED after explicit approval,
game closed: four additions, zero replacements,1180 others unchanged; hashes
and actual rollback preflight PASS. Next focused booth-routine and bar-wide
behavior check, not a repeat of accepted density/holograms/Zetatech. All live
R3 animation/coverage/return/reload proof pending; no percentage gain.

Latest2026-10-05: Phase4 Afterlife R3 four-booth-routine candidate implemented,
offline/source/guard/stream/redscript/Lua and workspace deployment tests PASS;
NOT INSTALLED/live-tested. Reuses four original actors, no spawn/density/scene
changes; preserves accepted R2/holograms/Rogue/Nix/Zetatech. Bar-wide read-only
audit prepared; additional idle defects and full live coverage remain unknown.
Next install approval and closed-game preflight, then focused booth + bar-walk
check via docs/afterlife_idles_r3_check.md. No percentage gain.

Latest2026-10-05: Phase4 Afterlife R2 crowd density now USER-pass. Preserve
this and the hologram visibility/Rogue/Nix/Zetatech successes; do not repeat
basic crowd-density testing. Remaining demonstrated Afterlife defect: four
scene-owned booth actors without their routines. Repeat-return, fast-travel,
save/reload and natural-ending validation remain unreported. No percentage gain.

Latest2026-10-05T14:49Z: Phase4 Afterlife population R2 INSTALLED after user
approval, game closed. Two backed-up replacements,1164 other files unchanged;
hashes/actual rollback preflight PASS. Live migration/density/return/reload
pending via docs/afterlife_population_r2_check.md. Require full departure
barrier before judging restored crowd. Four booth routines remain separate;
preserve hologram visibility/Rogue/Nix/Zetatech passes. No percentage gain.
Receipt: research/afterlife_world/population_r2/install_receipt.json.

2026-10-05 live follow-up: user passes hologram visibility, while crowding and
four idle booth actors remain. Installed hashes prove this is still R1; R2
has not been deployed or live-tested. Three sampled vanilla hologram NPCs are
in workspots; scanner-name parity is unverified, not a confirmed new defect.
Next remains approved R2 install + migration/matched population validation,
with four booth routines a separate unresolved owner issue. Preserve new
hologram pass, Rogue/Nix and Zetatech. No percentage gain; live_r1_result.md.

Latest2026-10-05: Phase4 Afterlife population R2 candidate implemented;
offline source/graph/lifecycle and workspace-fixture deployment/rollback PASS.
NOT INSTALLED: real preflight only, two proposed replacements,1150 others
protected. Original q005 ordinary roster20/66 allocations +5 extras reused;
71 allocations/70 native workspots, unchanged type/appearance/budget rules.
R1 wrong-cohort reacquisition disabled with saved graph IDs intact. New guarded
four-trigger local controller and departure/stream barrier; actual retirement,
visible density, appearance distribution and engine reload still pending.
Preserve Rogue/Nix/Emmerick/dancers and Zetatech. Await install approval, then
matched baseline/entry/exit/fast-travel/reload route in
docs/afterlife_population_r2_check.md. Evidence:
research/afterlife_world/population_r2/assessment.md and tests.json. No individual
booth-actor fix, missing-hologram success claim or roadmap percentage increase.

Latest2026-10-04: Phase4 Afterlife population-rule research takes priority over
individual NPC fixes. R1 wrong-cohort selection CONFIRMED: q103_done1 in both
save samples selects vanilla q005 ordinary66-slot roster plus5 direct extras,
not R1's q103-derived78 slots. Only q103 originals are retired; q005 originals
were not accounted for. Original q103 active count0 does not prove no overlap.
Actual live headcount/density and appearance distribution remain unmeasured.
Research/source assertions reproduce R1 policy FAIL; no R2 build/install or
runtime change. Read research/afterlife_world/assessment.md population-rules
section and machine audit. Next correct-cohort/exclusive ownership design and
matched baseline/stream/reload validation, preserving named services, Tower
and Zetatech. Earlier mercenary four-to-one late-game inference withdrawn.
No percentage change or claim of always-correct spawning yet.

Current2026-10-04: Phase4 Afterlife R1 partial live result: Rogue and Nix
presence USER-pass; preserve. Remaining: four frozen old booth mercenaries,
visually missing holograms despite all10 active entry flags, and suspected
excess crowd. The26 private crowd entries represent up to78 patrons. Verify
original entry activation before concluding duplication; earlier mercenary
four-to-one inference is superseded by the owner audit above. No scene replay,
blind global population reset or game-file installation while game is running.
See research/afterlife_world/live_r1_result.md. No completeness gain; Trade,
save/reload, streaming and fresh-ending validation remain separate.

Current2026-10-05T00:12Z: Afterlife R1 installed as the active Phase 4 check.
Four additions/two S4-Nix replacements; 1130 other tracked files preserved.
Ten original holograms, 26 ordinary crowd entries with source routines,
Emmerick guard stance, ambient 2079 Rogue booth idle, and Nix's extra stale
activity guard corrected (15 other S4 payloads unchanged). Private population
is 28 entries/up to 80 actors; no full roots or old quest dialogue restored.
Tiny Mike and four older scene-owned mercenaries remain outside this cohort.
Offline/source/374-node/readback/runtime and six-file rollback checks pass;
live behavior and save/load remain pending, no percentage increase. Next is
only docs/afterlife_r1_check.md; receipt/evidence in research/afterlife_world.
Do not repeat accepted Zetatech, Claire or mirror basic checks.

Current2026-10-04: Zetatech R12 local population/idle smoke USER-pass; no
inferred cold reload/ending/stability result or percentage change. User's
next Phase 4 priority is Afterlife: hologram dancers, Rogue, Emmerick/patron
behavior and missing Nix. Nix's explicit absence supersedes the earlier
aggregate S4 smoke interpretation. Compare original owners with installed
resources and observed facts; restore bounded local behavior, not story
roots. See research/afterlife_world for current repair evidence and receipt.

Current2026-09-28T21:41Z: R11 three doors/four street NPCs USER-pass. R12
installed for requested idle routines and remaining local residents:27 added
ordinary street entries (31total), private guard/clerk with stance/tablet
workspots, interruptible smoking for the existing private Terry.30spots, one
exact wheelchair and five documented independent-animation substitutions.
Three additions/one diagnostic replacement,1091 other files protected; all
R11 core and R8 unchanged. Offline212node/52guard/31stream/29race/readback/
compiler/Lua and recoverable rollback checks pass. Live animation/placement/
handoff/reload still pending; no completion increase. Use only the focused
docs/zetatech_population_r12_check.md route; do not repeat accepted door or
basic four-NPC checks. No ending cast/scene replay/story or save writes.

Current2026-09-28T20:49Z: R10 failed live. The guard is an indoor actor,
not the requested street population; missing staff means the upstairs clerk.
R11 is installed: private exact front/inner interactive doors, three independent
door readiness branches including the restored original rear unlock, indoor
clerk/guard activation, four private street entries/workspots, and a separate
private Terry clone. Two files replaced, three added;1071 others and R8
unchanged. Offline source/guard/128-stream-case/30-payload/runtime checks and
five-file rollback preflight pass. Door interaction, staff/ambient animation,
Terry damage/AI, streaming and reload remain live-pending. Terry death is not
persistent across reloads in this version. No scene replay, story/save writes
or percentage increase. Use `docs/misty_viktor_access_r11_check.md` and receipt
`research/misty_viktor_world/access_r11_install_receipt.json`; this supersedes
the R9/R10 status/routes and erroneous outdoor-guard claims below.

Current2026-09-28T20:02Z: R9 failed live despite request counters: both user-
located doors remained open/noninteractive and the indoor clerk was static.
R10 replaces only that installed archive. Its independent stream-aware branch
targets the front door and corrected inner q307_zetatech_doors_01, waiting for
both before close+unlock and rearming on unload. Migration deactivates the R9
clerk; only vanilla post-Viktor q307_alley_extra_01 is restored at the street-
front return workspot. Offline50-node/45-guard/four-loading-state tests pass;
1039 installed files and R8 are preserved. Live door and outdoor-NPC behavior
remain pending through `docs/misty_viktor_access_r10_check.md`; no completion
increase. Installed archive hash: 5DCEE0D2AA19C80A9A425A3D09D259B900C3BBCA3BE1AE67E5DDE7B0A0AA6FA8.

Current2026-09-28T19:04Z: user reports the R8 play test passed; record the
automatic blue-neon/police-light smoke result as USER-pass without extending it
to fresh natural-ending, pre-Tower baseline, save/reload or long-session proof.
R9 Zetatech access/receptionist follow-up installed as one R7 archive
replacement, preserving the XL, all five R8 additions and1026 other project
files. Exact front and surviving inner/rear vanilla doors now receive guarded
close+unlock restoration; only q307_zetatech_clerk is reactivated at the
authored post-scene idle workspot, with exact-entry release and no scene or
other q307 cast. Offline39-node/45-guard/92-loading/archive/scope tests pass;
live door auto-close/use, single-clerk idle, streaming and reload pending via
`docs/misty_viktor_access_r9_check.md`. No completeness increase yet.
The final migration-safe hash is DB2EEDF0C67ACC7762BCC73F45EF2382458CE0385E51B34B0A79F04E4CC7B437;
a private AccessRevision mismatch causes one guarded release/reacquire on an
already-active R7 save so no manual opt-out is required.

Current2026-09-28T17:32Z: user requires automatic post-Tower startup of all
completed fixes. R8 automatic lighting/startup candidate installed: 12 exact
aliases on the original sector, five original Tower blue/Cold clones in a
private default-off block, auto neon and R7-gated police phases, plus guarded
redscript startup for R7 street, validated journal reconciler and clock
unpause. S1's three files were moved to recoverable backup; five new files
installed,1009 others preserved. Offline tests pass; original alias/mesh
visibility and natural-ending/startup/reload are live-pending, so residual
glow/pink neon and automatic integration remain UNRESOLVED, not WORKING.
Use one no-save route `docs/misty_viktor_lighting_r8_auto_check.md`, then
save/reload only after visual pass. No completeness gain; see assessment and
receipt in research/misty_viktor_world.

Current2026-09-28T16:48Z: S1 original-police-light alias-only candidate
installed idle opt-in as three additive files. Exact decoded sector delta,
33-node native graph simulation, packed byte readback, Lua syntax, preflight
and postinstall hashes pass; zero replacements,992 protected files unchanged.
This is not the requested seven-police-light/pink-to-blue neon repair yet:
original alias resolution, pre-Tower baseline, natural-ending integrity,
visible Hide/Show, Stop, return and cold-load remain live-pending. Authored
Tower blue lights3113–3115 and Cold meshes3118–3119 are already known, so
the user need not search for blue IDs. Next one-site no-save test:
`docs/misty_viktor_original_lamp_s1_check.md`. No automatic activation or
completeness gain; see `research/misty_viktor_world/original_lamp_s1_assessment.md`.

Current2026-09-28: corrected one-light POC USER-visible Hide/Show pass;
65-row trace confirms native Ready and two Hide/three Show dispatches from
near the private 3m lamp. This proves private aliased static-light control,
not control of original zero-ref police lamps. Second trace has no Stop;
streaming/release/cold-load still unverified. No original lights altered,
automatic activation or completeness gain. See
`research/misty_viktor_world/light_poc_live_result.md`. Next: one exact-delta
singleton original-lamp alias POC with baseline/natural-ending checks, not a
seven-lamp or hotel-neon rollout.

Current2026-09-28: first one-light POC live attempt was inconclusive. User saw
no change in original police residue, but trace places V no closer than9.66m
to the private 3m-radius lamp; HideRequests stayed0 after stream-out. One
private Show was dispatched, not visually validated. Stop recorded one release.
Read `research/misty_viktor_world/light_poc_live_result.md`; corrected same-site
test in `docs/misty_viktor_light_poc_check.md`. Original neon/police lamps
remain unchanged, no automatic activation or completeness gain.

Current2026-09-28T15:10:34Z: user approved and one-light opt-in installed as
three additive files. All new hashes and three R7 hashes verified,919
protected files unchanged,zero replacements. Offline tests pass; live
reference/visible Show-Hide/return/Stop remain pending via the one disposable
route `docs/misty_viktor_light_poc_check.md`. Original lights are unchanged;
no automatic activation or completeness gain. Earlier install-block notes
below are historical.

Current2026-09-28: user-approved one-private-light POC BUILT/OFFLINE-PASS,
NOT INSTALLED.31-node serial native controller, default-off private lamp,
45 negative guards/141 wait-invalidation routes/Lua5.1/exact3 payloads pass.
Installer ValidateOnly protected919 files/R7 unchanged. Auto-review blocked
the installation escalation before execution, requiring explicit install
approval beyond build authorization. No workaround, original lighting change,
game write or live pass. Read
`research/misty_viktor_world/light_poc_install_authorization.md`.
After approval+closed game, install additive3 files then use
`docs/misty_viktor_light_poc_check.md`. No repeated basic R7 tests.

Latest 2026-09-28: USER confirms R7 cement sacks, pallet/pallet jack and both
police trucks restored. Wall-gap report withdrawn as misremembered, not a
repaired wall. Preserve all R6/R7 successes; no repeated basic prop tests.
86-row R7 trace confirms acquisition and stable sampled Tower guards while
V is present; no Stop/release/reload proof. See
`research/misty_viktor_world/live_r7_result.md`. Current task: investigate
targeted conditional hotel-neon/police-lamp control; no new fix installed.
Investigation result: exact7 police lamps and5 pink/cyan counterpart pairs
identified. Source layout rejects exported Id as a target; generic native
ShowWorldNode path found, static-light response/individual aliases unproved.
Next proposed proof: one private static lamp, then mesh, before any original
alias-only patch. Read `research/misty_viktor_world/r8_lighting_targeted_control.md`.
Positive vanilla precedent found: Afterlife mq016 nodes790/792 individually
hide/show a confirmed static light with an authored reference; registration
of our currently unnamed targets remains the next proof, not an installed fix.
Earlier dated pending/next-step notes below are historical where superseded.

R7 installed idle opt-in 2026-09-28T14:08:51Z: two construction piles
(16 cement sacks, pallet, pallet jack) plus two native NCPD truck placements.
All18 R6 world resources byte-identical;30-node controller changes only
revision6->7. Exact source/readback,45 negative guards,92 loading cases and
Lua pass; three R6 targets backed up,902 other installed files unchanged.
No story/save/record edits or ending scenes. Trucks are full vehicles:
stationary state, incidental occupants, return/duplicates and Stop teardown
remain live-pending. See details_r7_assessment.md and install receipt.
Neon/police lights are IDENTIFIED BUT UNRESOLVED: broad WLC03 pair includes
remote geometry and q307_misty_rising FX; no blanket toggle or global recolor.
Terminal restored USER-confirmed; no basic R6 repeat. One combined new-detail
route: docs/misty_viktor_details_r7_check.md. No completeness increase.

R6 live2026-09-28: USER confirms candles gone, police props gone and local
pedestrian wall-crossing solved. Residual police glow remains.303-row trace
spans multiple save loads (including q307-active reference fixture); it shows
one initial acquisition/crowd request, not release/rearm/cold-load proof.
Bradbury terminal subsequently USER-confirmed restored. See live_r6_result.md.
New target references: images1–3 vanilla pre-completion,4–5 modded. Audit
missing cement/construction props at two supplied points, cyan hotel neon,
residual police glow and two parked trucks. Preserve working R6. No blanket
WLC_03_Default toggle: scope includes remote geometry. Game closed; R7 work
in preparation, not installed. No completeness increase or new NPC scope.

Current 2026-09-28: R5 also FAILED the visual check; Revision5/Enabled1/
Applied1/Acquires1 were observed, but candles, police dressing, wall gap and
NPC crossing remained. Stop was followed immediately by Inspect/Finish, so
release is unobserved. R6 installed idle opt-in at13:21:49Z, live pending:
exact local lighting V_Default267 -> Q307_VV270 placements, separate19-member
q001_holo_scene OFF, original Bradbury & Buran terminal/proxy ON, and one
private Tower alley crowd-null area with guarded load/unload readiness.
Exact vanilla Viktor wait-before-crowd-enable and native pointer-presence/
inverted-absence predicate support readiness.30 nodes/45 negative guards/
92 loading cases/Lua pass;16 existing world resources unchanged. Three R5
files backed up and replaced;888 other installed project files unchanged.
The wall gap remains unidentified: no guessed wall or navmesh patch. No
Terry/ending replay/story writes/automatic activation/completeness gain.
Read research/misty_viktor_world/repair_r6_assessment.md and live_r5_result.md.
Next combined route: docs/misty_viktor_repair_r6_check.md. Verify visual
changes, local crowd/re-entry and guarded release; no live pass yet.

R5 installed idle2026-09-28T04:23:49Z: R4 live test FAILED visually—candles,
police dressing, wall gap and NPC wall-crossing remain. Trace proves Revision4/
Enabled1/Applied1/Acquires1 at the sites; immediate Stop/Inspect did not
observe release. Source audit found R1–R4 private shell/street variants wrongly
assigned to always-on range0. R5 moves14 private sectors to empty default+
controlled range1 and updates two block descriptors, with all placement
payloads/graph guards unchanged. Offline exact delta/45 guards/Lua pass;
three R4 targets backed up,874 others preserved. Live behavior and original
Misty/alley variant states remain unknown. Read live_r4_result.md and
variants_r5_assessment.md. No completeness gain or wall/nav claim.
One combined disposable route: docs/misty_viktor_variants_r5_check.md.

R4 was installed2026-09-28T03:43:05Z and subsequently failed live visual checks: exact candle point maps to
vanilla `q307_hide_misty` (three candle nodes within0.43m); original q307
cleanup requests this 1,244-node interior variant OFF. Guarded R4 copies that
single OFF request after private shell activation and filters24 police-specific
placements from the R3 private street copy (including one now-empty sector).
Archive/XL/graph/45 guards/Lua delta pass. Three prior files backed up and
860 other installed project files preserved. Police dressing may
also have an original-world owner; wall gap and local NPC pathing remain
unresolved. Superseded by R5's structural range correction; do not repeat
the R4 route.
No automatic activation or completeness gain.

R3 first visual check2026-09-28: user can enter clinic, but reports a police
line, apparent wall gap and NPCs crossing a wall. Local [overlap audit](research/misty_viktor_world/overlap_audit.md)
traces 24 NCPD tape/sign/logo pieces to the private R3 copy; they are not
proved leftover 2077 assets. The original older alley bundle is mixed and
q307 requests it off; do not blanket-despawn it. Positions now recorded for
wall/scene owner mapping. R3 remains opt-in; no nav repair, Terry, full
visual pass or completeness gain. Next: narrow police-art filter, then
wall/collision and local crowd/path audit.

R3 installed idle2026-09-28T01:27Z: first passive Tower storefront/street
candidate, opt-in only. Original Zetatech logo plus788 filtered placements;
existing R2 interior/access behavior retained. Offline source/45 guards/Lua
pass; installed3 hashes verified,819 other project files preserved, rollback
saved. No NPCs/Terry, dynamic lights/ads/sounds, ending scene or story writes.
One docs/misty_viktor_street_r3_check.md visual/support/return check pending;
do not call this the full exterior or increase completeness. NPCs/Terry follow
separately after scene behavior is verified.

Scope update2026-09-27: user requests Tower storefront/local street appearance,
ambient street NPC replacement, plus Terry as a fightable named exception.
Read research/misty_viktor_world/street_restoration_plan.md and its source
inventories. Terry=thug01/key81616; original Invulnerable record must remain
untouched. Plan a guarded private clone, not the assault scene/other ending
cast. Selection/research only: no street/NPC candidate built or installed;
R2 unchanged, combat/death/cleanup unverified, no completeness increase.

R2 live2026-09-27: rear door opens(USER), old Misty sign/light strips absent
(screenshot);96-row native trace confirms one acquisition/access dispatch.
Finish near storefront without Stop: release/baseline/re-entry/reload unverified.
No repeated basic door/sign test. Full facade/display remains unaudited; no
automatic integration or completeness increase. See shop live_r2_result.md.

Latest2026-09-27: R1 Zetatech interior visible; user identifies upper-shop rear
door blocked and old exterior sign retained. R2 installed idle opt-in21:59:46Z:
exact existing rear-door unlock and native old-sign removal; R1 geometry/XL
unchanged,145 other files preserved, rollback retained. Manual opt-out restores
known Tower door/sign baseline only with ownership guards intact. Offline pass,
live access/facade/release pending. No completeness increase or ending replay.
Read research/misty_viktor_world/assessment.md and updated combined check.

Current2026-09-27: radio playback/visible memorial samples user-passed,90-row
trace retained with receiver/station changes and no sampled fact changes. No
repeat basic check; conditional memorial variants/all broadcasts/reload remain
separate. User selects Tower Zetatech/closed-Misty appearance preservation.
Geometry-only shop candidate installed idle opt-in19:19:03Z:842 inert placements,
no entities/cast/scenes/story writes,145 prior project files preserved. Native
private variant/controller and45 negative guards pass offline; actual floors,
doors/access and existing Viktor group remain live-pending. Read
[shop assessment](research/misty_viktor_world/assessment.md) and
[one combined check](docs/misty_viktor_world_check.md). No completeness gain.

User priority2026-09-27: focused radio-content scheduler/columbarium validation
before the local shop pass. Native candidates already installed; a separate
read-only CET probe was added, stableR6 archive/XL/logger/observer unchanged.
Original scheduling and34 saved-outcome display actions pass preservation checks;
unique world display group resolved. Audible/visible output remains UNRESOLVED
pending one combined check. No fact/save writes or completeness increase. See
[focused assessment](research/radio_memorial_validation/assessment.md) and
[test](docs/radio_memorial_check.md). Gig-radio/altar/coaster gestures remain deferred.

Restoration checklist consolidated2026-09-27:
[current status index](research/restoration_checklist.md) separates WORKING,
INTENTIONALLY GATED, UNRESOLVED and DEFERRED with deployment, runtime evidence
and remaining limits kept distinct. Vanilla2.31 exports/runtime sources and
the online wiki roster were cross-checked; no game files/saves/facts changed.
Manual journal repair/cold-load passed; automatic integration remains open.
Next active gameplay work: Misty/Viktor local geometry/access/presentation,
then affected ambient NPC behavior. No new basic mirror/vendor test or
completeness increase from documentation. Historical assessments remain evidence.

User confirmation2026-09-27: journal cleanup cold-load passed. Manual repair
and persistence are accepted for the tested fixture; no repeat basic test.
Next active work is whitelist/service-matrix consolidation, followed by local
Misty/Viktor shop world/access and ambient NPC behavior. Automatic journal
integration remains production work, not an installed feature. This supersedes
historical cold-reload-pending and journal-first instructions below.

Tower journal live update2026-09-27: manual repair user-passed; durable logs
confirm both phases and root Active->Succeeded, all88 entries resolved, no
Active progress and no audited facts/other quest-root changes. Latest read-only
check remains Succeeded with zero repair requests. Cold-reload provenance awaits
confirmation; automatic integration remains pending. See
research/tower_journal_cleanup/live_result.md. No repeated basic repair test
or ending replay; historical runtime-pending notes below are superseded only
for the verified manual operation.

Tower journal candidate installed idle2026-09-27T01:09:21Z: exact88-entry
hierarchy audit,23 progress entries eligible only when Active, native state
completion bottom-up and exact-Tower ancestry untracking. Two additive files
preserve686 prior files; no quest fact/save/archive changes. Compiler,36 negative
guard cases and ten bridge cases pass. One current-save repair + new disposable
save/cold reload check remains required in docs/tower_journal_cleanup_check.md.
Automatic integration and Phase4F completion remain pending; no estimate increase.

Current next task (2026-09-27): Phase4F, finish q307 journal/history and tracking
cleanup. Earlier live repair completed only `05_take_walk`; its parent phase
and `q307_tomorrow` quest remained Active. Establish the current fixture state,
then finish the exact hierarchy after Tower completion, retain completed
history, and clear obsolete Tower tracking. Preserve Tower/2079 facts and
unrelated quests. Completion/reload and production integration remain open.
The current recommended priority list at the end supersedes older next-task
instructions in dated development notes. No ending replay requested.

Remaining interaction work deferred by user (2026-09-27): revisit housing and
relationship-home services, fortune-telling, shooting range, altar actions,
and gig-radio coordination when activity/quest work begins. Preserve existing
research and housing design; these unresolved areas remain deferred rather
than restored or intentionally gated. No installation or completeness change.

Coaster gesture deferred by user (2026-09-27): suspend gesture research/tests
until requested again. Current ride/exit and rollback retained; arm animation
remains incomplete. No deployment or completeness change from this decision.

Coaster offline follow-up (2026-09-27): gesture still unresolved; no installed
change or completeness increase. Listener creation/queue consumer and actual
scene-to-player animation request remain unproved. The traced player action
registers a tier request, not the clip. Original cinematic crash's invalid
resource handle has no identified writer; restoring it is not justified.
Keep crash-freeR6 andR5 rollback, no unchanged manual ride. See
research/b0_world_interactions/coaster_animation_audit/offline_followup.md.

Coaster revision6 live (2026-09-27T00:13–00:16Z): still no arms, no crash,
normal Exit/walking; trace hands5/5 and Return1. Direct clip targeting alone
failed. Correct mode8192, real queue self-test and12 active requests still
produce0 native callbacks. Further identical testing is not justified.
Original player animation/resource binding needs offline investigation;
ride/exit retained, complete restoration still pending. No percentage increase.

Coaster revision6 installed (2026-09-26,23:51:08Z): two entryId2->5 values
target cheer clips directly; ride/exit and nine other payloads unchanged.
Observer2 waits for active actor record, verifies native mode8192 and genuine
callback counts; prior REGISTERED was not acknowledgement.668 files preserved
with stable revision5 backup. Offline checks pass; next single combined visual/
diagnostic check docs/coaster_direct_entry_check.md. No live repair or increased
completeness claimed. Current evidence: coaster_direct_entry assessment/receipt.

Coaster callback probe live result (2026-09-26): five arm requests/starts and
normal Return; gate restored0, arm motion still absent. Observer reports
REGISTERED but zero events across178 rows (also no mount/exit callbacks).
Cannot distinguish played/skipped/missing; instrumentation needs investigation
before more manual testing. Native revision5 unchanged, no completeness gain.

Coaster animation observer installed (2026-09-26,23:15:55Z): one read-only
callback listener and logger update, native revision5 unchanged;656 other
tracked files preserved. Offline compiler/Lua lifecycle checks pass. One
diagnostic ride in docs/coaster_animation_trace.md will distinguish native
played/skipped/missing clips. Callback delivery remains unverified; this is
not a visual fix, restoration completion, or a request to repeat basic tests.

Coaster revision5 live follow-up (2026-09-26): SIX gesture requests/starts,
one normal Return and free movement; user confirms no crash but no arm motion.
Ride/normal Exit pass for this session, gesture remains failed. Requests2 is
automatic rearm, not two rides. Preserve revision5 stable ride as rollback;
see coaster_repeat_gesture/assessment.md. No repeat/reload or completeness claim.

Coaster revision5 (2026-09-26): revision4 first Raise arms acknowledged1/1 but
silent; second press crashed during ride. Dump proves node559 missing Success0
socket, causing one-past-table read. Restore empty Success0 on558/559 and set
gesture idle mode0; exact delta verified. Idle flag is a playback hypothesis
with native NPC action precedent, still player-live-unverified. Consult
coaster_repeat_gesture assessment/evidence/receipt. One ride/two separate arm
actions/normal Exit remains pending; no completeness increase. Keep prior
V-only lipsync fix and other services. Do not retest revision4.
Revision5 installed22:09:37Z: only coaster.scene changed, nine other native
payloads/registration unchanged,640 tracked files preserved with backup.
Offline150 graphs/128 guards/callback coverage/Lua51 pass; live remains pending.

Coaster Exit failure (2026-09-26): revision3 reaches Finished1/workspot=false
but crashes before Return (Requests1/Returns0). Minidump verifies V lipsync
index6 versus live table count1, not an actor-index hole. Revision4 combines
V-only lipsync rebasing6->0 with the two arm-action input corrections; the
arm-only build below was never installed. Exact scene-delta and graph/guard
checks pass. Read coaster_hands_binding assessment/evidence/receipt and
docs/world_interactions_check.md. No live fix/completeness claim; one ride,
one Raise arms and normal Exit remains required. Do not retest revision3.
Combined revision4 installed21:19:59Z: only coaster.scene changed, nine other
native payloads/registration unchanged,626 tracked files preserved with rollback.
Offline150 graphs/128 guards/Lua51 pass; no saves modified or live pass claimed.

Historical arm-only follow-up (superseded 2026-09-26): revision3 prompt accepts presses but user
reports no gesture; log shows HandsRequests4/HandsStarted0. Found exact socket
defect: randomizer561 still sends old section input0 (now CutDestination)
instead of quest-action In1 at558/559. Revision4 workspace build changes only
these two stamps. Full-scene exact-delta regression passes; installation waits
for game closed. Read coaster_hands_binding/assessment.md. No live fix or
completion increase; original crash-free full ride/normal Exit unconfirmed.

Coaster crash follow-up (2026-09-26): revision2 reached a moving mounted ride,
then user confirms crash after Hands up. Dump0x1cf71f differs from the earlier
Streetkid actor-index fault; exact engine cause unproven. Revision3 installed
21:01:35Z replaces the two optional cinematic cheer overlays with native
mounted-seat workspot gestures; optional shout omitted. Scene plus two private
workspots change, seven other native resources/registration byte-identical,
612 other files preserved. Offline checks pass; ONE ride/Hands up/normal Exit
check pending, no completeness increase. Read coaster_crash assessment/receipt
and docs/world_interactions_check.md before testing. Do not run revision2 again.

Coaster repair (2026-09-26): revision1 live prompt failed even with the user's
temporary gate1 (Registered1/Requests1/Returns0, scene=true). Revision2 installed
20:39:47Z restores the vanilla Activate-cart and hide-broken-clue startup actions
once per owner acquisition; seven other native resources are byte-identical,
registration unchanged,598 other files preserved.150 graph/128 guard/Lua51 and
exact two-action delta checks pass. No earned/story fact forced by production.
Live repair pending; see research/b0_world_interactions/coaster_fix/assessment.md
and receipt. No completeness increase or whole-table completion claim.

World-interaction batch (2026-09-26): three automatic native candidates installed
18:23:33Z: radio scheduling with one-time ending-gate repair, earned repeatable
V/cart-only coaster, and saved-outcome memorial displays without Johnny spawn.
Three additions preserve582 prior files.150 reciprocal graphs/128 negative
guards/dense cast/exact payload/Lua51 checks pass. Live candidate behavior is
pending; use docs/world_interactions_check.md for one combined disposable route.
This is PARTIAL fulfilment of the whole interaction-table request. Remaining:
paid fortune binding/quest-route isolation, disconnected range activation,
actual altar action, compatible gig-radio owners, housing entitlement/1.5x
reacquisition and relationship-safe non-mirror utility adapters. No ownership
or romance reset, root restart, new production polling or completeness increase.
Authoritative evidence: research/b0_world_interactions/batch/assessment.md.

Dancing result (2026-09-26): user reports all tests passed. Durable trace supports
Riot2 requests/2 returns,7th Hell3/3, with idle V after exits. Empathy/Totentanz
availability0 remained gated. Vanilla exits via movement, not a Stop choice.
Available-site action/exit/re-entry pass; cold reload/interruption unverified.
Do not repeat the corrected basic dancing check without a regression.

Club dancing (2026-09-26): four automatic guarded candidates installed17:36:51Z
for Riot/Empathy/7th Hell/Totentanz; three additive files preserve549 previous
tracked files. Original full scenes, local availability and native loops stay;
unconditional local enable writers replaced by private registration facts.
Atlantis is q108 memory staging and excluded. Offline exact-delta/actor/cleanup,
176 negative guards and Lua51 observer checks pass; live available-site actions
and repeat now passed above; reload/interruption pending. No estimate change.
Eight other-family owner extracts and five direct dependencies are recorded in
research/b0_world_interactions/restoration_plan.md for future coordinated
adapters. Rollercoaster/fortune-teller contain Johnny; radio has separate media
and gig owners. Do not blanket-start these phases or treat them as build-ready.

Lizzie's mirror (2026-09-26): deferred at user request after physical surface
could not be located. Native trigger statically found in the club open-world
sector; device/scene owner and live behavior remain unresolved. ID9 is not
counted as restored. See research/b0_lizzies_mirror/assessment.md; no further
manual search currently requested.

Mirror sample result (2026-09-26): user reports the five-site Randy/Shady/
Peralez/Police lab/Charter Hill route worked as expected (IDs4/12/14/15/37).
These are user-reported live sample passes; reload/interruption and durable
trace coverage remain unverified. Lizzie's candidate surface found near its
security room; owner identification pending. No completeness estimate change.

H10 TV live result (2026-09-26): user confirms seated picture and sound after
the native media-owner patch; Stand turns TV off as in the vanilla exit route.
Normal playback user-passed. Explicit multi-channel, save/reload, durable
scheduler trace and long-session stability remain unverified. See
research/b0_tv_media/assessment.md. No overall completeness estimate increase.

TV playback follow-up (2026-09-26): media candidate installed16:33:49Z,508 prior
files preserved. Flag repair restored channel choices only;
user still reports black/silent TV. Media-only native owner candidate built,
six original vanilla channel phases and #tv_content audio/display prefab behind
post-Tower guards. No media/story root restart or new tv_on writer. Offline
payload/graph/42-negative-guard audit passes; live playback pending. See
research/b0_tv_media/assessment.md and its install receipt. No completion bump.

H10 TV follow-up (2026-09-26): repair installed16:16Z, two additive files,493
prior files preserved. User found black/silent TV with Turn off prompt;
live tv_on=0, tv_apartment=1, H10 Active1/Interrupted0. Prior broad H10 success
does not prove current playback. One-time guarded post-handoff tv_on repair
built; no root/scene restart, periodic reassertion or ending-resource change.
Offline tests pass, live picture/audio pending. Installation authority and scope:
`research/b0_tv_restore/assessment.md` and its install_receipt.json.

Mirror scope update (2026-09-26): four candidates installed at15:45:45Z, two
additive files,478 prior files preserved. Keep Streetkid revisit. Restore companion-home
mirrors to original local behavior NOW; building access/relationship-home policy
remains later housing work. Four additive candidates built for new nomad camp,
Judy, Joss/River and Kerry; original gates/scenes retained, camp wardrobe
handshake audited and preserved. Offline exact-payload/graph tests pass; see
`research/b0_relationship_mirrors/assessment.md` and its installation receipt.
Installed:40/44 controller candidates, Lizzie9 unresolved, ending-only
16/17/18 excluded. Tower-hospital mirror excluded; rental/property mirrors
deferred to Phase5. Counts are not live completeness; no estimate increase.

Latest world-mirror rollout (2026-09-26): Red Dirt automatic/rearm is user-passed
and logged2 request/return cycles without interruption. Eight further guarded
automatic candidates are installed: Randy trailer, old nomad camp, shady ripper,
Peralez penthouse, police lab, Konpeki room, BD studio, sts_wbr_hil_01.476 prior
files preserved. All vanilla scene actions/leaf edges retained; no doors,
story roots or relationship facts restored. BD studio retains vanilla one-shot
behavior. No CET arm and no new polling. Offline tests pass, new-site live
coverage pending. Controller coverage is36/44 installed candidates, NOT36 live
passes or all world mirrors. Eight deferred plus separate apartment owners
remain: see `research/b0_remaining_mirrors/assessment.md`. Do not force their
gates or count unresolved owners as intentionally disabled. No estimate bump.

Latest Red Dirt step (2026-09-26): automatic native bootstrap installed with
460 prior files preserved. It sets only the existing C5 enable permission;
native owner, scene, identities, repeat loop and all quest guards are unchanged.
No new polling or duplicate prefab. Manual CET helper retired to read-only,
with rollback backup. Offline checks pass; automatic/repeat/reload observation
pending. See `research/b0_red_dirt_auto/assessment.md` and
`docs/red_dirt_auto_check.md`. This supersedes opt-in-only status below.

Red Dirt C5 follow-up (2026-09-26): user reports tests passed. Revision1 helper
was used; trace proves one native request/return, no interruption and clean
Stop with idle V. Repeat native re-entry/cold reload not independently proven.
Still opt-in; revision2 remote-arm helper remains uninstalled. See
`research/b0_general_mirrors_devices/assessment.md`. No completeness bump.

Latest Streetkid step (2026-09-26): revision4 visual/action test passed by user
report and logged completion. Automatic repeatable candidate installed with
403 other files preserved: redscript permission, native one-second rearm and
unused-prompt departure. Actions unchanged, CET now read-only. Fresh native
identity avoids old one-shot checkpoints; interruptions remain fail-closed.
Automatic/repeat use is now user-reported working; reload remains unverified: see `docs/streetkid_auto_check.md` and
`research/b0_streetkid_auto/assessment.md`. No completeness estimate increase.

Next device: Red Dirt C5 single-site opt-in. Baseline reports no interaction
and the observed local disable gates are0. Native entry preserves all Tower
guards, the exact sq011 trailing-space gate and fail-closed interruption.
See `docs/red_dirt_c5_test.md`; installation is tracked separately by
`research/b0_mirror_rollout/validation_c5_red_dirt/install_receipt.json`.
Physical action/re-entry validation remains pending. No other mirrors expanded.
C5 is installed idle (three additions, 431 existing files hash-preserved).

Vendor status rule (2026-09-25): a vendor is **restored** when its service works
when available, or when it is intentionally disabled by the original quest
facts on the tested save. The latter includes quest, unlock, death and refusal
outcomes; do not force those facts to open a shop. Apply this rule to every
vendor, not just Pepe. Unknown owners and untested behavior are tracked
separately from restored status.

Current Phase 4 step (2026-09-25): **S4 built and offline-validated for Nix,
Yoko, Mateo, Fingers, Viktor, Karim, Ronald and Bill**. Eight isolated automatic
service candidates retain original/earned availability, death/refusal and
stock state; mod-owned scenes exclude incompatible quest/reward/Johnny paths.
No original resources or prior 95 files are replaced. Installation is tracked
by the S4 receipt; the user reports the eight-site teleport check worked as
expected (smoke pass; detailed return/reload coverage unspecified). Viktor uses the
ordinary service actor, not a newly implemented 2079 presentation. Future quest
handover remains explicit work, not a proven generic feature. This supersedes
the eight-vendor unimplemented list below. [Scope/evidence](research/b0_story_eight/assessment.md),
[one combined check](docs/b0_story_eight_check.md).

S4 installation completed with the game closed: four new files, all 95 prior
files unchanged (99 total). User-reported smoke validation passed; durable-log
review and explicit return/reload coverage remain unverified for S4.

S3 follow-up: Fred/Cassius/Charles are user-reported working. Pepe's gate is 0,
mq040_active=1 and mq040_done=0; leave his quest-reserved service disabled. These
facts do not prove the quest graph is still executing. No forced unlock.

Latest Phase 4 result (2026-09-25): **S3 installed automatically for Fred,
Cassius, Pepe and Charles**, four additions with all 91 prior files unchanged.
Two mod-owned service scenes exclude Fred's fight-initiation and Charles's gig
progression branches; original quest scenes remain intact. Cassius/Pepe retain
full scenes and native ownership. Exact graph/scene checks, 60 negative guard
cases, combined 13-script compile, Lua51 logging and installer fixture pass;
live service/return/reload and future quest concurrency are not yet verified.
Zane is user-reported working; lease/reload is not thereby proven. The request
to restore **all** story-linked vendors remains partially fulfilled: Nix, Yoko,
Mateo, Fingers, Viktor, Karim, Ronald and Bill remain excluded for specific
unresolved quest/actor/service dependencies. Newly extracted Karim/Bill/Ronald
resources confirm mixed progression/reward/message machinery. See
[batch and blockers](research/b0_story_services/assessment.md) and
[one combined route](docs/b0_story_services_check.md). This supersedes pending
Zane-service status and remaining-vendor lists in historical entries below.

Updated from `Tower_Continued_Updated_Roadmap.md` on 2026-09-23.

Claire compatibility audit (2026-09-25): existing restoration retains vanilla sq024 availability and actor-phase coordination. Garage Reactivate precedes default-off, so do not transplant a generic despawn handoff. No installed change needed on current evidence; quest coexistence remains live-unverified. Future adapters must avoid a second default-dialogue owner and preserve authored switch order. [Audit](research/b0_claire/quest_compatibility.md).

Latest Phase 4 step (2026-09-25): **S2 Zane/Jinguji automatic service candidate installed**, first mixed-story adapter toward future quest coexistence. Mod-owned scene redirects only the `mq030_zane_met` write to a service fact; full unique dialogue, Trade, wardrobe and earned discount routing remain. Original mq030 resources are untouched. A cooperative QuestOwns/Released handshake blocks new service activations and waits for native departure before release. Future quests must explicitly honor it; actual quest handover/save-load are not proven. Graph/scene/compile/Lua/installer checks pass; four additions preserve all 87 prior files. Next: [one combined service/lease/return check](docs/b0_story_zane_check.md), [scope and contract](research/b0_story_zane/assessment.md). Other mixed-story vendors remain unimplemented. Stadium icons returned spontaneously without any refresh commands; no marker patch is warranted from that observation.

Latest S1 result (2026-09-25): user reports Dogtown services working, but Stadium vendor map icons absent. Exact site/reload coverage remains unspecified. Copied outer owners already retain vanilla POI Active nodes; inspect map filters and live journal state before choosing a marker-only repair. No service/root reset. This supersedes S1's pending live status below; [diagnosis](research/b0_special_services/assessment.md).

Latest Phase 4 batch (2026-09-25): **S1 adds 19 automatic Dogtown service candidates**, not all special vendors. Container-zone, Stadium and three Monument owners retain full native scenes, paired/companion actors, local gates and earned access; no regional/story root or Johnny Easter egg is restarted. Common guards additionally require `q307_ep1_killed=1`. Four additions preserve all 83 earlier files. Exact graph/payload checks, 345 negative startup cases, eleven-script compile, Lua and installation tests pass; live S1 coverage is pending. Claire is now user-confirmed working, with two logged native entries/normal requests and one exit; cold reload remains unconfirmed. Next: [combined S1 sample](docs/b0_special_services_check.md). Nix/Yoko/Viktor/Fred/Zane/Mateo/Pepe and other mixed story services still need narrow route work; [complete scope/blockers](research/b0_special_services/assessment.md). The user's all-special-vendor request is only partially completed.

Latest Phase 4 step (2026-09-25): **Claire's isolated automatic service candidate is installed; live check pending.** Only her narrow prefab-owning default-service phase is copied, retaining the full original scene, angry/refusal routing, garage-meeting gates, greeting latch and dialogue conditions. No race/default-dialogue root or outcome reset is included. Native trigger entry/exit and scene requests are logged; redscript stops polling after safe enablement. Four additions preserve all 79 earlier files; exact graph/payload, combined ten-script compiler, Lua and installer checks pass. Next: [one combined Claire first/return check](docs/b0_claire_check.md), not a special-vendor batch. [Evidence](research/b0_claire/assessment.md).

Yagami result (2026-09-25): the user reports all requested tests passed. The durable trace confirms automatic activation and four native entries/four exits, with the actor-distance gate reached; physical Trade is user-confirmed, not inferred from those counters. No cold-reload trace is established. This supersedes the pending first/return status in the earlier installation entry below.

Phase 4 follow-up (2026-09-25): **Yagami Market / Corpo Plaza food02 is now an installed automatic single-site candidate**. World-resource matching resolves the former location blocker; a `_duplicate` scene-marker suffix is corrected only in the mod-owned owner copy. Original spawn phase, complete scene, local gate, mappin approach and exact departure anchor are preserved. Four additions leave all 75 Baseline R1 + bar files unchanged. Offline checks pass; next is one seller/Trade/leave/return test, not broader special vendors. The preceding bars have a user-reported working result, without specified site-by-site/return/reload coverage. [Evidence](research/b0_cpz_food02/assessment.md), [combined check](docs/b0_cpz_food02_check.md). Earlier "unresolved food02 location" entries below are superseded.

Phase 4 ordinary-bar extension (2026-09-25): **four automatic candidates installed** for the previously deferred Corpo Plaza food01, Arroyo foodshop01, Northside foodshop02 and Charter Hill foodshop01 owners. Full vanilla trade/dialogue/drinking scenes and original local gates are preserved; drinking/workspot-aware departure prevents forced scene teardown during use. Four additive files leave all 71 Baseline R1 files unchanged. Offline graph, payload, combined compiler, Lua logger and installation checks pass; **physical actions, return cycles and cold reload remain unverified**. Next is one combined four-bar service/drink/stand-up/return check. Story bars, Coach Fred, Chang's deferred investigation and ambient NPC idling remain separate. [Evidence](research/b0_ordinary_bars/assessment.md), [test](docs/b0_ordinary_bars_check.md).

Current integration baseline (2026-09-25): **Restoration Baseline R1 is built and installed** at the user's request to consolidate implemented restorations and auto-load them. All 25 existing archives/registration identities remain unchanged. One new redscript coordinator automates the legacy tested vendors (including Wilson), H10's guarded geometry/action startup, Afterlife and Coyote; existing later automatic cohorts stay intact. Ten CET gameplay controllers are retired to read-only/non-writing compatibility bridges, and two superseded runtime jobs are dormant. Twelve replacements are backed up; no save or story fact was edited by installation. Combined compilation, 390 negative guard cases, Lua checks, all 71 installed file hashes and an isolated install/rollback roundtrip pass. **Combined in-game save/reload remains pending**; partial vendor observations are not promoted to full passes. Future work builds on R1, not old opt-in installers. [Evidence](research/restoration_baseline/assessment.md), [use and short integration check](docs/restoration_baseline_r1.md). Earlier entries below remain milestone history.

Current vendor boundary (2026-09-25): the six deferred ordinary variants are now a separate **installed automatic candidate**: Badlands gun02/food01, West Wind melee01, Rancho clothing01/medical01, and Japantown medical01. Exact full scenes, spawn phases, native approach and original local eligibility are preserved, including the two narrow Badlands setup operations. Offline graph/payload, compiler, Lua and installation checks pass. **Informal partial smoke pass:** the user reports vendors checked worked as expected but explicitly did not complete the prescribed test properly. Exact site coverage, return cycles, duplicates and cold reload remain unconfirmed; this is not six verified restorations. Christine is user-reported working; Chang is put aside after an unverified teleport landing and remains subject to his untouched gate. The prior working packages are unchanged. Next is one combined six-shop first/return run, not special vendors. [Evidence](research/b0_vendor_variants/assessment.md), [single-session check](docs/b0_vendor_variants_check.md). Earlier dated entries below are history, superseded where they name a different next task.

Deferred ordinary pair (2026-09-25, latest): following the user's narrowed request, Christine and Japantown netrunner 02 / Chang-Hoon Nam now have a separate **installed automatic two-site candidate**. Full original scenes, actor actions, narrow prefab ownership, local gates and shop-map lifecycle are retained. Chang additionally requires completed rescue and already initialized market state, with original q305 story-use exclusion; no rescue/discount/door events are replayed. Archive/edge/payload audits, redscript compilation, Lua tests and installed hashes passed. **Live result pending.** The working 25-shop cohort and netrunner 01 are unchanged. Next: one combined two-shop/return check, not Michał/Marcin or the broader special-vendor list yet. See [assessment](research/b0_deferred_ordinary/assessment.md) and [commands](docs/b0_deferred_ordinary_check.md).

Latest vendor result (2026-09-25): the user reports the automatic sample checks passed with no vendor problems. Logs confirm automatic enablement of all 25 eligible owners without Start, plus native visits at Northside clothing and Japantown melee; they do not establish 25 physical-site passes or cold reload. Preserve the working cohort. Next candidates are Christine's narrow default-dialogue Trade owner, then Michał/Marcin's shared-actor service; actual ancestor gates and complete local lifecycle must be traced before installing either. Claire/Nix/Yoko and other mixed story services follow individually, with Viktor highest-care because of Tower consequences. See [live result](research/b0_ordinary_vendor_batch/automatic_live_result.md) and [deferred-vendor plan](research/b0_vendor_rollout/vendor_restoration_plan.md).

Automatic vendor follow-up (2026-09-25, current): at the user's explicit request, the 25-shop cohort now auto-activates through its redscript driver after genuine Tower/owner/local-gate and player-safety checks. The opt-in test was **waived, not passed**; informal user checks remain pending. The two runtime files were updated with opt-in rollback backups; the archive, complete vanilla scenes, previous 15 regional owners, Wilson and mirrors are unchanged. Stop persists a mod-owned suspension; saved/in-flight owners and exclusions are preserved. Compilation, graph checks, Lua diagnostics and bootstrap contract-model checks pass, not live validation. See [current instructions](docs/b0_ordinary_vendor_auto.md). This supersedes the manual-Start/mandatory combined-test requirement in the earlier rollout entry below.

Latest vendor rollout (2026-09-25): **25 new matching regional owners are built, statically checked, and installed idle as one opt-in batch**, alongside 15 existing regional owners without duplication. Original complete vanilla scene references, actor actions, eligibility, dialogue history, stock and outcome state are retained; the tester confirms unique dialogue survived previous vendor tests. All 25 scene-node preservation checks, graph/archive checks, offline redscript compilation, Lua simulations and installed hashes passed. No new live pass is claimed. Twelve simple-shaped candidates and broader special/different-owner services remain deferred. Next is one combined sample/return/cold-load run, not automatic worldwide enablement. See [batch assessment](research/b0_ordinary_vendor_batch/assessment.md) and [complete commands](docs/b0_ordinary_vendor_batch_test.md). Earlier dated entries below are milestone history, not the current rollout boundary.

Ripperdoc/netrunner first pass (2026-09-25): eight simple-shaped regional owners have an installed **idle per-site opt-in** package. Archive, graph-edge, and Lua 5.1 checks passed. Charter Hill ripperdoc and Coastview netrunner passed reported full-menu first/return visits and 2/2 native entry/exit traces. In a second combined run the tester reported all five other ripperdoc menus worked; Downtown, West Wind, Rancho Coronado, and Japantown logged 2/2 cycles; Arroyo logged 1/1, and the tester does not recall its second route but reports no fault. All sites disabled cleanly. The original Vista del Rey netrunner gate was 0 on this save and remains untouched. A **separate** Japantown netrunner 01 opt-in passed static checks and its disposable two-visit test: one seller and actual menu reported, three native entries/exits logged, and clean disable/shutdown. Pre-enable visual baseline, transaction, cold persistence, and automatic initialization remain open. This is **not all ripperdocs/netrunners**: story/outcome/alternate-owner services and Japantown netrunner 02 remain separate. Do not auto-enable broadly or claim profile safety. See [eight-site assessment](research/b0_ripnet_eight/assessment.md), [Japantown candidate](research/b0_jpn_netrunner01/assessment.md), [two-type test](docs/b0_ripnet_eight_test.md), and [five-site test](docs/b0_ripnet_five_ripperdocs_test.md).

Paired vendor candidate (2026-09-24): the Badlands Inland Avenue SE5 junk and melee leaves passed source-shape, executable-edge, archive, and Lua 5.1 offline checks and are installed as one **idle opt-in** package. Both native owners reuse their vanilla actor/Trade scene and local default gate; a shared CET development driver manages two mod-owned exit flags. The first combined disposable trace recorded two native entries and exits **per shop**, both Far rearm cycles, clean Stop, and shutdown. The tester confirmed one seller and working Trade/inventory on both visits to **both** shops without failure. Precise pre-opt-in baseline, purchase, and save/reload remain unmeasured. Do not batch more vendors from this result alone. See [assessment](research/b0_junk_melee_pair/assessment.md) and [one-run test](docs/b0_junk_melee_pair_test.md).

Current vendor priority (2026-09-24): Wilson's H10 shop passed two disposable seller/Shop/menu visits with native entries/departures. Little China clothing v3 passed logged exit/rearm and reopened Trade. **Northside gunsmith passed a second regional-type test:** one seller, dialogue, physical Trade, a purchase, menu reopening on return, and three logged native entries/departures; the tester quit without saving. Both regional candidates still use a development-only exit distance flag and lack cold save/reload evidence. The expanded [vendor catalogue](research/b0_vendor_rollout/vendor_restoration_plan.md) distinguishes names from actual interaction requirements; Christine's inspected Trade loop is straightforward despite her name. The audit covers 23 questphase inputs / 143 scene occurrences / 125 distinct scenes, not 125 merchants or approved installs. Next: establish a reusable regional exit/persistence path, then batch only truly matching sites; treat local setups, outcome-sensitive paths, ripperdocs, and special stock individually. See [Northside result](research/b0_northside_gunsmith/assessment.md), [Wilson test](docs/b0_wilson_vendor_test.md), and [resource index](research/b0_vendor_rollout/service_resource_index.md). Mirror results are unchanged; Riot ambient NPC idling is deferred.

Focused Phase 4 update: H10 remains user-verified; the working Afterlife v5/v6 rollback is preserved. Native v7 omitted the narrow `#mirror_scene_afterlife` trigger prefab dependency. A1 passed native Inside=2/Exits=2; opt-in A2 matched three reported entries; development-only A3 passed two automatic cold loads and is inert. `ManualSave-16` made with A2 idle/armed cold-reloaded with native owner intact and 1/1/1. The one-site A4 redscript startup compiled and passed a no-save regression from pre-A2 `ManualSave-15`: automatic A2 owner, old owner off, one native 1/1/1 cycle, Look/expression/Stop working. v6 remains installed as dormant scene-driver rollback but still performs its 0.5-second polling; removing that residual poll and fresh post-credit integration are separate work. Saving inside the scene and other mirrors remain untested. No 36-mirror expansion was made. See [A4 test](docs/afterlife_native_bootstrap_a4_test.md), [saved reload](docs/afterlife_native_saved_reload_test.md), [A3 test](docs/afterlife_native_auto_a3_test.md) and [A2 test](docs/afterlife_native_scene_a2_test.md).

## Current design direction

The production target is a direct return to gameplay in the retained post-Tower session:

```text
The Tower completes normally
→ credits roll normally
→ remain in the genuine post-Tower / 2079 session
→ return directly to gameplay on the street in front of H10
→ restore only compatible sandbox content
→ preserve Tower consequences
```

The former mandatory **Continue in Night City / Return to Main Menu** popup is removed from the v1 roadmap. A brief notification remains optional polish, but it must not gate the handoff.

The project follows **Plan B0**:

```text
ordinary persistent Night City physical world
+ genuine Tower completion
+ q307_2079 and post-Tower logical state
+ existing 2079 media/content
+ selective restoration of compatible normal-world systems
```

Safe, localized 2079 visual or environmental overlays may be added later.

## Progress summary

| Phase | Completion | Current state |
|---|---:|---|
| 1. Reverse Engineering | 95% | Major architecture understood |
| 2. Direct Post-Credit Return | 95% | Retained-session return proven |
| 3. Basic Free Roam | 85% | Most fundamental sandbox systems already work |
| 4. World / Interaction / Services | 60% | Journal manual/cold-load passed; checklist consolidated; local shop/NPC world pass next |
| 5. Housing / Property Continuity | H1 installed | Five ordinary homes require purchase; H10 €$25,000, four native prices; earned Kerry access retained; live verification pending |
| 6. V Restriction Profiles | Accepted milestone | Character nerf implemented/installed and user-accepted; formal release regression remains |
| 7. Activity Restoration | Partial implementation | U9 implements 72 gig entries; startup blocked; side-job pilot passed, broader side jobs and other categories pending |
| 8. 2079 Content / Overlays | 35% | Census complete; Plan B0 selected |
| 9. Polish / UX | 5% | Mostly future work |
| 10. Release / Stability | Alpha planned | All-category pre-ending deployment and regression playtest required; not started |

Older percentages are planning estimates, not alpha readiness or playtest pass
rates. The integrated alpha is not ready until its entry criteria are met.

## Phase 1 — Reverse Engineering

**Status: ~95% complete**

Completed work includes q307 completion and cleanup mapping, `q307_persistent_content`, `internet_2_years_later`, final boards and credits, `questFinalBoardsVideosFinished`, One More Gig/PONR rollback, the q305/q306 in-place cleanup precedent, the Tower restoration matrix, and the 2079 content census.

Key conclusions:

- One More Gig is unsuitable because it restores a pre-ending PONR save.
- q305/q306 are the better precedent: remain in the live session and remove ending presentation state.
- q307 can retain a genuine post-Tower session.
- The game does not contain a complete alternate 2079 Night City.
- Most 2079 content is logical, media, or localized staging rather than a full alternate city.

Remaining work is limited to questions that block a concrete feature. Do not continue broad q307 research for its own sake.

## Phase 2 — Direct Post-Credit Return / Retained Session

**Status: ~95% complete**

The node-27/final-board hook, Q307 guard, mod-owned execution, retained-session return, Tower completion state, `q307_2079`, relationship outcomes, and post-Tower save/reload have been proven.

Production flow:

```text
The Tower
→ credits
→ direct retained-session return
→ final-board teardown
→ safe one-time placement on the street in front of H10
→ gameplay and automatic restoration
```

Remaining work:

- convert experimental direct-return logic into a clean production implementation;
- remove diagnostics;
- support watched and skipped credits reliably;
- prove no PONR load occurs;
- select and validate a street-level landing point in front of H10, including
  heading, streamed geometry/collision, restored player control and safe footing;
- perform the placement once per completed-ending handoff, after final scene/
  credits cleanup, never on ordinary reload, death/checkpoint reload or district
  re-entry; a pending handoff must recover without repeating a completed teleport;
- do not grant H10 ownership, a home marker or apartment services by arriving
  outside it; housing entitlement remains separate;
- validate both a fresh ending transition and save/load.

## Phase 3 — Basic Free Roam Foundation

**Status: ~85% complete**

Observed working: movement, map, inventory, character menu, skip time, saving, reloading, vehicle summon, weapons, combat, item pickup, pedestrians, police reactions, elevators, drop points, and ordinary world simulation in tested areas.

The normal sandbox is largely still running beneath Tower state. q307 removed or terminated selected world/content owners; the task is not to restart the entire open world.

Still verify and classify traffic, phone, owned vehicles, fast travel, vendors, apartment services, generic encounters, Dogtown access, and longer-session save stability.

## Phase 4 — World, Interaction, and Service Restoration

**Status: ~60% complete; current active phase (reassessed 2026-09-25)**

This is a planning estimate, not a pass rate across every game location. The
earlier 4B/4C/4D figures preceded the H10 normal-action pass, automatic
ordinary-mirror rollout and vendor batches. The dated accounts below document
how those results were reached; later observations supersede earlier failures.

Reverse only demonstrated sandbox-destructive effects. Never blindly undo every q307 action.

### 4A — Physical world geometry (~60%)

H10 entrance, bedroom, and bathroom geometry has passed visual, collision, save/reload, and sampled Tower-state checks. Build a q307 teardown inversion inventory and classify every target as `RESTORE`, `PRESERVE DISABLED`, `ENDING STAGING`, or `UNKNOWN`.

Do not automatically restore Zetatech, thug-scene, final-board, or temporary cinematic staging.

### 4B — H10 apartment interactions (~80%)

Current assessment: mirror appearance/expression, shower, sleep/time skip,
sofa/TV, wardrobe and holo-feeder were user-tested, with prompts returning
after leaving/returning and a full quit/reload. Normal use is restored on the
tested fixture. Forced interruption, exact effects and future housing
entitlement remain open. Earlier probe results below are historical.

Computer and toilet flush work. The V-only mirror action passed two manually triggered uses and normal exits, but the physical prompt remains missing. At the user's explicit request, a five-action, manual-only H10 test bundle for mirror, shower, sleep, sofa/TV, and wardrobe is installed for disposable saves. Run 1 confirmed the wardrobe path works, but its idle scene stayed active after the tester left H10; other attempted requests were refused by the overlap guard. After correcting copied socket stamps, run 2 confirmed the wardrobe scene exits cleanly (`Active=0`, `Completed=1`, `in_scene=false`). Run 3 confirmed sofa workspot entry/exit and the same clean scene exit; TV controls were not individually verified. Both prompts disappear on return because the current bundle starts temporary scenes and does not automatically restart them. At that stage mirror, shower, and sleep were untested. The bundle is not production-safe: active-action interruption, forced exit, unload, and save/reload cleanup remain unvalidated. Shower is a clothed first pass; sleep's effects are not yet profile-balanced. The near-sofa holo-feeder is a separate persistent device whose live interaction is unmeasured; do not blindly restart its owner or alter the q306 Tower memento. See `research/b0_h10_all_interactions/run1.md`, `run2.md`, `run3.md`, and `docs/b0_h10_all_interactions_probe.md`. Test one interaction per clean disposable save and do not change global story facts such as `q101_done`.

Run 4 now adds mirror and shower workspot entry/exit with clean later scene exits, but mirror's full options and same-visit prompt are absent. Sleep reached a high-tier/menu state without a recorded bed workspot or completed time skip. The tester reports frozen game time; no TimeSystem sampling exists, so attribution remains unknown. **Pause further interaction/sleep tests** until the clock advances on an untouched pre-interaction disposable save. See `research/b0_h10_all_interactions/run4.md`.

The pre-interaction baseline later yielded two identical `GameTimeStamp=7628401` readings after an instructed gameplay interval, with `TimeSkip` dilation false. This points to a pre-existing post-Tower clock pause rather than an H10-action origin, subject to confirming the interval was unpaused. q307 cleanup includes an unpause node, but its native effect/source semantics are unresolved. Read-only pause-owner diagnosis is the next gate; do not add a broad time reset. See `research/b0_time_pause/run1.md`.

Further graph inspection found source-`None` time pauses in q307's final-board call scenes after cleanup, with a q305 source-`None` unpause as a working native precedent. The installed manual one-shot completed-Tower source-`None` unpause probe succeeded in the retained session: `paused` changed true to false and automatic closed-console samples advanced `GameTimeStamp` from 7628401 to 7629048, while sampled Tower/2079 facts remained intact. This is manual recovery only; the later reload passed, but cold-start persistence and fresh watched/skipped-credit transitions remain gates before production post-credit integration. See `research/b0_time_pause/run2.md` and `run3.md`.

The tester subsequently reports time still running after reload. Trace confirms a detach/reattach and continued clock advance with `Done=1`; a cold game-process restart remains unverified unless separately confirmed. See `research/b0_time_pause/run3.md`.

### 4C — General mirrors and world devices (~65%)

Current assessment: Afterlife and public El Coyote mirrors work; the 25-site
ordinary-mirror C4 cohort starts automatically, with five sampled physical
sites and a cold-load Riot check reported working. The other sites, special
mirrors, apartment devices and some world interactions remain unverified or
deferred. The dated development sequence below is retained as evidence.

Next bounded follow-up: a Red Dirt single-site opt-in C5 candidate has passed
an offline build and scene-delta comparison, but remains uninstalled pending
site/quest-state observation. The Streetkid-start surface is a q000 visual
device with no ordinary Look owner. A one-shot S2 stool/fix-nose opt-in is
installed idle, preserving S1 and all baseline files. It isolates the original
V-only actions without prologue/story writes; live action/exit and reflection
are unverified, and real/fake mirror variants remain untouched. This optional
revisit is not counted as a restored vanilla free-roam seat. Public seating
still needs an independent persistent owner reference. See
[S2 assessment](research/b0_streetkid_seat_mirror_s2/assessment.md).

S2 live update: first Start crashed with a native access violation. The last
durable snapshot follows Enabled=1 but precedes any observed scene request;
exact crash instruction is unresolved. Resource-table/animation-binding and
unrelated-prop acquisition defects were found after the crash. S2 is rejected
and no further Start/S1 test is requested; repair and a smaller scene-load
probe must precede action testing. Existing restoration baseline is unchanged.

2026-09-26 recovery: approved S2 registration disable completed with a
recoverable hash-verified backup; 326 other installed files are unchanged.
Action resource/localization dependencies are repaired workspace-only. S3 is
built and offline-checked as an action-free 2 s acquisition/return probe, now
installed idle with all 326 prior files hash-preserved. Live Start subsequently
crashed reading0x34. Both dumps identify V actor3 indexing player slot1 from
a one-player cast after removal of template Johnny. Actor3->2 and performer
769->513 repairs now pass regression checks that reject the crashing artifact.
S3 revision2 is installed idle with 352 other files preserved and backups;
its short load/return test now passed: Requests1, Returns1, Completed1,
Interrupted0, idle V and unchanged required facts. S2 revision2 subsequently
passed nose/normal exit, but user reports blank labels and missing glass and
reflection. Revision3 is installed idle, preserving 377 other files: repaired
localization/indexing, scene-owned glass/Drink, explicit Get up after Fix nose,
and narrow mirror variant/device cleanup on normal/interrupted exit. Revised
live check now confirms readable action labels, room reflection and normal
scene return. Initial glass placement and V reflection remain defective; body
activation is absent from the current scene. Do not copy prologue outfit waits.
Revision4 is now installed idle (389 other files preserved; revision3 backup):
matching-body activation/workspot/release, default mirror appearance and glass
acquired at scene start at a bar-relative authored pickup transform. Revised
visuals await the single-site test. No completeness increase. S1 stays unarmed;
do not run S3 concurrently.
Inspect is optional; use the single disposable action test.
No completeness estimate changes and no full ending replay is requested.

2026-09-24 update: The Afterlife native A2/A4 site and public El Coyote washroom C2 site have passed user action checks; Coyote's durable log records one request/return/rearm, while its second working visit occurred after logging stopped. The Streetkid-start surface is a separate q000 prologue device without an ordinary Look owner and is deferred with special interactions. A 25-site C3 cohort passed physical action checks at five sites. A clean Riot run logged one native request/return, idle scene/workspot, and a prompt still present. Automatic C4 is now installed as a guarded beta, replacing C3's opt-in registration while preserving C3 as rollback. On a cold load of an older post-Tower disposable save, the tester reports two successful Riot uses without CET arming; native C4 counters were not supplied. No further manual mirror test is requested. Ten other simple-shaped leaves remain excluded for site-specific reasons; Coyote is already C2. None of those ten is counted as restored. Riot bar NPCs were separately observed standing idle; cause unknown, defer to later world-population/NPC service work. See `docs/ordinary_mirrors_c3_test.md` and `research/b0_mirror_rollout/inventory.md`.

H10 mirror ownership is not representative of all mirrors. A Shady Ripper leaf has been statically mapped as a possible one-site probe, but site access and live device state after Tower are unknown; see `research/b0_h10_generalization/interaction_branch_map.md`. Restore one non-H10 device, identify its owner, and generalize only if the ownership pattern is shared.

Corpo Plaza apartment is now the first non-H10 home comparison. The tester reports intact geometry and missing prompts, and confirms pre-Tower ownership. Its DLC6 site phase/interaction scene is a child of `mq000`; the scene's normal loop requires apartment state plus `#dlc6_apart_cct_dtn_tr_apartment`, and its mirror path includes Johnny-linked logic. Current purchase state and exact missing prompts remain unknown. Do not start the complete scene or apartment root; first read the local purchase fact and map a single safe action under Phase 5's new entitlement rule. See `research/b0_corpo_apartment/run1.md`.

At the user's direction, H10 remains the active target; Corpo Plaza is only recorded. One opt-in mod-owned H10 owner now combines the five statically reviewed routes and re-arms after normal H10 exit or mirror Leave. It is installed but not live-tested, so the next gate is physical prompt visibility, normal action cleanup, leave/return, and cold save/reload on disposable saves. Full mirror appearance/facial options and the separate holo-feeder remain unresolved; do not call this production-ready. See `docs/b0_h10_persistent_probe.md`.

The tester then confirmed v1's basic mirror Look/Stop prompt returns on second use and after H10 exit/return; the runtime trace also shows completed native cycles without Tower-fact drift. The installed v2 archive statically adds the vanilla-local appearance menu and five facial-expression actions, bypasses old `mq000_hairdresser_used`, and does not set global `mirror_interactions_facials`. Next gate: live-test those options, return from the appearance menu, normal Stop/rearm, then cold save/reload on a disposable save. Forced interruption and other H10 routes remain separate unresolved validations. See `research/b0_h10_persistent/run1.md` and `docs/b0_h10_persistent_probe.md`.

The v2 test found Look still worked but new choices did not appear. Static reachability had counted attachment-only edges; an executable-path audit exposed the missing entry. The installed v3 connects the mirror approach directly to the local appearance/facial chooser and Stop looking chooser, bypassing old MQ055/Johnny gates; executable-path tests pass. **Live choice visibility and action cleanup remain unproven.** Test v3 on the disposable save before further H10 generalization.

The v3 test now confirms mirror appearance/facial choices are visibly available. The tester reports exercising appearance, expressions, shower, sleep/time skip, TV/channel/sofa, wardrobe, and the separate sofa hologram, with prompts returning after full quit/reload and room exit/return. Treat H10's **normal interaction path as restored on the disposable fixture**, while keeping forced interruption, exact action effects, shower clothing, sleep/profile balance, and eventual ownership gating open. The separate hologram is not part of the combined scene owner. The next representative non-H10 site is the tester-confirmed missing Corpo Plaza apartment mirror; isolate only that action, and do not revive the complete DLC6 apartment scene or bypass Phase 5 entitlement. The Little China clothing shop remains the representative vendor.

### 4D — Vendors and services (~75%)

Current assessment: the consolidated regional baseline, ordinary bars,
Dogtown/local services and S2-S4 story-linked owners are installed; the user
reports broad vendor checks working, including the eight-site S4 smoke route.
Under the project rule, a vendor correctly disabled by original quest facts
counts as restored. Unknown owners/identities, some location-specific services,
return/reload coverage and future quest handover remain open. Earlier single-site
probe accounts below are historical, not the present vendor rollout status.

Wilson's service is owned by a branch of `default_dialogs.questphase`, not the generic regional vendor leaf. His installed opt-in uses the original spawn entry, native wanted-level scene cut, reduced five-node Shop/menu scene, and a CET development 80 m location sampler. A disposable two-visit test passed seller, Shop, menu, and native exit/re-entry without duplicates; transaction and save/reload remain unconfirmed. Little China clothing's regional owner required an inner-graph wiring repair (v1 failed); v2 restored seller, physical Trade and menu, but did not deactivate at >100 m. V3's one-shop development distance flag passed native deactivation and logged rearm/second Near entry; the tester confirmed Trade reopened on return and saw one seller without visible duplication. An instrumented actor count, second exit, and save/load remain open before any broad per-shop rollout. The 16-root regional census is branch-level inventory, not an installation list. Do not restart whole vendor roots or count the vendor system restored. See [Wilson test](docs/b0_wilson_vendor_test.md), [Wilson assessment](research/b0_wilson_vendor/assessment.md), [clothing assessment](research/b0_lch_clothing_vendor/assessment.md), and [regional inventory](research/b0_vendor_rollout/inventory.md).

**Vendor classification is evidence-based, not name-based.** Public retail categories are clothing, food/drink, firearms, melee, junk, meds, netrunners, and ripperdocs. The regional audit's nine internal name buckets (11 clothing, 28 food, 10 gunsmith, 4 junk, 12 medical, 4 melee, 3 netrunner, 11 ripperdoc, 1 tech) still sum to 84 scenes, but `tech` is not a ninth distinct retail/service type. Neither a name, extra dialogue, nor a quest-fact mention alone proves a special interaction requirement.

The [expanded catalogue](research/b0_vendor_rollout/vendor_restoration_plan.md) contains the location-labelled ordinary roster, named merchants across base game and Dogtown, alias/identity gaps, scene evidence, and per-vendor treatment. The [resource index](research/b0_vendor_rollout/service_resource_index.md) covers 125 distinct scenes across regional, default-dialogue, and EP1 owners. It includes excluded content for audit completeness; it is not an enable list.

| Treatment | Examples / evidence | Restoration plan |
|---|---|---|
| Standard trading, whether named or unnamed | Christine's two sq012 branches converge on the same Trade chooser; Satoshi, Saki, Susanna have local service state without an established bespoke story interaction | Reuse matching service logic while preserving exact owner and guards; Christine needs a narrow default-dialogue owner, not a new story quest |
| Local interaction setup | Michal and Marcin share a two-person dialogue/shop; Sammy has a bell/security actor; Leon has guitar/workspot state; some clothing sites have wardrobe | Preserve intended actors and local lifecycle; only add special handling where a dependency actually requires it |
| Story/outcome-sensitive route | Claire has a vendor panel plus sq024 conditions/story writes; Nix/Yoko/Fred/Zane have mixed service/quest paths; Bill, Chang-Hoon, Roger and Darrell have unlock/survival leads | Trace reachable branches, preserve outcome, and isolate compatible service. Do not replay quests or clear refusal/death flags |
| Ripperdoc/profile service | Shared cyberware service, plus individual cases such as Viktor, Fingers, Charles, Cassius and moving-camp Hutch | Enforce selected profile through equipment/menu/reload; preserve individual consequences without inventing a unique fix for every name |
| Inventory-specific service | Herold's iconic recovery stock; earned rewards and one-time purchases | Preserve original vendor identity, entitlement, and transaction state |
| Unresolved or non-repeatable | Jack/Zhan identity, some food actors, NCX access, Shank's exact service, quest-only sellers | Keep out of automatic batches until the specific gap is resolved; do not mistake all named conversational NPCs for vendors |

**Rollout:** the second regional type, Northside gunsmith, passed the disposable physical and native entry/exit test. Resolve a reusable production exit path and cold persistence, audit each next site's complete owner/eligibility, then batch genuinely matching services. Sample each new owner/menu/lifecycle mechanism; do not require a separate bespoke implementation or manual test solely because an NPC has a name. Separately validate bell/multi-actor/workspot, outcome-sensitive, ripperdoc, and special-stock mechanisms. Integrate only proven owners into the post-Tower initializer. Keep Sophia's Johnny Easter egg excluded; do not run the q304 stadium vendor controller or whole vendor/story roots as a repair.

Northside gunsmith baseline: no seller or Trade at 11.4 m from the mapped workspot, with local `default_on=1` and genuine `q307_done=1`. Its isolated opt-in then passed one seller, dialogue, Trade/menu, purchase, return with reopened menu, three native entry/departure cycles, Stop, and quit without saving. This validates the normal action path on the disposable fixture; cold save/reload and a production exit mechanism remain open. See [assessment](research/b0_northside_gunsmith/assessment.md) and [test record](docs/b0_northside_gunsmith_test.md).

Next retail type: Northside foodshop 01 has no physical seller on the post-Tower baseline while `wat_nid_foodshop_01_default_on=1` and Tower is completed. Its scene has a single food vendor panel and a local `used` flag. A one-site mod-owned owner/archive and CET probe were built, edge-audited, and installed idle while the game was closed. The initial test reached native spawn; a second disposable run logged departure/re-entry/departure with return Trade confirmed and clean Stop/shutdown. This is a one-site food-service/respawn pass, not broad food-vendor approval; purchase details, cold reload, and production exit still need validation. See [assessment](research/b0_northside_foodshop/assessment.md) and [test steps](docs/b0_northside_foodshop_test.md).

Medical representative: the tester previously found the med shop beside Northside foodshop 01 vendorless. Vanilla workspot positions identify it as `wat_nid_medicstore_02` (not medicstore 01). Its single-shop native owner and scene passed static build/edge audits; a separate opt-in package is installed. First Inspect confirmed local `default_on=1` but refused because V was already in a scene while earlier foodshop and gunsmith opt-ins were active; isolating those owners cleared that guard. On the next disposable run, the med owner enabled and logged native departure/re-entry twice, with the seller and medical Trade/inventory verified on return; the final departure, Stop, and quit also logged cleanly. Purchase, duplicate count, and cold persistence remain open. No medical-vendor batch is approved. See [assessment](research/b0_northside_medicstore/assessment.md) and [test steps](docs/b0_northside_medicstore_test.md).

The tester subsequently reported all three Northside vendors visible after cold reload. The available probe logs contain no corresponding new attach, and save/opt-in provenance is not yet known, so record this as a user-observed persistence signal rather than a confirmed automatic initialization or three-menu reload pass.

Shared regional-vendor candidate: a four-shop opt-in now combines the already tested Northside gun, food, and med owners with Little China clothing. A single redscript driver supplies all four development `Far` flags from one active player-position read; existing native phases still own spawn, Trade, exit, and rearm. A one-command CET batch arm waits for a fresh redscript challenge/ack, and a one-command Stop closes the combined run. Four fallback CET writers are bypassed only while shared mode is active; their originals are backed up and a checked rollback script exists. Offline redscript compile, Lua syntax/simulation, installed hashes, and scope checks passed. The **first live combined run passed activation and rearm**: the tester reports all four vendors worked on first and return visits, and the trace records two Near entries and two departures per shop plus clean Stop. An explicitly reported transaction, duplicate count, and production integration remain open. Older manual saves lack working world mirrors, but the tester found a later autosave with a working mirror. `ManualSave-17` was first made with `scene=true` at Riot, then overwritten at the Riot fast-travel point with `SharedMode=1`, all four shops `Enabled=1, Near=0, Far=1`, and V `combat/scene/workspot=false`. On a full quit/relaunch, this revised slot retained the shared mode and all four idle enabled flags; the tester reports the Riot mirror and visited Northside vendor actions worked without faults. The trace verifies all three Northside native Near paths and a clean outside Stop. Little China clothing stayed armed but was never approached in that cold-load run (minimum distance about 639 m); at the user's direction, treat its saved-reload Trade path as an explicit working assumption and do not demand a separate manual test now. Do not expand the roster or call the batch production-ready yet. See [assessment](research/b0_vendor_shared/assessment.md), [combined vendor test](docs/b0_vendor_shared_test.md), and [mirror correction](docs/ordinary_mirrors_c3_test.md).

Acceptance: correct intended actor group (some shops legitimately have multiple actors), physical prompt, real menu and representative transaction, normal departure/re-entry without extra actor instances, then cold save/reload with Tower/outcome/stock state preserved. A visible NPC or changed fact alone is insufficient. The installed medical candidate is opt-in and uncertified until its physical test.

### 4E — Scene and environmental restoration (~20%)

Classify localized content as `PERSISTENT 2079 ELEMENT`, `SAFE 2079 OVERLAY`, `ENDING-ONLY STAGING`, or `UNKNOWN`. The Zetatech route exposed missing geometry/collision, so cinematic staging must not be treated as a persistent city.

Misty/Viktor shop restoration belongs in the next world pass, after journal
cleanup and the restoration whitelist, before profiles/activities. Audit
missing geometry/collision, interior/street connections, doors and local
services separately. Viktor's existing service restoration does not establish
rebuilt geometry or a2079 appearance. Preserve appropriate Tower physical/media
outcomes; the original q307 cinematic scene is not a shop-restoration mechanism.

### 4F — Journal and quest presentation (~40%)

Target state:

```text
HUD: no Tower objective
Journal: Things Done Changed in completed/history
Quest tracking: inactive
Tower facts: unchanged
```

Finalize the parent journal hierarchy and stale presentation without deleting history or reactivating q307.

Manual hierarchy repair and user-confirmed cold-load passed2026-09-27; see
research/tower_journal_cleanup/live_result.md. Automatic integration and
tracking edge-case/fresh-ending release coverage remain open, not a reason to
repeat the same manual test. The earlier disposable P2 run
changed `05_take_walk` from Active to Succeeded, while `02_mistys_alley` and
`q307_tomorrow` stayed Active and Tower tracking persisted. Reuse that evidence
(`docs/phase2b_p2_run1.md`); inspect the current post-Tower fixture before
assuming the same residue remains. A repair must resolve the exact completed
Tower hierarchy, preserve unrelated quest states and existing history, and
verify HUD/tracking plus save/reload. Do not resume q307 or force story facts.

### 4G — Sandbox-service verification (~60%)

The current matrix is research/restoration_checklist.md: WORKING,
INTENTIONALLY GATED, UNRESOLVED and DEFERRED; deployment/evidence/limits are
separate fields. Correct original vendor gates count as restored on the
tested fixture, unknown/deferred owners do not. Pedestrians, police, combat,
drop points, vehicle summon and elevators are already observed working.

Ambient NPC behavior is scheduled in the same next world pass as the shops.
Begin with the user-reported Riot/bar NPCs standing idle: determine whether
affected actors lack local community/workspot/ambient scene owners, remain
scene-controlled, or exhibit expected idle behavior. Cause remains unknown;
this is not proof that global AI is disabled. Ordinary ambient behavior is
separate from story dialogue/quest restoration.

## Phase 5 — Housing / Property Continuity

**Status: H1 installed on 2026-10-23; live verification pending**

Required for the integrated alpha. The latest user revision requires repurchase
of **all previously owned ordinary apartments** after Tower: H10 for **€$25,000**;
the others at their normal purchase prices, without a surcharge. H1 adds a
permanent versioned receipt system, native home services, exact device guards
and safe migration of existing owners. It preserves shared inventory, old
purchase history and saved quest progress. No public beta is declared by this
implementation status.

Final build `prealpha/housing_h1/build/h1_02` passed full SCC compilation with
EquipmentEx, saved-field/catalogue/owner identity checks, compiled payment and
device guard review, and twenty scoped installation/rollback cases. Installation
added five files and replaced two scripts, with backups; 717 protected files,
including 215 saves and five cache files, were unchanged. Recovery starts with
H1 before S28 and older packages. See [the housing checklist](docs/housing_h1_playtest.md)
and `research/housing_h1/assessment_01.json`. These are build/install results;
they do not claim an actual future stable save upgrade or live purchase pass.

The two-year absence removes V's ordinary apartment entitlements, not the
apartments' geometry, shared stash contents or unrelated story state.

### Ownership reset

- Remove every previously owned ordinary apartment from V's active owned-home
  list until that apartment is repurchased.
- Gate each lost home's owned marker and home-only services, not public access or
  the building itself.
- Preserve unrelated story and relationship state.
- Record pre-Tower property state to identify which ordinary apartments need
  repurchase, without altering never-owned purchase eligibility.

### Reacquisition

- H10 costs **€$25,000** to reacquire, as one transaction. This is 2× a
  **mod-defined €$12,500 reference price**, not a claimed vanilla sale price.
- Other previously owned ordinary apartments require repurchase at their normal
  purchase prices, with no surcharge or price increase.
- Never-owned ordinary apartments retain their normal purchase rules and prices.
- Reuse compatible native purchase handling where safe, without inventing a
  vanilla H10 sale price or treating a renovation fee as that price.
- Ownership and services must persist through save/load.

H10 is the starting apartment, not one of the four separately rented properties;
the [official apartment notes](https://www.cyberpunk.net/en/news/41435/patch-1-5-next-generation-update-list-of-changes)
distinguish H10 customization from those rentals. The user-approved €$25,000
repurchase price is a mod rule, not the renovation fee. Alpha must test purchase, insufficient funds,
cancel, repeat purchase protection and reload without a second charge.

### H10

H10 geometry may exist while H10 is not V's home. The post-Tower street arrival
does not grant the apartment. After repurchase, restore its home marker and
appropriate stash/home, sleep, wardrobe and other apartment interactions.
Do not delete shared stash contents. Access through another ordinary home follows
that home's own post-Tower repurchase state.

### Relationship homes

Judy's apartment and similar homes are not generic real estate. They are not
purchasable and receive no repurchase price. Their access must follow the actual
Tower relationship outcome, not the ordinary-apartment repurchase rule.

**Explicit exception — Kerry's house (2026-10-21):** V keeps existing access;
this is the only home exempt from the post-Tower home-removal rules. Do not
remove its earned access or charge a purchase/repurchase fee. Capture that
access separately from ordinary apartment ownership and preserve it through
handoff, death/checkpoint reload and cold reload. Do not fabricate a romance,
complete Kerry quests, spawn Kerry, or enable excluded conversations to provide
house access. This exception does not grant unearned relationship history or
turn his house into purchasable real estate. Exact visitor/home services still
need a native entitlement audit during implementation.

### Interaction gating

Separate restored mechanics from entitlement. Home-only sleep, wardrobe, stash, shower, mirror, sofa, buffs, and map/fast-travel presentation should be enabled only when appropriate for current post-Tower ownership. Visitor-appropriate interactions may be classified separately.

Definition of done:

- all previously owned ordinary apartments lose housing entitlement until repurchased;
- H10 can be repurchased once for €$25,000;
- other previously owned ordinary apartments can be repurchased at normal prices,
  without any price increase or duplicate charge;
- never-owned apartments retain their normal purchase rules;
- Kerry's house retains V's existing access without removal or repurchase;
- other relationship homes remain non-purchasable and respect Tower outcomes,
  with no additional retained-home exception;
- home-only interactions follow new ownership;
- ownership survives save/load;
- no old story state is revived.

## Phase 6 — Canonical V Restriction Profiles

**Status: character-nerf milestone accepted by the user on 2026-10-08.**

The installed implant-focused profile selects HP 150, Body 3 with all Body
perks blocked, closed Relic, the reviewed cyberware whitelist, and 53 other-tree
implant/dependency perk bans. The stricter profile source remains available;
selection is build-time, not a live profile menu. No-vitals activation preserves
its existing opt-out. Previous refunds are not reversed or replayed.

No Nerf/Cyberware Only policy foundations and the Full Nerf implementation
remain documented in [profiles/README.md](profiles/README.md). Body/HP values
are user-selected balance rules, not numeric canon. Formal end-to-end,
compatibility and long-session regression belong to release work; the user's
acceptance does not manufacture unobserved engine test results.

This milestone stays **done**, including the user-confirmed HP checkpoint-reload
repair. Alpha adds integration/regression checks and production activation of
the selected profile; it does not reopen the balance or perk-selection design.

## Phase 7 — Activity Restoration

**Current status: partial implementation; full activity coverage required for alpha.**

U9 implements all 72 cast-whitelisted gig entries using original gameplay and
scoped native dependencies, but the first broad startup test was refused. The
phone-admission issue remains open. Only Pain supplied a working side-job pilot;
broader side-job and other-category implementations remain pending. Development
tests are not production pre-ending history or automatic-restoration proof.

Current production rule: restore only whitelisted gigs/side jobs captured as
unstarted before Tower. Previously started jobs remain unavailable/failed;
completed/rewarded and genuine failures are preserved. Capture actual history
before ending cleanup and preserve it across saves. Missing history stays
unknown. The development incomplete-as-unstarted assumption is a separate test
route, never certified history or completed-gig replay permission.

Restore other compatible activity categories as category-wide batches, retaining
native unlocks, completion history and repeatability. They do not need entries
in the gig/side-job whitelist. Supporting Johnny keeps voice and scene timing
but no visible projection; Johnny-central/Relic-dependent and live-participant
Panam/Kerry/Judy jobs remain excluded. Difficulty under Body 3/HP 150 or receiving
an unusable item alone is not an exclusion. Keep every omitted activity or
unimplemented owner explicitly recorded with its reason; do not silently narrow
the target to the currently working examples.

The older research and pilot notes below are historical where they conflict
with this current policy. In particular, earlier started-gig continuation and
completed-replay experiments do not broaden production eligibility.

**Latest2026-10-09:** user completed the stable native71 capture pair and asks
for pre-ending save-local history plus post-ending overrides for BOTH gigs and
side jobs, including completed-content replay. Default preservation remains;
explicit replay needs a per-activity ownership/reset/reward adapter, not blanket
journal/fact resets. First combined ending alpha waits until both are ready.

R3 **foundation installed, not alpha-ready**:71 gigs+57 side/minor jobs,
1695 journal observations/2192 fact getters; own persistent snapshots,
conservative boundary freeze, old post-ending unknown handling and override
interface.3 additions/0replacements/1759 protected files unchanged; compiler/
models/fixture/install/readback/rollback PASS. Native cutoff/save/reload/perf
unproven. Only G1 continuation supported; other127 adapters and all completed
replay pending. No new side job or broader gig activated. Next per-owner
adapters and representative side-job restoration before alpha.
[Current limits/commands](docs/gig_pilot_r1_check.md#activity-history-and-override-foundation-r3).

**2026-10-09 broader rollout:** the user reports G1 worked and selects the
broader **71-gig whitelist**. The log supports native quest/phase/objective
success, reward claim/ack and one Watson3->4 counter transition; independent
cold reload, exact cash/XP, native failure and owner release are not established.
All71 exact native IDs/resources are catalogued. A read-only batch collector
is installed (two additions, no replacements, 1,582 protected files unchanged;
installed hashes/rollback preflight PASS). **No additional gigs restored yet.**
That capture pair is complete:9 completed,5 cleanup patterns,56 inactive
candidates,1 ambiguous failure-monitor flag. Next per-gig eligibility,
compatibility and
stage-safe adapters. Preserve completed/rewarded and genuine failures. Selected
started gigs may continue only where supported, never blanket-reset or repeat
initialization/rewards. Side-job/default policy and other category order stay
unchanged. [Capture instructions](docs/gig_pilot_r1_check.md#broader-71-gig-rollout-next-capture),
[audit receipt](research/gig_restoration/rollout_r2/audit_install_receipt.json).

**2026-10-09 selected pilot:** the user now explicitly requests restoration of
one of the six visible started gigs. Many Ways to Skin a Cat is selected as a
single opt-in continuation exception. G1 is implemented/offline-tested and
installed 2026-10-09 (four additions, no replacements; receipt/readback and
rollback preflight PASS). Observed gameplay subsequently passed by user report
with native-success/reward/counter evidence; remaining evidence limits above.
The default fresh-only rule is unchanged for other activities; no global
less-strict mode or whitelist-wide restoration is implied. See
[pilot assessment](research/gig_restoration/pilot_r1/assessment.md) and
[live checklist](docs/gig_pilot_r1_check.md).

Delivery strategy chosen by the user (2026-10-09):

- **Gigs and side/minor jobs:** select one genuinely eligible representative gig and one representative side/minor job, restore and live-test each complete lifecycle, then generalize the proven pattern to the selected lore whitelists. Admission remains per job: audit native unlocks, pre-ending start history, actors, objectives, rewards, and Tower/profile compatibility before including it. A representative pass does not certify every other job or authorize a blanket quest-root restart.
- **Other activity categories:** restore each category as a batch rather than piloting and deploying one activity at a time. The category implementation must still preserve each instance's completed/failed state, existing rewards and original gates, and pass per-instance and save/reload checks. "All at once" means one scoped category rollout, not reset-all facts or replay-all rewards.
- **Cyberpsycho test fixture:** the user's current save completed Cyberpsycho Sightings before the ending. A future test may temporarily change the necessary fact(s) on a disposable copy, recording exact original values first, then restore those values and verify journal, encounter, reward and reload state. Reversing a fact alone may not reverse quest-graph or reward side effects; never use the sole/main save as a reversible test and do not treat this plan as authorization to mutate a save now. Prefer a genuinely unfinished fixture if available.

Planned category order:

1. Selected compatible gigs — representative first, then selected whitelist
2. Selected compatible side/minor jobs — representative first, then selected whitelist
3. NCPD Scanner activities (Assaults in Progress, Reported Crimes, Suspected Organized Crime Activities)
4. Cyberpsycho Sightings and their reporting/reward chain
5. El Capitán vehicle contracts (`Push It to the Limit` onboarding and repeatable `Just Another Story` loop; keep the one-time job's eligibility distinct)
6. Dogtown airdrops
7. Replayable races and other repeatable/systemic combat activities, retaining their native unlocks

### Quest and gig eligibility

Cast rule, approved2026-10-10: supporting Johnny dialogue may remain as a
voice-only gameplay interpretation, with no visible projection. Exclude
Johnny-central/personal-story/takeover/Relic-dependent jobs and entire jobs
containing Panam, Kerry, Judy or Misty as live participants, including optional scene,
call and message branches. Mentions, historical recordings and completed
prerequisites alone are not live participation. Unknown full-cast/branch
coverage stays pending; title selection is not runtime admission. Preserve
necessary internal scene bindings/timing. Voice-only presentation is installed
and user-tested on a pilot; it still needs per-route alpha regression. Do not
revive Johnny/Relic/Tower facts. Current
selection is [R6.1](research/gig_restoration/lore_whitelists_v6_1_dependencies.json), with
[final decisions](docs/whitelist_final_r6.md). Older installed history definitions
and package inputs remain pinned until reviewed integration/migration, without
invented pre-ending evidence. The R6 list alone does not alter runtime admission.

**Current side-job rule supersedes the historical default below:** completed
stays completed; unfinished restarts once; never-started begins natively.
General restart migration is not implemented. The following older fresh-only
rule remains relevant to gigs and historical design, not a reversal of the
17 October side-job instruction.

Historical default: **fresh selected activities only**.

- An unfinished quest or gig already started before The Tower ending becomes
  failed and stays unavailable after the ending. Preserve vanilla failure where
  it already occurred; do not reactivate or restart it under this default rule.
- Only explicitly selected, compatible quests and gigs that were not started
  before the ending may become playable. Fresh does not mean all unfinished
  content; original eligibility and outcome gates still apply.
- Completed/rewarded activities stay completed, and genuine prior failures stay
  failed. Do not erase progress, repeat rewards or recount fixer completions.
- Freshness is assessed against the ending boundary, not every load. A fresh
  activity legitimately begun after Tower may progress and resume after reload.
- Classify start history from audited per-activity evidence, not map discovery,
  an automatically initialized Active journal alone, or absent/default-zero
  facts. Unknown or contradictory history does not qualify as fresh.

For gigs, a **less-strict mode** remains a possible future playability option: selected,
compatible activities started before the ending could remain playable or be
restored afterward. It is not the active/default rule and is not implemented.
It would require explicit opt-in and per-activity handling of saved progress,
ownership and exactly-once rewards; it does not authorize blanket restarts,
replaying completed/genuinely failed content, or bypassing Tower compatibility.
The earlier broader71/G1 continuation requests were development pilot exceptions,
not current production permissions. Other categories retain their own original
one-time or repeatable lifecycle rules and completion preservation; do not apply
a one-time quest freshness test to disable a legitimately unlocked repeatable loop.

These are design rules, not a new runtime failure sweep or installed switch.
Any future enforcement must preserve vanilla q307 and apply only after genuine
Tower completion; this policy does not authorize changing ending/main-story
state, reintroducing Johnny's engram/visible projection or restoring Relic
content. The supporting voice-only R4 compromise does not authorize those
story changes.

Many Ways to Skin a Cat is **excluded on the tested saves under the default
rule**: start/combat markers and the [native comparison](research/gig_restoration/save_audit.md)
prove prior progress. Its quest/phase/inside are Active pre-Tower and Failed
post-Tower; completed controls remain Succeeded. The latest explicit request
selects the narrow G1 exception above, not a new-start adapter.

**Historical fresh-pilot finding, before the G1 exception:** the
six visible gigs—Dancing on a Minefield, A Lack of Empathy, Talent Academy,
Treating Symptoms, Many Ways to Skin a Cat and Rite of Passage—already show
active objectives before the ending. They are ineligible for a new start under
the approved fresh-only rule. [Race to the Top in Arroyo](research/gig_restoration/race_to_top_assessment.md)
is not shown in the available-gig screenshots; its tier-one source/save fact
did not prove availability. Do not request its prepared CET probe as the next
test. A started-gig continuation would need explicit selection of the
less-strict policy and a targeted native-stage audit. The latest user request
supersedes that hold only for the selected Many Ways continuation pilot.

[Serial Suicide in Corpo Plaza](research/gig_restoration/fresh_candidates/assessment.md)
is fresh in the pre/post read-only snapshots, including two agreeing post-Tower
reads, but its actual entry needs tier two or a debug gate. The recorded tier-one
flag does not lead to the gig, and tier two is not recorded in the inspected
saves. Do not force the gate. No gig restoration has been implemented or installed. See
[gig research](research/gig_restoration/assessment.md).

Classify each as `SAFE`, `CONDITIONAL`, or `INCOMPATIBLE`. Exclude Johnny-central,
Relic-dependent, Nocturne, conflicting main-story and Panam/Kerry/Judy-participating
jobs. Supporting Johnny voice is conditional on reviewed invisible presentation
and preserved native scene completion, not a blanket Johnny-bearing-owner restore.

## Phase 8 — 2079 Content / Plan B Overlays

**Status: ~35% complete**

Plan B0 retains normal persistent Night City plus Tower completion and 2079 logical/media state. Plan B+ may later add runtime-validated advertisements, graffiti variants, or localized visual changes. Do not invent a full alternate city.

## Phase 9 — Polish / Player-Facing UX

**Status: ~5% complete**

Remove development-only diagnostics from the player path, smooth the post-credit
handoff to the selected H10 street location, clean tracking/journal state,
present housing status, explain restriction profiles, add compatibility handling
and clean configuration. A short notification is optional; a mandatory
Continue/Main Menu popup is explicitly removed.

## Phase 10 — Release / Long-Term Stability

**Status: integrated alpha planned; entry criteria not yet met.**

### First integrated alpha

This milestone tests a complete installed mod from a real pre-ending world,
not just command overrides in an old post-Tower development save. The complete
task list is [Alpha playtest tasks](docs/alpha_playtest_tasks.md); the existing
[gig checklist](docs/gig_batch_u9_playtest_tasks.md) is its gig component.

14 October 2026 activity follow-up supersedes the visibility-only observations:
the user reports race markers but no start interactions, a single visible NCPD
scanner marker with an empty site, and spawned/idle fixers without interactions.
Record functional failures at tested locations; exact race IDs, NCPD subtype and
fixer names/count were not supplied, so do not extrapolate to every instance.
Inspect stock quest/service activation, native prerequisites and ending cleanup;
missing owners are a hypothesis, not a verified shared cause or a map-filter fix.
NCPD coverage still needs a pre/post-ending state comparison. All cyberpsychos
were completed before Tower: keep this character as a preservation control and
use a separate unfinished/disposable fixture for encounter restoration. Fixer
offices (including Wakako in the inventory) require checks independent of gig
phone/reward support. Details are in the alpha checklist. This result record
does not authorize save/fact changes or claim a runtime repair.

Alpha scope:

- All approved gigs and side/minor jobs, with recorded whitelist/cast/history
  exceptions, original flow, calls, rewards, progression and cleanup.
- Other compatible activity categories: NCPD scanner subtypes, Cyberpsycho
  Sightings/reporting, El Capitán vehicle contracts, Dogtown airdrops, replayable
  races and other native repeatable activities. Audit remaining categories so
  omitted content is explicit rather than assumed covered.
- All previously restored compatible world, service and interaction features,
  including H10, mirrors, vendors/ripperdocs/bars, Afterlife, Zetatech and the
  Misty/Viktor street, media, journal/time recovery and public interactions.
  Verify applicable physical fixer offices/conversations separately from phone
  and gig-owner restoration, preserving native service and reward eligibility.
- Loss and repurchase of all previously owned ordinary apartments, with home-only
  service gating: H10 at €$25,000 and the others at normal prices. Relationship
  homes do not become purchasable. Kerry's house is the sole retained-access
  exception; preserve access without restoring Kerry's excluded story content.
- The completed implant-focused HP150/Body3/closed-Relic profile and existing
  cyberware/perk/smart-targeting restrictions, without duplicate refunds.
- A one-time post-credit arrival on the street in front of H10, genuine 2079
  state, and automatic integrated startup without development Start commands.

Entry criteria: every intended category has an implementation or a specifically
approved exception; native dependencies and phone admission are ready; actual
pre-ending history and automatic dispatch are connected; housing decisions and
implementation are complete; H10 arrival is implemented; the full package passes
compile/deployment checks with a verified backup/recovery path. Do not ask the
user to replay the ending until these prerequisites are ready.

Exit criteria: the pre-ending-to-post-ending path and all required category,
housing, nerf and existing-feature regression groups pass; no unresolved crash,
softlock, wrong activity activation, duplicate owner/reward/charge, lost history
or ending-state regression remains. Record unplayed jobs and nonblocking issues
honestly. Representative gameplay across each distinct owner pattern is required;
completing all 72 gigs is not a prerequisite for beginning alpha or continuing
development, and a representative pass does not certify unplayed jobs.

### End to end deployment path

The release path must pass:

```text
pre-Tower save
→ install the complete alpha build while the game is closed
→ load the pre-ending world and capture real activity/housing history
→ complete Tower naturally
→ credits
→ direct return to gameplay
→ one-time H10 street arrival in the retained 2079 session
→ automatic selective restoration, housing rules and approved profile
→ normal play
→ save
→ quit
→ reload
```

Test ending integrity, sandbox systems, H10 and general interactions, vendors, housing, each restriction profile, representative activities, multiple saves/reloads, longer sessions, combat, police, district travel, Dogtown, apartments, and services.

## Current recommended priority

Updated 12 October 2026. This order supersedes historical next-step instructions.

1. Resolve U9 phone admission using the actual stock lifecycle; preserve completed
   gigs and old owners. Use the audited ManualSave-17 candidate for targeted
   development checks, not ManualSave-20 or an ending replay to hide the problem.
2. Finish broad gig readiness and keep the deferred gig playtest checklist. Carry
   forward native phone, prestate, progression, reward and cleanup dependencies.
3. Expand side jobs from the Only Pain pilot, with per-owner cast/branch review,
   multi-stage dependencies and service/quest ownership handoff where needed.
4. Restore other activity categories as batches. Include remaining compatible
   range/fortune/altar/gig-radio and repeatable features in the coverage audit;
   record incompatible or explicitly deferred exceptions individually.
5. Implement Phase 5 housing and the Phase 2 H10 street arrival; integrate actual
   pre-Tower history, automatic activity dispatch and the approved nerf profile.
6. Package all accepted restorations together and run the Phase 10 integrated
   alpha from a verified pre-ending save, then the category and regression tasks.

Preserve accepted nerf, journal, vendor, mirror, Zetatech, Afterlife and other
world work throughout. Existing bar-idle, coaster-gesture and Lizzie-mirror
deferrals remain named limitations, not silently completed features or removed
implementations. Earlier smoke passes remain evidence; alpha checks their
integration, not an obligation to repeat every historical prototype test.

