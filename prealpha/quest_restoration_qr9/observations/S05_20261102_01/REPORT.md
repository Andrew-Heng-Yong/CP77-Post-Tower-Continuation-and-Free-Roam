# Jinguji first visit — native starter is not a dialogue option

The user reports no quest start and supplied a screenshot of Zane's ordinary trade, Gillean Jordan and appearance options. The location/vendor is consistent with this test. A separate quest-start menu option is not required by the pinned native path.

The S05 baseline records private MQ030 Issued/Entered1, Finished/Fault0, Zane QuestOwns1/Released1/OwnerActive0, native `mq030_zane_met`0, active/done0 and ordinary default service1. These are initial readings, not proof of exact executing ownership. The user started outside/near the shop after loading; earlier owner startup is not observed.

The separate CET scripting log records first-visit changes at16:08:58 EST (`mq030_zane_met`0→1),16:09:08 (shop use0→1 and met1→2), and16:09:38 (wardrobe0→1 and met2→3). This supports meeting/shop/appearance interaction state being recorded. It does not prove a clothing purchase, and no purchase is required to satisfy the now-observed positive met predicate.

`native_starter_trace.json` records the verified pinned native raw/JSON identity and root/43 nodes/sockets. Input0 starts a wait12 for `mq030_zane_met>0`;12.Out→14.In then waits for the **player outside `#mq030_tr_jinguji_away`**. Only afterward does the authored route set up the second encounter, write active1 at9 and disable ordinary service at10. First-visit community scene17 is a separate branch. The source does not justify instructing a fixed multi-day wait or buying clothes solely to force this test.

The immediate absence of an attack/quest while still in the store is therefore not a confirmed missing-starter defect. Actual leave-area evaluation and the returning encounter remain unobserved. Next useful action: leave the shop area, walk away along the street, then return normally. Do not reset/replay quest history or force facts. If the encounter still does not start, preserve the branch and inspect the actual post-leave state rather than repeatedly waiting or purchasing items.

## Diagnostic limitation discovered

The six-row S05 probe is structurally valid:32 listener registration calls returned IDs, baseline/journal getters succeeded, and capture ended at16:10:38 with PLAYER_DETACH_OBSERVED_SCRIPT_CALLBACK and zero unregister-call failures. **There are zero FACT_DELIVERY rows despite three broad-log transitions for a watched fact inside the133-second capture window.** This is counterevidence to effective callback coverage. Returned IDs and offline Lua-double tests are insufficient to certify live delivery.

The cause is not yet source-confirmed: registration shape, function binding, callback signature, API selection or other engine behavior must be investigated. Do not silently “fix” a guessed API signature or equate this with a gameplay controller failure. The prior local observer uses the same pattern, so source similarity is not independent live validation. An attempted public NewProxy documentation lookup was inaccessible and supplied no usable API evidence. No diagnostic source or installed file was modified here.

Retain earlier initial-value/journal/phone and broad-log evidence, but do not treat absent probe transitions as negative gameplay evidence. S00/S03 had no independently established watched-fact transition to validate callback delivery; their returned-ID claims were already qualified. This new limitation remains visible and must gate any event-listener coverage claim. The next leave/return observation needs no extra probe command; existing broader CET logs can corroborate its native fact changes.

No game launch, CUA, runtime deployment, quest/save/fact edit or repair occurred during this analysis. The screenshot, logs, raw input hashes and native trace are preserved in this fresh observation directory. This is an incomplete first-meeting/leave-area test, not full S05 retirement/vendor-handoff acceptance.
