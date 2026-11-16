# Post Tower Continuation and Free Roam — Roadmap

Resume scope and status reviewed 15 November 2026; other work streams retain their separately dated evidence. This roadmap separates implemented mechanisms from evidence still needed. The original chronological record is [preserved](docs/history/instructions/2026-10-29/ROADMAP.original.md); old percentages and contradictory active-sounding paragraphs are not current coverage measurements.

## Current baseline

The installed RD10 Core is the baseline for post-Tower restoration polish. Exact mid-quest resume and older mid-journey admission are retired from the active build. Exact installation and evidence are selected by [current state](docs/knowledge/current-state.md). Earlier Core work includes QP2 over ML1 with QR10D01/D00E diagnostics. The user confirmed KOLD MIRAGE's speech removals and accepted KM2's Open → scan → Take → Nix route on 8 November. SD1 removes Sweet Dreams’ residual Johnny actor and presentation and preserves its gameplay sequence. Live testing awaits an intact genuine post-Tower pre-braindance fixture, and the current completed quest is preserved. The KM1 entry rule and PE1 [Boolean setup admission](docs/prepared_encounter_policy_20261108.md) remain. The user deferred the wider marker-count investigation. Counters, later stages and three unresolved native trace scopes remain protected. Bounded observations include Ronald enrollment, the natural El Capitan sampler, Jeopardy, the Voodoo Treasure first claim and KOLD's delayed marker restoration. QR18 and QR19 eligible-fixture qualification remain pending. The prepared beta remains a separate VD1 snapshot. [Current state and bounded observations](docs/knowledge/current-state.md)

QP2 installs the Small Man, Big Mouth, Heaviest of Hearts and Bartmoss contact fixes, the Judy travel text guard and the Tower rooftop handoff repair. In-game quest paths, rooftop setup and saved-owner transitions await qualification. [Combined repairs](prealpha/quest_parity_qp2/REPORT.md)

ML1 adds the first monk’s English lip-sync mappings to JB4. The install, 313 save-file checks and JB4 rollback readiness verified. Playback in Losing My Religion remains open. [Monk repair](prealpha/monk_lipsync_ml1_jb4/REPORT.md)

JB4 includes Johnny removal Batches 5 and 6 and the profile setup patch. Live quest flow, tattoo handling, setup failures and mid-scene save transitions remain open. The four Batch 6 caller or gate leads and untraced ambient speech still need source review. [Deployment and coverage](prealpha/johnny_batch6_jb4/REPORT.md)

<a id="any-point-quest-resume-after-the-tower"></a>

## Mid-quest resume after The Tower

**Paused.** The exact-resume experiment and the previous older entry rules are archived outside the game. The remaining steps below are for when this workstream reopens. [Archive and rollback evidence](prealpha/mid_quest_resume_retire_20261115_01/REPORT.md)

The final 15 November selection limits new mid-quest resume implementation to **earned items waiting for collection, travelling somewhere or waiting to talk, simple timers, and multiple unfinished objectives**. All other interruption stages are omitted and documented as unsupported, including pending texts/replies and exact mid-call, scene, encounter or transfer state. A timer or parallel objective with an inseparable excluded pending branch also defers. Native calls, messages and encounters can still run normally after a supported boundary resumes. For each supported state, preserve its verified execution position, branch progress, choices, counters and pending effects. [Selected scope and omission notes](docs/mid_quest_resume_four_types_20261115.md)

