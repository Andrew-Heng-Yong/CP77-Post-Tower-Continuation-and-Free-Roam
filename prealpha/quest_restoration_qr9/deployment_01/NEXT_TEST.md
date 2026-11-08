# Installed — first manual test

QR8:02 and QR9B04 are installed and file-verified. ManualSave-23 is unchanged and has a verified offline backup. The game has not been launched. You perform the following steps; Codex will analyze the logs afterward.

1. Launch normally. Load **ManualSave-23 — 29 October, 7:23 PM** only to create a working branch. As soon as the native menu permits it, use **Save Game → New Save**. Never overwrite23. Record the new slot's timestamp. If New Save is unavailable, stop and report it.
2. Return normally to the main menu. In CET, enter:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("S00")
   ```

3. Load only the newly created native working save. Move and open/close the map for 1–2 minutes. Accept no gig. Stop on an unexpected quest restart, repeated call, duplicate actor/reward or error.
4. In CET, enter:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop()
   ```

5. Quit normally. Reply with the new slot timestamp, whether loading/control/map worked, and any unexpected quest/call/error. Codex can then collect the local logs and check the master/backup again; no manual fact inspection is needed.

The initial Load23 → New Save is **bootstrap**, not disposable-startup proof. All restored controllers may initialize before the working slot exists. The subsequent working-slot load observes retained owners, not a recreation of the first registration attempt. Do not rename a copied folder as a substitute for a native New Save. Stop capture before every deliberate reload and start a separate segment afterward.

Logs are under `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR9_capture_*.jsonl`. Capture auto-stops after 300 seconds by default. If CET reports a missing module/API or failed capture, report the message and stop; do not set facts or force a quest.

If you prefer to collect immediately after quitting, this PowerShell command creates a fresh local bundle:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S00_01 --card S00
```

The bundle goes to `prealpha/quest_restoration_qr9/observations/S00_01`. Screenshots are needed only for a visual problem. Fresh CVI02/Saints/Spy and the already successful generic Ana test are not part of this smoke. Do not advance other cards yet.
