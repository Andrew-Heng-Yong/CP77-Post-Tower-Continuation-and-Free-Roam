# QR9 authorized deployment — 31 October 2026

**QR8:02 Core and QR9B04 Diagnostics are installed and verified.** The user approved deployment with “approved for deployment”. The game and RED launcher were closed; neither was launched or controlled. Runtime acceptance remains NOT_TESTED.

The reviewed installer SHA was `CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E`. All 41 sealed preparation artifacts matched before deployment. Real Core and Diagnostics preflights both returned `PREFLIGHT_READY`, installations both returned `INSTALLED_VERIFIED`, subsequent checks both returned `VERIFIED_AFTER`, and both rollback validations returned `ROLLBACK_READY`. No rollback was executed.

Only these game paths changed:

- `archive/pc/mod/zzzz_PTFR_Combined.archive` — replaced PH3 with the sealed QR8 archive.
- `archive/pc/mod/zzzz_PTFR_Combined.archive.xl` — replaced PH3 with the sealed QR8 registration file.
- `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua` — added the separate observer.
- `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json` — added its pinned watch configuration.

The consolidated core retains all 51 stable paths and 1,577 archive payloads. The observer's two files remain outside Core51. No core build, compile, ZIP regeneration, release operation or unrelated-mod edit occurred. The six required core external dependencies, including the Atelier correction and Lizzie's archive, retain their pinned hashes.

[Independent verification](verification.json) checked all 53 installed payload hashes, required dependencies, complete game-file metadata, all 307 save-file names/bytes and metadata, and the 23,828 preparation-protected SHA pins. Only the two authorized archive/XL replacements and two observer additions appeared in the game metadata. No unexpected protected changes occurred. This is a named-file SHA and complete metadata check, not a hash of every unlisted multi-GB game asset.

**ManualSave-23 is untouched and backed up.** Its three original files match the exact recovery copies under `../worker_a/recovery/core_qr8_02_01/master_before/ManualSave-23/`. No writes were made to Saved Games, no save body was parsed, and no facts were changed. A native working save has not been created; that remains the user's next step.

Immutable preflight/install/verify/rollback-readiness reports are in `../worker_a/deployment_01/`. Current recovery journals and old/new payload backups are in `../worker_a/recovery/core_qr8_02_01/` and `diagnostics_qr8_02_01/`. The component manifests retain exact before/after hashes. Replacements are journaled and atomic per file; the pair is not one atomic transaction or a proof of power-loss durability.

The curated current-state pointer and the current-baseline paragraphs of PROJECT/ROADMAP were updated after resource/save verification. Their prior bytes are preserved in `docs_before/`; no historical preparation proof was rewritten. The old `readiness.json` and preparation guides retain their accurate pre-deployment status. The mutable QR9 checkpoint now points to this deployment.

Next: the user follows [NEXT_TEST.md](NEXT_TEST.md) to create a native working save and perform the short S00 smoke. The earlier successful Ana test is not requested again. Fresh CVI02/Saints/Spy cases remain unavailable on the selected completed-history master. The existing 26-case template still has 23 NOT_TESTED and three selected-fixture NOT_TESTABLE rows.

Actual CET API/event delivery, successful private graph/owner activation, native receipts, clocks/queues and save transitions remain unverified. Source signals and plugin attempt bookkeeping are not successful-owner acknowledgements. The five static UNKNOWN contracts, held first Ronald enrollment and other QR8 conditional/opaque limits remain unchanged. This deployment is for controlled human testing, not general release certification.

Do not rerun Install or the before-state Preflight against this installed transaction. Use the reviewed `Verify` interface for the current state. A later authorized rollback removes the observer first and then restores the QR8 core to PH3 using the same journals; the exact commands are in `../USER_PROCEDURE.md`. File rollback does not rewind a working save. Preserve the master backup and recovery evidence.
