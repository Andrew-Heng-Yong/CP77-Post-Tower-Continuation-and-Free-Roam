# Northside gunsmith opt-in test

2026-09-24. **First disposable run passed.** The installed one-site archive, ArchiveXL registration, and CET probe produced one seller, dialogue, Trade/menu, a completed purchase, and reopened Trade on return. The log records three native entries and three departures; Stop and shutdown completed. The tester quit without saving. The commands below remain a reproducible procedure, not a requirement to repeat the passed run. [Evidence and installation receipt](../research/b0_northside_gunsmith/assessment.md).

The tester's baseline at the shop was: no seller, no Trade; `wat_nid_gunsmith_01_default_on=1`, `q307_done=1`. No mod command was run during that baseline visit. In the live run, an initial Inspect/Enable attempt outside the 20 m counter radius refused safely; Enable succeeded after moving closer.

1. Cold-launch the game and load the disposable post-Tower save. Go to the Northside gun shop. If needed, teleport near its counter:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1888.5,y=2727.5,z=7.6,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
   ```

2. Close CET, stand near the counter, and wait at least five seconds. If seller and Trade already work, do not enable the candidate; report that baseline change. Otherwise run this as one CET command:

   ```lua
   GetMod("PTFR_B0_Northside_Gunsmith").Inspect()
   ```

   Only if the output says **READY**, run a second, separate command:

   ```lua
   GetMod("PTFR_B0_Northside_Gunsmith").Enable()
   ```

   If `GetMod` is nil or Inspect refuses, do not set any fact manually. Send the output.

3. Close CET and wait about ten seconds. Check for one gunsmith, physical Trade, and the actual weapon menu. Close the menu normally. A low-cost purchase on this disposable save is useful if convenient; do not save it.
4. Leave the shop area by at least 60 m, wait a few seconds, then run:

   ```lua
   GetMod("PTFR_B0_Northside_Gunsmith").Observe("first-outside")
   ```

   Desired output: `Far=1`, `ExitWatchArmed=1`, `DespawnActionOut=1`, `Departed=1`, `Near=0`. Do not force these markers.
5. Return to the counter and verify one seller, Trade, and menu again. Run:

   ```lua
   GetMod("PTFR_B0_Northside_Gunsmith").Observe("return")
   ```

6. Leave the area by at least 60 m again, wait, and run these separately:

   ```lua
   GetMod("PTFR_B0_Northside_Gunsmith").Observe("second-outside")
   ```

   ```lua
   GetMod("PTFR_B0_Northside_Gunsmith").Stop()
   ```

   Quit without saving. Report whether Trade worked on both visits and whether a purchase completed. The logger flushes `northside_gunsmith_trace.jsonl` during the run; we will inspect its native stages afterward.

If seller or Trade fails after Enable, make one `Observe("failed-at-counter")` reading, leave the area, use `Stop()` only when `Near=0`, and quit without saving. Do not teleport with the menu open. The test is one site only; it does not authorize automatic restoration of other vendors.
