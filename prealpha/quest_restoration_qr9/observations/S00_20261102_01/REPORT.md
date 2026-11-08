# November 2 human run — bounded success

The user reported starting the probe at the main menu, entering the game, completing a gig without problems, stopping the probe and quitting. **The load/play smoke passes on that reported scope.** Logs and metadata strongly identify the gig as **Until Death Do Us Part (`sts_wbr_hil_01`)**. The exact title and loaded slot await the user's clarification; no repeat of this completed route is requested.

## What the evidence proves

- The S00 capture armed at **11:44:34 EST**, attached to an in-game player at 11:44:44, returned IDs for all 17 listener calls at 11:44:47, and recorded initial journal/phone/fact state without API errors.
- The probe automatically stopped at **11:49:34**, its configured **300-second duration limit**. All cleanup calls returned without error. There are no fact-delivery rows for its selected S00 facts; this does not prove absence of changes outside that watchlist or actual listener delivery.
- The user entered manual stop at **11:53:59**. By then the bounded capture was already closed. This was expected duration-limit behavior, not a probe crash. The full gig was not recorded by that probe.
- The separate CET scripting log continued recording after the probe stopped. At 11:53:13 it reports the gig's deposit receipt and Wakako start-count increment; at 11:53:34, `hil_01_finished` changes0→1, Westbrook completion counters increment, and at 11:53:35 the Wakako end-count increments. These are reported fact transitions, not exact graph-node or audible-call proof.
- AutoSave-1 metadata at 11:53:33 lists `sts_wbr_hil_01` as newly finished relative to the untouched master. AutoSave-0 tracked taking the shard; earlier metadata tracked reaching the councilman's apartment. The metadata timestamp slightly precedes the finish callback, so it is corroboration rather than a strict event-order clock.
- The master and ManualSave-24 already tracked this gig at the councilman-apartment stage. This run supports **continuing one already-active gig route through completion**, not fresh restored admission. ManualSave-24 exists as a working-save candidate, but metadata/entity ID cannot identify which slot the user actually loaded.
- In the matching load window, ArchiveXL logs parent quest patching and merges of the exact Ronald helper and PH3 shared-studio phase paths. This passes logged resource-merge preparation. It does not prove native startup dispatch success, exact private-owner activation or prefab lease acquisition.
- The current run's REDscript log reports successful compilation/output, and RED4ext records normal shutdown. No current-session scripting error candidates were found in the collected log. ArchiveXL has four existing clothing-resource link errors and three optional `mod\quest\newgameplus*.quest` missing-phase warnings, all with matching signatures in the previous run. Their broader impact was not investigated or certified here; they are not source-confirmed PTFR defects.

## Preservation and results

The guarded Core and Diagnostics Verify commands both returned **VERIFIED_AFTER** after the user quit. All 51 core and two observer file hashes match. All six pinned core dependencies verify, and the three original ManualSave-23 files and their offline backup still match. The generic collector marks Lizzie's large archive UNAVAILABLE because it exceeds that collector's64MiB bound; the separate Core Verify hashes that dependency successfully. It is not missing from disk.

The fresh [results matrix](analysis_01/results.json) and CSV preserve all other unperformed cases. S00 has two bounded PASS rows (reported visible load/play and logged registration/resource merges), one INCONCLUSIVE row (actual private owner), 20 other cases remain NOT_TESTED and three remain NOT_TESTABLE on the selected completed-CVI fixture. An additional gig observation records a user-reported PASS corroborated by completion evidence. This is not a ten-contract or all-route pass. Exact rewards, duplicate prevention, reload after completion and all phone variants remain unverified.

Ronald's contact was Inactive and message permission0 in the initial S00 state; its helper Issued0 is not treated as a fault or bypassed. The held first-enrollment route and other QR8 static limitations remain unchanged.

No mod/game/source/save/fact edits, game launch or CUA occurred during analysis. Only new workspace evidence and curated status pointers were written. No repair, build or deployment is justified by this run. The original collection integrity result remains immutable; the assessment is a separate successor, reproducible with `analyze_run.py --output <fresh-contained-name>` from its copied logs/metadata evidence.

Next: incorporate the user's exact gig/loaded-slot answer when available, then choose a genuinely eligible targeted card. For a later longer scenario, use that card's bounded profile for the relevant event window or segmented captures; the logger supports up to900 seconds through the third start argument. Do not repeat a completed gig or leave a capture running for multi-day timers. Private graph/owner/receipt/clock/queue/save-ID observations remain NOT_OBSERVED.
