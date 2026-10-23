# One-site Zetatech revision2 rear-door/storefront check

Candidate installed idle, not automatic. Cold-launch and load a disposable
post-Tower save made before this opt-in was used. Do not save; no ending replay
or story-fact commands. R2 now requests one exact rear-door unlock natively.
It removes old Misty signage/light strips, not adds a new exterior Zetatech sign.
Test world geometry/access, not Viktor/Misty's Tower dialogue.

1. Freely moving, teleport to the previously reviewed ordinary Little China
   arrival point, outside the clinic area:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1658.87463,y=997.365662,z=23.6999989,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=-170})
   GetMod("PTFR_MistyViktor_World").Start()
   ```

2. Close CET, wait two seconds, then:

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   ```

   Require Revision2/Registered1/Enabled1/Applied1 before proceeding. Applied confirms
   dispatch, not actual floor residency. If not1, report the output and stop.

3. Walk normally to the old Misty storefront/Zetatech area and Viktor's clinic
   (roughly230m northeast from this landing). Look before entering: the repaired
   area must have visible floors/walls. Use surviving normal doors, no noclip.
   Check that the old Misty sign/light strips are gone. Try the rear door INSIDE
   the upper Zetatech shop, then walk through it toward the courtyard. The
   downstairs clinic door is untouched. Check ground support and clipping along
   that route; if reachable, the existing Viktor menu should still work (no
   cyberware equipment changes). Do not repeat the full basic interior test.
   No Misty/clerk/thugs/Johnny or Tower conversation should be created. Mark:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("first-shop-check")
   ```

   If floor is absent/unsupported or a door blocks the route, stop exploration,
   screenshot/report it and return to the safe landing with the teleport above.
   Do not force original variants or story facts. A floor failure with Applied1
   needs live block/variant-registration diagnosis.

4. Walk outside, then return once. Confirm the same supported geometry/access,
   no additional Viktor group and no unexpected scene. Mark:

   ```lua
   GetMod("PTFR_MistyViktor_World").Mark("return-shop-check")
   ```

5. Return to the safe landing (teleport above is allowed while freely moving),
   then request release:

   ```lua
   GetMod("PTFR_MistyViktor_World").Stop()
   ```

   Wait two seconds, then:

   ```lua
   GetMod("PTFR_MistyViktor_World").Inspect()
   GetMod("PTFR_MistyViktor_World").Finish()
   ```

   Expect Enabled0/Applied0, Revision2, AccessRequests1/RestoreRequests1 and one
   acquisition/release on a fresh fixture. These
   are request-path counters, not acknowledgement of physical unloading. Quit
   without saving. Tell me about floor support, shop appearance, doors/stairs,
   Viktor/menu and any duplication/crash. Logging closes each JSONL row in the
   CET module directory and stops after ten minutes; stop safely outside first
   if the route takes longer. No repeated full ending is needed.
