# Automatic Streetkid check

No Start/Arm/Finish command required. The old S2 CET module is read-only.
Do not use S1 or S3 concurrently. Use a clean disposable post-Tower save.

1. Cold-launch, approach the stool; Sit → Drink → Fix nose → Get up.
2. Wait about1–2seconds and use it again.
3. Walk more than7m away and return. Also leave once while Sit is offered but
   without selecting it: movement should remain free and the unused scene end.
4. Optional reload check: outside the bar and idle, save to a NEW disposable
   slot, fully quit, reload it and return. Never overwrite the master.

Report missing prompts, duplicate body/glass, wrong reflection or stuck V.
Do not teleport during an action or clear facts to recover.

Optional read-only observation, not required for activation:

```lua
GetMod("PTFR_Streetkid_Seat_Mirror_S2").Observe("auto-repeat")
```

When CET is present, change-only streetkid_auto_*.jsonl logging is automatic.
Requests/Returns include unused-prompt departures. Interrupted1 intentionally
blocks rearm and requires investigation.
