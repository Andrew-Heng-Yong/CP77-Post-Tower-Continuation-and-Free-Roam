# QR14 — QR13 deployment preparation complete

**READY for separately authorized deployment; NOT installed.** Real read-only preflight passed. Installed Core remains QR8:02 with unchanged QR10D01/D00E diagnostics. No game, save/fact, diagnostic or staged package was modified. No game launch/CUA, publication or quest replay occurred.

## Concrete deployment

`deploy_core.ps1` / `core_manifest_02.json` validate51 stable Core paths and replace exactly3 existing leaves: combined archive, HistorySnapshotHS1 and SideJobsS23.48 other Core paths stay exact. The installer preserves both diagnostic files, the Atelier correction and unrelated mods; it creates verified old/new backups before any replacement and supports Preflight, Install, Verify, ValidateRollback, Rollback and interrupted-transaction Recover.

Final installer SHA256: `8DE067549901CD3AD6E41AE88F35DBAE4967DC6DEDAADADFF79CF6BB8E2A9A08`.
Manifest02 SHA256: `6963CB2679BF3D0ABD9F34A662C437A185D0FBA10873913B6AEC7EC4F76299C0`.
The unchanged QR13 ZIP SHA256 remains `B2BDC04BE7CF202047C3E7CF85F9BB3BD8F0D77B9D98ACA7C1377F5E5AD52EB8`.

[Exact commands, backup paths and rollback](DEPLOYMENT.md); [current human plan](MANUAL_TEST_PLAN.md); [readiness binding](readiness.json).

## Important compile correction

Independent review found17 runtime-registered Lizzie's Braindances sources omitted by QR13's131-source offline compile. The actual installed runtime log lists148 sources. A fresh workspace integration compile staged all148, overlaid the exact46 candidate managed scripts, passed exit0/Compilation complete with no warning/error lines, and preserved all151 installed source/compiler/cache inputs. Output SHA256: `6185E254BDB1F98A4371A0DEDB76E09D2958EF6006ECA5D5E8C8EABDE83E6F0F`.

The installer now checks complete source inventory across the enclosing r6/scripts and red4ext/plugins trees, refusing added/deleted/renamed sources, linked sources and directory links. Existing non-source framework log links are retained without following them.26 dependencies are exact-pinned, including the17 LBD sources. This is a compile-evidence/guard correction; QR13 runtime source, archive, ZIP and historical reports remain immutable. Knowledge pointers explicitly supersede the earlier complete-input claim.

## Validation

| Gate | Result and limits |
|---|---|
| Final full integration compile |148 sources /151 input pins; candidate46 linkage independently verified. Offline only. |
| Engine02 transaction matrix |52 checks /98 PowerShell actions PASS: normal install, caught/hard install/rollback interruptions and recovery, unknown/corrupt/source/dependency/save refusal, locks/reparse targets and actual Core51 integration. |
| Final engine03 controls |55 independent checks /23 actions PASS, including populated inventories, benign log links, source/link/drift refusal, hard interruption and final actual Core51 install/verify/rollback. |
| Protocol preservation |Independent exact comparison establishes engine02→03 changes only source-inventory link classification. The98-action matrix was not misrepresented as running engine03. Both source revisions/results remain preserved. |
| Real preflight |PREFLIGHT_READY, game/REDlaunchers closed, exact before/package/proof/input hashes, fresh recovery path. Read-only; actual game replacement permission not exercised. |
| Preservation |77 protected installed pins,310 save-file hashes, all game/save metadata, QR13 provider baseline metadata and all QR13 original metadata unchanged. Candidate51 and ZIP unchanged. |

Receipts: [composed fixture coverage](fixture_summary.json), [independent final review](review_01/review.json), [compile](verification/compile_01/result.json), [preflight](preflight_01.json), [preservation](preservation.json).

Initial engines, rejected link classification, failed reviewer fixture-construction/count/message assertions and intermediate receipts are retained. Their coverage is bounded to the source executed; final approval uses the corrected final controls. No unresolved technical deployment blocker remains in this pinned preparation.

## Save qualification

Reused204 QR12 current/backup locations:196 bodies still bind;8 changed bodies remain UNKNOWN. No save was reparsed or loaded. No newly qualified Ronald first-consent fixture was found: QR12 did not capture native known/offer/topic-counter facts; disabled subscription alone cannot establish no previous offer/refusal, exact Inactive contact or support-owning child refresh. Metadata/raw journals/facts do not prove actual saved-owner liveness. Known Brendan ManualSave23/24 fallback history/private Issued/Entered state remains ineligible for the strict earned final-Theo route.

[Fixture evidence and exact missing prerequisites](fixture_assessment.json) / [CSV](fixture_inventory.csv). No immediate special gameplay test is issued. Previously accepted Jinguji/Bullets/Zane/Wilson/Cynthia/D00E/load results and user-completed Skippy are not repeated.

## Remaining boundaries and next action

User approval is still required to install this three-file Core successor; this turn authorized preparation only. No rebuild of unchanged quest resources is needed. After approval, run fresh Preflight, Install, Verify and ValidateRollback with the exact commands in DEPLOYMENT.md. Keep game/launchers closed naturally.

Static/fixture readiness does not prove new Ronald/Brendan gameplay, saved-child graph/prefab refresh, actual executing ownership or opaque native placement. File rollback is not save rollback; newer private state/rewards are not undone or proven old-version-compatible by restoring files. Replacements are individually atomic, not a globally atomic three-file transaction; fixtures cover process interruption, not power loss. Ordinary unmanaged game files are protected through write-set containment/full metadata, not a SHA census of every game asset.
