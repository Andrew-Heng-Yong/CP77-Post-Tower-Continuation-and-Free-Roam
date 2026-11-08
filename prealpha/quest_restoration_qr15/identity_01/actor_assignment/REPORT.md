# Stub-to-actor identity: bounded native result

**The complete actor assignment contract remains unresolved.** The investigation now binds the actual registered PopulationSystem callbacks and their queue consumer; it does not stop at the registration virtual or infer failure from a direct-caller miss. It still cannot certify that associated ID10229047 is the actual instantiated vehicle's `+0x48` value.

`evidence_01.json` preserves the first bounded result and11 passing controls. Fresh `evidence_02.json` extends it through the registered callback and exact descriptor consumer, with8 passing controls. These are source-link controls, not an actor-identity PASS. The pinned EXE SHA is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`.

## Source links established

1. **Stub construction uses the requested value.** Actual `gameEntityStubSystem` instance `0x31083C0` was already bound. Its queued CreateStub/RestoreStub records are consumed by `0x2F94EC → 0x2FA3EC → 0x2FA4F4`. The create allocation route `0x2FA9A8 → 0x2FAA48` explicitly stores incoming R8 at EntityStub `+0x40` (`0x2FAA76`); restore `0xDCD34C → 0xDCD3E4` does the same (`0xDCD416`). No alternative-ID generator appears in those bound constructor paths. The duplicate check can report status3 instead of creating a new stub.
2. **The completion callback retains the token ID.** The population callback constructed at `0x9CF818` has table `0x3956DC8`, whose invocation `0x4D2648 → 0x4D227C` requires created status1 and copies Token `+0x08` into the first U64 of its PopulationEntityRegisterRequest. It passes that request through the actual PopulationSystem virtual `+0x1F0`.
3. **PopulationSystem registration is the actual current implementation.** Registration `0x16CF570 → metadata0x32DFC90`, ConstructCls `0x86FDC0 → 0x86FF40`, installs instance table `0x3677070`. Registration virtual `+0x1F0 → 0x465F48/0x465F50` looks up the stub using the input ID and queues a0x38-byte descriptor at system `+0x60`. The incoming ID's low32 bits occupy descriptor `+0x28`.10229047 fits the24-bit dynamic domain, so this copy loses no bits for the target.
4. **The registered update chain consumes that exact queue.** Instance `+0x108 → 0xDAB09C` registers builder `0x21D6A80 → callback table0x39569C8 → 0xC6C6EC/0xC6C6F4 → 0xC6C7B0 → job creator0xC6C858 → job0xD32E84 → tick0x4F6B5C → consumer0x4F5C18`. The consumer locks `+0x58`, swaps/drains `+0x60`, steps each descriptor by0x38, reads ID32 at `+0x28`, finds the corresponding stub and inserts a per-ID record in map `+0xF8`. Pending selection in map `+0x128` retains the same ID. This is a real asynchronous dispatch path, established from its registration and job builder rather than registration success alone.
5. **The final entity initializer has a direct assignment.** `0x71BEF0` reads EntityInitializeRequest `+0x20` at `0x71BF47` and stores it to the actual entEntity `+0x48` at `0x71BF4B`. The immediate native job consumer `0x71BD9C` passes that request from job context `+0x10`. A separate initialization wrapper `0x29A5954` reuses the same request. The ordinary native vehicle-data owner initializer therefore consumes this final field, as established in `../vehicle_data_native/REPORT.md`.

## Exact remaining link

The source side is now the PopulationSystem's per-ID record in `+0xF8`, its stub pointer, and pending-selection record in `+0x128`. The destination side is the EntityInitializeRequest `+0x20` supplied to `0x71BD9C/0x71BEF0`.

The **population materialization/spawn-job producer that connects that per-ID record to the EntityInitializeRequest** was not bound in this investigation. The registered callbacks and direct tick helpers establish registration, selection and spatial-manager updates, but do not establish this request construction. The general EntitySpawner request factory was inspected as terminal/context evidence; it is not substituted for the population route without a source link.

The class/type of the missing request is explicit (`EntityInitializeRequest`); the missing operation is its population-specific producer and handoff into the initialization job. The currently identified native destination takes a request pointer from job context `+0x10`. Direct call, RIP-reference and absolute-pointer searches did not bind that producer. This negative search is a limitation of the inspected call graph, not evidence that the job never executes. Registered callbacks were additionally followed and the queue consumer was successfully closed.

The bound constructors directly assign the requested ID, but their component attachment/initialization helpers also invoke component virtual methods. This work does not assert global immutability against every such callback or every world/restore alias path. No positive remap was found, and absence of a remap remains unproved across the missing materialization link.

## Consequence

The fourth key is an exact **expected canonical address for the candidate EntityID**, not a certified address for a historical or currently materialized vehicle. Its absence from the captured200 native vehiclePersistentDataPS rows does not yet prove that the actual car's saved native state is absent. It cannot establish incomplete node103/104 setup or justify a skip, replay, reset or actor-specific guard.

No new save read or parse, process access, game API, executable loading, build, installation or runtime resource change occurred. No manual test is requested by this source-only report.
