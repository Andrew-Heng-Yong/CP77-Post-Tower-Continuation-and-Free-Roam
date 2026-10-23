# First ripperdoc + netrunner representative test

Use a disposable post-Tower save and do not save during this first test. The installed eight-site package is **idle**; no site is enabled automatically. Test Charter Hill ripperdoc (`rip_hil`, Nina) and Coastview netrunner (`net_cvi`) first. Their scene-marker coordinates are approximate teleport targets, not verified navmesh spawn points:

```lua
-- Charter Hill ripperdoc area
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-41.71,y=-53.52,z=8.2,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Coastview netrunner area
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1908.16,y=-1924.15,z=50.3,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

1. Before enabling, inspect **both** locations physically. If either service already has its seller and opens its menu, do not enable that site; report it. If a teleport lands in geometry, reload rather than saving.
2. Move to a safe, idle place more than 70 m from both sites. Close all vendor/dialogue menus; V must be out of combat, scenes, and workspots. Run `GetMod("PTFR_B0_RipNet_Eight").Inspect("rip_hil")` and `.Inspect("net_cvi")`. If both say READY, run `.Enable("rip_hil")` and `.Enable("net_cvi")`. Do not force a refused local gate.
3. Visit Charter Hill, open the **full ripperdoc service panel** (not just a prompt), exit it, leave more than 70 m, return and reopen it. Repeat the same two-visit cycle for the Coastview netrunner's Trade/inventory. Close menus before teleporting. Watch for duplicate actors or V getting stuck.
4. Outside both shop areas, run `GetMod("PTFR_B0_RipNet_Eight").Observe("after-two-representatives")`, then `.Disable("rip_hil")` and `.Disable("net_cvi")`. Both disables should succeed. Quit without saving.

Report one seller, menu contents, menu exit, and return-menu result for each. The durable trace is `ripnet_eight_trace.jsonl` under the installed CET mod folder. Native entries/exits, Far clears/rearms, unchanged story facts, and clean shutdown will be reviewed before expanding to the other six sites. Cyberware profile enforcement is outside this development test; do not interpret menu access as proof of a release-safe profile.
