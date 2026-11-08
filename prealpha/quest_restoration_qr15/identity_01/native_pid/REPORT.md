# Native PersistentID hash and PersistencySystem2 key contract

**The native hash agrees with the SDK, and PS2 entry IDs are the resulting UInt64 PersistentID keys.** Neither reversed fields nor a separate StubID conversion explains the two prior candidate misses. The first PS2 `Ids` list is a different namespace: UInt32 dynamic IDs selected from the persistence-status table. It is not a list of component PersistentID hashes.

The installed EXE is pinned to SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`, base `0x140000000`; addresses below are RVAs. Only file bytes, existing local source and retained evidence/metadata were read. No save parser, game/process access, native callback, compiler or installer was used here.

**`GetConstAccessToPSObject` remains unapproved as a read-only diagnostic.** Its registered native path permits allocation, state hydration/creation, attachment and initialization. Its name does not make the lookup observational. No call was made.

## Registered lookup and exact field order

Native string **GetConstAccessToPSObject** is at `0x31F24E0`. Registration `0x134A148` obtains that name, supplies handler `0x802424` at `0x134A198..A1B6`, and registers it. Handler `0x802424` parses a 16-byte PersistentID and a separate requested state-class CName, resolves the class through RTTI, then calls `0x408DB4` with its stack boolean set to1 (`0x80253F`).

The concrete `gamePersistencySystem` class is independently bound: registration `0x17341D0` → metadata table `0x332B058`, ConstructCls `+0xD8 = 0x5A14B0` → constructor `0x5A02C8`, which installs instance vtable `0x36343D8`. That table binds lookup virtual `+0x1B0 = 0x408DB4`, save `+0x138 = 0x2A35150`, and load `+0x148 = 0x59FB28`. Old SDK virtual slot numbers must not replace these exact bindings.

Lookup `0x408DB4` checks the first PersistentID UInt64 for zero, obtains entity eligibility from `0x408FAC`, calls hash helper `0x409010`, and passes the returned UInt64 unchanged into its record table at system `+0x48` through `0x409044`. The requested state class is separate metadata; it is not part of the PersistentID hash.

Native hash `0x409010` reads **entityID from `+0x00`**, **component CName from `+0x08`**. These accesses and the entity-status check match local SDK `gamePersistentID.hpp`; no byte concatenation or FNV hash of the whole struct occurs here. Component-name strings become their CName hashes first; the component CName is not the requested PS class's name by definition.

## Native arithmetic and zero handling

All multiplications use their low64 bits and the shift is logical. With `M = 0xC6A4A7935BD1E995`:

```text
if component == 0:
    return entity
