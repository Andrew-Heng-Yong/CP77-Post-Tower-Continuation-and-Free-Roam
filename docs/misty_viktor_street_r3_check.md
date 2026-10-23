# R3 Tower street dressing — one disposable opt-in check

Installed idle; not automatic or live-verified. Use a disposable post-Tower save
and quit without saving. This pass adds passive Tower street meshes/decals/
collision, including the Zetatech exterior logo. It deliberately adds no NPCs,
Terry, scene replay, lights, sound or dynamic props. The R2 interior/rear-door
behavior remains in the same opt-in. Do not force any q307 facts or variants.

1. Cold-launch and load a disposable completed-Tower save. While freely moving,
   go to the known safe point outside the80m clinic area and arm R3:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
   GetMod("PTFR_MistyViktor_World").Start()
   ```

2. Close CET, wait at least two seconds, then run:

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   ```

   Require Revision3, Registered1, Enabled1, Applied1 before approaching.
   These indicate native requests, not visual/physical streaming success.

3. Walk to the Zetatech storefront and the street immediately in front of it.
   Look for the corporate logo and Tower street dressing. Check for clipping,
   duplicated old/new signs or barriers, invisible collision, missing ground,
   crashes or unexpected actors. Do not step into unsupported geometry. The
   previously passed upper-shop rear door and old-sign removal need only a
   quick regression glance. Record the observation:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("street-first")
   ```

4. Leave the clinic block, return once and check the same visuals and walking
   support, then run:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("street-return")
   ```

5. Go back outside80m (the safe teleport above is allowed only while freely
   moving). Disarm, wait two seconds, inspect and finish the trace:

   ```lua
   GetMod("PTFR_MistyViktor_World").Stop()
   GetMod("PTFR_MistyViktor_World").Inspect()
   GetMod("PTFR_MistyViktor_World").Finish()
   ```

   Expect Enabled0/Applied0 on normal guarded release. If you cannot leave
   safely, do not Stop under V. Quit without saving and report the obstruction.
   Otherwise quit without saving and report logo, dressing, old/new overlap,
   walking support, return visit, and any actor/scene anomaly. Do not infer
   full exterior completion from this passive first pass.
