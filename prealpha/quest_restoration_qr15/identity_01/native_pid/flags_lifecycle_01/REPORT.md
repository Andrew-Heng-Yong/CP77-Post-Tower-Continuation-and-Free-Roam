# Record flags, dynamic registration and PS2 stage-information loss

**The canonical PS miss is not a safe discriminator between node 103 pending and applied.** The exact native lifecycle permits a runtime PS with a false persistence-registration value, and the writer omits its key/body independently of its payload. Two such in-memory histories can therefore produce the same **PS2 projection**. This is not a claim that either history occurred, or that their complete saves are identical: graph, event and other saved systems may distinguish them.

The EXE remains pinned to SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. Addresses below are RVAs. Only native file bytes, local source and retained proof artifacts were read. No save, capture/parser invocation, game process, callback, build or runtime modification was used.

## Exact ordinary registration caller

The already bound EntityStubSystem instance table is `0x31083C0`. Its `+0x110 = 0x1818F68` resolves the interface type through global `0x3BC2F10` at `0x1818F7C` and stores the returned system at EntityStubSystem `+0xB0` (`0x1818F89`). The global's `gameIPersistencySystem` type is bound by the earlier sealed entity-origin/native PID evidence. This does not rely on a shifted SDK slot declaration.

The ordinary create route is:

```text
0x2FA3EC -> 0x2FA4F4 -> 0x2FA9A8 -> 0x2FAA48
```

`0x2FA9A8` takes the cached system `+0xB0` and passes it into the stub constructor. `0x2FAA48` stores that pointer at stub `+0`, and the incoming requested EntityID at stub `+0x40`. Before component attachment (`0x2FAAA6 -> 0x2FBC1C`), it calls that same system's virtual `+0x1E0` with the ID's UInt32 and **third argument 0** (`0x2FAA84..A93`). The concrete PersistencySystem table `0x36343D8` binds this virtual to `0x2FAAEC`.

Registration `0x2FAAEC` inserts a row in system `+0x1E8` if none already exists. Its value is true only if the current DynamicEntityIDSystem predicate is true **and** the third argument equals 1. The ordinary constructor's argument 0 therefore creates a **false-valued row**, even if the predicate is true. An existing row is retained rather than overwritten.

Presence and value have different roles. `0x2FAC58` returns eligibility flags 3 for a false-valued present row, flags 7 for a true row, and flags 1 for an absent row. PS lookup `0x408DB4` tests eligibility mask 2 before hashing: a false-valued registered row permits runtime PS lookup/creation; a missing row does not.

This is a direct native route allowing PS existence while the saved enabled-ID list omits that ID. It does not assert that the target's current registration has this value, or that every population/restore path uses the ordinary-create constructor.

## Record byte +0x79 is separate from the eligibility descriptor

The table below refers to the **record** byte `+0x79`, not the eligibility descriptor's different flags byte.

| Mask | Exact writes and reads | Bounded meaning |
| --- | --- | --- |
| `0x01` | Inline data installer `0x4B5E58` ORs1 at `0x4B5EDF`; heap installer `0x4B46C4` ORs1 at `0x4B476D`; clear helper `0x4B5E2C` clears1 at `0x4B5E4C` | Installed serialized-buffer state; set even for an empty buffer. It is not a node-completion receipt. |
| `0x02` | The data installers clear/set this bit when switching inline versus heap storage; reader `0x2164E80` selects its data address/length using this mask | Data storage representation. |
| `0x04` | Eligibility synchronization, persistence-value changes and reload set/clear it; the save writer requires it | Selection for saving, independent of payload contents. |

For a fresh record allocation block, allocator `0x2165940` requests 0x40000 bytes and clears them; `0x409154` also calls the zero-fill helper with zero/0x40000 before putting 0x80-byte records into the pool. A new block therefore begins with these bits clear. This is a fresh-block initialization proof, not a claim that every reused slot is freshly zeroed.

Data installation `0x21658F0` chooses inline storage for length at most 63, otherwise heap storage. Both paths unconditionally set mask 1 after copying data, including an empty inline span. The generic object serializer `0x4B5F70` installs its output through this helper at `0x4B604D`; it is not specific to node 103. The class-serialization helper `0x21650D0` calls that serializer when the actual class flag mask 0x400 permits it.

