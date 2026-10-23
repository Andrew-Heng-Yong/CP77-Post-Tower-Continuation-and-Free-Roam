# One combined public dance-floor check

Cold-launch after installation and load a disposable post-Tower save satisfying
the normal PTFR guards. No Arm/Enable gameplay command is needed.

Start the read-only durable logger once:

```lua
GetMod("PTFR_ClubDancing_Audit").Start(); GetMod("PTFR_ClubDancing_Audit").Mark("baseline")
```

Use these authored trigger positions (not previously live-verified landings).
If the room is absent, do not treat that as a dancing-owner pass or unlock it.

Riot:
```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1639.896,y=1019.51758,z=24.1416092,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```
Empathy:
```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1631.86816,y=380.381042,z=8.0638361,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```
7th Hell:
```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1929.21655,y=-41.6847763,z=-2.10787177,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```
Totentanz:
```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1718.91467,y=2202.97559,z=85.4273224,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

At each floor, close CET and allow streaming, step outside the dance area and
walk back in. Choose Dance; let it animate for about5 seconds; press a movement
direction (W/A/S/D or the controller movement stick) to stop. Vanilla supplies
no separate Stop dancing prompt. Verify walking and HUD return. Walk outside/
back and repeat Dance/movement exit a second time.
Fully exit dancing before the next teleport. Test logger tracks native scene
requests/returns and workspot observations; counters alone do not prove Dance.

If a prompt is missing, while there run:
```lua
GetMod("PTFR_ClubDancing_Audit").Mark("no-prompt")
```
Saved availability0 intentionally keeps this package idle. Its exact cause may
need a local quest-state audit; do not set any availability/story facts to1.

After the route, with V standing and able to move:
```lua
GetMod("PTFR_ClubDancing_Audit").Mark("finished"); GetMod("PTFR_ClubDancing_Audit").Stop()
```

Quit without saving. Report which floors worked and any missing prompt, bad
animation, stuck controls or missing music. Logs are flushed JSONL files in
the PTFR_ClubDancing_Audit CET folder. Stop() only stops recording.
Save/reload and forced interruption are separate future checks, not part of
this first combined test. Atlantis memory dance floor is excluded.

Correction2026-09-26: the first instructions incorrectly requested a Stop
choice. The original scenes expose only Dance; node65 listens for MoveX/MoveY
and reaches cut132 and normal cleanup127. Missing Stop prompt alone is not an
exit defect. User reported no Stop prompt at Riot; movement exit remains
unconfirmed, so do not ask for the full four-club route before this is resolved.
