# R10 — stability and Emmerick check

Installed 2026-10-06T18:50:56Z. This is the approved stability-first build,
not yet a proven crash fix. Live appearance changes and Rogue's dialogue/eye
glow adapter are disabled; population and restored named NPCs remain.

1. Cold-launch using a disposable test save, preferably from before the R8/R9
   interaction tests. Do not overwrite your main save or save this first visit.
2. Walk fully out to the street, pause 10–15 seconds, then approach slowly.
   Let Emmerick settle at the entrance before walking past him. Watch whether
   he steps aside and stays at the side. Leave and re-enter once. His earlier
   return-to-start movement was delayed, so a quick first pass can miss him.
3. Walk through the bar briefly to check stability. Do not expect Rogue's
   dialogue/glow or guaranteed unique faces in this build. No Inspector scan
   or console command is required; the new diagnostic records automatically.

Report whether Emmerick moved and whether another crash occurred. The newest
file beginning `afterlife_interactions_` is under:

`C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit/`

Its one-second samples include the entry stage, exact distance permission,
anchor/facing readiness, scene requests and completion/cancellation counts.
The older eight-second `afterlife_behavior_` files remain available too.
Counters are not proof of visible animation. There is no need to repeat
accepted crowd-density, Claire, Nix, hologram or Zetatech tests.

If another crash occurs, keep the game closed and report where it happened.
Do not re-enable R5 or Rogue with facts/old files. A short successful visit
does not prove saved reload, scene interruption or long-session stability.

## Rollback if needed

With the game closed, from the workspace:

```powershell
& ./tools/deploy_afterlife_interactions_r10.ps1 -Mode ValidateRollback
& ./tools/deploy_afterlife_interactions_r10.ps1 -Mode Rollback
```

This restores the pre-R8 interaction archive/XL and recoverably removes only
the interaction runtime. R10 face suspension and diagnostics remain. No save
is edited. Do not use R1/R2/R7/R8/R9 rollback tools against this installation.
