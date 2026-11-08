# Jinguji unfinished-checkpoint resume — 3 November 2026

**One short test; no fight replay.** Existing AutoSave-3,2November16:33:46, still matches the earlier pinned body, metadata and screenshot. Its screenshot shows Melissa inside Jinguji after the attack. Saved native active1, MaxTac-arrived1, grateful1 and private Issued/Entered1 are positive evidence of the progressed encounter; no positive native done record or finished metadata was present in the pinned parse. Saved absence is not runtime0 and actual executing owners remain opaque.

This qualifies a narrow observation of **resuming an existing active checkpoint**, conditional on the expected in-game state after load. It does not certify a precisely decoded pending-cleanup node, native owner retirement or reward idempotence. Completed-state reload/shop results remain accepted. The previous full replay corroborated completion after a death/reload but its sampler stopped at the detach; no full fight is requested again.

## Exact steps

1. Launch normally yourself. Stay at the **main menu**; do not load a save yet. No installation or restart of diagnostic files is needed. Keep ManualSave-23 and24 untouched.
2. Open CET and run:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("S05", "QR12-Jinguji-PendingLoad", 300)
   ```

   Require **Armed**. An error/unknown profile/NOT_RUNNING is a stop condition. If Already recording appears, stop the old capture before starting this one. The bounded installed logger waits for an attached non-pregame player, then takes its initial baseline; arming does not observe engine writes before attachment.
3. Close CET. Load **AutoSave-3 — 2November,4:33PM (16:33:46)** through the normal menu. Expected location: Jinguji with Melissa/MaxTac after the fight. If it loads a different situation, an earlier ending/PONR state or another incompatible branch, stop and report. Do not force the quest/actor/facts.
4. Observe the journal and NPCs. If Bullets is still active, finish only the remaining normal dialogue/objective. If already completed immediately after load, report that; do not restart it. No attack, shopping, new fight or side quest is required.
5. After the quest completes—or its already-completed loaded state is clear—wait **six seconds** in ordinary unpaused gameplay, then open CET:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop("QR12_JINGUJI_PENDING_DONE")
   ```

   Require **Stopped**. Capture has a5minute limit including loading. If it auto-stops, report the reason/result; do not treat later actions as recorded. If another death/reload happens, the session guard stops capture; restart the start command after loading as a separate segment if capture is still needed, and report that interruption.
6. Exit normally. No manual save or repeated shop/completed-state reload is needed. Report: **actual save/date; Active or completed immediately after load; completed normally yes/no; missing/duplicate NPC/dialogue or any reward issue; stopped/auto-stopped; any death/reload**. The assistant can collect the automatic logs from the existing diagnostic directory.

Logs: `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR10_capture_*.jsonl`.

Expected evidence: S05 start/SESSION_WAIT, attached baseline, native journal observations, any captured done/active/vendor-marker changes, explicit native-callback-unavailable declaration, clean STOP/CAPTURE_CLEANUP. If completion precedes the first baseline, only post-load state and broader log are observed; missing sampled transitions are INCONCLUSIVE for timing, not automatically a failed quest.

Behavior PASS is limited to the expected progressed checkpoint resuming/completing without a visible replay/stall/duplicate. A wrong fixture is NOT_TESTABLE. Visible stalls/errors require investigation. Native owner identity/leases/termination and exact native-write order remain unobserved even if the behavior passes; no universal S05 or reward-idempotence PASS is implied.

The source snapshot is already preserved outside the save root under `../jinguji_replay_01/saved_inputs/AutoSave-3/`. No backup is restored. Original source files and runtime files are read-only to the assistant. Prior post-run60installed/sixmanual-save verification is reused; this preparation freshly checks the candidate's three files and both diagnostic file hashes. No build, install, save/fact edit, game launch/control or CUA occurs.
