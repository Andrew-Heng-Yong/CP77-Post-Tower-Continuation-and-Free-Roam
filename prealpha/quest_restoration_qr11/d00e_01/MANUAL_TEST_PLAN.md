# D00E — El Capitan natural-call check

**Installed and verified. No further installation command is needed.** Only `watch.json` changed to add D00E. Existing profiles and the QR10D01 logger code remain unchanged. Regina's D00 stays NOT_TESTABLE; this is its separate replacement. User confirmed El Capitan has a genuine Call option and interaction lines. The actual loaded slot at that observation was not independently identified.

1. Launch normally and load the verified working **ManualSave-24 — 2November2026,16:37:02 /4:37PM,level51**. Do not load the protected ManualSave-23 or an ending/PONR slot. Confirm El Capitan still offers **Call** in the normal phone (T). If absent, stop and report NOT_TESTABLE; no forced call. If your earlier observation used a different slot, report its actual name/date rather than treating it as verified ManualSave-24.
2. Close the phone. Open CET with **backslash `\`**, Console tab. Run:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("D00E", "QR11-ElCapitan", 120)
   ```

   Require `[PTFR QR10] Recording: QR10_capture_...jsonl`. The QR9 module name/QR10 console prefix are intentionally stable. An error/NOT_RUNNING/unknown profile is a stop condition.
3. Close CET. Wait **four seconds** in normal gameplay, then place **one ordinary El Capitan call**. Remain in ringing/conversation for at least **six seconds** when possible. No new job, vehicle purchase or quest-report topic is required. Let it end normally or use normal Goodbye. Wait **six seconds** after it ends, outside pause menus. Note ringing/voice/choice-menu/no-answer/stall.
4. Reopen CET and stop:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop("D00E_DONE")
   ```

   Require `Stopped: QR10_capture_...jsonl`. Report auto-stop/early error if it happened. Quit the game and RED launcher normally. No manual save/reload or cleanup is needed; never overwrite the master.
5. In PowerShell, collect evidence automatically:

   ```powershell
   & 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\d00e_01\collect_d00e.py'
   ```

   The printed folder under `...\quest_restoration_qr11\d00e_01\evidence\` includes the capture copy/hash, summary, current installation hashes, bounded CET log tails and metadata. No manual fact list is required. If collection errors, retain the original capture and printed error.
6. Return the folder path/filename plus: **actual save name/date; El Capitan Call available; rang/answered/choice menu/no answer/stalled; recording stopped/auto-stopped; unexpected behavior**. A normal unanswered call alone is not a mod failure.

Original logs stay at:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR10_capture_*.jsonl`

Expected records: QR10D01/D00E start and attached baseline; explicit native-callback-unavailable declaration; sampling started; one or more `FACT_SAMPLE_CHANGE` records for `phonecall_player_with_muamar_el_capitan_reyes`; STOP/CAPTURE_CLEANUP. Global phone-active getter changes may also appear. No journal change or quest/reward outcome is requested.

**PASS for sampler:** natural call + coherent sampled difference + valid completed capture without getter/log errors. **INCONCLUSIVE:** no sampled difference, missed/transient window, early stop or installation drift. **NOT_TESTABLE:** no genuine Call option. **Diagnostic FAIL:** startup/getter/log/integrity error, separately from any gameplay anomaly. Sampling is approximately two seconds apart; it does not prove native callbacks, actual controller ownership, native-write time/order or unseen intermediate values. Live validation is pending until this human test.

No other quest test is qualified, and prior Wilson/Bullets/Zane/Cynthia/reload successes must not be repeated.
