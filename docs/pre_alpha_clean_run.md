# Pre-alpha handoff and graphics checks

## Current follow-up — N2 citywide scanners, 14 October 2026

The user reports N1 activities work; exact completion/call/reload coverage was
not specified. N2 is installed additively:154 additional native scanner owners,
157 total with N1, across all seven regions. Native gates/rewards/cleanup stay;
completed, started and cyberpsycho progress is not reset. Partial-progress and
certified pre-Tower history restoration remain outside this batch. The expansion
is offline-verified but not yet gameplay-verified.

Use **AutoSave-8,level48,12:10:04,14.10.2026** for the
[short N2 test and deferred checklist](ncpd_n2_playtest.md). Cold launch; enable
the NCPD Scanner map filter and check several districts plus actual content.
No ending replay, forced facts or StartAll. The existing active N1 owner must
continue. Keep the byte-exact backup in `recovery/ncpd_n2_fixture_20261014`.

Recovery starts with N2's deployer and `recovery/ncpd_scanners_n2_01`, then N1,
FO1,PA6 and older transactions. Three additions,zero replacements;659 protected
files unchanged including209 save files,5 caches and settings. No game launch.
N2 build/test/deployment tools and receipts are pinned.

## Historical follow-up — N1 scanner pilot installation, 14 October 2026

N1 is installed over FO1+PA6+GD2. It restores three fresh-only Little China
scanner owners, one per subtype, using original gameplay, dispatcher calls,
rewards and cleanup. No completed cyberpsycho or scanner reset. This is not all
scanner activity and is not yet gameplay-verified.

Use **AutoSave-6, level48,11:14:31,14.10.2026** for the
[short scanner test and full checklist](ncpd_n1_playtest.md). Cold launch; no ending
replay or forced facts. Enable the NCPD Scanner map filter and verify actual
enemies/evidence, not just icons. Earlier FO1/PA6 fixtures below are historical.

Recovery now starts with N1's deployer and `recovery/ncpd_scanner_n1_01`, then
FO1, PA6 and older transactions. Two additions; all657 protected files unchanged,
including209 saves,5 caches, settings and the previously installed mods. N1
build/test/deployment evidence is pinned. No game launch performed by the agent.

## Current follow-up — FO1 fixer offices, 14 October 2026

