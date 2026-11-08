# Native saved graph stores — verified limits

## Read one existing save without changing it

**Status:** verified 4 November 2026 for one authentic AutoSave-8 body. This is a fact-store inventory, not an owner/stage decoder. [Exact extraction](../../prealpha/quest_restoration_qr15/stores_autosave8_01/facts.json), [script](../../prealpha/quest_restoration_qr15/read_one_graph_stores.ps1).

**Prerequisites:** an existing allowed slot (`AutoSave-8` or the protected `ManualSave-23`), its readable `sav.dat` and `metadata.9.json`, PowerShell7, the explicit WolvenKit9.1 tooling path used by the script, and a fresh workspace output name. Review the script before use. It opens the source read-only, snapshots into memory, reads all ten physical FactsTable children, and verifies source/metadata hashes afterward. It never calls a save writer or Game API. No save body is modified or made playable. Slot names/metadata do not bind an exact body to a previous live test.

Working directory: `C:\Users\Ayong\Documents\cp77 modding\tower ws`.

```powershell
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -File 'prealpha\quest_restoration_qr15\read_one_graph_stores.ps1' -Slot AutoSave-8 -OutputName stores_autosave8_02
```

**Expected output:** a fresh `prealpha/quest_restoration_qr15/stores_autosave8_02/facts.json`, status `READ_ONLY_PHYSICAL_NATIVE_FACT_TABLES`, ten table arrays, raw UInt32 keys/values, actual source/parser hashes and `source_unchanged=true`. Occupied outputs, reparse inputs, changed source/metadata and unexpected parser/table shapes are refused. Counts may change with a genuinely newer save; the preserved first extraction had11545/0/525/2819/2980/824/13781/879/879/28entries in physical order. Those counts are not target settings or proof for another input.

**Verification:** hash the input before/after; retain physical ordering and all values. Match known named-fact hashes independently to store1. The source proof below maps physical ordering for the exact installed engine. Retain signed/unsigned interpretation explicitly. Missing graph records are not automatically zero, completed or retired.

## Interpret only source-proven store semantics

**Status:** source-confirmed against `Cyberpunk2077.exe` SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. [Native proof and RVAs](../../prealpha/quest_restoration_qr15/saved_graph_state_01/REPORT.md), [17 static checks](../../prealpha/quest_restoration_qr15/saved_graph_state_01/verification_01.json), [sealed evidence](../../prealpha/quest_restoration_qr15/saved_graph_state_01/manifest_01.json). These are static byte/reader/writer proofs, not an execution trace or general support for another engine binary.

| Physical child / native API index | Established meaning | Limit |
| --- | --- | --- |
| 1 | Named facts | Does not enumerate owners. |
| 2 | OPAQUE for owner/stage purposes | Empty is not retirement proof. |
| 3 | Disabled-node execution suppression for `questDisableableNodeDefinition`, restored into phase+0xC8 | Does not prove historical execution, phase termination or released leases. |
| 4 | Logical AND input-signal bitmask, cleared on full satisfaction or reset | Zero may follow success; nonzero may represent only partial input. |
| 5 | Logical XOR first-input latch with explicit reset paths | Not a monotonic visited marker. |
| 6–10 | OPAQUE for complete owner/stage interpretation | Do not label them pending, active, completed or retired without exact class/lifecycle proof. |

The serializer writes ten pointers in ascending physical order. Native GetFact/SetFact indexes1–10 map to those ten children. QR12's reverse stack traversal ordinal is `11 - nativeIndex`; it is not the serialization index. The inspected native manager contains ten pointers and a count at+0x58. The local Codeware `data[11]` declaration is not a verified raw storage layout or an eleventh saved store. Use actual accessor/serialization proof rather than indexing that declaration directly.

## Encode a bound node key correctly

**Prerequisites:** exact source node ID, a proven native phase path/hash and the matching engine hash. An inferred path or guessed first/root ID is insufficient.

