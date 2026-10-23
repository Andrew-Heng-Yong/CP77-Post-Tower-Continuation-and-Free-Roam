# Streetkid stool: S2 revision 4 opt-in

**Revision 4 installed idle on 2026-09-26.** Revision3 fixed labels and room
reflection and exited cleanly, but glass appeared only during Drink and V was
absent from the reflection. Revision4 adds matching-body activation/workspot/
release using vanilla patterns, default mirror appearance, and an initially
acquired glass anchored to the verified bar marker. Do not arm S1 or S3.
The controller requires native S2 Revision=4.

Installed idle. This is an experimental optional revisit, not a restoration of
a normally available free-roam Sit prompt. The user's ordinary pre-Tower check
also had no seat/mirror prompt. Do not arm S1 during this test.

Use a disposable post-Tower save that has never armed S2. Do not save. The
controller opens and flushes `streetkid_seat_mirror_s2_*.jsonl` automatically.
No q000, Pepe, Mama Welles, Pedro or Tower story facts are written.

1. Cold-launch and load the disposable save. Optional teleport outside El Coyote:

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1256.16101,y=-1000.92426,z=12.42,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
   ```

2. Walk to the Streetkid-start stool by the mirror, approximately
   `(-1261.89,-1001.64,12.03)`. Stand idle nearby and run once (Inspect is optional):

   ```lua
   GetMod("PTFR_Streetkid_Seat_Mirror_S2").Start()
   ```

3. Close CET. Use **Sit**. BEFORE Drink, check for the glass already on the
   counter and V in the mirror. Then choose **Drink**, **Fix nose**, and
   explicitly **Get up**. Confirm labels, the glass in V's hand, reflected pose,
   no duplicate body, and free movement afterward. Report wrong outfit/face or
   floating glass rather than counting any visible body as a complete pass.
   Drink returns to the seated choice;
   Fix nose changes V's pose and leads to a separate Get up choice. These are
   staged options, not three simultaneous indefinitely repeatable actions.
   No prologue dialogue, quest progression or automatic stand should occur.
   Mirror presentation remains experimental; a lifecycle PASS is not a visual
   pass. The changed variant/device must return to its inactive presentation
   after leaving the scene. Do not teleport during an action.

4. After V can move, record and finish with one command:

   ```lua
   GetMod("PTFR_Streetkid_Seat_Mirror_S2").Finish()
   ```

5. Quit without saving. Report which physical steps worked and whether V was
   free afterward. One visit only; S2 is deliberately one-shot.

Expected after-action trace: `SceneRequests=1`, `SceneReturns=1`, `Completed=1`,
`Interrupted=0`, `Active=0`, `scene=false`, `workspot=false`. A prompt alone is
not success. If Start refuses, send the reason and do not force facts. If the
prompt/action fails or V is stuck, safely Observe if possible, then quit without
saving; do not teleport out of an active scene or clear its facts.

S1 remains untested and must stay idle. Revision4's install receipt confirms
389 other tracked project files hash-preserved and revision3 backed up.
Red Dirt and the public washroom mirror are unchanged.
