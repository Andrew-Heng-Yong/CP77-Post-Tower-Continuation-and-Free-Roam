# Jason startup 103/104: requested, delivered and applied are different stages

**No safe setup replay/skip guard was established.** The exact native nodes 103 and 104 advance after submitting requests. Neither waits for the vehicle mutation. Their request queue has no node-specific completion receipt. The generic script flags and a missing saved PS key cannot supply that receipt.

This investigation reads the pinned EXE and existing current-script/resource captures only. There were no original-save reads, save parsers, game/process/API calls, runtime edits, builds, installations or new gameplay tests. All earlier observations remain unchanged.

## Inputs and reproducible controls

- EXE SHA256: `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`.
- Current base `final.redscripts` decompile input: `B78043064AE90FB80861B0D885D1C8DBCD22070F1DB71F20664D19F2D83C4AAC`; retained `base.script`: `5DED85C18A0FECFC055CB36E6636F55B6D909865D1393935FC6343DC23111E38`. This is current base source, not an assertion about all modded/live script dispatch.
- Exact native gameplay resource `ep1/openworld/street_stories/sts_ep1_03/phases/sts_ep1_03_gameplay.questphase`: `FE77E2DD110DD0AE72245FFEF3FEF757A56F0B2382E2B3A1B393CD284F5AA7F2`.
- `native_01.json`, `native_02.json`, `native_03.json` retain 61 selected function captures, plus the full local PreSave-record continuation span and actual instance/callback tables. These are selected captures, not 61 distinct complete semantic implementations.
- `reproduce_02/verification_01.json`: **38 source/byte controls PASS**, including four in-memory source-proof mutations. The controls verify 3016 retained instruction records against pinned executable bytes, exact graph payloads/edges, enum values, recipient construction and current methods. They do not execute the engine.

