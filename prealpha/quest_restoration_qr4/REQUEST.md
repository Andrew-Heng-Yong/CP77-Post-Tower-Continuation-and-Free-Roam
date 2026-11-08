# PTFR QR4 — High-Throughput Multi-Agent Quest Verification and Repair

Continue the comprehensive 161-quest restoration project from QR3.

**Target: deeply investigate at least 32 additional quests (Q02 + Q03), with Q04 as a stretch goal for up to 48 quests.**

Use multi-agent parallel execution with a continuously replenished task queue. Do not restrict this session to three quests or a single 16-quest batch.

## 1. Read the current checkpoint

Read:
- `prealpha/quest_restoration_qr3/HANDOFF.md`
- `prealpha/quest_restoration_qr3/REPORT.md`
- `prealpha/quest_restoration_qr3/checkpoint.json`
- `prealpha/quest_restoration_qr3/queue.json`
- Applicable AGENTS.md and developer knowledge files.

The current state is:
- 161 whitelisted quests.
- 16 quests deeply investigated.
- 145 quests awaiting deep investigation.
- Two confirmed QR3 repairs staged: MQ037 Brendan admission containment and MQ030 Bullets helper retirement.
- No quest fully STATIC_VERIFIED.
- Installed baseline remains PH3.

**Use the staged QR3 candidate as the source successor. Preserve both repairs. Do not restart from the installed PH3 archive and discard those changes.**

## 2. Dynamic parallel worker scheduling

Use the maximum available concurrent investigation workers, up to six.

QR3 encountered a three-worker concurrency limit. Detect the actual available capacity and saturate it.

Create a shared coordinator-owned task queue covering all 16 Q02 quests and all 16 Q03 quests from the current successor queue.

Do not hardcode Q03 identities from historical documents. Resolve them from the effective queue.

Group quests by shared native owners, phone systems, graph parents, prefabs, rewards and other dependencies.

Assign approximately 3–5 related quests per worker task, adjusting for complexity.

**As soon as a worker finishes, immediately assign the next unclaimed group while other workers continue investigating.**

Do not wait for an entire batch to finish before starting the next one.

Use independent, isolated investigation outputs. Workers must not concurrently modify shared sources, manifests or the central queue.

If capacity remains after Q02 and Q03, continue into Q04 without requiring another prompt, subject to available execution limits.

## 3. Deep investigation requirements

Each selected quest requires ten evidence-backed contracts:

1. Entry and initiation.
2. Eligibility and native prerequisites.
3. Phone calls, SMS and communication lifecycle.
4. Native ownership and duplicate prevention.
5. Progression, branches and scenes.
6. Actor, prefab, workspot, camera and asset semantics.
7. Journal, objectives and markers.
8. Completion, rewards and cleanup.
9. Persistence and saved-owner compatibility.
10. Shared controller and cross-quest dependencies.

Compare exact native and effective PTFR resources, including nodes, sockets, guards, writers, references, lifecycle transitions and approved intentional differences.

Reuse validated shared evidence instead of repeating identical controller investigations for every quest.

A contract must not receive PASS merely because its resource exists, its graph parses, or it has a prior audit entry.

Record exact unresolved evidence for CONDITIONAL and OPAQUE cases.

## 4. Repair implementation

This task includes implementation, not just auditing.

When a worker identifies a potential defect:

- Reproduce it against the effective source.
- Establish the expected vanilla behavior.
- Exclude legitimate Tower adaptations.
- Demonstrate a failing pre-repair test.
- Propose the smallest compatible correction.
- Obtain independent review.

The coordinating agent owns all changes to common runtime resources and the final build.

Independent workers may create isolated proposed patches and tests, but must not directly modify shared production resources.

Implement confirmed repairs promptly, without waiting for every investigation to finish.

Preserve all QR3 repairs, saved identities, native ownership, existing choices, outcomes, rewards, history and exclusions.

Never introduce speculative state resets or duplicate listeners to eliminate uncertainty.

## 5. Continuous integration and verification

The coordinator must process completed worker results continuously.

For each completed group:

- Verify all ten contract dispositions per quest.
- Check the evidence against current source hashes.
- Reject unsupported conclusions.
- Resolve shared-controller conflicts.
- Cross-review confirmed defects and proposed repairs.
- Add and execute applicable regression tests.
- Update a coordinator-owned progress ledger.

Investigations should use pinned baseline evidence; staged repairs must be tracked with versioned source hashes so concurrent investigators do not unknowingly compare different candidate versions.

Do not repeatedly recompile or rebuild an unchanged baseline.

After integrating actual repairs, perform affected graph checks, serialization/readback, package verification and current-input compilation when required.

Before finalizing, perform an independent package diff against QR3.

All unchanged resources must remain identical unless an explicitly reviewed difference is recorded.

## 6. Avoid redundant work

Do not repeat QR1 identity mapping, QR2 investigations, QR3 investigations, or unchanged full-package reproduction.

Do not regenerate large inventories unless a newly discovered defect makes it necessary.

Reuse existing test utilities, source pins, previous mutation controls and shared evidence.

Do not spend the entire session designing another verification framework.

The priority is **completing real quest investigations and implementing evidence-backed repairs**.

## 7. Independent adversarial review

Assign cross-reviews to workers that did not investigate the corresponding quests.

Prioritize every proposed gameplay change and all shared-system findings.

Review source-level and serialized output evidence independently.

If a review finds an incorrect assumption, preserve the original finding and record its correction.

A review must not convert unresolved engine behavior into a static PASS.

## 8. Required outputs

Create a fresh QR4 workspace and maintain:

- A central progress/checkpoint file.
- A complete persistent 161-quest queue.
- A ten-contract status matrix.
- Per-quest evidence and test results.
- A confirmed-defect and repair registry.
- Independent review records.
- A versioned changed-resource allowlist.
- A staged consolidated successor package if gameplay resources changed.
- A concise continuation handoff.

Report both unique defects and affected quest counts; do not confuse them.

Separate static findings from actual gameplay verification.

## 9. Success criteria

Primary target: all 32 Q02/Q03 quests receive deep investigations, giving 48 total deeply reviewed quests.

Stretch target: include Q04, reaching 64 total deeply reviewed quests.

Each investigation must have actual source-specific findings rather than generic inherited UNKNOWN statuses.

Complete and validate all justified repairs discovered within the processed scope.

If execution limits prevent completion, preserve fully validated results, identify unfinished contracts and queue them for the next session. Do not fabricate completion.

Maintain a clear distinction among:
- Verified static behavior.
- Approved intentional differences.
- Unresolved static questions.
- Opaque engine/resource behavior.
- Runtime-only validation.

## 10. Restrictions

Do not launch the game, deploy to the installed directory, edit saves/facts, publish releases or push to Git.

Do not change the whitelist or restore excluded/held content.

Do not sacrifice verification depth simply to increase the number of reviewed quests.

**Start the parallel worker pool immediately. Keep workers occupied as assignments finish. Begin Q03 as capacity opens rather than waiting for all Q02 workers.**

The goal is maximum evidence-backed throughput, with independent validation and controlled integration—not maximum token consumption or superficial coverage.