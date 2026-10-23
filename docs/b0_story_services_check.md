# S3 combined story-service check

Installed automatically: **Fred (H10), Cassius (Northside), Charles (Kabuki),
Pepe (El Coyote)**. No Arm/Enable command. Not all remaining story vendors.
Original service availability still applies: a zero vanilla gate is not fixed
by this package and must not be forced to one.

1. Cold-launch; load your disposable post-Tower save with the working baseline.
   Stand idle outside an interaction for about five seconds.
2. Visit Fred → Cassius → Charles → Pepe. At each: open the actual Trade/ripper
   menu, close it, and try available ordinary conversation. For Pepe optionally
   drink, but finish drinking and get up before travelling.
3. Repeat the same route once. Travelling between these separated sites also
   tests native departure/return without four separate run-away tests.
4. Confirm menus reopen, V is not stuck, and no duplicate main vendor appears.
   Cassius's assistant/kid are expected, not duplicate Cassius instances.
5. Exit all interaction menus, run this optional read-only summary, then quit
   without saving the first candidate run:

```lua
GetMod("PTFR_B0_StoryServices").Observe("two-route-finished")
```

Tell me which of the four worked or failed. Logging starts automatically on
game launch; no logging commands are required. Full facts/position are sampled
to `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_B0_StoryServices/story_services_*.tsv`.
These samples and native counters do not prove that a menu opened; your report
supplies that evidence. They also do not establish cold-save persistence.

## Optional teleport shortcuts

These are exact compiled vanilla scene markers from `marker_evidence.json`
(base and EP1 agree), with a small upward offset. **Not live-verified clear
landing spots.** Prefer normal map travel. Use only while idle, never inside
dialogue, menus, drinking or ripper animations. Close CET and walk to the vendor.
If a landing clips geometry, reload the disposable save; do not keep
teleporting while interacting.

Fred, H10:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1435.51013,y=1329.57983,z=119.48,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Cassius, Northside:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1696.19092,y=2380.32153,z=18.60,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Charles, Kabuki:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1240.69006,y=1945.66016,z=8.47,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Pepe, El Coyote:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1256.16101,y=-1000.92426,z=12.42,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Fred's fight-initiation choices and Charles's gig-confrontation choice are
deliberately excluded from these service copies. Other original dialogue and
outcome conditions are retained. This test does not restore their quests.
Claire, Zane, H10, mirrors and the earlier vendors are unchanged.
