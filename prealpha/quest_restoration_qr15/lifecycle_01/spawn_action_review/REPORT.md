# Native quest spawn actions — exact dispatch and repeat effects

**Population and community Activate both have an already-active guard in this executable.** Community activation does not increment its entry `+0x28` field: it changes zero to one and calls the activation callback only on that transition. This closes that specific counter concern. It does not make the complete Jason prefix safe to repeat: CommunityTemplate Deactivate/Reactivate also invoke a separate cancellation operation, phase selection can be another operation, and the target reference and saved stage remain separate requirements.

Static pinned EXE SHA256: `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`; image base `0x140000000`. Addresses below are RVAs. No game/process/debugger, console callback, save, compiler or installer was accessed. Only this fresh evidence directory was written.

## Exact four payloads

The already pinned native gameplay JSON, SHA256 `EE0E5F03FAA59148CB46C048E761F4D5B58263A46C2ED7F2A6ADD6B6EECA09B3`, was read structurally. `action_payloads_01.json` retains the exact action objects and their source/review pins.

| Definition ID | Action object | Action | Reference |
| --- | --- | --- | --- |
| 101 | `questSpawner_NodeType` | Activate | `#sts_ep1_03_gunfight_broken_car` |
| 142 | `questCommunityTemplate_NodeType` | Activate | `#sts_ep1_03_gunfight_crowd_com` |
| 143 | `questCommunityTemplate_NodeType` | Deactivate | `#sts_ep1_03_pre_gunfight_com` |
| 86 | `questCommunityTemplate_NodeType` | Activate | `#sts_ep1_03_gunfight_com` |

All three community objects have `communityEntryName=None` and `communityEntryPhaseName=None`. None is the zero CName; their exact Activate calls therefore use the zero-entry-name path and skip the optional SetPhase operation. Alias spelling does not establish a world-node placement class or a live registered object.

## Definition execution to action dispatch

The exact native binding is:

```text
questSpawnManagerNodeDefinition registration16A248C
  metadata32BDB88, ConstructCls+D8=35230C -> ctor352314
  instance vtable30473D0
  Execute+158=FA404C, handler factory+188=36CBB0
```

`0xFA404C` is the generic asynchronous-node executor. On an ordinary incoming signal it checks the node's existing handler through PhaseContext virtual `+0x80`; if none exists it calls `0x2B054C`. That calls definition virtual `+0x188`, here `0x36CBB0`. The factory creates a phase handler with `0x36CF18`, then calls `0x36CC40`, passing the definition's action array `+0x48`. That routine walks 16-byte `SpawnManagerNodeActionEntry` handles and calls each action object's virtual `+0x110` (`0x36CCBE`). Thus the action requests are issued during handler construction; a generic executor return is not proof that they have finished applying.

The factory propagates PhaseContext virtual `+0x100` into the action call. Its exact implementation `0x88BB64` tests QuestContext byte `+1 == 2`. The action implementations have an alternate branch for that value; this report's action/facade semantics concern the **byte+1 != 2** path. The alternate implementations (`0x2C86E88` for Spawner and `0x36D5B4` for CommunityTemplate) are not certified here. The generic executor's separate signal-equality branch unregisters its handler and supplies an output; it is distinct from the ordinary incoming-signal path. The compared global signal name is not assigned a meaning here.

## Population-spawner action

```text
questSpawner_NodeType registration16A2D14
  metadata32BE1D8, ConstructCls+D8=D6EF04
  ctor writes instance vtable30FCB68
  action virtual+110=36DFD0 -> normal helper36E038
```

`0x36DFD0` copies the SDK action byte `+0x30` and NodeRef `+0x38` into its call context. `0x36E038` resolves that reference through `0x351030`, obtains the game community system, then calls its virtual `+0x258`. Exact gameCommunitySystem vtable `0x30D3A18 +0x258 = 0x36E160`; this helper calls population-spawner weak lookup `0x383660` on subsystem `+0xD8`. The action proceeds only when its returned weak object can be locked. It does not choose a community facade based on alias text.

| Action byte / SDK enum | Normal population request |
| --- | --- |
| 0 Undefined | no action facade |
| 1 Activate | virtual `+0x1D8` |
| 2 Deactivate | virtual `+0x1E0` |
| 3 Reactivate | `+0x1E0`, then `+0x1D8` |
| 4 ResetKillCount | `+0x1E8`, through cold block `0x245E428` |

The sealed native community evidence binds those facades to queued operation2/3/4. The action dispatcher `0x382CF0` sends ordinary operation2 to the unchanged registry object and `0x9CEFB8`. That method tests initialized `+0x11`, then active `+0x10`; it returns when uninitialized or already active. Only initialized-and-inactive changes active to1 and calls object virtual `+0x38`. Thus **already-active ordinary population Activate does not invoke activation again**. This does not certify the inactive object's callback, rewards, entity state or every spawner class.

Reactivate is deliberately different: deactivation and activation are requested in order. ResetKillCount is a separate mutation, not an alternate spelling of Activate. Neither is selected by node101's exact payload.

