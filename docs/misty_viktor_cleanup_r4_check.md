# R4 clinic street/interior overlap — disposable opt-in check

R4 remains opt-in and is not proof of a finished street scene. Use an unmodified
completed-Tower disposable save. Do not save this test. The native action hides
the original Misty interior variant, following the exact vanilla q307 cleanup
action; it does not change q307 facts or restore ending actors. The 24
police-specific placements removed here came from our *private copied* street
layer. The original world may still own other police dressing.

1. Load the save while freely moving. At the safe point outside the 80 m clinic
   area, arm the controller:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
   GetMod("PTFR_MistyViktor_World").Start()
   ```

2. Close CET, wait two seconds, and run:

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   ```

   Require Revision 4, Registered 1, Enabled 1 and Applied 1 before entering.
   These are dispatch indicators, not proof of streaming or collision.

3. At the Zetatech counter around `(-1546.18,1192.93,16.26)`, verify the old
   candle cluster is absent while the Zetatech floor, counter and exits remain
   physically usable. Do not proceed if the floor or doors are missing. Record:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("r4-candles-and-interior")
   ```

4. From a safe path, look at the NCPD tape and signage near the street and the
   alleged wall gap `(-1570.24,1210.58,17.0)`. Note separately whether police
   dressing remains, whether the gap remains, and whether NPCs still cross
   solid art near `(-1544.05,1174.82,17.17)`. Do not treat this R4 test as a
   wall or navigation fix. Do not shoot NPCs or force a fight in this pass.

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("r4-police-wall-nav")
   ```

5. Leave the 80 m clinic area while V moves freely; the safe teleport in step
   1 is allowed. Stop, wait two seconds, inspect, and finish:

   ```lua
   GetMod("PTFR_MistyViktor_World").Stop()
   GetMod("PTFR_MistyViktor_World").Inspect()
   GetMod("PTFR_MistyViktor_World").Finish()
   ```

   Expect Enabled 0 and Applied 0 only on normal guarded release. The original
   Misty interior remains hidden after Stop, as the vanilla Tower cleanup
   specifies; this is not a restoration of a pre-test erroneous interior. If
   movement or support fails, do not Stop beneath V. Quit without saving and
   report the problem. Otherwise, quit without saving and report the three
   observations separately.
