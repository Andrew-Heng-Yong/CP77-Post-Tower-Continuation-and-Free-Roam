# Yagami Market / Corpo Plaza food vendor 02

Installed automatic candidate on top of Baseline R1 + the ordinary-bar add-on.
No Start/Enable/Arm command is needed. Vendor 01 and other existing restorations
are unchanged. No ending replay is needed.

1. Cold-launch and load a disposable copy/slot of your known-working post-Tower
   save. Wait up to ten seconds in ordinary unmounted gameplay, outside menus,
   combat and interactions, for safe automatic activation.
2. Visit the same Yagami Market counter. Check that one actual merchant appears
   behind the counter, talk if available, and open the actual Trade inventory.
   The ambient NPC leaning on the customer side is not the merchant count.
3. Close Trade/dialogue normally. Walk at least **100m away**, wait five seconds,
   then return. Confirm the seller and Trade work again, without overlapping
   merchant models. Do not teleport during dialogue or Trade.
4. Walk 100m away again, wait five seconds, and optionally run:

```lua
GetMod("PTFR_B0_CPZFood02").Observe("yagami-finished")
```

5. Quit **without saving**, and report whether both visits worked. No Stop is
   needed; logging starts automatically. `Finish()` stops only this logger.

Expected evidence: native Entries/Exits increase by at least 2/2, with Near=0
after final departure. Extra crossings can legitimately increase them further.
Counters alone do not establish successful Trade. Cold save/reload remains
unverified by this no-save test.

## Optional teleport back to your recorded counter position

This is the exact position you supplied while standing at Yagami Market, not
the previously unresolved scene marker. A teleport to it has not separately
been tested. Use only when V is free of all interactions:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1541.2741699219,y=-304.61795043945,z=-4.4756546020508,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

If no seller or prompt appears after ten seconds, run:

```lua
GetMod("PTFR_B0_CPZFood02").Observe("yagami-no-service")
```

Send the output; do not force `default_on`, `met` or Tower facts. Logs are in
the game's `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_B0_CPZFood02/` folder,
named `yagami_food02_*.jsonl`, flushed every two seconds and on manual marks.
