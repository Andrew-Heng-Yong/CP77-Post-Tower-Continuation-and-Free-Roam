# Automatic Red Dirt mirror

Cold-launch and load a disposable post-Tower save. No CET Start/Arm is needed.
Walk to Red Dirt's mirror, use Look, one expression and the mirror's Stop action.
Walk out of the mirror area, return and repeat. The bartender should continue
working. Do not teleport during a mirror interaction.

The original local quest gate still applies. If no prompt appears, report it;
do not clear story facts or Interrupted. Optional read-only observation:

```lua
GetMod("PTFR_RedDirt_Mirror").Observe("automatic-check")
```

Legacy Start/Stop now only report state. Leave scenes normally before saving.
For persistence verification later, use a new disposable slot outside the bar
and idle, fully quit, reload and return. Never overwrite the master fixture.
Automatic save/reload is not yet live-verified. Optional diagnostic logs are
`red_dirt_auto_*.jsonl` inside the existing PTFR_RedDirt_Mirror CET folder.
