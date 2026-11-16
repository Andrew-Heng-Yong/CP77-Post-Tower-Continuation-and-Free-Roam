# Step 3 native wait handoff

14 November 2026. The first isolated Step 3 handoff passed **35 checks**. The fixture exercises the real-time hold and return, native registration retirement, reattachment, native timer save data and stock reload. It also holds and restores a game-time wait while the real-time transfer is in progress. The selected run pins 76 real-time and retirement slices and 32 game-time slices to the current executable. [Check output](run_03/fixture_checks.txt) · [Build and input hashes](run_03/assessment.json)

## Suspension and reload

The Step 2 Reed export supplied the original Kabuki node 5 wait with **4.44955587387085 real seconds** remaining out of 10. The fixture identifies it by the full phase address, stock provider digest, node class, current registration and native timer mapping. It rejects a due wait, an in-flight notification and a hold without a save exclusion window. An abort restores the original callback and duration to the same generation. [Handoff implementation](WaitTransfer.hpp)

The notification worker copies the old slot before a second thread would gain the graph lock. The fixture interleaves the native retirement at precisely that point, with two late duplicates in the shared queue. A replacement registration receives another slot while the copied batch still holds the old index. The handoff requires stopped producers, a completed native drain and removal of the old timer mapping. Native reattachment then creates one timer at the same logical node. After 1.5 seconds of resumed play, the native save collector reports **2.9495558738708496 real seconds** remaining. Reload attaches it to a new registration. That handler fires once at the deadline, and the prior handlers stay quiet. [Interleaving and reload checks](WaitTransferChecks.cpp)

The second wait supplied **170,486 game seconds** from the Reed export. Its duration comes from Claire's pending reply after Where Eagles Dare and serves as a clock fixture under the existing exclusion. Both selected waits are held together. An unrelated real-time timer fires normally. The game-time fixture uses native list removal, insertion, deadline evaluation and saved-ID callback binding with modeled absolute clocks and saved timer data. [Mid-quest exception](../../docs/quest_resume_exceptions.md) · [Native game-time evidence](../universal_resume_eagles_20261114_01/REPORT.md)

## Step 2 save evidence

The backed-up Manual Save 29 has 11,317 event-manager rows. Their managed values matched the decompressed 181,080-byte component at offset 18,314,418, node 909. The component SHA-256 is `B139DCC2D35305FA94BE5BFA8CCA5B5EAD1D087A818AA9ACC3CD19FEAB43E275`. Its parent save SHA-256 is `33CC1F6E96B1E8ACB357A91AA5CF2BBEE924DF70D1BAC771FFC3BE623A2397DE`.

| Reed timed registrations | Manual Save 29 |
| --- | --- |
| 18, including the Kabuki slot 2084 and Claire slot 10148 | Prior slot cleared and prior logical key absent |
| 2346 and 6628 | Same physical slot has a different registration and prior logical key is absent |
| 2478, the vehicle bootstrap wait | Same registration tuple still present at that slot |

This compares saved registration tuples. It leaves uninterrupted owner identity, timer expiry and callback delivery open. The Step 2 export binds all 21 sampled waits to source nodes. Claire's completed-job reply is the sole match to a quest body in the selected roster. [Exact Reed checkpoint and reload evidence](../universal_resume_checkpoint_probe_20261114_01/observations_04/REPORT.md)

## Live qualification

Over the Edge has an original Falco game-time wait at node 28 with an authored 24-hour duration. Its Reyes/Falco branches and parent prefab ownership need a qualified pre-ending save and handoff. No Easy Way Out has a ten-minute real-time wait at intro node 124, after Fred's message, with a separate permanent cut and the Aaron and intro prefab obligations. MS26 already has the completed job. MS9 and Point of No Return Save 1 have an Active journal entry but their saved event tables lack the intro timer phase rows. This Corrosion has a three-day game-time wait at node 60 after Yoko's earned component-ready fact. The inspected MS26 has no recorded journal entry or positive component-ready fact for it. Each lead requires its actual entered stage and bound owner before a Tower trial. [Over the Edge source trace](../quest_restoration_qr3/agents/agent_d/quests/mq049_edgerunners/REPORT.md) · [This Corrosion source trace](../quest_restoration_qr6/groups/C03/quests/q305_postcontent/REPORT.md)

The isolated fixture supplies completion, save exclusion and producer quiescence as modeled inputs. Live Step 3 still requires a synchronized cutoff and save barrier, verified teardown of the original owner and its support, and a sole qualified owner through genuine Tower completion. The first live run must verify one actual timer, a save and reload before expiry, and one callback at the retained deadline. Base-game, EP1 and inactive-control qualification remain open. The installed checkpoint v0.1.4 still matches all 51 Core paths, one checkpoint DLL and 26 required paths. [Current installation](../universal_resume_checkpoint_probe_20261114_01/deployment_01/installed_manifest_01.json) · [Live acceptance contract](../../docs/quest_resume_contract.md)
