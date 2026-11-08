# PTFR QR9 — human runtime validation stage report

Date: **2 November 2026**, America/Toronto. Core: **QR8:02**. Optional diagnostics: **QR9B04**.

## Outcome

**The sampled quest routes and their reported shop/reload checks passed. Comprehensive QR9 runtime acceptance remains incomplete.** This report records the completed observations and the remaining coverage; it is not a blanket restoration or release PASS. The user confirmed that Bullets' completed-state reload was already checked, Zane's shop worked and post-Bullets dialogue was present. No repeat of that check is requested.

The user performed all gameplay and CET commands. Codex prepared the reviewed tools, performed the separately authorized deployment, collected logs, compared pinned native evidence and recorded bounded results. No CUA, automated gameplay, game launch by Codex, quest/fact setter, save edit, forced reward or actor command was used. No gameplay repair or diagnostic update was implemented during these observations.

## Installed baseline and preservation

The user explicitly approved deployment on 31 October. [Deployment evidence](deployment_01/REPORT.md) records successful Core/Diagnostics preflight, install, after-state verification and rollback-readiness checks. No rollback was executed.

- Core: 51 stable paths, 1,577 archive payloads. Only the combined archive and its XL changed from PH3.
- Archive SHA256: `2AB35CC95931CD3C7BB2FB3A4C8B52746DE7847D42AE1DD3503A90A965FD2039`.
- XL SHA256: `F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245`.
- QR9B04 adds two separate CET files; they are outside Core51. Exact identities are in [Core02](worker_a/core_manifest_02.json) and [Diagnostics01](worker_a/diagnostics_manifest_01.json).
- No unchanged core rebuild, fresh compiler run by Codex, baseline ZIP regeneration or release publication was needed.

At report preparation, a fresh read-only hash check matched all 53 installed payloads and all six files comprising original ManualSave-23 plus its verified three-file recovery backup. See [runtime pins](stage_report_01/runtime_pins_before.json). The last full Core Verify after the captured Bullets run also passed its 51 files, six external dependency pins and master/backup checks. The large Lizzie archive exceeds the general collector's 64 MiB bound; it was checked by that separate Core Verify, not silently assumed valid.

ManualSave-23 is the user-confirmed genuine Tower master. Working saves, including ManualSave-24 and normal autosaves, advanced through human play. The deployment's 307-save-file preservation result was a deployment-time result; it is **not** a claim that all working saves remained unchanged during gameplay. Save bodies were not parsed or edited. File rollback is not save rollback.

## Observed results

| Scenario | Result | Evidence and boundary |
| --- | --- | --- |
| Load/play smoke | PASS, bounded | User loaded and played successfully; probe attached and read initial state. This does not certify every ending presentation or exact private-owner startup. |
| ArchiveXL registration/resource merges | PASS for logged merges | Matching-run logs show parent patching and Ronald/shared-studio resource merges. This is not proof of successful native dispatch, actual owner activation or prefab acquisition. |
| Until Death Do Us Part | PASS for the continued route | User confirmed the title and no problems. Broader logs show the deposit receipt, Wakako call counters and finished transition; save metadata adds the completed gig. It was already tracked before this test, so fresh admission was not demonstrated. |
| Cynthia call | PASS for delivery | User received it; matching native start/end counters and phone-state observations corroborate delivery. Other Raymond Chandler Evening branches and reload are not covered. |
| Wilson invitation | PASS for delivery/activation | User received Shoot to Thrill; start/end counters and `mq011_active`0→1 corroborate the invitation. |
| Shoot to Thrill completion | PASS for reached winning route | User completed it; the final segment logs win, reward receipt, done1/active0, and finished save metadata. Earlier reload/second-place segments remain separate. Exact inventory payout and every outcome were not measured. |
| Wilson shop recovery | PASS, user-confirmed | Immediate trading was unavailable, then recovered after leaving/returning or waiting. Native scene/actor cleanup supports a non-instantaneous handoff. The exact recovery action and perfect vanilla-equivalent latency remain unproven. |
| Completed Wilson reload | PASS, user-reported | Completed quest and trading survived reload. Exact repeated-reward/invitation absence was not explicitly reported. |
| Nitro precheck | No valid fresh fixture; existing-owner result INCONCLUSIVE | Saved Issued1, purchase counter1, four guarded unlock readsfalse and Inactive journal. Fresh pre-Issued tests cannot be manufactured on this history. Current Issued1 does not identify an executing owner or when it was issued. No reset or purchase manipulation was performed. |
| Bullets starter | Native prerequisite observed; no defect established | First meeting was recorded. The pinned native route waits for `mq030_zane_met>0` then player outside the Jinguji-away trigger; a separate start-menu option is not required. The quest subsequently activated. |
| Bullets completion | PASS for reached route | Probe journal Inactive→Active→Succeeded; broader log records MaxTac, gratitude/dialogue, done1/active0; ManualSave-24 lists `mq030` finished. Exact reward contents and all outcome branches remain unproven. |
| Zane shop return | PASS, user-reported | Trading worked after returning following Bullets. Functional shop recovery does not directly expose helper termination/private lease state. |
| Completed Bullets reload and dialogue | PASS, user-confirmed | User explicitly confirmed that the check was already done, the shop worked and post-Bullets lines were present. No further replay or reload request is needed for this observation. |

The final Bullets confirmation is preserved [verbatim](stage_report_01/bullets_reload_confirmation.json). Earlier pending assessments remain unchanged historical evidence; the [cumulative results](stage_report_01/results.json) supersede their current-status interpretation without rewriting them.

