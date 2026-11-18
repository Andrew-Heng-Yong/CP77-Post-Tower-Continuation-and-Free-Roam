# KM3 — KOLD MIRAGE retest

**Retest update:** the user reported “ok the fix passed”. The start correction is USER_REPORTED_PASS; do not repeat that successful check. [Observation and limits](OBSERVATION_20261116.md).

The steps below preserve the original test procedure. Full completion, reward and reload checks were not individually reported. KM3 is installed; the installer did not launch the game. Keep ManualSave-32 intact.

1. Start the game normally and load **ManualSave-32**. Let PTFR reach its usual ready state in free roam.
2. Approach the freezer near Dexter's body. If the save loads inside the encounter area, leave and approach again. Check for the marker or an active quest objective, then use the normal freezer interaction.
3. Confirm KOLD MIRAGE enters the journal and offers its normal next objective. If it starts successfully, continue through taking the cyberdeck and talking to Nix. Use a **new save slot** for any new save.
4. Once a new slot exists, reload it and confirm the quest retains its progress without replaying setup or granting a duplicate reward. Completion/reward behavior is a separate check from the opening.

If the opening still does nothing, run this existing read-only CET check and report its output:

```lua
do local s=Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")); if IsDefined(s) then print(s:Inspect("mq016_bartmoss")) else print("S29 unavailable") end end
```

The immediate expected change is **Entered=1**; Issued remains 1. Do not set facts, reset journals, spawn scheduler tokens or reissue the quest. A successful opening does not by itself qualify every outcome, reward or future save upgrade.
