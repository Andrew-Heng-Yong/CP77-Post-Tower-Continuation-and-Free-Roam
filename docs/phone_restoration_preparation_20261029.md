# Phone-dependent progression: audit and later restoration plan

29 October 2026. The user requested investigation of bugs similar to the Organitopia entrance blockage and preparation for restoration later. This pass changed only workspace evidence and documentation. No implementation, installation, game launch, save editing, quest-fact editing or release was performed.

## Findings

Six missing contacts remain in the current restoration. These reconfirm earlier source findings against the current LR2 installation; they are not six newly reproduced failures.

| Priority | Route | Confirmed omission and potential effect |
|---|---|---|
| First | **Spy in the Jungle — Mark Bana** | The restored quest requests his audio controller and waits for start/end acknowledgements. The handler and matching cleanup are absent from restored support. The introductory scene's completion leads to the two native entrance-door commands. The user's blocked-door report and recorded request without acknowledgement make this a likely cause; exact live scene/door state is unproven. |
| First | **Spy in the Jungle — Janet** | A later scene branch requests Janet's holocall and waits for start/end acknowledgements. The handler and cleanup are also absent. Repair with Mark so a later branch does not encounter the same dependency gap. No live Janet failure was observed. |
| Second | **Nasty Hangover — Karl Ginsky** | The open-world phase and dialogue scene request an outgoing audio call; the phase waits for the start acknowledgement and the scene also waits for the end acknowledgement. Both handler and cleanup are missing. Actual blockage is untested. |
| Second | **Desperate Measures — Pedro Aimar** | The combat phase and car scene request his incoming audio call and wait for acknowledgements. Both handler and cleanup are missing. Actual blockage is untested. |
| Separate service review | **Nix and Viktor** | Their conditional outgoing phone-return branches request missing handlers and wait for acknowledgements. Ordinary in-person service and the repaired Viktor debt option have separate routes. These findings do not establish that all associated quests fail. |

Two related partial-state candidates remain unresolved: **Killing in the Name** sets `mq018_started`/`mq018_active` before later contact progression, while the fresh-entry guard requires both to be zero; **Every Breath You Take** similarly sets `mq028_started` before its call phase while the fresh-entry guard requires zero. Current source confirms those sequences and guards. Neither has a matched stranded-save observation or proof that the original owner has stopped. They require a separate saved-owner investigation before any admission change.

## What was checked

- Scanned 134 archive indexes and read all 1,566 installed PTFR resource payloads. Reviewed 498 selected dependencies plus eight specific owner/admission exports, representing **504 unique resources**.
- Revalidated the exact current writers for all **51 explicit call-request facts** in the prior bounded audit. Six still lack a reader in the inspected restored resource closure. The other 45 have static reader routes; this is not a gameplay pass.
- Examined every current private payload for explicit phone request/acknowledgement facts and native holocall dependencies. The 65 matching private resources contain 24 positive request facts. The additional raw Meredith request is in an unused scene branch: the current Stout owner connects only the farewell input, which cannot reach request node 3300. It is not a new Venus in Furs defect.
- Verified that **all 30 CR1 corrective donors remain byte-identical**, including the Dennis entry acknowledgement, shared phone cleanup, Delamain ownership repairs, Yoko/Viktor dialogue repairs and service handoffs. The historical consolidation failures must not be reopened as current regressions.
- Located the six native initializers and matching cleanup implementations. Mark/Janet's original EP1 cleanup uses inline branches; searching only for external cleanup resource references would miss them.
- Rehashed all 51 managed installation paths after the audit. They are unchanged. The user may be playing, so this report does not claim their live save files remained unchanged during the session.

The Organitopia log requires care: the 16:12 and 16:17 snapshots precede the 16:18:57 call request, and the 16:24 snapshot follows a reload. They cannot establish the failed attempt's live state. The user's statement that Mark's conversation completed is retained alongside the missing acknowledgement evidence; the exact correspondence remains unresolved.

## Prepared source map

The machine-readable [case manifest](../diagnostics/phone_restoration_preparation_20261029_01/cases_02.json) records current resource hashes, request nodes, downstream acknowledgement waits, native initializer bindings, cleanup sources and existing quest-owner receipts.

| Contact | Native initializer node | Native cleanup integration |
|---|---:|---|
| Mark Bana | EP1 root 21 | EP1 counter condition 82 → inline phase 81 |
| Janet | EP1 root 20 | EP1 counter condition 80 → inline phase 79 |
| Karl Ginsky | Base root 140 | Base cleanup phase node 497 |
| Pedro Aimar | Base root 141 | Base cleanup phase node 496 |
| Nix | Base root 130 | Base cleanup phase node 494 |
| Viktor | Base root 96 | Base cleanup phase node 354 |

The initializer nodes have no phase-instance prefabs. Their full native dependencies and the pending-call state still require validation when the actual successor is built. Native resources existing on disk do not prove that their original controllers remain active after the Tower.

## Later restoration sequence

1. Restore **Mark and Janet together**, then **Karl and Pedro**. Handle **Nix/Viktor** after reviewing their service leases and exact phone-return context.
2. Add one scoped persistent support owner per contact, retaining the native controller payload, dependencies and matching cleanup. For fresh content, require listener readiness before starting the quest. For an already-issued quest, attach the missing support while preserving the existing quest/scene and queued request.
3. Define ownership explicitly. The three U9 entries expose `ParentEntered`, `Started`, `MainFinished`, `OwnerFinished` and `Fault` receipts. Combine these with native journal/facts and pending-call evidence; receipts alone are insufficient. Prevent duplicate native/PTFR controllers and retain shared ownership acknowledgements across reloads.
4. Preserve queued start/end requests, counters, outcomes, rewards and journal state. Let native handlers acknowledge the call. Keep Organitopia's original conversation → `phone end 01` → authorization-disable → door-open sequence intact.
5. Distinguish idle, queued-start, active-call, queued-end, interrupted and reloaded states. The installed Dennis repair is a useful regression control: an existing quest must not wait for an interruption flag that its own unfinished call needs to clear.
6. Integrate cleanup under the contact's ownership receipt and native counter conditions, preserving the current shared cleanup chain. Preserve all 30 CR1 fixes and both Lizzie restoration resources in the successor.

The [restoration plan](../diagnostics/phone_restoration_preparation_20261029_01/restoration_plan_01.json) contains the implementation requirements, unresolved ownership decisions and acceptance matrix. It is preparation, not an implementation or installation authorization.

## Acceptance required later

The later build must independently verify native graph edges, scene/prefab bindings, request/handler/acknowledgement chains, ownership/adoption and cleanup. Cover fresh and already-active requests, pending end acknowledgements, interruptions, saved owners, completed/failed histories and non-Tower refusal. Verify preservation of old archive members, current provider precedence, proposed depot uniqueness, the stable 51-path package, applicable script compilation and deployment/rollback interruption fixtures.

When gameplay validation is later authorized, verify actual calls, native next objectives/doors, interruption recovery, save/reload and reward uniqueness. No gameplay test is requested now. This audit does not certify every dynamic phone API, message, world controller or arbitrary active-save state.

Final [assessment and evidence hashes](../diagnostics/phone_restoration_preparation_20261029_01/assessment_01.json). `cases_01.json` is the preliminary census; `cases_02.json` adds the inline EP1 cleanup contract and narrows the listed waits to call acknowledgements.
