# R12 — idle animations and expanded local population

Cold-launch the game and load a disposable completed-Tower save. The doors
and four original pavement NPCs have already passed; no repeat door test.

Optional teleport to the same street:

```lua
Game.GetTeleportationFacility():Teleport(GetPlayer(), ToVector4{x=-1554.5, y=1184.0, z=16.6, w=1}, ToEulerAngles{roll=0, pitch=0, yaw=0})
```

Wait 15–20 seconds, then check:

1. Terry at approximately `-1551,1173`: smoking rather than an unassigned
   idle. Look at him briefly so the automatic trace records workspot state.
2. Indoor Zetatech guard: idle movement. Upstairs counter staff: tablet
   routine. Confirm one of each, without duplicate originals. Look at each.
3. Walk the local street from the Terry end toward the four accepted people
   and farther past the shop. The target is 27 additional ordinary residents
   (31 total local ambient entries), including a wheelchair occupant and
   people drinking, smoking or sitting. They are spread along the alley and
   nearby stairs, not all clustered around the original four.
4. If something floats, overlaps or remains motionless, report its location
   or a screenshot. Five source poses were replaced with independent idles;
   their alignment still needs this visual check.

No console activation command is needed. Diagnostics sample automatically.
Optional labelled snapshot: `GetMod("PTFR_Zetatech_Access_Audit").Inspect("r12-idles")`.
Readiness/request counts are not proof of visible animation. Keep the player
out of combat for the initial animation check; combat-interruption testing
can follow only after the population is observed. Terry's death remains
session-only, not persistent across reloads.

Quit without saving after this first check. Report Terry, guard, counter
staff and added street residents separately. If the game fails at startup,
close it and use the exact prepared R12 rollback, not any old R11 rollback.