FO1 is installed on top of PA6+GD2. It restores seven native fixer default
conversation owners without changing the existing camera/H10/gig work. Wakako
was the confirmed failed office before this patch. The user now reports her
interaction works and matches their pre-ending comparison; the screenshot shows
available dialogue choices. Other offices, exit/revisit and new-save/reload
coverage remain unverified. Preserve the working patch; do not repeat the basic
Wakako check merely for confirmation.
See the [short office playtest](alpha_playtest_tasks.md#latest-activity-observations--14-october-2026).
Use the current post-Tower test save; no ending replay or StartAll is needed.
The checked fixture is AutoSave-5, level48,10:20:26,14.10.2026, not the historical
AutoSave-0 below. The user did not identify the exact slot used in the passing
report; no game launch or gameplay test has been performed by the agent.

Recovery order now starts with `prealpha/fixer_offices_fo1/deploy.ps1`
ValidateRollback/Rollback and `recovery/fixer_offices_fo1_01`, then PA6 and older
transactions. Two FO1 additions are recoverable; all59 previous package files,
GD2,209 save files, settings and5 cache files were preserved.

## PA6 installed — Rogue crash, H10 actions and quiet console

Latest user result after a pre-ending load and credits skip: **camera fixed,
H10 furniture restored, Emmerick and Claire working, four gig markers visible**.
H10 interactions were missing, and approaching Rogue crashed. These are individual
reported checks, not full-world or new-save persistence passes.

The latest logs were preserved and inspected before making changes:

- Camera/handoff completed without faults. Four main gig POIs were active,
  consistent with the reported four icons. No new gig changes are needed here.
- H10 geometry was acknowledged, but action permission was still off in the
  street/elevator samples. Those logs end before the apartment; they do not prove
  the exact later cause of every missing prompt. PA6 allows safe offsite arming,
  keeping all30 old fact guards and the native inside-apartment/no-incoming-call
  scene gate. Fresh preparation waits for permission, not an active indoor scene.
- Rogue's dump shows lipsync index2 requested from a two-slot table, leading to
  an invalid memory write. This is **not the earlier OOM crash**. A single-scene
  patch removes an unused duplicate reference and rebases V2→1. All47 scene
  nodes, dialogue/audio, actors and workspots remain unchanged. Actual stability
  and lip animation delivery still need a live check.
- Most CET spam was the PA5 diagnostic trace continuing after success, plus
  verbose per-gig status logging. PA6 disables automatic verbose output and keeps
  manual getters and once-only transition/optics fault warnings. Other mods'
  messages, including FactFinder's `Day ... fact -> value` lines, are untouched.

### Short test — no ending replay needed

1. Cold-launch and load **AutoSave-0 — level48,21:08:28,13.10.2026**. This is the
   latest Afterlife-approach checkpoint,27 seconds before the crash report, and
   byte-identical to its attached save. Preserve it as the pre-patch fixture.
   SHA256: `5204FB67C16A8E5988A7948C10B52D53BC6DA850DECEE44CC56156FFA24C2FD9`.
2. Stand safely outside, holster and close menus/CET for10 seconds. Routine PA5
   transition/map walls of text should no longer appear. Camera should stay normal.
3. Check H10 permission once:

   ```lua
   print(GetMod("PTFR_PreAlpha").H10())
   ```

   Expect `geometryAcknowledged=true`, `actionsArmed=true`; actions Ready/Enabled
   should be1/1 and Interrupted0. Active0 **outside** the apartment is normal.
4. Approach Rogue, allow the usual interaction and try a short conversation.
   No forced scene-start commands or fact changes. If it crashes again, stop and
   preserve the new report; a source correction is not a live stability guarantee.
5. Visit V's H10 apartment and test the previously restored interaction prompts.
   If missing, print `H10()` **while inside**. Enabled1 means permission, not proof
   that a prompt has appeared. Public-building geometry and apartment repurchase
   rules remain separate scope.
6. After success, make a **new separate manual save**, reload and verify camera,
   interaction permission/prompts and quiet logging, with no repeated transfer or
   duplicate owners. Fresh-ending integration is a later check, not required first.

Only if more logs are needed, opt into a bounded read-only trace:

```lua
print(GetMod("PTFR_PreAlpha").Trace(60))
print(GetMod("PTFR_PreAlpha").TraceStop())
```

Use the first to capture60 real seconds; the second stops early. Neither is
needed for normal restoration. Existing `Status()`, `Optics()` and
`GigVisibility()` remain manual read-only diagnostics. Do not repeat StartAll.

### PA6 verification and current recovery

Combined compilation/readback and96 integration checks passed; component checks:
29 Rogue,99 H10,51 logging. Deployment fixtures passed51 cases/86 checks, including
interrupted-copy recovery, archive-inventory drift and later user-mod preservation.
Installed three backed-up script replacements and one single-scene archive;
all59 package hashes and651 protected entries verified, including209 savefiles
and five cachefiles. Main restoration/PA5 optics/GD2 archives, settings and saves
are unchanged. No game launch was performed. Native gameplay remains unverified.

Build: `prealpha/postending_pa6/build/pa6_02`, SHA256
`BE71C5AC4D2F9267AFD97DE65B85136033427A2EEAEB42B505A833853004A299`.
Assessment: `research/postending_pa6/assessment.json`; receipt:
`recovery/postending_pa6_01/install_receipt.json`. Source/build/tools/tests pinned.

With game closed, **PA6 recovery must run FIRST** (PowerShell7):

```powershell
& 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\postending_pa6\tools\deploy.ps1' -Mode ValidateRollback -RecoveryRoot 'C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\postending_pa6_01'
& 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\postending_pa6\tools\deploy.ps1' -Mode Rollback -RecoveryRoot 'C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\postending_pa6_01'
```

This returns to PA5+GD2; only then use the historical PA5 recovery below. Removing
the patch does not undo saved gameplay state. Use the kept pre-patch save if rolling
back. No other mod or user-created load-order file is removed by this recovery.

## PA5 installed — short camera/H10 check, then gig visibility evidence

Installed 13 October local time (14 October 00:25 UTC). Camera/H10 changes passed
offline checks but have **not been verified in game**. The main restoration archive,
working GD2 darkness fix, nerf profile and existing gig graphs are unchanged.

What changed:

- **Camera:** one guarded stock player-camera FOV/DOF reset after PA4 handback.
  It does not force FOV 51/100, disable DOF globally, reset settings, or save/reload.
  Retained cinematic optics is still a hypothesis; the playtest must verify the view.
- **H10:** the existing five apartment geometry owners can start safely from the
  street/offsite position, not only the old upstairs test corridor. Fresh ending
  preparation waits for their native acknowledgements. Existing action prompts
  still start near the apartment. This repairs activation of prior apartment work;
  it does not establish that the entire public lobby/atrium was previously restored.
- **Gigs:** additional read-only POI/mappin diagnostics, **not a confirmed visibility
  repair**. No forced stock tiers, completion credit, journal activation or owner
  restarts. Some stock tier waits are expected; the reported one-icon discrepancy
  remains to be measured.

### First test — no ending replay or gig completion needed

1. Cold-launch the game and load **AutoSave-19, level 48, 19:31:18, 13.10.2026**.
   This is the existing post-ending street save, not an earlier crowd checkpoint.
   Its unchanged `sav.dat` SHA256 is
   `F63366A9CE209E8BD599D46B0DDB381A4196E90DCF76C0CDACEA17F468E8499C`.
2. Stay at street level, holster, close CET/menus and stay out of combat for
   **30–45 real seconds**. The optical reset is brief; H10 acquisition is sequential.
   No repeat teleport should happen. Check walking, mouse-look, zoom and focus.
3. Print these individually, then close CET again:

   ```lua
   print(GetMod("PTFR_PreAlpha").Optics())
   print(GetMod("PTFR_PreAlpha").H10())
   print(GetMod("PTFR_PreAlpha").GigVisibility())
   ```

   Optical success expects `owner/request/issued/out/done=1/1/1/1/1`, `fault=0`
   and `aligned=true`. It does **not** prove normal visual DOF. H10 expects
   `geometryAcknowledged=true`, each geometry Claimed/Entered=1 and Hold/Rejected=0.
   Action activation may remain off until the apartment is approached.
4. Visit H10 and check the previously restored apartment floor, rooms, collision
   and interactions. If the **public building interior** is still absent while
   geometry is acknowledged, capture that location separately; this patch must
   not be treated as a proven whole-building reconstruction.
5. Enable the map's Gigs filter. Report which markers are visible along with
   `GigVisibility()` output. The earlier run reached Fifth Column, Life's Work,
   Jeopardy and Tyger and Vulture main owners; that is not proof all four render.
   Do not rerun StartAll, change tier/visited facts or restart a gig for this check.

If a fault appears, capture these outputs before reloading or applying any manual
camera command. The one-shot repair does not automatically retry a fault. The
bounded automatic trace also records optics/H10/gig state in `PTFR_PreAlpha.log`.

### Later regression checks

- After visible success, create a **new separate save**, reload it and verify no
  repeated reset/teleport/refunds or duplicated H10 owners, with normal optics and
  apartment interactions retained. Preserve the original AutoSave-19 fixture.
- A continuous ending run, with watched/skipped credits, must later verify fresh
  preparation, movement, optics, H10 acknowledgements and unchanged HP150/Body3.
- Save-during-reset recovery, full gig playtests and whole-building visuals are
  not marked passed by source models or native acknowledgements.

### Evidence and recovery

Build: `prealpha/postending_pa5/build/pa5_03`; build SHA256
`5638C911EE19D89EEDB14B3FBF824B51B358E390D05AA7C63203E1F5E06900CA`.
Full combined compilation/readback and135 integration checks passed; camera67,
H10 158 and gig22 component checks passed. Deployment fixtures passed53 cases/
98 checks. Four backed-up replacements and five additions installed; all58
package hashes and635 protected entries verified, including200 savefiles and
five cachefiles. Settings and GD2 remain unchanged. No game launch was performed.

Current recovery is **PA5 first**, with the game closed:

```powershell
& 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\postending_pa5\tools\deploy.ps1' -Mode ValidateRollback -RecoveryRoot 'C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\postending_pa5_01'
& 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\postending_pa5\tools\deploy.ps1' -Mode Rollback -RecoveryRoot 'C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\postending_pa5_01'
```

Run those in PowerShell7. PA5 rollback returns to PA4+GD2; their previous
recovery procedures apply only afterwards. It does not roll back game-world
progress; use the preserved pre-PA5 save if rolling back. New PA5 build/source/
tools/tests/reports are now pinned; do not rerun their mains or overwrite evidence.
Assessment: `research/postending_pa5/assessment.json`; actual installation receipt:
`recovery/postending_pa5_01/install_receipt.json`.

## Current regression report — optics, missing H10 interior and gig visibility

13 October, latest 19:16–19:35 run: the user reports a zoomed/shallow-focus
post-ending view, only Jeopardy visible on the map, and none of the earlier H10
restoration visible. **H10 means the building interior, not a purchase offer.**
The missing physical restoration is not an intended apartment-repurchase lock.

Read-only findings:

- **Camera:** PA4 returned the player-following camera and all six handoff flags
  reached 1 with fault 0. Its check validates position/direction only, not FOV,
  zoom or depth of field. Stored FOV 100 and DOF enabled are unchanged. Native
  credits scenes contain player-camera FOV/DOF resets on their normal exit paths;
  a retained optical override after skip is a candidate, not a confirmed cause.
- **H10:** the old geometry/interaction resources and automatic driver are
  included: all 24 resources from the six frozen H10 archives are byte-identical,
  as is the baseline startup driver. Earlier verified scope was V's apartment
  geometry/interactions, not the entire public lobby/atrium/elevators; retain the
  user's building-interior report without assuming that broader scope passed.
  AutoSave-19 records all six H10 Ready flags and baseline Ready, but
  no acquisition/enable acknowledgements. The geometry driver still requires
  the old upstairs corridor rather than the new street arrival. Handoff success
  does not wait for H10. Exact live blocking predicates remain unmeasured;
  missing serialized facts are not asserted to equal live zero. The separate
  €$25,000 repurchase system remains unimplemented.
- **Gigs:** all 72 entries were considered: 53 requests accepted, 10 refused for
  unsupported entry state, nine terminal outcomes preserved. The captured run
  reached 51 parent entries but only four main entries: Fifth Column, Life's
  Work, Jeopardy, and Tyger and Vulture. Map wrappers entered for those four;
  that does not prove rendered icons. Their native POI activation precedes main
  entry, so absent visited facts alone do not explain the reported visibility.
  No global phone-idle or legacy-owner refusal was found in this run.

Keep GD2's reported darkness fix and PA4's input/spawn pass, separately from the
new optics failure. No new patch, launch, save edit or settings/cache change was
made for this diagnosis. Do not replay the entire ending or force H10 ownership,
gig tiers or completion facts merely to investigate these gaps.

Evidence: `research/post_ending_regression_20261013/` (camera/H10/gig assessments,
frozen logs/settings and read-only AutoSave-19 samples). Use `gigs_probe_v2.json`;
the retained draft v1 had incorrect grouped summary counts. Current AutoSave-18
has been overwritten and is not the earlier 13:16 checkpoint by slot name alone.

## Latest result — user reports graphics problem resolved

13 October: after GD2 installation and the stock comparison, the user reports
**“the problem is gone now.”** Record the graphics result as **user-reported PASS**
and retain GD2 alongside the already-working PA4 camera/spawn fix. No immediate
repeat ending run or vanilla comparison is needed merely to reconfirm this report.

This supports GD2's practical benefit, not a proven effect leak or mod-caused
regression. The user did not restate the loaded slot, continuous/no-reload path,
map/post-credits coverage or new-save persistence; do not infer those individual
checks or full-alpha completion. The stock loop and causal uncertainty remain as
documented below. No runtime, save, settings or cache change was made to record
this result. Historical build/install reports retain their original pending status.

Evidence: `research/graphics_investigation_20261013/gd2_live_result.json`.

## Latest investigation — stock comparison did not verify the cause

Read-only comparison of **14 local official archives and 69 installed mod
archives**, covering **57 relevant resource keys**, found no replacement of the
native thugs/Misty/crowd scenes, their phases, parent q307 flow or normal cleanup.
The two existing ending-board replacements preserve every original node payload
and the stock skip/scene-cut routing. Their behavioral changes concern credits
and the post-credits return, not the reported stand-up onset.

The suspicious injury-effect loop **is stock data**. GD2 deliberately removes it;
that makes GD2 an unverified workaround candidate, not a demonstrated repair of
a mod-created difference. The original scene data does not separately bake that
loop, but actual resource use and effect execution still have not been measured.

The injection/streaming audit found no direct q307 scene injection. All 26 custom
visual/workspot descriptors are default-off, with empty unguarded base ranges;
the five unvaried descriptors contain registry/area metadata. Targeted nearby
world and lighting changes wait for Tower completion. Nevertheless, the mod is
not wholly inactive beforehand: registrations, injected owners and callbacks
exist. File parity does not prove identical saved world state or rule out a
runtime interaction.

No game launch, mod disabling, new patch or save/settings/cache change was made
for this comparison. PA4 and GD2 remain installed unchanged. **No confirmed cause
yet.** Causal attribution would require a controlled runtime comparison with a
compatible baseline and unchanged settings, keeping GD2 separate from the
original-mod condition. Such isolation has not been performed; do not blindly
remove required mods from the existing development save or call it a vanilla
control. No additional immediate playtest is demanded by this source comparison.

Evidence: `research/graphics_investigation_20261013/stock_comparison_assessment.json`
and its three linked archive, scene-flow and injection reports. The GD2 test below
remains a candidate-benefit check, not proof of the original root cause.

## GD2 implementation — installation-time evidence; later user PASS above

Installed **13 October 2026, 17:31 Toronto / 21:31 UTC**, with Cyberpunk closed.
The earlier failed GD1 diagnostic remains removed. The working PA4 camera/spawn
repair is unchanged. At installation this was a targeted candidate fix with live
benefit pending; the later user-reported graphics pass is recorded above. The
exact diagnosis remains unconfirmed.

The earlier thug encounter uses `q307_falling_down_stairs.effect`. Its native
5–5.5-second hold loop coincides with a contrast increase and strong vignette and
chromatic effects. The audit found no explicit instance stop in the nearby scene
flow, but native automatic teardown is unmeasured; this is not proof of a leak.
GD2 removes only that hold loop, its marker and matching track reference. All four
visual effect payloads, curves and identifiers remain, and the original 20-second
recovery sequence can run to its end. **The injury filter will fade sooner during
long dialogue.** This effect-resource override applies to every caller of that
resource; unique-caller coverage has not been established exhaustively.

The world-lighting variant and active-mod callback audits found no supported
alternative culprit. No global renderer reset, scene/quest change, shader or
graphics-settings edit, cache deletion or automatic save/reload was added.

### Original playtest procedure — retained for reference, not a new request

1. Cold-launch the game. Load **AutoSave-16**, level **48**, **22:47:33,
   12 October 2026**, **Things Done Changed — Leave Viktor's clinic**. The original
   save was rechecked and is unchanged. This starts before the targeted injury
   effect; the later Misty and crowd reload checkpoints cannot validate prevention.
2. Play continuously through Terry, Misty, V getting up beside her, walking to
   her car and the crowd scene. **Do not reload midway**, change graphics settings
   or use reset/quest-stage commands. Ordinary dialogue skipping is fine.
3. Check the world and map at the reported failure point and after the ending.
   Credits may be skipped normally. No CET commands or gig playtest are needed.
4. Report whether the crushed/black/yellow visuals still appear. If they do,
   capture the view before using the known reload workaround. If the game crashes
   or scene progression breaks, stop and report that instead of forcing facts.

An improvement would support involvement of the earlier injury effect, not prove
that its original cleanup failed. A healthy reload beside Misty alone is not a
pass: the user already demonstrated that reload suppresses the fault.

### Validation and recovery

Twenty-one artifact/readback checks and independent review passed. Deployment
fixtures passed **28 cases / 93 checks**, with no skipped checks on the full run.
The initial sandbox-only junction skip is retained separately. Actual installation
added only `TowerContinued_StairsFX_GD2.archive`; there were no replacements.
All **53 existing package files and 635 protected entries**, including **197 save
files, five cache files and UserSettings**, stayed unchanged. Installed archive
hash and read-only rollback validation passed. These are offline/deployment
checks, not proof of engine execution or visible benefit.

Build: `prealpha/graphics_gd2/build/gd2_01`. Sources, build, tools/test mains,
reports and receipts are now pinned; do not rerun installed-version builders or
test mains. Recovery uses `prealpha/graphics_gd2/tools/deploy.ps1`, modes
`ValidateRollback` then `Rollback`, with exact recovery directory
`C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\graphics_gd2_01`.
It moves only the added archive recoverably. **Recover GD2 before changing or
recovering the PA4 package.** Do not reuse the consumed GD1 rollback.

Evidence: `research/graphics_investigation_20261013/gd2_install_assessment.json`;
actual receipt: `recovery/graphics_gd2_01/install_receipt.json`.

## Historical result — GD1 did not fix graphics; diagnostic removed

The user reports the fault persisted with the single-effect suppression. They
made a save **before getting up beside Misty** (explicitly confirmed, not the
final goodbye/crowd scene); reloading it fixed the visuals. This weakens the
dizziness effect as the sole cause, but does not prove
which transient state or interaction is responsible. Runtime effect substitution
was not directly instrumented. Reload relief is not proof of shader-cache damage.

On 13 October at 16:36 Toronto time, with the game closed, GD1 was rolled back.
Only its added archive was moved recoverably to `recovery/graphics_gd1_01`.
All 53 PA4 files and 635 protected entries remained unchanged. The working camera
fix is intact; no save, settings or cache edits. Do not repeat the old GD1 test,
reinstall it or rerun its consumed rollback. The steps below are historical.

The new checkpoint was identified and preserved: **AutoSave-17**, level 48,
**16:31:42, 13 October 2026**, *Talk to Misty*. Sampled data has `misty_sitting=0`
and no crowd-start fact; this does not independently prove V's pose or identify
the exact dialogue node. The user's observed timing is now clear; mapping that
observation to the newest saved slot is not independently established. The
original active save is untouched. A byte-exact three-file
copy and read-only fact report are in
`research/graphics_investigation_20261013/reload_before_standup/`.

The bounded scene audit found finite opening FOV/DOF events and the earlier
`Q307_EC` world-lighting variant setup, but no proven leak or faulty reload rule.
Neither camera transforms nor graphics options measure final exposure/LUT state.
No automatic save/reload workaround or new graphics patch is installed. The
timing clarification is answered; do not ask it again. A later useful observation is a
paired screenshot and existing `Camera()` output at the same faulty continuous
viewpoint versus the healthy reloaded viewpoint. No immediate ending replay is
requested. See `research/graphics_investigation_20261013/gd1_live_result.json` and
`native/reload_differential_assessment.json` in that investigation directory.

## Historical GD1 diagnostic — withdrawn after negative result

Installed 13 October 2026 at 20:17 UTC with the game closed. Exactly one archive was
added; all 53 existing PA4 package files and 635 protected entries, including 197
save files, five cache files and graphics settings, stayed unchanged. Fourteen
artifact/readback checks, independent review and 26 deployment cases/82 checks
passed. The installed hash and rollback readiness were verified. Sources, build,
test mains and receipts are now pinned; do not rerun installed-version builders.

The user approved this temporary diagnostic on 13 October 2026. It suppresses only
the native `ep1\fx\quest\q307\q307_dizzy.effect` resource using the separate
`TowerContinued_DizzyDiagnostic_GD1.archive`. Its three visual events and matching
track references are empty; native duration and five track shells remain. This
resource-level override affects any caller of that resource, not just one scene
event. All other effects, scenes, scripts and the working PA4 camera repair stay
unchanged. This is **not a confirmed graphics fix**.

### Next test

1. Cold-launch Cyberpunk. Load **AutoSave-16**, level 48,
   **22:47:33, 12.10.2026**, *Things Done Changed — Leave Viktor's clinic*.
   The verified original `sav.dat` hash remains
   `51EE74B3EF3CB7872A27AD2C8619FD05BF7B5AB53FB9A84BFA0113555F012F69`.
2. Continue normally through Terry and Misty, then V standing up and walking to
   her car, the crowd shot and credits. **Do not save/reload midway**, change
   graphics options or run FX/reset commands. Ordinary dialogue skipping is fine;
   do not jump quest stages. No CET command or gig test is required.
3. Check when V stands/walks, the crowd, and the post-ending world/map. The normal
   dizziness overlay is intentionally absent. Report whether the black/crushed
   lighting or other corruption still begins, and send a screenshot if it does.
   Credits may be skipped normally; leave menus closed during H10 preparation.
4. Preserve the source save. If the scene crashes or fails to progress, stop and
   report it rather than trying forced facts or resets.

**Do not use AutoSave-18 for this comparison.** Reloading directly into that later
scene already suppresses the reported fault and cannot test the effect's initial
activation. This run must cross its start continuously from AutoSave-16.

If visuals improve, that implicates this effect or an interaction involving it;
it does not prove the unusual color-grade timing is the cause. If the fault
persists, this candidate is weakened. Neither result proves shader-cache damage.
Static serialization and archive readback passed; engine acceptance and visible
benefit remain untested until this run. No automatic second run is requested.

Recovery uses the new `prealpha/graphics_gd1/tools/deploy.ps1`, modes
`ValidateRollback` then `Rollback`, with exact recovery directory
`C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\graphics_gd1_01`.
It moves only the diagnostic archive out of the game; no
permanent deletion, save editing or settings/cache reset. Perform GD1 rollback
**before** changing/recovering the main PA4 package. Historical PA4 recovery below
does not remove GD1.

Installation evidence: `research/graphics_investigation_20261013/gd1_install_assessment.json`.

## Current revision — PA4 spawn and camera user-confirmed working

13 October: user reports **the post-ending spawn and camera are fixed and work
as expected**. Those live checks pass; no need to repeat them merely to reconfirm
the old failure. No diagnostic output accompanied this report, so exact internal
stages, full preparation and new-save/reload regressions remain separate checks.
Evidence: `research/pre_alpha_camera_pa4/live_result_20261013.json`.

Follow-up log audit now corroborates the first run: at15:33:35 all six handoff
flags are1, camera aligned, `profileComplete=true`, fault0; HP stat/pool150 at
15:33:30. A second run restored the camera but was closed with preparation still
pending. These are not a completed-save/reload or all-gig playtest pass. See
`research/pre_alpha_camera_pa4/live_trace_result_20261013.json`.

Graphics remains a separate open issue: the latest report places onset after V
stands up and walks with Misty toward her car, continuing after the ending but
not affecting credits holocalls. Reloading into the scene suppresses it. Both
earlier option dumps were from broken state. Do not treat the historical camera
failure or the generic dump values as proof of the graphics cause.

Installed **13 October 2026, 17:57 UTC**. Only the Arrival REDscript and existing
CET diagnostic entry changed. The combined archive, other51 package files,
185 active save files and five cache files are unchanged. Both replacements have
verified backups. Staged CLI/full SCC compilation with EquipmentEx, compiled
readback,34 artifact/model/LuaJIT checks and38 deployment cases/58 checks passed.
These checks do not prove native camera selection or functioning mouse input.

The native credits already cut their scene on skip. Their external cameras have
blend-in events; retained-session camera handback is the suspected missing step,
not a proven engine-internal cause. PA3's readiness predicate definitely did not
check the selected view. Both earlier blend-reset console commands failed in the
user's test. PA4 instead selects V's existing FPP camera **once, only if the view
is misaligned**, after closed-credits/H10/Tier1/safe-local-player checks. It waits
for four aligned samples before acknowledging readiness and eight fresh samples
after preparation. A saved request is never blindly retried. Already aligned
views need no activation. Scene-camera control/priority, IFP settings, possession,
shaders and graphics settings are not changed. No automated save/reload.

### Retained test procedure — spawn/camera steps now passed

1. Cold-launch and load **AutoSave-18**, level48, **13:16:51, 13.10.2026**.
   This is the user's forced checkpoint immediately after the crowd scene;
   its metadata still says *Walk with Misty*. The user confirmed it replays credits.
   Do **not** use ManualSave-23 or a post-handoff save for this test.
2. Skip the credits at the same point as the failed test. Close CET/menus and
   leave V holstered. No manual reset, teleport, fact or gig-start command needed.
3. After the short H10 transfer, try mouse-look and walk several steps. Observe
   camera recovery separately from the still-unresolved lighting corruption.
4. If stuck, capture the following **before saving/reloading**:

   ```lua
   print(GetMod("PTFR_PreAlpha").Camera())
   print(GetMod("PTFR_PreAlpha").Status())
   ```

   `cameraRequest/aligned=1/1` means one activation was issued and alignment was
   measured; `0/1` is also valid if already aligned. `1/0` is not success.
   `alignedNow=true` is geometry evidence, not proof mouse-look works. Diagnostic
   output includes active/FPP positions, direction agreement, free-camera and
   possession state, NoCameraControl, and optional read-only IFP state.
5. If camera works, let preparation finish with menus closed. Arrival should
   eventually show `started/teleported/control/prepared/reveal/finished=1/1/1/1/1/1`
   and `fault=0`. A full new-save/reload regression remains separate; earlier
   mid-preparation reload lost coordinator admission, which PA4 does not repair.

Checkpoint backup and frozen failed-run logs:
`research/pre_alpha_camera_pa4/live_pa3_and_checkpoint/`.
AutoSave-18 sav SHA256:
`7F6A9D621BAEAC273AF83C8289479876808645365E69BF2B377D67515EAD2D37`.
No active save was edited or generated by this repair.

Recovery **first** uses `prealpha/camera_pa4/tools/deploy.ps1`, modes
`ValidateRollback` then `Rollback`, with exact recovery root
`recovery/pre_alpha_camera_pa4_01`. Only afterward use prior PA3 recovery if needed.
PA4 sources/build/tools/test mains/reports are now pinned; do not rerun builders
or mutate installed candidate evidence. Candidate `prealpha/camera_pa4/build/pa4_02`.

## Historical PA3 results below — superseded instructions

## Latest live result — camera remains stuck after credits

13 October: user reports H10 teleport worked, but the camera recovered only after
a new save/reload. The automatic trace reaches `coverReleased=1`, tier/high `1/1`
and `control=1`, without timeout. Those checks therefore do **not** prove the
camera has returned to V. Profile/preparation was unfinished at reload; afterward
the coordinator reported `lateEndingTest=false activated=false`. Full handoff and
reload-resumption remain unresolved. No camera-reset revision is installed yet.

A closer existing checkpoint is **AutoSave-16**, level48, **12.10.2026 22:47:33**,
**Leave Viktor's clinic**. Its screenshot shows the clinic exit stairs. It skips
Viktor's dialogue but is still before the Misty encounter, not immediately before
the crowd shot. Read-only facts and all three original file hashes were checked;
a byte-identical backup is in `recovery/pre_misty_checkpoint_20261013/AutoSave-16`.
This was preservation of an existing save, not fabrication of a later scene state.
No runtime files, active saves or caches were changed for this checkpoint search.

## Historical revision — PA3 installation

Installed **13 October, 12:59 UTC**. Two backed-up files changed: the combined
archive's handoff graph and its readiness observer. All53 installed hashes and
576 protected entries pass, including164 save files and five cache files.
CLI/full engine compilation with EquipmentEx and readback,40 artifact/regression/
model checks, and35 deployment cases/55 checks passed. These are not gameplay proof.

PA3 keeps a brief native blackout around the H10 teleport, then fades back in
**before** waiting for actual gameplay readiness. Profile/gig preparation happens
with the screen visible. Existing safety checks and timeout budgets remain;
there is no forced save/reload, fact reset, or PONR rewind. Status now reports a
current gate reason and no longer claims a stopped watchdog is still armed.

The reported graphics issue is **deferred at the user's request**. Shaders,
caches and graphics settings were not changed; no graphics fix is claimed.

## Previous failed handoff

PA2's captured run reached H10 while tier/high remained `5/5` throughout the
black-screen readiness wait. At timeout/fade-in it changed to `1/5`, then `1/1`,
after `fault=1` had stopped preparation. This strongly supports a self-blocking
native fade/readiness order, but exact engine internals were not instrumented.
Frozen evidence: `research/pre_alpha_transition/live_failure_20261013/result.json`.

PA1's first live run applied the nerf but left V stuck at Afterlife after credits
were skipped during Rogue's segment. The revised test below is for PA3, not a
repeat of the failed PA2 procedure.

## Package scope

This is a focused **pre-alpha rehearsal**, not the full integrated alpha. It
combines the existing world/service restorations, current 72-gig whitelist,
voice-only Johnny, accepted implant-focused HP150/Body3/Relic nerf profile, and
the new one-time H10 street arrival. Old overlapping gig pilots/diagnostics are
retired from the active installation. The existing Only Pain side-job pilot is
retained but not automatically started.

Broad side-job/other-activity rollout and apartment loss/repurchase are **not
implemented by this package**. The agreed future housing rule remains H10 at
€$25,000, other previously owned ordinary apartments at normal prices.

## Exact source save

Load **ManualSave-10 — Things Done Changed**, level **48**, saved at
**22:04:51 on 20.09.2026**. Its tracked step is **Meet with Viktor**; metadata
debug stage is `q307_cabride_start`. The original `sav.dat` hash is
`62742BF7E77451D5498AB724EEECD10CD2E35AFEF3442361D67A29BBDD486B3B`.

The original PA1 cleanup backed up this save and recoverably archived other old
save folders/PTFR files. Additional save folders are now present; PA3 leaves all
of them untouched and does not repeat cleanup. Use the exact original Manual10,
not Manual11 (already after the ending despite its stale quest label), or a new
PA1/PA2 postcredits save. No old development-save migration is attempted.

This save is already within the 2079 ending, **after the true pre-Tower capture
boundary**. The coordinator observes this actual ending session, then uses the expressly
approved development assumption that incomplete whitelisted gigs were unstarted.
It never labels that assumption as certified pre-Tower history. The separate
production snapshot/cutoff path still needs a genuine pre-Tower test later.

## Minimal test

1. Cold-launch after the install receipt is confirmed. Load the exact save above.
2. Wait a few seconds in gameplay. Optional read-only check in CET:

   ```lua
   print(GetMod("PTFR_PreAlpha").Status())
   ```

   During the ending, expect `lateEndingTest=true`, `completedTower=false`, and
   no post-ending teleport. A missing history certificate is expected here.
3. Close CET and finish Things Done Changed normally. For this regression test,
   skip credits during Rogue's segment again using the normal game control. Do not
   run old `StartAll`, fact-reset, refund, teleport or gig override commands.
4. Expect a brief black fade for placement, then the visible street in front of
   H10. Keep CET/menus closed and weapons holstered while preparation finishes;
   stay near the arrival point. This is not an engine loading-screen UI. Existing
   refunds run one rank per second, so preparation duration varies. The native
   readiness limit is60 seconds, followed by up to180 seconds for preparation;
   neither wait should hold the black screen. These are failure limits, not fixed
   delays. A timeout is a failed test, not success.
5. Check `Arrival()` below after preparation: all six flags should be1 with
   `coverReleased=1 fault=0`. Physically verify walking, camera and HUD. This
   does **not** grant apartment ownership. The accepted profile should
   be HP150, Body3, closed Relic and the existing implant/perk restrictions.
   Eligible gigs are requested automatically. Stock tiers and approach/briefing
   still determine which markers and journal objectives appear; not all 72 jobs
   should appear in the journal immediately. Completed outcomes remain preserved.
6. Enable the map's **Gigs** filter. For this short test, check a marker and,
   if practical, approach one available gig for its normal fixer call/journal
   activation. No full gig completion is required for the initial startup check.
7. Walk away from the arrival point, create a **new manual save**, reload it, and
   verify V stays where that new save was made. HP150 should remain applied;
   there must be no second H10 teleport or repeated perk refund.

Read-only diagnostics if something stalls:

```lua
print(GetMod("PTFR_PreAlpha").Status())
print(GetMod("PTFR_PreAlpha").Arrival())
print(GetMod("PTFR_PreAlpha").Profile())
print(GetMod("PTFR_PreAlpha").Phone())
print(GetMod("PTFR_PreAlpha").Entry())
print(GetMod("PTFR_PreAlpha").Gigs())
```

Successful `Arrival()` should show `H10 transition PA3`,
`started/teleported/control/prepared/reveal/finished=1/1/1/1/1/1`,
`coverReleased=1` and `fault=0`, with tier/high `1/1` in gameplay. Those flags
do not replace physically checking walking and camera. Opening a menu can make
the live gate say `menu open`; close it to allow unfinished readiness checks.
The unchanged coordinator/CET trace may still label itself PA2; the Arrival
component's PA3 label identifies this repair.
If stuck or timed out, send `Arrival()`, `Status()` and `Profile()` before using
a reload workaround. A read-only bounded transition trace is also written through
CET logging. Do not force facts or rerun old commands.
After this check you may close the game. Broader per-fixer completion/call,
reward, tier, cleanup, interruption and persistence checks remain in the gig
playtest backlog; a marker/compile pass is not proof of all gig gameplay.

## Deferred checks

- [ ] Live ending/credits return and street-front location/footing/camera/HUD.
- [ ] Watched versus skipped credits on separate branches from the original.
- [ ] Profile activation, refunds once, save/reload and death/checkpoint reload.
- [ ] No repeat H10 placement after reload/death; no placement during ending.
- [ ] Fixer incoming/debrief calls, messages and interruption/reset behavior.
- [ ] One representative gig per fixer and special dependency family, preserving
  outcomes, stock credit/tiers and one payout. Untested individual gigs stay open.
- [ ] Johnny voice/timing preserved, visual body suppressed.
- [ ] Previously restored world/services regression.
- [ ] Genuine pre-Tower snapshot/cutoff/production dispatch on a later fixture.
- [ ] Full alpha remaining side jobs, other activities and housing implementation.

## Recovery

Current PA3 recovery directory:
`C:/Users/Ayong/Documents/cp77 modding/tower ws/recovery/pre_alpha_handoff_pa3_01`.
Two replaced files were backed up;53 installed hashes and576 protected entries
passed, including164 save files and five cache files. With the game closed,
first use `prealpha/handoff_pa3/tools/deploy.ps1 -Mode ValidateRollback`, then
`-Mode Rollback`, with this exact `-RecoveryRoot`. This restores PA2 files only;
PA2's handoff is known to fail. No rollback rewinds in-game saves. Use the original
Manual10 for a fresh transition, not an already-faulted postcredits save.

Historical PA2 recovery directory, applicable **only after PA3 rollback**:
`C:/Users/Ayong/Documents/cp77 modding/tower ws/recovery/pre_alpha_transition_pa2_01`.
Four replaced files were backed up; all 53 installed package hashes and 568
protected entries passed, including 158 save files and five cache files.
With the game closed, use `prealpha/transition/tools/deploy.ps1` with
`-Mode ValidateRollback`, then `-Mode Rollback`, and this exact `-RecoveryRoot`.
This restores PA1 files only; it does not rewind an in-game save or fix an already
stuck postcredits snapshot. Reload the original pre-transition Manual10 for tests.

Historical PA1 recovery directory:
`C:/Users/Ayong/Documents/cp77 modding/tower ws/recovery/pre_alpha_clean_20261013T022533186Z`.
It contains 240 original PTFR file/folder entries and 49 archived save folders,
plus an unchanged backup of retained ManualSave-10. The post-install audit checked
all 53 installed files, 299 protected files and 2,479 archived original files.
Nothing was permanently deleted.

Only after PA2 is rolled back, the older `prealpha/tools/deploy.ps1 -Mode Restore
-RecoveryRoot <exact PA1 receipt directory>` applies. It verifies hashes and refuses save-name
conflicts rather than overwriting newly created saves. Do not use obsolete
per-version rollback scripts while the consolidated package is installed.

Current evidence: `research/pre_alpha_handoff_pa3/assessment.json`,
`prealpha/handoff_pa3/build/pa3_01`, and the exact PA3 install receipt.
Historical PA2 evidence: `research/pre_alpha_transition/assessment.json`,
`prealpha/transition/build/pa2_candidate_03`, and the exact PA2 install receipt.
Historical PA1 evidence remains under `research/pre_alpha_clean` and
`prealpha/build/20261013T021845834Z`. These installed artifacts,
tools and receipts are now pinned; changes require a new version/build/evidence,
not rerunning old installed builders against the altered game layout.
