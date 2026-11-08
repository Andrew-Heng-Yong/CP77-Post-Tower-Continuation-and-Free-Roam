# PTFR QR8 — Final Static Integration, Blocker Resolution and Test Readiness

Continue the 161-quest PTFR restoration project from QR7.

All 161 selected quests have undergone deep source investigation. Do not repeat the whitelist census or broad quest audits.

**Primary objective:** Establish whether the latest staged consolidated successor is technically ready for controlled in-game validation, while resolving remaining actionable static defects.

## 1. Resume the exact QR7 state

Read QR7 REPORT.md, HANDOFF.md, checkpoint.json, remaining_blockers.json, repair_queue.json, source_epoch_04.json, and the applicable developer knowledge.

Use the canonical QR7:04 candidate as the current source.

Preserve:
- All eight previously staged repairs.
- Nitro's corrected eligibility.
- CVI02's restored alternate Hands listener.
- Ronald's four-gig optional-news controller.

Installed PH3 remains untouched.

Verify all source, archive, ArchiveXL, and package hashes before making changes.

## 2. Use parallel agents

Run three concurrent workers with a continuously replenished task queue.

### Worker A — ArchiveXL and engine integration

Investigate the actual installed ArchiveXL DLL and the source used to justify QR7's new registrations.

Determine:
- Exact installed binary identity and version.
- Whether the relevant quest-phase registration, persistent receipt, and streaming methods match the analyzed source.
- Whether the newly appended phase and streaming block are correctly registered.
- Whether new generated IDs collide with existing resources.
- Whether private resources resolve under effective provider precedence.

Use disassembly or binary inspection where appropriate.

Do not assume upstream source behavior is identical to the installed DLL.

If exact compatibility cannot be proven statically, document the specific boundary and prepare a minimal diagnostic for later runtime verification.

### Worker B — Remaining communication and saved-state gaps

Investigate the remaining limitations of:

1. CVI02 alternate Hands calls.
2. Ronald optional-news subscriptions and historical timer state.

Prioritize:
- First-time Ronald subscription and contact creation.
- Previously entered quests.
- Old pending messages and native timers.
- Saved controller ownership.
- Duplicate listeners, notifications and cleanup.
- Cold-load and interruption implications.

Implement safe, source-confirmed extensions only when all ownership and history requirements can be established.

Do not fabricate enrollment facts, duplicate shared controllers, reset timers, or force quest progression.

### Worker C — Five remaining quest UNKNOWNs

Investigate:

- Career Opportunities: early notification ownership and persistent-state behavior.
- Cuckoo's Nest: original inventory predicate and null-edge semantics.
- Voodoo Treasure: exact door/controller ownership, container injection history and persistent identifiers.

Resolve each contract using actual source and provider evidence.

If the behavior depends on unobservable engine state, classify the limitation explicitly and stop repeating equivalent static searches.

Do not convert UNKNOWN to CONDITIONAL merely to change the counts.

## 3. Independent reviews and integration

Each worker must produce exact source/resource evidence and independently testable conclusions.

Cross-review findings between workers.

For an approved runtime repair:
1. Reproduce the defect before modification.
2. Establish the original vanilla behavior.
3. Implement the smallest compatible correction.
4. Run failing-before and passing-after regression tests.
5. Verify serialized CR2W resource readbacks.
6. Check identities, ownership, graph edges and dependencies.
7. Integrate through a coordinator-owned source epoch.
8. Independently validate the final packaged result.

Preserve every unchanged resource and prior correction.

## 4. Final integration gate

Verify the complete current staged build against the QR7 baseline.

Check:
- All packaged archive payloads.
- ArchiveXL phase and streaming registrations.
- Effective provider precedence and collisions.
- REDscript and dependency compatibility.
- Save-persistent identities and known migration boundaries.
- Cross-quest resource ownership.
- Existing historical regression controls.
- ZIP content, hashes, and installation layout.

Do not claim that static verification proves actual runtime execution.

## 5. Prepare controlled in-game acceptance tests

Create a minimal, prioritized test plan covering:

- Fresh post-Tower eligibility and quest activation.
- Mr. Hands alternate calls.
- Ronald optional news and initial subscription limitations.
- Nitro eligibility.
- Previously staged MQ007, MQ030 and MQ037 repairs.
- Scene/actor and world streaming.
- Quest completion and reward delivery.
- Save/reload and interrupted phone or quest states.

For each test, specify the required save baseline, actions, expected observations, relevant diagnostics and rollback precautions.

Prefer a small set of representative shared-system tests before full quest playthroughs.

Prepare the tests but do not launch the game or modify saves.

## 6. Final outputs

Produce:
- Confirmed remaining defects and repaired implementations.
- Original and final contract-disposition comparison.
- Exact unresolved static and engine-dependent limitations.
- ArchiveXL compatibility assessment against the installed DLL.
- Independently verified final package and source manifest.
- Targeted in-game acceptance checklist.
- Release-readiness assessment identifying blockers and acceptable documented limitations.
- Fresh QR9 handoff, if further work is necessary.

Do not generate a new ZIP unless runtime resources or packaging actually change.

## 7. Restrictions

No game launch, installation, save/fact modification, published-release change, whitelist expansion or Git push.

Do not perform another broad 161-quest source audit.

**Success means closing actionable static risks and preparing a reproducible, safely testable build—not artificially reaching zero CONDITIONAL or OPAQUE contracts.**