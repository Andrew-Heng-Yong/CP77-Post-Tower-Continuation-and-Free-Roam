# Jinguji load observation — two attempts, 3 November 2026

**Both attempts corroborate the user's completed journal on load, and both capture later terminal fact changes. No additional Jinguji test is requested.** The narrow observed result is PASS for post-load terminal-fact progression on these attempts; it does not prove exact saved-owner identity, cleanup/lease execution or rewards.

The user reported “did it2times. already complete after load in.” Both separately labelled S05 captures were armed from the main menu and waited for attachment. At the first journal read each showed `Succeeded(3)`, consistent with that report. The initial fact reads nevertheless showed `mq030_active=1`, `mq030_done=0`. Both later sampled active1→0 and done0→1,22/25seconds after attachment. Completion-related fact updates therefore were observed; they did not all precede the first baseline.

The journal and terminal-fact interfaces expose different observed points in progression. This is preserved as evidence, without claiming exact native writer timing, identifying a specific executing controller, or inventing a bug/fix. No Active→Succeeded journal transition was captured in these attempts.

## Separate capture results

| Item | Attempt1 | Attempt2 |
| --- | --- | --- |
| Capture | `QR10_capture_20261103T183826Z_0001.jsonl` | `QR10_capture_20261103T183943Z_0002.jsonl` |
| Main-menu arm (Toronto, UTC-05) | 13:38:26 | 13:39:43 |
| Attached baseline | 13:38:40 | 13:40:11 |
| First journal state | Succeeded(3) | Succeeded(3) |
| Terminal fact differences detected | 13:39:02 | 13:40:36 |
| Time after attachment | 22seconds | 25seconds |
| Total wall duration /sample rounds | 54seconds /19 | 88seconds /29 |
| Getter calls, including32initial reads | 640 | 960 |
| Sampled changes /recorded read errors | 2 /0 | 2 /0 |
| Stop | Player detach at13:39:20 | Explicit pending-done stop at13:41:11 |
| Capture cleanup | Recorded | Recorded |

The first run's detach stop occurred after its terminal samples. No death is inferred for this attempt. The next capture is a separate main-menu-armed segment. The second run stops cleanly on the requested command. Neither reaches the5minute limit. Native callbacks remain explicitly unsupported and no FACT_DELIVERY claim is made.

Both broader-log segments independently record `mq030_done`0→1. Their notice timestamps are several seconds later than the getter detection timestamps. Preserve both; these observations do not establish exact engine write order or the cause of recorder latency. Within each two-second sampling pass, active/done log ordering reflects reader iteration, not necessarily native-write order.

## Coverage and boundaries

Verified here: main-menu arming, attachment after load, readable completed journal, active/done getter finalization in two distinct attempts, no recorded getter/state errors, and cleanup of each diagnostic capture. The user did not report a visible stall. There is no basis for another fight, another identical load, a speculative gameplay repair or a diagnostic implementation change.

Not verified here: actual native/private graph/listener/lease/owner termination, precise saved scene/node, exact saved slot identity from the probe, item/currency/reward idempotence, all branches or unseen writes before attachment/between samples. The original source body is pinned and still exact, but runtime saved identity is not independently reported by the logger. A completed journal does not by itself prove controller termination. The private wrapper's Finished/lease markers are not promoted to executing-owner proof.

Earlier QR9 Bullets completion, shop return, post-dialogue and completed-state reload remain accepted. The earlier full replay's activation samples and post-death broader-log completion are retained separately. These two load attempts add bounded terminal-fact evidence; they do not convert S05's full internal-lifecycle coverage to PASS.

## Preservation and handoff

Original logs were read only and copied/hash-pinned to this fresh folder; [result.json](result.json) records exact observations, source lines and evidence limits, and [inputs.json](inputs.json) pins the copied files. All60current installed hashes, both manual saves' six pinned files, the candidate's three files and all83sealed QR12artifacts still match. This is not a whole-save-root immutability claim over human gameplay or retrospective proof of all executed bytes.

No assistant game launch, game API/CUA, installation, runtime/diagnostic edit, save/fact write or rebuild occurred. **Close this Jinguji check.** Other high-risk scenarios still need genuine eligible histories or separate source-confirmed development work; do not repeat accepted routes just to generate more logs.
