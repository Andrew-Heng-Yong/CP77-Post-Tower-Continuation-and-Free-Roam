# PTFR QR5 — High-Throughput Multi-Agent Quest Verification and Repair

Continue the same 161-quest PTFR restoration project from QR4.

**Primary target: complete deep verification of Q05, Q06 and Q07 (48 additional quests). Stretch target: Q08 (16 additional quests), for 64 new investigations.**

Use continuous multi-agent scheduling, parallel investigations, independent reviews and centralized repair integration.

This is an implementation-and-verification task, not another general audit or preparation session.

## 1. Restore the authoritative checkpoint

Read:
- `prealpha/quest_restoration_qr4/HANDOFF.md`
- `prealpha/quest_restoration_qr4/REPORT.md`
- `prealpha/quest_restoration_qr4/checkpoint.json`
- `prealpha/quest_restoration_qr4/queue.json`
- `prealpha/quest_restoration_qr4/source_epoch_03.json`
- Applicable AGENTS.md and developer knowledge.

Initial state:
- 161 selected quests.
- 64 deeply reviewed.
- 97 remaining.
- Three cumulative unique staged repairs.
- Installed baseline: PH3.
- Current staged source successor: QR4 candidate_01.

Verify the handoff sentinel, resource hashes and canonical source epoch before proceeding.

**Preserve all QR3 and QR4 repairs:**
- MQ037 Brendan excluded-fresh admission containment.
- MQ030 Bullets helper retirement and vendor lease ordering.
- MQ007 Machine Gun future-entry native post-return continuation.

Never silently revert these corrections.

## 2. Parallel scheduling

Use the maximum available worker concurrency, with the QR4 three-worker configuration as the expected starting point.

The coordinator must create a dynamic work queue covering Q05–Q07 and optionally Q08, using the exact identities from the current QR4 queue.

Group quests into investigation tasks of approximately 3–5 related quests, considering native parents, shared phone controllers, quest families, world owners and rewards.

**Launch independent workers immediately.**

When any worker completes a task, assign the next unclaimed task immediately. Do not wait for the entire current batch or all other agents to finish.

Use worker rotation for independent cross-review.

If fewer workers are available, continue in waves without reducing evidence requirements.

Do not create one worker thread per quest. Reuse available workers and avoid repeated loading of identical source material.

The coordinator alone owns the central queue, source epoch, integration state and final packaging.

## 3. Per-quest investigation

Every selected quest requires ten evidence-backed contract dispositions:

1. Entry and initiation.
2. Native prerequisites and eligibility.
3. Phone/SMS producers, listeners, acknowledgements and cleanup.
4. Quest ownership, original-owner lifecycle and duplicate prevention.
5. Progression, branches and scene paths.
6. Actors, scenes, prefabs, cameras, workspots and resource bindings.
7. Journal states, objectives and mappins.
8. Completion, rewards and cleanup.
9. Persistence, history and saved-owner compatibility.
10. Shared dependencies and controller interactions.

Compare exact vanilla and effective PTFR resources, not just historical descriptions.

Trace graph nodes, socket connections, predicate conditions, writers, parent ownership, native callbacks and outcome branches.

A quest must not be marked deeply reviewed simply because its resources are present, because a generic checker passed, or because the agent produced ten status labels.

Each conclusion must include source-specific evidence and explicit verification limits.

Where a mechanism genuinely does not apply to a quest, establish non-applicability using native evidence rather than assigning a generic UNKNOWN.

## 4. Shared evidence resolution

QR4 accumulated recurring CONDITIONAL and OPAQUE findings involving:

- TweakDB reward, economic, vehicle and item definitions.
- Streamed prefab, actor, NodeRef and workspot semantics.
- Shared phone-controller admission and cleanup.
- World ownership, journal/mappin writers and lifecycle.
- Persistent quest-owner transitions.
- Localization and presentation dependencies.

Avoid rediscovering the same evidence independently for every quest.

Maintain a source-pinned shared evidence registry.

When one worker establishes a reusable contract, propagate its exact evidence to affected quests, subject to independent applicability checks.

Distinguish:
- Static evidence successfully established.
- A confirmed restoration defect.
- An approved intentional deviation.
- A static dependency that remains unresolved.
- Opaque engine/resource semantics.
- Runtime-only behavior.

