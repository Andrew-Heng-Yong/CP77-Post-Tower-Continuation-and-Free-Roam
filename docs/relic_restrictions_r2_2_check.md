# Relic restriction test

The Relic extension was installed on October 7, 2026, at 4:40 p.m. Toronto time with the game closed. Two scripts were backed up and replaced and two were added. Installed hashes and file-recovery preflight pass; in-game verification remains pending. Keep a separate pre-test save: native perk refunds are not automatically reversed by removing the mod.

## Activate

Launch the game afresh. Load a completed-Tower save, close menus, holster weapons and leave combat, scenes, workspots and active Overshield. Note purchased Relic perks and available Relic points first.

Use the same command as before:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):FullNerfWithoutVitals())
```

On an existing Body-only save this adds the Relic restriction without replaying the completed Body refund. A fresh activation applies both. If the old Body transaction has not completed, its stored progression must still match; do not spend points or gain XP during that transaction.

Close CET and remain in safe gameplay until complete. Then check:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):GetStatus())
```

Expect `Relic enabled=true` and eventually `stage=4`. Stage 3 now includes Relic refunds before the final HP/stamina measurement. Stage 5 is a fault: capture status and audit output, then use the pre-test save; do not manually adjust points or repeatedly reactivate.

## Verify

- Each purchased milestone returns 3 Relic points; each purchased child returns 1. A fully purchased tree returns 15 points. Partially purchased trees return less.
- Reopen the character menu. The Relic category and Johnny placeholder should be absent; keyboard/controller tab cycling should skip Relic. Ordinary attributes and perk trees should remain usable after completion.
- Run `Measure()` to see the retained Relic-point balance and natural HP/stamina values. There is no direct HP/stamina override.
- Check that Body remains 3 and its previous refund totals are not repeated, while other progression and inventory remain unchanged. Check Relic gameplay effects as well as the menu.
- Repeat the activation command and verify no additional refund. After the first no-save test, use a disposable test save to check completed reload and a separate pre-Tower save.

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):Measure())
```

Do not overwrite your pre-test save until the result is verified. Hiding the tree does not erase points or change the story fact that unlocked it.

For file recovery, use only `tools/deploy_restrictions_relic_r2_2.ps1`: it restores the two backed-up scripts and recoverably removes the two additions. Earlier R2/R2.1 installers and receipts are historical for the replaced paths. File recovery does not reverse saved progression changes.
