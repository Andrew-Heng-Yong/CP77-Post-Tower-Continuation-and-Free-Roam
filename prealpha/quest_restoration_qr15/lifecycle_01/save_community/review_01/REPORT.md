# Independent CommunitySystem decode review

Disposition: PASS for this exact captured save component. No blocking decoder discrepancy was found.

`review.py` implements a separate cursor parser from the sealed native schema. It imports neither `decode.py` nor `decode_full.py`, reads only the captured component and evidence files, and does not read the original save. All22 checks pass in `review.json`, including malformed name encodings, footer truncation and an extra footer byte.

The independent traversal confirms:

- The capture has10294 unique outer keys and43473 nested rows. Their values are discovered from the captured input.
- The second map has3160 unique keys. The car's exact key `17433794865907239043` occupies its proper key-array slot at tail offset2051480.
- That key's corresponding row is2132739..2132770. Array `+0x00` is empty; raw `+0x42` is0; active byte `+0x46` is1; array `+0x10` is empty; raw `+0x40/+0x44` are0; array `+0x20` contains10229047; array `+0x30` is empty.
- All final sections agree with the native serializers: listA430 rows with1750 nested entries, and listsB/C/D empty. All2191992 tail bytes are consumed, with no unexplained remainder. Including the known node index, map count and outer keys gives the captured node size2274352.
- Actual names use the native no-dictionary signed VLQ negative-length ASCII format. Unsupported positive/Unicode names and noncanonical lengths fail closed. The fixed U32 array counts, version277 record fields and footer widths match native code.

The correct conclusion is **saved active=true**, with one associated ID in the reserved/filtered group. The native pre-save copier establishes the active-byte meaning. This is not evidence that entity10229047 is presently spawned, alive, initialized, owned by a running quest graph, visually destroyed, or configured with its doors disabled. The empty saved spawned group does not prove absence in the currently loaded world. JF01/JF02 loaded-body identity remains unbound.

The implementation deliberately qualifies this exact version277 capture. Its ASCII-only and bounds limits are conservative parser limitations, not proof that other inputs are corrupt. The original prefix-only decode01 remains preserved and does not masquerade as a complete component decode.
