# Restriction profile R3 activation and checks

R3 now selects the implant-focused profile; the original strict source profile is preserved. Body 3, all Body bans, Relic closure, HP 150 and the cyberware whitelist are unchanged. The offline compiler, model and deployment checks do not replace a live game test. Use a disposable completed-Tower save and retain an untouched pre-update save: perk and attribute refunds are permanent in a saved game.

The installed profile update accepts the exact reviewed strict revision 1 or 2 on next load, provided it is enabled, nonfaulted and not in flight. It relaxes 21 other-tree bans without restoring ranks, granting points or resetting the refund journal. A completed strict save can repurchase eligible ordinary skills with its retained points. No-vitals stays off; `FullNerf()` enables HP after migration finishes. Restoring old files does not downgrade saved profile metadata.

## Activate

Cold-launch the game. Load the completed-Tower test save, holster, leave combat/dialogue/workspots and close gameplay menus. In CET:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR3.ProfilePolicy"):FullNerf())
```

This queues Body 3, Body/Relic refunds if not already completed, the 53 implant-related/dependency other-tree bans/refunds, and final max HP 150. Stamina has no direct override. Existing completed Body/Relic refunds are not repeated. Installation alone does not activate an unenabled progression profile.

To exclude the numeric HP layer instead:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR3.ProfilePolicy"):FullNerfWithoutVitals())
```

The previous R2 `FullNerfWithoutVitals()` command now delegates to this command. After a no-vitals migration reaches stage 4, `FullNerf()` can enable HP without repeating refunds. Calling the no-vitals command does not turn off an already-enabled HP module.

Close CET and remain in safe gameplay while the queued steps run, up to one purchased rank per second. Then inspect:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR3.ProfilePolicy"):GetStatus())
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR3.ProfilePolicy"):Measure())
```

Stage 1 waits for existing Body/Relic work and equipment reconciliation. Stage 2 refunds other-tree ranks. Stage 3 verifies progression and HP readback. Stage 4 means the migration completed. Stage 5 is a fault; do not force-reset the journal. `GetAudit()` explains prior steps. A physical-module STOPPED message also needs investigation even if the progression stage is already 4.

If both Hands slots contain approved tattoos, clear one at a ripperdoc. If only slot 2 is occupied, R3 moves that tattoo into slot 1 and verifies item quantity and installed parts before proceeding. It never force-sells past the native slot/capacity checks.

## Live acceptance

1. On an already-completed strict save, confirm the profile becomes `tower_implant_focused` with stage 4 and no point/rank changes from the switch. For a new or unfinished migration, confirm refunds equal actual remaining purchased restricted ranks, not the 53-record count. Historical starting/refund counters are retained when switching mid-migration.
2. Confirm Body is 3, Body perks are empty, Relic remains hidden, and all selected other-tree perks refuse ordinary and forced purchase. Retained perks remain available after migration. Repeat the command: no extra points.
3. Confirm `Measure()` reports max-stat and pool max HP 150 after settling. Test while injured: activation and buff expiry must not refill current HP. Check food/health buffs, level progression and reload. Current-health behavior can depend on native pool scaling; stop testing if it rises solely from reconciliation or receives repeated damage.
4. Confirm stamina has no direct override. Its baseline may change when refunded perks lose their vanilla effects.
5. With each Casius tattoo and representative smart weapons, test actual acquisition, guided shots, switching weapons, holstering, driving and cold reload. No aiming/homing assistance is allowed; HUD-only changes are insufficient. Inventory and cosmetic tattoos must remain intact.
6. Save only to the disposable test slot, cold-reload and verify no duplicate refunds or stacked HP modifiers. Load an unrelated pre-Tower save: no restrictions, straight-shot forcing or stat modifiers should carry over.
7. Leave the accepted Afterlife content unchanged; bar NPC idle improvements remain deferred.
8. Confirm Lead and Steel, Bullet Deflect, blade finishers, Dash/Air Dash and Deep Breath/High Noon can be bought when native prerequisites are met. Check blade blocking in play and after reload. Air Kerenzikov, quickhacking, smart targeting and cyberware augmentation remain blocked. The switch itself must not restore any already-refunded ranks.

## File recovery

Use only `tools/deploy_restrictions_profile_implant_r3_2.ps1 -Mode ValidateRollback` followed by its `Rollback` mode with the game closed. It restores two backed-up R3.1 files. This is file recovery, not a reversal of saved progression or profile metadata; use the pre-update save with restored files. Earlier installers have obsolete hashes for these paths and must not be run directly against this installation.
