# Jason Foreman saved freeze and wake check

**AutoSave-8 has no saved original Jason wait for either native restoration or deferred-input wake to recover.** The saved freezer contains the installed PTFR admission gate. The earlier AutoSave-16 fixture still provides a positive control for what a native approach registration looks like. The prepared-state coverage gap stays open. [Selected-save comparison](../latest_save_01/REPORT.md)

## Saved records

The analysis rechecked the exact November 4 AutoSave-8 body and metadata. It read the previously extracted `questPhaseFreezer` child, ID `975`, against the pinned Cyberpunk executable's writer and loader. The 1,104-byte span contains 12 groups and 71 members, with zero deferred input words. All group owner and member hashes resolve uniquely against the saved path table. None match the original Jason subtree or any exact Jason phase-owner address along its ancestor chain. That includes `openworld/root/2:3` for approach, `openworld/root/2:14` for courier, and `gameplay/root/1:102` for the vehicle wait. A separate full-width `eventManager` check also found zero retained original Jason descendant registrations. [Machine-readable records and instructions](analysis_01/result.json)

The installed ArchiveXL entry at line 2418 targets `ep1\quest\ep1.quest` and attaches `towercontinued\native_gigs_u9\sts_ep1_03_entry.questphase` after node `1.Out`. Its generated ID `48952` matches the typed parent phase slot `8305` in the save. It does not collide with a node in the original EP1 root. Freezer group `5` has owner `[1,48952]:50` and members `[1,48952]:50` and `[1,48952,50]:65002`. Both arrays are empty. Node `50` uses `#combat_zone_content_tr` as its unfreeze reference. The report keeps the saved trigger key separately from that authored reference.

Node `65002` is the U9 admission wait. Its AND requires the existing Jason request and permit both equal to `1`. Its output leads through the Ronald arm writer `65007` to the parent-entry receipt at `65003`. The original main phase starts farther downstream via `65004.Out → 19.In1`. The saved private gate does not establish native main entry or actual live handler ownership.

## What the engine can recover

The matching executable routes QuestsSystem `+0x1A0` through freezer save/load slots `+0x90/+0x98`. The writer at `0x2CD9A24` and loader at `0x438888` agree on the group key, packed phase/node keys and variable-length deferred arrays. Wake processing at `0xBEB194` matches existing group records and supplies their members to `0xBEA6CC`. The mode-6 dispatch at `0xBEA753..79E` is inside the deferred input loop, reached only when an input exists. This loop has no Jason input to dispatch from the selected save. Separate live callbacks and natural reevaluation of the private gate were outside this check.

Mode-2 save restoration consumes existing `eventManager` slots. The selected save has none for the original Jason descendants. The retained Codeware source for `ExecuteNode` instead uses the root phase with mode 1. The installed pinned DLL contains that method name. This source and name check supplies no saved-slot rebind contract. [Native save restoration](../event_stage_01/quest_handlers/REPORT.md)

## Implementation gate

The fresh gate still rejects the existing preparation flag. Relaxing it would start the full original `In1` route, including branches with unresolved setup state. A compatible continuation needs a supported way to rearm the native approach under the correct phase and prefab ownership. It must preserve the existing car identity and distinguish pending from already applied vehicle work, and pending from consumed courier work. The saved car activation record and shared counter cannot make those distinctions. The remaining startup branches also need a preservation contract. [Startup branches](../effect_contract_01/run_01/BRANCH_MATRIX.md) and [offline continuation prototype](../resume_prototype_01/REPORT.md)

Further implementation needs positive evidence of those stages or a continuation that preserves both histories. Another scalar snapshot, leaving and reentering the combat zone, or calling a direct node executor would not establish that contract. There is no new gameplay test or runtime candidate for this save.

## Reproduce

From the workspace root, with the pinned executable, archive pair, selected save, captured components and existing local Python/Capstone tooling:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr15\rebind_01\analyze.py' --out analysis_02
```

The command checks the save and metadata hashes before and after, then writes only `analysis_02/result.json`. It refuses an occupied output directory. The decoder rejected eight malformed variants of the real capture and decoded an independent nonempty record. The stage also rechecked 77 installed paths and six protected save files against their pinned hashes. The installed Core and diagnostics were preserved.
