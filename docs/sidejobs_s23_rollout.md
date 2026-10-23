# S23 — full-whitelist side-job rollout

## Current installation: S27 original fresh family entries

Installed 21 October 2026, 15:56 UTC from
`prealpha/sidejobs_s27/build/s27_03`. Adds The Beast in Me's original story-race
family (five roots) and Heroes' original package outcome, not the funeral.
Their native gameplay, choices, calls, prerequisites and rewards are retained.
Original Mama and Claire phone controllers extend the existing S24 cleanup;
Claire's bar, repeatable races, Dogtown and prior restorations remain intact.
Johnny's existing voice-only/body-hidden policy is unchanged.

This is a fresh-entry expansion, **not the unfinished-job restart migration**.
Actual Inactive roots plus per-job freshness/ownership checks are required.
Completed/progressed jobs are not reset. Latest working-save metadata and the
prior live capture show both families completed, so no new entries are expected
on that branch. New-route playtests require a genuinely unstarted eligible
branch; do not clear facts to manufacture one.

Validation: 373 native/structure checks, 19,158 policy cases, scoped CLI and full game SCC
including EquipmentEx and 14 compiled arrays; 43 byte-exact official resources
plus both cooked-journal variants for 613 used metadata paths. All 85 installed
archives and all 61 XL files are bound. Independent component/support/native
comparison/deployment reviews and 89 deployment cases / 104 checks passed.
Three additions, no replacements; all 709 protected files, including 215 saves
and five cache files, unchanged. All three installed hashes and rollback validated.
No game launch; actual gameplay/rewards/reload remain pending.

Recovery first: `prealpha/sidejobs_s27/deploy.ps1` with
`recovery/sidejobs_s27_01`, then DT1, S26 capture and S25/older transactions.
File rollback does not undo gameplay saved later. Final source/build/test/tools
are pinned; further implementation uses successor paths.
Evidence: `research/sidejobs_s27/assessment_01.json`.
Build SHA: `BD3A829AFDCED97D9986C39D5673A67DA1F5D6774724DA1C7C1575FC33A66A6A`.

## Still pending: S26 restart policy and Cassius diagnosis

The requested policy is now completed → preserve, started-but-unfinished →
restart at the original beginning, never-started → original beginning.
**This new restart behavior is not implemented yet.** S25 gameplay remains
installed unchanged; one-time migration must retire existing quest owners
before replacement and protect completed jobs, siblings and prior rewards.

On 17 October local (18 October 02:01 UTC), the two-file manual CET helper
`PTFR_SideJobsCaptureS26` was installed from
`prealpha/sidejobs_s26/restart/build/capture_04`. No gameplay files were replaced.
Its explicit `ArmCassius()` observes normal shop events without creating stock;
`Capture()` stops observation and saves current quest, owner-fact and item
readings. It does not reset or restore quests. See the playtest's S26 section.

Cassius uses the native scene and opens his shop. Native stock offers one free
Advanced Yakuza tattoo when `sq_q001_add_reward > 0`; the frozen save has 1.
The Gig accepts possession of either Yakuza tattoo variant, not installation.
The existing inventory-only purchase path must be diagnosed before changing
stock, reward or cyberware rules. Actual failure cause remains unresolved.

Validation: 37 capture and 30 probe LuaJIT cases, 20 workspace deployment cases,
and independent review passed. Closed-game Validate/Install/ValidateRollback
passed; 703 protected files (215 save files and five cache/settings files)
remained unchanged, with eight existing working files hash-verified. No launch.
All 58 roots have a source-pinned NPC/service audit; this is not 58 working
restart implementations. Final sources, build, tests and deployment tools are
frozen; further changes require successor paths.

After newer S27 and DT1 have been rolled back, S26 capture recovery uses `deploy.ps1` with
`recovery/sidejobs_s26_capture_01`, then S25 and older transactions. Rollback
moves only its two added files into recovery and preserves generated reports.
File rollback does not undo gameplay saved after installation.

## Installed gameplay baseline: S25 Inactive-only expansion

