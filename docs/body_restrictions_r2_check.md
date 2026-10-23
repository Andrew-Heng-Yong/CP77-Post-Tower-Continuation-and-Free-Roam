# Body and perk nerf test

This opt-in command permanently reduces Body to 3, refunds every purchased modern Body perk rank, and enables the existing cyberware restriction profile. Body and Body-perk purchases are blocked while that profile is active. Character level, Street Cred, Solo and other skills, XP, other attributes, other perk trees and Relic points are not reset.

There is no reverse-respec command. Refunded progression is not restored by changing profile or removing the mod. Keep a separate pre-test save if you want a recovery point.

## Installation status

Follow-up: the [Relic extension](relic_restrictions_r2_2_check.md) was installed on October 7, 2026, at 4:40 p.m. Toronto time. The same command now opts an older Body-only save into Relic refunds and full tree closure without replaying completed Body refunds. Follow that guide for the current build. Current screenshots confirm Body 3 and the reported 17 Attribute/14 Body-rank refunds, but show stage 3 still waiting for safe gameplay; final measurement, Relic behavior and saved reload remain unverified.

The cost-check fix was installed on October 7, 2026, at 3:59 p.m. Toronto time, with the game closed. One script was backed up and replaced; its installed hash matches the tested candidate, and file recovery preflight passes. The other 1,407 tracked files and five cache/database files were unchanged. No save or story state was written.

The original R2 activation refused before starting the Body refund because the level-5 curve returns `1.00038397`, which its guard incorrectly required to equal `1.0` exactly. The installed correction uses the same integer cost conversion as native attribute purchases and retains rejection of unsupported costs. The Relic extension preserves this correction. Compilation and model checks do not establish in-game refund correctness. Current file recovery uses only `deploy_restrictions_relic_r2_2.ps1`; do not rerun the superseded R2.1, R2 or R1 installer against these files.

The original R2 deployment at 2:39 p.m. contained three new R2 script files and one backed-up replacement of the R1 policy for the already-approved normal Casius tattoo and two read-only readiness methods. Both Casius models and all eleven approved Basic Kiroshi records remain allowed. That installation preserved 1,371 other tracked files and five cache/database files. Neither installation activates the Body migration.

## Apply without changing HP or stamina directly

Load a genuine completed-Tower free-roam save. Use a disposable copy for the first test. Stand somewhere safe, holster weapons, close the ripperdoc and progression menus, and wait for any Adrenaline/Overshield to end.

Run this in CET:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):FullNerfWithoutVitals())
```

Close CET and remain in safe gameplay for about a minute. The command first waits for restricted cyberware removal to finish, then refunds one purchased Body perk rank per second, resets Body, and samples the resulting maxima. A locked implant or unsafe gameplay can keep it waiting longer. Do not make purchases, gain XP, enter combat or save during the first test.

Check progress:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):GetStatus())
```

`stage=4` means the transaction completed. The status reports actual refunded perk ranks and attribute points. `stage=5` means it stopped on a mismatch; do not try to repair points manually or repeatedly activate it. Capture the status and log, then load the pre-test save. A repeated activation never replays a completed or stopped refund.

Once complete, read the new values:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):Measure())
```

Send this output back. It includes current and maximum pool points, the Health/Stamina maximum stats, Body, and unspent points. **No direct Health/Stamina modifier, pool write, refill, regeneration change or numerical cap is applied by this build.** Native removal of Body/perk/cyberware bonuses can still change HP and stamina. Their resulting values are the baseline for choosing later numerical restrictions.

For the session log:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR2.BodyPolicy"):GetAudit())
```

## What to verify

Before activating, note Body, purchased Body perk ranks, Attribute and perk point balances, other attributes, character level, skills, and HP/stamina. After `stage=4`:

- Body is 3 and unspent Attribute points increased by old Body minus 3.
- Every purchased Body rank is gone; unspent regular perk points increased by the number of ranks removed, not merely the number of perk icons. Native modern refunds leave the internal Primary spent counter unchanged.
- Body attribute and Body-perk purchases fail without charging or granting points. Other attributes and other trees remain usable after the transaction.
- Character level, Street Cred, skill levels/XP, other attributes and non-Body/non-Relic perks are unchanged. The current Relic extension separately refunds purchased Relic perks and closes their tree as described in its guide.
- Cyberware removal retains owned items and parts under R1's existing rules. Inspect effects and actions too; inventory readback alone is not full effect-cleanup proof.
- HP/stamina output reflects the natural post-refund result. The code never explicitly refills pools, but native max-stat recalculation and transient effect cleanup still need live observation.

First verify the result without saving. Then, on a disposable test save, check completed-save reload, repeated activation, and a separate pre-Tower save. A saved mid-native-call marker stops instead of replaying. Clean acknowledged steps can resume only if the entire stored progression snapshot still agrees. These guards are not proof of engine save atomicity.

The existing R1 `NoNerf()` command is unchanged: it disables policy gates, not the permanent refunds. Reinvesting Body outside the profile does not authorize a second refund; a completed journal will stop on that disagreement. There is no automatic restoration or reconstruction of the old build.
