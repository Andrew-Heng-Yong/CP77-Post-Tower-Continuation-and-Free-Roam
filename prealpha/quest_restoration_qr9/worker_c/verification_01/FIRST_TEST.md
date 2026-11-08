# First test — S00 only
Prepared only; wait for explicit deployment authorization and successful verification.

Future authorized Install -BackupMaster preserves the exact original3files in workspace recovery. The user then loads ManualSave-23 solely to use native Save Game/New Save, identifies the actual new slot and keeps bootstrap separate. No backup or working copy has yet been created; never assume a renamed raw folder is recognized.
Read the reviewed working-save procedure: C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\USER_PROCEDURE.md
Keep original ManualSave-23 and its verified offline backup unchanged. Do not rename a copied folder and assume it is a recognized slot.

## Bootstrap only if no native working slot exists
Follow the reviewed user-only backup procedure first. In game, load ManualSave-23 only for this bootstrap, then immediately use native Save Game → New Save. Never select overwrite23. Record the actual newly created native slot. If saving is unavailable, stop; no workaround.
Any bootstrap capture is a separate segment, not a disposable-startup PASS. Stop capture before deliberate reload. The later working-slot reload does not recreate the first registration attempt.

## Short smoke on the native working slot
1. With capture stopped, return normally to the main menu. Enter `GetMod("PTFR_QR9_Diagnostics").start("S00")` manually in CET.
2. Load only the identified native working slot.
3. Move normally and open/close the map for1–2 minutes. Accept no gig and overwrite no master.
4. Enter `GetMod("PTFR_QR9_Diagnostics").stop()`, then quit normally.
5. Collect the bundle using the reviewed command in MANUAL_TEST_CARDS.md. Send: working-slot label, loaded? control/map okay? unexpected quest/call/error?
6. Use the reviewed read-only verification to check original23 and backup after the run; if either changed, preserve the backup and stop. No automatic save restore.

Logs: C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics
Early startup/numeric phase execution may remain unobserved. A receipt proves an attempt, not successful-owner activation.
Fresh CVI02/Saints/Spy are unavailable on this master; do not replay them. No generic Ana test is requested.