**Installed 16 October 2026, 15:41 UTC; live gameplay pending.** Build
`prealpha/sidejobs_s25/build/s25_04` adds five bounded fresh owners: The Gun,
Paid in Full, Beat on the Brat, the Human Nature/Tune Up/Epistrophy family and
The Prophet's Song. Their families cover 19 roots. Original gameplay, payments,
calls, rewards and prerequisites remain native; Johnny JV1 stays unchanged.
The Gun uses the stock order/shop/reward slice, not the obsolete first-meet
prop/attention staging, while keeping the existing Wilson actor and MQ011 lease.

New activation is **Inactive-only**, including the old unissued S22/S23 routes
and Only Pain's native saved-request check. Already-issued owners continue
unchanged. No native fact/history reset, journal-state fabrication, generic
restart or duplicate reward is introduced. All five candidates have prior
progress/completion in the frozen capture and must remain protected there.

The package contains three additions and two backed-up script replacements,
26 mod resources, five boot registrations and 20 reviewed mod-resource overrides.
There are no official resource overrides. Native graph IDs/edges/gameplay in
the policy-only replacements remain unchanged. Tests cover 4,194 native/structure
checks and 36,826 policy cases. Full game-compiler validation includes EquipmentEx;
the older CLI checks the mod's complete dependency slice because it rejects an
existing EquipmentEx expression. Compiled table readbacks cover S25 (35), S22
(24) and S23 (168), plus preserved S2 diagnostics. Resource audit checks 53 exact
official resources plus both official cooked-journal byte variants for 750 used
metadata paths; it also binds all 83 installed archives and all 59 XL files.

All 107 deployment cases / 130 checks passed, including interrupted replacements
and recoverable rollback. Actual closed-game validation, installation, all five
installed hashes and rollback validation passed. All 698 protected files,
including 215 save files and five caches/settings, stayed unchanged; eight
working package files were verified. No game launch or save/settings edits.
Final proof binds 271 source pins, all 60 component JSON witnesses and 25 fresh
raw-source comparisons. Earlier failed/superseded builds remain preserved.

Evidence: `research/sidejobs_s25/assessment_01.json`. Build SHA:
`5884AEB720E9AF6272A277F3750497B3C46021C165C2C3D10B1B56711F3AF6E6`.
Cold-launch the same working post-Tower branch, make a separate manual test save
and close menus for 20 seconds for a regression check. No ending replay needed.
Fresh gameplay tests require a separately preserved genuinely unstarted branch.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS25.SideJobsS25"); print(s:Status())
```

**Current recovery starts with S25:** use `prealpha/sidejobs_s25/deploy.ps1`,
`ValidateRollback` then `Rollback`, with `recovery/sidejobs_s25_01` and the game
closed. Then follow S24, S23 restoration/capture, S221, S22b and older recovery.
File rollback does not undo saved progress. Installed S25 sources/builds/tools/
tests and receipts are frozen; further code changes require successor paths.

The coverage inventory reports **52/58 roots with a bounded route**, not every
stage or live success. Heroes and Claire's story-race family remain pending;
the repeatable-race restoration is unchanged. See the
[S25 test checklist](sidejobs_s23_playtest.md#s25-clarification-and-next-batch).

## Previous successor: S24 fresh-entry batch

**Installed 16 October 2026, 14:33 UTC; live gameplay pending.** Build
`prealpha/sidejobs_s24/build/s24_02` adds Happy Together, Violence, Spellbound,
The Gig, Shot by Both Sides, No Easy Way Out and Moving Heat fresh-start routes.
It keeps all prior restoration files and saved progress. Johnny JV1 is unchanged.
Original per-job gameplay, calls, scenes, waits and rewards remain authoritative.

The frozen capture has prior progress/completion for all seven. This package
must leave those jobs alone; it is not seven extra entries on the current save.
Actual Inactive journals plus job-specific freshness and unused-owner guards
decide admission. Unknown state defers. There is no pre-ending-history claim,
native fact wipe, reward replay or completed-job reset. Aaron's existing partial
message bug remains parked; the fresh No Easy Way Out route is separate.

Three files were added, none replaced. Ten mod-owned resources and nine boot
registrations include only one resource-priority override: an extension of the
existing S23 phone cleanup. No official game resources are overridden. Silent
native contact setup and original Lizzy/R3NO phone controllers support fresh jobs;
historical call-count equality is not a busy-state condition.

Validation passed: 10,143 native/structure checks, 14,227 policy cases, full
installed-script compilation including EquipmentEx and 49 compiled-table
readbacks, 100 exact official-resource comparisons, 82 installed archives and all
58 XL files, ten packed-resource readbacks and nine collision-checked boot IDs.
The base cooked journal has two official byte variants: only used metadata is
compared across them (372 used paths, 553 independent variant checks); neither
journal is shipped, and whole-file equality is not claimed. All 87 installation /
rollback cases (102 checks) passed. Actual installation and rollback validation
passed; 697 protected files including 215 saves and five caches stayed unchanged.
The game was not launched; settings were not changed.

Evidence: `research/sidejobs_s24/assessment_01.json`. Build SHA:
`4753F0B47749FC061F437D95654EA9282EB3C14EEBD38908CB75084C3B0BD116`.
Cold-launch the current working post-Tower branch, preserve it with a new manual
test save, and close menus for 20 seconds for a regression check. No ending replay
is needed. See the [S24 fresh-fixture and regression checklist](sidejobs_s23_playtest.md#s24-fresh-entry-batch--live-tests-pending).

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS24.SideJobsS24"); print(s:Status())
```

