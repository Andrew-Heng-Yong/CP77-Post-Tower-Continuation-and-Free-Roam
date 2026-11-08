# D00E natural sampler validation — PASS

The human-operated El Capitan call validates the bounded getter-difference sampler on this fixture. **No repeat is needed.** This is not native callback delivery, full quest acceptance or actual engine-owner proof.

Evidence: `d00e_01/evidence/D00_20261103T162157Z_52fee7/`; capture `QR10_capture_20261103T161958Z_0001.jsonl`, SHA256 `EF31629E3BFE4A44C67A1CAB2BF312882BC3E4D032643F46E7B33217E9F10CE0`. The original capture and frozen copy match. The collector's provisional summary is preserved unchanged; this separate assessment adds the human correlation.

The user answered **“yes”** to whether the call connected or showed dialogue and ended normally, and whether the requested ManualSave-24(2Nov16:37) was loaded. This is accepted as user confirmation of normal call behavior/requested working slot; no specific anomaly was reported. Exact save identity remains unobserved by the probe, and no particular dialogue line/voice is inferred from that short reply.

## Observed values

| Capture time UTC | Elapsed | Observed getter value/change |
| --- | --- | --- |
|16:19:58 |0s | Attached baseline0 |
|16:20:18 |20s |0→1; prior successful read at18s |
|16:20:22 |24s |1→2; prior successful read at22s |
|16:21:10 |72s |2→0; prior successful read at70s |
|16:21:30 |92s | User stop `D00E_DONE` and capture cleanup |

The watched fact is `phonecall_player_with_muamar_el_capitan_reyes`. These timestamps identify **sample detections**, not native write timestamps. Numeric phone-state enums are not guessed. Changes that occurred and reverted between successful reads would remain unseen.

Global phone-active getter was false at baseline, true when sampled at22s, and false again at72s. This agrees with the human-confirmed call and return. It does not identify a particular controller/graph or establish native ordering relative to the fact writes.

## Verification

-12schema2 rows, one run/profile, contiguous sequence, one start/baseline/stop/cleanup.
-3coherent sampled differences,45sample rounds,46fact getter calls including baseline.
-No sampled-fact, baseline-read, unavailable-API or state-getter errors recorded; user stop happened before the120second cap.
-Cleanup records sampling disabled and zero native quest subscriptions by this sampling-only implementation; this is not enumeration of the engine's listener registry.
-All60post-run current diagnostic/Core/dependency/EXE hash measurements match the exact current manifest, including unchanged Lua and the D00E config. Prior verified deployment and capture declarations support binding; post-run hashes alone do not retrospectively measure executed bytes.
-Copied log-tail hashes and installation receipt hash match collection metadata. No matching El Capitan fact entry was found in the supplied broader scripting-log tail; no independent native-write trace is claimed. Its absence is not a failed-call result.

[Machine-readable assessment](result.json), [coverage boundary](coverage.json), [reproducible read-only assessment](assess.py). No game launch, CUA, runtime/config edit, save/fact write, build or deployment was performed during this assessment. Legitimate human gameplay/autosaves are separate from the earlier deployment's310-file preservation result.

## Closure and next work

**D00E PASS — one natural getter-difference observation.** The QR10 fallback now has live evidence and may support later qualified manual tests. Native callbacks remain **UNSUPPORTED_NOT_TESTED**; exact graph/listener/queue/lease/timer/save-owner observations remain unproven. Heavy96fact-profile runtime overhead, missed-transient coverage, reload races and other quest routes are not certified by this one-fact test.

Regina D00 remains NOT_TESTABLE. No additional CVI/Ronald/Skippy/Brendan/Nitro/pending-owner fixture is currently qualified; prior Wilson/Bullets/Zane/Cynthia/reload successes remain accepted. No further gameplay test, cleanup, rollback or repeat is requested now. A stopped logger is idle. Preserve this evidence and request new quest tests only after genuine fixture prerequisites are established.
