# Local pre-ending history test

Installed over `QP2_TOWER_EVENING_RECOVERY` on 12 November 2026. The test uses the genuine revision 159 export from Reed’s pickup. The Lua command reads the original file. The REDscript system compares all 158 rows against the loaded save’s retained history in the simulation before selecting that history for admission. Selection ends when the save reloads. The normal export stays bound to the save’s canonical snapshot. [Original capture](../johnny_load_crash_20261111_01/observations/manual_save_26_pickup_01/REPORT.md)

## Run the test

Load the existing post-Tower `AutoSave-5`. A read-only decode verified all 158 retained rows against the revision 159 export and the identical 80,702-byte payload in `AutoSave-16`. Once V is in free roam, run this in CET. [Retained save history](retained_history_readback.json)

```lua
print(GetMod("PTFR_HistorySnapshotHS1").UsePreEndingForTest("20261111T224622Z_159_1"))
```

Close CET briefly so simulation can verify the rows. Reopen CET and check the result.

```lua
print(GetMod("PTFR_HistorySnapshotHS1").TestHistoryStatus())
```

The expected result is `Using verified pre-ending revision 159 for this test session.` A refusal means the loaded save did not meet the selection checks. The test requires a verified post-ending fallback, genuine Tower completion and exact equality with the retained rows.

## Quest stages that still defer

I compared the stage inputs in the revision 159 and 160 exports with the current REDscript and six decoded resources read directly from the installed archive. The four S22 adapters all require an Inactive root in REDscript. Each also checks it twice inside its own quest graph before starting a replacement owner. The post-ending export shows all four roots Failed and all four private Issued receipts at zero.

| Quest | Evidence on this save | Installed graph admission |
| --- | --- | --- |
| Moving Heat | The cutoff objective was Reach the door. Every tested fact and every other journal field matches the current first-door adapter. | `moving_heat_boot` nodes 2 and 3 require Inactive. The current boot then checks for an Active acknowledgement at node 9 before entering inline phase 1200. |
| Beat on the Brat | The cutoff had four active find-the-fight objectives. Every tested fact and every other journal field matches the adapter for after the introduction and before the first bout. | `mq025_progress` nodes 1001 and 1002 require Inactive before the path to native continuation node 55. |
| The Gig | Wakako’s cash reward is recorded. The pending objective is the remaining tattoo reward. Every tested fact and every other journal field matches the reward adapter. | `the_gig_reward_resume` nodes 1001 and 1002 require Inactive. The route is scoped to the earned tattoo objective. |
| Epistrophy | Northside was active at the cutoff and is now Failed. `sq025_scan_scared_intro_done` is 0 and the adapter expects 1. | The Delamain owner nodes 1002 and 1003 require Inactive. The current stage also needs its own Northside introduction review. |
| Small Man, Big Mouth | Revision 159 records an Active root. Both hospital and post-Tower save records mark Meet Kirk Failed. The snapshot carries the root alone for this job. | S29 requires an Inactive baseline and the wrapper nodes 65003 and 65004 require an Inactive live root. The QP2 garage repair acts later in the fresh-entry route. |

Moving Heat, Beat on the Brat and The Gig match the recorded stage facts and journal inputs outside the root gate. The snapshots and graph readback establish those predicates. Saved-owner retirement, required leases, reload behavior and exactly-once rewards need independent qualification before changing their admission. [S22 stage inputs](../tower_evening_recovery_20261112_01/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS22.reds) · [S29 admission](../tower_evening_recovery_20261112_01/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds) · [Installed archive readback](fixtures/graphs_01/inventory.json)

## Verification

All 148 registered REDscript sources compiled offline. The actual Lua command passed the 158-row export fixture and the negative input checks. Nine installer actions passed across clean rollback, interrupted replacement recovery and game-running refusal. The closed-game deployment verified all 51 Core files, all 26 required dependencies, 349 byte-identical save files and file rollback readiness. In-game request handling and admission are pending. [Installed manifest](deployment_01/installed_manifest_01.json) · [Compile result](compile_02/result.json) · [Lua and source checks](candidate_02/test_readback.json) · [Installer fixtures](fixture_results.json)
