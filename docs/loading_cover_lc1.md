# Loading cover and setup scheduling — LC1

24 October 2026. Local test package; live UI behavior and total deployment time
must still be verified. The current installation receipt and final assessment
are under `recovery/loading_cover_lc1_01` and
`prealpha/loading_cover_lc1/candidate_04/assessment_01.json`.

## What the cover waits for

The opaque cover blocks gameplay input while the simulation continues. It shows
the current stage and Body, Relic and other perk refund counts where applicable.
It uses Codeware's base `CustomPopup`, without the time dilation or modal game
context that its `InGamePopup` subclass adds. It does not apply a movement or
camera restriction, change scene tiers, or take ownership of the native fade.

For a new or interrupted initialization, all of these must pass:

- HS1's accepted quest snapshot is frozen and its JSON file verified.
- The native arrival, camera and optical handback are acknowledged.
- Cyberware reconciliation, Body/Relic and the full profile transaction are
  complete; the current progression ledger and health modifier/pool are valid.
- Housing loss and relationship access changes are acknowledged, with no
  transaction fault. Buying a home is not part of automatic setup.
- H10 geometry is acknowledged, and its service owner is armed if V is entitled
  to use it. An unowned apartment does not require active private services.
- The initial U9 admission pass has run and the native handoff has completed.
  Each of the eight installed side-job/U10 controllers has performed two
  classification passes. Native prerequisite failures and unsupported stages
  defer those entries; they do not hold the cover forever.
- Fresh camera/control and safe-player checks remain valid for one second.

New U9 requests, unissued side-job/U10 permits and fresh Only Pain activation
wait for the cover to be released. Existing owners, quest choices and rewards
are retained. Calls and distant/location-dependent quest activity remain under
their normal native gates; "setup complete" does not mean every selected quest
is eligible or every remote actor is spawned.

Already completed saves take a validation path based on their existing profile,
Body, housing and handoff receipts. They still verify the snapshot, actual
progression ledger, cyberware and health state. They do not require another
respec or demand that an equipped weapon be holstered while input is blocked.
Combat/vehicle/camera behavior on this path needs a separate live test.

## Cover acquisition and failure

The current native `final_boards.questphase` has two added nodes before its
existing fade-in: clear the owned cover acknowledgement, then wait for its new
attachment acknowledgement. The acknowledgement follows popup attachment and
a short render opportunity; it does not wait for Tier1, profile or housing.
The native fade and its established Tier1/control ordering then run unchanged.
All old node payloads, the timeout branches and the other 615 archive resources
are preserved, including the current 2.5 lighting sector.

For loaded post-ending saves, the player-attach/restore hooks request the cover
as the UI initializes. Actual first-frame coverage must be checked in-game.
Transient epochs reject old callbacks. A service holds any pending old popup
until it is retired, preventing duplicate requests during save switches.

**Esc returns to the main menu.** It does not unlock gameplay or mark setup
complete. The cover remains until player detach or successful completion. A
failed check displays a stop message. After 180 simulation seconds, a long-wait
message offers the same exit; elapsed time never counts as success. The game's
normal shutdown controls remain available.

## Scheduling changes

| Work | Change |
| --- | --- |
| Body and Relic refunds | One acknowledged rank per 0.25-second opportunity while refunding; queued/in-flight operations and warmup do not accelerate |
| Other restricted perks | Remove the four-tick throttle only during the refund stage; the 0.25-second physical update stays unchanged |
| Body stat settling | Require at least four elapsed simulation seconds as well as matching samples |
| Entry readiness | Check every 0.25 seconds after the ending; retain three elapsed seconds of safe-player stability |
| U9 admission retry | Keep the five-second retry but separate it from geometry/housing readiness checks |
| H10 preparation retry | Retry once per second until geometry acknowledgement, then return to the existing cadence |

The retained failed fixtures have 27 ranks to refund. The nominal scheduling
opportunities for those ranks change from 27 seconds to 6.75 seconds. This
approximately 20-second reduction excludes load settling, engine callbacks,
equipment, housing, world readiness and final checks. It is not a measured
end-to-end result. Stage changes are logged under `PTFR_LoadingLC1` with elapsed
simulation time so the live critical path can be measured.

## Live test

1. Cold-launch and load retained post-ending AutoSave 8 or 9. Keep the original;
   save testing progress into a new manual slot. Check that the cover appears
   without an exposed playable frame and that stage text/refund counts advance.
2. While covered, try movement, camera, combat, interaction and menu shortcuts,
   including controller input. They must not reach gameplay. Esc must return to
   the main menu without exposing unfinished gameplay. Reload the original to
   continue the test after checking this exit.
3. Wait for successful setup. Check profile limits, housing restrictions, H10,
   quests, the camera and normal controls. No automatic home payment or reward
   replay should occur. Unsupported quests may remain deferred.
4. Make a new manual save, reload it, and confirm that no loss/refund/reward is
   repeated. Separately check a completed save with a weapon, in a vehicle and
   after death/checkpoint reload. A normal ending traversal is needed to verify
   the newly added native cover acquisition before fade-in.

Read-only CET status:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.LoadingCoverLC1.StartupCoverLC1"):Status())
```

The full 87-source stack, including Equipment-EX, compiled. Offline checks cover
saved fields, unchanged mutation/camera bodies, compiled readiness predicates,
native graph ordering and archive preservation. These checks cannot prove the
engine's notification input behavior, first rendered frame or performance.

## Recovery and evidence

With the game and launcher closed, run from the workspace in PowerShell 7:

```powershell
& ./prealpha/loading_cover_lc1/deploy_01.ps1 -Action ValidateRollback
& ./prealpha/loading_cover_lc1/deploy_01.ps1 -Action Rollback
```

This restores the prior HS1 scripts and the working **2FC245…** main archive,
including the current 2.5 lighting rebase. It does not restore the obsolete
crashing archive. Roll back LC1 before HS1 or older Tower packages. Core and
cosmetic recovery are separate. File rollback does not undo gameplay already
written to a new save.

Final script package: `candidate_04`; compile: `compile_02`; offline proof:
`tests_01.json`; native splice proof: `candidate_02/native_01.json`; deployment
proof and manifest: `candidate_04/deployment_tests_01.json` and
`install_manifest_01.json`. Intermediate candidates are historical. Final
sources/builds/proofs are pinned; use successors for edits. Generated packages,
private evidence and backups remain Git-ignored. No public release was updated.
