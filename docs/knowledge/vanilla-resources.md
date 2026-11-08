# Vanilla resource extraction, editing and rebuilding

## V1 — Locate and extract the actual provider

**Status:** recorded working API/workflow in PH1–PH3 captures. No extraction or resource modification was performed for instruction maintenance.

**Prerequisites:** exact depot paths, fresh output folder, readable current game archives, WolvenKit 9.1 runtime at `research/sidejobs_s28/tooling/wolvenkit_9_1_0/package`, and explicit write scope for investigation outputs.

Load only the helper API from the repository root:

```powershell
. ./tools/build_phase2a.ps1 -HelpersOnly -WolvenKitRoot `
  (Join-Path (Get-Location).Path 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
```

The default script is an old builder with an 8.20 tool path. Omitting `-HelpersOnly` can execute build mutations. Do not dot-source arbitrary builders for one helper.

The exact extraction pattern is in `diagnostics/phone_expansion_ph3_20261029_01/capture_studio_04.ps1` and `diagnostics/phone_restoration_preparation_20261029_01/capture_01.ps1`. They use:

- `HashService.Load()` and `FNV1A64HashAlgorithm.HashString(depot)` for archive lookup.
- `ArchiveReader.ReadArchive(path, hashService, [ref]archive)`, requiring `NoError`.
- `archive.Files[key].Extract(memoryStream)` to obtain exact payload bytes.
- SHA256 of extracted bytes; original archive identity and every matching provider are retained.

**Procedure:** adapt the inspected capture into a fresh task; enumerate relevant archives under `GAME/archive/pc` including base, EP1 and mods; retain all matches, not the first. Record archive paths/metadata, depot/hash key, raw output, payload hash and selected-provider rationale. A mod can override a native resource; an archive filename alone is not winner proof. Do not hash tens of gigabytes of unchanged archives merely to repeat a bounded lookup.

**Expected output:** provider/inventory JSON, exact raw resources and selected exports in the fresh directory. **Verify:** no missing/ambiguous query silently passes; actual winners are resolved; source hashes match the baseline. Historical 134-archive counts are not today's census.

The named capture scripts have pinned output paths. Their literal historical invocations are references, not current commands to rerun; `capture_studio_04.ps1` writes `native_04`. Do not replace those outputs.

## V2 — Deserialize and export

**Status:** recorded working for supported CR2W types. Known unsupported studio/world sectors are explicitly excluded from decode claims.

After V1 and helper loading, the exact existing API calls are:

```powershell
$resource = Read-Cr2wFile $rawPath
Export-Cr2wJson $resource $jsonPath
```

**Prerequisites:** verified raw input; a fresh export path. **Outputs:** CR2W object/root and WolvenKit JSON. **Verify:** root type, source/export hashes, expected fields, and handle references. JSON handles use both definitions and references; do not compare raw HandleId numbers as semantic identity.

WolvenKit 9.1 can fail casting `DynamicBaseClass` to `worldNode` on native sectors (PH3 studios and WA3 group1013 are concrete cases). Retain raw bytes and the error. A descriptor or byte-string match is not a full decoded placement audit. Do not “fix” this by exporting a lossy object or promoting an unfiltered original into a new owner. A reviewed exact-native-prefab reference, as in PH3, preserves the opaque sector and carries that limitation forward.

## V3 — Modify an authorized private successor

**Status:** derived editing procedure, with successful mechanisms in PH1, LR2 and WA3. Not an instruction to modify them during documentation work.

**Prerequisites:** intended semantic diff; explicit native/modified resource separation; exact nodes, sockets, saved identities, references and prefab ownership; independent verifier plan.

Use `DeepCopy()` for copied nodes and handles. In `tools/build_fresh_gigs_b5.ps1`, inspect `ClearB5`, `EdgesB5`, `RebuildB5` and `RewireB5`; PH1 demonstrates copying them via bounded helper extraction. Nested graphs must have their edge connections rebuilt against the copied sockets recursively. A shallow copy or a top-level-only edge repair can serialize successfully while losing behavior. Do not execute the whole B5 builder as a library.

`New-InputNode`, `New-SetFactNode`, `New-FactCondition`, `Set-RedHandleProperty`, `Connect-QuestSockets` and `Write-Cr2wFile` are implemented by the loaded helper API. Follow a matching vanilla structure rather than inventing engine properties. Preserve both resource-root `PhasePrefabs` and node-owned `PhaseInstancePrefabs` obligations; they are distinct.

Write/readback shape used by current builders:

```powershell
Write-Cr2wFile $resource $freshOutput
$readback = Read-Cr2wFile $freshOutput
Export-Cr2wJson $readback $freshReadbackJson
```

**Expected outputs:** private raw resource plus independent readback JSON. **Verify:** normalized semantic diff, all retained nodes/sockets/nested edges, entry/exit/cut paths, exact actor/marker/community/variant bindings, owned fact writes only where intended, no unintended native progression/reward reset. Record every official-resource override. Serialization success is only the first gate.

## V4 — Preserve a vanilla baseline

**Status:** current evidence convention; repository has no single universal pristine-baseline directory.

Use V1's source manifest as the authority. Historical caches under `research/q307_extracted`, `research/sidejobs_s29/native_03` and `diagnostics/restored_audit_20261025_01` are reusable only after current-provider/payload-hash equivalence is established. Do not label a modded winner, private copy or old export “vanilla” without its archive/depot/hash provenance. Keep untouched bytes, decoding errors and comparisons in the task evidence; never rewrite the baseline in place.
