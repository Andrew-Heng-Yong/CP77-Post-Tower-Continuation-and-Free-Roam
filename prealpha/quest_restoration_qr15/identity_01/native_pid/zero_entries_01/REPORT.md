# Zero and filtered PersistencySystem2 entries

**A missing nonzero entry key does not prove that its runtime or historical persistent state never existed.** The native writer emits anonymous zero-key placeholders for several conditions, including a present, locked table record failing either required selection bit. The pinned WolvenKit parser preserves these as `Id = 0, Data = null`; it does not retain the discarded key.

This addendum uses the same EXE SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4` and WKit9.1 `WolvenKit.RED4.dll` SHA256 `EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987`. Native addresses are RVAs. It reads file bytes, managed method IL and the coordinator's retained capture02 metadata only. No save, parser invocation, game/process access or native callback was used here.

## Exact native zero branches

Previously bound save virtual `0x2A35150` calls `0x1820E8C` on system `+0x48`. That helper locks the record table, copies its UInt64 keys into a temporary array and releases the table lock. The writer writes that array's **unfiltered count** at `0x2A353ED..3F4`, then processes each key. It does not reduce that count when a row is filtered.

| Condition after the key snapshot | Exact path | Output for that row |
| --- | --- | --- |
| Snapshot key is zero | `0x2A3541C..41F` → `0x2A35453` | One UInt64 zero |
| Nonzero snapshot key no longer resolves to a record | `0x2A35427..432` → `0x2A35453` | One UInt64 zero |
| Locked record's current key differs from the snapshot key | `0x2A35440..450` → `0x2A35453` | Unlock, then one UInt64 zero |
| Present matching record lacks mask `0x04` at byte `+0x79` | `0x2A35470..475` → `0x2A355EB` | One UInt64 zero, then unlock |
| Present matching record lacks mask `0x01` at byte `+0x79` | `0x2A3547B..47D` → `0x2A355EB` | One UInt64 zero, then unlock |
| Both masks are set | `0x2A35483..` | UInt64 key, separate UInt64 class CName, UInt32 body size, body bytes |

The first three zero branches store the previously zeroed `r12` into the UInt64 output temporary (`0x2A3545D`), with size8. The record lock address is reset to zero after every unlock, including the key-mismatch branch. The flag-filtered path explicitly zeroes the output temporary at `0x2A355F2`, writes size8 at `0x2A355FD`, and unlocks through `0x2A355DB`. Neither zero path writes a class, body size or body for that row.

The two flag checks occur **after** a nonzero key has resolved to a matching, locked record. Therefore a zero row can replace an actual record in the native table. This proves a filtered-record possibility, without proving that the record ever held a materialized PS object or assigning its lifetime from those bits. The same format also allows a stale/missing snapshot record. No reset, removal, destruction, quest completion or actor-absence meaning is assigned to either flag.

The snapshot/per-record split and explicit mismatch branches are native defensive paths; this report does not assert that any specific one occurred in the fixture. The original nonzero key is absent from the zero row, so that row cannot be attributed to Jason's car or either candidate component.

## Exact managed parser behavior

`parser_il_02.json` records `PersistencySystem2Parser.Read`, `PS2Entry` accessors/constructor and the invoked `RedTypeManager.Create(Type)` body. Offsets here are managed IL offsets inside `Read`:

- `IL_0045` (decimal69) constructs a fresh `PS2Entry` per declared row. `IL_004F..0054` (79..84) reads one UInt64 directly into its plain `Id` backing field. No hash, mask or class lookup changes this value.
- `IL_0060` (96) branches on `Id == 0` directly to `IL_013B` (315), where the entry is added. No class/body bytes are read. `PS2Entry`'s constructor only calls `System.Object` and leaves the reference-valued `Data` field at its CLR default, null; its getter returns that field directly.
- A nonzero key reads the following UInt64 class hash and UInt32 body size (102 and110). A known class is created and assigned to `Data`, then added. `RedTypeManager.Create(Type)` returns a nonnull `RedBaseClass` or throws.
- Unknown class hashes and caught class/body decode failures instead restore the body position and construct an `UnknownRedClass` (272), retain the class hash and raw body buffer, set that nonnull object as `Data` (310), then add the same entry. The previously read nonzero `Id` is retained.
- The loop counts declared rows, preserves each row and performs no deduplication. The `Id` setter is called only at84. A successfully completed parse therefore has **null Data exactly for zero-key rows**; unknown class/body decoding does not manufacture zero or remove the nonzero key.

This supports checking nonzero key membership independently of whether a body was fully decoded. It does **not** certify field presence or the values of generated property getters; those defaults were not used in this review.

## Completed capture02 and bounded conclusion

Current retained metadata authority is `identity_01/save_inventory/capture_02/manifest.json`, with its successful `capture_02.ps1`. It replaces the partial capture01 metadata reference in the preceding report; capture01 and the preceding native proof remain preserved. The completed manifest records source SHA256 `AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E`, reader hash matching this review, unchanged inputs and no writes/game calls. This addendum does not reopen the save to independently reproduce that extraction.

The completed metadata reports116,594 rows,27,923 null `Data` values,27,922 duplicate keys and29,725 keys at most `0xFFFFFF`. Combining the exact parser contract with those recorded aggregates:

- The27,923 null rows are zero-key placeholders.
- Their27,922 repeated zero keys account for all recorded duplicates; all nonzero keys in that parsed fixture are unique.
- The low24-bit key count includes all27,923 zero placeholders. It is not a count of29,725 live dynamic entities.

The first dynamic-ID list has2,165 entries and excludes10229047. The completed capture separately found no nonzero entry for raw10229047 or the two correctly hashed candidate component keys6695448052237678836 and15311582179580628726. The permissible wording is **no serialized nonzero PS2 entry under those exact three keys in this pinned historical body**. It cannot distinguish no record from a record omitted/replaced by zero, establish the exact component identity, or identify a current actor. No placeholder can be mapped back to any of the three candidates from this metadata.

Class counts include200 `vehiclePersistentDataPS` entries as well as382 `VehicleComponentPS` and384 `vehicleControllerPS` entries. The old766-row wrapper filter omits the former class by its explicit regex; this is a filter limit, not evidence that the other200 entries were missing. No body property default is interpreted here.

The separate `identity_01/vehicle_data_native/REPORT.md` subsequently bound the actual vehicle-data component name and candidate key17113219195054135786. That fourth key was not one of capture02's three membership checks, and the766-row retained wrapper filter does not include the200 vehicle-data rows. Its saved membership is therefore unknown in the metadata reviewed here; no miss is claimed for it.

`verification_01.json` and `manifest_01.json` pin the selected native instruction bytes, managed IL and completed metadata used for these conclusions. `GetConstAccessToPSObject` remains unapproved as a passive diagnostic because the already bound native lookup can allocate/hydrate/attach/initialize state.
