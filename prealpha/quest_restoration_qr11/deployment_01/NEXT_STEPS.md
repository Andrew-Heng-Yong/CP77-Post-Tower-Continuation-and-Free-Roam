# D00 — ready to test; installation is complete

QR10D01 is installed, verified and rollback-ready. **Do not run Install again.** The game has not been launched by Codex. Allow about one minute; no manual save or reload is needed.

1. Launch Cyberpunk2077 normally. Use **Load Game → ManualSave-24**, dated **2 November 2026,16:37:02 /4:37PM**, **level51**. Do not use Continue or the protected ManualSave-23. Stop if that save cannot be identified.
2. With normal player control, no combat/dialogue/incoming call, open the phone with **T** and select **Regina Jones**. If her normal **Call** option is absent, stop and report **D00 NOT_TESTABLE — no Regina Call option**. Do not force eligibility or substitute a quest.
3. If available, close the phone. Open CET with **backslash `\`**, select Console and enter:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("D00", "QR11-D00-Regina", 120)
   ```

   Require `[PTFR QR10] Recording: QR10_capture_...jsonl`. Error/NOT_RUNNING/unknown profile means stop and report the text. Optional supported check: `print(GetMod("PTFR_QR9_Diagnostics").status().state)` must say `RECORDING`.
4. Close CET. Wait **four seconds** in normal gameplay. Make **one ordinary Regina call**. Let it ring/converse for at least **six seconds** when possible; select no quest-starting topic. Let it end naturally or use normal Goodbye. Note ringing, voice, no answer or a stall. No answer alone is not a defect.
5. Wait **six seconds** after the call ends, then open CET and enter:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop("D00_DONE")
   ```

   Require `Stopped: QR10_capture_...jsonl`; retain the filename. Report an automatic120second stop or other early stop instead of hiding it with another run.
6. Quit the game and RED launcher normally. No manual save/reload is needed; never overwrite ManualSave-23. In PowerShell run:

   ```powershell
   & 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\collect_d00.py'
   ```

   The collector automatically freezes a copy/hash, checks schema2, reads current installed hashes, copies bounded CET log tails and metadata, and prints a fresh folder under `C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\evidence\D00_*\`. It never launches or controls the game or changes game/save files.
7. Return the printed folder path/capture filename plus:

   > D00 | ManualSave-24,2Nov16:37 | Call available yes/no | rang/answered/no answer/stalled | recording stopped/auto-stopped | unexpected behavior none/details

Original captures remain under:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR10_capture_*.jsonl`

Expected: attached baseline, explicit callback-unavailable declaration, bounded sampling and one or more `FACT_SAMPLE_CHANGE` records for `phonecall_player_with_regina_jones`, then STOP/CAPTURE_CLEANUP. Global phone-active getter changes may also appear. No journal change, quest completion or reward is required.

Natural call + coherent sampled change + valid complete/error-free capture supports **PASS for the sampler only**. No sampled difference or missed capture window is **INCONCLUSIVE**; absent genuine Call is **NOT_TESTABLE**. Logging/getter/integrity errors are diagnostic failures, not proof of a quest defect. Samples are approximately two seconds apart and may miss reverted/transient states; they never establish native callbacks or exact native-write ordering.

No cleanup or rollback is normally needed; a stopped logger is idle. Preserve logs. No other quest test has a qualified fixture, and Wilson/Bullets/Zane/Cynthia/reload successes must not be repeated. The detailed historical plan and missing-prerequisite queue remain in `../MANUAL_TEST_PLAN.md` and `../runtime_test_queue.json`; their pre-install instructions have already been completed.
