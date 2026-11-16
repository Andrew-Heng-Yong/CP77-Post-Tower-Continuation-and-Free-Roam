# v0.1.6 startup and MS26 smoke test

15 November 2026, Toronto time. RED4ext loaded checkpoint v0.1.6 at 00:50:49, and the checkpoint runtime registered capture and decode at 00:51:13. The installed DLL matched the authorized candidate SHA-256 `24A16F4AA09E00D763949DFC1DFFFC5EAE810917D2F9F79E768AD84FF957E0E1`. [Installed manifest](../deployment_01/installed_manifest_01.json)

At 00:55:16.819, the checkpoint probe logged 4,061 phases, 10,002 live handlers and 21 wait handlers. The guard logged `PTFR native save handoff admission: deferred` at the same timestamp in `red4ext/logs/ptfr_executioncheckpoint-2026-11-15-00-51-13.log`. This build reports engine availability, guard contention and a stock save in progress with the same status. Idle admission remains unverified. One retry in free roam after the save indicator clears can distinguish a transient deferral from a repeatable one. [Guard binding](../NativeSaveAdmission.inc)

Manual Save 30 was written at 00:56:02.263 with 4,673,009 bytes and SHA-256 `6D1EFBA83496CD1D53A6EC91F87A1E201D8AEC09B11B3BFF5B12A20A895E9146`. The user reported completing the new-slot save and reload test. The file and timestamp were independently observed. The first live timer handoff remains pending.