Clear `0x4B5E2C` first installs an empty inline span, clears record metadata `+8`, then explicitly clears mask 1. The actual Reset virtual `+0x1D0 = 0xABF470` reaches this clear helper at `0xABF4F7`, after handling the live state. Actual dynamic-state removal `+0x1E8 = 0x408A50` removes the registration row and walks its known component associations through `0x408ADC`, which also clears matching records at `0x408BC2`. No reset/remove operation was performed here.

## Save selection can change without a setup-state change

Change helper `0x2FD6BC` compares and updates the registration value at system `+0x1E8`. If changed, it calls `0x716E3C`. That function enumerates associated live state handles, hashes each state's PersistentID, finds and locks its matching record, then replaces only record mask 4 with the new value (`0x716F33..F4D`). It does not inspect a node 103 receipt or the PS payload to choose that bit.

The create-enabled lookup's `0x408E2B..E41` can synchronize mask 4 from its eligibility descriptor when descriptor bit 0 is clear. Low24-bit registration descriptors have bit 0 set, so this particular synchronization branch is skipped for them. Fresh records and the explicit registration-change/refresh paths must not be conflated with the static-ID branch.

The bounded record-refresh body `0x2164C10..0x2164D1B` also recomputes eligibility from a live state's entity and actual class, replaces record mask 4, and calls the generic serializer only if eligibility mask 4 is set. The body is captured with an explicit span including its continuation beyond the first unwind segment; no assumption that one `.pdata` extent contains the whole body is made. Its writes corroborate the persistence-selection meaning; this report does not need an unproved callback dispatch to establish the writer's loss of information.

Actual enable virtual `+0x1F8 = 0xF78440` requests true only after the DynamicEntityIDSystem predicate succeeds. Disable `+0x200 = 0x2FD61C` requests false through the same change helper. The actual DynamicEntityIDSystem instance `0x3213628` binds that predicate at `+0x1D8 = 0x2FAB90`: high-range IDs can consult an additional per-ID membership set. Therefore allocator interval labels alone do not establish universal inability to persist, and this review does not claim the target can never become enabled.

## Reload does not restore the discarded identity or payload

The previously verified modern loader `0x59FB28` clears the registration table and recreates **only** first-list IDs as true-valued rows. False-valued registration rows are not in that list. For nonzero PS2 entries admitted by its class/body checks, it creates/finds the matching record, installs body data through `0x21658F0` (setting mask 1), and calls `0x5A02A4` to set mask 4. This is generic restoration of retained selected data, not a setup receipt.

The key-zero branch at `0x59FFC5..FC8` skips directly to the next declared row. No record identity/class/body can be reconstructed from that row. The canonical key miss therefore proves that PS2 does not restore a nonzero keyed record under that address from the pinned body. It does not prove that no corresponding runtime record existed before saving, that another system carries no relevant state, or that subsequent native registration/materialization cannot create state.

## Conditional projection counterexample and decision

Consider two hypothetical in-memory histories with the same canonical record key and false persistence profile. One has node 103's relevant setup still pending; the other has applied it, with a different in-memory state/payload. **If record mask 4 remains clear in both**, the exact writer branches at `0x2A35473..475` to the same eight-byte zero output at `0x2A355EB..5FD`, regardless of mask 1 or payload contents. The first enabled-ID list also omits the false-valued ID in both.

Thus those histories are indistinguishable **by the missing canonical key / anonymous zero row and enabled-ID omission**. This is a source-based conditional counterexample for that PS2 projection, not a recovered pair of actual histories, a byte-for-byte full-save equivalence claim, or proof that node 103 ran or did not run in this fixture. Other saved graph/event state may differ and must be reviewed separately.

Capture03's verified canonical miss and first-list omission cannot be promoted into a safe skip/replay guard. The exact native mask 1 and mask 4 lifecycle provides no stage discriminator here. No repair, API probe or new manual test is selected.

`verification_01.json` records exact-byte/slot/branch controls; `manifest_01.json` pins captured native spans, local headers and prior sealed proof artifacts. Some retained exploratory captures include neighboring code after leaf thunks; only the explicitly identified bodies/spans above are used for lifecycle conclusions. Existing evidence is preserved, with no runtime or package changes.
