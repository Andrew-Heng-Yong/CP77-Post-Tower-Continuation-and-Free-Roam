# PTFR QR3 — Parallel Multi-Agent Quest Verification and Repair

Continue the comprehensive 161-quest restoration task from QR2.

**Use Codex's multi-agent capability to investigate multiple quests simultaneously. Do not process quests sequentially unless a shared dependency requires serialization.**

Read:
- `prealpha/quest_restoration_qr2/HANDOFF.md`
- `prealpha/quest_restoration_qr2/REPORT.md`
- `prealpha/quest_restoration_qr2/checkpoint.json`
- `prealpha/quest_restoration_qr2/queue.json`
- Applicable AGENTS.md files and developer knowledge.

## 1. Objective

Complete deep static verification of **all 13 remaining Q01 quests** in this session using up to six concurrent investigation agents.

The previous three quests (Paid in Full, Big in Japan, Send in the Clowns) are already investigated. Do not repeat them unless a newly discovered shared-system defect directly affects them.

The overall 161-quest task remains active.

## 2. Parallel agent assignments

Spawn six independent investigation agents concurrently, subject to the available concurrency limit.

**Agent A — Racing**
- `07_nc_underground` — The Beast in Me

**Agent B — Vehicle and world activities**
- `mq046_cave_vehicle` — Murk Man Returns Again Once More Forever
- `mq047_ad_vehicle` — Dressed to Kill

**Agent C — Brendan quest family**
- `mq037_brendan` — Coin Operated Boy
- `mq037_brendan_hooligan001` — Spray Paint

These share native resources and must be investigated together to avoid duplicate or conflicting conclusions.

**Agent D — Communication-heavy quests**
- `mq041_corpo` — War Pigs
- `mq044_jakes_vehicle` — Sex on Wheels
- `mq049_edgerunners` — Over the Edge

Prioritize phone calls, SMS, original prerequisite gates, acknowledgement and cleanup.

**Agent E — Side-job progression**
- `mq030_melisa` — Bullets
- `mq032_sacrum` — Sacrum Profanum / Losing My Religion
- `mq026_conspiracy` — The Prophet's Song

**Agent F — Boxing quest family**
- `mq025_06_pacifica` — Beat on the Brat: Pacifica
- `mq025_psycho_brawl` — Beat on the Brat

Verify shared ownership, progression, fight controllers, reward and completion handling.

If fewer than six agents can run concurrently, schedule assignments in waves. Do not silently omit an assignment.

## 3. Agent responsibilities

Each agent must independently inspect original vanilla files and effective PH3 resources.

Verify all ten contracts per assigned quest:

1. Entry handlers and initiation.
2. Eligibility, fact/journal conditions and prerequisites.
3. Phone calls, SMS, request/acknowledgement and cleanup.
4. Native owner lifecycle and duplicate prevention.
5. Quest progression, branches and scene execution paths.
6. Actors, prefabs, variants, workspots and resource dependencies.
7. Journal objectives, states and markers.
8. Completion, rewards and cleanup.
9. Persistent identities, saved progress and reload implications.
10. Shared controllers and cross-quest dependencies.

Use exact graph/node/socket identifiers, resource hashes and native predicates.

Trace complete relevant paths, not just the existence of handlers.

Compare against vanilla and the registered intentional Tower adaptations.

Use existing QR1/QR2 audit utilities, identity evidence and shared verification results where applicable.

Do not invent repairs for UNKNOWN, CONDITIONAL or OPAQUE findings.

### Required output per agent

Write independent evidence to:

`prealpha/quest_restoration_qr3/agents/<agent_id>/`

Include:
- Per-quest ten-contract results.
- Exact vanilla versus restored evidence.
- Verified intentional differences.
- Confirmed defects with reproducible failing cases.
- Proposed minimal patches, if justified.
- Focused regression/mutation tests.
- Explicit static unknowns and live-only limitations.

