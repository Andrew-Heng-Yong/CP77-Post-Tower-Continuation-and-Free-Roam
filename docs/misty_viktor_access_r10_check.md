# R10 Zetatech doors and storefront NPC — disposable check

Use the same disposable completed-Tower save. No CET Start command, ending
replay, or repeat R8 lighting comparison is required.

1. Cold-launch the save and approach the Zetatech storefront. Wait up to 20
   seconds after both doors and the storefront are visibly loaded.
2. Confirm the former R9 indoor storekeeper is absent.
3. Confirm one Zetatech guard/NPC appears on the street directly in front of
   the store. Report whether he visibly idles/animates or remains frozen.
4. Check the front door at
   `-1548.5966796875 1191.4342041016 16.215202331543`: it should be closed at
   rest, offer normal interaction, open for V, and close afterward.
5. Check the inner door at
   `-1542.2309570313 1200.6055908203 15.869735717773` the same way.
6. Read only these diagnostics:

```lua
local q=Game.GetQuestsSystem(); for _,n in ipairs({"PTFRMV_Revision","PTFRMV_AccessRevision","PTFRMV_DoorReady","PTFRMV_DoorRequests","PTFRMV_StreetNPCRequests","PTFRMV_ClerkRemovalRequests","PTFRMV_Applied","PTFRMV_Enabled","q307_active","q307_done","q307_finished","q307_2079"}) do print(n,q:GetFactStr(n)) end
```

Expected near the loaded storefront: Revision 7, AccessRevision 10,
DoorReady 1, all three request counters at least 1, Applied/Enabled 1, and
Tower guards 0/1/1/1. Counters prove dispatch only. Door rest state,
interaction/open-close behavior, absence of the clerk, and the visible outdoor
NPC are the live evidence.

Quit without saving. Report both doors separately and whether the outdoor NPC
is animated.
