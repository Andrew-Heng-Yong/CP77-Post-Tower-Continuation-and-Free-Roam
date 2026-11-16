# TP2 retained-session presentation repair — 12 November 2026

Candidate 03 implements a covered body refresh and a bounded ending-loading cleanup. It is **prepared, not installed, and unverified in gameplay**. The arm investigation found a concrete weakness in TP1: its single native deactivation can do nothing when the representation already reports first person. The blackout's precise cause is still unconfirmed; TP2 targets residual loading presentation after the ending, with added observation of actual UI state transitions.

The installed baseline remains TP1 candidate 02, pinned by manifest SHA256 `D1EFF6EA9B2A98FE1C92C90576D8DCA1BF9A6E371818C68E046966FC90F95A4E`. All 51 Core files and 26 dependencies were freshly checked against it. No installed file, save or other mod was changed, and the game was not launched or closed.

## Findings and change

The failed TP1 trip reached the stadium, the simulation continued, the owned setup popup was absent, and no loading-finished callback was recorded before shutdown. The later restored post-Tower save completed travel to the same destination. These observations localize the difference to the retained ending session; they do not establish which native loading/fade state was stuck. The normal map flow already selects the FastTravel loading type, so repeating that request is not the repair. [Failed-session evidence](../tower_presentation_tp1_20261112_01/observations/live_20261112_1825/REPORT.md) · [Restored-save comparison](../tower_presentation_tp1_20261112_01/observations/comparison_20261112_1833/REPORT.md)

The stock fists item was attached even while the user saw no arms. Native deactivation returns without rebuilding in representation states 1 and 5. TP2 therefore replaces that standalone request with the native activation/deactivation pair, after the existing stock-arm attachment work settles. The user's successful vehicle third-person/exit workaround supports trying that pair. It remains a candidate until the rendered result is seen.

`StartupCoverLC1` now runs this sequence once, after all existing genuine-ending, arrival, profile and world checks pass and before it releases its drawn input-blocking cover:

1. Require safe, attached local V, no scene, vehicle, workspot, phone, free camera, weapon/equipment manipulation or pending stock-arm work. Require no active/loading fast-travel flag and zero loading-layer game controllers.
2. Broadcast the native loading-screen hide event and request removal of only the named `inkEndGameLoadingState` visual state. This addresses presentation bookkeeping; it does not force an actual UI state-machine transition or fabricate a loading-completion signal.
3. After a short queue interval, request native TPP representation activation. One second later, with the guards still satisfied, request native FPP return. Leave appearance callbacks and finalization to the engine. Recheck the existing handoff conditions before reveal.
4. After a settling interval, permit the ordinary cover release. Completed saves loaded into a fresh session bypass the sequence. A replaced player is never sent the old actor's delayed return event.

The sequence changes no camera, quest fact, item, equipment ID, reward or persisted field. The two modified scripts are `PTFR_LoadingCoverLC1.reds` and `PTFR_RestrictionsR1.reds`. The latter keeps its existing attachment/conservation implementation and exposes whether that transient work has settled. All other 49 paths, the 1,742-member archive, XL registrations, global-latest snapshot selection and quest restoration remain exact baseline bytes.

Diagnostics now include skinned mesh components, which TP1's `MeshComponent` cast missed, and at most 24 native UI-state callback observations per session. Existing fast-travel methods and loading-finished handling remain unchanged.

## Source evidence and validation

Native analysis is tied to executable SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4` and the matching decompiled script/cache in [input evidence](evidence_01/inputs.json). It reads executable bytes; it does not execute engine code or prove runtime state.

| Mechanism | Matched native evidence |
| --- | --- |
| Deactivation can skip a rebuild | TP1 `native_12`, handler RVA `0x2AA7794`, states 1/5 early branch |
| Representation activation and native finalization | [Event registrations](events_01/readback.json), handlers `0xAAD830`, `0x2AA79E0`, `0x2AA7A6C`; [state handling](native_20/readback.json) |
| Loading hide handler | `inkHideLoadingScreenDelayedEvent` registration to `0x7D71BC`: phase 4 via `0x7D7340`, native removal path and clear current loading-screen type; [callee evidence](native_31/readback.json) |
| Named visual-state removal | [Event registration](events_03/readback.json), `inkVisualStateRestorePreviousEvent` to `0x7D75D4`; removes that name from the visual stack rather than resetting every UI context |
| Genuine Tower and credits retained | [Final boards export](graphs_01/final_boards.questphase.json), [ending board export](graphs_01/q307_ending_board.questphase.json); no archive mutation |

The final 148-source offline compilation passed, with the full current registered inventory and unchanged installed compiler inputs. Source checks confirm unchanged persisted fields, quest/item writes, attachment implementation and fast-travel wrappers; guard/order checks cover the new one-shot path. The full 51-entry ZIP was read back for CRC, exact names and hashes. All 18 deployment/recovery fixture actions passed, including exact-byte rollback, interrupted replacement/staging/receipt recovery and a running-game rejection. [Deployment fixtures](fixture_results.json) · [Readiness](readiness.json). [Assessment](assessment_03.json) · [Compile result](compile_03/result.json) · [Candidate manifest](candidate_03/manifest.json) · [ZIP readback](deployment_01/zip_readback.json)

Candidate 01 failed compilation because its added methods were not resolved on the module-qualified class. Candidate 03 incorporates the methods directly; earlier candidates and their evidence are retained. Current readiness must be determined from the final assessment and transaction, not the highest-numbered directory alone.

## Remaining limits

Native event delivery and its effect on the blackout have not been observed. A zero-controller sample is a guard, not proof that every native fade/streaming owner has retired. The body cycle uses settling intervals, not a native rendering-completion acknowledgement. Static checks and deployment fixtures cannot certify visible arms, a working fast-travel cycle, or interrupted-save compatibility.

The next gameplay test is one fresh Tower handoff from the preserved AutoSave-2 fixture, checking arms before a reload or vehicle workaround, then one trip to the stadium. [Test card](TEST_CARD.md). Machine Gun and the user's completed Moving Heat fixture do not need to be repeated for this presentation change. Misty's clothing and Moving Heat's remaining Johnny dialogue are outside this repair.
