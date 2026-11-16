# Selected mid-quest resume scope

15 November 2026. After reviewing stage difficulty, the user selected **only these four types** for new mid-quest resume implementation. This decision supersedes the earlier broad most-stage target and the proposal to add selected message stages. [Earlier difficulty review](mid_quest_resume_scope_20261115.md) · [Implementation roadmap](../ROADMAP.md#mid-quest-resume-after-the-tower)

| Included type | Required boundary |
| --- | --- |
| Earned item waiting for collection | Entitlement and earlier payments are settled. Restore the collection listener and required support without repeating grants or setup. The Gig's Cassius tattoo stage is a source-reviewed candidate. |
| Travelling somewhere or waiting to talk | V has not entered the conversation or scripted sequence. The destination, actor, interaction and original ownership must be recoverable. An interrupted call hidden behind a travel objective does not qualify. |
| Simple timer | The clock, pending callback, expiry and successor are known, with no excluded interrupted state that must be reconstructed alongside it. Preserve remaining time or an observed natural expiry without restarting the wait. |
| Multiple unfinished objectives | Preserve every outstanding supported branch, completed inputs, choices, counters and separate final rewards. Epistrophy's partial join is a useful fixture, subject to its cooperating owners and support being qualified. |

Membership in these types makes a stage a candidate for implementation. Runtime support still requires exact state and owner evidence, playable advancement and save/reload qualification. The selected types do not establish a measured percentage of quest coverage. The first candidate should be a contained earned collection or travel/talk boundary. The Gig already completed and was saved successfully in the earlier RD2 adapter test; transaction details and gameplay reload were unobserved. A new native fixture still needs exact original-owner evidence and arbitration with that installed adapter. [Later The Gig result](../prealpha/resume_dispatcher_rd2_20261112_01/observations/cassius_20261112_2355/REPORT.md) · [Parallel-objective evidence](../prealpha/quest_resume_contracts_rc2_20261114_01/REPORT.md)

All interruption stages outside those four types are omitted from the implementation plan and documented as unsupported. In particular:

| Omitted stage | Note for the player and developer |
| --- | --- |
| Pending text delivery, message read/reply state, expiring reply choices or a pending call handoff | New resume support for these states will not be implemented under this scope. A timer or objective label does not override this exclusion when the handoff requires restoring already-pending phone state. |
| A call, conversation, cutscene or scripted interaction already underway | Playback position, choices, actor bindings and acknowledgements are outside the resume target. A settled wait before talking may still qualify. |
| Active combat, a chase, race or coordinated vehicle/actor sequence | Mid-action health, roles, commands and choreography will not be reconstructed. An independently qualified stable travel or waiting boundary may still qualify. |
| Confiscated equipment or an unresolved item/reward transfer | Preserve escrow, existing items and receipts. Do not replay the transfer or invent its result. Sweet Dreams' existing confiscation-to-recovery exception remains. |

These exclusions concern the state being resumed. Native texts, calls, scenes and combat may still start and run normally later in a quest after a supported boundary resumes. Existing reviewed adapters and qualifying fresh post-Tower starts retain their existing behavior. This decision does not remove ordinary quest content or authorize uninstalling existing support.

Classify the whole cooperating state, not just one node. Recheck after any native progression before retirement and before restoring the family. If a timer has naturally advanced into an excluded pending successor, defer that family rather than rewinding the timer or restoring the excluded state. If multiple objectives include an excluded pending branch, resume a separate supported branch only when ownership, shared joins, cleanup and rewards prove it independent. Otherwise defer that inseparable family. Do not drop optional phone listeners when they also control cleanup or an earned follow-up. Existing whole-quest and narrower exceptions remain in force even when an objective appears to fit one of the four types. [Exception notes](quest_resume_exceptions.md)

**Over the Edge's Falco/Reyes pending message handoff is omitted from the active implementation and playtest queue.** Its v0.1.10 result remains a registration/save success with message delivery stalled. The test did not qualify gameplay continuation or reload. Retain its source, build and AutoSave-17 evidence; do not keep developing or retesting message delivery as a required milestone. A later, independently settled collection stage of the same quest would need its own evidence and would not inherit qualification from this pilot. [Recorded run](../prealpha/universal_resume_native_registration_20261115_01/observations_01/REPORT.md)

Use one shared mechanism for the selected four types. Finish implementation and offline verification for all four before the live handoff test. The final Step 5 run verifies genuine Tower completion, actual advancement, save/reload and preservation of prior outcomes and rewards. Include negative controls that ensure omitted states do not receive new resume owners. A stage outside scope follows normal Tower cleanup and can remain unavailable afterward; there is no automatic objective skip, rewind, forced completion or fallback.

The [roadmap and past-work review](mid_quest_resume_roadmap_review_20261115.md) records successful older adapters, reusable native foundations and the next qualification gates.

This scope note changes the development and test plan. The installed v0.1.10 build is unchanged; enforcing the selected scope in a successor dispatcher remains implementation work.
