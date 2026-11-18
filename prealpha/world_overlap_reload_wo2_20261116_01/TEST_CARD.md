# WO2 AutoSave-16 live test

Load the existing AutoSave-16 normally. At the same street near Viktor's clinic and Afterlife, check the raised sidewalk and road immediately when free roam appears, and again after a few seconds without fast travelling. Confirm that the ordinary street remains solid. If a duplicate flashes briefly before disappearing, report that timing separately from a persistent duplicate.

If any duplicate persists, this CET command only reads WO1's private facts:

```lua
do local q=Game.GetQuestsSystem(); print("WO1="..q:GetFactStr("PTFRWO1_CleanupRegistered").."/"..q:GetFactStr("PTFRWO1_CleanupPermit").."/"..q:GetFactStr("PTFRWO1_CleanupDone")) end
```

Expected after dispatch: `WO1=1/0/1`. This proves a dispatch receipt, not visible removal. `1/0/0` means the phase has not dispatched; `1/1/0` means the permit is set but the waiting owner has not advanced. Keep the loaded save and original AutoSave-16 unmodified for diagnosis where possible. A later separate load of ManualSave-33 can test whether an already-done world variant persists across reload.
