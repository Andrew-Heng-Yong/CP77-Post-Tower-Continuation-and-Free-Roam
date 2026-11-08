# Authoritative current-state pointers

As of 29 October 2026. Three distinct artifacts must not be conflated: the current local installation, the older prepared beta, and the last recorded published alpha.

## Local installed successor: PH3

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

**Latest human observation:** the user reported “the fix worked” after PH3, before this instruction-maintenance task. Treat that as a pass for the reported Ana/phone fixture. Preserve the original installed assessment's historical LIVE_PENDING value; it predates the report. This observation does not certify all contacts, 174 studio variants, reloads or future save upgrades.

[PH3 report](../phone_studios_ph3_20261029.md), [PH2 report](../phone_merge_ph2_20261029.md) and [PH1 report](../phone_support_ph1_20261029.md) explain the controller, generated-ID and shared-prefab layers. PH1 missed shared root prefabs; PH2 corrected a Mark injection ID collision; PH3 owns the exact two native studios. Do not revert those dependencies independently without reviewing the chain.

Rollback order for the newest layers is **PH3 → PH2 → PH1 → LR2 → LR1**, then the documented predecessors (VD1, LC4, WA3/CO1, WA2, BA1, CC1, SC3, CR1 as applicable). Each receipt and actual installed hashes must still agree before a step. This is not authority to execute a rollback now, nor proof that a long chain remains feasible after new gameplay.

## Prepared beta: a separate VD1 snapshot

`release/package-v0.2.0-beta.json` records the final four-folder package, built from `prealpha/viktor_door_vd1/candidate_02`, not PH3. Its 51 core files plus four readme references make 55 ZIP entries:

`archive/`, `bin/`, `r6/`, `readme/` containing only `AI_CLEANUP_INSTRUCTIONS.md`, `MANUAL_CLEANUP_INSTRUCTIONS.md`, `FILES.json`, `OBSOLETE_FILES.json`.

ZIP: `dist/v0.2.0-beta/Post-Tower-Continuation-and-Free-Roam-v0.2.0-beta.zip`, 10,127,545 bytes, SHA256 `F3FFEEED127532FF9F3DB5B4BCBB364FA673A9A50F519AF106D9E6D87030D7AE`. Required Atelier correction is documented manually; no scripts, old ZIP, backups, release notes or persistence contract are bundled. The known obsolete manifest covers 124 paths with accepted hashes and no current-core overlap.

This beta has not been updated with LR1/LR2/PH1/PH2/PH3 by this maintenance task. `published:false` is the recorded local beta state. README's alpha link is the last recorded public release (`v0.1.1-alpha.20261024`); publication was not checked online in this task. Do not describe a local candidate as a public download or latest remote release without verification.

## Script/toolchain evidence

Last complete-input offline compilation: `prealpha/world_support_wa3/candidate_02/compile_01/result.json`, recorded PASS with 112 staged REDS inputs, including CO1. `compile_inputs_01.json` pins the exact source inventory. Later archive-only successors claim no new compilation. Fresh input equivalence must be checked before reusing that result; an old count is not a current dependency census.

The historical installed framework evolution includes PR builds followed by public Codeware evidence. Read manifests/logs for actual current binaries; do not install framework versions from older PROJECT/ROADMAP prose. WolvenKit 9.1 and the Python path are documented in the workflow pages. There is no freshly certified one-command rebuild for the whole PH3 lineage.

## Known limits to carry forward

- Entry coverage historically reached 80 gigs/81 side jobs (S30), distinct from 158 selected entries in older R6/S29 reports. This is bounded entry implementation, not full lifecycle parity.
- Skippy's progressed Machine Gun resume adapter has exact captured-state limitations; [Skippy audit](../skippy_vanilla_wiki_review_20261028.md).
- MQ018/MQ028 partial-state cases remain source-only suspects, without stranded-owner proof; do not reset/admit them.
- WA3 progress-gated exclusions, group1013 decoding and unsafe fight controllers remain explicitly bounded; [WA3 report](../world_support_wa3_20261028.md).
- The studio sectors have a WolvenKit DynamicBaseClass decoding limitation. PH3 references exact native prefabs; it does not claim a complete decoded placement audit.
- [Conflicts](conflicts.md) records policy/pipeline questions. No comprehensive quest-parity auditor has been built or run by this instruction-maintenance task.

Preservation verification and original/new instruction sizes: [maintenance report](../maintenance/instruction-system-20261029/REPORT.md). Those checks are read-only state verification, not a runtime or quest audit.
