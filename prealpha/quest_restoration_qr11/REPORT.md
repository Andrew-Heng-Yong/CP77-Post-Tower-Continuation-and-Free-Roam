# QR11 — diagnostic deployment readiness and manual plan

**READY_NOT_INSTALLED. Real read-only preflight: PREFLIGHT_READY,3November2026.** Core QR8:02 and QR9B04 remain installed. No real Install, Rollback, Recover, game launch, CUA or fact/save write was performed.

The primary deliverable is [MANUAL_TEST_PLAN.md](MANUAL_TEST_PLAN.md): exact working save and controls, conditional deployment commands, one D00 start/stop pair, gameplay windows, expected logging/classification, automatic collection and a blocked-test priority list. It is self-contained; the user need not reconstruct it from technical reports.

## Exact engineering result

`deploy_diagnostics.ps1` is a separate, reviewed successor of the pinned QR9 transaction. It permits only replacement of the two existing diagnostic leaves, verifies recoverable before/after payloads, refuses drift/unknown states, journals individual atomic replacements and supports Preflight/Install/Verify/ValidateRollback/Rollback/Recover. No Core selector, save restore or new gameplay code exists. [Frozen manifest](diagnostics_manifest_01.json), [readiness](readiness.json), [recovery procedure](DEPLOYMENT_AND_ROLLBACK.md).

The payload remains QR10D01 candidate_02, unchanged: Lua SHA1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90; configA1AAB30B9F896CD24687D82CC2160D773C04B7193BDDCA71CC933A4C93997AAA. Installed B04 bytes are still exact. QR10's44Lua/6mutant/15independent controls were reused rather than rerun. No Core recompilation, unchanged archive reproduction or whitelist audit occurred.

| Gate | Measured result |
| --- | --- |
| Main transaction fixtures |[48checks/86PowerShell actions PASS](run_02_results.json): normal install/rollback, early/backup/staging/mixed-pair/receipt crashes, caught failures, interrupted rollback, active-game guards, unknown target/dependency/save changes, corrupt evidence, device/path/reparse and stable-lock controls. Actual diagnostic payload bytes, synthetic other game/save contents. |
| Independent review |[8assertions/7actions PASS](review/adversarial_results_02.json), including working24 overwritten by later play and preserved during verification/rollback, proof drift and broken report link. [Review](review/REVIEW.md); no blocking source findings. |
| Collector |[13offline parser controls PASS](collector_controls_02.json). Main live collection is prospective until a human D00 capture exists. Automatic current-byte checks, fresh copy/hash, bounded log tails and metadata; no manual fact transcription. |
| Real read-only preflight |[PREFLIGHT_READY](preflight_real_01.json): two B04 files, exact D01 source/manifest/readiness/proofs,58required game files (Core51+6dependencies+EXE), master3, working24 and current save/unmanaged protection snapshot. Recovery target remains absent. |
| Preservation |[Final verification](preservation_final_01.json):84protected hashes,310save file bytes/names, complete game/QR9/QR10 metadata and frozen candidate. Only new QR11 work and a backed-up current-state documentation pointer are intended edits. |

The initial generator stopped on a duplicate text-transform assertion before creating an installer; its pinned baseline/manifest were retained and explicitly reused with `prepare.py --resume`. Initial run_01 fixtures and the independent discovery run are nonqualifying: primary run was interrupted to replace slow PowerShell ancestor lookups with equivalent fail-closed .NET attribute checks; the review detected the source change and refused to qualify that mixed run. Original draft and partial fixtures remain preserved. Only unchanged final source run_02/review_02 bind readiness.

## Human fixture and observation limits

Filesystem slot **ManualSave-24**, metadata **16:37:02,2.11.2026**, level51, mq030complete, same playthrough ID as the already user-confirmed Tower master23. Original master23 and its recovery copy remain exact. This reuses confirmed lineage; metadata alone is not an independent genuine-ending certificate. Selecting the matching UI row remains a human action; no Continue/ending/master slot substitute is requested.

Current configured CET key decodes to VK0xDC/backslash; Windows read-only character mapping agrees. UserSettings maps openPhone toIK_T. [Controls evidence](controls_evidence.json) pins the read configuration and official decoder excerpt. No keyboard input or CUA was issued. The plan explicitly stops if the UI save cannot be identified or Regina's real Call option is unavailable.

D00 observes **two-second sampled differences**, not native callbacks or write ordering. Native callback delivery remains unsupported by QR10D01; live sampling remains NOT_TESTED. The phone getter is global state, not actual graph/listener/queue/lease ownership. A positive sampler result is not general quest acceptance or reward/owner verification. QR10's observability boundaries remain applicable.

No remaining quest fixture is currently qualified. The [runtime queue](runtime_test_queue.json) preserves source evidence and gives exact missing prerequisites for CVI, Ronald, Skippy, Brendan, pending-owner/rewards and Nitro. Successful QR9 Bullets/Zane/Wilson/Cynthia and completed-state reload observations must not be repeated.

Real Program Files permissions and hardware power-loss behavior cannot be proven by workspace fixtures. The two leaves are individually atomic, not a globally atomic pair; preserve the flushed journal and use the explicit recovery procedure on interruption. A normal stopped logger needs no cleanup/rollback. All real mutating commands remain for a separately authorized deployment or the user's own chosen execution.
