# Emmerick R7 focused check

After an R7 install receipt, cold-launch a disposable completed-Tower save.
Do not save during this first check. No CET mutation commands are required.

1. Approach Afterlife from outside its streamed area. If loading inside,
   travel well away first and return so the old private spot unloads.
2. Watch Emmerick at the entrance for 60–90 seconds. Expect one Emmerick near
   (-1457.196,1026.172,16.793), with the vanilla varied standing gestures rather
   than a fixed bodyguard pose. Brief neutral standing is not itself failure.
3. Look at him with World Inspector or the gameplay crosshair, then capture:

```lua
print(GetMod("PTFR_Afterlife_Behavior_Audit").Observe("posttower-emmerick-r7"))
```

4. Report whether his visible movement matches the pre-Tower observation,
   whether placement is correct, and the log filename. If still static, send
   his entry/phase, entity ID and position; do not toggle story facts.
5. Quit without saving. A second return and disposable save/reload are separate
   validations, not implied by a successful first visit.

The private phase may still display `q005_emmerick_bouncer`: retained for
compatibility, not evidence that the old workspot is installed. The same
private alias is now backed by the observed entrance02 routine. No repeated
crowd-density, Nix, door or hologram test is needed.

The four booth actors keep R6; their optional 90-second visual check is in
afterlife_booth_r6_check.md. Pre-Tower scenes do not validate post-Tower R6.
Rogue dialogue/glow and optional Claire choice parity are not fixed by R7.

With the game closed, exact R7 rollback is:

```powershell
./tools/deploy_afterlife_emmerick_r7.ps1 -Mode ValidateRollback
./tools/deploy_afterlife_emmerick_r7.ps1 -Mode Rollback
```

It restores only the backed-up R2-based archive; never use the older R1 rollback.
