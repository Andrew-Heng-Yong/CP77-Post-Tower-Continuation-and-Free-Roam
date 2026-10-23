# HP 150 after death/checkpoint reload — R3.3

Installed 2026-10-12. One replacement: `r6/scripts/PTFR_Restrictions_R3/ProfilePhysical.reds`. No gig, phone, reward, profile selection, perk/refund, Body, Relic, stamina or save-file changes.

## What changed

The old HP limiter's first unsaved modifier was gated by `BodyPolicy.Safe`. A restored physical module has no retained modifier, so combat, a drawn weapon or the native phone content lock could defer the cap after loading. This is a source-confirmed defect consistent with the reported symptom; the reported checkpoint was not instrumented, so this does not prove it was the only cause in that session.

An already-approved HP policy now waits only for its live, attached local player, available stat services and positive registered Health stat/pool maxima. Loading, death and replacers defer HP application and pause the outstanding pool acknowledgement budget. Combat, weapons and phone content locks do not prevent HP reapplication. Existing saved opt-in, active mode, profile fingerprint and stage checks still govern eligibility. Initial FullNerf/migration safety remains unchanged. Only retained owned modifiers are managed; the existing negative-only, single-request correction is unchanged.

## Short live check

1. Cold-launch the game. Load the save you kept after completing Jeopardy, **if you saved it**. Otherwise use a normal post-Tower test save where the HP profile was already enabled. Do not reload original ManualSave-20 just to replay Jeopardy, and do not rerun U7/U4 Start or a gig batch.
2. Close menus and let gameplay run for 3 seconds. A weapon may remain drawn. Open CET and run:

   ```lua
   print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR3.ProfilePolicy"):Measure())
   ```

   Expect `target=150`, max Health/stat/pool approximately 150, and `HP R3.3`. Current HP can legitimately be below 150. `HP requested=false` means this save opted out; do not force it on as part of this test.
3. For the actual reported regression, die and use **Load Last Checkpoint** from a disposable test session. No gig completion is required. After control returns, close menus for 3 seconds, leaving your weapon drawn if it is already drawn, then repeat Measure. Max Health should again be 150. This test, not the offline compile, closes the checkpoint bug.
4. If HP is wrong, also capture this getter without running FullNerf again:

   ```lua
   print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR3.ProfilePolicy"):GetStatus())
   ```

Do not overwrite the original recovery saves. No new save is required merely to test HP, and you can close the game after reporting the output.

## Separate U7 result

The user reported Jeopardy completed and the post-completion Padre call played, after a death/checkpoint reload. Record these as user-reported passes. Native fixer credit, owner cleanup and a separate newly saved/reloaded completion are not verified by that report alone.

If you retained that completed session as a save, this read-only command can check it without replaying the gig:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeSupportU7"):Inspect())
```

## Evidence and recovery

`research/restriction_profiles/profile_hp_reload_r3_3/` contains staged compiler logs/readback, tests, exact install receipt and predecessor backup. Both compilers and the full installed script set (including EquipmentEx) passed. 384 admission, 768 readiness and 64 feedback/reload model cases passed; these are not engine execution. A one-file install/recovery fixture rejected six unsafe cases.

Only `tools/deploy_profile_hp_reload_r3_3.ps1` owns recovery of this current replacement. With the game closed, its ValidateRollback/Rollback modes verify exact hashes and retain the removed candidate recoverably. Rollback restores the earlier HP gate, not game state. Original R3 aggregate recovery is historical for this replaced path. Predecessor evidence and source stay pinned; the current repair source is `build/ProfileHpReloadR3_3/ProfilePhysical.reds`. Do not rerun the installed test main or rewrite its receipts.
