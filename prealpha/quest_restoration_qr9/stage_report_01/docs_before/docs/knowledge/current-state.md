# Authoritative current-state pointers

Local installation updated 31 October 2026 after explicit user approval. The prepared-beta and recorded-publication sections retain their 29 October evidence. Local deployment, the older prepared beta and the recorded published alpha are separate artifacts.

## Local installed successor: QR8:02 with QR9B04 diagnostics

The sealed QR8:02 core is now installed, with the optional two-file QR9B04 read-only CET observer separately installed. The core retains the 51 stable Tower paths; only the archive and XL changed from PH3. The observer is outside Core51. Deployment involved no game launch; the user has since performed the bounded November2 run described below.

| Item | Evidence/value |
| --- | --- |
| Core source/package | `prealpha/quest_restoration_qr8/candidate_01/`; source epoch `source_epoch_02.json`, 1,577 archive payloads |
| Exact component manifests | `prealpha/quest_restoration_qr9/worker_a/core_manifest_02.json` and `diagnostics_manifest_01.json` |
| Authorized deployment and installed assessment | [Deployment report](../../prealpha/quest_restoration_qr9/deployment_01/REPORT.md), [independent verification](../../prealpha/quest_restoration_qr9/deployment_01/verification.json) |
| Install/verify/rollback-readiness receipts | `prealpha/quest_restoration_qr9/worker_a/deployment_01/` |
| Archive SHA256 | `2AB35CC95931CD3C7BB2FB3A4C8B52746DE7847D42AE1DD3503A90A965FD2039` |
| XL SHA256 | `F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245` |
| Optional observer | `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/{init.lua,watch.json}`; exact hashes in the Diagnostics manifest |
| Core recovery | `prealpha/quest_restoration_qr9/worker_a/recovery/core_qr8_02_01/` |
| Observer recovery | `prealpha/quest_restoration_qr9/worker_a/recovery/diagnostics_qr8_02_01/` |
| Required external Atelier correction | Unchanged SHA256 `5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8` |

All 53 installed payload hashes and required dependencies verify. All 307 save files retain their names/bytes and metadata. The three original ManualSave-23 files match their verified recovery backup. The 23,828 preparation-protected SHA pins have only the two authorized archive/XL replacements; no unexpected protected changes were found before the three documentation pointers were updated. Complete game metadata shows exactly those two replacements and two observer additions.

Both components are `VERIFIED_AFTER` and `ROLLBACK_READY`; no rollback was executed. If later authorized, remove the QR9 observer first, then roll the QR8 core back to PH3 using these exact receipts. Only then can historical PH3 predecessor rollback be reviewed. File rollback does not reverse saved state.

**November2 human observation:** the user reports loading, completing a gig without problems and exiting. [The bounded assessment](../../prealpha/quest_restoration_qr9/observations/S00_20261102_01/REPORT.md) records a load/play PASS and logged resource-merge PASS, with actual private-owner activation INCONCLUSIVE. The user subsequently [confirmed Until Death Do Us Part](../../prealpha/quest_restoration_qr9/observations/S00_20261102_01/confirmation_01/user_confirmation.json), matching the CET transitions and save metadata; the loaded slot remains unconfirmed. The probe attached and auto-stopped cleanly after300 seconds, before the later gig-completion events. The broader CET log and metadata corroborate one already-active route's completion; fresh admission, exact rewards, all call variants and post-completion reload are not proven. No replay is requested.

Both installed components still verify after that run; ManualSave-23 and its verified backup remain unchanged. ManualSave-24 exists as a user-created working candidate, but metadata does not prove it was the loaded slot. Actual graph activation, native owner/receipt/clock/queue/save-ID observations remain unsupported. The earlier Ana/phone success remains bounded to its PH3 fixture. QR8's held routes, five UNKNOWN contracts and conditional/opaque limits remain in force; use [QR8's report](../../prealpha/quest_restoration_qr8/REPORT.md), the new assessment and the mutable QR9 checkpoint for the next task. The sealed [installed handoff](../../prealpha/quest_restoration_qr9/deployment_01/HANDOFF.md) retains its historical pre-test state.

**Later November2 S03/call observation:** [the assessment](../../prealpha/quest_restoration_qr9/observations/S03_20261102_01/REPORT.md) records user-observed Cynthia and Wilson delivery with matching native start/end counters; Wilson also set `mq011_active`1. Contest progression/rewards are not yet tested. Nitro's observed saved Issued1, purchase counter1, four guarded unlocksfalse and Inactive journal make this an existing-state fixture; fresh positive/negative admission is NOT_TESTABLE there and exact saved-owner progress remains INCONCLUSIVE. No reset or purchase manipulation is requested. Installed components, original master and backup still verify. The next human route is [Shoot to Thrill progression](../../prealpha/quest_restoration_qr9/observations/NEXT_WILSON.md), using normal gameplay and working saves; no additional S03 command is needed.

