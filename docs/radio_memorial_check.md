# One combined radio / columbarium check

Use a disposable post-Tower save with the current restoration baseline. Cold
launch after installation; no new ending replay. Do not save this test. The
native candidates are already automatic: no Arm/Enable or fact writes.

1. Once loaded and freely moving, run:

   ```lua
   GetMod("PTFR_RadioMemorial_Audit").Start()
   ```

2. Close CET. Turn on the pocket radio normally. Listen for 20–30 seconds, change
   station, then turn it off and on once. Note actual sound (not just station UI).
   Record what happened, choosing the truthful label:

   ```lua
   GetMod("PTFR_RadioMemorial_Audit").Mark("radio-audio-ok")
   ```

   If silent, use `Mark("radio-silent")` instead. Do not force `radio_on` or news
   facts. A vehicle radio may be observed if already convenient, but is not an
   extra required route.

3. Travel normally to the Columbarium in North Oak. Inspect several memorial
   plaques/holographic names. Record which are visible (a screenshot is useful),
   walk away and return once. No use/prompt is required. Saved outcomes determine
   which plaques should appear; Jackie is not mandatory when Heroes is unfinished.
   Do not scan to summon Johnny or change death/quest facts.

   ```lua
   GetMod("PTFR_RadioMemorial_Audit").Mark("memorial-checked-return")
   ```

4. Stop logging, then quit without saving:

   ```lua
   GetMod("PTFR_RadioMemorial_Audit").Stop()
   ```

Report audible radio yes/no, visible plaque names or screenshot, whether they
remained after returning, and any unexpected Johnny appearance. Logging is
bounded to ten minutes; restart a recording if the route takes longer. Durable
`radio_memorial_*.jsonl` files are in the CET module directory. Do not use the
older `PTFR_WorldInteractions_Audit.Start()` for this check: its deferred coaster
observer is outside this test.
