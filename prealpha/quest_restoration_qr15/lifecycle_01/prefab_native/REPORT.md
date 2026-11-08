# Native quest prefab lifecycle — bounded static review

This closes the native **lease accounting and asynchronous boundary**, not the current live world's population or persistent-state lifecycle. Normal phase stop cancels both its child-instance prefab ticket and its owning phase-node handler's ticket before returning. The shared loader disables a resolved prefab only after its final ticket releases it. That disable is queued for the world-streaming update; CutControl's Out is not a completed-detach acknowledgement.

No game, debugger, save reader, console, compiler, runtime asset builder or installer was used. All writes are fresh evidence in this directory. Addresses are RVAs in the pinned installed executable, image base `0x140000000`, SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`.

## Exact objects and source bindings

The existing Codeware `src/Red/QuestsSystem.hpp` names PhaseContext `+0x30` as `prefabLoader`, declares the five base phase-handler virtuals, and provides the independently verified PhaseInstance resource/graph/path/children/handler offsets. Generated SDK headers give these serialized fields:

| Type | Field |
| --- | --- |
| `questQuestPhaseResource` | `phasePrefabs +0x50`, array of 8-byte `QuestPrefabEntry { NodeRef prefabNodeRef; }`; `inplacePhases +0x60` is a different resource-reference array |
| `questPhaseNodeDefinition` | `phaseInstancePrefabs +0x70`; unfreezing trigger `+0x80`; asynchronous resource path `+0x88`; `saveLock +0x90` |
| `questQuestPrefabsEntry` | resolved/global NodeRef `+0`, loading mode `+8` |
| `worldQuestPrefabLoadingMode` | `Disable = 0`, `ForceLoad = 1` |

The exact executable binds three distinct objects; they must not all be called the same prefab manager:

| Object | Native binding |
| --- | --- |
| Shared `questQuestPrefabsHandler` / PhaseContext `+0x30` | Type registration `0x169A050`, metadata table `0x32B7780`, ConstructCls `+0xD8 = 0x2CA3338`, constructor `0x697CD4`, instance vtable `0x306F8C0`; QuestsSystem `+0x100` set in `0x697564`. PhaseContext ctor `0x3C7704` obtains it from QuestsSystem `+0x100`. |
| Resource cache/loading object / PhaseContext `+0x38` | Created by `0x697860`, instance vtable `0x306F758`, stored in QuestsSystem `+0x198`. Resource acquisition virtual `+0x30 = 0x21F99D0`, release `+0x38 = 0x34F7C4`. Descriptive cache name here comes from its observed path-keyed resource handles and owner count; no SDK class name is invented. |
| Per-phase-node handler | Created by `0x351930` / ctor `0x350F04`, size `0x88`, vtable `0x3046748`. This is a `QuestPhaseHandler`, not the shared `questQuestPrefabsHandler`. It stores shared loader `+0x38`, coordination object `+0x40`, node key `+0x48`, state byte `+0x50`, ticket `+0x54`, trigger `+0x58`, resource path `+0x60`, prefab array `+0x68`, and weak owner-node handle `+0x78/+0x80`. |

PhaseContext `+0x40` is bound to QuestsSystem `+0x1A0`. It handles the unfreezing-trigger/phase coordination calls observed in the phase handler. Its complete world/population lifecycle is outside this result. `34F170` checks the SDK `saveLock +0x90`; it is not evidence of prefab removal.

## Acquisition: external and embedded phase prefabs

PhaseNode virtual `+0x188 = 0x3519F8` constructs its handler. When resource path `+0x88` is zero it passes `phaseInstancePrefabs +0x70`; with an external resource path it initially passes an empty list and that resource path. Generic factory `0x2B054C` registers the result using PhaseContext virtual `+0x60`; `0x2B0800` installs the handler and calls handler Initialize (`+0x10 = 0x88AFCC`).

For an external resource, Initialize calls `0xDD514C`, which requests the path through the resource-cache virtual `+0x30`, passing a weak-handler callback. A cached resource can call back immediately (`0x21F99E0`); an uncached resource attaches a callback to a resource token (`0x21F98A0..99CF`, including its separately emitted continuation). The response `0xDD53D0 → 0xDD5418` first checks that handler `+0x30` remains enabled, copies **resource.phasePrefabs +0x50** into handler `+0x68`, and updates the owner definition's cached resource handle. With prefabs present it sets state byte 4 and schedules another handler visit; Reinitialize `0xDD5114` switches 4→5 and calls `0xDD5270` to acquire their prefab ticket. Without prefabs it can mark the handler ready directly.

For the embedded array, Initialize directly calls `0xDD5270` when the copied array is nonempty. That routine calls shared loader `0x699F78` and stores its UInt32 ticket at handler `+0x54`. Its retained callback eventually reaches `0x698994`, which checks handler `+0x30`, sets its state byte to 7, and sets readiness through `0x88B6AC`. Handler virtual `+0x48 = 0x3515D8` reads readiness `+0x2C`; PhaseNode Execute `0x34F37C` gates ordinary phase execution on it.

The running child instance also acquires a **separate ticket**. Child factory path `0x2B13F0` calls `0xDAE8FC`, copies the selected array, calls `0x699F78`, and stores the ticket in PhaseInstance `+0x84`. The exact selector is:

```text
if PhaseNode.cachedResourceHandle(+0x48) exists:
    return cachedResource.phasePrefabs(+0x50)