**Subsequent Wilson completion observation:** [the successor assessment](../../prealpha/quest_restoration_qr9/observations/WILSON_20261102_01/REPORT.md) corroborates the user's completed final winning route, reward receipt and `mq011_done` with logs/finished metadata. The user could not shop immediately. The default shop-enable flag returned157 wall-seconds after the reward callback, but actual trade UI recovery remains INCONCLUSIVE. Pinned native evidence includes Wilson-door/scene exit, a distance100 fallback and later distance99 actor-retirement wait; the private vendor lease releases only after native termination. These do not prove which route executed or establish perfect visible timing parity. No source-confirmed defect or repair was inferred. The next observation is [shop recovery after ordinary leaving/returning](../../prealpha/quest_restoration_qr9/observations/NEXT_WILSON_SHOP.md), only if it has not already recovered; no contest replay. Both components and the original master/backup still verify. Prior handoffs/assessments retain their dated pre-completion statuses.

**Wilson follow-up confirmed:** the user subsequently answered “Available after leaving/returning or waiting.” [The confirmation](../../prealpha/quest_restoration_qr9/observations/WILSON_20261102_01/confirmation_01/completion.json) closes the eventual shop-recovery observation as a bounded PASS. The combined answer does not distinguish the exact action or latency; exact owner execution and universal timing/save parity remain unproven. The immediate symptom and earlier INCONCLUSIVE assessment remain preserved as historical evidence. No repair or replay is needed for this successful fixture.

**Completed Wilson reload confirmed:** the user then reported “yes it persists and shop opens after reload.” [This additional observation](../../prealpha/quest_restoration_qr9/observations/WILSON_RELOAD_20261102_01/observation.json) passes the completed-quest/shop persistence check for that route. No new logs or file verification were collected for this reply; exact loaded slot and reward/invitation repetition were not explicitly reported. This is not every S08 alternative, exact reward-idempotence proof or future-version save certification. No repeat of the completed Wilson test is needed.