Machine-readable exports: [planned-case CSV](stage_report_01/results.csv), [additional functional observations CSV](stage_report_01/functional_results.csv), and [coverage/remaining work](stage_report_01/coverage.json). [Report verification](stage_report_01/verification_01/result.json) passed data parity, linked evidence hashes, local-link checks and preservation of the named installed/master files; it is a documentation check, not a new gameplay test.

## Coverage of the original plan

The prepared plan contains **nine cards with 26 alternative subcases**. These are not 26 independent quests, and unavailable histories must not be reset to satisfy them. The cumulative exact-subcase matrix currently contains:

| Status | Subcases |
| --- | ---: |
| PASS, bounded original observations |2|
| INCONCLUSIVE |3|
| NOT_TESTABLE on the selected fixture |5|
| NOT_TESTED |16|

Additional successful functional observations are recorded separately from this denominator. In particular, completed Wilson/Bullets reloads do not prove the original pending-controller interruption/reload alternatives, exact reward idempotence or direct helper retirement. A functional vendor PASS is not silently promoted to full S05 lifecycle PASS.

| Remaining family | Current limit |
| --- | --- |
| S00 exact private graph/owner activation | INCONCLUSIVE; the probe provides no exact executing-owner/engine-receipt API. |
| S01 alternate Hands/CVI success, failure and muted routes | NOT_TESTABLE on the selected already-completed CVI history. A different genuine supported fixture is needed. |
| S02 Ronald future news, late-future gate and timer/reload | NOT_TESTED. Last observed contact was Inactive/messages0; genuine enrollment and a qualifying future route were not established. First enrollment remains held. |
| S03 prospective Nitro positive/negative | NOT_TESTABLE on this already-issued history. Existing-owner execution remains INCONCLUSIVE. |
| S04 Machine Gun/Skippy return and timer/reload | NOT_TESTED; needs the exact supported stage/owner/history, not a reset or forced return. |
| S05 helper retirement and pending-cleanup reload | Functional completion/shop/reload passed. Exact helper termination/lease execution remains INCONCLUSIVE; the separate pending-cleanup-stage reload is NOT_TESTED. |
| S06 Brendan containment/progressed descendant | NOT_TESTED; no general fresh-chain/continuation adapter is approved. |
| S07 old/completed CVI/news/history variants | NOT_TESTED as planned; Wilson/Bullets persistence does not substitute for those specific histories. |
| S08 interruption, pending-stage reload and exactly-once reward revisit | Exact alternatives remain NOT_TESTED. Completed-state functional reloads provide partial evidence, not full reward/owner/interrupt coverage. |

No overall gameplay percentage or 161-quest runtime certification is claimed. QR8's held first Ronald enrollment, five static UNKNOWN contracts and inherited conditional/opaque limitations remain in force. This stage does not qualify the mod for general release or all saves.

## Diagnostic issue requiring engineering follow-up

**The QR9B04 probe's fact-callback coverage is unreliable.** During S05, the broader CET log recorded changes to facts included in the watchlist, while the probe produced zero FACT_DELIVERY rows. This occurred both during the first meeting and the final completion segment. Returned listener IDs, successful unregister calls,39 offline assertions, five source mutants and prior peer checks did not establish actual engine callback delivery.

The cause has not been confirmed. Do not guess a NewProxy signature, reset a quest or fabricate facts to make a diagnostic test pass. No diagnostic fix was installed. The positive user reports, probe journal getters, phone-state snapshots and broader fact logs remain separate evidence; absence of probe events cannot be used as negative gameplay proof. Direct graph activation, native owner/lease, numeric ArchiveXL receipt, native clock/queue and loaded-save identity remain NOT_OBSERVED.

Some initial probes stopped at their 300-second cap before later gameplay completed. Broader logs supplied later corroboration. The final Bullets capture used a 900-second limit and stopped manually after 476 seconds. Captures across reloads are kept separate; callback timestamps are not native-write ordering guarantees.

## Stage disposition and next work

This set of available functional route checks is documented and needs no repetition. **Full QR9 acceptance is still incomplete.** No confirmed gameplay defect from these sampled routes justified a repair. The unresolved diagnostic coverage failure and missing fixture/internal evidence prevent a blanket PASS.

The next engineering priority is to investigate the real callback API/binding and validate any source-confirmed diagnostic correction against a naturally occurring event, with independent review and explicit before/after evidence. Preserve the installed core, saved identities, master backup and all prior observations. Further gameplay should target genuine missing histories or specific unanswered contracts rather than repeat these successful routes. Any observer successor, deployment or gameplay repair needs its own concrete scope and guards; no such action was performed by this report-writing task.

Evidence entry points: [deployment](deployment_01/completion.json), [startup/gig](observations/S00_20261102_01/REPORT.md), [S03/calls](observations/S03_20261102_01/REPORT.md), [Wilson native handoff](observations/WILSON_20261102_01/REPORT.md), [Wilson reload](observations/WILSON_RELOAD_20261102_01/observation.json), [Jinguji first meeting/callback gap](observations/S05_20261102_01/REPORT.md), [Bullets final route](observations/S05_20261102_02/REPORT.md), [Zane return](observations/S05_20261102_02/shop_return_confirmation_01/observation.json), and [stage results/coverage](stage_report_01/results.json). Source paths, hashes, nodes/sockets and exact log lines are retained in the linked evidence directories.
