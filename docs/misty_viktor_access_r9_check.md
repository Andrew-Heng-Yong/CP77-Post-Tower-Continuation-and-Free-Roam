# R9 Zetatech doors and receptionist — disposable check

Use a disposable completed-Tower save. No CET Start command is required. Do
not replay the ending and do not repeat the R8 neon/police comparison.

1. Cold-launch the save, approach the Zetatech shop, and wait up to 20 seconds
   for the area to stream.
2. Confirm the front door is closed at rest, opens normally for V, and closes
   again after passage. Repeat once from the inside.
3. Walk to the surviving inner/rear door. Confirm it is closed at rest, opens
   normally from the usable side, and closes again rather than remaining fixed
   open.
4. Confirm exactly one male Zetatech receptionist is inside at his authored
   idle position. He should not start the q307 conversation or summon Misty,
   Johnny, the new merc, guards, or the alley scene cast.
5. Read only these diagnostics:

```lua
local q=Game.GetQuestsSystem(); for _,n in ipairs({"PTFRMV_Revision","PTFRMV_AccessRevision","PTFRMV_DoorRequests","PTFRMV_ClerkRequests","PTFRMV_Applied","PTFRMV_Enabled","q307_active","q307_done","q307_finished","q307_2079"}) do print(n,q:GetFactStr(n)) end
```

Expected: Revision7, AccessRevision9, DoorRequests and ClerkRequests at least1,
Applied1/Enabled1, and Tower guards 0/1/1/1. Counters prove dispatch only; the
door motion and single visible receptionist are the live evidence.

Quit without saving. Report front/rear open-close behavior, receptionist count
and whether any dialogue/scene unexpectedly started.
