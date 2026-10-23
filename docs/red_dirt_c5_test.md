# Red Dirt C5: one disposable two-visit check

Superseded by the installed automatic integration on 2026-09-26. Use
`red_dirt_auto_check.md`; Start/Stop are now read-only. Historical steps below
describe the opt-in test, not the current installed controller.

This is opt-in, not automatic. It adds one native prefab owner and a mod-owned
copy of the original mirror scene. Existing restorations remain installed.
No vanilla quest fact is written. Do not arm other mirror probes here.

Helper revision 2 removes only the opt-in distance limit. It must be installed
with the game closed before following these revised instructions.

1. Load a disposable post-Tower save. Stand in a quiet area outside all vendor,
   mirror and other scene areas. If starting at Red Dirt, leave the bar at least
   70m from the bartender and wait several seconds. From that quiet location run:

```lua
GetMod("PTFR_RedDirt_Mirror").Start()
```

This checks all listed guards and opens a flushed durable log before enabling
the owner. Inspect is not a prerequisite. If NOT READY appears, send that exact
message; never force a fact. Do not treat the four baseline values as a full
guard or quest-ownership pass.

2. Close CET and return to Red Dirt's mirror. Native activation still requires
   its own trigger; remote arming does not start the mirror scene remotely.
   Use Look, one facial expression, and the mirror's Stop action. Walk outside
   at least 15m from the mirror, return and repeat all three actions once.
   Do not teleport during a mirror scene. Do not save.

3. Leave the entire bar area (about 70m from the bartender), wait several
   seconds for the service scene to release V, then run:

```lua
GetMod("PTFR_RedDirt_Mirror").Stop()
```

If refused, finish the mirror action and walk farther away before retrying.
Quit without saving and report whether actions worked on both visits.

If no prompt appears, do not rerun Start repeatedly. At the visible mirror use:

```lua
GetMod("PTFR_RedDirt_Mirror").Observe("no-prompt")
```

Send the output, leave and Stop if possible, then quit without saving.
Never clear an Interrupted value. Logs remain in the installed CET module
folder as `red_dirt_c5_*.jsonl`. Requests count scene requests, not proven
physical uses; compare request/return deltas with the user's action report.
Native counters are not reset by this helper.

Known limits: local player idle checks do not prove universal sq011 ownership
handover; no restored sq011 root is supported by this trial. Additional scope
or dependency changes require diagnosis if the native trigger fails.

Initial trial was blocked before arming: combat=false, scene=true,
workspot=false. The ordinary-bar trace shows Arroyo Near1/Far0 and no drinking
at the reported position; the user confirms the bartender works. This suggests
service-scene participation, not proof of a stuck player or broken bartender.
The former 50m arming limit made clean isolation awkward next to the bar's 55m
departure radius. Revision 2 leaves busy checks, Stop checks, all native files,
and working services unchanged. Do not bypass a persistent scene=true refusal.
