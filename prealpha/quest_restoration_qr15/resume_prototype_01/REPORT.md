# Jason Foreman prepared-entry prototype

The offline prototype distinguishes a pending courier wait from an already consumed one and follows the native approach into the first briefing input. The recorded save projection supplies too little history to select either continuation. [Model results](run_01/result.json)

## Where the quest can resume

`sts_ep1_03_openworld.questphase` enters `root/2:13` to write `sts_ep1_03_start_community=1`. That node separately arms the normal approach wait at `3`, the debug alternate at `12`, and the courier wait at `14`. The preparation fact says nothing about which of those waits subsequently completed.

The normal approach requires `IsInside` for the player, neither driving nor riding as a passenger, and absence of all three vehicle scene restrictions. The route is `3.Out → 4.In → 1.In`. Node `4` updates the original POI to `DiscoveredPhase` with notification. Node `1` emits the terminating output. The typed native output dispatcher at `0x2B393C` returns zero for this exit type. The nested child return path reaches `0xBEC890`, which runs recursive stop before removing the child. That closes the remaining preparation waits. It does not end the parallel gameplay phase that owns the car setup.

Parent output `root:2.Out1` starts both native children `3` and `4`. The prototype follows the briefing selection in `root/4` through the original phone and content gates. It reaches `129.Start 0` for the unmuted call or `45.Active` for the content-blocked message path. It models the original entry conditions as ordered predicate completions. Phone delivery, the separate muted route, later progression, and simultaneous event ordering require separate evidence.

## The courier window matters

The two exact trigger nodes share the shipped gunfight quest prefab. The `0x44` setup records bind the courier area to node `79`, global ID `18161995001983064865`, and the approach to node `82`, global ID `10474260546255922770`. The pinned `AreaShapeOutline` serializer at `0x45E9F0` reads a four-byte count, sixteen bytes per cooked point, and four bytes for height. The prototype uses those cooked points and the recorded setup positions. The default-looking editable JSON squares are irrelevant to this calculation.

The courier outline contains a disk of radius `105.55`. The approach outline fits in a disk of radius `83.12`, and their origins are `3.48` apart. With the authored unit scales and yaw-only rotations, the entire approach footprint fits inside the courier footprint with at least `18.94` units of clearance. The modeled approach Z interval `31.16–66.77` also sits inside the courier interval `11.59–94.89`. The larger volume therefore has a region that can satisfy the courier geometry alone. Navigation, live trigger registration, and callback order were outside this static comparison.

The courier path `14.Out → 15.In` adds one to `sa_ep1_114_toggledoff_force`. A pending wait can add before approach closes the child. After the wait is consumed, restoring it can add again. The counter also gates an existing courier service and its cleanup request. [Courier lifecycle evidence](../review_01/COURIER_ADDENDUM.md)

## Offline checks

| Synthetic history | Model result |
| --- | --- |
| Vehicle setup applied, courier consumed | Rebind the approach cursor alone. The original call input is reached and the courier counter stays at `1`. |
| Vehicle waiting at native node `102`, courier pending | Keep `102` as the vehicle predicate and `14` as the courier predicate. Ordered completions emit the original `103/104` dispatch once and increment the counter from `0` to `1` before the briefing message. |
| Approach completes before the pending courier callback | The terminating output closes the courier window and the late callback adds nothing. The independent car wait remains pending. |
| Force the same courier choice for both histories | Omitting `14` loses the pending increment. Rearming `14` for an already consumed wait advances `1` to `2`. |
| A command may have been submitted but application is unknown | Defer. This case lacks a reliable distinction between pending and applied effects. |

The 24 checks include missing owner or support evidence, changed source wiring, a nonterminating output, a replacement counter write, a relaxed approach condition and an altered trigger placement. The fixture flags for exact instance, retired owner, restored support and the rest of startup are hypothetical prerequisites. `103/104` dispatch in the trace stands for command submission. Their actual application, including work queued by the original actor, remains a separate obligation. [Prior application analysis](../event_stage_01/REPORT.md)

## Gate for a real repair

The actual historical projection still has only `start_community=1` among 55 selected facts and 29 inactive journal entries. Its catalogue omits the courier counter. JF01 separately sampled a counter of `1` with zero cleanup receipts. That reading supplies no per-instance cursor or proof of which queued effects were consumed. The current planner returns `DEFERRED` with an empty cursor list for the retained evidence. [JF01 observations](../observations/jf01_01/REPORT.md)

The modeled cursors refer to native internal nodes. The original main phase exposes only `In1`, so a real adapter still needs a supported way to rebind those exact waits under the correct phase identity. It also needs the actual saved stage, settled old ownership, verified prefab and actor state, and the remainder of the 16 startup branches. The current fix gate stays closed until those prerequisites can be established or a continuation can preserve both histories without deciding between them. [Startup branch matrix](../effect_contract_01/run_01/BRANCH_MATRIX.md)

## Reproduce

From the workspace root with the existing Python 3.14, local Capstone dependency and pinned QR15 inputs, run:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr15\resume_prototype_01\prototype.py' --out run_02
```

The command writes a new `resume_prototype_01/run_02/result.json` and refuses an occupied output directory. The result retains both trigger bindings, source hashes, selected native instructions, the successful synthetic traces and the actual projection's refusal.
