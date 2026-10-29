# Viktor clinic access — VD1

Status: installed and file-verified on 29 October 2026. The user subsequently
reported that the door is fixed and resumed Open Beta 0.2.0 preparation.
This confirms opening in their run; streaming and save/reload were not separately
itemized. No public release was made by the repair task.

The user reports that Viktor's downstairs clinic door cannot be opened after
The Tower and the return to free roam. This report concerns the post-ending
world, not the ending sequence.

## Cause and repair

The current native `q307_06_viktor.questphase` locks
`#q115_dvc_ripperdoc_room_door` at node 42 and closes it at node 44. The existing
R11 access owner restores the upstairs front and inner doors and the rear shop
door; it has no clinic-door action. This is a concrete missing restoration step
consistent with the reported blockage. The current live door's full device
state has not been captured.

VD1 adds a separate private native quest phase for the exact clinic door:

```text
$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/single_door_prefabSSNK5BI/#q115_dvc_ripperdoc_room_door
```

It preserves all 17 existing world-access gates and additionally waits for
`PTFRPA2_Finished=1`. Once the door is loaded and the guards pass an immediate
recheck, it sends one native `ForceUnlock`. The native handler clears lock and
seal without forcing the door open. Requests rearm only after streaming loss or
guard loss. A mod-owned claim prevents duplicate ownership; all diagnostic
writes use `PTFRVD1_`. No native quest facts, story scenes, rewards, service
owners or existing saved node identities are reset.

The full successor retains 51 installation paths. Only the combined archive and
its XL registration change. All 1,563 LC4 resources remain byte-identical, with
one new private phase bringing the archive to 1,564 members. All existing
registrations remain unchanged; one registration is added. REDscript sources
are unchanged.

## Evidence and limits

- Fresh 133-archive census: the native Viktor phase and scene have one provider
  each, R11 has the expected PTFR provider, and the new depot has no collision.
  The clinic sector has the expected base-game and Phantom Liberty providers;
  no mod overrides it.
- WolvenKit 9.1 cannot fully decode that native sector because of an unknown
  `worldNode` class. The sector is preserved without editing. The exact clinic
  identity comes from the established native mapping and prior runtime probe;
  the freshly extracted native phase still addresses that clinic alias.
- All 1,564 archive members were read back. Independent serialized graph checks
  cover 89 assertions and 262,144 combinations of the 18 fact guards.
- The current 112 REDscript sources and archived compiler output match the
  successful WA3 compile exactly. No recompilation was necessary for this
  archive/XL-only change.
- Six deployment fixture cases passed, including five interrupted installations
  followed by rollback (20 actions in total). Actual game-closed Validate,
  Install, Verify and ValidateRollback passed. All 52 managed files match, and
  all 307 save files retain their names and bytes. Only the combined archive
  and XL registration were replaced. The game was not launched.
- `EndGameSave-62` was read without changes. No matching persistency entry was
  found under the historical entity ID; this does not establish an unlocked
  door or the user's latest live device state.
- Candidate 01 stopped before creating the owner because a builder argument
  was missing. Candidate 02 is the selected, verified resource.

The relevant records are under `prealpha/viktor_door_vd1/candidate_02` and
`native_review_03`; the earlier native-review attempts retain the sector
provider/decode findings. Physical opening, streaming and save/reload behavior
remain unverified until observed in gameplay.

The full unreleased successor ZIP has SHA-256
`ADA69E9D0AF95E2B836BD0914D7E9F4E3F7BEF09782F46506AD8F2B7B5EC2E62`.
The installed outcome and exact file hashes are recorded in
`prealpha/viktor_door_vd1/candidate_02/assessment_01.json`.

## Recovery

After a successful installation, use
`prealpha/viktor_door_vd1/deploy_01.ps1 -Action ValidateRollback`, then
`-Action Rollback`, with the game and launcher closed. VD1 must be rolled back
before LC4. The backup is `recovery/viktor_door_vd1_01`. File rollback does not
undo device or quest state subsequently stored in a save.
