# Step 2 execution checkpoint

14 November 2026. The workspace candidate records execution state through the existing pre-cleanup gates on the Reed and Hanako routes. It commits the native record and the corresponding history samples in the current save before acknowledging the gate. RD10 is the installed baseline. [Candidate files and hashes](candidate_02/receipt.json) · [Verification](checks_02/results.json)

## What the checkpoint records

- The ordered quest-resource indices, loaded phase paths and depots, and the original handler registration types, nodes and slots. Each slot records whether the live handler map resolved that registration uniquely. The record includes pending resource requests, queued handler notifications, and the native node-instance key/value pairs written by the stock serializer.
- Native suppression, logical AND input masks and XOR latches in stores 3 through 5. For the Epistrophy fixture, the recorded value of 70 at native node 198 preserves In2, In3 and In7 as signaled, with four other inputs still pending. The runtime reads each mask from the native table.
- Real-time and game-time wait samples on their respective scheduler jobs. A sample must match the original handler, timer ID and node-instance value, remain within 250 milliseconds of the graph read, and have no observed ready or queued signal. The record carries each sample's age. Exact remaining time at suspension still requires the Step 3 handoff.
- The matching journal states, objective counters, optional and tracked bits, named facts and item observations. The checkpoint retains these save-local copies when the global latest-history loader updates its cache.
- The player's entity ID, scene tier, scene and dialogue participation, and scene camera control. The phone observation records the manager's active flag, the blackboard contact, phase, mode, direction and other call flags, and the corresponding talking fact when the contact is known. These reads use the installed script interfaces and occur in the same queued capture request as the graph read.

## Cutoff and recovery

The native sampler checks the exact game executable and RD10 archive. It recognizes the authored FactDB manager node, gate operation and current native phase before accepting the route and ticket. It uses the native graph and queue locks and tracks quest load, teardown, root creation and deferred restoration. It also declines capture while the native notification worker holds a copied batch. Two further history polls can retry a missed read. The native gate retains its existing acknowledgement and timeout paths.

The save stores a per-capture ID and the packed checkpoint words. The recovery writer uses the existing write, flush, close, readback and rename protocol to publish a file keyed by that ID. Recovery verification requires byte equality with the checkpoint in the current save. The global history loader continues to accept its existing history formats.

The candidate contains two existing history-file replacements and one private RED4ext plugin. Its report records the exact input archive and gate member hashes. [Compile inventory](compile_05/receipt.json) · [Native source](NativeCheckpoint.cpp) · [Save-local fields](checkpoint_members.reds) · [Recovery writer](checkpoint_export.lua)

## Evidence and remaining work

The 148-source REDscript compile, 41 native fixture checks, 46 executable checks and 12 Lua checks passed. Compiled-script readback confirmed the checkpoint commit precedes the final acknowledgement. The fixtures cover both routes, concurrent clocks, queued or stale waits, the Epistrophy mask from Manual Save 26, and two saves with matching ticket and revision values. The global-loader regression check transferred every primitive from the pinned HS1 and HS3 files. All 51 installed Core paths and 26 dependencies matched RD10 after verification. [Recorded results](checks_02/results.json)

Live validation still needs a genuine Tower cutoff, followed by save/reload and checkpoint recovery readback. External actor and prefab bindings, ordinary scene playheads, and phone dialogue playback positions still need qualified readers. The current presentation fields identify participation and call state. The shared mechanism needs a timed original handler in an unfinished in-scope quest for the first suspension and reattachment test. The Epistrophy fixture covers the separate partial-input control. [Resume roadmap](../../ROADMAP.md#any-point-quest-resume-after-the-tower) · [Step 1 saved controls](../quest_resume_contracts_rc2_20261114_01/REPORT.md)