The target is exact continuation at any eligible interruption point across quests within the four selected types. One shared mechanism discovers pending state from the same-session checkpoint, binds it to matching native source and restores the cooperating owners. Named quests are fixtures for the shared path. Existing saved owners retain their progression paths. Record unsupported intervals and already-reviewed fallbacks in the exception notes. [Shared discovery contract](docs/quest_resume_contract.md#shared-discovery-and-handoff) · [Mid-quest resume exceptions](docs/quest_resume_exceptions.md)

The review below separates earlier earned-stage adapters from the new native handoff. The Gig completed at Cassius; Epistrophy advanced through Northside and Wellsprings to 5/7; Kabuki passed loss/retry/win; Rite of Passage and Small Man, Big Mouth completed on their observed adapter routes. These results retain their exact limits and need no repeat merely to recreate evidence. They do not qualify a new native owner. [Past work, source review and remaining gaps](docs/mid_quest_resume_roadmap_review_20261115.md)

| Step | Current evidence | Remaining work |
| --- | --- | --- |
| 1. Source and stage contracts | RC2 maps 160 selected quests and saved control states. Cassius tattoo collection is the first selected fixture. | Use the source inventory as input to the shared discovery path. Expand coverage where source and checkpoint evidence qualify the actual state. [Fixture selection](prealpha/quest_resume_stage_selection_20261115_01/REPORT.md) |
| 2. Capture before cleanup | v0.1.4 passed the genuine Reed MS26 → MS29 capture/save/reload test with exact payload equality. | Reuse this foundation. Hanako and external actor/support coverage remain separately unqualified. Captured bytes alone do not qualify continuation. |
| 3. Implement the shared handoff | Cassius passed the offline ownership, journal, prefab and rollback test in v0.1.12. [Test and evidence](prealpha/quest_resume_cassius_handoff_20261115_01/REPORT.md) | Carry the shared handoff into Step 4. Gameplay verification is part of Step 5. |
| 4. Finish all four types offline | Runtime admission is still Cassius-specific. Moving Heat’s original travel subtree passed binding, restore and rollback fixtures. Rite of Passage supplies a missing-owner control. [Travel evidence](prealpha/quest_resume_travel_20261115_01/REPORT.md) | Generalize discovery and the runtime transaction. Qualify the same code across more quests and execution points using checkpoint and source data. Cover both clocks, supported successors, partial joins, support ownership and reward preservation. |
| 5. Integrated acceptance | Pending completion of all four types and their offline checks. | Prepare compatible fixtures and verify the test build. Finish Step 5 with the live handoff through genuine Tower cleanup in the same session. Exercise all four types, verify advancement and save/reload, and check for duplicate owners and rewards. |

[RC2 source contracts](prealpha/quest_resume_contracts_rc2_20261114_01/REPORT.md) · [Step 2 live result](prealpha/universal_resume_checkpoint_probe_20261114_01/observations_04/REPORT.md) · [Native wait fixtures](prealpha/universal_resume_step3_20261114_01/REPORT.md) · [Live guard](prealpha/universal_resume_save_session_20261115_01/observations_01/REPORT.md) · [v0.1.10 result](prealpha/universal_resume_native_registration_20261115_01/observations_01/REPORT.md)

The next implementation sequence is:

1. **Selected.** Use The Gig at Cassius. AutoSave-13 is the preferred pre-cutoff fixture and Manual Save 31 is the fallback. Both retain the native collection wait and earned payment. The recorded cleanup and S22 takeover define the competing-owner check. [Fixture selection](prealpha/quest_resume_stage_selection_20261115_01/REPORT.md)
2. **Diagnostic candidate verified.** v0.1.11 selects the original Cassius collection stage at the Reed cutoff and passes the shared phase, handler and notification fixtures. Step 3 uses those primitives for the ownership, journal and support transaction. [Candidate report](prealpha/quest_resume_cassius_shared_20261115_01/REPORT.md)
3. **Cassius offline test passed.** The v0.1.12 test uses the preserved cutoff and save evidence. The fixtures cover eligibility, prefab and journal readiness, duplicate-owner prevention and rollback before a fallback can claim. [Run the test](prealpha/quest_resume_cassius_handoff_20261115_01/REPORT.md#run-the-offline-test)
4. Replace the Cassius-only runtime entry with checkpoint-driven discovery and one source-driven handoff. Reuse the retirement, support, journal and rollback transaction. Cassius and Moving Heat are initial fixtures. Demonstrate the same path on other quests and different moments within a quest. For simple timers, cover both clocks and recheck the successor if expiry wins the race. Defer if the successor needs an excluded pending state. For parallel objectives, verify partial joins and preserve settled outcomes and rewards.
5. After all four types pass offline, prepare the integrated test build and fixtures. The final check in Step 5 is the live run from a genuine Reed cutoff through Tower cleanup and credits in the same session. Group compatible base-game and EP1 samples in one run where possible. Verify that each selected stage advances, progress survives save/reload, and owners and rewards are issued once. Include inactive, terminal, excluded and existing-owner controls in the acceptance plan.

Older post-Tower saves can use their existing reviewed adapters when evidence qualifies. A checkpoint from the same ending session is required for the new native handoff; the old global-latest history file does not supply that identity. The shared feature remains incomplete. When the feature reopens, resume Step 4 offline implementation and qualification across all four types. The first full live handoff run is the final Step 5 check, after all four types are implemented and pass offline. [Continuation contract](docs/quest_resume_contract.md)

## Static parity audit

The source-pinned vanilla-parity audit follows the [handoff](docs/maintenance/instruction-system-20261029/HANDOFF.md) and [audit method](docs/knowledge/static-parity-audits.md).

It must reconcile catalogue denominators; traverse phases, scenes and actual entry sockets recursively; trace actor/prefab/phone/cleanup/reward/saved-owner dependencies; identify intentional adaptations; report confirmed gaps separately from opaque/unknown/live-only cases; and preserve the historical regression controls.

## Work streams after evidence

| Stream | Implemented evidence | Remaining work/limits |
| --- | --- | --- |
| Ending and direct continuation | Retained-session handoff; LC4 cover and later installed lineage | Per-route watched/skipped credit and regression evidence remains bounded to actual fixtures |
| World, NPCs, interactions | BA1/WA2/WA3, LR1/LR2, VD1 and recorded user observations | Native dependency/owner completeness; excluded progress-gated/fight families and opaque group1013 |
| Quests and phones | Bounded gig/side-job entries; CR1 corrective donors; PH1 listeners, PH2 ID correction, PH3 shared studios | Full recursive lifecycle, optional route, cleanup, reward and save-state parity; catalogue denominator reconciliation |
| Unfinished jobs | Scoped stage adapters and offline native handler and timer readback | One shared continuation lifecycle for the four selected stage types, with all other interruption states omitted. Qualify supported owners, callbacks and timers, shared support, Johnny edits, actual advancement and reload. [Universal resume work](prealpha/universal_resume_20261114_01/REPORT.md) |
| Skippy | SC3 ambient loop; observed remarks/hologram behavior | Progressed Machine Gun resume-state limitation and unmeasured dialogue/return routes |
| Housing | H1/H5/H6/HS2 mechanisms and user fixtures | Broader native entitlement/service/reload coverage; preserve €$25,000 H10 and Kerry exception |
| Restriction profiles | Current implant-focused JSON/runtime implementation | Proposed selectable profile product design and conservative migration requirements |
| Release/reproducibility | Stable 51-path consolidation; prepared beta proof; guarded deploy/rollback | Current all-lineage rebuild recipe, stale final-beta test, PH3-to-beta integration if later requested, future-save upgrade fixtures |

## Release qualification

Preserve vanilla Tower, cured/2079/relationship state, R4 limits, progression, exactly-once rewards and original ownership. Verify current-input compilation where scripts change; archive and registration readback; save/external-mod preservation; deployment interruption recovery; appropriate runtime and save/reload behavior. Keep untested and opaque cases explicit.

Future stable-save continuity is a requirement, not an already-passed test. No automatic publication, game launch, quest/fact mutation or historical installer rerun follows from this roadmap. Policy and pipeline questions remain visible in [conflicts](docs/knowledge/conflicts.md).
