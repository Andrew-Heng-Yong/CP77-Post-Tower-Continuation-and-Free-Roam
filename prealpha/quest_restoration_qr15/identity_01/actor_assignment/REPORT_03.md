# Population materialization identity — successor03

The native population materializer is now bound to the EntityInitializeRequest ID field. **The traced selected-entity route preserves the requested ID through request construction and heap copying.** This is a static source property; it does not depend on observing gameplay. Actual materialization and the final asynchronous handoff remain separate limits.

This successor preserves `evidence_01.json`, `evidence_02.json`, and the earlier `REPORT.md`. It supersedes their earlier materializer-producer gap. `evidence_03.json` captures the21 relevant downstream functions and passes14 byte/field/call controls. All use the same pinned EXE SHA `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`.

## Source-backed materialization contract

1. The already bound update tick calls `0x3C2E0C`. That function traverses pending map `+0x128`, obtains its UInt32 ID key through `0x3C3A78`, and looks up the corresponding per-ID record in map `+0xF8`. It packs the ID above eight flag bits (`ID <<8`).
2. Selected spawn `0x537D4C` unpacks the ID with `>>8` and passes the ID plus its record to actual population materializer `0x4F7D80`. The target10229047 fits24 bits, so packing loses no ID bits.
3. `0x4F7D80`, at `0x4F7ECD..0x4F7EFD`, copies this ID through the plain U64 wrapper `0x409320` into EntitySpawnerRequest `+0x30`. It calls EntitySpawner dispatch `0x5C140C` at `0x4F810B`.
4. Population world attach `0x96DA58` obtains the spawner from scene `+0xA0 → runtime entity system +0x58`. Runtime setup `0x9D5A44 → 0x11DA620` installs factory table `0x3617C00` in spawner `+0x68`; its virtual `+8` is `0x5C1508`. The setup's mode branches change a mode byte and retain this same factory table. This closes the dispatch used by `0x5C140C`; a generic factory is not merely assumed.
5. Factory `0x5C1508` explicitly copies EntitySpawnerRequest `+0x30` to EntityInitializeRequest `+0x20` (`0x5C1552..0x5C1556`, local request baseRSP+0x40). `0x719F40 → 0x719FE8 → 0x719D68` clones that request to heap storage; `0x719DAC..0x719DB0` preserves its `+0x20` value. The copied request is retained at spawn context `+0x10`.
6. The previously bound ordinary initializer `0x71BEF0` copies EntityInitializeRequest `+0x20` to actual entEntity `+0x48` without conversion. Its immediate consumer `0x71BD9C` gets the request from context `+0x10`.

Thus, on this ordinary selected-population request path, no WorldNode/static-ID substitution appears between the pending ID and the constructed initialization request. If this context reaches the bound ordinary initializer, that ID becomes the actor's `+0x48` value. This does not certify all engine spawn routes or every historical alias.

## Exact dispatch limit

The local job setup was additionally followed: `0x71A170 → 0x71A2B8 → 0x71B480 → 0x71A38C → 0x7191E0`. Its later handoff to `0x71BD9C` was not bound. This is a remaining static dispatch boundary, not an inference that it fails, never runs, or must be replaced with a gameplay test.

The conditional ID-preservation property above is established from source. Whether this particular saved candidate was ever instantiated, currently has a loaded body, or survived a reload is not established by that property. No actor liveness, node103 visual-state receipt, node104 door receipt, or executing quest owner is proved.

## Canonical PS key does not require actor assignment

The exact **stub-associated historical lookup address** was already independently established and does not depend on closing the actor handoff. Native `0x9A24E4` constructs PersistentID directly from **EntityStub `+0x40`** and exact component CName `vehiclePersistentDataPS`, then calls `0x9A2514`. Its callers `0x9A2428/0x2B9ED90` deliberately select that name.

Therefore, for associated candidate10229047, key17113219195054135786 (`0xED7E5E302C9919EA`) is a canonical native stub lookup address. A captured PS2 miss at that exact address is a valid address-level absence statement. It does not prove absence of the actual car's entire state, because persistence enablement, materialization history, alternate owner/body association and save selection remain separate issues. The generic visual flag and that miss do not determine setup stage.

No new original-save read, save parse, process/game API, build, installation or runtime change occurred. No manual test or repair is authorized by this source result alone.
