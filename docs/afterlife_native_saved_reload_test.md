# Afterlife A2 saved-active-session reload test

Authorized by the user on 2026-09-24 for **one new disposable manual save only**. Do not overwrite Manual Save 13, a master fixture, or any existing save. A3's quota is 0 and it is inert. The v5/v6 fallback and A2 package hashes were verified unchanged before the test. This test is Afterlife-only; no story facts, other mirrors, or vendors are changed. The user performs the in-game save/load manually.

First attempt at Stage 1 (13:50Z) did **not** create a save. The log reached `Requested=Guard=Ready=1`, old Enabled=0, Active=0 at the idle mark near Claire. The player then walked to the mirror before Stop; the final snapshot was scene/workspot active with one request. The user confirmed no save was made and the game was closed. The standard game save directory showed no new manual slot. This attempt does not count as a persistence test. On retry, remain physically near Claire throughout Stage 1 and do not visit the mirror before creating the new manual save.

Stage 1 retry created `ManualSave-16` at 10:01:28 local time, the first new manual slot observed since the 2026-09-23 baseline. The durable A2 log `afterlife_native_scene_a2_20260924T140045Z_0001.jsonl` records baseline at (-1441.2933, 1013.0497, 16.5000), successful Arm, then Requested=Guard=Ready=1, old Enabled=0, Active=0, SceneRequests/Returns/Rearms=0/0/0 and scene/workspot false at `idle-before-new-save` at 10:01:12. Read-only save metadata for `ManualSave-16` reports the same player position. This supports the intended outside/idle save point. The game was still running at the last process check; wait for a full exit before Stage 2.

Stage 2 log `afterlife_native_scene_a2_20260924T140705Z_0001.jsonl` begins after a full game exit and fresh launch from `ManualSave-16`. At baseline and before entry, A2 Requested/Boot/Guard/Ready=1/1/1/1 with native counters 0/0/0; old Enabled/Near/Active=0/0/0. After one reported visit, native SceneRequests/SceneReturns/Rearms=1/1/1, Active=0, Interrupted=0, and old owner remains off. Sampled Tower/story facts are unchanged and there are no read errors. The user confirmed Look, one facial expression, and Stop all worked without manually rearming A2. The game was closed after Stop and `ManualSave-16` remained unchanged. Native saved-owner continuation **passed for this one outside/idle save**. This does not establish saving during an active mirror scene or behavior at other mirrors.

## Stage 1 — make one new test save while A2 is idle and armed

Load the original disposable post-Tower baseline save outside the bathroom near Claire. Enter each CET line separately:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Start("a2-persistence-before-save")
GetMod("PTFR_Afterlife_NativeScene_A2").Arm()
```

If Arm refuses, stop; do not change facts manually or save. If it succeeds, wait a few seconds and run:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("idle-armed-before-save")
local q=Game.GetQuestsSystem(); print("A2",q:GetFactStr("PTFRALMA2_Requested"),q:GetFactStr("PTFRALMA2_Guard"),q:GetFactStr("PTFRALMA2_Ready"),"old",q:GetFactStr("PTFRB0ALM_Enabled"),"active",q:GetFactStr("PTFRALMA2_Active"))
```

Expected `A2 1 1 1 old 0 active 0`. **Do not go to the mirror during Stage 1. Stay near Claire for Stop and for the save.** Only then stop the logger, use the in-game **New Manual Save** option to create one fresh disposable slot while still outside/idle, note its slot/name, and fully quit without saving again:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Stop()
```

The save itself is the sole authorized save mutation. Do not quicksave or overwrite another slot.

## Stage 2 — cold-load exactly that new save

After checking the Stage 1 log, relaunch the game and load the newly created test save near Claire. A3 is inert; do **not** run Arm. Start a fresh durable log and inspect state:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Start("a2-persistence-after-reload")
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("saved-reload-before-entry")
local q=Game.GetQuestsSystem(); print("A2",q:GetFactStr("PTFRALMA2_Requested"),q:GetFactStr("PTFRALMA2_Guard"),q:GetFactStr("PTFRALMA2_Ready"),"old",q:GetFactStr("PTFRB0ALM_Enabled"),"active",q:GetFactStr("PTFRALMA2_Active"))
```

Expected `A2 1 1 1 old 0 active 0`. If those values differ, do not force facts or enter the mirror; Stop the logger, quit without saving, report output. If they match, enter the mirror area once, use Look, one facial expression, and Stop, then leave toward Claire and wait at least one second. Record and stop:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("saved-reload-after-one-visit")
GetMod("PTFR_Afterlife_NativeScene_A2").Stop()
```

Quit without saving again. Success requires native request/return/rearm each increment by one for the reported one entry, Active=Interrupted=0 after exit, old owner remains disabled, user-visible actions work, and sampled Tower/story facts are unchanged. This proves one safe outside-idle saved reload only; it does not cover saving while inside the scene or universal persistence for other mirrors. Retain the new disposable test save for review unless the user separately asks to remove it.
