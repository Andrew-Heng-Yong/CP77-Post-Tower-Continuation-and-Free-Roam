# Northside medicstore 02: combined enable and respawn test

The one-site package is installed **idle**. Test only on a disposable post-Tower save. This is the medical counter beside the tested Northside foodshop; do not test medicstore 01 elsewhere.

If `Inspect()` says `combat/scene/workspot must be inactive`, the probe log distinguishes the three conditions. On the first attempt, combat and workspot were false but `in_scene=true`; the separate Northside foodshop and gunsmith opt-ins were both still `Enabled=1, Near=1` in that loaded session. To isolate the med test, leave at least 60 m from **both** earlier shops, wait until their owners depart, then run their own `Stop()` commands (not raw fact writes):

```lua
GetMod("PTFR_B0_Northside_Foodshop").Stop()
```

```lua
GetMod("PTFR_B0_Northside_Gunsmith").Stop()
```

Both must report `Stopped`; if either refuses, walk farther away and retry. In the first refusal screenshot, the logs still placed V around `(-1931.7,2742.3)`, only about 18 m from the food actor and 43 m from the gunsmith actor, so both native `Near` flags correctly remained 1. Leave the entire shop block (well over 60 m from **both** actor positions), not just the med counter, and wait several seconds before retrying. Return to the med counter, out of dialogue/menu, and resume step 2. Do not save this temporary isolation state. If med `Inspect()` still reports `in_scene=true`, stop and send the output; do not bypass the guard.

On the follow-up attempt both older `Stop()` calls succeeded, and med `Inspect` far away showed `in_scene=false`; the game then exited before the tester returned. These temporary Stop operations were not saved, so on the next load use a clean pre-vendor disposable save if available, or repeat the two Stops while far away **and continue in the same session** to the med counter.

1. Cold-load the save. Go to that med counter and wait five seconds. If needed, teleport nearby while not in a menu:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1931.0,y=2741.0,z=10.5,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
   ```

2. Before enabling, check whether the seller and Trade are still missing. Paste this **one** CET command; it inspects first and enables only if ready:

   ```lua
   local m=GetMod("PTFR_B0_Northside_Medicstore"); if not m then print("MED PROBE NOT LOADED") else local r=m.Inspect(); if r and r.ready then m.Enable() end end
   ```

   If it says `NOT READY` (especially `wat_nid_medicstore_02_default_on must be 1`) or `MED PROBE NOT LOADED`, send the output and stop; do not change a fact manually. Otherwise close CET, wait about ten seconds, check that one seller appears and physical Trade opens the medical inventory. Complete one cheap purchase if possible, then close the menu normally.

3. Leave at least 60 m and wait a few seconds. The probe logs native departure automatically; no observation command is needed. Return to the counter, check there is one seller, and reopen Trade. Close the menu normally.

4. Leave at least 60 m again, wait a few seconds, then run:

   ```lua
   GetMod("PTFR_B0_Northside_Medicstore").Stop()
   ```

   Quit without saving and report the seller, Trade, inventory, purchase, and return behavior. I will inspect the automatic `northside_medicstore_02_trace.jsonl` for native entry, first departure, re-entry, second departure, and clean Stop. If `Stop()` refuses, move farther away and retry once; do not force any fact. Do not teleport from inside the vendor menu.
