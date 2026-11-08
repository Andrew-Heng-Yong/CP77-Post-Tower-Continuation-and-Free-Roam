# PTFR — Comprehensive Whitelisted Quest Restoration and Repair

Your task is to systematically verify, repair, and complete the restoration of **every quest in the current effective PTFR whitelist**, using the completed PH3 static vanilla-parity audit as the starting point.

**This is an implementation task, not another audit-only task.** You are authorized to modify mod source files, repair quest resources, improve the build pipeline where necessary, compile, run static tests, and prepare a complete consolidated successor package.

Do not modify the installed game, saved games, runtime facts, or published releases without explicit authorization.

## 1. Establish the current baseline

Read the applicable AGENTS.md files, developer knowledge base, and PH3 audit results.

Use the current effective PH3 candidate, not historical prototypes.

Current catalogue:
- INCLUDE: 161 quests
- EXCLUDE: 51
- SEPARATE_SCOPE: 15
- Held: `mq057_motorbreath`

Respect all existing exclusions, story consequences, eligibility policies, and save-compatibility requirements.

Use the actual current catalogue pointer and installed source/provider manifests. Historical counts must not override the effective selection.

Preserve existing successfully restored functionality.

## 2. Objective

For every included quest, establish whether the following are restored correctly relative to vanilla:

1. Quest entry and initiation.
2. Entry prerequisites and eligibility.
3. Phone calls, SMS and other communications.
4. Native quest ownership and lifecycle.
5. Quest progression and conditional branches.
6. Dialogue, scenes, actors and required resources.
7. Objectives, markers and journal transitions.
8. Quest completion, rewards and cleanup.
9. Save/reload persistence and prevention of duplicate owners.
10. Interactions with shared controllers, other quests and world services.

**Preserve vanilla behavior wherever possible.** Only introduce the minimum necessary modifications to make the quest work after The Tower ending while preserving that ending's intended consequences.

Do not rewrite complete vanilla quest logic where reusing the native logic is possible.

Do not assume that a quest is broken merely because the previous auditor classified it UNKNOWN or OPAQUE.

## 3. Resolve existing audit gaps

Use the existing auditor rather than starting from scratch.

Prioritize:

- 32 selected quest IDs without exact resolved identity mappings.
- 5 generic bindings without catalogue matches.
- 8 unresolved phone cleanup/counter associations.
- 15 structural dangling-edge findings.
- 6 embedded-resource lifetime uncertainties.
- 23 missing external graph inputs.
- Unresolved provider precedence affecting effective resources.
- Unsupported registration formats and asset dependency classifications.
- Incomplete intentional-deviation and lifecycle coverage.

For each discrepancy:

1. Inspect the exact original vanilla resources.
2. Inspect the effective current PTFR resources.
3. Trace the relevant native and restored control flow.
4. Determine whether the discrepancy is a real defect, an authorized difference, a baseline limitation, or still unresolved.
5. Implement a repair only when the available evidence supports it.
6. Add a regression test for each confirmed defect.

Do not manufacture placeholder assets, dummy listeners, artificial quest facts, or arbitrary ownership resets to eliminate warnings.

## 4. Implement repairs

Repair all source-confirmed defects discovered across the 161 selected quests.

Pay particular attention to phone controllers, entry handlers, nested quest graphs, cleanup, and resource ownership.

For each repair:

- Preserve original conditions and branches unless an explicit Tower-specific adaptation is required.
- Preserve exact native quest, scene and resource references where appropriate.
- Preserve persistent owner identities, saved progress, completed quests, failed quests, choices and rewards.
- Do not restart or duplicate an already-running native quest owner.
- Do not duplicate phone listeners, shared controllers or cleanup services.
- Do not allow a repair to change pre-Tower vanilla gameplay unintentionally.
- Verify all modified resources against pinned vanilla references and explicitly approved differences.

If a repair cannot be justified without runtime evidence, leave it unresolved and document the precise missing evidence. Do not introduce speculative fixes.

## 5. Work systematically across the complete whitelist

Do not randomly select quests or focus exclusively on previously reported bugs.

Create a persistent machine-readable work queue covering every included quest.

Process quests in bounded batches, grouping shared dependencies and controller families where useful.

For every quest, record:

- Vanilla entry and handler identities.
- Restored handler and effective resource identities.
- Relevant graph and phone dependencies.
- Differences from vanilla.
- Confirmed defects and implemented repairs.
- Automated tests and their results.
- Remaining static or runtime limitations.
- Final verification status.

A quest may be marked STATIC_VERIFIED only when all required static contracts have been checked or explicitly approved as intentional deviations.

Do not mark a quest complete because its entry exists, its graph parses, or its resources are present.

Maintain persistent checkpoints so another fresh Codex session can continue without repeating completed work.

## 6. Consolidation and regression protection

Preserve the current consolidated packaging architecture.

Known regression classes that must remain protected:

- CR1: older donors replacing corrected resources.
- PH1: missing phone listeners, cleanup and studio dependencies.
- PH2: generated-ID collisions.
- PH3: shared phone studio and prefab ownership.

Use exact effective-resource provenance and provider precedence.

Do not create an additional overlay stack when an existing consolidated successor can be updated.

If the existing rebuild pipeline cannot produce a verified successor, repair the minimum necessary tooling and validate it. Do not blindly invoke obsolete historical builders.

Every repair must pass:
- Relevant vanilla graph parity checks.
- Phone and lifecycle contract checks where applicable.
- Full REDscript compilation.
- Archive serialization and readback verification.
- Dependency and resource resolution checks.
- Generated-ID and provider-collision checks.
- Existing regression and mutation suites.
- Save-persistent identity compatibility checks where static evidence permits.

Report any checks that cannot be executed. Never substitute a source-level check for a packaged-build check.

## 7. Independent verification

After completing a repair batch, perform a separate adversarial review.

The reviewer should examine the original vanilla graph, the actual changed implementation, the effective packaged payload, and the tests.

Review for omitted branches, incorrect prerequisites, duplicate owners, incomplete cleanup, and unintended effects on existing functionality.

Do not simply repeat or endorse the implementation agent's conclusions.

Re-run relevant regression tests after each batch and the complete available static suite before finalizing the consolidated successor.

## 8. Deliverables

Produce:

1. A corrected source implementation covering all statically identifiable defects in the whitelist.
2. A verified, staged consolidated successor package, if the current build pipeline supports producing one safely.
3. Updated reproducible verification tests.
4. A complete 161-quest status matrix.
5. A list of each actual defect found and the specific repair made.
6. Remaining unresolved static and live-only requirements.
7. A separate minimal in-game acceptance checklist for behaviors impossible to verify statically.
8. A concise handoff for continuing the repair process in a fresh session.

Do not claim that all quests work in-game based solely on static checks.

## 9. Execution requirements

**Do not stop after writing another audit report or implementation plan. Begin actual repair work.**

Use the completed audit to guide implementation. Resolve evidence gaps when needed, but avoid repeatedly performing broad audits without making progress.

Prioritize high-impact shared infrastructure defects before individual quest-specific defects.

Continue systematically through the whitelist, with reproducible checkpoints and verified changes.

If the current session cannot finish all 161 quests, complete and validate as many justified repairs as possible, preserve the exact remaining work queue, and provide a continuation handoff.

Do not sacrifice correctness to reduce UNKNOWN counts.

**Final objective: every selected quest has a traceable restoration implementation, all identifiable static defects are repaired, all available static verification requirements pass, and remaining gameplay-dependent uncertainties are explicitly documented.**