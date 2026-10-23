# Integrated alpha playtest tasks

## Final selection baseline

Use [R6 final decisions](whitelist_final_r6.md) and the
[complete catalogue](whitelist_final_r6_catalogue.md): 80 gigs and 78 side jobs
in the broader target. Selection is closed, not a claim that every route is
installed or tested. Older batch inventories below describe their own releases.
New Heroes admission and the fresh Brendan dumpster route must be denied by a
safe successor migration; that enforcement is not installed yet. Preserve
already-issued owners and earned rewards. Do not remove S27/shared Claire support.

## Four side jobs — S28, 23 October 2026

S28 and the explicitly approved Patch 2.5 framework package are installed.
Follow [the S28 playtest notes](sidejobs_s28_playtest.md) for Space Oddity,
Ezekiel Saw the Wheel, The Highwayman and I'm in Love with My Car. Use the same
working post-Tower branch with a new manual test save. Compilation and deployment
checks passed; gameplay, rewards and reload behavior still need observation.
Completed and progressed jobs are protected, not restarted. Hoon's original
crate must be loaded before its fresh-entry check can succeed.

Recovery starts with `prealpha/sidejobs_s28/deploy_02.ps1` and
`recovery/sidejobs_s28_01`, before U10 and older mod packages. Framework recovery
is separate under `recovery/framework_pr63_01`. File rollback is not save rollback.

## Eight-gig regression — U10, 22 October 2026

U10 is installed. Follow [the eight-gig playtest notes](gigs_u10_playtest.md)
on the same working post-Tower branch with a new manual test save. No ending
replay or forced facts are needed. Completed gigs are protection controls;
unstarted gigs still need their native requirements. Unsupported unfinished
stages stay unchanged. Family Heirloom defers when pre-Tower Ghost Town completion
is unknown; current completion alone does not manufacture the missing witness.

Verify native calls, interactive objects, choices and one-time rewards, plus
Psychofan's Johnny presentation, Ladrillo/Greed retaliation and cold reload.
The package passed offline checks; none of these live results is assumed.
Recovery now starts with U10 (`recovery/gigs_u10_01`) before S27 and older packages.

### Prerequisite admission tests

R6.1 is not yet enforced across all installed content. U10 enforces the narrow
Family Heirloom prerequisite boundary; broader runtime enforcement and recursive
dependency coverage remain incomplete. For each affected follow-up test:

- [ ] Required excluded prerequisite completed before Tower with the correct
  outcome: follow-up may enter only if all its other native guards pass.
- [ ] Required excluded prerequisite unfinished, never started, or pre-ending
  completion unknown: follow-up remains blocked; no forced parent completion.
- [ ] An approved prerequisite completed legitimately after Tower can unlock
  its selected successor normally; preserve native AND/OR branch conditions.
- [ ] Existing owners, completed jobs and rewards are preserved without resets.

## Dogtown checkpoint regression — DT1, 17 October 2026

**21 October user result:** "downtown stuff has been restored" in this Dogtown
repair context. Functional user pass recorded; individual lane, deeper-district
wanted and reload items below remain unconfirmed unless separately reported.

User reported the militarized gate would not open during an El Capitán vehicle
contract, and shooting Barghest guards did not produce wanted stars. Source
inspection found that the terminated EP1 open-world graph owns the checkpoint
controller, including its guard/security combat → three-star branch. DT1 adds
one post-Tower bootstrap referencing that original controller directly. It does
not restart EP1, change police rules, or restore story quests. **Installed
17 October at 22:43 local; live tests pending.** Installation and evidence are
recorded in the roadmap and DT1 assessment.

Test the **current working post-Tower branch**, with a separate manual test save;
do not choose an old slot merely by number or replay the ending. Initialization
waits for no combat/no wanted and for V to be outside the checkpoint's native
guard-respawn area. The original Dogtown content streaming trigger is retained.
Start somewhere inside Dogtown, well away from the main checkpoint, close menus
and allow normal gameplay before approaching. No courier abort, quest/fact reset
or forced teleport is part of this repair.

- [ ] Drive normally through the correct checkpoint lane and stop for the stock
  scan. Test both directions, including an El Capitán delivery vehicle.
