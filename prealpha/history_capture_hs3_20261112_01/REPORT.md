# Reliable player history capture — 12 November 2026

**Step 2 implementation is complete as a staged candidate; deployment and gameplay qualification remain pending.** `candidate_04` replaces the snapshot REDscript, its CET exporter and the consolidated archive. All 51 Core paths remain stable. The currently installed `QP2_QUEST_HISTORY_AUTOLOAD` files remain unchanged.

This supplies prospective history for later resume work. It does not enable additional resumed quests or replace their owners. Step 1 remains accepted as completed by the user. The source registry's bounded evidence still limits what individual observations can establish.

## Capture before native cleanup

Two minimal official-resource patches insert a capture gate before native journal damage. Both source providers were identified and their exact payloads pinned in `evidence_01/plan.json` and independently read back from the packed archive.

| Route | Resource and graph | Replaced edge | Purpose |
| --- | --- | --- | --- |
| Direct Tower/Reed | `ep1\quest\main_quests\q307\phases\q307_01_pickup.questphase`, `root/10` | `97.Out → 169.In` | Capture before contact removal and the connected bulk journal failure nodes |
| Earlier Hanako cutoff | `base\quest\main_quests\part1\q115\phases\q115_00_hanako.questphase`, `root/3/113` | `97.Out → 46.In` | Capture before the q115 point-of-no-return writer and its bulk journal updates; q307 skips its corresponding branch when that cutoff already occurred |

Each insertion adds seven local node IDs, 60000–60006. It clears its own result, records the route, increments its own ticket, opens capture, waits for acknowledgement or a native 30-second real-time condition, closes capture and records that the gate passed. The last diagnostic is **not** a capture-success receipt. The q115 capture guard correctly expects its native point fact still to be zero on this side of node 46.

All original nodes, support scopes, prefabs, sockets and other edges are retained. The gate dominates all 33 reachable q307 bulk writers and all 31 q115 writers in their modified graphs. Native q307 node 170 was already disconnected and remains so. Native journal failures, quest cuts and genuine ending cleanup remain in place; no native shutdown or ending-completion fact is fabricated. The timeout lets the original ending continue even if the new script cannot commit.

The archive has 1,740 members: every one of the existing 1,738 payloads is byte-identical, plus the two overrides. There are no new ArchiveXL registrations. The current 54 archive/pc XL files and 21 supplemental plugin XL files were checked separately from resource providers. Neither of the two plugin archives supplies either patched depot; the supplemental XL files contain no quest-phase injections. Three unrelated log symlinks were recorded and not followed.

## Save-local capture and reload handling

An additive `CaptureArchiveHS3` system stores a schema/fingerprint, route, ticket, revision, observations, stability flags, previous committed observations and export token inside the player's save. Existing HS1 saved fields and all 158 row definitions/indices are unchanged; HS1 gains a capture ticket.

The generated catalogue covers 218 current selected/separate/activity records and retains legacy observations. It contains 4,982 journal references, 18,685 source fact names and 1,086 item quantity IDs, derived from 5,109 source resources. This is a field inventory, not measured stage-resume coverage. Love Rollercoaster, The Shape of a Pony and Career Opportunities are included. Machine Gun includes Deliver Skippy, the existing weapon quantity and its exact lethal/nonlethal/total counter facts.

The new system reads on its queued simulation requests after player attachment and with no pending journal changes. Two passes compare journal state, counter, optional/tracked values, facts and quantities. A changing field is retained as unstable and cannot be trusted by later adapters. Missing journal entries and unavailable item records remain unknown. It publishes extended data and the existing HS1 baseline in one queued request before acknowledging the native gate. A later unsuccessful ticket cannot qualify an older snapshot for new admission.

The former restore path could erase a valid frozen certificate after an early zero-valued boundary read. The candidate preserves a valid serialized certificate without making that boundary assumption. It retains saved unknown/future-schema data while refusing to consume incompatible data. It never promotes unfrozen legacy rows after cleanup merely because those rows resemble a prior export.

The fixed revision-159 comparison and filename override are removed. Existing public compatibility methods remain callable but cannot select that test history. Valid old frozen HS1 certificates remain useful on their original saves; already-cleared flags, missing HS3 fields and destroyed native handlers are not reconstructed.

## Verified recovery export

Both the existing schema-1 baseline and extended schema-3 history export from each loaded save. The exporter uses completed cached strings rather than reading saved arrays from CET. A transient export lease, epoch and revision bind each operation to the current loaded system, including save switches that reuse the same numeric epoch/revision.

Export uses a temporary file, checked write/flush/close, exact readback, rename and final readback before acknowledgement. A different existing file is preserved; a missing file is recreated from authoritative frozen save data. Export failure does not erase that data. There is no global latest-file selection or automatic external-history import. A separate reviewed recovery import/migration is still needed to repair older damaged saves.

The maximum estimated export is 3,352,864 bytes against an 8 MiB limit. The two capture passes have 98 scheduled ticks (4.9 seconds of nominal delays), excluding engine execution and scheduling. Neither figure establishes actual frame cost or capture duration. The 30-second timeout and engine save serialization still require live qualification.

## Validation and exact selection

| Evidence | Result and boundary |
| --- | --- |
| `compile_04/result.json` | PASS: all 148 exact registered REDscript inputs; installed sources/cache unchanged |
| `archive_02/readback.json` | PASS: full 1,740-member payload readback and preservation of the 1,738 predecessor payloads |
| `verification_04/verification.json` and `semantic_diff.json` | PASS: 22 source/graph/package checks, exact three-file replacement, saved identity preservation, guards and catalogue fields |
| `verification_01/export_fixtures.json` | PASS: 14 tests executing the actual Lua exporter, including I/O failures and save switches; the selected candidate has the identical Lua hash |
| `verification_06/protocol_fixtures.json` | PASS: 19 actual-source predicate and cooked gate parameter checks; no engine scheduling/persistence claim |
| `verification_07/plugin_providers.json` | PASS: supplemental resource and registration checks |
| `fixtures_saves_01` and `verification_saves_01` | PASS: 24 bounded checks against four current real saves and the candidate source; [save-fixture report](verification_saves_01/REPORT.md). No gameplay execution |
| `checkpoint.json` | Final artifact/source pins and selected candidate; explicitly not installed |

Earlier compile/pack/verifier attempts are preserved. They exposed an incorrect GetEntryByString argument type, a typed delay property requirement, the q115 pre-writer guard, and overstrict verifier assumptions. Those were corrected before candidate 04 was selected. No failed attempt was deployed. Runtime/gameplay, installation and future-save compatibility are distinct pending gates.

## Remaining limits

The new data records stage and reward-related observations; it does not prove every one-time reward receipt. Quantities cannot identify an item's individual instance or whether a reward was already spent. Dynamic/unbound source fields, engine graph stacks, exact dialogue cursors, combat/actor state and remaining timers are not reconstructed. Unsupported observations remain unknown. Later stage/owner review must consume this evidence conservatively.

Manual Save 26 is suitable for prospective testing before Reed's cutoff. Its current body matches the earlier pinned save and it tracks Deliver Skippy. Existing AutoSave-2 is already past the capture gate, so it can test old-save compatibility but cannot demonstrate a new pre-cleanup capture. The new read-only fixtures do not replace a genuine run through capture, hospital, Tower completion and reload. Use the [test card](TEST_CARD.md) for that remaining qualification; no prior accepted quest fixture needs repeating.
