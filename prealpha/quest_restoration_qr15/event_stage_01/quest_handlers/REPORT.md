# Saved quest handlers: exact projection and completion limits

**The decoded quest structures do not supply a reliable Jason103/104 completion receipt.** The saved handler registry retains registrations for restoration, and normal removal erases their identities. A pending handler cancelled by a cut and a handler already finished before that cut can therefore leave the same missing-registration result. The phase-path catalog survives this removal and is not an active-owner list. This conclusion is limited to the structures decoded below; other saved components remain opaque for stage evidence.

Only native file bytes, local SDK/framework source and the coordinator's retained component files were read. EXE SHA256 is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`; addresses are RVAs. This review did not reopen a save, call a parser/game API, access a process, build or change runtime files.

## Actual serializer ownership

QuestsSystem instance table `0x30BCE78` binds prepare/save/load virtuals `+0x130 = 0x2C9F5A0`, `+0x138 = 0x2C9F364`, and `+0x148 = 0x739578`. The save holds the already reviewed system lock `+0x60`. Named children are directory/open-close scopes, not inline strings to scan for.

| Child | Native owner / writer / loader | Meaning established here |
| --- | --- | --- |
| `QueuedData` | System fields `+0x130` and `+0x158`; `0x2CA0568` / `0x7392E4` | Pending resource-acquisition request keys and queued handler-slot notifications, described below. |
| `customArray` | System `+0xB8`; outer writer / `0x73A0D0` | Interned complete UInt16 phase paths. |
| `eventManager` | System `+0xE8`; outer writer / `0x73A024` | Reusable handler-registration slots. |
| `nodeInstanceDataManager` | System `+0xF0`; `0x2CD3208` / `0x739EEC` | Fixed16-byte record framing only; key/data meanings remain OPAQUE for stage. |
| `questPrefabsHandler` | System `+0x100`; `0x2CA3348` / `0x739D2C` | Lease manager separately reviewed; this saved schema is not decoded as a103/104 receipt. |
| `questPhaseFreezer` | System `+0x1A0`; virtuals `+0x90/+0x98` | Coordination state remains OPAQUE for103/104 stage. |
| `questDebugLogManager` | System `+0x2C8`; name helper `0x738A4C`, string writer `0x27CAB4` / `0x739C80` | Saved text; no complete, durable event-history contract established. |
| `questSceneDataHelper` | System `+0x190`; virtuals `+0x30/+0x38`, writers `0x2CD9EC4` / `0x7397AC` | OPAQUE for103/104 stage. Its buffer is not reclassified as a completion log. |
| `playerObjectListenerMapper` | System `+0x110`; `0x2CD264C` / `0x438048` | OPAQUE for103/104 stage. |

The earlier progress message calling `+0x190` debug was incorrect. The exact child-name helpers and outer call order above correct that label; no debug-history inference from the scene helper is retained.

## customArray is path interning, not the registered phase tree

Constructor `0xB26624` installs the actual QuestsSystem table and sets the custom-array record-header size to **one UInt16** at `0xB266AB` (`this+0xC8`). CreateContext `0x2B30A0` passes system `+0xB8` into QuestContext field `+0x20` through constructor `0x2B3150`.

PhaseInstance.Initialize `0x2B1F40` builds its complete path, then uses that context pointer at `0x2B2046`. Lookup `0x8F86A0` searches for the path. If missing, `0x2B2063..20BA` extends the array, writes its UInt16 length, copies the UInt16 path words, and updates the auxiliary index. This occurs during initialization; it does not establish dispatch of an event node inside that phase.

The native child body after its four-byte NodeID is:

```text
UInt32 totalWordCount
repeat until exactly totalWordCount words are consumed:
    UInt16 pathLength
    UInt16 path[pathLength]
```

Writer `0x2C9F3F9..428` writes the total count and count×2 raw bytes. Loader `0x73A0D0` reads that same framing and marks the index dirty. Reload callback `0xCC57C0` invokes `0x4E7EBC`, which reindexes the records and recomputes native phase hashes into system `+0x78`.

The exact stop chain previously established in `saved_graph_state_01/inspector_review_01/` removes Children and Handlers, cancels phase work and releases its support tickets. It does not delete the interned path records in this chain. The whole-system destructor separately destroys `+0xB8` (`0xB265E4..5EB`). Thus a retained catalog path is compatible with a stopped/unregistered phase. This is not a claim that no other lifecycle operation can replace/reset the catalog.

## eventManager is a reusable handler-slot registry

Generic node handler registration `0x2B054C` calls definition virtual `+0x188` to create a handler, then `+0x180` for its type/name CName, and PhaseContext virtual `+0x60`. Actual `0x2B0800` obtains the current phase/node key, registers it through `0xEB6B3C`, assigns the resulting slot index to handler `+0x28`, installs the handler in phase `+0x98`, and calls Initialize.

`0x35187C` supplies the actual definition class CName from its RTTI metadata. `0x2B2224` supplies the key as two UInt32 fields. Consequently each serialized16-byte row is:

```text
UInt64 definitionTypeCName
UInt32 phasePathHash
UInt32 nodeID                 // actual IDs are zero-extended UInt16
```

