# Over the Edge timer and prefab handoff

15 November 2026. The workspace implements native game-time deadline restoration and prefab ticket readback for the first Step 3 handoff. Manual Save 31 supplies the original Falco wait. The earlier plan supplies the nine selected original registrations and the Reyes choice. [MS31 restore selection](../universal_resume_falco_transfer_20261115_01/REPORT.md)

## Game-time restoration

The native handler initializer at `0x193C74` reads its node mapping. With an empty mapping it schedules through TimeSystem at `0xA09BC4`, then publishes the new timer ID at the original quest node key. The scheduler computes absolute time before calling the factory at `0xA0A84C`. The restore scope supplies the captured remaining time at that factory. It preserves the native allocator, one-shot callback, authored period and queue operation. Calls for other owners take the stock path. The scope requires a save permit and the bound replacement handler, quest context and clock. It defers before initialization if the old mapping is still present. [Game-time restore source](GameTimeRestore.hpp)

**13 offline checks passed.** The fixture runs stock initializer, scheduler, timer factory, constructor and expiry callback code against synthetic system objects. With MS31’s 86,388 remaining game seconds and the MS29 control clock of 7,430,843, the new record enters the queue at deadline 7,517,231 with its 86,400-second authored period and a fresh ID. The native evaluator stays quiet until that deadline and notifies the rebuilt slot once when due. The factory override leaves an unrelated wait on its stock deadline. A failed timer-ID reuse control exercises native uninitialization, which clears its mapping and enqueues cancellation. The fixture models queue consumption and observes notifications at the quest boundary. [Clock checks](run_01/checks.txt) · [Exact inputs and results](run_01/assessment.json)

## Prefab lease readback

The source-matched path contains two authored prefab references, `#mq049_pr_main` and `#mq049_pr_reyes`, both on the parent quest resource. The phase instance and its owning phase-node handler each receive a native ticket. Readback uses the pinned loader’s ticket map, resolved-reference counts and ready queue under its native try-lock. It checks that both replacement tickets resolve the same two references, that their pending and ready queues have cleared, and that the retired IDs are gone. An unrelated shared lease can still hold either reference. Actual streamed support requires separate world evidence. [Lease readback source](PrefabLeases.hpp) · [Pinned lifecycle](../quest_restoration_qr15/lifecycle_01/prefab_native/REPORT.md)

**12 offline checks passed** with synthetic loader state. They cover a valid shared lease replacement, stale or reused tickets, ready-queue entries, pending and failed requests, mismatched or insufficient references and a busy native lock. [Prefab checks](run_prefab_01/checks.txt) · [Layout pins and inputs](run_prefab_01/assessment.json)

## Live integration boundary

The normal quest update at `0x4AD5CC` processes prefab callbacks through `0x698FC8` before finishing the notification batch through `0x3534DC`. That batch takes and releases the quest graph lock at `+0x60`. Its return is a candidate boundary for reading drained notifications under the existing checkpoint hook. The clock update at `0x7C0CA0` independently consumes enqueue and cancellation requests before it evaluates timers. A quest-side mapping therefore needs clock-side readback before committing the handoff.

Stock restore uses the resource cache’s `+0x28` entry at `0x19387E4` for the full paths collected by `0x2B26A4`. It uses `0x2B28EC` during startup to initialize the saved registry. The live successor still needs to submit the nine selected paths and bind their resource readiness within the retained quest session. It must verify the original callback producers have stopped and resolve actual world support before publishing the new owner. Installation, gameplay and save/reload qualification remain pending. [Prior native path fixture](../universal_resume_falco_transfer_20261115_01/REPORT.md)
