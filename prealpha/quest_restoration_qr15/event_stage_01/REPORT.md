# QR15 — saved handlers and vehicle/door event stages

**No reliable completed-setup marker was established in the inspected saved handler/event structures. A replay-free repair is not justified for this prepared Jason Foreman fixture.** This is a source-confirmed limitation of the reviewed evidence, not proof that the native gig is broken or that all saved systems are fully decoded. No runtime change, successor package, deployment or additional manual test is selected.

## What the saved quest structures actually retain

Only nine exact child blocks of the already pinned historical AutoSave-8 were extracted, totaling374,629bytes. The source, metadata and reader hashes match the preceding identity investigation. Ten offset/node-ID controls and complete managed-versus-raw comparisons of the path and event arrays passed. No complete decompressed save or playable save was written. [Capture manifest](components_01/manifest.json).

| Evidence | Verified result | What it cannot establish |
| --- | --- | --- |
| `customArray` |112,318UInt16 words decode completely to13,112interned phase paths. Five belong to the original Jason subtree, including startup and preparation. Native phase initialization interns these paths; ordinary cut cleanup leaves them cached. | Active owners, pending commands, or completed visual/door setup. This is a path registry, not an active phase tree. |
| Saved `eventManager` |8,924slots, including5,148blank slots. Native registration uses a type token and parent phase/node address. Removal overwrites that identity with a blank sentinel and reuses the slot later. | Whether an erased handler finished before the cut or was cancelled while pending. |
| Jason descendants | No retained event row matches any of the five exact original Jason phase contexts. Target hashes have no collisions among the captured registered paths. | Never-entered or completed history. |
| Original ancestor route | Eight exact parent-context/PhaseNode pairs were queried from pinned source ancestry. Only EP1's outer `[1]` node0 retains a matching registration; the seven downstream route nodes, including the actual parent-context node19, do not. | Past node103/104 application or current physical world-detach completion. |
| `QueuedData` | Both retained lists are empty in the exact9-byte child. | No past dispatch, or equivalence to the separate PersistencySystem command queue. |
| Saved debug text |28managed-parsed lines; these are selected diagnostic messages, not an exhaustive visual/door event receipt stream. | A negative completion result merely because a message is absent. |

[Native lifecycle and restoration evidence](quest_handlers/REPORT.md), [raw-component analysis](analysis_01.json), [exact ancestor query](ancestor_membership_01.json), [native-width query and controls](native_layout_01.json).

The native event record is `{typeToken UInt64, phaseHash UInt32, nodeID UInt32}`. WolvenKit splits the final UInt32 into two UInt16 properties. The initial raw query used the low half; all current high halves are0, so its current results remain correct. The authoritative successor compares the full UInt32. A mutation of the high half of a real matched record is rejected by that query and would fool a low16-only query. This is a metadata-query correction, with no runtime change.

## Dispatch does not certify application

Exact startup node103 is an EventManager dispatch targeting the broken car's `controller` component and VehicleComponentPS. Its native implementation advances Out after attempting dispatch, including failed/unresolved attempts. The separate PersistencySystem queue is consumed before PS dispatch. The script visual handler asks to forward the event to the current entity; a missing current entity can end that forwarding path. None of those operations supplies a durable acknowledgement that the native destruction grid was applied.

Exact node104's authored enums select the ordinary ToggleDoor path. It queues `vehicleToggleDoorWrapperEvent`, returns the immediate path and advances Out without waiting for the nested door actions. The current script wrapper queues six DisableAllVehInteractions changes and then sets its generic `m_stateModifiedByQuest` flag. Each later per-door handler writes the native door interaction state. That flag therefore cannot certify that all six changes finished, nor certify the specific visual event.

The three relevant state addresses are now distinguished by source, not by guesses:

| Component for EntityID10229047 | Native PersistentID key | Role |
| --- | --- | --- |
| `controller` |6695448052237678836 | Visual/door wrapper recipient and generic modified-by-quest flag. |
| `VehicleController` |15311582179580628726 | Final native door-interaction state owner, reached by the current PS script. |
| `vehiclePersistentDataPS` |17113219195054135786 | Native vehicle destruction-state storage. |

The previous verified global PS2 capture has no serialized nonzero entry under any of those keys. Its native selection/filtering proof still prevents interpreting those misses as “never applied.” No new PS getter is called; GetConstAccessToPSObject remains unsuitable as an observational command.

[Exact vehicle queue, save lifecycle and source controls](vehicle_events/REPORT.md), [current-script contract](vehicle_events/source_contract_01.json), [preceding saved-key and filter proof](../identity_01/REPORT.md).

PersistencySystem's own save/load and PreSave-record paths do not serialize its live request ring. This is not a proof about every higher-level save barrier: the engine could run an ordinary consumer first. Actor event-queue persistence and exact Tower scheduling relative to both queues also remain unproved. No live PS/actor queue was captured, and an empty saved quest QueuedData block is not an empty-PS-queue observation.

A [narrow scan of the current registered REDS](registered_override_scan_01.json) reuses the148-source registration census without compiling. The scoped names match only six native vehicleControllerPS field-exposure annotations in Codeware; no named event-method override was found in those sources. This literal scan does not certify an executing modded cache or dynamically injected hooks.

## Repair decision and remaining limits

The candidate indicators fail for specific reasons: paths outlive owners, handler identities are erased on removal, Out means attempted/queued rather than applied, the wrapper flag precedes final actions, and selected PS state can be absent from the save independently of setup history. Empty queues do not recover a past delivery result. A standalone admission exemption or a fresh rerun would bypass these missing contracts rather than repair them.

`nodeInstanceDataManager`'s eight records and the other captured support/freezer/scene/listener blocks remain explicitly limited or OPAQUE for setup-stage interpretation where their exact subtype semantics were not established. No complete saved-state-absence, full-save-equivalence or universal impossibility claim is made. This historical body is still not bound to the body loaded during JF01/JF02, and static serialization evidence is not current executing-owner proof.

A repair requires either positive, source-bound stage evidence tied to the genuine instance, or a continuation proven to preserve both possible histories. It must also preserve every startup branch, original saved identities, native outcomes, existing U9/HS1 fingerprint and the shared courier's non-exact increment/cleanup lifecycle. No such complete contract was established here. Keep this prepared state deferred; do not reset facts, fabricate a receipt, force the gig, replay setup, or call mutating APIs to observe it.

No JF01/JF02, Ronald enrollment/reload, Jeopardy, Bullets/Jinguji/Zane, Wilson, Cynthia or D00E repeat is requested. There is no new special gameplay action to perform.

## Verification and preservation

The raw reader has13malformed-component controls. Native-width membership has7controls, including the high-half mutation. These are framing/address checks, separate from native source checks, extraction equality and any gameplay result; overlapping counts are not summed into quest coverage. No repair failing-before/passing-after result is claimed because no repair is selected.

`preservation.json`, `completion.json` and `verification.json` record the exact final readback and updated continuation pointers. The unchanged Core's existing compile and consolidated-package evidence is reused. No compiler, archive/ZIP builder, game launch, CUA, process attachment, installer, save/fact writer, release, publication or push is used.
