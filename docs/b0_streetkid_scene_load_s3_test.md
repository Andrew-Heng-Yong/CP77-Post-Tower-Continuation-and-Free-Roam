# S3 revision 2 — actor-index crash repair installed

**Revision 2 installed idle on 2026-09-26. The original S3 payload is rejected.**
Both crash dumps identify the same out-of-range player index. Revision 2 fixes
V's actor ID and packed performer references. Offline regression checks reject
the original crashing payload. Live return still needs this short check.
Start checks the native revision stamp; Inspect is not required.
Use the disposable post-Tower save from before the failed S2 run. No ending
replay is needed. Keep S1 and S2 unarmed, and do not save this probe.

The entire check is:

1. Cold-launch, load the disposable save, and walk to the Streetkid stool.
   Optional teleport outside El Coyote (not while in any scene/workspot):

   ```lua
   Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1256.16101,y=-1000.92426,z=12.42,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
   ```

2. Stand idle within 3 m of the stool. Run once:

   ```lua
   GetMod("PTFR_Streetkid_Scene_Load_S3").Start()
   ```

3. Close CET and wait five seconds. **No Sit, mirror prompt or animation is
   expected.** Do not interact or teleport during this short interval.
   Start should have printed `Revision 2 started (actor-index fix)`.

4. Run:

   ```lua
   GetMod("PTFR_Streetkid_Scene_Load_S3").Finish()
   ```

5. Quit without saving and send the output. Logging starts automatically and
   flushes each record to `streetkid_scene_load_s3_*.jsonl` in the CET mod folder.

Pass: Ready=1, Requests=1, Returns=1, Completed=1, Interrupted=0, Active=0,
scene=false, workspot=false, required facts unchanged, and no crash/control
fault. Finish checks these values and disarms only when V is idle. A refusal
is not a reason to force facts. If it crashes or cannot return, stop testing
and quit without saving; do not arm S2/S1 or introduce extra dependencies.

This pass would validate only acquisition and return, not the fix-nose action
or reflection. The repaired action package remains uninstalled afterward.
