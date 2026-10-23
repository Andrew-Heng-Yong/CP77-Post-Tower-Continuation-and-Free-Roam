# Original Padre handler — U6 call test

Installed2026-10-12. This trial starts the original Padre phone controller only;
it does not restart the global phone initializer or alter Jeopardy's dialogue.
Offline compilation/package/recovery checks passed. Live call delivery is pending.

1. Launch the game after installation. Load **ManualSave-20**, level49,
   **16:32:18,11.10.2026**, the original snapshot before U4 Jeopardy was requested.
   Do not use the previous failed-call run or a new snapshot with Jeopardy started.
2. Close menus and let the world settle15 seconds. Open CET, arm the existing trace:

```lua
print(GetMod("PTFR_PadrePhoneU5").Arm())
```

Expect `active=true`. Then request the new original-Padre-handler entry:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativePadreU6"):Start("DISPOSABLE_SAVE"))
```

3. Close CET/menus, holster, stay out of combat/vehicles for5 seconds. Inspect:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativePadreU6"):Inspect())
```

Expect `ready/request/issued=1/1/1`, `fault=0`. `issued` means the original controller
was entered; it does not yet prove a working call. If refused/not issued, send the
output and stop here. Do not force facts or rerun restoration batches.

4. Start the unchanged original Jeopardy pilot:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeJeopardyU4"):Start("DISPOSABLE_SAVE"))
```

Close CET/menus and approach the same Jeopardy encounter. Answer normally if
offered; do not reject or enter combat. Wait40 real seconds after approach, or
finish the call if it runs longer. **Do not complete the gig.**

5. Stop the trace and capture handler status:

```lua
print(GetMod("PTFR_PadrePhoneU5").Stop())
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativePadreU6"):Inspect())
```

Report whether you saw the call popup, heard Padre's briefing, and could finish
it normally. Text may also follow a successful native call; text alone is not a
success criterion. The trace will be inspected locally.

No new save or gig completion is needed. You may close the game after this test.
If travel exceeds the trace's five-minute cap, report expiry; do not replay a
briefing in-place or set native call facts to recreate it.

## Scope and recovery

Only the original Padre controller is entered. Global phone reset/cleanup,
other contacts, shared interruption handling and fixer-credit progression are
not restored by this package. Keep this first check out of combat; interrupted
call handling and persistence are later tests, not claimed complete.

Entry is gated by the source-backed ending shutdown and idle balanced call state,
plus one-shot mod-owned tracking. This is not an API for inspecting arbitrary
third-party serialized owners; do not combine with another mod that restarts
native phone initializers.

Game-closed recovery uses `tools/deploy_native_padre_u6.ps1 -Mode Rollback` for
only its three additive files. Reload the original pre-U6 snapshot afterward;
removing files cannot rewind native phone state already written into a new save.
