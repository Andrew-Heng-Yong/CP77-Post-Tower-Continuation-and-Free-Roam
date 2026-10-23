# Five remaining simple regional ripperdocs — combined disposable run

The Charter Hill ripperdoc and Coastview netrunner passed two visits each. These five ripperdocs are the other locally eligible sites on the same post-Tower fixture: `rip_dtn`, `rip_wwd`, `rip_arr`, `rip_rcr`, `rip_jpn`. `net_rey` is **not** part of this run because its original local gate was 0; do not force it.

Use a disposable save; do not save during the run. The following are vanilla scene-marker coordinates plus approximately one metre of height, not certified teleport landing spots. Close every dialogue/service menu before teleporting. Reload if a landing is inside geometry.

```lua
-- Downtown ripperdoc
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-2412.16,y=395.01,z=12.7,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- West Wind Estate ripperdoc
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-2606.36,y=-2501.32,z=18.9,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Arroyo ripperdoc
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1066.00,y=-1270.50,z=12.5,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Rancho Coronado ripperdoc
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=585.67,y=-2180.27,z=43.4,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Japantown ripperdoc
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-707.34,y=868.74,z=12.8,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Distant staging point observed idle in the prior two-type test
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-506.40,y=-760.19,z=7.42,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

1. Visit all five **before enabling**. Record which already have a seller and a working cyberware service panel. **Do not enable already-working sites**: duplication is possible. Note any inaccessible or unsafe location.
2. Teleport to the distant staging point and confirm V is idle. It was observed out of combat, scene, and workspot in the prior test, more than 70 m from all five. Run `GetMod("PTFR_B0_RipNet_Eight").Inspect()` once to see all local gates. For each physically missing site whose Inspect result is READY, run one matching command below. If a local gate is 0 or V is in a scene/combat/workspot, do not force the fact.

```lua
GetMod("PTFR_B0_RipNet_Eight").Enable("rip_dtn")
GetMod("PTFR_B0_RipNet_Eight").Enable("rip_wwd")
GetMod("PTFR_B0_RipNet_Eight").Enable("rip_arr")
GetMod("PTFR_B0_RipNet_Eight").Enable("rip_rcr")
GetMod("PTFR_B0_RipNet_Eight").Enable("rip_jpn")
```

3. Visit only the sites you enabled, in the order above. At each, verify one intended seller, open the full ripperdoc service panel, then close it. Repeat the same route once more and reopen each menu. Each teleport to a different district exceeds the 55 m exit threshold. Wait a few seconds for streaming and native departure/arrival at each stop. Do not buy or equip cyberware on this first pass; restriction-profile behavior is unvalidated.
4. Teleport back to staging and wait for each native exit. Run `GetMod("PTFR_B0_RipNet_Eight").Observe("after-five-ripperdocs")`, then run the matching Disable commands for **only** the sites you enabled:

```lua
GetMod("PTFR_B0_RipNet_Eight").Disable("rip_dtn")
GetMod("PTFR_B0_RipNet_Eight").Disable("rip_wwd")
GetMod("PTFR_B0_RipNet_Eight").Disable("rip_arr")
GetMod("PTFR_B0_RipNet_Eight").Disable("rip_rcr")
GetMod("PTFR_B0_RipNet_Eight").Disable("rip_jpn")
```

Quit without saving. Report which sites were missing and enabled; at each, whether a single seller, full menu, exit, and return menu worked. The durable `ripnet_eight_trace.jsonl` will show native entries/exits and Far rearm per site. A prompt without a full menu is not a pass.
