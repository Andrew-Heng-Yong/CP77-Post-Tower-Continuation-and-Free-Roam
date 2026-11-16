# KM1 KOLD MIRAGE check

Use the post-Tower working save on which the Dexter/freezer approach did nothing. The successful pre-ending comparison is recorded and needs no repetition. Keep that comparison save separate.

After installation, start the game normally and let PTFR finish startup. The admission check now accepts `mq016_active=0` or `1`, with every other progress, history, receipt, Tower and support gate retained. No quest fact or save was reset.

1. Before discovering the encounter, check for its undiscovered side-job marker. If the save loads inside the approach trigger, discovery may happen immediately and the active objective can replace that marker.
2. Approach or scan the freezer. Check that the native Open interaction and objective appear. Dexter's separate Johnny discovery scene is not required or restarted by this fix.
3. Open the freezer and take the cyberdeck through normal interactions. Continue to Nix and use the native rescue/progression route. The installed JP1 Johnny/V dialogue removals and menu bypasses remain in place.

Report whether the marker/objective appeared, the freezer could be opened, the deck could be taken and progression continued. Fixed scene timing from JP1 remains, so silent pauses are still possible.

If it stalls, this CET command only reads admission status:

```lua
do local s=Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")); if IsDefined(s) then print(s:Status()); print(s:Inspect("mq016_bartmoss")) else print("S29 system unavailable") end end
```

Once issued or progressed, `currentMatch=false` can be expected: the fresh-state sample is no longer the quest's current stage. Do not clear facts or reissue the owner. This fix remains limited to an Inactive quest and its Inactive checked objectives; it does not reopen completed/failed quests or restart a later active stage.
