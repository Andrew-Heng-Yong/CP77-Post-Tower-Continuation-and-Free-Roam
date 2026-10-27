# Skippy pre-ending behavior reference — 27 October 2026

The user explicitly confirms all four observations in the **pre-ending world**: reload remarks, lines on drawing, a shot/comment from aiming without pressing fire, and matching hologram expressions. This is a native pre-ending behavior reference with the current mod setup still installed, not a clean unmodded run. No counts, exact dialogue sequence or timing measurements were supplied. Jump acknowledgement was not included in the question or confirmation.

The captured logs distinguish this from the earlier restored session. After the 11:43:32 load boundary, the 11:43:58 SC3 status reports `tower=false`, `Ready=1` and `Request/Claimed/Entered/Active/Stop/Stopped=0`. Thus SC3's private ambient controller was unclaimed and inactive at that sample. Times are Toronto local time.

The pre-ending log records aiming at 11:44:15–19, reload at 11:44:21–23 and another reload at 11:45:01. Native dialogue-interruption/rapid-interruption flags are set at 11:44:25 and cleared at 11:45:22. Enemy counters advance, including total 94 to 98. These facts corroborate native activity; the audible and visible observations come from the user, because these logs do not contain a dialogue transcript or rendering trace. `gamelog.log` and `scripting.log` have different flush boundaries while the game is running; their point-in-time copies are retained separately.

This establishes that reload remarks can play in the user's pre-ending setup. It does **not** establish restored-world reload playback or explain the reported near-every-draw frequency. The [restored SC3 trigger review](skippy_triggers_20261027.md) remains separate. Future comparisons should use this pre-ending reference without converting it into a restored-world pass.

Evidence: `diagnostics/bottle_skippy_preending_20261027_01/capture_01` and `user_observations_01.json`. Capture assessment SHA-256: `E3D76F26AB7F22D30038CF5B49FFDB57E2CAFD293AA8FEFBDF41340773218C70`. Only logs were read and workspace evidence written; no game files, native facts or saves were edited.
