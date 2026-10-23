# R11 Zetatech correction — one disposable visit

Cold-launch a disposable completed-Tower save after installation. This check
covers the three doors, upstairs counter staff, Terry, and four nearby ambient
street people. The installed receipt determines the package version.

The earlier teleport landed inside the shop at the guard's workspot. This
point is on the street near the storefront and Terry:

```lua
Game.GetTeleportationFacility():Teleport(GetPlayer(), ToVector4{x=-1554.5, y=1184.0, z=16.6, w=1}, ToEulerAngles{roll=0, pitch=0, yaw=0})
```

Wait about 15 seconds, then check:

1. Terry near `-1551.20, 1172.57, 16.31`, and four ambient people near
   `-1558, 1193` through `-1555, 1189`. Report visible idle animations.
2. Upstairs counter staff present; the Zetatech guard's indoor position is
   intentional. Viktor downstairs is a separate, unchanged service.
3. Front door at the original reported position: closed at rest, normal
   interaction, opens, then closes. Repeat for the inner door.
4. The outer rear door opens again. This is the previously working access
   restored from R2/R7.
5. If testing Terry's combat, do it after the doors and population check.
   Only his private clone lacks the original Invulnerable tag; actual damage,
   reactions and death still require this live check. His lifecycle is
   session-only and is not a claim of persistent death across reloads.

Read-only diagnostics automatically record while near the shop. Looking at
each door during the test lets the log capture the actual device state.
An optional labelled sample is:

```lua
GetMod("PTFR_Zetatech_Access_Audit").Inspect("after-door-check")
```

Expected facts include `PTFRMV_AccessRevision=11`,
`PTFRMV11_Registered=1`, each `FrontReady/InnerReady/RearReady=1` while its
door is loaded, and `PTFRMV11_StreetReady=1` while the pavement spots load.
These are dispatch/readiness diagnostics, not substitutes for visible results.

Quit without saving and report each door separately, counter staff, Terry,
and whether the four pavement NPCs appeared and animated.
