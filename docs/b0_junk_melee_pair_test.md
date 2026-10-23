# Badlands junk + melee paired disposable test

Use a disposable post-Tower free-roam save. The package is installed but **idle** until Start. It is not part of the normal vendor batch. Do not save during this first run.

Approximate teleport targets derived from vanilla scene markers (not navmesh-certified spawn points):

```lua
-- Junk seller area
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-986.82,y=-4418.16,z=65.3,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Melee seller area
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=138.25,y=-4671.50,z=56.1,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})

-- Distant staging point previously reached safely by the tester (Little China)
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1519.8586,y=1700.9325,z=18.3175,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Close CET and allow the district to stream before judging a baseline or Trade prompt. If a teleport lands inside geometry, reload the disposable save; do not save there. Never teleport while Trade or dialogue is open.

1. Teleport to junk and then melee for **pre-opt-in baseline**; inspect each counter. **If either already works, do not Start:** the paired test could create a duplicate. Report which shop works instead.
2. Teleport to the distant staging point. Finish any conversation, Trade panel, combat, or workspot. Run `GetMod("PTFR_B0_JunkMelee_Pair").Inspect()`. If it refuses, send the reason and do not force facts. If it says READY, run `GetMod("PTFR_B0_JunkMelee_Pair").Start()` once.
3. Teleport to junk, wait for streaming, find the seller, and open Trade/inventory. Close Trade. Teleport to melee; this is junk's departure and melee's first visit. Open and close melee Trade. Teleport back to junk and reopen Trade (junk respawn). Then teleport back to melee and reopen Trade (melee respawn). Wait a few seconds at each counter; verify one seller, not duplicates.
4. Close Trade, teleport to staging, wait a few seconds, then run `GetMod("PTFR_B0_JunkMelee_Pair").Observe("after-both-return-visits")` and `GetMod("PTFR_B0_JunkMelee_Pair").Stop()`. Stop should report success. Quit without saving.

Report for each shop: first seller count, first Trade/inventory, return seller count, return Trade/inventory, and any fault. The durable CET trace is `junk_melee_pair_trace.jsonl`; inspect native Near/Departed and Far transitions before calling this live result passed. A prompt alone is not success.