## Community-template action

```text
questCommunityTemplate_NodeType registration16A2BA8
  metadata32BE0D0, ConstructCls+D8=CA8F08
  ctor writes instance vtable30E0230
  action virtual+110=36D1B4 -> normal helper36D28C
```

The helper resolves the NodeRef through `0x351030`, calls community-system virtual `+0x230` (`0x46757C`, weak lookup in root map `+0x68`), and requires a lockable community object. It then dispatches:

| Action | Normal community operations |
| --- | --- |
| Undefined | none |
| Activate | If phaseName nonzero, `+0x1C0` SetPhase; then `+0x1B0` Activate |
| Deactivate | `+0x1D0` cancellation operation; then `+0x1B8` Deactivate |
| Reactivate | `+0x1D0` cancellation; `+0x1B8` Deactivate; optional `+0x1C0` SetPhase; `+0x1B0` Activate |
| ResetKillCount | `+0x1C8` |

The extra `+0x1D0` is not a population facade. It is absent from Codeware's simple `DeactivateCommunity` source wrapper, so that source wrapper must not substitute for this exact quest action's behavior.

### Queue and already-active guard

Community Activate facade `+0x1B0 = 0x36D42C` validates the community's registry membership (`0x3851E0`) and queues a 32-byte row to root `+0x48` under lock `+0xA0`, with operation byte0. Deactivate `+0x1B8 = 0x36C714` uses operation1; SetPhase `+0x1C0 = 0x36D540` uses operation2. Append helper `0x36D49C` writes at the tail.

Actual root update is `0x4676DC`, called from native tick `0x71EDD0` after the separate population-subsystem tick. It takes that queue under the same `+0xA0` lock, copies it, clears the source count, then visits rows in order. Operation0 calls `0xFB2680 → 0xFB26A0`; operation1 calls `0x1481FE4 → 0x4685F0`. The consumer reads the community from the root registry and chooses either the named entry or, for zero entryName, the native list at community `+0x28`. This review does not establish that list's complete relationship to the separate entries array at `+0x18`.

Entry Activate `0x467ECC` is exactly:

```text
if entry.Int32(+28) != 0: return
exchange entry.Int32(+28) = 1
call entry virtual+18
```

There is no increment. Repeated ordinary Activate on the same already-active targeted entries is a no-op at this mutation/callback boundary. Inactive entries do transition and invoke their callback. The zero-entry-name operation applies this guard to each entry in that native list; its return does not promise a particular actor population.

Entry Deactivate `0x46863C` similarly returns when `+0x28` is zero; otherwise it exchanges zero and tail-calls virtual `+0x20`. This proves an already-inactive no-op only for that **queued entry deactivation** step.

### Additional Deactivate/Reactivate effect

Before queuing entry deactivation, `0x36D28C` calls virtual `+0x1D0 = 0x36DF5C`. It inspects the object at community-system `+0xF0`, gated by that object's byte `+0xC0`. For zero entryName—the exact node143 payload—it scans its 16-byte pair array `+0x88`, removes every pair whose first UInt64 equals the community ID, and decrements count `+0x94` (`0x245E3F6..E422`). For a named entry it delegates matching-pair lookup to `0x46886C`; the named cold erase continuation is not reviewed here.

That exact list mutation is source-confirmed. The semantic identity of all requests represented by those pairs is **unknown** in this bounded review. It is not labelled a kill-count reset, physical despawn acknowledgement or actor retirement. Therefore an already-inactive pre-community observation alone does not prove that replaying the complete node143 action has no effect. Reactivate includes the same cancellation plus a deactivate/activate transition, so Activate's guard cannot justify replaying it.

## Consequence for the prepared Jason prefix

The exact actions at101/142/86 are ordinary Activate; none selects Reactivate or ResetKillCount, and the community phaseName fields are zero. The native already-active guards are valid evidence for those specific mutations on the same correctly resolved objects. The concern that ordinary community Activate necessarily adds another unit to an entry activation counter is rejected.

This is not a ready repair. The exact prepared stage, original graph retirement, prefab/world leases, resolved native target identity, inactive entry callbacks, saved pending cancellation pairs and downstream car/door/damage setup remain separate contracts. Node143's extra cancellation operation is an explicit remaining boundary. No flags, facts, counts, IDs, journals, actors or queues were changed, and no replacement action or new user test is supplied.

## Evidence and validation

Existing sealed `../community_native/capture_01.json` (SHA256 `A2805CC1E047115D2D2D7188E5001E6713392D82B54CB017E4B5600E6C15E343`) supplies the three original Spawner/SpawnManager registrations, factory/action and population queue chain. Fresh `native_01..12.json` supplies the missing generic Execute binding, CommunityTemplate instantiation/action, community queue consumer, guarded entry mutation and extra cancellation. `verify_review.py` rechecks exact retained bytes, vtable/metadata pointers, action enum and four pinned payloads; `verification_01.json`, `bindings_01.json` and `manifest_01.json` record results. Earlier prefab and installed-Codeware reviews are reused without rerunning their checks.
