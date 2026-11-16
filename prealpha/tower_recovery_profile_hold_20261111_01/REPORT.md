# Tower profile setup stall

The user reported a 41% setup stall on 11 November. The CET log for the 23:41 run shows the genuine ending and control handoff, then successful Smart Link and Monowire unequips with item quantities and attached parts preserved. The arm and hand receipt was written at 23:41:57. The Body and other-tree profiles queued at 23:42:01. No refund start was logged before the run closed. The cover stayed at check 5 through 70.8125 seconds. ArchiveXL also logged a successful merge of the private bruise phase. This observation covers the merge alone.

A read-only decode of EndGameSave-68, written at 23:41:23, found two occupied Skeleton slots and no Cellular Adapter. Its SHA256 was `9E4516DF4E5F10048749D3A471779437D7C047745A398A259F9D95BB5B1E5330` before and after the read. The incident log did not identify the exact live effect record.

## Repair

The previous code held Body and Relic admission until the native package list contained none of the IDs associated with retained implants. It made one removal pass per exact item, so a surviving package ID could prevent convergence indefinitely. Package IDs alone cannot distinguish a retained contribution from another source. The repair uses the native instigator-specific removal call for the live package references associated with an exact implant. Refund admission requires the completed per-item treatment, initial unequip receipt, arm appearance readback and stable equipment slots. Residual package IDs are reported separately with the implant identity. Actual disabled effects still require a gameplay check.

The cover now includes the current cyberware or refund wait reason. The existing perk and item safeguards, recovery clock and day-14 appearance phase carry forward. [Script diff](candidate_01/source.patch) · [Scope review](scope_review.json)

## Installed verification

Installed as `QP2_TOWER_RECOVERY_PROFILE_HOLD` over `QP2_TOWER_RECOVERY`. Both changed scripts compiled with all 148 registered sources. Nine transaction fixture actions passed, including interruption between the two replacements, rollback and running-game refusal. All 51 Core files and 26 dependencies verified. The archive and its ArchiveXL registration matched the predecessor, all 337 save files matched their pre-install hashes, and both rollback copies verified. The repaired cover transition awaits a live run. [Installed manifest](deployment_01/installed_manifest_01.json) · [Compile result](compile_01/result.json) · [Transaction fixtures](fixture_results.json) · [Rollback readiness](deployment_01/rollback_readiness.json)
