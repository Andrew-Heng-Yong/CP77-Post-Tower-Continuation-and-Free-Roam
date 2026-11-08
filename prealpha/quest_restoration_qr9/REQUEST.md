# PTFR QR9 — Human-Driven Runtime Validation

Continue from the canonical QR8:02 candidate and QR8 handoff.

**Important workflow change: Do not use Computer Use Automation (CUA), GUI automation, remote desktop, simulated mouse/keyboard interaction, or automated gameplay.**

The user will personally launch Cyberpunk 2077, operate CET, and perform all in-game tests.

Codex is responsible for preparation, diagnostics, log analysis, and source-confirmed repairs.

## 1. Division of responsibilities

**Codex:**
- Prepare and verify safe installation/rollback scripts.
- Compile and package when necessary.
- Create read-only runtime diagnostics.
- Generate concise manual test instructions.
- Analyze resulting logs and observations.
- Investigate failures and implement justified repairs.

**User:**
- Run the provided installer after reviewing its preflight.
- Launch the game.
- Load the specified disposable save.
- Perform the requested gameplay actions.
- Report visible behavior and provide logs/screenshots when required.

Never attempt to control the game through CUA.

## 2. Parallel offline preparation

Use up to three workers for independent tasks:

**Worker A — Deployment preparation**

Prepare and fixture-test an installer for QR8:02.

The installer must:
- Verify exact package and installed baseline hashes.
- Back up the two changing managed paths.
- Preserve existing saves and external dependencies.
- Support preflight, installation verification and rollback.
- Refuse unexpected state changes.

Do not run the installer against the real game without explicit authorization.

**Worker B — Automated diagnostics**

Prepare a lightweight, read-only CET/REDscript diagnostic system that records relevant:

- Quest entry and actual graph activation.
- Phone request, listener, acknowledgement and cleanup.
- Journal and selected fact transitions.
- Native and restored owner lifecycle.
- ArchiveXL registration receipts versus actual activation.
- Save/reload observations where possible.
- Relevant errors and missing dependencies.

Avoid excessive per-frame polling, huge logs, or diagnostics that interfere with gameplay.

Prefer event-based capture and bounded sampling.

Do not set quest facts, issue quest starts, manufacture state or modify saves.

Provide simple CET commands to start/stop capture, with clear log locations and automatic session metadata.

**Worker C — Manual acceptance tests**

Prepare a short, prioritized test guide based on QR8's existing nine-case checklist.

For each test specify:
1. Required save and prerequisites.
2. Exact player actions.
3. Expected visible behavior.
4. Expected diagnostic evidence.
5. How to stop capture.
6. What the user should send back.

Prioritize:
- ArchiveXL quest registration.
- Alternate Mr. Hands calls.
- Ronald prospective news.
- Nitro eligibility.
- Previously repaired MQ007, MQ030 and MQ037 behavior.
- Save/reload and interrupted-controller behavior.

Group tests that can safely share the same save and session. Do not combine tests if their persistent quest states would invalidate each other.

Do not require the user to manually inspect hundreds of facts or graph nodes.

## 3. Minimize interaction and token usage

- No CUA or graphical automation.
- Reuse existing QR1–QR8 verified evidence.
- Do not repeat broad static audits.
- Do not rebuild unchanged resources.
- Avoid unnecessary subagents for trivial tasks.
- Use machine-readable diagnostic logs rather than screenshots where possible.
- Require screenshots only when visual evidence is necessary.
- Provide one concise manual test card per scenario.
- Keep detailed diagnostic evidence in files, not in long chat responses.

The user should spend most of their time actually playing, not entering commands or collecting technical information.

## 4. Runtime test workflow

First complete offline preparation and fixture validation.

Then provide:
- Exact installer command and preflight result.
- Exact rollback command.
- Diagnostic start/stop commands.
- First recommended manual test.
- Expected results and log location.

Stop before real installation or game launch. Wait for the user's explicit authorization for deployment.

After the user completes testing, analyze the observations and logs.

Classify each result:
- PASS — observed correct behavior.
- FAIL — observed incorrect behavior.
- NOT_TESTED.
- NOT_TESTABLE — required genuine save/conditions unavailable.
- INCONCLUSIVE — insufficient evidence.

Do not treat missing notifications as confirmed defects without examining prerequisites, phone settings, callbacks and owner states.

## 5. Repair workflow

For a reproducible runtime defect:

1. Identify the first incorrect state or execution path.
2. Compare it with the exact vanilla and effective PTFR resources.
3. Implement the smallest compatible fix.
4. Add failing-before/passing-after regression tests.
5. Independently review the repair.
6. Verify affected serialized and packaged resources.
7. Prepare a new guarded successor only if the runtime resource actually changed.

Preserve completed quests, existing saves, Tower consequences, all prior repairs and native ownership.

## 6. Deliverables

Prepare:
- Safe QR9 installer and rollback procedure.
- Lightweight diagnostic collector.
- Concise manual acceptance checklist.
- Structured log and test-result format.
- Initial deployment-readiness report.
- Exact first test instructions.

**Do not launch the game, use CUA, deploy, alter saves, or perform gameplay on the user's behalf.**

The goal is to make human testing fast and technically informative, while using Codex for tasks where automation provides real value.