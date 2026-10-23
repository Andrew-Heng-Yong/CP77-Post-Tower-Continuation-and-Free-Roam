# R7 — construction props and parked trucks

Load a disposable completed-Tower save from before the clinic opt-in was
enabled. This is not the active-ending reference save. Cold-launch after
installation; do not save this test.

R6's candles, police-prop removal, pedestrian result and terminal are accepted. No
repeat of those basic checks is needed. **R7 does not fix the pink neon or
residual police glow.** Their exact sources are identified, but narrow
conditional control is not yet proven. No guessed wall is added.

## Start outside the area

While V is free to move:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
GetMod("PTFR_MistyViktor_World").Start()
```

Close CET, wait two seconds, then:

```lua
GetMod("PTFR_MistyViktor_World").Inspect()
```

Require Revision7, Registered1, Enabled1, Applied1. If a guard fails, stop
and report it; do not force facts. Counters do not prove visible streaming.

## One combined loop

Walk back to the street and check:

1. Near(-1561.04,1206.60,16.59): nine cement sacks, pallet and pallet jack.
2. Near(-1543.04,1182.22,17.05), beside the hotel strips: seven cement sacks
   on the already-existing pallet. No duplicate pallet or floating objects.
3. Behind the barricades near(-1570.75,1217.30,17.02): exactly two NCPD
   armored trucks matching reference image1. They must remain parked. Report
   any unexpected occupants, driving, aggression, overlap or disappearance.

The trucks are native vehicle objects, not inert meshes. First test their
presence and lifecycle without entering, attacking or moving them. No quest
cast or ending scene should start. Look at ordinary support/collision when
walking near the new props; do not enter visibly unsupported ground.

Leave along the public street, return once and check the piles/trucks are
still correct, with no duplicates. Record the result:

```lua
GetMod("PTFR_MistyViktor_World").Mark("r7-details-return")
```

No terminal, full travel or other vendor/mirror retest is requested.

## Release and finish

Use the safe outside teleport from the first block again, then:

```lua
GetMod("PTFR_MistyViktor_World").Stop()
```

Close CET for at least two seconds, then:

```lua
GetMod("PTFR_MistyViktor_World").Inspect()
```

Expected after the first run: Enabled0, Applied0, Releases1. If still Applied1,
wait briefly and Inspect; do not force facts. For the truck teardown check,
approach only on supported public ground and confirm the two private trucks
and added piles are absent. Do not enter the released private shop/street
geometry. Bradbury's ordinary terminal deliberately stays restored.

```lua
GetMod("PTFR_MistyViktor_World").Mark("r7-details-release")
GetMod("PTFR_MistyViktor_World").Finish()
```

Quit without saving. Report: both piles, two parked trucks, return/no
duplicates, removal on Stop, and any unexpected behavior. If anything is
unsafe or stuck, abandon the route and quit without saving.
