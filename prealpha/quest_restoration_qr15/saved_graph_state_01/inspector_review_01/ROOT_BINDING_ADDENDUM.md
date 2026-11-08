# Saved root binding and SaveVersion closure

This addendum closes two of the earlier review's bounded unknowns. It does not change the blocked live-inspector readiness result or certify pending/world-owner state.

The parent investigation independently extracted exactly 17 bytes between FactsDB end and customArray start from pinned AutoSave-8 body SHA256 `AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E`. It recorded 13 native node-offset/ID controls, unchanged source and metadata, and no save/game writes. This subtask reads only those already-extracted bytes and recorded tables; it does not reread the original save.

The gap is `02 6B577A51814903CA E118A84B9942C8C4`. Native signed-VLQ count decoding yields 2; the following two little-endian UInt64s exactly consume the gap:

| Saved root index | ResourcePath hash | Provider-pinned resource |
| --- | --- | --- |
| 0 | 14556559240358156139 | `base\quest\cyberpunk2077.quest` |
| 1 | 14179656652942743777 | `ep1\quest\ep1.quest` |

Both values match the fresh provider manifest and independent FNV1a64 hashing of canonical depot strings. The actual saved array establishes EP1 index 1; the `.gamedef` list was not used to guess it.

All eight phase-node links were independently resolved through handle-aware normalized graphs with pinned source hashes. The Jason gameplay startup embedded graph `root/1` has path **`[1,0,10,5,2,50,19,5,1]`**. Exact native seed entry 1 at `0x37015BC` is `0x01800013`; hashing the complete UInt16 path bytes with that seed gives **2698350362 / `0xA0D58F1A`**. The wrapper resource index and `.quest` phase-node 0 are distinct elements. Codeware's default-seed path helper alone gives a different hash here.

The bounded lookup checked 247 nodes in nine exact ancestry graph contexts and found these serialized graph-store rows in the same pinned body's existing extraction:

| Source context / node | Node class | Graph key | Serialized row |
| --- | --- | --- | --- |
| EP1 `root/10`, 8 | PauseCondition | 637430697 | store 7 = 1 |
| EP1 `root/10`, 15 | PauseCondition | 3909444386 | store 7 = 3 |
| EP1 `root/10`, 25 | LogicalXor | 470258260 | store 5 = 2 |
| Jason gameplay `root/1`, 33 | PauseCondition | 3846627466 | store 7 = 0, explicitly serialized |

No hash collisions occurred within these candidate contexts; global collision freedom is not claimed. Immediate startup action nodes 101/142/143 have keys 2394538006 / 2892351145 / 2630427640 and no rows in graph stores 2–10. Their absence is **not** evidence that they never executed. Store 7's complete condition/reset lifecycle is not decoded here. A stored 0 and a missing row are distinct offline observations, even when a runtime getter returns 0 for either. These are not current running/retired/pending labels.

`root_binding_decode_01.json` records the ancestry, matches, source hashes and limits. That exact-fixture decoder accepts the current canonical `02` count, but its original generic signed-VLQ helper did not explicitly reject negative zero or overlong representations. It is not certified as a universal decoder. Fresh strict validation and malformed controls are recorded separately, preserving the initial evidence.

The earlier schema/root decode retained a version-mapping unknown when written. The following exact native linkage supersedes that narrow unknown:

- Save reader vtable `0x30AD578`, virtual `0x48`, points to getter **`0x3E9C70`**: load `[this+0xE0]`, then return `[header+0x298]`.
- The same vtable's virtual `0x68` points to `0xFA507C`, which calls `0xFA5548`; that verifies VASC magic and calls `0xFA55F0` on the same header object.
- `0xFA55F0` reads the first post-magic UInt32 into `header+0x298`, the second into `header+0x29C`, checking maxima `0x115` (277) and `0x9C4` (2500).
- ArchiveVersion `0xC3` (195) is read separately later and stored at reader/underlying-stream `+0xC` (`0xFA55CF..D2`).

The QuestsSystem version query at virtual `0x48` therefore refers to **SaveVersion**, not GameVersion or ArchiveVersion. The parent's same-body header artifact `root_saved_resource_array_01/header.json` records SaveVersion 277 and satisfies the native `>= 139` layout gate. Native linkage is retained in `stream_version_binding_01.json`, `save_header_candidates_01.json`, and `native_26/27.json`.

The CutControl FIFO/unregister result in REPORT.md remains usable alongside exact graph edges. External lease completion, later reactivation, exact prepared pending state and current loaded-body identity remain separate questions. No live inspector, installation or new gameplay test follows from this addendum.
