# Native traversal inspector prerequisite review

Subsequent bounded evidence closes the saved root index and SaveVersion identity for one pinned historical body; see [ROOT_BINDING_ADDENDUM.md](ROOT_BINDING_ADDENDUM.md). It does not change the live-inspector readiness result below.

**Live inspector readiness remains BLOCKED by an unclosed lifecycle/thread boundary.** The exact executable confirms that the QuestsSystem byte lock at `+0x60` protects ordinary graph-dispatch and stop operations. It does not establish that a manual CET/shared-lock snapshot is safe during every initialization, reload or teardown transition. A separate useful result is closed: native phase cuts remove handler and child registrations; these are not merely cached liveness flags. A further offline route can bind the saved root resource index without installing an inspector.

This is static evidence only. Executable SHA256 is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`, image base `0x140000000`. All addresses below are RVAs. No game/CET/framework code was executed; no process was attached, save was parsed, or runtime file was changed. No module, compile, package or install is prepared by this review.

## Lock coverage actually established

Codeware's `src/Red/QuestsSystem.hpp` declares the lock, RootPhase `+0x68`, phase Children `+0x88` and Handlers `+0x98`. Its `QuestPhaseExecutor.hpp` and `QuestsSystemEx.hpp` hold a `std::unique_lock` on this lock throughout native node/path dispatch. Those source methods mutate; they do not themselves prove a read-only inspector or CET call-thread contract.

The native exclusive acquisition helper `0x1FFAD60` calls `0x22CA300`, which waits for byte zero and atomically changes it to `0xFF`. Release `0x19417F0` exchanges the byte back to zero. This matches the SDK SharedSpinLock byte protocol: zero free, `-1` exclusive, positive reader count.

Source-confirmed examples:

| Native operation | Exact lock and protected work |
| --- | --- |
| Path execution wrapper `0xBEA6CC` | Acquires `this+0x60` at `0xBEA6EA..F8`; traverses RootPhase and dispatches virtual `0x120`; releases at `0xBEA853..5A`. |
| Targeted phase stop wrapper `0xBEC238` | Acquires at `0xBEC25F..26D`; resolves the path and invokes root phase virtual `0xF8`; releases at `0xBEC37E..382`. |
| Descendant collection/operation wrapper `0xBEC8F8` | Acquires at `0xBEC91B..926`, traverses root, releases `0xBEC9F3`. |
| Whole-root child stop `0xBECD74` | Acquires at `0xBECDAF..DBB`; calls `0xBECE2C` to stop/clear children; releases `0xBECDDB`. |
| Save writer `0x2C9F364` | Acquires at `0x2C9F378..380`; serializes quest state; releases `0x2C9F537`. |
| Teardown root release `0x35EAEC` | Acquires at `0x35EAFA..EB03`; clears/releases RootPhase; releases `0x35EB35`. |

Inner mutation methods do not independently acquire this lock: `0x889C38` appends a new phase to Children before Initialize; `0xBEC890`/`0xBEC6D4` stop and erase child handles; `0x2B0800` adds handlers; `0x2FCF0C` uninitializes and erases them. They rely on their calling context. This review closes the sampled ordinary execution/stop chain, not every possible caller in every framework or transition.

The critical exception is root construction/replacement `0x35F430`. It constructs a new root and writes `this+0x68/+0x70` at `0x35F475..4A4` with **no acquisition of `+0x60` in the function**. Its virtual entry is QuestsSystem vtable `0x30BCE78 + 0x110`; no direct caller was found in the bounded call search. An enclosing lifecycle serialization/thread guarantee was not established. Teardown `0x35EAEC` also clears NodePathHashMap `+0x78` **after** releasing the root lock (`0x35EB35`, then `0x35EB37..3B`). Therefore a proposal to copy that global map under only this lock lacks a complete synchronization contract.

## What TryLockShared does and does not solve

SDK `SharedSpinLock-inl.hpp` implements one `TryLockShared` attempt by reading the byte and CAS-incrementing it unless it equals `-1`; it never waits. A successful shared acquisition blocks the native exclusive protocol above. If a manual call re-enters while the same thread owns the exclusive lock, a single try attempt returns busy rather than deadlocking. The SDK has no owner-thread or recursive-lock tracking; success is not proof of a safe engine lifecycle or execution thread. The byte counter also has no saturation check; a proposal must not assume this is a general unbounded reader lock.

An existing strong `questIQuestsSystem` handle can preserve that object's lifetime. It does not serialize unlocked root replacement or supply a CET console/thread/lifecycle contract. Native-pointer validity cannot be proved by a non-null test or by a cap on traversal depth.

If the transition admission contract is later established, a reviewed snapshot would need one nonblocking attempt, guaranteed shared unlock on every exit, strict total/depth/entry/byte bounds and owned copies made before unlock. It should preallocate output storage and perform file I/O, formatting, RTTI/getter/script calls and user callbacks after unlocking. It must not call native methods that reacquire the exclusive QuestsSystem lock while holding a shared lock. These are conditional implementation requirements, not a claim that an inspector is now safe or useful enough to install.

Codeware's `QuestPhaseRegistry::OnBootstrap` has both phase-preload and initialization hooks commented out in the local source; its separately locked cached map is not a substitute for the native RootPhase tree or a proven installed liveness API.

## CutControl ordering and retirement of registrations

The CutControl native class is bound by registration `0x168DC18`, class global `0x3BCB1E8`, getter `0x195BD10` and vtable `0x3126940`; execution virtual `0x158` is `0x9752AC`. It emits the cut signal first (`type 2`, or `type 3` for permanent at `0x97535B`) and then ordinary Out (`type 0` at `0x975320..33B`). Output insertion order alone is not the ordering proof.

The executor provides the missing queue proof:

1. `0x2B393C` appends each node output to the pending-output array in vector order (`0x2B3A27..74`, push helper `0x352E10` appends at the tail).
2. `0x352BFC` copies the **front** pending output, then `0x352B00` removes the front. Its removal helper `0x352B44` moves successive `+0x20` entries left and decrements the count: FIFO, not a last-in/first-out stack.
3. Expanding one pending output appends all its connected destination commands to the immediate array (`0x352DB1..DBD`). `0x352984` drains that immediate array through `0x2B393C` before expanding the next pending output. Both arrays use the same FIFO primitive.
4. Therefore the CutControl's direct cut destinations run before that same CutControl's Out destinations in the ordinary dispatch loop. If a destination phase's stop method returns, its synchronous unregister/remove chain below has completed before the later Out command is expanded. This does not prove completion of unrelated asynchronous world work.

The exact `questPhaseNodeDefinition` binding is in `phase_type_01.json`: registration `0x15B5014`, global `0x3BCAB50`, vtable `0x30470A8`, stop virtual `0x178 = 0xBEC7A0`. Special signal dispatcher `0x2B3C84` invokes this stop virtual for signal types 2/3; type 3 passes the permanent-disable flag.

Phase stop calls PhaseContext virtual `0x48` (`0xBEC814`). It finds the corresponding child and calls `0xBEC890`, which synchronously calls recursive cleanup `0x2B1D30` and then erases the child's handle from its parent's Children array. Recursive cleanup repeatedly stops handler-owning nodes while the phase's handler count at `+0xA0` is nonzero, recursively removes all children, cancels the pending phase ticket at `+0x84` if present, and invokes resource/prefab manager cleanup callbacks. The graph is not merely left intact with a killed fact.

The generic signal-stopping base `0x2FDA9C` optionally records permanent disabled state through PhaseContext virtual `0x98`, then removes an existing handler through virtual `0x68`. That context method is `0x2FCEAC`, calling `0x2FCF0C`. The latter holds a local strong handler reference, calls its **Uninitialize virtual `0x20`**, erases it from the phase HashMap via `0x2FD024`, and releases the local reference. Codeware's `QuestPhaseHandler` interface independently names virtual `0x20` Uninitialize.

Consequently, on the exact phase-stop path, removed handler entries and removed descendant registrations are stronger evidence than generic cached-object presence. A retained C++ object through another reference is not a still-registered descendant. Conversely, a present phase can be idle and have no handler, and a registered handler is not proof of current scheduling/condition delivery/world liveness. Do not equate any of those observations.

For the original EP1 cut, this engine result can be combined with the **separately proven exact graph edges**, genuine ending lineage, all writers of the following fact, permanent/temporary setting, and absence of later reactivation. A scalar killed fact alone still cannot select the executing cut or certify all saved histories. No claim that a prefab/community/spawner lease or external asynchronous callback has fully retired follows from a void cleanup call; that remains a separate required contract.

## Narrow offline root-path binding route

Root phase construction does not append a universal `[0]` path prefix. Its constructor `0x889CC4` starts with an empty path array, then the new synthetic root uses vtable `0x3699F88`. Its ExecutePath override `0xBEA3D0` uses the first UInt16 path element as the index into the root's Children array. The first element is a quest resource index, not the `.quest` root phase node's own ID.

Root quest-resource factory `0x2C9C2F4` looks up the quest resource's UInt64 path using `0x1266558`, passes the returned index to ordinary phase initialization, and thereby appends that index before the `.quest` graph's phase-node ID. The lookup reads the ordered array referenced by QuestContext `+0x18`, compares each UInt64 resource path and returns its zero-based ordinal (`distance/8`), or `0xFFFF` if missing. CreateContext `0x2B30A0/0x2B3150` binds that pointer to QuestsSystem `+0xA8`.

This array is **saved state**, not an index guessed from current `.gamedef` mainQuests ordering. Native load `0x739578` loads it after FactsDB; save `0x2C9F364` writes it in the same place. The exact decoding contract is in `resource_array_schema_01.json` and the clarification below. An exact one-save resource-array extraction can therefore bind the missing first path element without a live inspector, provided its offsets/version and path hashes validate. This review did not perform the save extraction or assert a resulting ordinal.

The complete path hash must use the native first-element seed selection already documented in the parent report. For a nonzero resource index, do not silently use Codeware's universal default FNV seed. Bind the `.quest` node chain to current provider-pinned resources; do not search invented root IDs for coincidental key matches.

## Serialization contract and clarification

The outer node is named `questSystem`. Native serialization opens `QueuedData`, then `FactsDB`. Immediately after closing FactsDB, it writes the untagged `+0xA8` array in the parent payload, then opens a child named `customArray`. In `resource_array_schema_01.json`, the field named `prior_child` records **QueuedData as an earlier child**, not the immediate predecessor of the untagged array; the placement statement correctly names FactsDB. Preserve that distinction when using the schema.

For native stream versions `>= 0x8B`, the array is a signed VLQ count followed by `count * 8` raw bytes of little-endian UInt64 ResourcePath values. Helper `0x73AD98` calls `0x104170C` for the count and then transfers `size << 3` bytes. Read count `0x27B824`: first byte has six magnitude bits, continuation bit `0x40`, sign bit `0x80`; continuation bytes have seven magnitude bits and `0x80` continuation, at shifts 6/13/20/27. Writer `0x2F60040` confirms this encoding. Negative/overflow/excessive counts must fail the offline decoder. Older streams use another layout and must defer.

Exact stream placement must come from verified decompressed NodeEntry offsets and child end/next-start conventions. The native names belong to the node directory/open-close protocol, not an inline marker string to scan for. The count+array should consume the complete parent gap between FactsDB end and customArray start; unexplained bytes or an inconsistent parent boundary block binding. Pin the native stream version query corresponding to virtual `0x48` to the parser's actual field before applying the version gate. Do not assume a similarly named header version is equivalent.

SDK `ResourcePath.hpp` defines canonical path normalization and FNV1a64 hashing. Compare array elements to the hashes of exact provider-pinned `.quest` depots and retain all entries/collisions. Do not reclassify absent/mismatched candidate keys as owner absence. This binds resource indices only; it does not itself decode executing/pending handlers, validate world leases, or identify the currently loaded live body.

## Fields worth copying if an inspector is later qualified

Only bounded, correctly labelled structural values have immediate utility: resource depot hashes, complete UInt16 phase paths and their native hash, parent/child registration edges, raw handler-map keys/counts, and the already understood disabled-node ID set at `+0xC8`. These can bind exact owners and show registration at one instant. Handler pointers/vtable fingerprints should remain opaque; no guessed GetType/liveness or raw field labels are needed. A zero handler count or missing child only describes the captured registered tree, subject to complete traversal and transition safety; it does not certify every external owner.

The highest-value next step is the one-body offline root-array extraction. A live inspector that cannot satisfy the transition/thread gate is not ready, even if it compiles and uses TryLockShared.
