# Manual Save 26 snapshot capture at Reed pickup

**Pass for capture and export** on 11 November 2026 at 5:46:22 p.m. Toronto time. The latest session compiled the installed scripts at 5:39:35 p.m. and reached the rooftop commitment. The exporter logged `pre_ending snapshot verified` at the cutoff, after the file readback and `AckFile` succeeded. [Installed build](../../deployment_01/installed_manifest_01.json)

## Export verification

- File `snapshot_hs1_20261111T224622Z_159_1.json` under the installed CET mod `PTFR_HistorySnapshotHS1`. SHA-256 `F1CBD023E336F7A4173BF3700E5FCB0B9667CE5924FBE00C35D81A253E82B0B0`.
- Schema 1, revision 159, origin `pre_ending`. All 158 rows are unique and stable, with their definition and ordering matching the installed catalogue. Each row has matching definition and value counts for its journal and fact fields. The snapshot contains 3,178 journal state fields and 4,715 fact fields, including repeated references across rows.
- All ten references to `q307_point_of_no_return` retain `0`. The same-second CET events show the native cutoff advancing to `1` and the verified export. [Earlier source trace of the native cutoff and journal updates](../../../history_snapshot_cutoff/REPORT.md)

## Comparison with the pre-ending save

Manual Save 26 still matches its extracted body SHA-256 `6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4`. The export agrees with all 42 sampled journal states backed by matching saved records for the three quests below. The hospital column uses the earlier run’s independently extracted AutoSave-10. [Source save records](../../../history_snapshot_cutoff/evidence_01/journal_comparison.json)

| Quest | Manual Save 26 | New snapshot | Earlier hospital save | Sampled journal states matched |
| --- | --- | --- | --- | --- |
| Moving Heat | Active | Active | Failed | 30/30 |
| Beat on the Brat | Active | Active | Failed | 11/11 |
| Small Man, Big Mouth | Active | Active | Failed | 1/1 |

## Observation limit

The session was observed through the rooftop call. Snapshot persistence through hospital and save/reload and resumption of the three quests await a later save from this run.