Do not repeatedly investigate intrinsically runtime-only properties with static tools merely to increase PASS counts.

Shared evidence improvements must not displace the primary quest investigation workload.

## 5. Repair confirmed defects

When a worker identifies a potential defect:

1. Reproduce the actual faulty path against the effective staged source.
2. Establish the original vanilla behavior and required Tower adaptation.
3. Exclude legitimate intentional differences.
4. Implement a failing-before regression test.
5. Propose the smallest compatible repair.
6. Obtain independent cross-agent review.
7. Integrate only after the coordinator accepts the evidence.
8. Verify the repaired serialized resource and affected package dependencies.

Investigation workers may generate isolated proposed patches, but only the coordinator may modify shared candidate resources.

Never implement speculative fixes to clear CONDITIONAL or OPAQUE findings.

Preserve saved identities, native ownership, history, consequences, rewards, existing choices and all prior confirmed repairs.

## 6. Maintain source-epoch consistency

Investigations must use pinned source versions.

If the coordinator integrates a repair while other investigations are running:

- Record a new canonical source epoch.
- Preserve the previous source and evidence.
- Identify which quest investigations depend on changed resources.
- Revalidate only affected results against the new epoch.
- Never silently combine findings from incompatible candidate versions.

All proposed resource changes must appear in an explicit reviewed allowlist.

## 7. Independent review and regression tests

Every investigation group requires independent cross-review.

A reviewer must examine actual raw native and effective resources, rather than merely endorsing the initial agent's report.

Every gameplay repair requires a separately implemented verification path where feasible.

Use actual serialized resources for fault-detection tests whenever possible; tests against only an abstract graph model are insufficient to establish packaged correctness.

Run affected graph, socket, condition, generated-ID, dependency, ownership and serialization checks.

Reuse QR1–QR4 compilation and regression evidence where all exact inputs remain unchanged.

Recompile when relevant source or dependency inputs change.

After integration, independently compare the final staged candidate against QR4. Verify all intended changes and all preserved resources.

## 8. Existing unresolved policies

Carry forward, without speculative changes:

- MQ007 progressed and previously returned saved-owner states.
- Brendan earned-history sequel admission.
- Delamain parent token/mail prerequisite uncertainty.
- Life's Work and Sex on Wheels timer/context differences.
- Gig journal, mappin and entry-guard uncertainties.
- Runtime-only interruption, reward, phone and streaming behavior.

Investigate these when new evidence or a relevant shared dependency makes them actionable.

Do not repeatedly reopen resolved investigations without a concrete new reason.

Do not restore excluded or held content.

## 9. Required progress and outputs

Create `prealpha/quest_restoration_qr5/` with:

- Coordinator-owned persistent work queue.
- Per-quest ten-contract results.
- Source-pinned evidence and verifier results.
- Shared evidence registry.
- Independent agent review records.
- Confirmed defect and repair registry.
- Versioned source epochs and changed-resource allowlist.
- Updated 161-quest and 1,610-contract matrices.
- Final independent integration and preservation checks.
- Staged consolidated successor package only if runtime resources changed.
- Concise QR6 continuation handoff.

Record both the number of unique defects and the number of affected quests.

Do not confuse source correctness, static reachability or test counts with proven gameplay execution.

## 10. Completion targets

Primary:
- Q05, Q06 and Q07 fully investigated: 48 new quests.
- Total deep-reviewed: 112/161.

Stretch:
- Q08 fully investigated: 64 new quests.
- Total deep-reviewed: 128/161.

Prioritize finishing the primary scope with real evidence before expanding to Q08.

All confirmed, justified repairs discovered within the completed scope must be integrated and verified or explicitly blocked with a precise reason.

If context, execution limits or worker capacity prevent full completion, preserve validated work and the exact unprocessed queue.

Do not inflate coverage by lowering review requirements.

## 11. Restrictions

Do not launch the game, install the staged mod, edit saves/facts, change published releases, push to Git or alter the whitelist.

Do not rebuild unchanged baselines or generate redundant ZIPs.

**Begin concurrent investigations immediately. Keep workers continuously occupied, integrate evidence as it arrives, and proceed through Q05–Q07 without waiting for a new user prompt between batches.**

Success means reproducible progress toward correct restoration of all 161 selected quests, not merely fewer UNKNOWN classifications.