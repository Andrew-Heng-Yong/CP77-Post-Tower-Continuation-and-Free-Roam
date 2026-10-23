# Afterlife R9 — focused interaction check

SUPERSEDED after live failure/crash. R10 safety build installed
2026-10-06T18:50:56Z. Use `afterlife_interactions_r10_check.md`; do not run the
historical R9 test or rollback below against the R10 installation.

Installed 2026-10-06T14:35:03Z. R9 corrects the Rogue actor-index defect found
in the crash dump and revises Emmerick's admission gates. Offline checks pass;
the engine's visual behavior is not yet verified. Keep this first visit
disposable and do not save. No quest-fact writes or spawn commands are needed.

1. Cold-launch. If the save starts inside Afterlife, walk fully outside to
   the street, wait a few seconds, then walk down and enter normally. Watch
   Emmerick return to the entrance and step aside to your left. Check he
   settles at the side. Leave fully and enter once more to check rearming.
2. Approach Rogue. Check her gold eyes and local dialogue choices; try one
   short available exchange, then leave her area and return. Choices remain
   conditional on existing quest/conversation history, not forced to match
   every pre-Tower screenshot. Her Tower appearance remains unchanged.
3. If Emmerick remains stuck, capture this read-only CET status once outside
   and again just inside, close to him. If Rogue fails, also capture it there:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.AfterlifeInteractionsR8.AfterlifeInteractionsR8"):GetStatus())
```

It should say `Interactions R9`. The class path deliberately still says R8.
`native=9` is written on fresh native root entry; a saved in-progress wait
can retain an older value until that entry executes. Report it; do not force it.

| Stage | Meaning |
| --- | --- |
| 1 | Waiting for permission and player outside |
| 2 | Return-to-start issued; waiting for entry trigger |
| 3 | Waiting for native player-to-Emmerick distance <=5m |
| 4 | Waiting for runtime anchor readiness |
| 5 | Step-aside scene requested |
| 6 / 7 | Completed / cancelled (brief intermediate states) |
| 8 | Waiting for departure before rearming |

`E` and `R` groups are permission/start/active/request-counter. Completion and
cancellation counts, plus `anchor`, `facingDot`, `workspot`, `quiet` and
`distance`, help locate a blocker. Counters and active flags are NOT proof
that animation/dialogue rendered. Existing Inspector communities stay the
same. Emmerick may show `PTFRAL8_Entrance` then `q005_emmerick_bouncer`.

If the game crashes, stop testing, keep it closed and report when it happened.
Do not retry the old R8 build. A focused success here does not establish saved
reload, combat interruption, streamed return or long-session stability.
No need to repeat accepted Claire/crowd/face/Nix/hologram/Zetatech checks.

## Safe rollback, if needed

With the game closed, run from the workspace:

```powershell
& ./tools/deploy_afterlife_interactions_r9.ps1 -Mode ValidateRollback
& ./tools/deploy_afterlife_interactions_r9.ps1 -Mode Rollback
```

This restores the pre-R8 archive and XL, and moves only the interaction
runtime into a recoverable backup. It does **not** restore the crashing R8.
Other accepted restorations and booth R6 remain installed. Do not run the
earlier R1/R2/R7/R8 rollback tools against the R9 archive. No save is edited.
