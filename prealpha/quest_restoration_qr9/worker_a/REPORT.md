# QR9 deployment preparation

Prepared a guarded Core installer and separate optional Diagnostics component. **No installer action, including Preflight, was run against the real game. No selected save was copied or edited. No game was launched.** Root's independent read-only baseline checker is separate evidence.

Final user entry point: `deploy_qr9_guarded.ps1`, SHA `CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E`. It is byte-identical to the tested `deploy_qr9_guarded_final.ps1`. Promotion occurred only after all historical-source readers finished; `canonical_promotion_01.json` records the verified workspace copy. `deploy_qr9.ps1` and `evidence/deploy_guarded_C8EE.ps1` are historical fixture inputs.

The Core manifest pins 51 files and replaces only `zzzz_PTFR_Combined.archive` and its `.archive.xl`, from installed PH3 to QR8:02. Diagnostics pins two absent-before addon files and existing CET only; it does not change Core51 or certify the installed Core version. Diagnostics rollback preserves logs, unknown files and directories.

Validation is attributed to exact source versions:

| Evidence | Result | Source |
| --- | --- | --- |
| `fixture_result_02.json` | 29/29 workspace scenarios | 3D3504… original guarded transaction body |
| `final_fixture_result_01.json` | 7/7 affected-path/lock scenarios | C8EE59… lock successor |
| `exact_payload_result_01.json` | Actual Core51 and addon2 workspace lifecycle transactions pass | C8EE59… |
| `receipt_guards_result_01.json` | 4/4 committed-recovery/receipt/same-process disposal scenarios | CE0201… final source |
| `evidence/source_applicability.json` | Exact, bounded source delta proof | All three sources |
| `reviews/diagnostics_01/result.json` | 16 independent source/Lua-double checks | Frozen addon QR9B04 |

These are separate scenarios, not a gameplay-coverage percentage. Worker C independently approved the final CE020 source at `worker_c/reviews/installer_final_01/review.json` (32 final checks), using its separate four-scenario/84-check C8EE run and explicitly attributed final source/test applicability. This is offline preparation approval. Source applicability proves that the prior path/reparse, source-package, hash, process, save/external preservation, backup, replacement and rollback controls remain unchanged. Added guards serialize mutating actions across recovery directories/components; refresh state after acquiring the lock; validate journal enums; refuse Recover on committed receipts; and dispose the lock explicitly on normal/error exit. Hard process termination releases the Windows handle.

Preserved failure evidence includes suite01's PowerShell `$null`/empty backup-path API failure, which stopped and restored fixture state. The corrected call uses `[NullString]::Value`. The intermediate committed-Recover admission gap is closed in CE020. Tests require actual injected exit72, sentinel changes or intended exception text, so an earlier parameter-binding failure cannot satisfy a fault test.

Future `Install -BackupMaster` explicitly copies only the three pinned ManualSave-23 files into recovery and verifies the offline copy. Preflight only checks that plan. It never writes Saved Games. The human must create a working branch using native Load23 → Save Game → New Slot. Each write transaction snapshots then-current saves; later legitimate working-slot progress remains intact. Verification stops if the original master changes and preserves its backup instead of restoring it automatically.

`DEPLOYMENT.md` contains prerequisites, exact future commands, expected states and recovery limitations. Core receipts use `PREFLIGHT_READY`, `INSTALLED_VERIFIED`, `VERIFIED_AFTER`, `ROLLBACK_READY`, `ROLLED_BACK_VERIFIED` and `VERIFIED_BEFORE`. Interrupted actions require explicit Recover; unknown files, damaged backups/journals, links and dependency drift stop the operation.

Real write permissions, CET API/event delivery, early startup, native graph/owner/ArchiveXL receipts, timers/queues and gameplay outcomes remain unverified. Replacements are atomic per file and journaled, not a single two-file Windows transaction or a proof of power-loss durability. File rollback is not save rollback. Deployment and game launch remain pending explicit user authorization.
