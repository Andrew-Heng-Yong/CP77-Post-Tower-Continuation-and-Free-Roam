# QR3 — Q01 deep verification and controlled repairs

**All 13 remaining Q01 quests received ten-contract investigations and independent cross-review. Q01 is now 16/16 deep-reviewed, including QR2's three.** The full 161-quest project remains incomplete: 145 quests await deep review, and none has full static certification.

## Confirmed defects and staged changes

1. **Brendan: excluded fresh Dumpster activation.** Effective S23/HS1 admission accepts the all-Inactive family, then native full `In1` can activate the explicitly excluded Dumpster quest before the two selected sequels. The serialized repair changes only wrapper edge `1004.True ->1005.In` to existing owned Refused node `1008.In`. All 13 node payloads and saved descendants remain unchanged. This contains invalid new issuance; **a valid earned-history adapter for Spray Paint/Coin Operated Boy remains blocked and is not claimed implemented**. Already-issued/past-preclaim saves are not rolled back.
2. **Bullets: vendor ownership released before helper retirement.** The private Zane helper can loop after the native quest finishes while the wrapper releases the B0 lease. The repair wakes the helper's existing native retirement path on real Finished, waits for its Terminating output before lease release, and handles an already-pending rearm wait separately. Two local decision nodes are added; existing identifiers, native quest/reward body, actor bindings and writes remain. Actual saved transitions and prefab teardown remain live-only.

Exact source pins, failing-before/passing-after checks and implementation limits: [defect registry](defects_and_repairs.json), [explicit allowlist](approved_changes_02.json), [Brendan tests](candidate_01/repair/verification_01/tests.json), [Bullets tests](candidate_01/repair_mq030/verification_01/tests.json). The source-confirmed defects affect three quest rows but are **two unique defects**. Initial 14 FAIL contract dispositions are preserved in the source findings and `pre_repair_status`; corrected containment/cleanup contracts remain CONDITIONAL where full implementation or other evidence is missing.

## Investigation coverage

| Assignment | Quests | Focused checks / mutations | Outcome |
| --- | --- | --- | --- |
| [A: Racing](agents/agent_a/REPORT.md) | The Beast in Me | 273 / 5 | Story/replay owners, Claire calls, native gates and outcomes traced |
| [B: Vehicles](agents/agent_b/REPORT.md) | Murk Man; Dressed to Kill | 210 / 8 | Boot conditions, native vehicle bodies and prefab obligations traced |
| [C: Brendan](agents/agent_c/REPORT.md) | Coin Operated Boy; Spray Paint | 288 / 4 | One shared excluded-admission defect reproduced; later adapter blocked |
| [D: Communications](agents/agent_d/final_result.json) | War Pigs; Sex on Wheels; Over the Edge | 322 / 8 | Actual calls/SMS, real acknowledgements, cleanup and outcomes traced |
| [E: Progression](agents/agent_e/REPORT.md) | Bullets; Sacrum Profanum; The Prophet's Song | 167 / 5 | MQ030 helper defect; other native branches and disjoint seams traced |
| [F: Boxing](agents/agent_f/REPORT.md) | Pacifica; Beat on the Brat | 250 / 5 | Fresh/progressed dispatchers, fight conditions, SMS, rewards and cleanup traced |

These are **1,510 focused assertions**, including fault reproductions; they are not gameplay coverage percentages. Three workers ran concurrently. A hard limit on distinct agent threads required reusing A for E and C for F; all six assignments were processed, with reviews assigned to different workers.

The [new 130 contract findings](contract_status_matrix.csv) contain **33 PASS, 19 APPROVED_DEVIATION, 65 CONDITIONAL, 13 OPAQUE, 0 FAIL, 0 UNKNOWN and 0 LIVE_ONLY-only dispositions** after repair adjudication. The full Q01 set has **45 PASS, 24 APPROVED_DEVIATION, 75 CONDITIONAL and 16 OPAQUE** across 160 contracts. A zero UNKNOWN count does not mean all evidence exists: exact missing static inputs are classified CONDITIONAL/OPAQUE, and live-only limits remain in the per-contract findings. The other 1,450 contract rows retain predecessor status.

