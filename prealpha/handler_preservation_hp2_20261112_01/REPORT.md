# Step 3: native freezing is not an exact quest pause

The native area freezer does not qualify as the shared mechanism for resuming every restored quest at any moment. Its stop path removes running handlers. The two inspected native delay handlers remove their saved timer-ID mappings and request cancellation; initialization without the old mapping takes the duration from the quest definition. This provides a concrete timer-state obstacle beyond HP1's previously unverified suspension contract.

This is a static engine result, not a live freeze/resume observation. No preservation candidate was built or installed. Step 3's preserved-owner Tower/reload trial remains unrun. Use the adapter fallback from the original plan; exact arbitrary-moment preservation would require additional timer, callback and ownership work. A reviewed stage restart remains distinct from exact continuation of a partially elapsed timer.

## What was established

The read-only investigation binds the following paths to executable SHA-256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. Addresses are RVAs in that file, not callable public APIs.

| Path | Evidence and consequence |
| --- | --- |
| Native freeze | Freezer update `0xBEB194` calls quest-system eligibility `+0x220`, collection `+0x228` and targeted stop `+0x218`. The stop wrapper `0xBEC238` constructs mode 5. |
| Original identities | The path routes through the synthetic root and existing phase tree. It collects existing node keys and deferred input words; it does not relocate the quest under a private root. Some graph stores preserve state in mode 5, as independently documented in QR15. This is useful, but not a complete suspension contract. |
| Handler removal | Root/phase `+0xF8` leads through `0xBEC6D4` to recursive stop `0x2B1D30`. PauseCondition's exact stop virtual is `0x2FDA9C`; removal reaches handler Uninitialize `+0x20` at `0x2FCF77`. |
| Real-time delay | Definition vtable `0x302C5A8` creates handler vtable `0x31267A0`. Uninitialize `0x194828` removes the node-to-timer mapping and calls DelaySystem `+0x1D0`. That method enqueues the timer ID at `0x7C72C0`; it is not a cancellation-complete acknowledgement. Initialize `0x1948BC`, when the mapping is absent, schedules using the definition duration at handler `+0x48`. |
| Game-time delay | Definition vtable `0x31033B0` creates handler vtable `0x31C2388`. Uninitialize `0x1934AC` removes the mapping and calls TimeSystem `+0x250`, which enqueues the timer ID through `0x2179420`. Initialize `0x193C74`, when the mapping is absent, uses the definition duration at handler `+0x44`. |
| Wake | The freezer reconstructs necessary phase state and dispatches recorded inputs in mode 6. This does not supply an established remaining-time transfer for the two removed delay handlers. |

For example, a 60-second delay frozen after 20 seconds needs approximately 40 seconds remaining after resume. The traced reinitialization without its original timer mapping supplies 60 seconds. That example illustrates the code path; it is not a measured gameplay result. Cancellation-queue races, expired records and other condition types remain separate questions.

The selected ManualSave-26 stages contain 23 original registrations: five Machine Gun, seven Moving Heat and eleven inactive Highwayman. None is an active timer condition. They are good ownership/callback controls, but cannot measure remaining-time preservation. Native quest-phase delay examples are retained in the assessment; their source presence does not mean those timers are active in this save.

## Effect on the preservation prototype

Simply adding an unfreeze trigger or bypassing q307 cuts cannot implement the requested feature. HP1 also established independent base-game and EP1 ancestor retirement, private admission that assumes retirement, and Highwayman's original scene references bypassing the installed Johnny edits. These remain unresolved by the freezer investigation.

A true preservation implementation would need all of the following before a human trial: capture and restore each supported timer's remaining duration; suspend callbacks with a defined policy for already queued events; preserve ancestor and support ownership; use truthful selective-retirement receipts; exclude duplicate private owners; and route the retained identities through the approved Johnny edits. Neither snapshot loading nor a zero/one killed fact provides these capabilities.

For the minimal-effort route, retain genuine native retirement and use the shared dispatcher with reviewed earned-stage adapters. Keep unsupported states deferred. This does not establish universal every-moment coverage or authorize resetting quest progress. HP1's [stage-entry requirements](../handler_preservation_hp1_20261112_01/NEXT_STEPS.md) remain applicable.

## Validation and current status

[Selected assessment](analysis_02/assessment.json) records 158 successful evidence/preservation checks: captured instructions were compared with current executable bytes and decoded again; captured table pointers were read back; 79 pinned runtime/manifest/snapshot inputs and four historical save bodies remain unchanged. These are static and file checks, not 158 gameplay tests. The large registry database was not rehashed in this successor; the selected HP1 qualification is pinned separately.

`analysis_01` is retained as the earlier assessment. `analysis_02` adds the timer-system queue bindings and explicitly distinguishes requesting cancellation from observing completion. Leaf decoding can include bytes after an unconditional tail jump; those following bytes are not used as part of the wrapper's semantics.

HS4 remains installed with the user's global-latest snapshot selection. Its successful AutoSave-2 snapshot test is not reopened. No game process was accessed or launched, no game/save files were written, and no deployment or gameplay qualification occurred.

The [test card](TEST_CARD.md) records the distinct tests required if a preservation implementation is pursued later. There is no new test for the user to run on the installed build.
