# R11 — Emmerick, Rogue and removal check

**Installed 2026-10-06T19:13:43Z, live pending.** Build, exact installation hashes
and safe-rollback preflight passed. Live success is not yet proven.

R11 is intended to restore Emmerick's step-aside and Rogue's local dialogue/gold
eyes while removing live face changes and the ten tube dancers. Duplicate
ordinary faces may return; crowd quantities and restored named NPCs are retained.

1. Cold-launch a disposable test save, preferably from before the R8/R9
   interaction tests. Do not overwrite your main save or save this first visit.
2. Walk fully outside Afterlife to the street. Let Emmerick settle, then re-enter
   normally. Look for a continuous step to your left out of the doorway—not
   merely appearing at the side, turning, or returning to his start position.
3. Approach Rogue's booth without starting another conversation. Check whether
   her available local choices appear and her eyes glow during the interaction.
   Try one offered optional line, then leave normally. Choices retain vanilla
   eligibility/history; not every earlier screenshot option is forced open.
4. Check that the hologram tubes are empty. Do not expect unique faces among
   ordinary patrons: live face changes have been removed.
5. Leave the bar fully and return once. Check Emmerick's response and Rogue's
   dialogue/glow again, then quit without saving.

No Inspector scans or console commands are needed. The existing automatic
one-second `afterlife_interactions_*.jsonl` trace records entry stages,
permission checks and outcomes, including the new driver status. Files are in:

`C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit/`

Report: continuous Emmerick step yes/no, Rogue choices and glow yes/no, tubes
empty yes/no, return result, and any crash. If anything fails, send the newest
trace filename; no repeat of accepted Claire, Nix, crowd-density or Zetatech
checks is required. A request/completion counter alone is not visual proof.

If the game crashes, keep it closed and report where it happened. Do not force
facts, re-enable old face code or restore old R8/R9 files. R10's one crash-free
visit did not establish the crash's cause; R11 still needs live verification.
This short visit does not prove long-session stability or saved reload.

## Safe fallback after an R11 installation

With the game closed, from the workspace:

```powershell
& ./tools/deploy_afterlife_interactions_r11.ps1 -Mode ValidateRollback
& ./tools/deploy_afterlife_interactions_r11.ps1 -Mode Rollback
```

This returns interactions to R10 quarantine while **keeping dancer retirement,
the inert face-policy shim and passive diagnostics**. Rogue remains present,
but her dialogue/glow are disabled in that fallback. No save is edited. Do not
use older rollback tools against this installation.
