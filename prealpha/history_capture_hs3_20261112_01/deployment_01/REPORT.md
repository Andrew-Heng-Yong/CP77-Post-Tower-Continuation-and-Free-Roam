# HS3 installed for the Manual Save 26 test

**Installed and file-verified on 12 November 2026, America/Toronto**, following the user's instruction, “install and i will test.” The selected build is `HS3_NATIVE_HISTORY_CAPTURE`, candidate 04. Gameplay remains pending the user's test. The game was not launched.

Exactly three existing files changed: the combined archive, `PTFR_HistorySnapshotHS1.reds`, and that snapshot system's CET `init.lua`. All 51 Core paths and 26 required dependencies match their selected hashes. The archive contains 1,740 members, preserving all 1,738 predecessor payloads and adding the two reviewed native capture gates. There are no new ArchiveXL registrations.

The fresh pre-installation scan checked 137 archives, the exact two native source providers and all 75 unchanged ArchiveXL files. Full 51-member ZIP readback and 18 transaction fixture actions passed, including actual-payload clean rollback, interrupted writes/staging/receipt recovery and the running-game refusal. Preflight checked the closed game/launcher, exact compiler input inventory, candidate/proof hashes and Manual Save 26's three original files.

The actual transaction verified all 349 saved files byte-for-byte before and after installation. Required dependency bytes and other unmanaged game file names/sizes/timestamps are unchanged. No save writes, quest commands, game launches or unrelated mod edits occurred. File rollback readiness is verified; it is not a save rollback or a guarantee that an older build can load future saves.

## Test

1. Launch the game and load **Manual Save 26**. Keep that original slot unchanged.
2. Follow the normal Reed/Tower route. Capture runs automatically before native cleanup; no revision-159 override or console command is needed. A brief capture wait may occur before progression continues.
3. Continue through the hospital and ending. Use a separate save slot for the post-ending save/reload check.

First confirm the new capture and exports at the hospital; then compare the new saved records after genuine Tower completion and reload. This installation tests history preservation. Later plan steps still supply missing stage/owner resumption support; an active journal or successful capture alone does not certify a working resumed quest.

## Evidence

- [Installed manifest](installed_manifest_01.json): authoritative installation, exact candidate and archive source.
- [Preflight](preflight.json), [installation](install.json), [post-install verification](verify.json), [rollback readiness](rollback_readiness.json).
- [Transaction manifest](../core_manifest_01.json), [deployment fixtures](../fixture_results.json), [current provider scan](../deployment_sources_01.json).
- [Build report](../REPORT.md), [save-fixture report](../verification_saves_01/REPORT.md), [full qualification card](../TEST_CARD.md).

Recovery is pinned under `../recovery/core_history_capture_hs3_01/`. Preserve it and use the current transaction's guarded recovery actions only when separately requested. The earlier staged checkpoint remains immutable build-time evidence; this installed manifest supersedes its installation status. A metadata-recording attempt encountered missing Python timezone data after installation; the recorder now uses Windows' timezone database. The installation and its verification were already successful and were not repeated.
