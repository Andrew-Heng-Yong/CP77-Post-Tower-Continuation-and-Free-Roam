# QR15 — native car identity and persistence

**The saved car ID and its canonical vehicle-state key are now source-bound. The available save data still does not establish whether the original visual/door setup ran. No runtime repair or successor package is justified by a missing key.** Installed Core, diagnostics and saves remain unchanged. No further JF01/JF02 command or repeat gameplay test is requested.

## What is established

The population route consumes saved associated ID `10229047` (`0x9C1537`) as an EntityID. It copies that value through the reserved-ID array, stub request and stub field `+0x40`; no numeric StubID conversion occurs on those bound paths. The ordinary allocator can supply the same field. The value belongs to the high dynamic allocation interval, which alone does not establish persistence eligibility or absence of runtime state. [Native origin and 17 controls](entity_origin/REPORT.md).

The actual native PersistentID hash matches the SDK, including entity/component field order, wrapping arithmetic and zero handling. PS2 record IDs are those UInt64 hash results; the requested PS class is separate metadata. The first PS2 `Ids` list is a different structure: an enabled subset of the dynamic persistence-status table. Its omission of an ID does not establish that the full runtime table lacked a false-valued row. [32 native controls and 12 arithmetic controls](native_pid/REPORT.md).

The exact native vehicle-data component is `vehiclePersistentDataPS`, CName `0xF8B5D41E08E5736F`. Both the ordinary vehicle initializer and a native stub accessor construct that component's PersistentID. The stub accessor uses `stub+0x40` directly, so the canonical lookup address for the bound stub is established independently of the remaining actual-actor assignment question. For `10229047`, its key is **17113219195054135786** (`0xED7E5E302C9919EA`). The two earlier controller component calculations were numerically correct for their inputs; they did not identify this native destruction-state component. [14 native controls](vehicle_data_native/REPORT.md).

| Component input | Exact key for EntityID 10229047 | Captured nonzero membership |
| --- | --- | --- |
| None / raw entity | 10229047 | No match |
| controller | 6695448052237678836 | No match |
| VehicleController | 15311582179580628726 | No match |
| vehiclePersistentDataPS, native source-bound component | 17113219195054135786 | No match |

These membership queries run over **all 116,594 parsed PS2 rows**, outside the vehicle-class filter. The final capture additionally retains the parsed payloads of all 200 native vehiclePersistentDataPS records; it does not rely on the older 766-row wrapper-only selection. The final selected vehicle metadata contains 966 rows. [Successful capture source](save_inventory/capture_03.ps1), [capture manifest](save_inventory/capture_03/manifest.json), [27-control independent review](save_inventory/review_01/REPORT_FINAL.md).

## Why the missing key is insufficient

The exact native saver snapshots the component-record keys, writes the unfiltered count, and can replace an existing matching record with an anonymous UInt64 zero when either required selection bit is absent. Missing/stale snapshot records and zero keys also produce zero placeholders. No original key, class or body survives those zero rows.

The matching WolvenKit parser preserves zero rows as `Id=0, Data=null`; unknown classes or decode failures retain a nonzero key and nonnull UnknownRedClass instead. The 27,923 zero/null rows account for all 27,922 duplicate keys in this capture. They cannot be attributed back to the car. The 29,725 low-valued row keys include all those zeros and are not a live-entity count. [26-control native writer/parser review](native_pid/zero_entries_01/REPORT.md).

Consequently, the valid conclusion is **no serialized nonzero record under the exact canonical key in this particular saved body**. It does not establish never spawned, absent current actor, no runtime PS, incomplete setup, or a safe permission to replay nodes 103/104. Parsed property getters and metadata property names are also not certificates of originally serialized field presence or quest-event completion.

The [exact registration/flag lifecycle](native_pid/flags_lifecycle_01/REPORT.md) closes this distinction beyond a hypothetical parser limitation. Ordinary stub creation can register an ID with a false persistence value while permitting runtime PS access. Record mask1 tracks installed serialized-buffer data; mask4 selects persistence and can change independently of the payload. Two hypothetical pending/applied setup states whose mask4 remains clear produce the same anonymous-zero PS2 projection, regardless of payload differences. This is a conditional source counterexample to using the key miss as a stage guard. It does **not** prove either history occurred, that two complete saves are identical, or that other graph/event evidence cannot distinguish them.

The candidate key is not an exact historical/current actor-state certificate. The [registered population and materialization trace](actor_assignment/REPORT_03.md) binds the requested ID through real queue consumption, per-ID selection, the actual spawner factory and the copied EntityInitializeRequest. The native terminal initializer copies that field to entity+0x48 unchanged. This proves a conditional source property, without requiring actual game execution. The later asynchronous job handoff remains unbound; no actual historical/current materialization or liveness is inferred. Predecessor evidence01/02 and the earlier partial report remain preserved.

## Read-only diagnostic boundary

The registered `GetConstAccessToPSObject` native handler enables allocation. Its lookup can create or hydrate a PS record, attach it and invoke initialization. It is **not qualified as an observational CET command**, despite its name. No such call was made. This rejects an unsafe proposed observation method; it is not a diagnostic or framework defect. [Exact native registration and lookup](native_pid/REPORT.md).

The installed Codeware flag ABI finding from the [previous lifecycle step](../lifecycle_01/REPORT.md) is unchanged: the DLL is correct and the research header is stale. There is no justified Codeware correction or sampler change.

## Inputs, provenance and limits

- Native executable SHA256: `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`.
- WolvenKit RED4 reader SHA256: `EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987`.
- Historical AutoSave-8 body SHA256: `AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E`; metadata SHA256: `BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E`.

The capture checks these save hashes before reading, against the captured bytes, and after reading; it rejects links, refuses occupied output directories and never writes a playable save or retains a complete decompressed body. This historical body is **not proven to be the body loaded during JF01/JF02**. Current liveness cannot be recovered by relabeling its provenance.

The first capture stopped after partial metadata because PowerShell's case-insensitive automatic `$Matches` variable overwrote a similarly named list. Fresh capture02 corrects the variable name; fresh capture03 adds the fourth native key and 200 native payloads. Partial and predecessor outputs remain intact. Capture03's inherited prose saying “raw and two” is stale; its actual four-key source query and independent review are authoritative. No old proof is edited to conceal these limitations.

The separate controls validate selected native source links, arithmetic, metadata extraction and parser semantics. They overlap in inputs and are not summed into quest coverage or gameplay PASS. Existing unchanged Core compile/package results are reused rather than rebuilt.

## Repair disposition

The required discriminator remains **pending versus already-applied visual/door setup and queued events**, together with the full startup and shared courier preservation contract. A valid adapter must handle both histories without replaying setup, changing saved identities, fabricating a receipt, clearing the shared courier increment, or weakening the old HS1 snapshot fingerprint. Canonical-key absence does not provide that discriminator.

No runtime source/resource, dependency, installed diagnostic, save/fact or release artifact is modified. No compiler, archive/ZIP builder, installer, game launch, process attachment, CUA, publication or push is used. `completion.json` and the preservation files select the precise remaining source work; there is no new installation or manual gameplay action to perform.
