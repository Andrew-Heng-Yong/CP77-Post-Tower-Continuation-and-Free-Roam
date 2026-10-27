# CR1 consolidated resource repair

**Installed locally on 26 October 2026; gameplay validation pending.** CR1 repairs the resource-selection regression found by the audit of all 81 restored side jobs. The user requested implementation and excluded further identification of the 11 missing markers.

The original consolidation overwrote 30 corrective resource definitions with older versions. CR1 selects each replacement explicitly from hash-verified preconsolidation backups and verifies its intended behavior against the earlier repair evidence. It replaces only `archive/pc/mod/zzzz_PTFR_Combined.archive`. The complete package still contains the same 51 install paths; the other 50 files and 1,142 of 1,172 archive members remain byte-identical to S30. No new overlay or resource path is added.

## Repairs restored

| Area | Restored behavior |
| --- | --- |
| This Corrosion / Yoko | Four component conversation choices and their continuations |
| Paid in Full / Viktor | Two native debt choices with their scoped prerequisites |
| The Gun / Shoot to Thrill / Wilson | Gun-order scene dispatch and vendor owner release/reacquisition acknowledgement |
| Beat on the Brat / Fred | Native boxing introduction selector and the later FS1 private-scene distance/rearm fix |
| Bullets / Zane | Shop rearm after the encounter releases the service |
| Big in Japan / Dennis | Fresh-entry acknowledgement that the phone listener has been issued |
| Shared phone cleanup | 49 root nodes and six inline courier nodes, covering 17 character branches and NCPD |
| Epistrophy / Don't Lose Your Mind | S25 shared-controller receipt and S22 exclusion, coordinated with the retained S29 adoption/message guards |
| Entry admission | Prior native journal-state and sibling-owner guards, preserving runtime history protections |
| Other conflicting resources | H10 entitlement/mirror leases, the exact PA6 Rogue lipsync-index correction, and U10 scoped retaliation gates |

The [per-resource review](../prealpha/consolidation_repair_cr1/donor_review/review_01.md) describes all 30 selections. Restored node IDs, scene interfaces, casts and dialogue are preserved. Fred's `cookingPlatform` metadata follows the previously installed FS1 serialized source. The S30 trio, 48-scene English lipmap, SR1 visual repairs, MQ058 completion receipt, current runtime scripts, and River exclusion are retained.

These changes replace resource definitions. They do not restart already-issued quest owners or clear progress facts. Whether an owner already serialized into a save revisits a repaired node remains a live-test question.

## Verification and package

- Independent checks against 70 pinned repair inputs: **2,057 assertions, 30 groups, all passed**. The same checks detect the known regressions in S30 as a negative control.
- Packed archive: **all 1,172 members read back exactly**, with no collisions in 67 other installed archives.
- Full **64-source** script compilation with installed public Codeware 1.21.1 and EquipmentEX: passed. Compilation outputs stayed in the workspace.
- Installer: **38 fixture actions passed**, including six interruption points, partial-copy recovery, refusal of later target changes, and path-boundary checks.
- Actual closed-game `Validate`, `Install`, `Verify`, and `ValidateRollback`: passed. **All 51 installed hashes match**; the previous archive is recoverable.
- Protection baseline: **498 unaffected files and all 295 save files/names unchanged**. The sole changed file is the combined archive. No assistant game launch, fact/save edit, framework change, Git push or public release.

The full local package is `prealpha/consolidation_repair_cr1/candidate_01/dist/Post-Tower-Continuation-and-Free-Roam-CR1-unreleased.zip` (51 entries, SHA-256 `E50D2A253107953C3FBB5426D01D4563CE1B9983C3786CF5EFBB00CAFBA9A75E`). It is unreleased. The repaired archive SHA-256 is `BDDAE9BB742041B74B10B2C2F814C286BD4C740452E517835952968B1B59BC31`.

The selected installer is [deploy_02.ps1](../prealpha/consolidation_repair_cr1/deploy_02.ps1), with `candidate_01/install_manifest_02.json` SHA-256 `B93D40F32706B8106570FB27B0139B44C554558473D80771C98FA22F508CFD73`. Version 01 failed an isolated fixture because PowerShell converted a null backup argument to an empty string. Version 02 uses a verified null value and passed the complete suite before any real installation. Preserve the historical scripts and proofs; use successors for changes.

## Recovery and remaining work

The previous full 51-file package is archived in `candidate_01/archived_previous`. The actual replacement backup and receipt are in `recovery/consolidation_repair_cr1_01`. With the game closed, run CR1 `deploy_02.ps1 -Action ValidateRollback`, then `-Action Rollback` if rollback is desired. **Roll back CR1 before S30 or any older installation layer.** File rollback does not undo progress already written into a save. No real rollback was performed during installation verification.

Raymond Chandler Evening remains unresolved for the captured inactive-journal/`mq040_active=1` case. The original quest owner's retirement cannot be established from the available capture or `q307_main_game_killed` alone: two different native paths write that fact, and only one contains MQ040. No fact bypass or second quest owner was introduced. The [Raymond record](../prealpha/consolidation_repair_cr1/raymond/assessment_01.md) pins the evidence. MQ018/MQ028 partial-state candidates remain unconfirmed.

Cold load, affected conversations, phone completion, rewards and save/reload still require gameplay checks. This release does not claim that every restored job works on every prior save, or that the 11-marker difference is explained.

Final machine-readable evidence is under `prealpha/consolidation_repair_cr1/candidate_01/assessment_01.json`, with independent validation under `prealpha/consolidation_repair_cr1/validation`. Future builds must retain the explicit donor-selection contract; do not regenerate the consolidated archive using the historical overwrite-order builder.
