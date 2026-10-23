# R8 automatic post-Tower startup — disposable smoke test

R8 is installed and starts without CET opt-in. The original neon/police
sector has only 12 added individual references. The Tower's five authored
Cold/blue light and strip nodes are cloned into a private default-off sector.
Native controllers switch the hotel from pink to blue after genuine Tower
completion; the seven police lamps hide only when the existing R7 street
restoration is active. A redscript bridge automatically arms R7 after the
ending when V is safe and outside the 80m clinic area. Separate guarded
bridges request the previously tested Tower journal and frozen-clock fixes.

**Use a disposable save and do not save this first test.** A crash is a failed
test; do not repeat the last command. The rollback is prepared and validated.
No CET Start/Hide/Show or RedHotTools visibility action is needed.

## Pre-Tower baseline

Cold-launch a suitable pre-Tower save and inspect the hotel strip/police-line
area normally. It should remain vanilla pink with its original police lights.
The new Cold sector must remain off. If the baseline changed, quit without
saving and report it before continuing. The strongest compatibility test is
to play the normal Tower finale from this save through credits and the direct
return, with no forced facts or S1 commands.

## Automatic post-Tower activation

After the direct return, allow V to settle. If you are near the clinic,
walk/drive out of the 80m safety area. This previously used outside TP is
available if the ground is visible:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
```

Close CET and wait about 10 seconds. This does **not** arm anything; it only
lets the automatic R7 bridge satisfy its prior safe-distance rule. Read:

```lua
local q=Game.GetQuestsSystem(); for _,n in ipairs({"PostTowerFreeRoamActive","q307_active","q307_done","q307_finished","q307_2079","PTFRMV_Revision","PTFRMV_Enabled","PTFRMV_Applied","PTFRTJA_State","PTFRB0TU_Done"}) do print(n,q:GetFactStr(n)) end
```

Expected Tower guards are 1/0/1/1/1. R7 should show Revision7,
Enabled1 and Applied1. `PTFRTJA_State=1` means the journal reconciler's native
readbacks verified; 2 or 4 is a guarded refusal/partial result to report.
The time one-shot Done can remain0 if the clock was not paused. Do not force
any facts if a counter is delayed or missing.

## Same-view street comparison

Visit the hotel strip and police-line area. This is a previously reported
standing point; teleport only if the floor is visibly present:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1543.04138,y=1182.21973,z=17.05,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Close CET, wait up to 20 seconds once for the sector to stream, and inspect
the vertical hotel strips and nearby pavement. The pink light **and** pink
emissive strips should be absent, replaced by blue/cyan Cold counterparts.
The seven police-line lamps should not leave the prior yellow residue. The
construction props, trucks, terminal, Zetatech frontage/access and normal
pedestrian behavior should remain as previously accepted; no need to redo
their full test route.

Read the native controller facts:

```lua
local q=Game.GetQuestsSystem(); for _,n in ipairs({"PTFRMVN_Registered","PTFRMVN_Revision","PTFRMVN_Applied","PTFRMVN_Ready","PTFRMVN_ApplyRequests","PTFRMVP_Registered","PTFRMVP_Revision","PTFRMVP_Applied","PTFRMVP_Ready","PTFRMVP_ApplyRequests","PTFRMV_Applied"}) do print(n,q:GetFactStr(n)) end
```

Expect each R8 Revision8, Applied1, Ready1, with ApplyRequests at least1.
Those counters prove dispatch, **not** visible color. Paired pre-/post-Tower
screenshots from similar camera views establish the visual result. If the
neon stays pink or overlays both colors, report that even if counters read1.

Quit without saving. Send the two CET outputs, whether pink became blue,
whether police glow disappeared, and any crash/overlap. Only after this
smoke test passes should we test save, full quit, reload and return streaming.
