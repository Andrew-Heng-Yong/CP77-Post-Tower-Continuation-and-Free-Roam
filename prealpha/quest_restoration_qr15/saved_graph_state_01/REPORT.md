# Saved graph stores: bounded native semantics

Result: **SOURCE_CONFIRMED_STORE_LAYOUT_AND_LIMITED_NODE_STATE; NO_SAVED_OWNER_STAGE_DECODER_JUSTIFIED.** This investigation read local framework source and static executable bytes. It did not load the executable, attach to a process, call a game API, parse a save, change runtime code, or build/install anything. The parent investigation separately extracted one authentic saved body's ten physical FactsTable arrays; that body is not bound to the currently running session.

All RVAs below apply only to `Cyberpunk2077.exe` SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`, image base `0x140000000`. Full static instructions and xref candidates are preserved in `native_01.json` through `native_29.json`; these are static evidence, not an execution trace. `verification_01.json` verifies selected exact-byte anchors against the file and records input hashes.

## What the ten saved tables mean

The native manager constructor at RVA `0x697F88` constructs ten stores. The manager vtable begins at `0x306FA58`. Its GetFact virtual at offset `0x10`, RVA `0x2B2270`, computes `index-1` and reads pointer `[this + 8 + (index-1)*8]`; its SetFact virtual at offset `0x18`, RVA `0x350E50`, selects the same pointer. The native save function `0x2CD9538` writes ten table children in ascending pointer order, and load function `0x7399BC` reads up to ten in that order. The table serializer at `0x2CD95B4` and loader at `0x739A68` transfer a UInt32 key array and corresponding 32-bit value array without labelling them as owners or phases.

Thus physical child 1 maps to API store 1, through physical child 10/API store 10. QR12's stack traversal visits siblings in reverse order, so its traversal ordinal is `11 - API store index` for this ten-child database. That reverse traversal does not change serialization order. Native storage has ten pointers and a count at `+0x58`; the local Codeware `data[11]` declaration should not be used as a raw native storage layout or an extra eleventh serialized table.

| API store / physical child | Source-confirmed meaning in this investigation | Proof limit |
| --- | --- | --- |
| 1 | Named facts; local Codeware API and the parent's independently checked named-fact hashes agree. | Named facts do not establish executing-owner state. |
| 2 | OPAQUE for present purpose. | Empty in the parent's one saved fixture is not retirement proof. |
| 3 | Persistent disabled-node suppression for `questDisableableNodeDefinition`. | Disabled node is not a retired phase, missing pending handler, released prefab, or historical executed-node receipt. |
| 4 | `questLogicalAndNodeDefinition` input-signal bitmask; accumulates input socket bits, clears when all required inputs arrive; explicit reset also clears it. | A remembered partial AND state is not a generic visited marker or full phase stage. |
| 5 | `questLogicalXorNodeDefinition` latch; accepts only while zero, records the first input socket bit; explicit reset clears it. | A remembered XOR input is not generic progress/retirement or a monotonic receipt. |
| 6–10 | OPAQUE for exact owner/stage purposes. Some key-based setters were located, including condition-result writes to store 7 and separate setters for stores 8/9. Their complete lifecycle was not audited. | No active/pending/retired labels assigned. |

Evidence: constructor/table/vtable in `native_04/06/08/09`; full FNV callers in `native_key_uses_01.json`; logical-node wrappers, getters, registrations and reset methods in `native_24/25/26/28/29`.

## Exact node-key codec

Codeware `src/Red/QuestsSystem.hpp` supplies `QuestNodeKey` and `FactID`; the corresponding native calculation is independently confirmed at `0xC97792..0xC977E1` and `0x2B2140..0x2B2178`:

1. Obtain the current phase's path hash and a node ID. PhaseContext GetKey at `0x2B2224` reads the current phase's `+0x80` hash and copies the requested node ID into the second dword.
2. Form the integer `(uint64(phasePathHash) << 32) + uint32(nodeId)`.
3. Hash its eight **little-endian** bytes with FNV1a32, initial seed `0x811C9DC5`, multiplication constant `0x01000193`. Native FNV helper is `0x1EFA14`.

The bytes are **nodeId32 followed by phasePathHash32**. They are not a raw in-memory copy of the source struct's declared `{phaseHash, nodeID}` fields, whose order is different. A candidate decoder must implement the conversion operator's integer packing.

The native path hash function `0x4E7D4C` reads the UInt16 path array, uses the first UInt16 as an index into seed data at `0x37015B8`, then hashes the complete `size*2` byte array. Seed entry 0 is `0x811C9DC5`, so paths beginning with root element 0 match Codeware's plain FNV1a32 path helper. The meaning/admission of a different first element was not established; do not generalize beyond this proven root-0 case. Native initialization copies the parent path, appends the phase node ID and stores the resulting hash at `+0x80` (`0x2B1FE1..0x2B2030`).

The real outer path/root ancestry for the selected native EP1 instance is still unbound. The parent investigation's candidate-key misses therefore mean only that those tested candidate encodings did not match; they do not establish absent, completed or retired owners. A 32-bit hashed identifier also requires a collision-aware binding to exact source paths, not unqualified reverse lookup.

## Why store 3 is useful but insufficient

Class registration `0x1620A14` names `questDisableableNodeDefinition` and writes its class pointer to global `0x3BCB1D0`. The initialization cast helper `0x2B2424` compares against that global. During phase initialization, the engine reads store 3 using each eligible node key. A nonzero result adds that UInt16 node ID to the sorted set at phase `+0xC8` (`0x2B2115..0x2B21B1`).

During node dispatch `0x2B3AA0`, the same class test and `+0xC8` membership check occur before the node's execution virtuals. Membership returns result 1 without invoking those execution steps (`0x2B3AE5..0x2B3B07`, branch to `0x2B3C6F`). The context method at virtual `0x98`, RVA `0xC976E8`, calls `0xC9773C`, which adds the ID to `+0xC8` and writes store 3 = 1 using the exact codec above.

This proves an execution-suppression state for a bound node. It does not prove why that node was disabled, that it ever dispatched its actions, whether the enclosing phase instance remains in `Children`, whether a pause condition/handler is pending, or whether its community/prefab/world leases were released. The bounded paths did not establish a comprehensive reset/clear contract for this set or store. The local framework's `ResetGraphFact` helper deliberately writes zero across stores 2–10, but that source reset helper is neither a native retirement decoder nor authorization to run it.

## Logical masks have concrete lifecycle semantics

Logical AND registration `0x15C8F18` names the class and writes global `0x3BCAE28`; getter `0x195B770` reads it. That getter and execution wrapper `0x9F1288` share vtable `0x369D710`. The wrapper calls `0x9F136C`. It obtains an input socket index through `0x9F1BA0`, reads store 4, sets that input's bit, and compares with `(1 << inputCount) - 1`; partial input masks are written back, while the satisfied mask is cleared to zero. Reset method `0x1068978` also clears store 4 except in context mode 5. The numeric mode's name was not inferred.

Logical XOR registration `0x1693B5C` names the class and writes global `0x3BCAE08`; getter `0x195B730` reads it. That getter and wrapper `0x14C714C` share vtable `0x369D3D0`. The wrapper calls `0x14C718C`, which refuses a nonzero store-5 latch, otherwise writes `1 << inputSocketIndex`. Reset method `0x1076B10` clears store 5 except in context mode 5. Phase path operation `0x2CA7550` contains a further explicit store-5 zero write; its complete dispatch contract was not promoted into a named operation.

These readers/writers refute treating all graph values as a uniform visited-node catalogue. For example, a zero AND mask can follow successful full input collection, while a nonzero mask can mean only some inputs arrived. The semantics depend on exact node class and lifecycle.

## Decision for the Jason Foreman repair

An offline inventory of the ten tables and a narrowly labelled node-key/mask inspector are justified. **An offline saved owner/stage decoder that certifies native retirement or pending-state absence is not justified by the closed evidence.** Required missing links are the exact saved native root/phase path binding, the pending-handler/queue and restoration contract, and the community/spawner/prefab/ancestor lease lifecycle for the prepared Jason instance. Store 3 and logical signal masks do not close those links, and missing candidate keys cannot substitute for them.

No source-supported non-replaying repair follows from these facts alone. Keep the prepared-state admission deferred. No new gameplay test, fact getter, fact/save edit, compile, package or deployment is requested by this report.

## Reproduction and retained inputs

`inspect_native.py`, `scan_graph_uses.py` and `scan_key_uses.py` are read-only native inspectors. They use the existing local Capstone 5.0.9 package, exact file bytes and PE sections/unwind boundaries; calls/xrefs located by byte-pattern searches remain candidates until their complete containing instructions are checked. Leaf functions without `.pdata` are explicitly marked and decoded through a bounded span, not silently assigned a compiler function boundary. They refuse occupied evidence outputs.

`validate_evidence.py` verifies the selected assertions and seals a fresh verification/manifest. It does not reparse saves or execute any game/framework code. The artifact's source inputs and outputs remain separate from runtime resources and from the parent's one-save extraction.
