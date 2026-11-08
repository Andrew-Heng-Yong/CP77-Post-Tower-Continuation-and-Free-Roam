# Jason Foreman earlier-save evidence

The **October 26, 4:05 PM AutoSave-16 backup** contains Jason’s original approach wait and eleven other registrations in its quest subtree. This is a genuine positive example of a saved prepared instance. It gives the continuation work a concrete restoration record to study. The save used for the blocked session still needs its own exact file binding. [Results](analysis_02/result.json)

## What the older bodies retain

The read-only capture inspected seven distinct bodies selected from the existing inventory by exact slot, timestamp, source path and both body and metadata hashes. All seven have `sts_ep1_03_start_community=1` and `sa_ep1_114_toggledoff_force=1`. They retain the same five Jason phase paths in the path catalogue. Six have zero retained Jason descendant slots. AutoSave-16 has twelve. Every earlier body retains three upstream typed phase registrations. The previously captured historical post-ending AutoSave-8 retains only the outer EP1 registration among those queried.

| Body | Saved game format | Jason descendant slots | Approach / courier / vehicle wait slots |
| --- | --- | ---: | --- |
| ManualSave-9, October 8 | 2310/269 | 0 | — / — / — |
| AutoSave-3 and AutoSave-14 backups, October 12 | 2310/269 | 0 each | — / — / — |
| PointOfNoReturnSave-0 and PointOfNoReturnSave-1, September 6 and 20 | 2310/269 | 0 each | — / — / — |
| WA1 AutoSave-8 backup, October 26 | 2500/277 | 0 | — / — / — |
| **WA1 AutoSave-16 backup, October 26** | **2500/277** | **12** | **9379** / — / — |

The dashes mean the saved registry contains no matching row. The same preparation flag, courier counter and interned paths occur on both sides of the observed registration difference. Those scalars and cached paths alone cannot choose a resume plan. The inventory's matching playthrough metadata is a lead for comparison. It does not establish an uninterrupted chain to the user’s blocked session.

## The positive record

The saved resource array places `ep1\quest\ep1.quest` at index `1`. Actual source phase hops bind approach node `3` in `sts_ep1_03_openworld.questphase` `root/2` to phase path `[1,0,10,5,2,50,19,6,2]`. Saved slot `9379` has the matching phase hash, full 32-bit node ID and type token `0xA135C358CCDC56C9`.

The first address check expected a `questPauseConditionNodeDefinition` token and correctly stopped on the mismatch. The pinned native instance table shows that this node’s type virtual `+0x180` delegates to its condition’s virtual `+0x118`. For this wait that is `questLogicalCondition`, whose CName is the exact saved token. The same tracing binds the courier trigger type and the vehicle-spawned subtype. The corrected query verifies the saved condition token, full node ID and unique phase-path binding. [Native checks and node bindings](analysis_02/result.json)

AutoSave-16 also retains the native gig parent, both gameplay and openworld child phase registrations, the phase’s merchant wait, seven gameplay startup waits at `16, 30, 33, 92, 98, 133, 135`, and the authored debug alternate at openworld `root/2:12`. All twelve descendant rows resolve to exact graph nodes. The inline `root:2` wrapper has no saved slot even though the approach and debug child records are present.

A targeted reread of the same body reproduces the resource array and both registry blocks byte-for-byte, with the same selected fact values. The nine-byte quest `QueuedData` contains zero resource requests and zero handler notifications. Thus the approach registration has no queued notification in that saved quest component. Separate actor and persistency queues and the final vehicle setup remain unresolved. The courier counter was already `1` and there is no retained courier wait. This supports the consumed-courier test case without proving the precise writer or every intermediate action in the user’s current history.

## How this advances the repair

The current native restore path resolves retained slots through the phase-path catalogue, dispatches the exact node path in restore mode, and reuses the saved registration slot. AutoSave-16 supplies an authentic input for evaluating that path. The historical post-ending comparison has lost those Jason slots. A repair after the cut still needs evidence from the actual blocked body and a supported way to restore the intended waits without creating a second owner or repeating completed setup. [Native restore lifecycle](../event_stage_01/quest_handlers/REPORT.md)

The positive snapshot does not establish the final car visual or door state, all sixteen startup dispositions, or the exact current support lease. The original preparation route stays deferred until these conditions can be bound or a continuation can safely preserve the unresolved histories.

## Reproduction

The capture uses the pinned QR12 inventory and WolvenKit 9.1 reader, and refuses altered inputs, linked paths and occupied outputs. It keeps only the selected quest spans and named facts. All seven resource arrays decode exactly. Two malformed registration controls reject a changed high node-ID half and a wrong type token. Retained earlier native donors match the current source bytes for six of the seven queried resource depots. The older `ep1_open_world.questphase` provider is outside that donor comparison.

The recorded PowerShell captures used `capture.ps1` with `-Group before_tomorrow -OutputName capture_01`, `-Group remaining_leads -OutputName capture_02`, and `-Group positive_wait -OutputName capture_03`. To verify the retained captures from the workspace root with Python 3.14:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr15\earlier_saves_01\analyze.py' --out analysis_03
```

The command replays the recorded `capture_01` through `capture_03` evidence and writes its result to a fresh directory. The first passing analysis `analysis_01` records the typed wait queries. `analysis_02` adds the full descendant mapping and the targeted quest queue check.
