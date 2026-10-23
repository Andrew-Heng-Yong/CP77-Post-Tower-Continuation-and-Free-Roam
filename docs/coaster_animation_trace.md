# Coaster animation trace

Superseded: this revision1 probe produced no callbacks. Do not repeat this
unchanged test. Use `coaster_direct_entry_check.md` for the revised candidate
and active-instance observer after confirming its installation receipt.

The ride/exit package is still revision5. This check records actual native
animation callbacks to diagnose the missing hands. It is not another gesture
fix. No need to repeat the six-press check.

1. Cold-launch and load the same original disposable save whose coaster gate
   was0. At the platform, start the logger:

```lua
GetMod("PTFR_WorldInteractions_Audit").Start()
```

It should print `Animation observer: REGISTERED`. If it prints UNAVAILABLE,
stop here and report that line; a ride would not supply the needed evidence.

2. Enable the previously authorized temporary gate:

```lua
Game.GetQuestsSystem():SetFactStr("mq006_enable_repeatable_rollercoaster", 1)
```

3. Get in and select Raise arms ONCE. Finish the ride and Exit normally.
   No special observations/marks during the ride are needed.

4. After Exit:

```lua
Game.GetQuestsSystem():SetFactStr("mq006_enable_repeatable_rollercoaster", 0)
GetMod("PTFR_WorldInteractions_Audit").Mark("animation-trace-after-exit")
GetMod("PTFR_WorldInteractions_Audit").Stop()
```

Quit without saving and report done. The JSONL records setup path and actual
played/skipped/missing clip names. A start counter alone is insufficient.
