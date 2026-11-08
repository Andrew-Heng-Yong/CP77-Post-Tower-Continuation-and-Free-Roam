# Authoritative current-state pointers

Core installation updated 31 October 2026; diagnostic-only update installed with explicit user approval on 3 November. Quest-fixture assessment is 2 November; natural diagnostic sampling validation passed on 3 November. The prepared-beta and recorded-publication sections retain their 29 October evidence. Local deployment, the older prepared beta and the recorded published alpha are separate artifacts.

## Local installed successor: QR8:02 with QR10D01 diagnostics

The sealed QR8:02 core is installed. The separately installed two-file observer was updated from QR9B04 to QR10D01 candidate_02 on 3 November through the reviewed QR11 transaction, followed by the D00E config-only layer. Core retains the 51 stable Tower paths and 1,577 archive payloads; the observer is outside Core51. No deployment launched the game. Human El Capitan D00E validation subsequently passed for bounded getter sampling; native callbacks remain unsupported.

| Item | Evidence/value |
| --- | --- |
| Core source/package | `prealpha/quest_restoration_qr8/candidate_01/`; source epoch `source_epoch_02.json`, 1,577 archive payloads |
| Exact component manifests | Core: `prealpha/quest_restoration_qr9/worker_a/core_manifest_02.json`; diagnostic code: `prealpha/quest_restoration_qr11/diagnostics_manifest_01.json`; latest one-file D00E config: `prealpha/quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json` |
| Authorized deployment and installed assessment | [Deployment report](../../prealpha/quest_restoration_qr9/deployment_01/REPORT.md), [independent verification](../../prealpha/quest_restoration_qr9/deployment_01/verification.json) |
| Install/verify/rollback-readiness receipts | `prealpha/quest_restoration_qr9/worker_a/deployment_01/` |
| Current diagnostic deployment | [QR11 installed report](../../prealpha/quest_restoration_qr11/deployment_01/REPORT.md), [preservation verification](../../prealpha/quest_restoration_qr11/deployment_01/verification.json); INSTALLED_VERIFIED / VERIFIED_AFTER / ROLLBACK_READY |
| Current capture profile | [El Capitan D00E config update](../../prealpha/quest_restoration_qr11/d00e_01/REPORT.md), [current manual card](../../prealpha/quest_restoration_qr11/d00e_01/MANUAL_TEST_PLAN.md); only watch.json changed, readback/rollback readiness verified |
| Latest diagnostic observation | [D00E natural sampler PASS](../../prealpha/quest_restoration_qr11/observations/D00E_20261103_01/REPORT.md):3sampled differences0→1→2→0, normal human-confirmed call, clean92second stop, no getter errors; no repeat needed |
| Archive SHA256 | `2AB35CC95931CD3C7BB2FB3A4C8B52746DE7847D42AE1DD3503A90A965FD2039` |
| XL SHA256 | `F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245` |
| Optional observer | `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/{init.lua,watch.json}`; exact hashes in the Diagnostics manifest |
| Core recovery | `prealpha/quest_restoration_qr9/worker_a/recovery/core_qr8_02_01/` |
| Observer recovery | Current D00E→previous D01 config: `prealpha/quest_restoration_qr11/d00e_01/recovery/diagnostics_d00e_01/`; then D01→B04: `prealpha/quest_restoration_qr11/recovery/diagnostics_qr10d01_01/`; older addition recovery remains under QR9 |
| Required external Atelier correction | Unchanged SHA256 `5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8` |

At the 31 October deployment, all 53 installed payload hashes and required dependencies verified; all 307 save files retained their names/bytes and metadata. The three original ManualSave-23 files matched their recovery backup. The 23,828 preparation-protected SHA pins had only the two authorized archive/XL replacements before documentation updates, and complete game metadata showed those two replacements and two observer additions. Later user working saves legitimately advanced; the latest report's verification scope is stated below.

The original components reached `VERIFIED_AFTER` and `ROLLBACK_READY`; the 3November diagnostic successor independently reached those same file gates. No rollback was executed. Current diagnostic rollback must use the QR11 receipt to restore B04 only. Removing that older observer or rolling Core back needs separately reviewed authorization and the appropriate older receipts. File rollback does not reverse saved state.

## QR9 human quest assessment — 2 November 2026

The [QR9 stage report](../../prealpha/quest_restoration_qr9/report.md) is the current runtime-assessment pointer; its [cumulative results and coverage](../../prealpha/quest_restoration_qr9/stage_report_01/coverage.json) preserve exact test boundaries. The observed routes need no repetition. Comprehensive runtime acceptance is incomplete, with no general-release or all-save qualification.

