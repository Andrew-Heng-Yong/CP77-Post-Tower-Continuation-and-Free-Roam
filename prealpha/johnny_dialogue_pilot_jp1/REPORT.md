# JP1 two-quest dialogue pilot

Installed 7 November 2026 over HH1 for the user's in-game test. JP1 removes **25 Johnny dialogue events and 12 V dialogue events** across KOLD MIRAGE and Sweet Dreams. It bypasses **four conversation options in two menus**. All 25 caller-qualified indexed Johnny speech events in these two quest closures are covered. Gameplay verification is pending.

The original edited notes are preserved in `input_03/user_notes.txt`. The user subsequently approved the seven omitted Johnny lines, the Bartmoss identification exchange and additional V responses to Johnny. `input_03/plan.json` records every exact event/choice identity, wording variants, source hashes and V classification. Six additional V events were selected as direct responses to Johnny. The prior explicit cuts remain selected, including the SGI-deck observation. V's independent freezer observation, wake-up confusion, realization about the scavs, laptop self-assessment and conversations with Nix/Stefan remain. Addressee metadata alone did not determine whether V was reacting to Johnny.

## Progression and identity

In the private freezer scene, the timed exit from section 28 now enters shared section 42 directly, bypassing the Bartmoss identification menu and its two reply branches. This preserves the save's existing recognition flag; no recognition fact is set or reset. The native inspection condition still selects the appropriate later wording for that value.

Section 284 now enters native exit section 90, bypassing the later two-option Johnny menu. Section 90 retains its non-dialogue events, original duration, timed workspot output and native journal-completion output. The original Close/Open controls, deck inspection and Take cyberdeck interaction remain connected with their native conditions, pickup, inventory and reward ownership. No completion fact, item grant, controller or prerequisite bypass was added.

Both old menu nodes and their option IDs remain serialized to preserve saved identities and native exits. They are unreachable from normal scene entry. A save already active inside either menu is not qualified for the new removal behavior; the test should start before entering the affected scene. All retained event/node/resource identities and all other node payloads are preserved. No new depot or ArchiveXL phase registration was introduced.

This first pilot preserves fixed authored section timing and unselected animation/workspot/camera events. Silent gaps can remain. The in-game test should report timing or presentation issues before further retiming changes.

The payload targets the current private PTFR scene copies. Original native resources are unchanged. A legacy/native saved owner using another scene provider is not qualified by this pilot; an observed occurrence on such a route needs its own caller and save-state review.

## Validation and installation

- `validation_05/scene_verification.json` constrains cooked readback to 37 exact speech-event removals, associated persistent/debug reference cleanup and two reviewed edge replacements. All other graph payloads, conditions, actor bindings, localization/line tables, support references and fixed section durations match the source.
- `validation_05/provider_collisions.json` checked all 134 installed archive indices. Each changed private scene has one exact provider. Existing depot keys and byte-identical XL registrations preserve both namespaces.
- `validation_05/archive_readback.json` verifies every one of the 1,581 packed payloads. Exactly three private scene payloads changed; 1,578 payloads remain byte-identical. The other 50 Core files, including the XL, remain unchanged.
- Resource-only changes required no new REDscript compile. The complete current 148-source/151-input inventory was verified against the inherited compile proof, with only the normal 16-byte timestamp sidecar refreshed before deployment.
- `fixture_results.json` records 22 actions across eight isolated installation/rollback fixtures, including actual Core51 bytes, crash recovery, interrupted rollback, a running-game guard and unknown-file refusal.
- `deployment_01/` records closed-game preflight, `INSTALLED_VERIFIED`, `VERIFIED_AFTER` and `ROLLBACK_READY`. All 51 Core files, 26 dependencies and 313 save files verified; save names/bytes, dependency bytes and unmanaged game metadata were preserved. No game was launched and no save was written.

Installed archive SHA256: `E90954970A5EFC7AF420FE6363E25A381B919FAEA9172B80835B5A10FE2E64F5`.

The [installed manifest](deployment_01/installed_manifest_01.json) identifies the exact package and transaction. The HH1 archive recovery copy is under `recovery/core_jp1_01/old/`. File rollback does not reverse saved progress. No real rollback was performed.

## Next action

Follow the [test card](TEST_CARD.md). The user will run the game and report the actual routes and observations. No runtime success, universal save transition or full-game Johnny-removal coverage is claimed. The Step 2 SQLite index remains the pre-JP1 source snapshot; use this candidate's readbacks and decision manifest for the three changed scenes. The rest of Step 3/4 remains bounded to its own reviewed and tested scopes.