- [ ] Check pedestrian entry/exit, scanner lights, barriers and guard behavior.
- [ ] Separately, on the disposable branch, test checkpoint guard combat. The
  native controller should escalate to three stars when below three; check
  lockdown and reopening after the chase ends. Do not expect passage in combat.
- [ ] Test wanted response deeper inside Dogtown separately. DT1's source-backed
  repair covers checkpoint escalation, not a proven district-wide defect.
- [ ] Save and cold reload away from the checkpoint; repeat a normal crossing.
  Existing vendors, vehicle contracts, airdrops and scanner activities still work.
- [ ] Fresh-ending integration later: nothing activates during Tower/credits;
  normal post-Tower handoff and restriction profile remain intact.

If startup is unclear, this CET command is read-only:

```lua
local q=Game.GetQuestsSystem(); print("DT1 gate ready/issued="..q:GetFactStr("PTFRDT1_GateReady").."/"..q:GetFactStr("PTFRDT1_GateIssued"))
```

Issued confirms dispatch only, not streaming, live scanning or a successful
crossing. Broader Dogtown utility roots (stadium terminals, summon restrictions,
ambient communities/traffic) were audited but not blindly restarted; they mix
working services and story content or lack a confirmed live defect.

**Separate pre-alpha rehearsal:** the consolidated package has progressed through
PA6; see [the clean-run instructions](pre_alpha_clean_run.md) for version-specific
context. The original PA1 rehearsal used ManualSave-10 in Things Done Changed
with explicit late-ending development admission. That is historical fixture
information, not an instruction to load a slot by name today. Pre-alpha results
do not mark the full-alpha entry checklist or genuine pre-Tower history complete.
Other saves and old PTFR runtimes were recoverably archived, not deleted.

