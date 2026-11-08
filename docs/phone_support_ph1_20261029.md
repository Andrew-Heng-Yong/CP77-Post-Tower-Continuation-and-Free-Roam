# PH1 — missing phone support restored

29 October 2026. Implemented and installed with the game closed under the user's explicit authorization. Selected build: `prealpha/phone_support_ph1/candidate_03`.

The repair restores native phone controllers and matching cleanup for Mark Bana and Janet (**Spy in the Jungle**), Karl Ginsky (**Nasty Hangover**), Pedro Aimar (**Desperate Measures**), and conditional Nix/Viktor service phone returns.

Each contact has a persistent scoped listener with its own Ready/Issued receipt. New gig admission waits for its listeners; already-issued active gig receipts allow support to attach without restarting the gig. Service listeners require their restored service owner. Start/end requests, acknowledgements, call counters, choices, rewards and journals are left for the original native handlers. Interrupted pending calls do not wait on an interruption flag that their own completion must clear. Existing executing quest descendants are untouched.

The ordinary native initializer ancestry was traced through base additional content and EP1 additional content, along with the alternate Q307 infrastructure owner. Both original retirement routes were reviewed. Admission requires the completed Tower journal as well as the existing post-Tower and phone-support guards. There is no public runtime phase-liveness query; this is source and receipt-based ownership, not a claim of live owner observation.

Matching cleanup is integrated into the existing shared reset chain under each contact's issued receipt and original counter tests. Mark/Janet retain their inline EP1 cleanup graphs; the other four retain original cleanup references. The original Organitopia conversation-completion → authorization-disable → door-open sequence is preserved.

## Verification and installation

- 76 serialized graph/binding checks and 206 scoped admission/pending-call condition cases passed. These are structural checks, not an engine or save-restoration simulation.
- Full archive readback: 1,572 members, including 1,562 byte-identical old members, four reviewed edits to old resources, and six new resources. The edits are the shared cleanup and three U9 admission wrappers.
- All 29 other CR1 corrective donors remain byte-identical. Existing cleanup nodes and nested graphs were independently compared, with its terminal routing extended into the new scoped branches. LR1/LR2 and other restored content remain byte-identical.
- Fresh 134-archive checks verified native providers and absence of collisions for the new depots. Native controller, cleanup and scene resources were pinned. No REDscript changed; no new script compilation is claimed.
- The full 51-path local ZIP passed CRC and per-file hash readback. Beta distribution files were not revised.
- Four deployment fixtures passed, including recovery from three simulated interruptions. Actual closed-game Validate, Install, Verify and ValidateRollback passed.
- Only the combined archive and its XL changed on disk. All 51 managed hashes were verified after installation. All 307 save files and 49 Lizzie's Braindances files retained their names and bytes.

The game was not launched. Actual call playback, resumption of an already-stalled scene, physical Organitopia opening and save/reload remain **live unverified**. No further gameplay test is requested by this record. Killing in the Name and Every Breath You Take remain unconfirmed partial-state cases and were not changed.

## Evidence and rollback

See `prealpha/phone_support_ph1/candidate_03/installed_assessment_01.json`, `evidence_hashes_01.json`, `semantic_verification_01.json`, `state_tests_01.json`, `ancestry_proof_01.json`, `verification_01.json`, and the deployment/preservation reports.

Recovery is `recovery/phone_support_ph1_01`. With the game and launcher closed, roll back PH1 **before LR2**:

```powershell
pwsh -NoProfile -File prealpha/phone_support_ph1/deploy_01.ps1 -Action ValidateRollback
pwsh -NoProfile -File prealpha/phone_support_ph1/deploy_01.ps1 -Action Rollback
```

This restores installation files, not saved gameplay state. Candidates 01/02 are intermediate build evidence; candidate 03 is the installed selection. Historical builders must not be rerun against production.