**After rolling back S25, recovery continues with S24:** use `prealpha/sidejobs_s24/deploy.ps1`,
`ValidateRollback` then `Rollback`, with `recovery/sidejobs_s24_01` and the game
closed. Only then follow the S23/older recovery below. File rollback does not
undo progress already written into a save. All installed build sources/tools
and receipts are pinned; further code changes need a new successor directory.

## Earlier S23 rollout

**16 October follow-up:** new work now prioritizes unstarted whitelisted jobs.
Keep this installation and all earlier progress-preserving restorations intact.
The user reports that No Easy Way Out has its reply objective but Aaron's message
is missing; that repair is deferred under the new priority, not verified working.
See the [updated work/test queue](sidejobs_s23_playtest.md#unstarted-first-priority--16-october).
No additional runtime package was installed for that scope-change-only turn;
S24 above is the subsequent implementation.

Status: **installed 16 October 2026, 02:10 UTC; live playtest pending**. Build
`prealpha/sidejobs_s23/build/s23_02` covers the remaining families from the
58-root R4 whitelist alongside the existing S1/S2/S22/S22.1 owners. This is not
a claim that every possible partial stage or live outcome has been tested.
Main story and excluded jobs remain outside this rollout.

The stable live capture contained 33 Inactive, six Active, 18 Succeeded and one
Failed root. Active and completed jobs stay untouched. The new package supplies
24 bounded admission routes for 25 remaining journal roots (Brendan has three
roots; Skippy has mutually exclusive fresh and progressed routes). Nine Inactive
roots remain covered by existing owners. Original local prerequisites and waits
still decide when a job becomes available; this does not add 58 journal entries.

## Preserved progress and native behavior

- No Easy Way Out resumes the captured Aaron SMS outcome, retaining completed
  clinic/Angie objectives and earlier rewards. Its additional native phone-journal
  guards must actually match; unavailable/unknown states defer.
- Skippy has a separately confirmed-history continuation described below. Its
  fresh owner cannot admit the progressed state.
- Existing Epistrophy, boxing, The Gig and Moving Heat owners are not restarted.
  S1 Only Pain is armed through its existing public preflight, not a second owner.
- Native per-quest phases/scenes/rewards are retained. New native Frank, Mr. Stud,
  Ozob, Sandra and Wilson phone controllers use the existing shared phone support;
  historical call-count equality is not an admission requirement.
- Wilson/Zane/Bill service ownership is coordinated with the previous restorations.
  Steven's follow-up defers to an existing active Spy in the Jungle owner.
- Johnny keeps the existing voice/hidden-body policy. No global graphics, ending,
  nerf, apartment, gig, NCPD, courier, race or airdrop changes are included.
- Runtime is quiet; manual `Status()` / `Inspect()` diagnostics remain available.

Current development selection remains whitelist plus **Failed OR Inactive after
Tower**, preserving supported partial progress. Future **Inactive before Tower**
certification remains separate. Unsupported/ambiguous stages are protected, not
silently restarted. Existing captured state is not a fabricated history record.

## After installation

Cold-launch the same working post-Tower save used for the S23 capture. Preserve
that original and use a new manual test branch. Close CET/menus for about 20
seconds on foot, safely outside a scene/call. No ending replay is needed.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS23.SideJobsS23"); print(s:Status())
```

Use the [short smoke test and deferred playtest checklist](sidejobs_s23_playtest.md).
Issued/Entered are owner diagnostics, not interaction, NPC, reward or map proof.

### Skippy: explicit history confirmation

The user confirmed that the 50-enemy firing-mode conversation already happened.
Native counters cannot distinguish that from a pending conversation on one branch,
so this exception is not enabled automatically on arbitrary saves.

On the matching captured save, run this **once** after installation:

```lua
Game.GetQuestsSystem():SetFactStr("PTFRS23_MQ007_ModeTalkConfirmed", 1)
```

This writes only the mod's confirmation marker, not a native quest/counter/mode
fact. Exact progress, journal, safety and unused-owner guards still apply. The
original pickup and mode-change scenes are not replayed. Skippy retains the gun,
mode and counters; its original two-game-day return-stage delay starts anew (the
old remaining timer is not reconstructed), followed by native inventory/safety
conditions and the owner-reveal conversation. A fresh quest entry need not appear
immediately. Do not reset counters to make this route match another save.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.SideJobsS23.SideJobsS23"); print(s:Inspect("PTFRS23_MQ007_RESUME"))
```

## Evidence and validation

- Frozen capture: `research/sidejobs_s23/live_20261016_01/capture.json`, SHA
  `47084A3833CFE507D184A19CDD1276215A15F917F6B97AA4130E6A6E6919748A`.
- Final build SHA:
  `84A8FB28CCAD8E209D6D3C32899E91116ECD2137B099E0A1D1A2AB8DBBFBB5DE`.
- 34 mod-owned resources, 29 one-shot boot registrations, 24 runtime adapters.
  Three file additions; zero replacement of installed files. Two mod-owned
  resources supersede the earlier cleanup/Wilson versions through load priority;
  no official resource override.
- 1,210 aggregate native/structure checks and 9,501 policy cases passed, plus
  the retained predecessor component proof. Full installed-script compilation
  including EquipmentEx and 168 compiled table readbacks passed.
- 112 official resource byte comparisons, 81 installed archive audits, all 57
  installed XL file identities/hashes and packed-resource readbacks passed.
- Earlier failed/superseded builds and compiler-verifier output are retained.
  The verifier needed normalization of decompiler-escaped apostrophes; the
  successful compile/readback was rerun before installation.
- All 74 deployment/recovery cases (89 checks, no skips) passed. Installation
  added three files with zero replacements. Actual installed hashes and rollback
  validation passed; 694 protected files, including 215 saves and five caches,
  were unchanged. Settings were untouched and the game was not launched.

Per-family evidence lives under `research/sidejobs_s23/base_a`, `base_a_v2`,
`base_b`, and `ep1`. Full gameplay, alternate seams, rewards, save/reload and
fresh-ending production integration remain pending playtesting.

## Recovery

After recovering S24 as described above, recover **S23 restoration**, using
`prealpha/sidejobs_s23/deploy.ps1` and `recovery/sidejobs_s23_01`:
`ValidateRollback`, then `Rollback`, with the game closed. It recoverably moves
the three added files; it does not undo gameplay written into a save.

Then remove the older capture helper only if desired, using
`prealpha/sidejobs_s23/capture/deploy.ps1` and
`recovery/sidejobs_s23_capture_01`. Follow S22.1, S22b and older recovery after
those. Never repeat the already-consumed `sidejobs_s22_01` rollback.
