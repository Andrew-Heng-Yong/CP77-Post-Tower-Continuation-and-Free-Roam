# Post Tower Continuation and Free Roam — Project

## Purpose and behavior

Continue free roam after Cyberpunk 2077: Phantom Liberty's **The Tower** ending, while preserving the ending and its consequences. The ending runs normally through its final scenes, credits and cleanup; continuation returns in the retained session without loading a pre-ending/PONR save.

Preserve cured V, 2079 state and Tower relationship outcomes. Do not revive Johnny's engram, visible projection, takeover, Relic powers or Nocturne. Reviewed supporting voice-only Johnny is the specific R4 presentation compromise, subject to cast and route review. This is not a happier-ending rewrite or a new 2079 campaign.

## Authorities

- [AGENTS.md](AGENTS.md): concise operating invariants and task boundaries.
- [Current state](docs/knowledge/current-state.md): exact local installation, source/package manifests, beta separation and observation limits.
- [Knowledge base](docs/knowledge/README.md): task-specific development procedures and their verified/historical status.
- [ROADMAP.md](ROADMAP.md): work still required, without unsupported percentages.
- [Conflicts](docs/knowledge/conflicts.md): unresolved requirements, explicit supersessions and stale tooling.

The original 155 KB PROJECT record is preserved [byte-for-byte](docs/history/instructions/2026-10-29/PROJECT.original.md). Its dated updates and prototypes are evidence, not a current build recipe. [Traceability](docs/maintenance/instruction-system-20261029/TRACEABILITY.md) maps preserved instructions and policy changes.

## Restoration policy

Restore compatible native sandbox systems and selected activities while preserving progress, ownership and exactly-once rewards. Completed stays completed. Current work focuses on polishing post-Tower restoration. Exact mid-quest resume and new starts through older resume rules are paused, with their prior files archived outside the game. The retained 15 November scope for future mid-quest work covers four types: earned items waiting for collection, travelling somewhere or waiting to talk, simple timers, and multiple unfinished objectives. Other interruption stages, including pending texts/replies, mid-call/scene/encounter states and unresolved transfers, are omitted and documented as unsupported. Exact continuation from the verified pre-ending execution state remains required for each supported state. When reopened, exact resume will use the shared native mechanism. The selected types do not establish measured coverage. Previously claimed owners can continue from their saved state. Fresh restoration uses accepted Inactive quest history. Do not invent pre-Tower history, replay setup, clear journals or force gates to make an entry eligible. [Selected four-type scope and omission notes](docs/mid_quest_resume_four_types_20261115.md) · [Mid-quest resume plan](ROADMAP.md#mid-quest-resume-after-the-tower) · [Mid-quest resume exceptions](docs/quest_resume_exceptions.md)

The November 5 stage-start policy permits a reviewed adapter to begin an earned stage from its original start when the exact resume point is unavailable. Use each player's verified in-game prerequisites and ownership. Keep personal save paths, slots and hashes out of runtime admission. Restarting a stage may restart its own timer. Earlier outcomes, rewards and excluded prerequisites stay protected. [First application in Brendan's handoff](prealpha/quest_restoration_qr17/REPORT.md)

The [November 8 marker/encounter policy](docs/prepared_encounter_policy_20261108.md) admits source-qualified Boolean setup fields at zero or one for otherwise supported Inactive entries. Preserve accepted history, current progress, original ownership and native marker/encounter setup. Counters, fights, phone calls and later stages require verified handling of their state.

The [R6/R6.1 selection](docs/whitelist_final_r6.md) and [catalogue](docs/whitelist_final_r6_catalogue.md) record cast, exclusions and prerequisite policy. Excluded prerequisites require earned pre-Tower completion and the correct outcome. Titles and entry counts are not lifecycle proof. Optional routes, phone/message branches, shared leases, cleanup and reload matter.

The [9 November R6.3 decision](docs/whitelist_prophets_song_20261109.md) excludes The Prophet’s Song from new post-Tower admission in JB2.

Prefer private resources and native patterns. Necessary official-resource patches must be narrow, justified and independently diffed. Runtime scripts coordinate persistent behavior; native graphs retain authored progression and outcomes. Native actor/prefab support is separate from entry admission. A killed flag alone does not prove an original owner retired.

## Profiles and housing

The actual active restriction profile is selected by [profiles/active.json](profiles/active.json); [profiles/README.md](profiles/README.md) documents its implementation, catalogues and migrations. Proposed three-way profile selection remains a separate design issue. No policy text change authorizes runtime regeneration or a saved-profile migration.

Housing follows the recorded later policy: ordinary homes require reacquisition, H10 costs €$25,000 once, other homes retain normal prices, shared stash and geometry are preserved, and services follow current entitlement. Relationship homes are not generic real estate; Kerry's existing earned house access is the explicit retained-access exception. Details and provenance are in [invariants](docs/knowledge/invariants.md).

## Current delivery state

The local installation includes the four cyberware treatments, Health and Stamina recovery, and day-14 facial injury reset over the Manual Save 26 load repair. It contains 51 consolidated Core paths and 1,738 archive payloads. Deployment verified the installed hashes, save preservation, compile provenance and file rollback. In-game qualification for the recovery update is pending. [Current state](docs/knowledge/current-state.md)

The user confirmed KOLD MIRAGE's speech cuts. KM2 disables its residual Johnny actor and presentation and rewires Open → scan → Take → Nix for the selected pre-first-opening save. The user accepted KOLD MIRAGE editing as complete with no bugs reported on 8 November. SD1 removes Sweet Dreams' residual Johnny actor and presentation while preserving the quest sequence, authored timing, gear and outcomes. Its live test awaits an intact genuine post-Tower pre-braindance fixture, and the current completed quest is preserved. PE1's reviewed Boolean setup admission is retained. Wider marker-count investigation is deferred. Heavy Hearts animation and reload and QR20’s installed Bartmoss contact repair await in-game qualification.

JB1 introduced the approved removal of 89 Johnny/61 V speech events and presentation in five reviewed quests, with native skips and one parent cleanup wait. The user authorized the closed-game install; all 51 Core files, 26 dependencies, 313 saves and SD1 recovery verify. Five-quest gameplay tests remain pending. [Implementation](prealpha/johnny_batch2_jb1/REPORT.md) and [test card](prealpha/johnny_batch2_jb1/TEST_CARD.md).

The prepared four-folder beta is an older VD1 snapshot and remains separate from PH3. The public alpha link in README is the last recorded publication; this maintenance task did not check remote releases or publish anything. Exact identities and hashes are in [current-state](docs/knowledge/current-state.md).

No universal current all-lineage rebuild command is established. Preserve pinned candidates and use a reviewed fresh successor with exact input/proof manifests. File rollback is not save rollback.

## Boundaries

A complete new campaign, AI voice replacement, romance rewrite, wholesale 2079 city rebuild and restoration of incompatible Johnny-central/Relic/main-story content are outside the established target. Do not narrow compatible restoration to only the currently working samples, or expand it through unsafe resets.

This instruction-maintenance session ends after documentation verification. The [fresh-session handoff](docs/maintenance/instruction-system-20261029/HANDOFF.md) prepares a future comprehensive static vanilla-parity auditor; no quest audit is authorized to start within this maintenance session.
