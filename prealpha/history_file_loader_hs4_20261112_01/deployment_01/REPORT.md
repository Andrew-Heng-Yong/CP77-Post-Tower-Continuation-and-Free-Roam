# HS4 installed — 12 November 2026

Installed `HS4_GLOBAL_LATEST_HISTORY`, candidate 02, as the requested global-latest follow-up to the ongoing mod installation/test. The immediate predecessor is `HS3_NATIVE_HISTORY_CAPTURE`. [Exact installed manifest](installed_manifest_01.json) · [Transaction allowlist](../core_manifest_01.json) · [Implementation and test limits](../REPORT.md).

Exactly two existing files changed:

- `r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds`
- `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua`

The game and launcher were closed. Read-only preflight, installation, installed-file verification and rollback readiness all passed. All 51 Core paths and 26 dependencies match their expected hashes. All 349 save files retained exact names, sizes and hashes. Other unmanaged game paths retained their recorded names, sizes, timestamps and reparse metadata; this is not a claim of hashing every unrelated game asset. The archive, ArchiveXL configuration, diagnostic observer and required Atelier correction are unchanged. Existing snapshot files were preserved.

Recovery copies for these two files are retained under `../recovery/core_global_latest_hs4_01/`, with a committed transaction journal. Rollback restores the immediate HS3 file baseline and requires its own authorization and current-state checks; it does not undo saved progress. No game launch, save edit, external-mod edit, publication or push occurred.

On the next normal load, the mod automatically selects the global newest valid pre-ending capture. No filename change, per-save match or CET command is needed. Successful loading writes `[PTFR] Global latest snapshot loaded:` followed by both selected filenames to the CET log. The currently tested capture is schema-3 revision 1 from 19:39:31 UTC on 12 November, with schema-1 revision 151. A later valid capture will take priority automatically on load.

The in-game import remains unobserved. No repeat of the previously successful snapshot-creation test is required for this change; the installed-file and fixture results are distinct from gameplay verification.
