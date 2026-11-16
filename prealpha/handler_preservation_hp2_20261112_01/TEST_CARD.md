# Step 3 preservation trial: prerequisites and observations

**Not ready to run.** The installed HS4 build loads snapshot history; it does not implement the preservation mechanism in this card. HP2 found that the native freezer alone does not provide exact remaining-time suspension. Do not replay The Tower solely to test that missing feature.

## Developer gates before a game test

- [x] Identify real original registrations for one active base-game quest, one active EP1 quest and one inactive quest. HP1 found 5, 7 and 11 respectively in ManualSave-26 and AutoSave-10, then none after native shutdown.
- [x] Review native freezer stop/reinitialization. HP2 identifies timer mapping removal and authored-duration fallback. This is a rejection of the proposed exact-pause primitive, not a gameplay pass.
- [ ] Implement a qualified suspension mechanism, including remaining time and queued-event behavior, or explicitly limit the design to reviewed stage adapters.
- [ ] For preservation, retain original path/node/resource identities and ancestors; qualify parent/support leases and interruption cleanup.
- [ ] Preserve genuine Tower cleanup with truthful ownership receipts; block private duplicate controllers for retained jobs.
- [ ] Apply the existing Johnny edits along the actually retained native paths. Inactive Highwayman's private edited resources are not automatically used by its original owner.
- [ ] Build a fresh candidate, perform exact resource/registration readback and relevant offline checks, and prepare a guarded deployment. No candidate exists in HP2.

## Small timer/callback test first

Use an isolated, private test fixture with no quest rewards, player inventory changes or synthetic pre-Tower history. The fixture still needs implementation. It must cover both real-time and game-time delays, plus an event listener.

1. Start a measured 60-unit delay and suspend after approximately 20 units. Capture the native timer identity and remaining duration.
2. Keep it suspended for longer than the original remaining interval. Advance the relevant clock only through the reviewed fixture/game behavior. Confirm no completion callback or downstream effect during suspension.
3. Resume. Expect approximately 40 units remaining within measured scheduler tolerance, followed by exactly one callback. Immediate firing or a fresh 60-unit interval fails exact resume.
4. Repeat with a supported save/reload while suspended and after resume. Verify durable identities and no extra callback registration.
5. Exercise an event queued just before suspension and another generated during suspension. Verify the explicitly designed delivery/discard policy and exactly-once handling after resume. A quiet log alone does not prove the queues drained.

The three selected quest stages have no active timer, so they cannot replace this test. Do not request a new real timer save until the mechanism and fixture are ready.

## Three-quest Tower trial after those gates pass

Start from **ManualSave-26 before Reed's cutoff**, with the exact candidate and fixture hashes recorded. AutoSave-2 at Viktor is already after retirement of the original handlers and cannot test prospective preservation. Preserve the original save and use separate new test slots. Record the exact global-latest snapshot selected; do not change the user's global-latest policy or assume an unrelated file matches the fixture.

| Case | Natural action after genuine continuation | Required result |
| --- | --- | --- |
| Machine Gun | Continue the existing **Deliver Skippy** objective using the existing Skippy. | Original earned progress and counters remain intact; Regina delivery works; one weapon handoff and one reward; no setup replay, duplicate gun or duplicate ambient owner. |
| Moving Heat | Continue the existing first-door objective and then its natural quest route. | Door/security/loading-area callbacks and actors work with the same earned state; no duplicate setup, repeated messages or repeated vehicle reward; approved cast behavior remains intact. |
| The Highwayman | Leave it undiscovered first, then trigger its normal discovery. | It remains inactive until the legitimate trigger; one set of discovery callbacks; normal progression and one-time reward; the installed garage/body Johnny edits actually execute. |

Capture before cutoff, during the hospital period, after genuine ending completion and after continuation. Complete Viktor, thugs, Misty, final scene and credits normally; do not force ending facts or load a pre-ending save to simulate continuation. Verify exactly one owner for each retained quest and no progressing callbacks while suspended.

Save and reload at game-supported points during suspension and after resume. A lack of save permission during a scene is not a reason to force a save. Complete the natural quest outcomes, verify cleanup, then reload once to check that setup and rewards do not repeat.

Passing these three fixtures qualifies only their observed states and routes. It cannot certify all restored quests at every stage. Other handler/timer/callback families require their own capability evidence or a reviewed stage adapter.