From workspace `C:\Users\Ayong\Documents\cp77 modding\tower ws`, reproduce into a new directory:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr15\event_stage_01\vehicle_events\verify.py' --out-dir 'prealpha\quest_restoration_qr15\event_stage_01\vehicle_events\reproduce_03'
```

The verifier refuses existing result files. `verification_01.json` and `reproduce_01/` preserve the preceding 34-control runs; the current 38-control result is `reproduce_02/`. Capture scripts also refuse overwriting their evidence.

## 103: visual-destruction request

Native `root/1` has `101.Out ->102.In ->102.Out ->103.In ->103.Out ->104.In`. Node 103 specifies `VehicleQuestVisualDestructionEvent`, `accumulate=0`, explicit `PSClassName=VehicleComponentPS`, component `controller`, and the broken-car EntityRef. Although its payload also contains `managerName=VehicleManager`, the explicit successfully resolved PS-class route is the relevant branch; it is incorrect to assume the named legacy manager necessarily handles this event.

Actual EventManager instance table `0x3047DB8`, normal Execute `+0x158 ->0x565B5C`:

1. `0x566160` resolves the explicit class. `0x1817C7C` constructs `PersistentID{resolvedEntityID, componentName+A8}`. The component is therefore **controller**, not componentNone or the native destruction-storage class.
2. The low24-bit dynamic-ID path also checks a class cache. A zero EntityID or rejected cache lookup goes to commonOut. The cache's complete membership is not inferred here.
3. An admitted request calls the actual PersistencySystem virtual `+0x1C8 =0x1A5568`.
4. Common path `0x565C01..C1D` appends literal `Out` and returns0. It is shared by successful queue attempts and rejected/nil routes. There is no acknowledgement wait or node-specific listener registration in this route.

For the **historically associated EntityID candidate 10229047**, the source-bound event-recipient PID key is **6695448052237678836**. This corrects the earlier description of `controller` as merely a guessed component for this event. It does not change the separate native destruction-storage owner: component `vehiclePersistentDataPS`, key **17113219195054135786**. Neither key binds the current loaded actor or proves application.

## Shared PS queue and actor forwarding

`0x1A5568` appends to system `+0x218` a 40-byte request:

| Offset | Content | Stage meaning |
| --- | --- | --- |
| `0x00` | PersistentID 16 bytes | Target entity plus component |
| `0x10` | Runtime class pointer 8 bytes | Required PS type |
| `0x18` | Event handle 16 bytes | Payload to dispatch |

The request carries no quest resource/node identifier, completion flag or acknowledgement handle. This is a property of the inspected record, not a claim that no other system could track a request.

Registered update `0xDAAE14 ->callback table0x394E1E0 ->0xE6EC4C ->0x1A50EC` consumes this queue. `0x1A5160` decrements/pops before `0x1A519F ->0x1A5200` dispatches. Dispatch obtains/creates the requested PS through `0x408DB4`; invalid state/class can drop the consumed request. Generic typed dispatch is `0x1A536C`.

The current `VehicleComponentPS.OnVehicleQuestVisualDestructionEvent` only returns `SendThisEventToEntity` (enum 1). Dispatch follows `0x1A52B3 ->0xE36684`. That function looks up the **current** entity through system `+0x280`; a nil registry/entity returns without enqueuing an actor event. There is no retained fallback request in this inspected branch. Even a found entity can reject `QueueEvent` at `0x1A67B0` for native lifecycle values 6/7; their symbolic names are not inferred here. An accepted event is appended to entity `+0xD8` through `0x1A67D4/0x1A6820`.

Only the actual actor-side `VehicleComponent.OnVehicleQuestVisualDestructionEvent` calls the two native destruction-grid setters. Its generic visual flag remains a different field and is not written by either inspected visual-event handler. Native setter application/idempotence and actor-queue serialization are not established by the script calls.

PS dispatch's later PID-listener notification `0x1A52E0` is generic and can occur after a forwarding attempt that found no actor. It is not a node 103 completion acknowledgement.

**Concrete source counterexample:** an admitted node 103 request advancesOut; the queue consumer later invokes the PS handler, which returns1; current-entity lookup returnsnil; the queue request has been consumed and the actor handler never ran through this route. Out, an empty PS queue and the generic PID notification are therefore compatible with **no visual application**. This is a permitted source route, not a claim that it occurred for Jason's car.

## 104: door wrapper and six child requests

Actual VehicleNode table `0x3047F38`, Execute `0x9A1524`, calls ToggleDoor action virtual `+0x108 =0x18F3D54`. The authored values are doorIDNone, `seat_front_right=1` and `DisableAllInteractions=9`. They satisfy the normal branch checks1<6 and9<15. `native_03.json` also retains the separate cold branch `0x25F98AE..0x25F9998`; no unreviewed enum branch is silently assumed for104.

The normal action creates exact `vehicleToggleDoorWrapperEvent` at `0x18F3E78`, copies action/door/forceScene to its fields, and queues it through the same PS virtual +0x1C8. Native class hash matches `VehicleComponentPS`; the component-name constructor independently matches `controller`. The action returns0 at `0x18F3E61`; VehicleNode's false branch immediately appendsOut at `0x9A164C..667`. Its general asynchronous-handler machinery is **not entered by this normal action**.

Current script processing is:

```text
OnToggleDoorWrapperEvent
  ->OnVehicleQuestChangeDoorStateEvent
    ->DisableAllVehInteractions
      ->QueuePSEvent(this, Disabled for door 0)
      ->...doors 1..5
  ->SetHasStateBeenModifiedByQuest(true)
  ->DoNotNotifyEntity

later child PS dispatch
  ->OnVehicleDoorInteractionStateChange
    ->SetDoorInteractionState
      ->native vehicleControllerPS.SetDoorInteractionState
