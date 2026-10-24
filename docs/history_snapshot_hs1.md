# Quest history snapshot HS1

Installed locally on 24 October 2026. Compilation, exporter tests, installed
hashes and rollback validation passed. Native capture, saving and reload still
need an in-game test. The public release package has not changed.

The earlier probe kept evidence inside the save and could certify selected
gigs when it observed them before the ending cutoff. It did not produce a
standalone snapshot file or accept a new current-state baseline after the ending.
HS1 adds both, following the user's explicit acceptance of post-ending history.

## Capture and file behavior

1. During ordinary pre-ending play, HS1 periodically reads the selected quest
   roots, available objectives and associated facts in bounded batches. At the
   native point-of-no-return signal, it freezes a recent settled observation as
   `pre_ending`. Entries that changed between checks cannot admit new quests.
2. A save that reaches genuine Tower completion without a valid frozen snapshot
   gets a snapshot of its current state, labelled `post_ending_fallback`. This
   is an accepted baseline, not a claim about what happened before the ending.
3. CET exports and reads back a JSON file. New quest admissions and the added
   startup path wait for acknowledgement of that verified file. Once frozen,
   the baseline is retained; restored quests do not become a new baseline.

The snapshot payload and its filename token belong to the individual save.
The external JSON is a readable companion file. If that file is missing but
the save still contains its snapshot, HS1 recreates the file from that stored
payload, retaining its origin. Only a save with no valid frozen snapshot needs
a new post-ending capture. An incompatible saved schema is held for migration
instead of silently replaced.

Files appear in:

```text
Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_HistorySnapshotHS1\
    snapshot_hs1_<UTC>_<revision>_<counter>.json
```

A file is written when the snapshot freezes, not after every ordinary-world
refresh. The exporter writes a temporary file, verifies it, renames it and
verifies the result before acknowledgement. A differing existing file is kept
and a new filename is chosen. Partial writes are not acknowledged. There is
no global "latest snapshot" selection or arbitrary JSON import between saves.

The JSON contains source, catalogue revision, quest definitions, journal states,
objective counters, tracking/optional flags, associated facts and stability
results. Genuine older pre-ending certificates are recorded separately; the
fallback does not fabricate those certificates.

## Restoration rules and scope

- Completed and failed entries in the accepted baseline remain preserved. A
  post-ending failed entry may have failed during ending cleanup; HS1 does not
  guess its earlier state or automatically revive it.
- Unstarted selected quests must still pass their native eligibility and
  existing owner/reward checks. Inactive journal state alone is insufficient.
- Active quests use the existing supported resume paths. An unsupported stage
  is deferred without resetting objectives, choices, items or rewards.
- Unknown, unstable and unselected entries cannot receive new admission.
  Already issued owners are retained rather than restarted or cancelled.
- Family Heirloom can use recorded Ghost Town completion plus its two required
  outcome facts from the accepted snapshot. This does not rewrite the original
  `familyPreTowerCompleted` witness or complete the prerequisite quest.

The snapshot covers **158 selected roots**: 80 gigs and 78 side jobs. Current
installed catalogues provide detailed evidence for 140 entries; 18 have root
observations only. Snapshot coverage does not add restoration implementations,
generic stage resume, or complete recursive dependency enforcement.

## Startup change included with HS1

The former startup predicate could wait for profile/housing completion before
allowing those systems to initialize on a late-ending save. The new path accepts
a verified snapshot and the completed native arrival/control/camera conditions
without requiring that circular completion condition.

The retained AutoSave 8/9 failure has a separate, narrowly bounded continuation:
HS1 records its own recovery state before clearing the exact preparation timeout
`PTFRPA2_Fault=2`. The current native archive confirms that this failure cut the
old waiters. Existing profile, housing and arrival systems then continue their
own work. HS1 acknowledges `PTFRPA2_Finished` only after their required readiness
conditions pass. It does not restart the ending, teleport, alter camera paths,
write native story facts or directly replay purchases/refunds. Other faults and
incomplete arrival states do not qualify.

This package does **not** add the proposed non-pausing loading cover, change
refund cadence or establish a measured deployment speedup. Those remain separate
work, as does the Viktor clinic door investigation.

## First live check

Cold-launch normally and load the retained post-ending AutoSave 8 or 9. Keep the
original fixture and use a new manual slot for testing. In the CET console:

```lua
print(GetMod("PTFR_HistorySnapshotHS1").Status())
```

For a save without previous HS1 evidence, expect `origin=post_ending_fallback`
and `ready/frozen/exported=true/true/true` after capture/export. A JSON file should
appear in the directory above. Check profile restrictions, housing loss/access
and eligible quest restoration. H10 ownership restrictions still apply; owning
the geometry does not grant apartment services.

Save into a new manual slot and reload it. The same baseline must remain, with
no repeated loss, charge, refund, reward or quest restart. A genuine pre-cutoff
save and ending traversal require a separate test of `pre_ending` capture.
AutoSave 6/7 are late 2079 fixtures and cannot prove pre-cleanup history capture.

## Validation and recovery

The final package passed full SCC compilation with 85 sources including
Equipment-EX, compiled predicate/schema/catalogue readback, 21 offline exporter
and source checks, and 14 real-installer fixture actions. Thirteen installed
files match the package: ten replacements and three additions. All 608 protected
files, including all 229 save files, remained unchanged during installation.
No game launch or save-file edits were performed by the assistant.

Backup: `recovery/history_snapshot_hs1_01`. From the workspace, with the game
and launcher closed, run the following with PowerShell 7:

```powershell
& ./prealpha/history_snapshot_hs1/deploy_01.ps1 -Action ValidateRollback
& ./prealpha/history_snapshot_hs1/deploy_01.ps1 -Action Rollback
```

The guards reject later edits to these files. Rollback preserves generated JSON
files and restores only this package. It does not undo changes already saved
through gameplay. Roll back HS1 before older Tower script packages; core,
cosmetic and L1 archive recovery chains remain separate.

Evidence: `prealpha/history_snapshot_hs1/candidate_01/assessment_01.json`, final
`compile_04/result.json`, `tests_02.json`, `readback_01.json`,
`native_check_01.json`, `deployment_tests_01.json`, `install_manifest_01.json`
and the recovery receipt. Final source/proof hashes are pinned; use successors
for subsequent changes. Intermediate `changes_01.json` hashes are not the final
installation manifest. Candidate files and private evidence are Git-ignored.
