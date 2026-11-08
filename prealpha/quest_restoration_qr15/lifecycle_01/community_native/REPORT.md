# Exact native CommunitySystem lifecycle evidence

This investigation reads the pinned Cyberpunk2077.exe as bytes. It does not load executable code, call the game, change saves, or change runtime resources. The EXE SHA-256 is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`.

The authoritative outputs are `capture_01.json`, `supplement_02.json`, `schema_02.json`, and `verification_02.json`. The last file passes 30 independently specified byte, slot, identity, schema and mutation controls. The older `verification_01.json` intentionally remains: its only failure was a hand-counted raw-name offset of50 instead of51, corrected in fresh run02. This was an evidence-control mistake, not a game failure.

## Instance identity and ordinary activation

The earlier metadata-table interpretation is superseded. `gameCommunitySystem` registration `0x16CDD44` constructs RTTI metadata with table `0x32DEB60`. Its `CClass::ConstructCls` slot `+0xD8` points to `0xC2DC74`, which forwards to the actual instance constructor `0xC2DF6C`. That constructor installs instance table `0x30D3A18`.

The actual instance slots are GetSpawner `+0x260 → 0x38360C`, Activate `+0x1D8 → 0x36E344`, Deactivate `+0x1E0 → 0x36E388`, and Reset `+0x1E8 → 0x2BCD5F8`. The latter three check registry membership and queue opcodes2,3,4. Membership is not a readiness or active-state check.

The update callback is registered through instance `+0x108 → 0xDABF78`. Its queue job reaches `0x71EDD0 → 0x71EE6C → 0x382CF0`. Opcode2 resolves the actual registry object and reaches `0x9CEFB8`. That complete ten-instruction body:

1. Returns when object byte `+0x11` is zero.
2. Returns when object byte `+0x10` is already nonzero.
3. Otherwise sets `+0x10` to1 and calls object virtual `+0x38`.

Therefore ordinary Activate does not call the activation virtual again for an already-active initialized object. This is a precise idempotence result for that operation, not a proof that an entire quest setup route, visual-destruction event, door command, or inactive historical encounter can safely be replayed.

The exact native `questSpawner_NodeType` path `0x36DFD0 → 0x36E038` first resolves its contextual NodeRef and requires an existing spawner object. Enum1 Activate calls only system `+0x1D8`. Enum3 Reactivate calls Deactivate `+0x1E0` and then Activate. Enum4 reaches Reset `+0x1E8`. These paths must remain distinct.

## Typed population-spawner allocation and returned pointer

`worldPopulationSpawnerNodeInstance` registration `0x16CF404` has ConstructCls `0xFA6858` and instance table `0x36773C0`. Initialization `0x383F0C` constructs the exact vehicle-spawner configuration and calls CommunitySystem virtual `+0x2C8 → 0x3840D4 → 0x3840E0`.

Registration allocates0xC0 bytes through `0x383EAC`, calls constructor `0x384470`, and keeps the allocation base unchanged. The constructor stores the GlobalNodeID at `+0x08`, clears the active/initialized word at `+0x10`, and returns the original pointer. `0x1F5544` wraps that pointer. Registry insertion `0x3847B4 → 0x38484C → 0x18F068` moves the same pointer pair. GetSpawner `0x383660` returns that map value unchanged; its facade only moves the pair through `0x26117FC`. The action consumer `0x382DA8` obtains that same allocation pointer. There is no eight-byte base adjustment in this chain.

The corroborating local `Red::Spawner` source declares active/initialized at `+0x08/+0x09`; that declaration is stale relative to this native object. This does **not** establish an installed Codeware defect. The separate installed-binary review must decide its actual implementation. JF02 returned nil, so it never read wrapper flags or arrays.

## Exact saved-row schema

Actual instance `+0x130 → 0x2BD3C30` prepares a save. Its spawner helper `0x2BD3CDC` copies the saved/unregistered map and enumerates live registry `+0x2028`. `0x2BCED84` then copies actual object active byte `+0x10` into saved-row byte `+0x46`. This is saved activation intent at the captured save, not initialized state, private-graph ownership or present liveness.

Actual Save `+0x138 → 0x2BD3A48` and Load `+0x148 → 0xA5C5BC` establish two map groups followed by three auxiliary lists and one final list. All array counts are fixed little-endian U32: helper `0x3EAA6C` sets transfer size4. They are not VLQ counts.

`schema_02.json` records the exact ordering and version gates. For save version277, a spawner row contains:

- U32 count, U64 entries for memory array `+0x00`.
- Raw2 bytes from `+0x42`, raw1 byte from `+0x46`.
- U32 count, U64 entries for array `+0x10` (version>=1).
- Raw2 bytes from `+0x40` (>=15), raw2 from `+0x44` (>=143).
- U32 count, U64 entries for array `+0x20` (>=180).
- U32 count, raw16-byte entries for array `+0x30` (>=254).

The first outer map was partially consumed by WolvenKit: its count and U64 keys are known. Its remaining rows each have an inner map with those rows plus a name after each inner row. `0x27A7C4` supports two name formats depending on the stream dictionary. The actual pinned save tail contains literal signed-length ASCII names (`0x87` plus `default` at offset51); it uses the no-dictionary branch `0x2444600/0xB9E560`. Native independent encoder `0x2F60040` and decoder `0x27B824` establish the signed VLQ length encoding. A positive length enters the separate Unicode reader; a parser must support its exact encoding or fail closed. Do not substitute dictionary U16 indices.

Do not stop component verification at the second map. The exact remaining sections are recorded in `schema_02.json`; they come from `0x2BD693C/0x2BD6898` and the final instructions of `0x2BD3A48`. Unknown scalar bits remain raw; a transfer width does not prove a gameplay label or signed interpretation.

## Decision boundary

These results remove two concrete uncertainties: ordinary already-active Activate is idempotent, and a strict saved CommunitySystem reader can identify the car's persisted activation without guessing from an isolated hash hit. They do not establish current prefab registration, graph-owner retirement, VehicleSpawned condition behavior, or safe replay of visual destruction and door setup. No gameplay repair is approved by this evidence alone. No new manual test is requested here.
