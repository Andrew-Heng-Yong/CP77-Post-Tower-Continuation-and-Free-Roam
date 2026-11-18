# Credits-to-setup flash: video review, 16 November 2026

The supplied `example vid.mp4` confirms an uncovered view of the Afterlife bar before the setup page appears. The issue remains open. This investigation changed no runtime source, game file, save or fact and did not build, install or launch anything.

## Observed in the supplied recording

The 1920 x 1080 recording contains 442 video frames over approximately 15.35 seconds. Its SHA-256 is `76114B30255841929F0BBE5FBE58E5D366C2264402C1A2838051D51372B40388`. Frame numbers below are zero-based video samples, not engine render-frame counts. Timestamps come from the decoded presentation timestamps; the recording is not assumed to be exactly 30 fps.

| Video timestamp | Observation |
| --- | --- |
| Beginning | Credits with Rogue's call visible |
| Following credits | Black screen, then a loading indicator, then black again |
| 10.621770 s, frame 306 | Last black sample before the exposed location |
| 10.656547 s, frame 307 | Afterlife begins to fade into view |
| 10.899983 s, frame 314 | The bar is brightly visible |
| 11.143419 s, frame 321 | Last exposed bar sample |
| 11.178195 s, frame 322 | Opaque setup page appears: “Finishing the ending handoff,” 2 / 12 checks |
| Later in the clip | Setup advances to “Preparing arrival,” 4 / 12 checks |

The exposed interval spans 15 recorded frames and approximately **0.522 seconds**. Only one exposed location was identified in this clip. It ends during setup, so it does not establish completion or a setup stall. Neither the installed version used to record it nor live fade/quest state at the flash is embedded in this evidence.

[Three-frame comparison](../diagnostics/credits_flash_20261116_01/handoff.jpg), [all boundary samples, part 1](../diagnostics/credits_flash_20261116_01/boundary_01.jpg), [part 2](../diagnostics/credits_flash_20261116_01/boundary_02.jpg), and [timestamps and image measurements](../diagnostics/credits_flash_20261116_01/video_frames.json) are local evidence. Images and extracted game data remain under the ignored diagnostics directory.

## Current source and installation checks

The installed combined archive still matches WO1: `20957F0D58A3F10B9FD050E6F6FDEF1FCBB592EFBE49DB34324B11A993665FF7`. The installed loading-cover script still matches its current manifest: `28DE7FF86E287533F0F4B9A7EC9BE0C5ED44198F4AA7B8373628612D0EE2125D`.

The current consolidated `final_boards.questphase` source is byte-identical to LC4's recorded cooked resource, hash `BEF2A39D09272E66BA2D48CC4392F970EF575424F7288EC13D999DE92684F1EC`. LC4's inspected graph JSON matches its assessment pin. This establishes that the existing repair is retained in the installed lineage; it does not establish the recording's exact build or executing saved owner.

- Nodes 182/183 acquire instant world black on the guarded Tower route before node 27's videos-finished notification. Nodes 184/185 suppress node 28's original reveal and record the black-held receipt on the same guarded route.
- Setup eligibility starts later: two closed-credit checks at nodes 104/107, separated by a 100 ms graph delay, precede node 140 setting `PTFRPA2_Started`.
- `StartupCoverLC1.Required()` needs that start fact and genuine completed Tower facts. The installed Codeware popup manager queues its attachment through a delay callback and retries if its notification container is unavailable. Requesting the popup is not a synchronous visible-cover operation.
- The setup popup sets its root opacity to one and uses a 0.10-second constant-opacity animation completion callback to acknowledge its cover. That source does not independently verify that its parent UI layer is visible in the final composed frame across loading/menu teardown.
- The later graph handoff already waits for `PTFRLC1_CoverReady` at node 181 before node 176 releases native fade and permits camera/control readiness. Holding this native fade until all setup checks finish would conflict with that dependency.

[Current hashes](../diagnostics/credits_flash_20261116_01/source_hashes.json) and [compact graph trace](../diagnostics/credits_flash_20261116_01/current_graph_trace.json) record the inspected inputs. The older [LC4 report](credits_cover_lc4_20261028.md) correctly left watched/skipped rendered-frame validation pending. The [earlier investigation](credits_transition_cover_20261028.md) already identified asynchronous popup attachment and a possible pre-close UI bridge as limitations.

## Diagnosis and repair target

Follow-up: the current executable and matching vanilla scripts now qualify the pre-close integration point. See the [LC5 continuous-cover proposal](credits_cover_lc5_solution_20261116.md) for the bounded implementation design and remaining rendering-host check. No runtime fix is installed.


**Confirmed:** visible coverage is lost before the setup page takes over. The gradual reveal is consistent with a fade being released while no opaque setup layer is visibly covering the world.

**Not established:** which fade command or UI/loading transition causes the reveal, whether the LC4 guard ran in the recorded session, or whether cover acknowledgement preceded actual on-screen visibility. Current local log excerpts are from other continuation-save loads and cannot answer those frame-specific questions. The video does not establish a wardrobe/Atelier cause.

The repair target is continuous Tower-only visual coverage through credits closure, loading-layer dismissal and setup attachment, with overlap until the receiving cover is visibly ready. Review a cover that survives those UI transitions and the validity of the present acknowledgement; merely adding another fixed delay or calling `ShowPopup` earlier is not demonstrated to solve it. Preserve genuine ending completion, all current admission guards, saved identities, cancellation cleanup and the later fade-release-to-camera/control ordering. Any native/script close hook from the older 2.31 lifecycle research needs validation against the current game before implementation.

Acceptance must include the recorded close-during-Rogue-call route, another skipped call, watched credits, slow loading/UI attachment, setup completion and camera release, reload/cancellation, and an unaffected non-Tower ending. These are future checks, not results from this review.
