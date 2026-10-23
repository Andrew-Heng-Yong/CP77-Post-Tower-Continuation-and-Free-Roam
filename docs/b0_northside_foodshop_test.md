# Northside foodshop 01 opt-in test

2026-09-24. One-shop candidate installed idle. Its seller was absent on the disposable post-Tower baseline with `wat_nid_foodshop_01_default_on=1`; see [assessment](../research/b0_northside_foodshop/assessment.md). The owner remains inactive until `Enable()` is called. The first live test reached native spawn; a second disposable test logged native departure/re-entry/departure and the tester confirmed Trade reopened on return. The procedure below remains the full validation reference; purchase and cold save/reload have not been reported.

1. Cold-launch the game and load the same disposable post-Tower save. Go to the Northside food counter, or teleport near it:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1912.2,y=2737.2,z=11.0,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
   ```

2. Close CET, approach the counter, wait five seconds, and verify the seller/Trade baseline again. If it is still missing, run:

   ```lua
   GetMod("PTFR_B0_Northside_Foodshop").Inspect()
   ```

   Only after **READY**, run as a separate command:

   ```lua
   GetMod("PTFR_B0_Northside_Foodshop").Enable()
   ```

   If the module is nil or Inspect/Enable refuses, send its output. Do not set any fact manually.

3. Close CET; wait about ten seconds. Check for one seller, physical Trade, the food inventory, and a completed small purchase. Close the menu normally.
4. Leave at least 60 m and wait a few seconds. Run:

   ```lua
   GetMod("PTFR_B0_Northside_Foodshop").Observe("first-outside")
   ```

   Desired: `Far=1`, `ExitWatchArmed=1`, `DespawnActionOut=1`, `Departed=1`, `Near=0`.
5. Return and verify one seller and that Trade opens again. Leave at least 60 m again, then run these separately:

   ```lua
   GetMod("PTFR_B0_Northside_Foodshop").Observe("second-outside")
   ```

   ```lua
   GetMod("PTFR_B0_Northside_Foodshop").Stop()
   ```

   Quit without saving. Tell me whether the seller, Trade, inventory, purchase, and return visit worked. The logger flushes `northside_foodshop_trace.jsonl`; we will read its native stages afterward.

If seller or Trade fails after Enable, take one `Observe("failed-at-counter")` reading, move outside the 50 m area, run Stop only once `Near=0`, and quit without saving. Do not teleport while the vendor menu is open. No other merchant is enabled by this test.
