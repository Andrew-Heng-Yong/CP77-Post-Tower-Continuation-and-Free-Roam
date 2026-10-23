# One combined world-interaction check

## Current coaster-only crash check — revision5

Do NOT retest revision4: first Raise arms was silent; the next press crashed.
Revision5 restores both native completion/start callback sockets and disables
idle-only mode for the gesture. Verify deployment in
coaster_repeat_gesture/install_receipt.json before this ONE-ride check.

The candidate uses native
mounted-seat workspot playback instead of the two cinematic cheer overlays;
the optional shout is omitted. No need to repeat the whole route below.

Cold-launch and load the same ORIGINAL disposable fixture (whose gate was0,
not a save of the temporary unlocked/crashed session). Start logging and
temporarily enable that one gate:

```lua
GetMod("PTFR_WorldInteractions_Audit").Start()
Game.GetQuestsSystem():SetFactStr("mq006_enable_repeatable_rollercoaster", 1)
GetMod("PTFR_WorldInteractions_Audit").Mark("coaster-r5-before")
```

Only while freely standing before the scene, teleport near the platform:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-2390.45,y=-1950.31,z=18.0,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Close CET. Get in, select Hands up on TWO separate offers, allowing the first
action to finish before selecting it again. Let the ride finish, and use Exit.
Confirm both visible gestures, no crash, no Johnny and free movement.
One ride is enough for this crash-isolation check. After normal Exit:

```lua
Game.GetQuestsSystem():SetFactStr("mq006_enable_repeatable_rollercoaster", 0)
GetMod("PTFR_WorldInteractions_Audit").Mark("coaster-r5-after-exit")
GetMod("PTFR_WorldInteractions_Audit").Stop()
```

Quit without saving. On failure, stop logging if possible and quit without
saving; do not force additional facts, call Exit through scripts or teleport
mid-scene. `hands=2/2` means selections/requests and Work Started, NOT proof of
gesture completion. A normal Return plus actual visible gesture/free movement
is needed. Repeat/reload coverage is separate and remains unproven.

## Original combined route

Three automatic candidates are installed: radio scheduling, earned repeatable
coaster, outcome-driven memorials. This is not completion of the whole table.
No Arm/Enable command is required. Other restored services remain unchanged.

Coaster revision1 failed after a temporary gate unlock. Revision2 restores its
omitted native cart activation and hides the colocated broken-cart clue. Check
`research/b0_world_interactions/coaster_fix/install_receipt.json` for deployment.
The read-only logger now prints setup/registered as well as requests/returns;
setup1 is an issued setup action, not proof the cart actually exists.
For the user-authorized disposable gate0 test ONLY: start logging, set
`mq006_enable_repeatable_rollercoaster` to1, and mark the change. Do not change
other facts. After two normal exits restore its recorded original0, stop
logging, and quit without saving. On any failure stop and quit without saving
instead of forcing cleanup or repair facts. Radio/memorial need not be retested
just to validate this coaster-only repair.

1. Cold-launch, load a disposable post-Tower sandbox save with the normal
   baseline already active. Do not load a pre-Tower fixture or save afterward.
2. Start the read-only durable logger:

```lua
GetMod("PTFR_WorldInteractions_Audit").Start()
GetMod("PTFR_WorldInteractions_Audit").Mark("outside-before-route")
```

3. Try ordinary pocket/vehicle radio: choose a station, listen, change once,
   turn off, then on. Report whether music/audio actually plays. A fact value
   alone does not prove audible playback; no specific rare news item must play.

```lua
GetMod("PTFR_WorldInteractions_Audit").Mark("radio-checked")
```

4. Read the printed `coaster gate`. If0, the original earned repeatable gate
   is closed: do not force it or run mq006. Report gated and skip the ride.
   If1+, visit the Pacifica coaster platform. Its compiled cart origin is
   -2393.4502,-1950.30566,17.9441681. A CET development teleport near the cart
   (landing spot is inferred from the cart, not yet live-verified) is:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-2390.45,y=-1950.31,z=18.0,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

   Close CET. Find Get in, ride to the end, use Exit, confirm free movement.
   Hands up is optional. There should be one usable cart and no Johnny/party
   actors. Walk away/back and repeat once, fully exiting each time. Never
   teleport while mounted or during any scene. If prompt/ride/exit fails,
   stop the test and quit without saving; do not force ride-finished facts.

```lua
GetMod("PTFR_WorldInteractions_Audit").Mark("coaster-two-normal-exits")
```

5. Visit the Columbarium via its normal map/fast-travel route. Check memorial
   displays appropriate to already-dead NPCs, and confirm no Johnny appears
   when scanning. Registered1 is not proof displays changed; report what is
   actually visible. No new death, loot or story facts should be set manually.

```lua
GetMod("PTFR_WorldInteractions_Audit").Mark("memorial-checked")
GetMod("PTFR_WorldInteractions_Audit").Stop()
```

6. Quit without saving. Report radio audio, coaster gate and both complete
   rides/exits (or precise first failure), and visible memorials/no Johnny.
   I will read `world_audit_*.jsonl` in the new CET logger folder. Requests/
   Returns are scene-launch/normal-exit counts, not direct ride-completion
   proof; combine them with actual action reports.

Logging is the only one-second CET job and runs only after Start. Production
restoration is native. Stop stops logging only, not the installed adapters.
No retest of already-passed dancing, mirrors, vendors or H10 TV is requested.
