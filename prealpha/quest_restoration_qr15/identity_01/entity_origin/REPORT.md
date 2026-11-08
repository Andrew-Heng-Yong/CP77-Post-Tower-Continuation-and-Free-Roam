# Native origin and consumption of saved associated ID10229047

Disposition: the traced associated value is in the **EntityID namespace**, not a separate opaque StubID requiring numeric conversion before a PersistentID lookup. The value's connection to a current loaded actor or saved vehicle PS is still unproved.

`evidence_01.json` captures40 finite native functions from the pinned EXE SHA `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. `verification_02.json` passes17 byte/slot/data-flow controls. The original failed control file remains preserved: run01 had two hand-transcribed relative-displacement typos; run02 calculates direct destinations from their signed rel32 operands. Neither failure was a runtime result.

## Saved-row origin

The previously validated native saver `0x2BCED84` constructs saved array `+0x20` from two sources:

- Object array `+0x98` is appended unchanged through `0x2F9DF0` at `0x2BCEE43..0x2BCEE4D`.
- Active IDs obtained through `0x36E5E0` are also considered. That function extracts each pending stub's U64 field `+0x40`, and appends the object's `+0x88` array. The saver passes the raw U64 ID to `gameIPersistencySystem` virtual `+0x1F0`; IDs whose returned state is not2 can enter saved array `+0x20`.

The system type in this filter is exact: global `0x3BC2F10` is assigned by registration `0x163D24C`, which names `gameIPersistencySystem`. It is not the EntityStubSystem interface. The concrete PersistencySystem registration `0x17341D0`, ConstructCls `0x5A14B0`, constructor `0x5A02C8`, and instance table `0x36343D8` bind virtual `+0x1F0` to `0x4CB220`.

Because the saved array merges those sources without a per-item origin tag, this row cannot tell whether10229047 was already reserved or was an active ID routed by that filter. An empty saved spawned array does not resolve the ambiguity.

## Restore and native request identity

Registration `0x3840E0` restores saved array `+0x20` through `0x2606570 → 0x467DEC` into object array `+0x98`, preserving all U64 values. The ordinary activation virtual `0x9CEFD8`, via its separately captured taken branch `0x9CEFE2`, reaches `0x9CF5A0`. That helper pops a U64 from array `+0x98` and passes it unchanged to `0x9CF6EC`.

`0x9CF6EC` puts the value into the first U64 of a create request, with transform at `+0x10` and record ID at `+0x30`. It then calls `0x2F9E74 → 0x2FA044`. Native token creation `0x2FA378` copies that request U64 unchanged into token field `+0x08`. No hash conversion, bit rearrangement, pointer interpretation or separate StubID lookup occurs in this route.

The request target is independently typed. `gameEntityStubSystem` registration `0x173C1C8` binds metadata `0x3330838`; ConstructCls `0xDB3B7C → 0xDB3B84` installs instance table `0x31083C0`. Its CreateStub slot `+0x1B0` is the same `0x2FA044`, and RestoreStub `+0x1B8` is `0x9CF378`. These current native layouts corroborate the SDK request/token/EntityStub EntityID fields; the conclusion does not rely on a header name alone.

The fallback when no reserved ID exists closes the namespace identity: `0x9CF5A0` resolves global `0x3BC48B0`, whose registration `0x162FCD4` names `gameIDynamicEntityIDSystem`. It either obtains an existing record-associated ID via `+0x200 → 0x4FAB74 → 0x382BE0`, or calls `0x4FABB8` to choose a current native ID allocator. Its result fills exactly the same request field used by a restored associated ID. This is an EntityID allocation path, not an independently converted StubID path.

## Current native allocation interval

Current native registration `0x16E6E38` for `gameDynamicEntityIDSystem` binds metadata `0x32F1268`, ConstructCls `0x13EFF30`, constructor `0x13EFF38`, and instance table `0x3213628`.

- The constructor initializes counter `+0xE0` to10,000,000. Actual slot `+0x1B0 → 0x4FAC20` allocates that interval with upper bound0xFFFFFF, wrapping back to10,000,000.
- Counter `+0xE4` starts at9,000,000. Actual slot `+0x1B8 → 0x12EC1A8` allocates below10,000,000 and wraps back to9,000,000.
-10229047 lies in the first interval. The SDK describes it as the transient/non-savable allocation interval; the current native initialization and bounds independently match it. The old SDK generator slot declarations are shifted relative to the current instance table and must not be used blindly.

This interval alone is not proof of permanent inability to persist. Current native predicates `0x2FAB90/0x2B338D8` inspect an additional per-ID map for IDs in this high interval, and PersistencySystem `0x4CB220` also considers its registered-state map. Their exact gameplay policy names and all transitions were not established here. No MarkSavable or universal remap claim is made. In the concrete reserved-ID restoration route above, the ID is copied unchanged.

## Consequence for the proposed repair

No additional StubID-to-EntityID numeric conversion is supported or required by this traced path. Direct PersistentID hashing can therefore be reviewed using10229047 as an EntityID candidate, subject to the separate native component-name/key proof.

Candidate misses still do not prove absent vehicle state, an unspawned car, failure of node103/104, or permission to replay setup. The original captured ID may not identify the currently loaded body, and the merged saved row contains no visual/door completion certificate. This evidence authorizes no runtime repair, reset, new diagnostic API call or save mutation.

Only captured evidence and file bytes were read. No original save, game process or game API was accessed; no runtime resource, build, installation or save was changed.
