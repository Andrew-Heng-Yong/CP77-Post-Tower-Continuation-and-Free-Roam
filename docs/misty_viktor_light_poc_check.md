# One private lamp — disposable visibility test

This is **not the hotel-neon/police-glow repair**. It adds one copied yellow
point light at a separate pavement location. There is no physical lamp model.
The original lighting and R7 restoration are unchanged. No quests, dialogue,
actors, workspots, collision or player restrictions are changed.

Use a disposable completed-Tower save and **do not save this test**. Launch
the game after the separate POC package is installed; do not reload CET mods
mid-session to substitute for a cold launch. The test defaults disabled.

## 1. Reach the test spot after dark

Use normal time-skip if necessary: the copied vanilla lamp is only25 lumens,
so daylight can conceal the difference. The script does not change time.
It is at the former wall-gap observation point, near the two police trucks.
The wall-gap report was withdrawn; no wall has been added or removed.

Optional TP to the previously reported standing location, slightly raised:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1570.2422,y=1210.5839,z=17.15,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Only use this if the street/floor is visibly present. This is a previously
reported user position, not a new engine-verified safe landing. Look at the
pavement where you arrived. Keep V within 2m of x=-1570.2422, y=1210.5839
for Start, Inspect, Hide and Show; do not walk toward the original police
glow at x=-1552.9783, y=1171.5599 during this test. The private light center
is z17.544 and its illumination radius is only 3m. Native Ready can still
read 1 outside this radius, so Ready alone cannot validate visibility.

## 2. Start, then check native readiness

```lua
GetMod("PTFR_MistyViktor_Light_POC").Start()
```

Close CET, wait two seconds, then:

```lua
GetMod("PTFR_MistyViktor_Light_POC").Inspect()
```

Expect Revision1, Registered1, Enabled1, Applied1 and Ready1. ShowRequests
should be at least1. **Ready means the reference resolved and a command was
dispatched, not that illumination is visibly correct.** The lamp has no mesh.

If Ready stays0 near the test point, allow up to20seconds once. Then Inspect,
Stop and report the output; do not repeatedly Start, force facts or switch
original variants. If Ready1 but no visible difference, also report that
separately; do not call it a successful visibility test from the counters.

## 3. Compare Hide and Show from the same view

```lua
GetMod("PTFR_MistyViktor_Light_POC").Hide()
```

Close CET and wait two seconds, then Inspect again. HideRequests must increase
by one while V remains at the test spot. Does the extra yellow pavement glow
disappear or clearly diminish? Other nearby lights should remain unchanged.

```lua
GetMod("PTFR_MistyViktor_Light_POC").Show()
```

Close CET and wait two seconds, then Inspect again. ShowRequests must increase
by one. Does the same glow return? Then capture:

```lua
GetMod("PTFR_MistyViktor_Light_POC").Mark("hide-show-observed")
```

If both visual transitions work, one short streaming check is useful: leave
the area, Inspect, then return to the same spot. The native controller should
wait while its node is absent and reapply the requested state on return. A
trip without observed absence is **not** proof of unload/rearm.

Optional known outside point (~230m from the lamp):

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
```

Return with the test-spot TP above. Do not repeat the already-passed R7 prop,
door, terminal, candle or pedestrian checks.

## 4. Stop and quit without saving

Stop works from any distance; this private light supplies no floor/collision.

```lua
GetMod("PTFR_MistyViktor_Light_POC").Stop()
```

Wait two seconds, then Inspect. Expect Enabled0, Applied0, Ready0 and
Releases incremented. Visually confirm the extra glow has gone. Finish only
stops logging; it is not a substitute for Stop.

```lua
GetMod("PTFR_MistyViktor_Light_POC").Finish()
```

Quit **without saving**. Report: Ready result, initial glow, Hide effect,
Show effect, any observed streaming absence/return, and disappearance on Stop.
The log records private dispatch/state plus unchanged sampled Tower guards;
it cannot measure rendered brightness. No original-light patch follows
automatically from an offline test or a successful request counter.