Updated 15 October 2026. **Full alpha planned, not ready to run.** This alpha covers the
complete post-Tower experience, not only the gig batch. It begins with the full
mod installed in a genuine pre-ending world and ends with normal post-ending
play, new saves and cold reloads. Do not replay the ending until the entry
checklist is ready. See [the roadmap](../ROADMAP.md#first-integrated-alpha).

## Latest activity observations — 15 October 2026

**S23 family expansion is installed (16 October, 02:10 UTC); live pending.** The stable
capture covers all 58 whitelist roots. The new package adds the remaining native
families, preserves existing active/completed jobs, resumes Aaron's captured SMS
outcome and offers Skippy's separately confirmed post-mode-conversation route.
It does not prove every possible partial state or all live outcomes. Epistrophy's
earlier initial user pass is retained; remaining cars/reward/reload are unverified.
Follow the [S23 rollout](sidejobs_s23_rollout.md) and
[deferred playtest checklist](sidejobs_s23_playtest.md). Do not replay Tower or
reset native progress/phone facts. Full-alpha history certification remains pending.

**S22.1 installation history (before the initial user pass):** three other S22 journal
entries appeared, but Epistrophy remained blocked by historical phone counts
(main 7/2, sad 0/1) despite matching progress and zero busy flags. Only the added
counter-equality preflight requirements were removed; native cleanup, all 57
busy flags and progress checks remain. No quest/counter resets or new owners.
Test the same post-Tower branch: Epistrophy active with 3/7, unfinished-car
interaction/call, completed cars protected, then new-save/reload. Do not replay
Tower or force phone facts. Recovery starts S22.1 (`recovery/sidejobs_s221_01`)
before S22b. See the [updated checklist](sidejobs_s22_playtest.md).

**Latest policy / S22:** whitelist + Failed **or Inactive** after Tower, with
halfway progress preserved. Future whitelist selection uses Inactive pre-Tower
history, not a fabricated certificate. Four bounded native resume routes are
installed (The Gig, Beat on the Brat, Epistrophy, Moving Heat); other partial
stages and No Easy Way Out are not all implemented. Existing S2 Inactive
admission is repaired without changing its freshness checks. Follow the
[S22 checklist](sidejobs_s22_playtest.md), not the older diagnostic-only step below.
The first S22 install was rolled back before launch for lifecycle hardening;
the reviewed successor installed at 21:10 UTC with hashes/rollback validated,
215 saves and all unrelated package files preserved. Use its recovery instructions.
Actual restored gameplay, payouts, reloads and full ending integration remain pending.

**15 October: S2.1 diagnostic/auth repair installed; Failed replay not implemented.**
The user selected whitelist + Failed after Tower for current development,
preferring resume where reliable and restart otherwise. Future selection is
actually unstarted before Tower, tracked separately. The existing fresh-only
monk test was blocked by missing authorization, not a Failed root. S2.1 adds a
manual read-only inventory for all 58 roots and surviving catalogue-bound progress
data, plus a separate optional fresh-fixture opt-in. No automatic replay/reset.
Full compilation/readback and installation/rollback checks passed; 82 other
package files, 215 saves and five cache/settings files preserved. Next is the
single `FailedDetails()` command in [the S2 notes](sidejobs_s2_playtest.md), not
another ending run. Full Failed restoration and its playtests remain pending.
Recovery starts **S2.1 → S2 → R1 → P1 → D1 → N22 → N21 → C1 → N2 → N1 → FO1 → PA6**.

**Earlier 15 October: S2 first side-job batch installed.** Sacrum Profanum
/ Losing My Religion and Stadium Love passed offline graph, policy, compilation,
resource and deployment tests. Three additive files installed with game closed;
existing mods, saves, settings and caches preserved. Hash and rollback checks
passed; no game launch. Recovery starts **S2**, then R1/P1/D1/N22/N21/C1/N2/N1/
FO1/PA6/older. Johnny's existing voice-only/body-hidden approach
was explicitly approved. [S2 playtest](sidejobs_s2_playtest.md) records the exact
fixture and deferred live checks. Stadium is completed on that fixture and must
not be replayed; all-whitelist restoration and full alpha remain pending.

**R1 repeatable-race interactions: user-reported functional pass (15 October).**
The user reports the test passed using Johnny's car, with no Johnny appearing.
Exact route, all-four-route, payout, voice, repeat and reload coverage remain
separate; basic startup does not need another test just to reconfirm this. Offline
preservation, admission, archive and installer checks passed. See
[the R1 playtest](races_r1_playtest.md). After removing S2, recovery starts with **R1**, then
P1/D1/N22/N21/C1/N2/N1/FO1/PA6/older. No forced unlock or ending replay required.

**Cyberpsycho P1: user-reported functional pass.** All 17 encounter owners are
fresh-only; completed sightings and claimed rewards stay completed normally.
The Lt. Mower/Regina fixture remains an explicit disposable-only test, not a
normal replay feature or genuine fresh-history proof. Do not repeat the basic
test just to reconfirm the user's result. All-17, reward-variant and reload
coverage remain separate. [Earlier P1 instructions](cyberpsycho_p1_playtest.md).

**N2.2 scanners: user-reported visibility/functionality pass. C1 courier:
user-reported functional pass.** Do not repeat basic startup just to reconfirm
these reports. Exhaustive rewards, repeat cycles, new-save/reload and fresh-ending
coverage are not established by them.

**Dogtown airdrops D1: user-reported functional pass.** Exact enemies/crate/loot
coverage, unforced recurrence, and new-save/reload remain unverified. The reported
5/5 cooldown may follow a manual fact test; natural progression is not proven.
No immediate repeat of basic startup is needed. Original controller
and rewards remain native; startup bypasses the one-time introduction. No permanent
all-map marker expectation. See [D1 instructions](airdrop_d1_playtest.md). Recovery
starts with D1, then N22/N21/C1/N2/N1/FO1/PA6. Earlier notes below are historical.

**N2.2 marker-only repair installed; live check pending.** One script replacement
permits native journal activation for an issued, unfinished inactive encounter
without requiring its saved marker record first. Independent terminal guards,
existing owners/archives/table, bounded retries and quiet logging are retained.
Supplemental startup permissions and separately guarded partial-progress cases
are not widened. All 24,576 policy cases, full compilation and 46 deployment
cases/63 checks pass offline. Quick test uses **AutoSave-9, level 48,
14:20:26 on 14.10.2026**, menus closed 20 seconds; no ending replay. See the
[current instructions](ncpd_n2_playtest.md). Recovery **N22 first**, then N21,
C1, N2, N1, FO1, PA6. No new live visibility/completion/reload pass yet.

Earlier result:

**N2.1 citywide visibility failed; one Westbrook encounter works per user.**
Watson looks populated, but WBR/CCT/HEY/STD/PAC still show only one or two markers.
The latest save has 128 N2 startup requests issued and only 24 marker acknowledgements.
The saved-marker prerequisite before journal activation is the leading blocker;
raw save data supports it, but a live getter was not captured. No new patch this
diagnostic turn. Completion/reward/new-save/reload and other previously started
encounters remain unverified. See the [current findings](ncpd_n2_playtest.md).
Recovery remains N21 first, then C1, N2, N1, FO1, PA6 and older. No repeat ending
or current-build map test is needed merely to reconfirm the reported failure.

**Earlier N2 missing-activity diagnosis, confirmed by the user's pre-ending comparison.**
All 154 additions loaded, but source audit found phase-only map startup after
Tower had deactivated POI entries. Fresh-only admission also excludes some
started-but-unfinished scanners. Investigation only; no fix installed yet.
See the [current N2 findings](ncpd_n2_playtest.md). Do not mark citywide restoration
passed or request another full playthrough to establish the same missing icons.

**C1 courier restoration installed; live test pending.** The user deferred N2
testing and requested El Capitán vehicle contracts next. Original courier
controller and native story gates are retained, with Daniels phone support for
the later mission. No completed-story replay, partial contract migration,
custom payout, global phone restart or console polling. Johnny remains
voice-only. Use the [deferred courier checklist](courier_c1_playtest.md) for
vehicles, calls, delivery variants, payout, next opportunity, new-save/reload,
onboarding and later-story coverage. The existing AutoSave-8 fixture is usable;
no ending replay is required. Offline checks are not a gameplay pass.
This C1 installation's earlier recovery order is superseded by N21 first above.

**Earlier installation baseline: N1 functional PASS; N2 now has the regression above.**
The user says the activities work, without specifying completion/call/reload
coverage. N2 adds154 stock-connected owners to the unchanged three pilots,
covering157 scanner POIs across seven regions. Original gameplay, gates,
dispatcher,rewards and cleanup are used. No completed scanner/cyberpsycho reset
or partially completed encounter migration. Two factless-start owners query
saved native POI state; unknown safely waits. Four unwired journal entries are
not activated. Catalog count is not an expected number of new icons.
Use the [N2 test instructions](ncpd_n2_playtest.md): cold launch **AutoSave-8,
level48,12:10:04,14.10.2026**. No ending replay. Citywide content, representative
completion,phone coexistence and new-save/reload remain unverified.
Recovery order is now **N2 first**, then N1,FO1,PA6 and older transactions.

**FO1: Wakako interaction PASS, user-reported14 October.** The user confirms it
works and matches their pre-ending world comparison. The screenshot shows the
normal talk prompt and two dialogue choices. Other six offices remain untested;
new-save/reload and separate exit/revisit coverage were not specified.
Seven post-handoff native default owners are now included: Wakako, Regina, Padre,
Dino, Dakota, El Capitán and Mr. Hands. No races, scanner encounters, side jobs,
cyberpsycho resets or gig starts are added. Original dialogue and availability
checks remain. The package adds no polling script or console output.

Original small test procedure (basic Wakako interaction now passed; no need to
repeat that check solely for confirmation, and no ending replay is requested):

1. Cold launch and load the current post-Tower test save. The checked fixture is
   **AutoSave-5, level48, 10:20:26 on14.10.2026**; identify it by timestamp, not
   merely the reusable slot name. It has finished handoff and existing phone
   support. Do not load an old pre-alpha developer snapshot for this check.
2. Close menus, holster and visit Wakako's office. Confirm the normal talk prompt
   and conversation, then exit normally. Do not complete a gig just to test this.
3. Leave the office, return and check the conversation again.
4. Make a **new** save, reload it and repeat the interaction. Keep the earlier
   fixture unchanged. There should be no added console chatter or duplicate NPC.

If no prompt, this optional CET command is read-only (issued1 is not proof that
a scene actually ran):

```lua
local q=Game.GetQuestsSystem(); print("FO1 Wakako ready/issued/default="..q:GetFactStr("PTFRFO1_wakako_Ready").."/"..q:GetFactStr("PTFRFO1_wakako_Issued").."/"..q:GetFactStr("wakako_default_on"))
```

- [x] Wakako: basic interaction works; user compared behavior against pre-ending
  world. Screenshot corroborates prompt and dialogue options.
- [ ] Wakako: separately confirmed exit, leave/return and new-save/reload.
- [ ] Other six fixers: normal office conversation and clean exit, retaining
  stock eligibility. A legitimately disabled native gate is not a forced unlock.
- [ ] Regina: existing cyberpsycho reporting/reward state stays intact; no
  repeated claimed reward, respawn or renewed completed encounter.
- [ ] Original gig briefing/debrief calls still work; default calls do not create
  concurrent/duplicate phone ownership.
- [ ] Fresh ending integration later: no office activation during Tower/credits;
  normal office availability after handoff. Do not repeat the ending now.

Evidence: `research/fixer_offices_fo1/assessment.json` and the separate
`research/fixer_offices_fo1/live_result_20261014.json`. Offline graph/packaging and
29 installer cases/39 checks pass; live confirmation is limited to Wakako above. Recovery
must remove N1 first, then FO1 using its own transaction before PA6 or older rollback.

User-reported observations below are not a fresh log/save audit or gameplay pass.
No new ending run, forced unlock or completed-encounter reset is requested here.

- **Races: start interaction FAIL (user-reported).** On 13 October the user
  reported all race markers visible; on 14 October they report no interactions
  at the race marker(s) visited. Exact routes and number of visited locations
  were not supplied; do not claim every route was tested. Marker visibility is
  not a working-race pass. Identify the visited locations and inspect native
  unlocks, start-interaction and race-owner state before adding restoration.
  After repair, exercise a representative race through start, opponents/checkpoints, finish,
  payout, cleanup, repeat availability and new-save/reload. Test abort separately
  on a disposable branch. Do not restart an already functioning race controller
  merely to make the restoration batch uniform. A representative pass does not
  certify every route or establish whether the current markers came from the mod.
- **NCPD: historical empty encounter report; N1 now user-reported working.**
  Before N1, the user saw one scanner marker versus many pre-ending and reported
  the marked location empty. N2 citywide expansion still needs coverage checks.
  The original marker ID/subtype, completion history and actual
  runtime owner state are not yet established. Identify that activity and compare
  the same character's preserved pre-ending unfinished encounters against the
  post-ending state, using matching map filters, extent and zoom. Distinguish
  hidden markers from inactive encounters and legitimate completed exclusions;
  do not assume one visible marker means only one functioning encounter. Test
  all three scanner subtypes and preserve completed controls.
- **Cyberpsychos: completed-state preservation REQUIRED.** User completed all
  sightings before Tower. This character is the negative control: no respawn,
  renewed objectives/report requests, duplicate payout or repeated counter credit.
  Record reporting and final-reward states separately; all encounters completed
  does not establish whether every report/reward was already claimed. Test
  unfinished restoration on a separate fixture as described in section E.
- **Fixer offices: Wakako interaction FAIL (user-reported, before FO1).** User
  confirms Wakako was visited, spawned and idling without interaction; other
  offices are suspected, not confirmed failures. Gig calls, markers,
  rewards and a working phone controller do not certify the physical location,
  actor or conversation. Add office/hangout visits to gig-service regression,
  preserving each fixer's native eligibility and story outcomes. Do not invent
  a trade/service interaction for a fixer who does not normally offer one.

Historical next diagnostic target (fixer comparison now implemented as FO1): compare stock native activation paths with current
restoration for race start interactions, NCPD encounter content and fixer ambient
conversations. Visible markers/actors with missing functions are consistent with
missing or blocked quest/service owners, but do not prove that mechanism or a
single shared cause. Inspect native prerequisites and ending cleanup before
choosing a repair; do not reset completed encounters or rebuild map markers as
an assumed solution. Finish/reward/repeat/reload checks remain untested for these
reported failures. No runtime, save or fact changes accompany this test record.

## Scope and exceptions

Include every approved gig and side/minor job, all compatible other activity
categories, all previously restored compatible world/services, H10 repurchase,
the accepted nerf profile and arrival on the street in front of H10.

- Gigs retain their audited pre-Tower freshness rule. Missing history is not
  freshness. Side jobs follow the later target: completed stays completed,
  unfinished restarts once, never-started begins natively. General unfinished
  restart migration is not implemented; no blanket reset or duplicate payout.
- Supporting Johnny voice and scene timing remain; his projection does not.
  Exclude Johnny-central/takeover/Relic-dependent jobs and jobs with Panam,
  Kerry, Judy or Misty as live participants, including optional calls/messages.
- Original unlocks, cast outcomes, tiers, transactions, rewards and cleanup
  remain. Body 3/HP 150 difficulty or an unusable reward is not an exclusion.
- Other activity categories are restored as batches outside the quest/gig
  whitelist. Preserve their native one-time versus repeatable behavior; do not
  reactivate completed one-time encounters to make the map look populated.
- All previously owned ordinary apartments require repurchase after Tower. H10
  costs **€$25,000** (2× a mod-defined €$12,500 reference price); the others
  retain normal purchase prices without an increase. Never-owned apartments
  retain normal purchase rules. Relationship homes follow Tower outcomes and
  are not for sale. **Kerry's house is the only retained-home exception**:
  preserve V's existing access without removal or repurchase, not Kerry's
  quests, romance or live participation (user revision 2026-10-21).
- Keep an explicit exception register: activity/feature, reason, implementation
  state and test status. Existing bar-idle, coaster-gesture and Lizzie-mirror
  deferrals stay visible; an omitted category cannot silently become an exception.

## Entry checklist

- [ ] Full gig startup and shared phone dependencies work on a suitable fixture.
- [ ] Side-job coverage has expanded beyond Only Pain, including multi-stage,
  phone/message, shared-service and follow-up owners as applicable.
- [ ] NCPD, cyberpsychos, vehicle contracts, airdrops and repeatables have category
  implementations and explicit native eligibility/exception inventories.
- [ ] Actual pre-Tower activity history capture and boundary freeze are connected
  to automatic production admission. Development assumptions stay separate.
- [ ] Ordinary-apartment entitlement loss and repurchase are implemented: H10
  for €$25,000, other previously owned apartments at normal prices. H10's mod
  price is not a vanilla purchase or renovation fee.
- [ ] Kerry's house access is explicitly preserved as the sole home-removal
  exception, independently of ordinary apartment purchase state; no Kerry
  quest/romance completion or NPC restoration is used to grant access.
- [ ] One-time H10 street placement is implemented and its landing point verified.
- [ ] The selected, already accepted nerf profile is wired into the approved
  production startup/configuration, without development activation commands.
- [ ] Previously restored features are included in the full package, with one
  compatible owner per feature and no obsolete experimental controller overlap.
- [ ] Complete package compilation, registration, dependency, install/readback
  and recoverable file-rollback checks pass. Preserve original save snapshots.
- [ ] Record the exact pre-ending save slot, timestamp, level and hash after
  verifying its state. Do not invent a slot from an earlier post-Tower fixture.

ManualSave-17 (level 48, 21:02:06, 25.09.2026) is only a post-Tower development
candidate. Its old phone counter mismatch still needs review. ManualSave-20 is
not suitable for U9. Neither is the pre-ending fixture for this alpha.

## Test record

Record build/receipt, game/framework versions, configuration, exact source save,
each new slot/time, and logs/screenshots. Use `PASS`, `FAIL`, `UNTESTED`, or
`EXPECTED EXCLUSION` with a reason. Installation and a visible marker are not
gameplay passes. Keep per-job untested cases even after a representative passes.

## A Full deployment from the pre-ending world

1. Preserve the chosen pre-ending save. Close the game, install the complete
   alpha package, verify its receipt, then cold-launch and load that exact save.
2. Confirm the normal pre-ending world still works: no early nerf/refunds,
   housing loss, H10 teleport or post-ending restoration owners.
3. Record examples of unstarted, started, completed and genuinely failed jobs,
   plus apartment ownership, money, profile/perks and relevant unlocks. Verify
   captured history is save-local and does not fabricate absent observations.
4. Make a new pre-ending checkpoint and reload it. Capture survives; it still
   tracks legitimate pre-ending changes until the real ending boundary.
5. Complete Tower normally. Watch credits on the main branch; test skipping them
   on a separate branch from the preserved pre-ending checkpoint.
6. Verify genuine Tower/2079 and relationship outcomes, no PONR rollback, normal
   final-board teardown and automatic restoration without `StartAll`/fact setters.

## B H10 street arrival and ending cleanup

- [ ] V appears on safe street-level footing in front of H10, with working
  collision, world streaming, camera, movement, HUD and normal time progression.
- [ ] Arrival happens after ending/credit control releases, never inside the
  apartment, a wall, traffic lane, scene/workspot or unstreamed void.
- [ ] H10 is not granted merely by arrival; other previously owned ordinary
  apartments also require repurchase before their home services become available.
- [ ] Tower history remains completed, stale Tower tracking is cleared and an
  empty journal has the correct generic label without deleting other history.
- [ ] Save at another location, quit and reload: no return teleport to H10.
- [ ] Death/checkpoint reload and repeated loads do not repeat handoff, housing
  reset, refunds, owner initialization or payouts. Test a pending-handoff reload
  separately: it completes once, not zero times or twice.

## C Gig playtest

Use [the detailed gig checklist](gig_batch_u9_playtest_tasks.md) for representative
routes, phone recovery, prestates, tiers, rewards, cleanup and reload. Its old
development override is not used to pass the automatic alpha startup test.

- [ ] All intended entries have an implementation and an admission result.
- [ ] Sample available gigs across fixers/regions and distinct native patterns,
  including Dogtown. Original tiers may legitimately defer later gigs.
- [ ] Approach/briefing creates the expected journal objectives; Gigs filter is
  on. Map registration alone is not proof of a rendered marker or working owner.
- [ ] Complete representative objectives, receive actual native calls/payouts,
  credit where stock supplies it, leave, and verify cleanup and reload.
- [ ] Fresh captured jobs restore; prior started/completed/failed and excluded
  jobs do not restart. A job begun after Tower resumes correctly after reload.
- [ ] Supporting Johnny is audible but invisible, without awkward scene stalls.
- [ ] Physical fixer offices/hangouts are checked separately from gig phone
  support: begin with Wakako, then cover other applicable fixers. Verify access,
  actor presence, conversation entry/exit, currently eligible native choices and
  any stock service/reward handoff actually offered there. No stuck camera/input,
  duplicate actor, premature or repeated reward. Revisit after a new-save/reload.
  Record unavailable stock-gated choices as such, not automatically as defects.

## D Side-job playtest

- [ ] Inventory the full selected side-job set and explicit exceptions; a gig
  graph pattern or the Only Pain pass does not certify every side-job owner.
- [ ] Test a local encounter, a phone/message-initiated job, a multi-stage or
  chained job, and a shared vendor/service takeover where the whitelist permits.
- [ ] Check optional branches and full cast, native timing, objectives, choices,
  rewards, follow-up availability, cleanup and service return after the quest.
- [ ] Save/reload during and after a representative job; no duplicated dialogue,
  actors, rewards or lost stage. Verify captured freshness and excluded history.
- [ ] Include compatible final fixer reward jobs in the side-job inventory;
  legitimately earned rewards must neither disappear nor be granted prematurely.

## E Other activity playtests

Restore each category as a batch; test its individual state preservation and
representative lifecycle. Category-wide restoration does not mean forced unlocks.

| Category | Required checks |
| --- | --- |
| NCPD scanner | Assault in Progress, Reported Crime/follow-up, Suspected Organized Crime; enemies/evidence/loot, completion, marker removal, reload and completed controls |
| Cyberpsycho Sightings | Encounter, original survival/outcome logic, reporting/reward chain, completion/cleanup and reload; preserve prior completed sightings |
| El Capitán vehicle contracts | One-time onboarding eligibility separately from the repeatable theft/delivery loop, calls, vehicle spawning, objectives, rewards, next contract and reload |
| Dogtown airdrops | Native scheduling/unlocks, encounter, loot, cleanup, later legitimate event and reload; no repeated one-time payout |
| Races and other repeatable activities | Original unlock, start, finish/abort, reward, cooldown/repeat, cleanup and reload; distinguish story race from repeatable race |
| Remaining compatible public activities | Audit range, fortune-telling, altar, gig-radio, arcades and other authored interactables; record coverage or a specific exception, not an assumed blanket pass |

The user's current character completed the cyberpsychos. Prefer a genuinely
unfinished fixture for the positive restoration test; separately keep the
completed character as the preservation control, including after save/reload.
Do not reset all sightings or Regina's aggregate reporting/reward state to make
markers appear. If a temporary fact-based test is used, use a separate
disposable branch, record and restore exact original values, and verify outcomes,
rewards and reload. Restoring a fact may not undo a running graph or paid reward;
discard the experimental branch and reload its untouched source when necessary.

## F Apartment repurchase

- [ ] Every previously owned ordinary apartment loses home entitlement once
  after Tower; geometry/public access remain separate. Shared stash contents
  and inventory are not erased.
- [ ] Purchase is reachable without already owning H10 or accessing a locked
  home-only computer. Display the final **€$25,000** price clearly.
- [ ] Insufficient funds and cancellation grant nothing and charge nothing.
- [ ] Successful repurchase charges once and restores the correct marker,
  access, stash, bed, shower, wardrobe, mirror, sofa/TV and home services.
- [ ] Repeated interaction, reload and death/checkpoint reload neither recharge
  nor revoke H10; home-only prompts do not bypass ownership before purchase.
- [ ] Each other previously owned ordinary apartment is repurchasable at its
  normal price, with no increase; its owned marker and home services return only
  after payment. Insufficient funds, cancellation, repeated interaction and
  save/reload never create a duplicate charge. Never-owned homes retain native
  prices/unlocks. Relationship homes are not sold or revived.
- [ ] Kerry's house retains the access V had before Tower, with no removal,
  purchase offer or fee. Verify entrance/exit after handoff, death/checkpoint
  reload and cold reload, plus appropriate already-earned services.
- [ ] The Kerry-house exception does not spawn Kerry, reactivate his quests,
  invent romance facts, or grant unrelated relationship homes. Public building
  access and preserved shared stash contents are not mistaken for ownership.

## G Completed nerf profile regression

The nerf design is done, including the confirmed HP checkpoint fix. These are
integration checks, not another profile redesign.

- [ ] Approved implant-focused profile: maximum HP150, Body3, all Body perks
  blocked, Relic closed, reviewed cyberware/perk whitelist and no smart targeting.
- [ ] Refund only purchased forbidden ranks once; preserve other progression,
  inventory and approved cosmetic tattoos. Allowed ordinary blade/movement perks
  remain available under their native prerequisites.
- [ ] HP persists after death/checkpoint reload, cold reload and relevant buff
  changes without stacking modifiers or unintended healing. No direct stamina
  override is introduced.
- [ ] Incompatible loot may be collected without enabling forbidden equipment;
  native quest interactions such as the approved Personal Link still work.
- [ ] Loading another pre-Tower save does not carry over restrictions or history.

## H Previously restored content regression

Build the full-package feature inventory from installed receipts and the
[restoration checklist](../research/restoration_checklist.md), using newer dated
evidence where that checklist is stale. Carry forward every accepted restoration;
test one representative of each distinct owner/service pattern plus known risks.

- [ ] H10 architecture and previously restored interactions, gated by repurchase.
- [ ] Public/world mirrors, compatible ordinary and special vendors, ripperdocs,
  bars, native refusal/stock gates, repeat Trade and quest-to-service handoff.
- [ ] Afterlife accepted population, Claire/Emmerick/Rogue behavior and removed
  holograms/dancers; Zetatech and Misty/Viktor world/access/street restorations.
- [ ] TV/radio/media, memorials, dancing, stable coaster and other existing public
  interactions; no return of ending-only or Johnny-central staging.
- [ ] Journal, time, fast travel, elevators, vehicles, traffic/pedestrians,
  combat/police, district/Dogtown travel, saving and restored services coexist.
- [ ] Return visits, cold reload and longer mixed-activity sessions produce no
  duplicate owner, stuck scene/phone, missing collision or unexplained load crash.

## Completion and follow-up

Alpha passes only after required integration groups pass and critical defects
are fixed/retested. Record exact failed steps, source/new save identifiers and
logs. Report crashes separately from assumed causes. Unplayed jobs remain
untested; a full 72-gig playthrough is not required to start alpha or continue
development. Preserve explicit nonblocking limitations for later polish/release.

File rollback does not rewind a newly saved game world. Keep the original
pre-ending fixture and use new manual slots for every experimental branch.

