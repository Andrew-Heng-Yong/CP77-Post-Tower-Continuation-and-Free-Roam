# KOLD MIRAGE prepared entry correction — KM3

Installed on 16 November 2026 over `RD10_MID_QUEST_RESUME_RETIRED`, following the user's request to “fix kold mirage now”. Only the combined archive changed, and only one of its 1,748 resources differs: `towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase`. Installation verification is complete. The user subsequently reported “ok the fix passed”; the start correction is recorded as USER_REPORTED_PASS. [Bounded retest observation](OBSERVATION_20261116.md).

## Finding

The paired ManualSave-31/32 evidence shows KOLD already prepared before the Tower: `mq016_active=1`, with the native freezer approach/scan waits registered. The six selected native owner registrations are absent after the ending. The post-Tower private owner is issued but has not entered; its saved node 196 waits for `mq015_active=0 AND MinorQuestAndSts`. The live check confirmed the first predicate and an unblocked content system. [Original fixture evidence](../installed_qualification_20261115_02/REPORT.md)

Fresh extraction from all 135 installed archive indices confirms that the original token precedes KOLD's active flag and freezer setup. The already approved KM1 admission accepts this otherwise unopened `active=1` state, but its copied prefix was requesting the initial token again. The installed engine's scheduler reader/writer and update functions also bind the two saves' 20-byte `questContentSystem` records: both have state 0, no queued token, no blocking sources and no queued manager operations. The remaining float is not an active countdown in state 0. Unblocked alone does not supply another token. This does not establish a global scheduler defect or imply that new phone messages cannot arrive.

The paired saves and current sources corroborate the previously prepared state. Runtime eligibility does not contain a save slot, personal save hash or fabricated pre-Tower certificate. It remains bounded by the existing admitted unopened-state contract; unrelated mod-written facts are not certified by this review.

## Change

Private pause node **196** retains its ID, outer AND and exact `mq015_active=0` condition. Its token operand now distinguishes two states:

- **Previously prepared, unopened (`mq016_active=1`):** recheck the complete existing admission guard, with Issued required to be 1, then wait for the native content-lock condition to be unblocked. All 63 Inactive journal requirements, seven other zero MQ016 progress facts, startup/support requirements, Permit and untouched Entered/Finished/Fault receipts remain required.
- **Not previously prepared (`mq016_active=0`):** retain the exact original `MinorQuestAndSts` token condition.

The existing saved owner continues through its original successor. There is no owner reissue, new controller, global token injection, journal/fact reset, forced completion or new mid-quest resume admission. Nodes, connections, original milestone waits, resource paths, XL registrations and prefab ownership are unchanged. Every downstream resource, including KM2's freezer/Nix scenes, rewards, pickup, outcomes and cleanup, is byte-identical. The broader retired resume mechanism remains retired.

## Verification and installation

- **565 checks passed:** independent cooked-graph comparison, unchanged edges and support fields, fresh/prepared condition matrix, rejection of changed progress/receipts and each non-Inactive journal state, plus the bounded paired-save evidence.
- **All 1,748 packed resources read back:** exactly one approved replacement; 1,747 identical payloads. The replacement has one current provider. No depot, injection name or generated node ID was added or renamed; XL bytes are unchanged.
- **Compile equivalence:** all 148 REDscript sources, compiler and base bytecode match the retirement build's successful compilation. A fresh transaction inventory pins 151 inputs including the current cache sidecar. No REDscript change or new compile occurred.
- **Full Core51 package verified:** all ZIP members reopened and hashed. Fifteen installation/recovery fixture actions passed, including rollback, interrupted staging/replacement/receipt and refusal while the game is running.
- **Actual deployment passed:** closed-game preflight, one-file installation, all 51 Core paths and 26 dependencies verified, **436 save files unchanged**, unrelated game metadata preserved, exact predecessor archive retained and rollback readiness verified. No game launch or save write occurred.

| Identity | SHA256 |
| --- | --- |
| Installed archive | `E615D4D594A3F752B76DE316BB305D2201AE788456AC34E5334FAFE4D088AEB7` |
| Changed private entry | `51A900CE31B733D1C5CDBFCF493E02A11A1C7D32897B0B050D0E012C24FACAC8` |
| Installed manifest | `D7D6EDC420052701621F9EE409075302E6AF5B1B931EABA5EF9A911526F2C7FF` |

[Graph assessment](work/assessment.json) · [Archive readback](work/archive_01/readback.json) · [Compile equivalence](work/compile_equivalence.json) · [Transaction fixtures](work/fixture_results.json) · [Installed manifest](work/deployment_01/installed_manifest_01.json) · [Installation receipt](work/deployment_01/install.json) · [Verification](work/deployment_01/verify.json) · [Rollback readiness](work/deployment_01/rollback_readiness.json)

Raw game exports, save projections, disassembly, archives and recovery files remain in the ignored `work/` directory. The investigation helpers read files only; they do not access a running game process. The stopped initial broad save serializer produced no result and wrote no save; the final reader explicitly projects scalars and raw scheduler bytes.

## Current gameplay result and limits

The user accepted the KOLD start fix after the requested retest. No repeat opening test is requested. Exact handler transitions, full quest completion, every outcome, reward idempotence and new-slot reload are not independently established by that report. The [original test card](TEST_CARD.md) retains the earlier procedure and its limits. Previous successful Space Oddity, Ezekiel and Highwayman opening observations remain accepted. No release or GitHub push was performed for KM3. File rollback does not undo later gameplay or saves.
