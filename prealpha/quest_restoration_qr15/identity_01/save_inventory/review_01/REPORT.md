# Independent review of capture03 identity metadata

**Capture03 supports only this finding: the pinned historical PS2 body contains no serialized nonzero entry under canonical vehicle-data candidate key `17113219195054135786` (`0xED7E5E302C9919EA`) for EntityID candidate10229047.** The recorded full scan also misses raw10229047 and the two earlier component probes. This does not prove PS absence, current actor identity or completed/incomplete quest setup.

## Extraction and source binding

The reviewed extraction is `../capture_03.ps1`; current retained results are the four JSON files in `../capture_03/`. This review **does not invoke that script, reopen the save, call a parser, access a game process or make a native callback**. Capture01's partial outputs and completed capture02 remain preserved.

`capture_ast_01.json` records a static PowerShell AST review. The four candidate strings are exactly:

| Input | UInt64 key |
| --- | --- |
| Raw EntityID probe | 10229047 |
| Prior `controller` probe | 6695448052237678836 |
| Prior `VehicleController` probe | 15311582179580628726 |
| Native vehicle-data component `vehiclePersistentDataPS` | 17113219195054135786 |

The candidate condition is a direct child of the full `foreach($entry in $ps.Entries)` loop, outside the vehicle-class filter. Every entry's raw UInt64 `Id` becomes a decimal string before that filter; matches are accumulated in a separate `candidateMatches` typed list. The source has no references to automatic `$Matches`, avoiding the case-insensitive variable collision that affected capture01. The completed manifest records `candidate_matches: []` across116,594 entries.

The script checks source and metadata hashes before reading, verifies the captured bytes' SHA256, checks source and metadata hashes again after processing, and writes a success manifest only after those guards. Its referenced prior receipt and completed capture03 manifest agree on:

- Save body SHA256: `AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E`.
- Metadata SHA256: `BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E`.
- WKit9.1 reader SHA256: `EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987`, independently matched here to the local managed DLL bytes.

Thus the retained extraction records the same pinned body before/snapshot/after its read. This review verifies the source guards and receipt; it does not independently rehash the original save. No binding to the user's exact currently loaded session follows.

The capture03 source and manifest's descriptive `limits` string still says “raw and two” component-hash candidates. The actual four-element query is raw plus **three** component keys. This is stale description text; the reviewed query and retained results are explicit. Sealed capture03 files were not edited.

## Hash and native component contract

The preceding sealed native PID review binds memory fields `{entity UInt64 at0, component CName UInt64 at8}`, exact helper RVA `0x409010`, wrapping UInt64 arithmetic with magic `0xC6A4A7935BD1E995`, and PS2 entry.Id as that full native key. The requested state class is a separate argument and a separately serialized class hash. This review pins that32-check proof and the26-check native zero/parser proof without rerunning their older workflows.

The separate `../../vehicle_data_native/REPORT.md` binds the ordinary vehicle initializer `0x593118` to `vehicleBaseObject`'s actual instance virtual `+0x160`. This review independently checks the captured bytes for its initializer, name helper and lookup against EXE SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`:

- `0x59321A` reads entity from vehicle `+0x48`; the initializer puts it in PID field0 and the name-helper result in field8 before calling `0x9A2514`.
- `0x9A24AC` supplies exact CName `0xF8B5D41E08E5736F` for spelling/case `vehiclePersistentDataPS`.
- `0x9A2514` receives that PID and passes the requested class separately to PersistencySystem virtual `+0x1B0`.

`review_capture.py` independently calculates the CNames and all four keys using the previously bound formula. Arithmetic inversion of each result returns10229047 as a control. This is a control on those exact inputs, not an identity decoder for every other class/factory or saved row. The old raw/`controller`/`VehicleController` probes are not additional native component-owner proof.

## Retained rows and independent membership checks

Capture03 retains966 selected IDs/classes:382 `VehicleComponentPS`,384 `vehicleControllerPS`, and **200 `vehiclePersistentDataPS`**. These counts match the complete manifest's class totals. All retained IDs are unique nonzero canonical UInt64 decimal strings. All200 vehicle-data rows include parseable JSON payloads and a property-name inventory captured before JSON export.

Python independently searches all966 retained IDs, including all200 vehicle-data IDs, and finds none of the four candidates. `key_lookups_01.json` records those exact integer searches and distinguishes them from the completed coordinator's global `candidate_matches` scan. The other115,628 parsed entry IDs are not individually retained here; their global membership result relies on the reviewed full-scan source and completed receipt.

The previous766 wrapper IDs/classes are unchanged from capture02. Class-count aggregates, the first PS2 `Ids` sequence and dynamic-ID metadata are also unchanged. The addition is the200 previously excluded vehicle-data rows and their payloads. Dynamic maps remain uninterpreted.

Payload availability does not certify that every exported property was explicitly serialized: managed constructors/getters and JSON export can expose defaults. This review uses IDs, class counts and payload-container validity only. It does not interpret destruction, doors, visual setup, queued events or property-default values.

## Zero-row boundary

The pinned native writer writes its snapshot row count before applying selection checks. A present matching record missing either mask `0x04` or `0x01` at record `+0x79` can become a single UInt64 zero instead of its key/class/body. Stale or missing snapshot records also produce zero. The row loses its original key.

The pinned parser stores each UInt64 entry.Id before class/body decoding, retains nonzero IDs through `UnknownRedClass` fallback, and leaves `Data` null exactly for zero rows in a completed parse. Capture03's aggregates therefore mean:

-27,923 null rows are anonymous zero-key placeholders.
-27,922 duplicate IDs are fully explained by repeated zero; nonzero parsed keys are unique.
-29,725 low24-bit keys include those zero placeholders, leaving1,802 nonzero low24-bit keys. These are not an actor count.

The separate first `Ids` list contains2,165 enabled dynamic IDs and excludes10229047. It is not a component-key census.

The canonical-key miss establishes **no serialized nonzero PS2 record under that exact key in this pinned historical body**. It cannot distinguish no record from a record replaced by an anonymous zero placeholder, assign any placeholder to Jason's car, prove that a runtime object never existed, or certify a quest stage. Current actor/body binding, persistence eligibility, other native factory routes and cleanup/event completion remain separate requirements. `GetConstAccessToPSObject` remains unsuitable as a passive diagnostic because its native path can create or hydrate state.

`verification_01.json`, `key_lookups_01.json` and `manifest_01.json` seal the source/metadata review, arithmetic and input hashes. Original-save reads, parser/capture invocations, game calls, runtime changes and builds are zero in this review. No manual test or repair is proposed.
