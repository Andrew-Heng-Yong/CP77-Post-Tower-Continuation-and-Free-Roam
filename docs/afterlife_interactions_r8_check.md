# Afterlife R8 — focused interaction check

SUPERSEDED: R8 failed live and crashed. R9 was installed 2026-10-06T14:35:03Z.
Use `afterlife_interactions_r9_check.md` and its safe pre-R8 rollback instead.
Do not test R8 or run the historical R8 rollback below against R9 files.

Installed 2026-10-06T05:31:43Z. Compilation/install checks pass; live results
are pending. Use a disposable post-Tower session and do not save this first
test. No forced quest facts, spawning commands or repeated Claire/crowd test.

1. Cold-launch the game. If your save starts inside Afterlife, walk fully out
   to the street first, wait a few seconds, then walk down and enter normally.
   Emmerick should return to the entrance start and then step aside to your
   left as you enter. Watch whether he settles at the side rather than
   drifting. Leave fully and re-enter once to check rearming.
2. Approach Rogue's booth. Check for gold eyes and local dialogue options.
   Options remain dependent on your existing quest/conversation history;
   R8 does not force every option visible or reset previously used choices.
   Try one short available exchange, then leave her area and return.
3. If either fails, report what happened plus this read-only CET status:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.AfterlifeInteractionsR8.AfterlifeInteractionsR8"):GetStatus())
```

Status groups mean permission/start/active/request-counter. Counters are
dispatch evidence, NOT proof an animation or dialogue was rendered. Capture
once outside, after entering, and beside Rogue if needed. World Inspector
still identifies the same private communities, not new copies. Emmerick may
show phase `PTFRAL8_Entrance` outside and `q005_emmerick_bouncer` after stepping.

First-visit success does not prove save/reload, streamed return, combat
interruption or long-session safety. Test those separately after the focused
visit passes. Preserve Claire's confirmed working dialogue and accepted crowd,
face, Nix, hologram and Zetatech results; no need to repeat them here.

If the build causes a regression, close the game and use the R8-only rollback:

```powershell
& ./tools/deploy_afterlife_interactions_r8.ps1 -Mode ValidateRollback
& ./tools/deploy_afterlife_interactions_r8.ps1 -Mode Rollback
```

This restores two backed-up files and moves only the added R8 script into a
recoverable backup. Do not use older R1/R2/R7 rollback instructions. No save
rollback or save editing is performed.