The native key is `FNV1a32(LE64((phasePathHash << 32) + nodeId))`, with seed0x811C9DC5 and multiplier0x01000193. Its bytes are **nodeId32 then phasePathHash32**. Copying the source struct's declared field order (`phaseHash,nodeID`) hashes the wrong bytes because the conversion operator packs an integer first.

Native path hashing uses the first UInt16 path element to select a seed, then hashes the complete UInt16-byte array. Seed0 is the normal FNV offset, so source Codeware's plain helper is verified only for root0 paths here. The first extraction left the outer/root binding unknown; the later exact one-body procedure below closes it for that body. Candidate misses and 32-bit reverse-hash matches cannot substitute for collision-aware source binding.

**Expected output/verification:** report source path/node, exact bytes, hash and store-specific interpretation alongside its proof. Validate both key packing and native path-root/seed selection independently before inspecting records. Keep unbound paths UNKNOWN. No complete saved owner/stage decoder was justified by this work.

## Bind the saved resource root without a live plugin

**Status:** recorded PASS,4November2026, for the same pinned AutoSave-8 body only. [Extraction](../../prealpha/quest_restoration_qr15/root_saved_resource_array_01/extraction.json), [independent binding](../../prealpha/quest_restoration_qr15/saved_graph_state_01/inspector_review_01/ROOT_BINDING_ADDENDUM.md), [current bounded report](../../prealpha/quest_restoration_qr15/next_step_01/REPORT.md). This does not identify the body loaded in JF01 or establish owner liveness.

Prerequisites are the exact native EXE hash above, WolvenKit9.1 RED4.dll hash EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987, the existing facts extraction, and exact AutoSave-8 source/metadata pins enforced by the scripts. Read each script first. They use explicit helper-only loading and read-only input handles. Complete decompression is private memory; only the17-byte parent gap is written to evidence. A save writer is never called. The native schema is bound to **SaveVersion**, not the game or resource archive version.

Exact recorded commands, from workspace root:

```powershell
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoLogo -NoProfile -File prealpha/quest_restoration_qr15/capture_root_binding_sources.ps1
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoLogo -NoProfile -File prealpha/quest_restoration_qr15/read_saved_root_array.ps1
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoLogo -NoProfile -File prealpha/quest_restoration_qr15/root_saved_resource_array_01/read_header.ps1
```

These are exact historical-output scripts and now refuse because outputs exist. Preserve those outputs; a future rerun requires a reviewed fresh-output successor and matching inputs. Do not silently substitute a newer AutoSave-8.

Expected outputs: four provider-pinned root resources, `root_saved_resource_array_01/{extraction.json,facts_to_custom_array.bin,header.json}`. Verification requires all13parent/adjacent/table offset-ID controls, exact FactsDB-end→customArray-start bounds, before/after source hashes, and native signed-VLQ decoding that consumes the full gap. Negative/sign-bit counts, noncanonical/overflow/truncated data and unexplained trailing bytes defer. The independent decoder has16controls. Match every UInt64 to uniquely pinned .quest paths; retain hash collisions as unknown.

For this body, SaveVersion277 qualifies for the >=0x8B schema. The17bytes decode to index0=base cyberpunk2077.quest and index1=ep1.quest. Eight source phase links produce startup path[1,0,10,5,2,50,19,5,1]. Native seed1 is0x01800013; phase hash is0xA0D58F1A. The saved ordinal and .quest phase-node0 are separate path elements. A gamedef's ordering is not a substitute for the actual saved array. Sparse immediate-action rows do not certify which startup effects completed.

## Native cleanup ordering and live-inspector boundary

[Exact engine review](../../prealpha/quest_restoration_qr15/saved_graph_state_01/inspector_review_01/REPORT.md) establishes that cut destinations complete recursive handler Uninitialize/map erasure and child removal before Out destinations dispatch. This proves source ordering for the actual cut path, with source graph/writer provenance still required; a killed scalar alone remains insufficient. External prefab/community/spawner release completion is not acknowledged by this proof.

