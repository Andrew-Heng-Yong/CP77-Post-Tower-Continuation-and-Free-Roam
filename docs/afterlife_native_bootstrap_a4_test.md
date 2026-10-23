# Afterlife A4 redscript startup regression

2026-09-24. A4 is one new installed redscript file (`AfterlifeNativeBootstrapA4.reds`, SHA-256 `F9A1FBA35C295664D04D2F3B9338CE6E54E21B82AC3AF658A1C8A18A0F39B059`). It is the Afterlife-only production startup candidate, not a new mirror rollout. The working v5 archive, v6 driver, A2 archive and A2 CET observer remain byte-for-byte unchanged; A3 has quota 0 and is inert. An exact-file rollback script is `tools/remove_afterlife_native_bootstrap_a4.ps1` and has not been run.

A4 uses redscript `ScriptableSystem.OnAttach` with an epoch-protected, bounded one-second startup retry. It checks genuine post-Tower facts, A2 Boot, old scene inactivity and V outside the Afterlife mirror radius. From an ordinary post-Tower baseline (`A2 Requested=0`, old Enabled=1), it writes only old `PTFRB0ALM_Enabled=0` then `PTFRALMA2_Requested=1`. A saved A2 state (`Requested=1`, old Enabled=0) is left untouched. Inconsistent or interrupted states are not switched. It does not write q307, Johnny, PONR or any other story facts. If the A2 request write fails synchronously, it restores the old mod-owned Enabled flag. The redscript compiler and live behavior remain unverified until the following game test.

## One short no-save regression

Load the same original disposable post-Tower baseline used for the A3 cold-load test, outside the bathroom near Claire. **Do not load ManualSave-16 for this first regression**, because it already contains active A2 and would not test A4's new switch. Do not run CET `Arm()` or save this session. Watch for a redscript compilation error on launch; if it occurs, stop and report it.

After the save loads, wait a few seconds. Enter each CET line separately:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Start("a4-production-startup")
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("a4-after-load")
local q=Game.GetQuestsSystem(); print("A2",q:GetFactStr("PTFRALMA2_Requested"),q:GetFactStr("PTFRALMA2_Guard"),q:GetFactStr("PTFRALMA2_Ready"),"old",q:GetFactStr("PTFRB0ALM_Enabled"),"active",q:GetFactStr("PTFRALMA2_Active"))
```

Expected `A2 1 1 1 old 0 active 0`. If not, do not force facts or visit the mirror; Stop the log, quit without saving, and report the output. If matched, enter the mirror area once and use Look, one facial expression, and Stop; leave toward Claire, wait at least one second, then:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("a4-after-one-visit")
GetMod("PTFR_Afterlife_NativeScene_A2").Stop()
```

Quit without saving and report physical actions. Pass requires clean redscript compile, automatic A2 startup without CET Arm, old scene owner off, native request/return/rearm=1/1/1 for one entry, Active=Interrupted=0 after exit, and unchanged sampled Tower/story facts. A4's bounded startup timer should stop after the switch; v6 remains installed as rollback, but its proximity fact remains 0 while old Enabled=0. A post-credit fresh-transition integration test and other mirror sites remain separate work.

## Live result (2026-09-24, passed for one site)

The game's `redscript_rCURRENT.log` reports successful compilation with the installed A4 source listed. The user loaded `ManualSave-15` (the A2 log's initial player position exactly matches that slot's read-only metadata; this save predates A2) and did **not** run CET Arm. A2's durable `afterlife_native_scene_a2_20260924T142622Z_0001.jsonl` begins with Requested/Boot/Guard/Ready=1/1/1/1, old Enabled/Near/Active=0/0/0, and native counters 0/0/0. After one visit the counters are 1/1/1, Active=Interrupted=0, old owner still off. Sampled Tower/story facts did not change and no read errors occurred. The user confirmed Look, one facial expression, and Stop worked; the game was closed without a new save. This validates the A4 automatic owner switch from the pre-A2 disposable baseline and one native mirror cycle. The v6 script remains installed and schedules its existing 0.5-second checks, but it keeps Near=0 while old Enabled=0; removing that residual poll is separate cleanup and has not been done. Keep v5/v6 available as rollback and do not extrapolate this one prefab to other mirror sites.
