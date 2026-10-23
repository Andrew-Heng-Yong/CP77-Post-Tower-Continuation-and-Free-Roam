# Afterlife A3 automatic cold-load bootstrap test

2026-09-24. This is a two-run development-only CET bootstrap for the proven one-site A2 native Afterlife mirror scene. It does not replace the installed v5/v6 fallback, A2 resources, or any vanilla resource. It is not production code; CET remains a diagnostic dependency here. The installed controller hash is `1671D5C51EEA391124424F4BFE3DC6C00A271577AD448192926F6396E1FFC7F5`.

The bootstrap starts with a local quota of two **successful** cold-load arms. On each launch it waits up to 300 seconds for a loaded, post-Tower player to be outside the Afterlife mirror area and outside combat/scene/workspot. It then calls the already-tested A2 `Start()` and `Arm()`; A2 alone writes `PTFRB0ALM_Enabled=0` and `PTFRALMA2_Requested=1` after its full guard check. A3 consumes one quota only after A2 reports success and makes no further updates that launch. When quota reaches zero, it becomes inert on future launches. Do not save while A2 is armed. The quota file is diagnostic local configuration, not a game save.

## First cold-load check

1. Load the original disposable post-Tower save **outside the bathroom near Claire**. Do not run `Arm()` manually.
2. Wait a few seconds, then in CET run each line separately:

```lua
GetMod("PTFR_Afterlife_Native_Auto_A3").Status()
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("a3-after-auto-load")
```

Expected: `remaining=1`, `pending=false`. If A2 says `Start recording first`, or A3 reports no automatic arm, stop and quit without saving. Do not force facts.

3. Enter the mirror area once, use Look, one expression, Stop. Leave toward Claire and wait at least one second. Count how many times you **entered** the mirror area from outside (normally one). Run:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("a3-after-one-visit")
GetMod("PTFR_Afterlife_NativeScene_A2").Stop()
```

4. Quit without saving and report the physical actions and number of entries. The durable A2 log must show auto `ARMED`, Guard/Ready=1, old scene owner off, and native request/return/rearm counts equal to the reported entries.

Only after inspecting the first log, repeat from the same unchanged disposable baseline for the second cold load. Expected A3 quota then drops to zero. This validates automatic cold startup, **not** persistence of A2 state from a saved active session. Saved-load persistence requires separate, explicit authorization to create a disposable save and remains untested.

### First cold-load result (2026-09-24)

User confirmed Look, one facial expression, and Stop worked and reported one entry into the mirror area. A3's installed quota went from 2 to 1. The flushed A2 log `afterlife_native_scene_a2_20260924T133353Z_0001.jsonl` shows fresh baseline, automatic `ARMED`, Guard=1 and Ready=1 at `a3-after-auto-load`, and exactly SceneRequests=1, SceneReturns=1, Rearms=1, Active=0, Interrupted=0 after the visit. The old scene owner remained disabled (`PTFRB0ALM_Enabled=0`, Near=0, Active=0); sampled Tower/story guards did not change. The game process was closed after the test. First automatic cold-load attempt passed; one quota remains. This is not a saved-active-session reload test.

### Second cold-load result (2026-09-24, passed)

The user entered the mirror area once before making the requested manual mark, then visited it again. A3 auto-started its A2 log at 13:39:48Z and consumed the final quota (installed quota now 0). The log `afterlife_native_scene_a2_20260924T133948Z_0001.jsonl` records automatic `ARMED`, then SceneRequests/Returns/Rearms=1/1/1 at `a3-second-auto-load` and 2/2/2 at `a3-second-after-visit` and Stop. Guard=Ready=1, Active=Interrupted=0, and old Enabled/Near/Active=0 at the final mark. The two native cycles match the two reported entries despite the first visit occurring before the manual mark. The user confirmed Look, one facial expression, and Stop worked on both visits and quit without saving; process closure was checked. Both automatic cold-load attempts passed. This does not establish saved-active-session persistence.

## Rollback and scope

The old v5 archive, v6 redscript driver, A2 archive and A2 CET logger were hash-checked before and after installation and remain installed. Quit without saving to return to the baseline. A3 is installed as two new files only in `PTFR_Afterlife_Native_Auto_A3` and becomes inert after two successful arms. No other mirror is affected. No 36-mirror rollout follows from this test.