A manual raw-tree inspector remains unqualified: ordinary mutations use the quest lock, but root initialization's outer lifecycle/thread boundary is not closed and teardown clears the global path map after unlocking. TryLockShared and a successful compile would not establish safe coherent capture. No native inspector was built or installed.

## Decode the current saved CommunitySystem component

**Status:** recorded PASS,4November2026, for the same pinned AutoSave-8 body. [Lifecycle report](../../prealpha/quest_restoration_qr15/lifecycle_01/REPORT.md), [exact native schema](../../prealpha/quest_restoration_qr15/lifecycle_01/community_native/schema_02.json), [independent decoder review](../../prealpha/quest_restoration_qr15/lifecycle_01/save_community/review_01/REPORT.md). This is a complete structural byte traversal with limited field semantics, not full saved-actor/quest parity.

Prerequisites: exact EXE hash above, pinned WolvenKit9.1 reader, the unchanged historical save/metadata hashes enforced by the scripts, and fresh workspace outputs. The native save/load/record functions were traced independently. Array counts in this component are **fixed little-endian U32**, unlike the saved quest resource-array count. Actual saved names use the non-dictionary signed-VLQ negative-length ASCII branch; positive Unicode or dictionary formats defer rather than guessing. Version277 qualifies every field in the selected schema.

Exact recorded commands, from workspace root:

```powershell
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoLogo -NoProfile -File prealpha/quest_restoration_qr15/lifecycle_01/save_community/capture.ps1
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr15/lifecycle_01/save_community/decode_full.py
```

The first reads the original read-only into memory and retains only the parsed component's opaque tail and metadata. The second reads those captured bytes only. Outputs `capture_01/{capture.json,community_trailing.bin}` and `decode_02/result.json` now exist; these exact scripts refuse overwriting them. Any future rerun needs a reviewed fresh-output successor and current native/source equivalence. No complete playable save is written.

Expected current-body verification: outer10,294keys,43,473nested rows,3,160spawner keys, all2,191,992tail bytes and all footer sections consumed. The node-size equation independently includes the nodeID, outer count and outer keys, totaling2,274,352bytes. These are observed input statistics, not hardcoded catalogue targets. Fifteen primary malformed-data/mutation controls and22independent controls pass. Earlier partial decode01keeps its footer-opaque label; current complete decode02supersedes it.

Target worldkey17433794865907239043 binds a saved row with active byte1 and reserved/filtered group ID10229047. Native pre-save copies the active byte into row+0x46; this is saved activation intent, possibly retained from an unregistered object. It is not initialized state, a current live vehicle, a completed visual/door setup receipt, or executing ownership. The generic visual flag is also not an established receipt: current script handlers do not directly set it, while indirect native setter effects remain unreviewed.

A targeted two-candidate SDK PersistentID lookup missed parsed PS2 entries. Native entity/stub/PersistentID identity is not bound, and parsed defaults are not necessarily originally serialized properties. Those misses must not be used as no-PS, never-spawned or fresh-stage evidence. See the exact [candidate limits](../../prealpha/quest_restoration_qr15/lifecycle_01/save_community/vehicle_ps_01/result.json).

## Use matching binary evidence for framework ABI

The local research `Red::Spawner` header declares flags08/09, but the current installed Codeware DLL reads10/11, matching the actual native object. [22-check installed-binary binding](../../prealpha/quest_restoration_qr15/lifecycle_01/installed_wrapper_review/REPORT.md) uses exact current DLL hash808D8BCE11641073091DDA33830D06AB98BD9AC710A9A47ECD7EC56E6193440C. Both local PDBs mismatch and were rejected. Do not patch/rebuild a working installed framework merely to match a stale research header.

