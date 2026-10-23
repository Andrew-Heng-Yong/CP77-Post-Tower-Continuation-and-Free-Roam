# Padre call trace — U5

Installed diagnostic only, not a phone repair. Jeopardy's original activation,
journal and written briefing worked in the prior test. The missing audible call
needs a short capture before choosing the native dependency to repair.

1. Start the game after this installation. Load **ManualSave-20**, level49,
   **16:32:18,11.10.2026** — the original post-Tower snapshot before Jeopardy was
   requested. Do not use a new snapshot where Jeopardy has already started.
2. Let the world settle with menus closed for15 seconds. Open CET and arm:

```lua
print(GetMod("PTFR_PadrePhoneU5").Arm())
```

It must say `active=true`. The trace expires after five minutes. If it refuses,
send that output; do not force facts or start other restoration batches.

3. Request the original Jeopardy graph once:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeJeopardyU4"):Start("DISPOSABLE_SAVE"))
```

4. Close CET/menus, holster and approach the same Jeopardy encounter used last
   time. Remain outside combat. If a call is offered, answer normally; do not
   deliberately decline/skip it. Wait at least40 real seconds after approaching
   or until a longer call finishes. **Do not complete the gig.**
5. Stop the recording:

```lua
print(GetMod("PTFR_PadrePhoneU5").Stop())
```

Send the final status and whether you got a ringing/answer prompt, spoken call,
or only a message. The local `padre_u5_*.jsonl` trace is saved in the CET
`PTFR_PadrePhoneU5` mod folder; no manual upload is needed on this PC.

No new save or save/reload check is needed. You may close the game after stopping
the trace. Keep the original ManualSave-20 unchanged.

## Scope and limitations

The logger only reads facts, journal state and phone getters; optional observers
copy call-event metadata. It starts no quest/phone owner and changes no gameplay
facts, rewards, journal entries, phone UI, save files or cache. Session changes
cancel recording; getter failures stay unknown; storage errors disable logging.
Frame sampling can miss same-frame pulses, and successful observer registration
does not prove native callback delivery. Absence of a sampled acknowledgement
alone must not be called proof that a native handler is absent.

Recovery, with game closed: `tools/deploy_padre_phone_u5.ps1 -Mode Rollback` moves
only the logger source to a recoverable workspace copy and preserves trace files.
U4 gameplay recovery is separate; never enable its predecessor copied owner in a
save already running U4.