**Jinguji first-visit observation:** [S05's assessment](../../prealpha/quest_restoration_qr9/observations/S05_20261102_01/REPORT.md) records no quest start while Zane's ordinary dialogue was available. Broader CET logs show `mq030_zane_met`0→1→2→3. The pinned native route next waits for the player outside `#mq030_tr_jinguji_away`; [ordinary leaving/returning](../../prealpha/quest_restoration_qr9/observations/NEXT_JINGUJI_RETURN.md) remains the next observation, not a forced quest-start option or purchase. Actual post-leave progression is pending. Separately, S05 produced no fact-delivery rows despite three watched transitions in the broader log during capture. **Probe callback coverage is unreliable; root cause remains unconfirmed.** Returned listener IDs/offline tests do not close it, and absent probe events must not be used as negative gameplay proof. No speculative diagnostic or gameplay change was installed.

**Subsequent Bullets completion:** the user reported activation and finishing the recording. [The new assessment](../../prealpha/quest_restoration_qr9/observations/S05_20261102_02/REPORT.md) independently confirms completion through journal Inactive→Active→Succeeded, native MaxTac/gratitude/done1/active0 callbacks in the broader log, and finished `mq030` metadata in ManualSave-24 at16:37:02 EST. This is a bounded reached-route completion PASS; Zane's vendor/helper return and completed-state reload remain pending. The [next short check](../../prealpha/quest_restoration_qr9/observations/NEXT_ZANE_COMPLETED.md) observes ordinary trade after leaving/returning and reload, without replay. The probe callback gap persists while its journal getters work; those sources remain distinct. Core/observer hashes, required dependencies and original master/backup verify. No gameplay or diagnostic repair was installed.

**Zane shop return confirmed:** the user then replied “return works” to the shop-return check. [This confirmation](../../prealpha/quest_restoration_qr9/observations/S05_20261102_02/shop_return_confirmation_01/observation.json) records functional trading after return as a bounded user-reported PASS. Completed-save reload remains pending; exact helper retirement/lease execution is still not directly observed. No shop-return repetition or repair is requested.

## Historical installed predecessor: PH3

Selected baseline: `prealpha/phone_studios_ph3/candidate_01/`.

| Item | Evidence/value |
| --- | --- |
| Installation receipt and file hashes | `install_manifest_01.json`, its `.sha256`, and `recovery/phone_studios_ph3_01/receipt.json` |
| Deployment assessment | `installed_assessment_01.json`, `preservation_after_01.json` |
| Consolidated source and package | `archive_source/` and `package/` inside this candidate |
| Tower install layout | 51 stable paths; combined archive/XL plus consolidated scripts and CET helpers listed in manifest |
| Archive members | 1,574; PH3 adds one owner, preserving all 1,573 PH2 payloads |
| Archive SHA256 | `18B855B55A62771F146B9BA518F8DB782832606AA7666755303EEBA91D9F66C7` |
| XL SHA256 | `C55FB23E72710FD0FC8D348C62E2118C2E3FAD04DE3FCE2E6B459E6AB2A1F720` |
| Local full 51-path ZIP | `PTFR_phone_studios_ph3_full_51.zip`; SHA256 `FA9B92347A33336F623849337230E012E580CCCD0531A89A7489C30A42FC68EC` |
| Required external Atelier correction | `r6/scripts/virtual-atelier-full/SetupNewTab.reds`, corrected SHA256 `5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8` |

**Recorded PH3 human observation:** the user reported “the fix worked” after PH3, before the instruction-maintenance task. Treat that as a pass for the reported Ana/phone fixture. Preserve the original installed assessment's historical LIVE_PENDING value; it predates the report. This observation does not certify all contacts, 174 studio variants, reloads or future save upgrades.

[PH3 report](../phone_studios_ph3_20261029.md), [PH2 report](../phone_merge_ph2_20261029.md) and [PH1 report](../phone_support_ph1_20261029.md) explain the controller, generated-ID and shared-prefab layers. PH1 missed shared root prefabs; PH2 corrected a Mark injection ID collision; PH3 owns the exact two native studios. Do not revert those dependencies independently without reviewing the chain.

Rollback order for the newest layers is **PH3 → PH2 → PH1 → LR2 → LR1**, then the documented predecessors (VD1, LC4, WA3/CO1, WA2, BA1, CC1, SC3, CR1 as applicable). Each receipt and actual installed hashes must still agree before a step. This is not authority to execute a rollback now, nor proof that a long chain remains feasible after new gameplay.

## Prepared beta: a separate VD1 snapshot

`release/package-v0.2.0-beta.json` records the final four-folder package, built from `prealpha/viktor_door_vd1/candidate_02`, not PH3. Its 51 core files plus four readme references make 55 ZIP entries:

`archive/`, `bin/`, `r6/`, `readme/` containing only `AI_CLEANUP_INSTRUCTIONS.md`, `MANUAL_CLEANUP_INSTRUCTIONS.md`, `FILES.json`, `OBSOLETE_FILES.json`.

ZIP: `dist/v0.2.0-beta/Post-Tower-Continuation-and-Free-Roam-v0.2.0-beta.zip`, 10,127,545 bytes, SHA256 `F3FFEEED127532FF9F3DB5B4BCBB364FA673A9A50F519AF106D9E6D87030D7AE`. Required Atelier correction is documented manually; no scripts, old ZIP, backups, release notes or persistence contract are bundled. The known obsolete manifest covers 124 paths with accepted hashes and no current-core overlap.

This beta has not been updated with LR1/LR2/PH1/PH2/PH3 by this maintenance task. `published:false` is the recorded local beta state. README's alpha link is the last recorded public release (`v0.1.1-alpha.20261024`); publication was not checked online in this task. Do not describe a local candidate as a public download or latest remote release without verification.

## Script/toolchain evidence

QR9 deployment changed no core REDscript inputs and added only the separately tested Lua observer. It reused the sealed QR8 package and compile evidence linked by the [QR8 handoff](../../prealpha/quest_restoration_qr8/HANDOFF.md); no compilation or core rebuild was performed for this deployment.

Historical PH3-era pointer: `prealpha/world_support_wa3/candidate_02/compile_01/result.json`, recorded PASS with 112 staged REDS inputs, including CO1. `compile_inputs_01.json` pins that inventory. This historical count is not today's dependency census. Fresh input equivalence is required before reusing a compile result.

The historical installed framework evolution includes PR builds followed by public Codeware evidence. Read manifests/logs for actual current binaries; do not install framework versions from older PROJECT/ROADMAP prose. WolvenKit 9.1 and the Python path are documented in the workflow pages. There is no freshly certified one-command rebuild for the whole PH3 lineage.

## Known limits to carry forward

- Entry coverage historically reached 80 gigs/81 side jobs (S30), distinct from 158 selected entries in older R6/S29 reports. This is bounded entry implementation, not full lifecycle parity.
- Skippy's progressed Machine Gun resume adapter has exact captured-state limitations; [Skippy audit](../skippy_vanilla_wiki_review_20261028.md).
- MQ018/MQ028 partial-state cases remain source-only suspects, without stranded-owner proof; do not reset/admit them.
- WA3 progress-gated exclusions, group1013 decoding and unsafe fight controllers remain explicitly bounded; [WA3 report](../world_support_wa3_20261028.md).
- The studio sectors have a WolvenKit DynamicBaseClass decoding limitation. PH3 references exact native prefabs; it does not claim a complete decoded placement audit.
- [Conflicts](conflicts.md) records policy/pipeline questions. No comprehensive quest-parity auditor has been built or run by this instruction-maintenance task.

Preservation verification and original/new instruction sizes: [maintenance report](../maintenance/instruction-system-20261029/REPORT.md). Those checks are read-only state verification, not a runtime or quest audit.
