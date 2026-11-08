# Step 1 source inventory for Johnny dialogue removal

Successors: the [Step 1 completion report](../johnny_dialogue_coverage_20261107_01/REPORT.md) accounts for this source inventory, and the [verified Step 2 successor](../johnny_dialogue_index_20261107_02/REPORT.md) completes its identified index extension. The [Steps 1/2 scope audit](../johnny_dialogue_scope_audit_20261107_01/REPORT.md) and [active work ledger](../johnny_dialogue_scope_audit_20261107_01/active_work_ledger.json) correct broad work implications and stale task statuses. The original capture assessment follows unchanged; its full-corpus counts are not measured post-Tower work.

7 November 2026. The [seven-step plan](../../docs/johnny_dialogue_removal_plan_20261107.md) is recorded and linked from the project knowledge index. Step 1 has a verified baseline and a first resource-reference inventory. Complete post-Tower dialogue coverage still requires the follow-up below.

The baseline is HH1 on QR19, selected through [current state](../../docs/knowledge/current-state.md) and the exact [installed manifest](../heavy_hearts_hh1/deployment_01/installed_manifest_01.json). Its manifest SHA256 is recorded in the [summary](step1_01/summary.json).

| Verified input or measured inventory | Count |
| --- | ---: |
| Installed Core paths | 51 |
| Installed dependency and diagnostic paths | 26 |
| Candidate package paths | 51 |
| Candidate source resources and matching combined-archive members | 1,581 |
| Private scenes in that payload | 139 |
| Installed runtime source files examined | 232 |
| ArchiveXL phase registrations | 904 |
| PTFR registrations within that total | 827 |
| Archives indexed | 134 |
| Quest and scene provider entries in the global census | 15,581 |
| Unique resource keys within that graph census | 15,575 |
| Unique scene keys within that census | 8,895 |
| Captured resource depots | 11,025 |
| Captured provider payloads | 11,068 |
| Captured native scenes | 4,100 |
| Pending queries in the captured reference pass | 0 |

The provider-entry and registration counts include stored variants and repeated bindings. They measure source inventory. Connected inputs, condition feasibility and execution on a particular save require later review.

The final check performed 13,039 input and retained-payload hash comparisons with zero discrepancies. All 1,581 combined-archive members match the candidate source inventory, and an independent Python implementation confirms their depot keys. Archive metadata checks found zero changes during capture. The managed installation and candidate checks include the required Atelier correction. Capture and verification write their outputs within this task workspace.

The inventory follows imports and graph-reference candidates from every private resource, installed source literals and phase registrations. It follows quest, scene, gamedef, entity, appearance and streaming dependencies. ArchiveXL parent graphs are recorded as attachment interfaces. The complete parent campaign remains a separate availability question.

## Remaining work in step 1

1. Inventory the 16 distinct referenced .conversations resources and determine their dialogue dependencies. Review the 113 recorded speech-API candidate lines for dynamic paths and dialogue triggered outside ordinary scenes. Other referenced support includes 418 .scenerid paths, 2,669 .workspot paths and 280 .animgraph paths. Their relevance needs actor and caller context before expanding the audit.
2. Account for the 4,513 scene keys in the global census outside the captured reference closure. Use reverse references and entry evidence to identify post-Tower relevance. Preserve unavailable and uncertain cases in the denominator.
3. Resolve or bound 55 opaque provider payloads spanning 37 depots. These comprise 54 streaming-sector payloads with decoder failures, including the existing WolvenKit world-node limitation, and one native q303_10_concert_braindance.scene payload rejected for questSetFadeInOut_NodeType.fadeColor. The decoder errors and exact payload hashes are retained.
4. Review 91 missing reference candidates, 41 depots with multiple providers and 9,729 archive entries without resolved depot names. Missing candidates include optional external-mod assets and lexical references. They require source context before becoming gameplay findings. Provider enumeration order does not establish the winning provider.

The [unresolved inventory](step1_01/unresolved.json), [dependency inventory](step1_01/dependency_inventory.json) and [global scenes outside the closure](step1_01/scene_census_outside_closure.json) retain the concrete inputs for that follow-up. Step 2 can use this corpus after the remaining source boundaries have been reviewed.

## Evidence and tooling

The [summary](step1_01/summary.json) pins the original and supplemental capture hashes and all task tools. Bulk inventories and native payloads are locally ignored by Git. The task checkpoint identifies the current next action.

The structured YAML pass preserves all 827 bindings accepted by the original bounded parser and captures 77 additional connection-form bindings, with zero parser errors. The corrected path scan resolves 28 paths truncated by the initial pattern at hyphenated directory names. The supplemental capture records 43 further provider payloads and reaches zero pending queries.

The first supplemental attempt stopped on a timestamp comparison after PowerShell converted JSON dates into DateTime values. Independent metadata checks confirmed that the archives had retained their recorded values. The successor compares UTC ticks. The failed script and log remain preserved under evidence_02/ and step1_01/capture_additions.log.

The scripts prepare.py, capture_sources.ps1, capture_registrations.ps1, refine_inventory.py, capture_additions.ps1 and summarize.py provide the task-specific capture and verification. Their output names refer to this preserved run. A future capture needs a fresh successor workspace. The investigation has zero game writes and zero save writes.
