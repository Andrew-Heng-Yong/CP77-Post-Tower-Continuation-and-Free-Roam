# Booth R6 — installation and focused animation check

R6 INSTALLED2026-10-06 at00:16 Toronto, with exact backups and rollback
preflight verified. R5 appearance/type USER-pass and R2 density are preserved;
this check is only for the four booth NPCs. Live animation is still pending.

The following installation commands document the completed deployment;
do not reinstall over the receipt. Installer default is validation:

```powershell
./tools/deploy_afterlife_booth_r6.ps1 -Mode ValidateInstall
./tools/deploy_afterlife_booth_r6.ps1 -Mode Install
./tools/deploy_afterlife_booth_r6.ps1 -Mode ValidateRollback
```

Install backs up and replaces exactly the R3 private archive and its runtime
script. Do not use the old R3 additive installer or rollback to remove R6.
Do not hot-reload the scripts or copy archives while the game runs.

After the actual installation receipt exists:

1. Cold-launch an untouched/disposable completed-Tower save, not a new save
   made with the actor stranded on the table. Do not save during this test.
2. Approach the booth. Once spots are ready and actors are at their original
   anchors, they should begin their three-seated/one-standing routines shortly,
   without the previous roughly11-second controller delay. Native streaming
   delay is not eliminated. Record any floor/table alignment problem.
3. Watch for90 seconds. The three native gesture lists should keep running;
   the lean270 seated actor has a quieter base idle, not a new gesture set.
   They should not routinely finish, walk away and repeat the startup sequence.
4. Read status in CET:

```lua
local s=Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.AfterlifeIdlesR3.AfterlifeIdlesR3")); if s then print(s:GetStatus()) end
```

The label must say `Booth R6`. Each entry reports requests, direct starts and
current workspot state. Dispatch/workspot flags alone do not prove animation.
If an actor leaves or stands on the table, also record the diagnostic mark:

```lua
print(GetMod("PTFR_Afterlife_Behavior_Audit").Observe("R6-booth-issue"))
```

Send the observation and new `afterlife_behavior_*.jsonl` filename; no need
to repeat the root animation component screenshots. Quit without saving.
Only after initial success: leave/return, then separate disposable save/reload
and interruption checks. Do not claim those pass from the initial visit.

Recoverable rollback, game closed:

```powershell
./tools/deploy_afterlife_booth_r6.ps1 -Mode ValidateRollback
./tools/deploy_afterlife_booth_r6.ps1 -Mode Rollback
```

Only two backed-up R3 files are restored; R6 versions are also backed up.
The accepted R5 appearance fix remains installed.