The normal native PhaseNode support-lease path is now [source-traced](../../prealpha/quest_restoration_qr15/lifecycle_01/prefab_native/REPORT.md), including two ticket lifetimes and shared resolved-NodeRef counts. Last-release disable/reacquisition are queued; no physical-detach acknowledgement at CutControl Out is established. Population and community actions have different dispatch. Already-active ordinary Activate guards do not make complete-prefix replay safe: community Deactivate also cancels matching pending pairs, and car visual/door stage remains unresolved. Refer to [action bindings](../../prealpha/quest_restoration_qr15/lifecycle_01/spawn_action_review/REPORT.md) before choosing preserve/rearm/hold behavior.

## Read-only live partial world state

JF01 established actual CET delivery for public Codeware GetCommunity/GetEntries/IsActive and named fact readings. The observed case was crowd50entries/50active, pre-gunfight5/0 and car population-spawner UNRESOLVED. [Human/log assessment](../../prealpha/quest_restoration_qr15/observations/jf01_01/REPORT.md). Entry counts are not spawned/alive NPC counts; active flags do not expose reference counts or executing graph ownership. Unresolved lookup is not inactive/absent state.

The original source investigation and JF01 observation remain separate. Do not repeat that test or weaken quest admission simply because partial world state is now readable. A later [34-control car binding](../../prealpha/quest_restoration_qr15/runtime_probe_01/car_binding_review_01/REPORT.md) identifies the exact quest-owned vehicle spawner and absolute reference. [JF02's human/log result](../../prealpha/quest_restoration_qr15/observations/jf02_01/REPORT.md) is ABSOLUTE_CAR_UNRESOLVED: the wrapper was not obtained, and the bool/list getters did not run. Their values remain UNKNOWN, not false/zero. Matching source has several null-return sites, which this output does not distinguish. JF02 is closed; no immediate further manual command is qualified. Stored entity-ID lists, if eventually observed, can overlap and are not unique/live actor counts. The prepared Jason adapter still needs a complete non-replaying prefix, saved-stage and support/lease contract. No reset, debug entry, serialization writer, replayed setup/reward or runtime installation follows from these procedures.

## Bind native PersistentID keys and retain absence limits

**Status:** recorded static source and read-only metadata verification,4November2026, for the same pinned EXE, reader and historical AutoSave-8 only. [Identity report](../../prealpha/quest_restoration_qr15/identity_01/REPORT.md), [native hash/serializer](../../prealpha/quest_restoration_qr15/identity_01/native_pid/REPORT.md), [final independent capture review](../../prealpha/quest_restoration_qr15/identity_01/save_inventory/review_01/REPORT_FINAL.md). This is not a complete state decoder or permission to repeat a setup action.

Prerequisites: matching pinned native executable and WolvenKit reader above; exact source/metadata hashes recorded by the preceding component extraction; an inspected helper-only loader and fresh workspace output. Determine the actual component CName from native parameter construction, separately from the requested PS class. Do not guess it from a class label or treat a stub request as a separate numeric ID namespace without conversion evidence.

Native PersistentID is `{entityID UInt64, componentCName UInt64}`. With wrapping UInt64 arithmetic and M=0xC6A4A7935BD1E995: if component=0, return entity; otherwise t=M*component, return M*(entity XOR M*(t XOR (t>>47))). CName spelling is case-sensitive. PS2 entry.Id is the resulting component-record key. Its first `Ids` array instead records enabled dynamic IDs from a separate table; these are different namespaces.

Exact recorded metadata capture, from workspace root:

```powershell
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoLogo -NoProfile -File prealpha/quest_restoration_qr15/identity_01/save_inventory/capture_03.ps1
```

This occupied historical-output script now refuses. Reuse its output; a necessary rerun requires a reviewed fresh-output successor and the same source guards, not substituting the current contents of an autosave slot. It reads the save into private memory, validates hashes before/against/after the captured bytes, never calls a save writer and retains only identity/vehicle metadata. Expected outputs are `capture_03/{manifest.json,ps2_ids.json,vehicle_ps_metadata.json,dynamic_ids.json}`. Membership checks must cover the complete entry list outside the selected-class filter. Parsed properties/defaults are not serialized-presence or event-completion receipts.

For this body,116,594PS2rows contain27,923anonymous zero entries; those account for all27,922duplicate keys. Native saving can filter a present matching record into a bare UInt64zero, discarding its original key and body. The matching managed parser retains nonzero keys even when class/body decoding falls back to UnknownRedClass. Thus a missing nonzero key proves only absence at that serialized address, with filtered history still unresolved. Do not assign zero placeholders to a specific car or count them as live low-ID actors.

The exact native vehicle-data component is `vehiclePersistentDataPS`, CName0xF8B5D41E08E5736F. The native stub getter constructs it directly from stub+0x40; EntityID10229047 gives key17113219195054135786. Global four-key capture finds no match; it also retains all200parsed native vehicle-data payloads, avoiding the older wrapper-only filter. This does not establish missing current car state or pending/applied visual-door setup. Source population request identity and actual asynchronous materialization/liveness are separate properties.

**Unsafe getter boundary:** registered `GetConstAccessToPSObject` enables record allocation and can hydrate/create, attach and initialize PS state. It is not qualified as a read-only CET observation; no call was made. An apparent getter name, returned handle or registration result does not establish nonmutation. No new live API, console test, native plugin or repair follows from this procedure.

## Inspect retained quest handler and event projections

**Status:** recorded4November2026 for the same pinned historical body/EXE. [Result and limits](../../prealpha/quest_restoration_qr15/event_stage_01/REPORT.md), [native quest lifecycle](../../prealpha/quest_restoration_qr15/event_stage_01/quest_handlers/REPORT.md), [vehicle dispatch/lifecycle](../../prealpha/quest_restoration_qr15/event_stage_01/vehicle_events/REPORT.md). This is not a complete saved-state decoder or current executing-owner observation.

Prerequisites are the exact pins above, inspected helper-only loader, source-bound root/phase paths and a fresh output successor. The recorded `event_stage_01/capture_components.ps1` command in its [handoff](../../prealpha/quest_restoration_qr15/event_stage_01/HANDOFF.md) verifies source hashes before/in-memory/after reading and exact node offsets, then retains nine selected quest child spans totaling374629bytes. Complete raw/managed comparisons cover the customArray words and eventManager rows. No full decompressed save is written. Occupied outputs refuse; do not rerun a historical capture to replace its evidence.

`customArray` is a fixed-U32-count UInt16 word list containing length-prefixed paths. Native phase initialization interns the complete path; ordinary cut cleanup leaves cached paths. Registry membership therefore does not certify an active owner or completed node. The inspected body has13112paths, including the original Jason startup path.

The native saved EventManager record is `{typeToken UInt64,phaseHash UInt32,nodeID UInt32}`. The managed reader splits nodeID into two UInt16 properties; use the full32-bit value for address matching. Removal clears the slot to `{0,0,0x0000FFFF}` and registration can reuse it. A missing original registration cannot distinguish finished-before-cut from pending-then-cancelled. Query a PhaseNode's **parent** context hash and its node ID as well as descendant contexts; querying only the child hash misses the parent's handler.

Recorded pure metadata analyses are `analyze_components.py`, `analyze_ancestors.py` and authoritative native-width `analyze_native_layout.py`, all under `event_stage_01/`. Commands and outputs are in its handoff. They refuse occupied outputs, read captured evidence only, and provide13malformed-framing plus7native-width/address controls, including a damaged upper-nodeID case. They do not simulate the engine or certify gameplay. Preserve explicit OPAQUE labels for unbound subtype fields in other selected blocks.

Vehicle startup103/104 have no final-application wait on the exact reviewed paths. PS submission, queue consumption, forwarding and actual actor mutation are separate stages. The door wrapper sets a generic flag after queuing six children; disabled door values can also have other writers. PersistencySystem's own serializer does not retain its live request ring, while higher-level save barriers and actor-queue persistence remain unproved. An empty **quest** QueuedData block is not a live PS/actor queue observation. Do not use any of these projections as an applied-setup receipt or permission to replay setup.