```

Despite104 naming `seat_front_right`, **DisableAllInteractions loops all six door slots**. The wrapper flag can be true after the six requests are submitted but before this consumer has processed them. The flag is persistent but generic: other wrapper actions also set it, and ResetVehicle/ResetVehicleInteractionState clear it. It is neither a unique104 receipt nor monotonic history.

`GetVehicleControllerPS` explicitly constructs component **VehicleController** for the same entity. Thus historical candidate key **15311582179580628726** is now source-bound as the final door-state owner, rather than merely a guessed spelling. Native registration `0x5E5FE4 ->thunk0xEE2A70` writes each interaction state at controller `+0xA0 +0x40*door`. The script wrapper flag is in the **different controller/VehicleComponentPS** owner. Existing capture03 membership misses for both keys remain valid but stage-ambiguous.

Default vehicle-state processing also issues DisableAllInteractions, and other code can write native door states. Six disabled values alone would establish a state, not uniquely prove104 authored it. No read-only API was called: the relevant PS getters use create-enabled lookup and are not passive diagnostics.

## Save/load, detach and Tower boundaries

The full actual save virtual `+0x138 ->0x2A35150..0x2A35640` is retained, together with loader `+0x148 ->0x59FB28..0x5A0279`. The writer emits its earlier raw `+0xA0` block, then the selected dynamic-ID list and PS2 records from the `+0x48` record map. It emits an explicit zero byte-span length at `0x2A353D2..D7`; each retained PS record contains key, class identifier and serialized buffer/hole metadata. That buffer is PS payload, not a traversal of the live `+0x218` queue. A nonzero reserved span is skipped by the modern loader at `0x59FF5B..7F`; it is not reconstructed as these live requests.

This conclusion uses the complete writer/reader flow **and** the exact PreSave producer, not just a search for offset218. PreSave `0x2A35648` snapshots the record-map keys, schedules a job through `0x21647F0`, and binds callbacks `0x2164F30 ->0x2164A00 ->0x2165040 ->0x2164C10`. The full local continuation `0x2164C10..0x2164D1B` refreshes each record's eligibility/selection and serializes its actual PS class through `0x21650D0 ->0x4B5F70`. It does not drain or serialize the separate request ring. This does **not** prove that a higher-level save barrier never runs the normal update consumer before these hooks.

The live queue constructor `0x5A1588` initializes an empty ring. Actual PersistencySystem destruction `0xA21FF0` calls `0xA21484/0xA21490` on `+0x218`: pending event handles are released and its count is cleared; they are not applied by the destructor. The inspected BeforeWorldDetach/AfterWorldDetach hooks clear/release records, registrations, listeners and current-entity registry pointers; they do not provide a per-request application receipt or an explicit queue +0x218 flush. Whether the engine reuses/destroys this system around a particular load or schedules a final consumer first is outside this bounded lifecycle trace.

Therefore:

- **Source-confirmed:** PS2's own writer/loader does not persist/restore this live request queue. Retained PS property changes survive only when their record passes actual save selection, as already proved in `identity_01/native_pid/flags_lifecycle_01/REPORT.md`.
- **Source-confirmed:** request consumption, generic notifications and questOut can all precede or occur without actor application. Destruction can discard pending requests.
- **Not established:** complete entity `+0xD8` event-queue persistence, every global save/load barrier, or exact Tower cleanup ordering relative to these queues. This report does not equate an empty captured quest QueuedData block with an empty PS or actor queue.
- **Not established:** any current live stage or what happened to this car during the user's Tower transition. The historical associated EntityID and missing saved PS keys do not close that gap.

## Decision and narrow remaining evidence

**Do not add an automatic prepared-entry replay or a skip based on these observations.** There is no approved runtime change here. A reliable discriminator would need either a source-bound durable application acknowledgement for these exact mutations, or an independently qualified stage/ownership transition that makes the original setup safe without guessing whether it ran. Neither was recovered from103/104, these queue records or generic flags.

Further generic fact probes, GetConstAccessToPSObject calls or repeats of JF01/JF02 are not proposed. The new useful result is the exact two recipient/storage bindings and the demonstrated information loss between queue submission and application. Parent-owned quest-handler/event serialization evidence can be combined with this result; its saved markers must still be bound to the actual node and application stage before changing admission.