Agents must not modify the common queue, shared baseline, installed files or each other's outputs.

## 4. Parallel safety and shared dependencies

All investigation agents should perform read-only analysis of shared inputs.

Do not allow concurrent edits to the same runtime resource, shared REDscript file, build manifest or package.

If different agents discover problems in a shared controller, escalate the dependency to the coordinating agent.

The coordinating agent must reconcile conflicting conclusions against the actual native and current resources before accepting any proposed repair.

Agents may write disposable tests, analysis scripts and proposed patch artifacts in their isolated output directories.

## 5. Coordinating agent — integration and implementation

The main agent acts as coordinator and integrator.

While investigations run, it may prepare the shared evidence index, review earlier verified inputs and establish output validation.

After receiving completed agent findings:

1. Check every assigned quest has ten explicit contract dispositions.
2. Reconcile shared dependencies and overlapping resources.
3. Reject findings unsupported by exact original/current evidence.
4. Assign independent cross-review: another agent must review each proposed gameplay fix.
5. Implement justified repairs in a single controlled QR3 successor, respecting shared resource ownership.
6. Add failing-before/passing-after regression checks for actual defects.
7. Run affected compilation, graph verification, archive serialization/readback and regression checks.
8. Preserve persistent identities, native ownership, reward history, PH3 fixes and intentional Tower consequences.

Use a fresh successor and explicit changed-resource allowlist. Do not rebuild or repackage an unchanged baseline.

## 6. Independent adversarial verification

After initial investigations, use available agents to cross-review findings from other assignments.

Reviewers must inspect raw source/graph evidence independently rather than simply reading the first agent's conclusions.

Prioritize:
- Confirmed defects and proposed repairs.
- Shared controller and phone lifecycle claims.
- Quest-entry conditions that might admit duplicate owners.
- Claims that a quest has no static defects.
- Any approved deviation that changes vanilla behavior.

Correct mistakes and record review resolutions.

No contract may be promoted to PASS merely because two agents agree without supporting evidence.

## 7. Reuse existing verified work

Do not repeat unchanged QR1/QR2 baseline compilation, identity reconciliation, archive reproduction or general provider inventory.

Reuse pinned evidence and hashes.

Run fresh verification only for changed inputs, newly investigated paths or newly identified gaps.

Preserve the already rejected Delamain patch and Sandra/Delamain synthetic-reset prohibition.

Do not spend the session exclusively developing new audit infrastructure.

## 8. Completion and reporting

Update the successor 161-quest queue and ten-contract matrix centrally after integrating the agent outputs.

Target for this session:
- All 13 remaining Q01 quests receive detailed investigations.
- Q01 reaches 16 of 16 deep-reviewed quests, including QR2's three.
- Every Q01 quest has ten evidence-backed contract dispositions.
- Every source-confirmed defect found is repaired or recorded with a precise implementation blocker.
- Every actual repair has independent review and regression tests.
- Remaining static uncertainty and live-only behavior remain explicitly classified.

Report:
- Newly deep-reviewed quests.
- Contracts passed, approved, conditional, opaque, unknown and live-only.
- Confirmed defects versus repairs implemented.
- Shared-system findings affecting other quests.
- Verification failures and remaining blockers.
- Updated persistent queue and exact next-batch handoff.

Do not claim gameplay verification from static results.

If execution limits prevent completion of all 13, preserve valid completed work and accurately identify the unprocessed assignments. Do not claim full Q01 completion.

## 9. Restrictions

Authorized: isolated investigation, source-confirmed repairs, relevant test improvements, static verification, staged successor builds.

Not authorized: game launch, deployment, installed game changes, save/fact modifications, published release changes or Git pushes.

Do not change whitelist eligibility or restore excluded/held quests.

**Start all available independent investigation agents promptly. Do not wait for Agent A to finish before assigning B–F.**

The objective is high-throughput, evidence-backed quest restoration—not another preparation-only audit or speculative mass repair.