t = (M * component) mod 2^64
t = (M * (t XOR (t >> 47))) mod 2^64
return (M * (entity XOR t)) mod 2^64
```

This is exactly the SDK formula, including wrapping **before** the47-bit shift. `hash_controls_01.json` compares a pure arithmetic interpretation of the14 pinned native instructions with an independently written SDK formula across12 controls, including zero, high-bit and overflow cases. No native code was executed.

| Entity candidate | Component CName input | Native/SDK key |
| --- | --- | --- |
| 10229047 (`0x9C1537`) | `controller` (`0x18B8DE5B56F6D021`) | 6695448052237678836 (`0x5CEB02878DB538F4`) |
| 10229047 | `VehicleController` (`0x149307BBD7B0A813`) | 15311582179580628726 (`0xD47DAADE3B1ACEF6`) |

The prior candidate numbers are therefore correct for those exact inputs. Case/component identity remains an input contract.

There are three separate zero rules:

- A zero component returns the entity ID unchanged. A zero entity and zero component hash to zero.
- Lookup rejects a zero entity **before** hashing, even if a nonzero component would produce a nonzero arithmetic hash.
- Table lookup/creation also treats hash0 specially and does not create a normal keyed record. A nonzero pair can mathematically collide to hash0; a control demonstrates this, so hash0 must not be described as uniquely identifying a zero pair.

## Dynamic IDs and the first PS2 Ids list

`0x408FAC` separates IDs with any bits above bit23 from low24-bit IDs. High IDs obtain the static eligibility path (with an additional requested-class flag). Low IDs, including10229047, delegate to `0x2FAC58`; this is **not an unconditional rejection**.

`0x2FAC58` looks up the ID's UInt32 value in system `+0x1E8`, under lock `+0x1E0`. A present row returns flags3, or7 when its value byte at row `+0x0C` has bit0 set. An absent row returns flag1. `0x408DB4` requires flag bit1 (`flags & 2`) before looking up the component key. Presence with a false value and absence are distinct.

Native status method `0x4CB220`, exact virtual `+0x1F0`, returns2 for a nonzero high ID, or a low ID whose row exists with nonzero `+0x0C`. Otherwise it asks the dynamic-ID subsystem and returns0 or1. Thus status2 is not a PS/component existence test. The table's value can be changed independently by `0x2FD6BC`; native callers `0xF78440` and `0x2FD61C` select true/false and update dependent state after a change.

The **first data list** inside the named PersistencySystem2 node is this table's enabled-ID subset:

```text
UInt32 idsCount
UInt32 dynamicIds[idsCount]
UInt32 currently-written-zero field   // meaning not assigned here
UInt32 recordCount
... keyed PS records ...
```

Writer `0x2A352B4..0x2A353CD` scans map `+0x1E8`, reads each UInt32 key at row `+8`, and appends it only when row byte `+0x0C != 0`. It writes the count using `0x2A35018` (fixed four bytes), then count×4 raw bytes. It does not serialize false-valued rows in this list. Therefore absence from `Ids` is not absence from the full in-memory table.

Modern loader `0x59FEDB..0x59FF45` clears/prepares that table, reads the UInt32 array using `0x18F0064`, inserts each ID through `0x2608060 → 0x5A4FB0`, and sets its value byte to1. This is the same table consumed by `0x2FAC58` and `0x4CB220`, not the component-record table. Load selects the modern path at save version205 or newer; the separately pinned fixture's SaveVersion277 satisfies that gate.

The coordinator's retained `save_inventory/capture_01/ps2_ids.json` contains2165 IDs and does not contain10229047. This review reads that metadata only and pins its bytes separately; original save provenance remains the coordinator's extraction evidence. The bounded conclusion is **not included in that historical saved enabled-ID list**. It does not exclude a false-valued in-memory row, later registration, a current actor or state in another system.

## PS2 entry.Id is the component record key

Name helper `0x19225D4` supplies **PersistencySystem2**, hash `0xF586F03EA6BDDC7D`. Save `0x2A35150` and modern load `0x59FB28` both enter that named node using this helper.

The record table used by lookup is the same system `+0x48` used by the save/load loops:

- `0x409154` creates/finds a record using the incoming UInt64 key and writes it unchanged at record `+0` (`0x409275..27C`). For the registered lookup, that incoming value is the exact `0x409010` result.
- Save enumerates that table's UInt64 keys, finds and locks each record, verifies record `+0` equals the key, then checks record flags at `+0x79`.
- For a selected record, save writes **record `+0` as the first UInt64** at `0x2A3548A..494`. It next writes **record `+0x18` as a separate UInt64 class-name hash** at `0x2A35497..4AC`, followed by its serialized data. The class-name hash is not folded into entry.Id.
- Records missing or rejected by the required flag masks `0x01` and `0x04` emit a zero key instead. A zero-key row has no ordinary keyed PS body in this format; it is not proof of no allocated runtime record or no actor.
- Load reads the first UInt64 through `0x5A027C`, skips a zero key, and inserts a nonzero key unchanged into the same table through `0x408BF8 → 0x409154`. It reads the following class name separately and stores it at record `+0x18` (`0x5A0058`).

Therefore the parsed PS2 **entry.Id** is the native UInt64 PersistentID record key, not a raw EntityID, not a CName by itself, not the class ID, and not the table's smaller internal bucket hash. The body's complete property/event schema is not decoded by this review.

## EntityID versus StubID and remaining question

The independent sealed `../entity_origin/REPORT.md` closes the numeric namespace in the actual population route. It traces saved array20 → reserved object array98 → create request's first UInt64 → native CreateStub `0x2FA044` → token `+8`, without a numeric conversion. The fallback EntityID allocator fills the same request field. This result is reused, not re-audited here. Associated10229047 is therefore an **EntityID-domain candidate**, despite being handled by an EntityStubSystem. No extra StubID-to-EntityID transform is justified before hashing it.

That does not make it a current actor or establish which persistent component it owns. The saved row merges reserved and filtered active IDs, and its exact live/save identity is unbound. The two key misses cannot now be attributed to a different native hash, reversed fields or a numeric StubID conversion. They still do not prove that the car has no state: the exact component name, persistence enablement, materialized/selected record, correct fixture/body and other saved systems remain relevant. The saved `Ids` list and the component-key records answer different questions.

## Lookup safety and verification boundary

In `0x408DB4`, the boolean passed as1 by the registered GetConstAccess handler selects a path through `0x409154` that can allocate a record. With no materialized state, the function can hydrate it or create a default object via `0xBED864`, write the PersistentID to state `+0x48`, attach it to the system/record and call initialization methods. These are actual native writes/calls in the captured body. This API is not selected for a new diagnostic, and no live lookup follows from this report.

`native_01..11.json` preserve targeted exact bytes; `hash_controls_01.json` records12 pure arithmetic comparisons; `verify_review.py`, `verification_01.json`, `key_contract_01.json` and `manifest_01.json` pin and verify the registrations, field order, zero rules, dynamic-ID map, named serializer and record-key data flow. No current owner, vehicle visual destruction, door setup, queued-event completion, safe replay or repair is certified.