The last two bytes in the managed `U64,U32,U16,U16` framing are the high half of nodeID32, not an independently named state flag. The packed key here is its in-memory `{phaseHash,nodeID}` layout; it is not the differently ordered hashed FactID codec.

Registration `0xEB6B3C` pops a free slot index and overwrites its full16 bytes, or appends a new slot. Save `0x2C9F468..491` writes a fixed UInt32 high-water slot count and all count×16 bytes, including cleared slots. Loader `0x73A024` restores this exact array.

**Removal destroys the slot's identity.** PhaseContext RemoveHandler `0x2FCEAC` retrieves handler `+0x28` and calls `0x2FCFD0` before calling `0x2FCF0C` to uninitialize/erase the phase's handler. `0x2FCFD0` writes type0, phaseHash0, nodeID32 `0x0000FFFF`, then appends that index to the free list. It does not retain the removed key or a completed/cancelled distinction. The previously proven CutControl FIFO/recursive-stop chain reaches this removal synchronously before its Out branch; external world acknowledgement remains separate.

Reload callback `0xCC5844` rebuilds the free list from rows with phaseHash0 or nodeID32 `0xFFFF`. Restore preparation `0x2B26A4` skips those rows, resolves each remaining phase hash through the rebuilt path map, and appends its node ID to the full path. After resource preparation, callback chain `0x14D459C -> 0x14D4640 -> 0x156EFD0 -> 0x2B32B0` dispatches those paths through root virtual `+0x130` using context mode2. Registration in mode2 finds the saved slot with `0x79CF00` and reuses its index. These are restoration registrations; a present row does not independently certify scheduling, actor application or completion.

## QueuedData is not an actor-event acknowledgement log

For the current native version, `0x2CA0568` writes:

```text
signedVLQ resourceRequestCount
UInt64 resourceRequestKeys[resourceRequestCount]
UInt32 handlerNotificationCount
UInt32 handlerSlotIndices[handlerNotificationCount]
```

The first sequence comes from pending objects' `+0x30` keys under system lock `+0x128`. Load `0x7392E4` passes each key back through system virtual `+0x1F0 = 0x2CA04E4`, which requests it from the resource cache `+0x198`. Nonempty decoding must retain the native signed-VLQ/version guards; no generic decoder beyond the observed empty case is selected here.

The second sequence is system `+0x158` under lock `+0x150`. The common handler notification path `0x88BB74` uses its assigned slot index; its EventManager endpoint `0x88BC48` forwards to system virtual `+0x200 = 0x88BC58`, which appends that UInt32. These are quest-handler notifications, not the separate persistency/actor event queues receiving103/104 commands.

## Bounded historical-body result

The coordinator's `../components_01/manifest.json` pins nine selected child spans from body SHA256 `AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E`, with unchanged source/metadata and12 offset/raw-vs-managed controls. This review reads only those retained bytes/metadata.

The completed framing analysis records112,318 path words /13,112 catalog paths,8,924 handler slots and8 opaque node-instance records. All five Jason catalog paths remain present, while no slot matches their phase hashes. The separate source-bound ancestor query checks all eight parent-context/PhaseNode pairs; only `[1]` node0 has a saved row, and none of the seven deeper owner addresses does. No relevant catalog hash collision was found in that query. These are historical serialized-membership observations, not current loaded-body/liveness or application results.

QueuedData has exactly nine bytes: its four-byte node ID, zero VLQ resource-request count and zero UInt32 notification count. Both queues are empty in this projection. This says nothing about pending events in other systems. Saved debug text has no Jason receipt; absence of text is not proof that an event did not occur.

Exact node103 type binding is independently established here: registration `0x168EBBC` -> metadata `0x32AED58`, ConstructCls `+0xD8 = 0x352840 -> 0x352770`, actual definition table `0x3047DB8`, Execute `+0x158 = 0x565B5C`. Its inspected execution attempts dispatch, emits Out and returns0 without a handler-factory wait; unresolved-target paths also reach Out. This is not an actor-application acknowledgement. Node104's exact vehicle/action and separate PS command route are reviewed in `../vehicle_events/`; no broader no-wait claim for every VehicleNode action is made here.

The `+0xF0` nodeInstanceDataManager is distinct from the handler registry. Its eight raw records have known16-byte framing but unclosed semantic keys/data and reset/retention rules. No dedicated `+0xF0` operation appears in the inspected103 execution body, but this is not an exhaustive exclusion of indirect/outer dispatch or listener writes. The freezer, prefab, scene-helper and player-listener projections likewise remain OPAQUE for103/104 completion. This report therefore does **not** claim complete event-stage absence across all saved structures.

A node103/104 event already dispatched, an original pending handler later cancelled, and other histories can leave no identifying handler row after cleanup. The decoded registry/queues/path catalog do not distinguish those histories. They cannot justify replaying or skipping startup. Other saved graph/event systems may differ; no full-save equivalence or universal information-loss claim is made.

`verification_01.json`, `schema_01.json` and `manifest_01.json` seal exact bytes, native slot/format controls and preserved source pins. Exploratory captures include generic helpers/neighboring code not used as lifecycle evidence. No runtime repair or new manual test is proposed.