else:
    return PhaseNode.phaseInstancePrefabs(+0x70)
```

This is not `QuestPhaseResource.inplacePhases +0x60`. Any earlier working description of the `+0x84` ticket as an inplace-resource ticket is superseded by this exact selector proof. Likewise, `0x351CA8` returns the cached resource handle from definition `+0x48/+0x50`; `0x351DD0` selects its graph or inline `phaseGraph +0x60/+0x68`.

## Shared ownership and cancellation

`0x699F78` allocates a ticket ID, resolves each input NodeRef through `0x351030`, records its resolved UInt64 ref in that ticket, and maintains a pending-ref array. Shared loader `+0x60/+0x70` holds resolved refs and matching UInt32 reference counts. `0x6996C0` requests desired=true only on 0→1, then increments the count. A second ticket for the same **resolved** NodeRef increments the existing count. Equal text or equal relative references are not independently proven to resolve equally.

Cancel `0x698E24` locks the ticket map, finds that ticket, calls `0x698F24` once per recorded ref, erases the ticket record, then removes its ID from the ready-callback list at loader `+0xA0`. Release `0x698F24` decrements the shared count; while nonzero it returns without disabling. At zero it erases the ref/count pair and calls `0x699498(..., false)`.

`0x699498` keeps the loader's desired-state entry per resolved ref, coalescing a repeated equal state. Changed desired state calls `0x699520`, which appends a 16-byte `{ resolved ref, desired byte }` to the world queue at `+0x2D8` under its lock at `+0x2E8`. It does not wait for a world operation. Reacquiring a ref after its count reaches zero goes through the same native 0→1 path and requests desired=true again. Native sharing is per resolved ref; it does not create a private copy of a native prefab.

Stop cleanup `0x2B1D30` drains synchronous handlers, runs definition cleanup, recursively removes children, cancels child ticket `+0x84` when nonzero, releases the resource path through PhaseContext `+0x38` virtual `+0x38`, then invokes PhaseInstance virtual `+0x150 = 0x34EFAC`. That callback locates its owning PhaseNode and calls `0x34F0D0`, which cancels its handler ticket through `0x34F144 → 0x34F28C`, unregisters the handler via `0x34F2B4`, and releases its cached owner-definition resource when applicable. `0x34F28C` clears the canceled handler's ticket `+0x54` to zero.

Unregister `0x2FCF0C` calls handler Uninitialize (`+0x20 = 0x34F1C0`) before erasing the map entry. Uninitialize cancels the ticket and clears handler `+0x30`. Both late resource response `0xDD5418` and prefab-ready response `0x698994` check this field. Thus an uninitialized surviving handler is guarded against reacquiring its prefab array or becoming ready through these callbacks. This is a bounded callback guard, not a universal race/thread-safety proof.

The resource-cache release at `0x34F7C4` is distinct: it decrements a path-keyed owner count, or erases its resource handle (`0x34F680`). That call is not an acknowledgement that world nodes detached. Definition `+0x58` also has an independent cached-resource owner count (`0x350BF8` acquire / `0x34F330` release).

## World queue, later state and retained registrations

The queue consumer is type-bound to `worldRuntimeSystemWorldStreaming`: registration `0x17B90F0` → metadata `0x338DE20` → ConstructCls `+0xD8 = 0x8B8800` → constructor `0x8B8244`, which writes instance vtable `0x308F3E0` and secondary interface vtable `0x308F3B8` at `+0x48`. Secondary virtual `+0x18 = 0x69B1FC` adjusts back to the owner and calls, in order:

```text
69BC60
69B738   evaluate previous requested states / notify listeners
69B450   drain newly queued desired-state requests
69B2B8
```

Consumer `0x69B450` takes the queue under `+0x2E8`, moves it to a local array (`0x547ACC` clears the source count), releases the lock, and applies entries in array order. It looks up the resolved ref in the existing NodeRef→sector index at `+0x128`. On enable it sets request bits and desired-map `+0x2A8 = 1`; on disable it clears request bits and removes the desired-map entry. Per-sector `0x69A238` changes its requested byte and schedules node-request bits through `0x69A6E0`; `0x69AB30` changes node flags. **This consumer does not erase the NodeRef→sector index.** The separate index is not a live-owner receipt.

State evaluation `0x69B738 → 0x69BA68/0x69B9D0` examines native streaming/node flags and updates state 0/1/2. It notifies weak `IQuestPrefabStateListener` objects at virtual `+0xD8`. Shared loader's exact listener slot is `0x306F8C0 +0xD8 = 0x69A0D8`. That callback maintains its cached ready-ref set at `+0x88`: states 0 and 2 take the completion path, state 1 removes the ready ref. On a ticket's final pending ref it queues its ticket ID at `+0xA0`; later quest update `0x4AD5CC → 0x698FC8 → 0x699064` invokes its retained callback. No SDK names for these callback state values are assigned here. Missing world-index entries can also emit state 2 (`0x69B450`), so ticket readiness cannot certify that an expected object exists.

This establishes an actual asynchronous protocol, beyond a void cleanup assumption. It also establishes its limit: a newly acquired ticket can reuse cached readiness and already materialized support; neither callback completion nor a disable request identifies a fresh prefab generation. The update even evaluates previous state before draining new requests.

The prior saved-graph review separately proved that native CutControl drains the cut destinations' synchronous phase cleanup/unregister before dispatching that CutControl's Out. Combining it with this result supports **release of the cut graph's tickets before Out**, conditional on that exact cut having run. It does not support world-detach completion before Out.

## Usable successor contract and remaining boundary

A successor that uses a normal native PhaseNode with the exact reviewed `phasePrefabs` / `phaseInstancePrefabs` and exact resolved native references can reuse the engine's readiness gate, shared ticket counts and stop cancellation. This avoids constructing a second private world-tree copy. Its lease may legitimately reuse native world objects and their saved persistent state. The engine deliberately keeps support loaded while any other native ticket still holds it.

This is a **native pattern**, not approval to call the reverse-engineered functions directly, invent a scripting API, or start the Jason controller. It is conditional on separately establishing original graph retirement, exact prepared stage, correct root/context reference resolution, shared dependencies and one-time outcomes. No mutation/API wrapper is supplied.

This review does **not** establish when population/spawner registrations, persistent-state components, actor AI ownership, or other listeners have retired. The traced world consumer retains its NodeRef index and changes streaming requests; subsequent community/spawner lifecycle is a separate subsystem. A nil car lookup, stored ID lists, `q307_ep1_killed`, ready ticket, cached definition resource, or source prefab presence cannot supply that missing proof. The new result closes the phase prefab ticket contract; it leaves those external ownership questions explicit.

## Evidence and validation

`native_01.json` through `native_35.json` retain targeted `.pdata` functions, explicit reviewed split/leaf spans and vtable/registration bytes. `queue_candidates_03.json` records the bounded exact-displacement search that yielded producer `0x699520` and consumer `0x69B450`; class identity is then established independently by constructor/vtable evidence. Earlier `queue_candidates_01/02.json` used rejected over-restrictive filters and are retained failure controls, not absence evidence. Every retained instruction and pointer is verified again against the pinned file by `verify_evidence.py`; `verification_01.json` records the checks and limits. No result is a gameplay test or live owner observation.
