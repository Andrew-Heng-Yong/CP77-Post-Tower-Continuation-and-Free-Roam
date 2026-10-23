# R6 — one combined disposable check

Cold-launch with R6 installed and load a completed-Tower save made before
these shop opt-ins. Do not save this test. No q307 fact changes or direct
variant commands are needed.

1. While freely moving, teleport to the known safe point outside the clinic
   area, then start:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
   GetMod("PTFR_MistyViktor_World").Start()
   ```

   Close CET for at least two seconds, then:

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   ```

   Require Revision6, Registered1, Enabled1, Applied1. These are dispatch
   checks, not proof the assets are visible. If a guard fails, do not bypass it.

2. Walk back along supported public ground. In one loop, inspect the shop
   candles, original yellow police tape/body bags, and pedestrians at the
   previously reported crossing. Check the lighting and walking support too.
   Do not enter unsupported floors. The already-passed rear door needs only
   a regression glance; no service/mirror retest is required.

   Run `GetMod("PTFR_MistyViktor_World").Inspect()` once near the alley.
   CrowdRequests should have increased after the private area loaded. This
   confirms the guarded request ran, not that pedestrians obeyed it.

3. Continue to Bradbury & Buran, around (-1555.25,1246.65,19.08). Check the
   actual terminal exists, offers its normal interaction and opens the travel
   map. Merely having its map icon does not pass this check. Close the map and
   walk back once to see whether the changed props/crowd behavior persist.
   Record the combined visit:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("r6-local-route")
   ```

   The apparent wall gap is still unresolved; note it but do not expect a
   fabricated filler wall. The crowd change is a local exclusion, not a proven
   route fix for every kind of NPC. No Terry or ending actors should appear.

4. Freely moving again, use the safe teleport from step1. Then:

   ```lua
   GetMod("PTFR_MistyViktor_World").Stop()
   ```

   **Close CET and wait at least two seconds before the next commands.**

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   GetMod("PTFR_MistyViktor_World").Finish()
   ```

   Normal release should show Enabled0/Applied0/Releases1. If Applied is
   still1, wait briefly and Inspect before Finish; do not force facts.
   Stop disables the private crowd area and street/shell, and conditionally
   restores the known original door/sign/police/lighting state. Bradbury's ordinary
   terminal deliberately remains enabled. Quit without saving in every case.

Report just: candles, police props, terminal/menu, NPC crossing, and any new
lighting/support issue. No second unchanged direct candle-toggle test.
