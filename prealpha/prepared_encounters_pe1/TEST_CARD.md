# PE1 post-Tower check

After the verified installation, start the game normally and load the existing genuine post-Tower working save. Let PTFR finish startup and native setup settle before checking markers. The user [observed markers appearing after a delay](observations/kold_no_marker_20261108_01/REPORT.md); no fixed duration was measured. No ending replay, new campaign, save reset or fact command is needed.

The KOLD MIRAGE marker appearance is now user-reported after the delay and needs no special repeat. Continue by approaching/scanning the freezer and checking the Open interaction, cyberdeck pickup and normal progression. Loading inside the approach area can discover it immediately, replacing the undiscovered marker with the objective. The separate Dexter Johnny discovery scene is not required. JP1's dialogue cuts and menu bypasses remain; silent scene timing can remain.

For other naturally unfinished, unclaimed entries in the [covered list](REPORT.md), check the expected native marker, message or approach and then normal entry. Original prerequisites, timings and entitlement still apply; this does not promise that all markers appear immediately. Completed/failed jobs and progressed or already-issued owners stay preserved. Previously completed Bullets, Shoot to Thrill, Jeopardy, Ronald and Voodoo Treasure tests do not need repeating.

If KOLD MIRAGE still stalls, this CET command reads status only:

```lua
do local s=Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")); if IsDefined(s) then print(s:Status()); print(s:Inspect("mq016_bartmoss")) else print("S29 system unavailable") end end
```

For another entry, report its name, whether the marker/normal offer appeared, whether it entered and where it stopped. Admission still defers when the cached baseline is missing/contradictory or another protected stage fact is set. Once an owner has entered, a fresh-state mismatch can be expected; do not clear facts to make it match again.

The pre-ending KOLD MIRAGE comparison is already recorded and needs no repetition. Installation rollback changes files only and cannot undo saved gameplay progress.