All six assignments have independent raw-source reviews: [A](agents/agent_d/reviews/racing.json), [B](agents/agent_e/reviews/vehicles.json), [C](agents/agent_b/reviews/brendan_quarantine.json), [D](agents/agent_f/reviews/communications.json), [E](agents/agent_b/reviews/progression.json), [F](agents/agent_e/reviews/boxing.json). Actual serialized repairs were separately reviewed for [Brendan](agents/agent_d/reviews/brendan_serialized.json) and [Bullets](agents/agent_d/reviews/mq030_serialized.json). Agreement alone was not used to promote a contract.

## Final packaged evidence and preservation

[Independent final archive/ZIP review](agents/agent_d/final_package_review_01/evidence/review.json) passed against the actual pinned PH3 archive: identical 1,574-key inventory; exactly two approved payload changes; all other **1,572 payloads and 50 package files unchanged**. ArchiveXL bytes and registration identities are unchanged. The two new MQ030 IDs are local graph-node IDs, not new ArchiveXL injection IDs. ZIP CRC and all 51 file hashes passed.

Staged artifact: [PTFR_QR3_quest_static_candidate_full_51.zip](candidate_01/PTFR_QR3_quest_static_candidate_full_51.zip), 10,154,520 bytes, SHA256 `B9743BC0D13AD849134460E2909628CD01544807FDD5697CC48975FA5741EF20`. It is **not installed or published**, and its static checks do not establish gameplay success.

Only changed CR2W resources were serialized/rebuilt. [Compile reuse](compile_reuse.json) verifies exact equivalence of the 131 current REDscript sources, compiler/cache inputs and 46 staged managed scripts to QR1's successful compilation; unchanged SCC compilation was not repeated. CR1/PH1/PH2/PH3 unaffected resources/scripts/registrations are preserved, with prior controls reused. [Protection](protection_after.json): **2,676 protected hashes unchanged**, zero game-tree or save-tree metadata changes. No deployment, launch, save/fact edits, release edits or Git publication occurred.

## Corrections and remaining blockers

Two historical global owner-parent exports did not match current native payloads. Bounded fresh extraction supplied authoritative parents and proved the current main-root -> additional-game-elements -> open-world -> minor-activities -> Badlands hierarchy. All six vehicle input pins matched current providers. The older parent exports remain evidence, not current authority. [Exact source corrections](native_owner_gap_resolution.json).

Verifier corrections are explicit: [root socket assertion](verification_corrections.json) now uses native mappin `Inactive`, not generic `In`; Agent D preserved earlier source-parent/path assumptions and corrected MQ049 trigger-name prose; Agent F's cross-review corrected its scalar probe and abbreviated-edge assumptions; B preserved original reports before correcting resolved ancestry wording. [Review resolutions](review_resolutions.json) records the final boundaries. None of these checker/prose corrections caused a gameplay patch.

Static blockers include exact TweakDB reward/economic/vehicle/keycard definitions, streamed prefab/actor/workspot/camera bindings, localization/JV1 presentation semantics, and the unsupported earned-history Brendan adapter. Live-only limits include actual scene/fight/driving/phone execution, owner cancellation, interrupts, rewards and saved-version/reload transitions. No game tests were performed or requested.

Authoritative continuation: [queue.json](queue.json), [checkpoint.json](checkpoint.json), [HANDOFF.md](HANDOFF.md). Next is Q02, beginning with Kabuki, Full Disclosure and Arroyo; reuse inspected MQ025 shared evidence without assuming its other quest contracts are already complete. Future source work must preserve the staged QR3 repairs while distinguishing the still-installed PH3 baseline.
