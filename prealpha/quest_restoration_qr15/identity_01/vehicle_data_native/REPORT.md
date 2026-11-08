# Native vehiclePersistentDataPS ownership and PersistentID key

The ordinary native vehicle initialization route uses component CName **`vehiclePersistentDataPS`**, not componentNone, `controller`, or `VehicleController`. Its native CName hash is `0xF8B5D41E08E5736F` (`17921463517654119279`). This is established from actual parameter construction, not inferred from the PS class name by convention.

For associated EntityID candidate10229047, the previously verified native PersistentID formula yields key **17113219195054135786**, hexadecimal **`0xED7E5E302C9919EA`**. This is an exact additional key for a captured-data lookup. No live PS getter or original save was accessed here.

## Exact type and owner binding

The pinned EXE SHA is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. `evidence_01.json` records the13 bounded functions and type links; `verification_01.json` passes14 controls.

`vehicleBaseObject` registration `0xEC3E8C` names that literal class and size0xBC0. Metadata table `0x3670030` has ConstructCls `+0xD8 → 0x10A63DC`, which installs actual instance table `0x317BB80`. Its virtual `+0x160 → 0x593118` is the initializer containing the vehicle-data lookup. The separate ordinary constructor `0x23591C` installs the same instance table.

`vehiclePersistentDataPS` registration `0x16DDA58` names the exact native class and size0x220. It binds metadata table `0x32EA648`, ConstructCls `+0xD8 → 0xDD73C8 → 0xDD73D0`, and type global `0x3BC8160`.

Name helper `0x9A2498` returns literal CName hash `0xF8B5D41E08E5736F`; its spelling matches both the class-registration string and an independently calculated FNV1a CName value.

## PersistentID parameter construction

Initializer `0x593118`, at `0x593211..0x593234`, builds the16-byte lookup key explicitly:

```text
PersistentID.entityID = [vehicle + 0x48]
PersistentID.componentName = 0xF8B5D41E08E5736F  // vehiclePersistentDataPS
```

It obtains the exact PersistencySystem interface through `0x256F2C` and calls `0x9A2514` with that PersistentID. The returned state handle is stored at vehicle `+0x538`.

`0x9A2514` keeps the PersistentID pointer as the R8 argument, separately loads the requested state class from global `0x3BC8160` into R9, sets its stack create argument to1, and calls PersistencySystem virtual `+0x1B0`. The class argument is separate from the component CName, even though this concrete route intentionally supplies the same class's name as the component.

Other native consumers corroborate the same component convention: `0x9A2428/0x2B9ED90 → 0x9A24E4` constructs a PersistentID from the supplied stub's EntityID field `+0x40` and this same CName, then reaches `0x9A2514`. No raw-entity-only key appears in these inspected vehicle-data routes.

The shared native lookup can create, hydrate, attach or initialize persistent state, as established independently in `../native_pid/REPORT.md`. It remains unsuitable as a passive diagnostic. No such API call was made.

## What this does and does not establish

The SDK `vehicle::PersistentDataPS` describes a native destruction-state block at `+0x100`, unlike the generic script `m_visualDestructionSet` flag. The current class size and constructor writes corroborate the native class layout, but this review does not decode a saved property body or certify grid contents. A meaningful saved-state investigation must first find this exact key, verify its class and fixture/body association, and distinguish explicitly serialized fields from defaults.

A miss for key17113219195054135786 still would not prove that the current car has no PS or incomplete setup. Entity10229047 came from a historical merged reserved/filtered-ID row; its current loaded-body identity and persistence eligibility remain separate contracts. No visual-destruction, door-setup, queued-event or graph-owner completion receipt is established. The earlier two guessed-component misses and raw-entity miss do not replace this newly source-bound key.

No gameplay repair, skip or replay follows from this key alone. All work here reads pinned file bytes and retained evidence; game calls, original-save reads and runtime/build/install/save writes are zero.