| Observed route | Bounded result |
| --- | --- |
| Startup/load/play and ArchiveXL merges | User play and logged resource merges PASS; exact private-owner activation remains INCONCLUSIVE. |
| Until Death Do Us Part | Continued already-active route completed; user report, broader logs and save metadata corroborate. Fresh admission/all branches unproven. |
| Cynthia and Wilson calls | Delivered on the observed fixture with start/end markers. Other phone variants remain untested. |
| Shoot to Thrill | Winning completion/reward receipt corroborated; eventual shop recovery and completed-state shop/journal reload user-confirmed. Exact reward idempotence/all outcomes unproven. |
| Bullets | Native completion corroborated; Zane shop return, completed-state reload and post-Bullets dialogue user-confirmed. Exact helper termination/lease execution and all branches unproven. |
| Nitro | Saved Issued1, purchase counter1, guarded unlocksfalse, Inactive journal. No clean fresh fixture; existing-owner execution INCONCLUSIVE. No reset/purchase manipulation. |

The user confirmed ManualSave-23's genuine Tower lineage. Original master and offline backup remain exact; all53 installed core/observer payload hashes matched the fresh read-only report-preparation check. Human working saves legitimately advanced. The earlier307-save-file preservation result belongs to deployment, not the entire later play period. Latest full external dependency verification is the recorded post-Bullets Core Verify; it was not rerun just to write the report.

**Diagnostic blocker:** QR9B04 returned listener IDs but missed watched fact transitions seen in the broader CET log. Live fact-callback coverage is unreliable and its root cause remains unconfirmed. Journal/phone getters, human observations and broader fact logs are separate evidence. No speculative diagnostic or gameplay fix was installed. Missing probe events must not be treated as negative gameplay proof.

**Subsequent QR10 offline engineering:** the [QR10 report](../../prealpha/quest_restoration_qr10/REPORT.md) confirms an installed-binary receiver-class mismatch: QuestsSystem requires scripted-class flag4, while CET NativeProxy constructs flags2. This supersedes the root-cause uncertainty above without changing the QR9 observations. Reviewed QR10D01 `candidate_02` removes the unsupported binding and adds bounded, explicitly labelled getter-difference sampling. It is **prepared, not installed**; installed B04 and Core remain unchanged. Native callback delivery remains unsupported, and live sampling is not yet tested. The [QR11 handoff](../../prealpha/quest_restoration_qr10/HANDOFF.md) and [test queue](../../prealpha/quest_restoration_qr10/runtime_queue.json) retain exact prerequisites and no-repeat boundaries.

**QR11 preparation —3November2026:** [deployment readiness](../../prealpha/quest_restoration_qr11/REPORT.md) now includes the guarded two-existing-file installer,48primary fixture checks/86actions,8independent checks/7actions and a successful real read-only preflight. **No real installation occurred; QR8:02 +QR9B04 remain installed.** The self-contained [manual test plan](../../prealpha/quest_restoration_qr11/MANUAL_TEST_PLAN.md) selects verified working slot ManualSave-24(2Nov16:37:02), gives exact conditional installation/CET/collection commands and one Regina D00 sampler test. No Call option means NOT_TESTABLE. Other quest fixtures remain unqualified; prior successes need no repetition. [Continuation handoff](../../prealpha/quest_restoration_qr11/HANDOFF.md).

**Subsequent authorized QR11 deployment — 3November:** QR10D01 is now installed and verified. Exactly two diagnostic paths changed; all310save files remained byte-identical, and Core/dependencies/old evidence were preserved. Follow the [current human D00 steps](../../prealpha/quest_restoration_qr11/deployment_01/NEXT_STEPS.md); no new install command or repeat successful quest test is needed. Native callbacks remain unsupported by this Lua probe; the pending natural test validates sampled observation only. The mutable QR11 checkpoint selects this deployment and the next human action.

**Latest human diagnostic result — 3November:** Regina [D00 remains NOT_TESTABLE](../../prealpha/quest_restoration_qr11/observations/D00_not_testable_01/REPORT.md). El Capitan [D00E passed natural sampler validation](../../prealpha/quest_restoration_qr11/observations/D00E_20261103_01/REPORT.md):3coherent sampled changes, phone-active false→true→false, no recorded getter errors and clean stop after92seconds. The user confirmed normal call behavior and the requested working-slot question with “yes”. Exact native save/owner identity remains unobserved. All60post-run current manifest hashes matched; this is not retrospective executed-byte or native-write proof. No contact restoration, fact reset or runtime repair occurred. No repeat or new gameplay test is requested now.

Further quest tests require genuine supported histories. Fresh CVI is unavailable on the selected completed fixture; Ronald enrollment/history, Skippy, Brendan, pending-owner/reward and exact engine-owner/clock/queue observations remain limited. QR8's five static UNKNOWN contracts and held/conditional/opaque scopes remain. Historical detailed observations, preparation “not installed” statuses and pending results are preserved as dated evidence.

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
