# HS4 global latest snapshot loading

HS4 candidate 02 is installed. The user explicitly selected **global latest**, superseding the earlier same-ending-run preference. Each load validates the newest complete pre-ending capture in the existing snapshot folder and imports its historical baseline automatically. There is no character, playthrough or ending-run filter and no fixed revision override. See the [installation record](deployment_01/REPORT.md) and [exact installed manifest](deployment_01/installed_manifest_01.json).

The schema-3 file supplies extended history; its schema-1 companion must agree on comparable stable values. Invalid or incomplete candidates are skipped in favor of the next valid complete capture. Existing valid files take priority over old cached save data. If no schema-3 file exists, intact saved history can regenerate its export. If files exist but none form a valid complete pair, new admissions wait. Both files from a fresh native capture must finish exporting before the global loader can replace its cache.

The implementation uses queued primitive packets with lease/epoch checks and complete staged publication. It preserves all previously shipped saved field identities and adds two persistent Boolean bookkeeping fields. Import changes mod history caches, not native quest facts, current quest progress, rewards or controllers. The native pre-cleanup gates and combined archive remain byte-identical to HS3. This change does not supply missing mid-progress quest stages or owners.

| Validation | Evidence and boundary |
| --- | --- |
| Compilation | [148 registered sources passed](compile_02/result.json), including the actual installed source closure and candidate overlay. |
| Loader fixtures | [20 passed](verification_02/latest_fixtures.json), executing the candidate Lua with full real exports, an in-memory filesystem and a queued engine double. Includes malformed/newest fallback, global selection, incompatible companions, changing files, save switches, queue stalls, absent-file regeneration and dual export acknowledgement. |
| Source/package checks | [20 passed](verification_03/verification.json): complete 51-file package, exactly two changes, stable saved identities/catalogues, unchanged archive/XL, staged publication and native-capture safeguards. |
| Deployment/recovery fixtures | [18 actions passed](fixture_results.json): actual-payload rollback, interruption recovery and refusal while the game is running. |
| Installed state | All 51 Core paths and 26 dependencies verified; 349 save files retained exact names/bytes/hashes. File rollback to HS3 is ready. |

The full-value fixture uses `snapshot_hs3_20261112T193931Z_1_3.json` and `snapshot_hs1_20261112T193921Z_151_2.json`. Machine Gun retains the captured Active Deliver Skippy state and counter 97. Stable values and unknown/unstable markers are transferred unchanged. These offline checks and installed-file verification do not establish native engine scheduling, save serialization or quest resumption in gameplay. No game launch or new ending run was performed.

`checkpoint.json` remains immutable preparation evidence, pinned by the transaction. `installation_checkpoint_01.json` selects the installed state. Candidate 01 and its earlier checks remain preserved and unselected. [Implementation design](DESIGN.md) records the selected behavior; [build source](build.py), [Lua source](latest.lua) and [deployment preparer](deploy.py) are the corresponding implementation tools.
