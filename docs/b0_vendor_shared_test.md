# One combined four-vendor and cold-reload test

This is one opt-in disposable-save run for the **already tested** Northside gun, food, and med shops plus Little China clothing. The old one-shop packages remain available with shared mode off. Do not use a master save or change any vanilla fact.

1. Cold-load a disposable post-Tower save while V is idle **more than 70 m from all four shops** (H10 is suitable). Do not stand in a menu, dialogue, combat, or workspot. Run just one start command:

   ```lua
   GetMod("PTFR_B0_VendorBatch").Start()
   ```

   Wait about three seconds for `[PTFR VENDOR BATCH] ARMED`. A `NOT READY`, `ACK_TIMEOUT`, or `ARM_ERROR` is a stop condition: send the output; do not set facts manually. Start may accept a saved old one-shop `Enabled=1` only if its native `Near=0` and V is safely outside all shops.

2. Visit the Northside gunsmith, food counter, and med counter in one pass. At each, check the intended seller and physical Trade, open and close the correct inventory. Make one cheap ordinary purchase at any one shop (no unique item is needed). Then leave the **whole Northside shop cluster** by more than 70 m from each counter, wait five seconds, return, and reopen Trade at all three. Report any duplicate-looking seller or wrong inventory.

3. Visit Little China clothing. Open and close Trade, leave over 70 m, wait five seconds, return, and reopen Trade. Do not teleport while any shop menu is open. A quick Wilson or kiosk check can be added on the same trip as an unaffected control, but it is not required for the four-shop success criterion.

4. If all four shops worked, move more than 70 m from every shop (H10 is suitable), wait five seconds, and run this read-only checkpoint:

   ```lua
   local s=GetMod("PTFR_B0_VendorBatch").Observe("outside-before-reload"); print("mode",s.shared.mode,"combat",s.combat,"scene",s.scene,"workspot",s.workspot)
   ```

   Confirm all four report `N=0 F=1 E=1` **and** V reports `combat=false, scene=false, workspot=false`. If any does not, do **not** save: move farther away, wait, and retry once; send the output if it still differs. Make a **new disposable manual save** in this outside/idle state, then fully quit the game. Do not overwrite the master save. The first version of ManualSave-17 was made while `scene=true` at the Riot mirror; a later overwrite from the Riot fast-travel point now meets the idle checkpoint in the trace, but still requires a cold-load test.

5. Cold-launch and load that new disposable save. Do **not** run `Start()` again. Check Trade and the correct inventory at all three Northside shops and Little China clothing. Look for duplicate or absent sellers. This tests shared-mode persistence and all four owners after reload without another arm command.

6. Move more than 70 m from every shop, wait five seconds, then run the only stop command:

   ```lua
   GetMod("PTFR_B0_VendorBatch").Stop()
   ```

   It must say `Stopped all four opt-ins`. If it refuses, move farther from the named shop and retry. Quit **without saving again**. Report which shops had one seller, correct Trade inventory, reopened Trade after departure, and still worked after cold reload. The batch and existing one-shop logs automatically record redscript-driven `Far`, native Near/Departed/rearm, Stop, and shutdown. The one `Observe` checkpoint is the only extra CET command.

If a shop fails, close its menu, leave all vendor areas, use the same `Stop()` command, and quit without saving; skip the new save and reload. Do not enable individual shop modules during this combined trial. Keep the outside/idle test save disposable: it intentionally contains armed opt-ins and must not become the main play save.
