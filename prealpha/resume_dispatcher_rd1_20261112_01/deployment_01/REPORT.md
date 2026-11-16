# RD1 candidate 04 installed

The user requested “install it pls.” RD1 candidate 04 is installed as **RD1_EARNED_STAGE_RESUME**, replacing HS4_GLOBAL_LATEST_HISTORY. Installation completed at `2026-11-12T22:40:47.4402502Z` UTC. No game was launched and no saves were edited.

[Exact installed manifest](installed_manifest_01.json) SHA-256: `DCC4C8958756DDBA54C1F98404B96F2EBDF16E48F8CE3DEC6BB98A0DA6B30864`.

The five replaced paths are the combined archive, its XL, HistorySnapshotHS1, SideJobsS22 and SideJobsS23. The remaining 46 Core files are unchanged. Global-latest snapshot selection remains installed; the CET loader is unchanged. The archive contains 1,742 payloads.

Validation: the candidate's 148-source compile and 354 bounded offline checks remained applicable; current source, archive-provider inventory and XL inputs matched. The 51-file engineering ZIP was read back. Eighteen fresh deployment/recovery fixture actions passed, including actual-payload rollback, interruption recovery and game-running refusal. The real [preflight](preflight.json), [installation](install.json), [installed verification](verify.json) and [rollback readiness](rollback_readiness.json) passed.

All 51 installed Core paths and 26 required dependency hashes match. All **355 save files** retained their names, sizes and SHA-256 hashes across the transaction. External dependencies were hashed; other unmanaged game files retained names, sizes, modification times and reparse metadata and were outside the write set. This is not an all-external-file content-hash claim.

The checked predecessor and successor payloads are retained in `../recovery/core_resume_rd1_01/`. The receipt is committed and rollback-ready. A future rollback must use this newest layer with the game/launcher closed and exact current hashes; file rollback does not undo saved quest progress. No rollback was performed on the real installation.

Next: load **AutoSave-2 at Viktor**, complete the remaining genuine Tower sequence and credits normally, then check **Machine Gun — Deliver Skippy** and **Moving Heat — first door**. No AutoSave-5 command test or separate snapshot-loader test is requested. Follow the [gameplay card](../TEST_CARD.md) for outcomes and save/reload checks. Native gameplay is still unverified for RD1.
