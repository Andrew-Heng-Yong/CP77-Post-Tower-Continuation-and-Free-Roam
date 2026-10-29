# Hiding the credits-to-setup camera flash

Update: the scoped LC4 candidate described below was subsequently built and installed. See [LC4 installed record](credits_cover_lc4_20261028.md). The following report preserves the original investigation and proposal.

There is a concrete candidate for hiding the brief credit-call location shown before setup: keep the world black across the Tower credits handoff, then transfer coverage to the existing setup popup. The installed graph contains an early reveal that can explain the reported flash. This is a source-supported diagnosis and proposed solution, not a reproduced frame trace or an implemented fix.

The user reports a brief view near the credits phone-call staging location, such as Afterlife, immediately after credits end and before the setup screen appears. This is a separate issue from the earlier Buran St–El Coyote fast-travel blackout. No fresh game test, deployment, save edit or fact write was performed for this investigation.

The current installed combined archive, XL, loading-cover script and arrival script match WA3 candidate_02. A fresh scan indexed **133 installed archives** for the two credits phases and the menu resource. Each phase has its native copy and the expected PTFR replacement only; the menu has one native provider. The inspected resources were extracted directly from those installed archives. This is a three-resource check, not an audit of all resources in those archives. Captures and hashes are in [capture_01.json](../diagnostics/credits_transition_cover_20261028_01/capture_01.json).

| Boundary | Installed behavior | Consequence |
| --- | --- | --- |
| Credit calls return or are cut | Shared `final_boards` node27 notifies that the videos finished; its output also invokes node28, `fadeIn=1`, duration0 | The native world blackout is cleared immediately. Video completion is earlier than text-credit dismissal on a watched run. |
| Wait for credits closure | Nodes104/107 test CreditsRolling=false twice, with a100ms delay; the true branch polls every100ms | Cover acquisition downstream of this wait cannot precede the first observed closure. These are graph delays, not a measured visible-gap duration. |
| Start setup | Node140 writes `PTFRPA2_Started=1`; node141 starts a250ms fade-out | The popup's `Required()` and listener only become eligible here. The world can be exposed before this point. |
| Transfer cover after arrival | Node180 resets `PTFRLC1_CoverReady`; node181 waits for it; node176 fades in, followed by Tier1/control checks | This existing overlap protects the later native-fade-to-popup handoff. It does not protect the earlier credits-close gap. |

The Tower board's skip path already has an instant fade-out: `ForceStopped` node12 → black node7 → cut node6 → shared return. Shared node28 then undoes that blackout. Natural call completion and the skip/cut return converge before the shared node27. The exact ordering of the quest scheduler, native UI close request and rendered frames remains unmeasured, so this topology alone cannot guarantee a zero-frame skip transition.

**Recommended first candidate:** add a narrowly guarded Tower fade handoff in the existing combined `final_boards` resource. Acquire an instant black cover after the Q307 call phase has returned or been cut, preferably before notifying node27, and suppress the node28 instant reveal only for that authorized handoff. Keep the original node28 behavior for other routes and failed admission. Preserve the video notification, credit-call scenes, music, skip controls, retained-session routing, teleport, camera repair and setup transactions.

The current native `finalboards_credits` menu is explicitly `isAffectedByFadeout=0`. That supports holding world fade beneath the remaining scrolling credits. Starting after the call phase returns avoids intentionally covering an ongoing call. The menu property is not proof of how every scene texture or the first closing frame renders; watched completion and skipping during different calls remain separate acceptance cases.

Let the existing sequence continue to `PTFRPA2_Started`, popup attachment and its opaque animation acknowledgement. Keep the native fade release at node176 **after** the cover acknowledgement. Then let the popup remain until its normal12 checkpoints and stability check pass. Holding native fade until all setup completes would reintroduce the old PA2/PA3 dependency problem: camera/control readiness waits for native fade release. The popup is the layer that should cover the rest of setup.

The proposed sequence is:

```text
credit calls finish / are cut
    → guarded world black; remaining credit UI remains visible
    → normal credit UI dismissal and Tower cleanup
    → existing setup popup attaches and acknowledges coverage
    → native fade releases beneath that popup
    → setup completes and popup reveals H10
```

This needs an explicit ownership/cancellation path. An early black cover must have a matching release if admission is withdrawn or the session changes before setup starts. Reuse the genuine Q307 route and guard, distinguish an in-progress bridge from a completed handoff, and preserve epoch/load cleanup. Do not set `PTFRPA2_Started` early just to summon the popup: it authorizes other arrival behavior. Keep the existing cover acknowledgement as a real wait, and retain fault reporting and rollback behavior.

**Fallback if a skip still exposes a frame:** a guarded pre-close UI bridge at `MenuScenario_FinalBoards.OnCloseFinalBoardsRequest`, before `GotoIdleState`, with coverage retained until the setup cover takes over. The locally decompiled scenario code closes menus through Idle. Codeware's currently installed popup manager attaches notifications asynchronously through a delay callback; simply calling `ShowPopup()` and immediately closing credits is therefore not an atomic cover. A pre-close bridge would need a verified surviving UI layer or a render-aware handoff and cancellation handling. This is more invasive than fixing the identified native reveal, so it is not the first candidate. Native-address observations in the older lifecycle research were not revalidated against today's executable and are not proposed hooks.

Changing only the250ms fade to instant, shortening polling, or moving the camera earlier would not remove the preceding reveal reliably. The source supports masking the handoff while retaining the established camera restoration.

Before promoting a candidate, verify watched completion, skipping during Rogue/Afterlife and another call, no visible world frame between covers, unchanged credit media and input, normal setup completion, restored-save loads, interruption/session changes, and non-Tower endings. Offline graph/hash checks can establish scope and ordering; first-frame behavior needs a runtime capture. This investigation records that validation requirement without requesting another in-game test now.

Evidence: [graph trace](../diagnostics/credits_transition_cover_20261028_01/graph_trace_01.json), captured installed `PTFR_LoadingCoverLC1.reds` and `Codeware.UI.reds`, prior [LC1](loading_cover_lc1.md), [LC2](loading_cover_lc2.md), and [credits lifecycle research](../research/finalboards_dismissal_lifecycle.md). No implementation or installed file was changed.
