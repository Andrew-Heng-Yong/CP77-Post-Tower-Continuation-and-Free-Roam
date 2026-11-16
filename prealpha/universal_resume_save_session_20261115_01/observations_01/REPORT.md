# v0.1.7 Manual Save 30 guard check

15 November 2026, Toronto time. RED4ext loaded checkpoint v0.1.7 at 10:14:15.244 and the checkpoint runtime registered capture and decode at 10:14:37.132. The user reported that CET returned `true` on the Manual Save 30 probe. The installed DLL matched SHA-256 `70A820D791635CA2AA9455D31BFB95169EA4ECE1943B4C6E77F4E3936F505568`. Manual Save 30's `sav.dat` matched the known fixture SHA-256 `6D1EFBA83496CD1D53A6EC91F87A1E201D8AEC09B11B3BFF5B12A20A895E9146`. [Installed manifest](../deployment_01/installed_manifest_01.json)

The two relevant lines in `red4ext/logs/ptfr_executioncheckpoint-2026-11-15-10-14-37.log` were

```text
[2026-11-15 10:17:06.140] [info    ] [ 27384] [PTFR Quest Execution Checkpoint] PTFR checkpoint probe ready: phases=4060 live_handlers=9993 slots=10094 AND_rows=2348 node_instances=25 notifications=0 resource_requests=0 wait_handlers=18
[2026-11-15 10:17:06.156] [info    ] [  2368] [PTFR Quest Execution Checkpoint] PTFR native save handoff admission: idle
```

**PASS for live idle admission.** The queued probe reached the native save dispatcher and acquired the guard on its live session. The active-save and held-handoff cases have offline coverage. The first live timer handoff and its post-Tower save and reload remain pending. [Guard implementation](../NativeSaveAdmission.inc) · [Offline detour checks](../run_01/CheckpointChecks.txt)
