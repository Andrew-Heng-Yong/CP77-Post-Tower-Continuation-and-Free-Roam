# Jinguji replay assessment — 3 November 2026

**Bullets completion is recorded in the broader CET log. The S05 sampler captured activation, then stopped on death/reload before the completion segment.** The user confirmed “Yes, died and reloaded” after the stop boundary was identified. No full fight replay or gameplay repair is requested.

The user initially reported “stopped, exited normally.” The later manual stop command appears after the probe had already stopped automatically; this is not an uninterrupted capture ending at that command. The game and launcher were closed at collection. Exact original logs were copied and hashed into this fresh directory. See [result.json](result.json) and [input pins](inputs.json).

## Observed timeline

Times below use the source's UTC-05:00 offset, matching America/Toronto on3November. Capture UTC timestamps and broader-log line identifiers are retained in result.json.

| Local time | Evidence |
| --- | --- |
| 13:21:53 | QR10D01 S05 starts,32watched facts. Baseline native active0/done0, met4, private Issued/Entered1, Finished0; native journal Inactive. Initial values do not prove executing ownership or exact saved identity. |
| 13:23:28 | Two sampled differences: native vendor default1→0 and `mq030_active`0→1. Both independently correlate with matching broader-log writes inside the capture window. This is sample-detection time, not exact native-write time/order. |
| 13:25:02 | Bounded native journal getter reports Active(2). This getter observation does not date the underlying journal write. |
| 13:25:28 | STOP reason `PLAYER_DETACH_OBSERVED_SCRIPT_CALLBACK`; cleanup disables sampling. User confirms death/reload. |
| 13:26:38 | Broader log after reload records MaxTac arrival. This is outside the capture. |
| 13:27:03 /13:27:55 | Broader log records Zane gratitude and the selected Melissa dialogue fact. No sampled continuation is claimed. |
| 13:28:06 | Broader log records `mq030_done`0→1 and `mq030_active`1→0. Completion is corroborated; exact internal owner termination/rewards are unobserved. |
| 13:28:32 | User's `stop("QR12_JINGUJI_DONE")` command appears, after the already-completed automatic stop. It does not extend capture coverage. |

## Separate results

- **PASS — bounded activation sampling:**10valid sequential rows;215seconds;106sample rounds;3,424fact getter calls including the32initial reads;2coherent sampled differences; zero recorded getter/state errors; explicit native-callback-unavailable declaration and clean cleanup. No native `FACT_DELIVERY` event is expected or claimed.
- **Completion corroborated by the broader log:** native done1/active0 follows the confirmed reload. The user did not separately describe the replay's voice/dialogue/visual behavior; do not manufacture an all-behavior PASS.
- **INCOMPLETE — full encounter/completion sampling:** MaxTac, gratitude, Melissa conversation and done/active cleanup happened after the capture stopped. They are separate broader-log observations, not missing native callbacks or silent probe transitions.
- **Expected lifecycle guard:** stopping on detach prevents conflating saved sessions. No diagnostic defect or runtime correction is established. A new segment must be started after a death/reload if continued capture is needed.
- **Still unobserved:** actual native/private graph, listener, lease ownership/termination, exact saved slot/body identity, reward quantity/idempotence, native request/ACK execution, exact write ordering and unseen intermediate values.

The original QR9 completion/shop/post-dialogue/completed-reload successes remain accepted; they need no repetition. This replay supplies a validated activation capture, not universal S05 lifecycle acceptance. A short pending-stage scenario, if later justified, needs its own qualified current fixture and instructions; it is not automatically prescribed here.

## Preservation

All60current manifest-protected installed hashes match; the six files belonging to ManualSave-23 and24 match their pre-replay pins. All83artifacts in the sealed QR12 completion manifest remain exact. Human gameplay legitimately changed autosaves/logs; no complete save-root immutability is asserted across this run. Current save metadata was inventoried read-only, without reparsing saved bodies or deriving owner liveness from metadata.

The assistant copied logs and wrote this fresh assessment only. No game launch/control/CUA, save/fact manipulation, installation, diagnostic change, rebuild or quest repair occurred. Current hashes are post-run observations, not retrospective proof of every executed byte.

## Next action

No additional replay is needed now. For future captures, restart recording after death/reload as a new labelled segment; stop before intentional save changes and never merge segments into one owner history. The replay instructions should have made that restart rule explicit. The original prepared plan remains preserved; this assessment supplies the clarification.
