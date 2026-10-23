# Ordinary bars — one combined check

Four ordinary bar owners are installed automatically on top of Baseline R1:
Corpo Plaza (`corpo_bar`), Arroyo (`arroyo_bar`), Northside (`northside_bar`),
and Charter Hill (`charter_bar`). This is a candidate pending in-game checks.
Story-linked bartenders and the previously restored systems are unchanged.

## Start

Load a **disposable post-Tower save that already works with the installed mod**.
No ending replay, Start, Arm, Enable or Reload All Mods command is needed.
Allow up to ten seconds in ordinary, unmounted gameplay after loading. The
original local shop gates remain authoritative; a locked bar is not forced open.
Logging starts automatically and flushes every two seconds.

## One route, including return checks

At each of the four bars:

1. Check the bartender and open the actual Trade inventory; close it normally.
   Try any available ordinary dialogue.
2. Use the bar's drinking/sitting option. Take a sip, then use its normal
   leave/stand-up option. Confirm V can walk and turn normally and the drink
   prop/interaction is not stuck. Choices still follow vanilla eligibility.
3. **Walk at least 100m away**, wait five seconds, then return. Check Trade
   and the drink→stand-up sequence again; look for overlapping bartenders.
4. Leave at least 100m and wait five seconds before the next site.

Do not teleport during dialogue, Trade, sitting or drinking. If a drink prop
is missing, the player is stuck, or an expected choice is absent, stop that
site's test and record what happened; do not force its vanilla facts.

After the route, while outside the bars, one optional read-only command gives
a concise state summary and adds a durable mark:

```lua
GetMod("PTFR_B0_OrdinaryBars").Observe("bars-finished")
```

Quit **without saving**. Tell me which bars passed/failed. No Stop command is
required: the logger cannot disable services or write facts. `Finish()` only
closes this logger if you want to stop recording before quitting.

Expected log evidence: each visited site's native Entries/Exits increases by
at least 2/2, Near returns to 0 after departure, and its drinking flag clears
after standing up. Extra boundary crossings can increase counters further.
Physical menu/drinking success still requires your observation. A returned
seller alone does not prove despawn/rearm. Cold save/reload is a separate
unverified property, not claimed from this disposable test.

## Locations / optional experimental teleports

Normal travel to the local bar is preferred. These are **extracted scene
anchors, not verified safe player landing points**. They may place V behind
the counter or in an unexpected spot; following the Chang experience, they
are not labeled verified teleports. Use only on a disposable save, outside
all interactions. If the landing is wrong, reload instead of saving there.

Corpo Plaza:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1521.81897,y=-326.054718,z=-4.51928806,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Arroyo:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-723.739014,y=-997.623169,z=7.71278858,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Northside (elevated interior; not the previously tested Northside food stall):

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1714.08936,y=2223.50317,z=87.2705765,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Charter Hill:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-258.517578,y=-57.5673828,z=1.66550803,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Logs: `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_B0_OrdinaryBars/ordinary_bars_*.jsonl`
inside the game directory. They record Tower/local gates, native lifecycle
counters, drinking flags, scene/workspot state and available runtime counters.
