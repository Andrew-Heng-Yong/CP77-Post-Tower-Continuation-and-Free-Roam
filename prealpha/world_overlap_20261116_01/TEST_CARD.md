# WO1 street cleanup — live check

Status: installed; visual, collision and save/reload behavior not yet observed. The existing accepted KOLD MIRAGE start result remains recorded separately.

1. Launch normally and load your genuine post-Tower save. Keep the original save slot.
2. Fast travel to another district, such as Heywood, more than 500 metres from the clinic/Afterlife streets. Stand on foot, outside combat or conversation, for about five seconds. This gives the automatic cleanup a safe opportunity to run.
3. Return to the two reported locations and walk or drive the affected streets. Check that the raised duplicate surfaces and their collision are gone, and that the ordinary road and sidewalk remain solid. Check the clinic's restored appearance as well.
4. If those checks pass, save in a new slot and reload it. Revisit the area to check persistence.

If the overlap remains, this optional CET command only reads three private cleanup facts and prints to the console. It does not set facts or write a save/file:

```lua
do local q=Game.GetQuestsSystem(); print("WO1 registered/permit/done="..q:GetFactStr("PTFRWO1_CleanupRegistered").."/"..q:GetFactStr("PTFRWO1_CleanupPermit").."/"..q:GetFactStr("PTFRWO1_CleanupDone")) end
```

After dispatch, the expected settled result is `1/0/1`. This confirms only that cleanup was dispatched; the visible result and collision still need observation. A `done=0` result means the phase has not dispatched, so report the output and location without forcing facts.

For any remaining duplicate, record its World Inspector sector, node definition/instance and position. That identifies whether it belongs to this reviewed decoration set or a different owner.
