# LC3: remove the exit action and stop purchase prompts competing with startup

Installed October 24, 2026. Live retest pending.

The 17:32 test completed the Body/Relic and eight other perk refunds, reached
150 maximum HP, acknowledged housing, and completed the native handoff. The
cover reached final checks at 41.31 simulation seconds, then alternated between
checks 10 and 11 every second until shutdown. Its continuous one-second
stability timer was repeatedly reset. The session shut down normally at 17:33:39;
it passed the previous crash point, not the complete startup/reload test.

H1 contains a feedback loop matching that cadence. Every second, its purchase
UI publishes `PurchaseReady` from `CanPurchase`, whose `SafeActor` predicate
requires V not to be in a scene. The four purchase scenes previously acquired
V as a player actor. Their native watcher exits when `PurchaseReady` becomes
zero, after which eligibility can turn true and start the scene again. The
native historical-purchase gate can admit those scenes far from their entrances.
The cover independently requires V to be free of scenes before revealing play.

LC2's log combined the final control predicates, so it does not identify which
subpredicate was false on each sample. The purchase feedback mechanism is
source-proven and matches the timing; successful elimination of the reported
stall still requires a live test. LC3 adds detailed camera/control, Body-safe,
and apartment purchase-scene diagnostics to future final-stage heartbeats.

Changes:

- Removed the Esc/main-menu hint and action, including error and timeout text.
  Cancel input is consumed. The old public `Leave(epoch)` signature remains as
  an inert compatibility entry point and never sends a main-menu request.
- Apartment purchase offers and confirmation dialogs wait for gameplay release.
  Native offers also require the exact existing entrance-position validator.
  This gates gameplay interactions, not housing setup or loss acknowledgements.
- The four world-attached purchase scenes no longer acquire a player actor.
  Their five executable nodes do not reference one. The unused player definition
  and its debug symbol are removed; every executable node, edge, price-related
  condition, request and exit remains identical. All thirteen other archive
  resources—including repaired service scenes and saved quest owners—remain
  byte-for-byte identical.

All previous setup checks and the continuous one-second stability requirement
remain. Faults still keep the cover in place. No time-based bypass, fake progress,
quest restart, refund replay, payment, forced native story fact or camera action
is introduced.

The package replaces three files: `StartupCoverLC1.reds`, `HousingPurchase.reds`,
and `00000000_TowerContinued_Housing_H1.archive`. The new archive SHA-256 is
`4D4CB40E745F9508F97F1A2A0F2D09DD02E0AD527BEC1A4D1B874AA647F55208`.
The main archive, native LC2 waiting condition, frameworks and cosmetics remain.

Validation: CLI preflight and the full 87-source SCC stack including EquipmentEx
passed. Compiled SHA-256:
`8BFB147CEAE835E16CFF8A2D27EE0EC20583A9BF4A867CBCD455A5075E674069`.
Seventy-three compiled/native/preservation/feedback checks and fourteen real
installer fixture actions passed. Validate, Install, Verify and ValidateRollback
passed with 647 protected files, including 253 save-directory files, unchanged.
No assistant game launch or save edit occurred.

Next: cold launch and load the same retained save used in the failed attempt.
Check that there is no exit hint, the cover completes, and control becomes
available. Use a new manual slot for save/reload. Local apartment purchase-choice
display, confirmation/cancel/payment and service-scene behavior remain live
tests; native scene acceptance is not established by offline readback alone.

Recovery: first use `prealpha/loading_cover_lc3/deploy_01.ps1 -Action
ValidateRollback`, then `-Action Rollback` if needed. Backups are in
`recovery/loading_cover_lc3_01`. Undo LC3 before either SC1 or LC2 because it
overlaps both packages. It restores the SC1 housing archive, LC2 cover and
previous purchase UI. File rollback is not save rollback. Older core/cosmetic
recovery chains remain separate.

Evidence: `prealpha/loading_cover_lc3/candidate_01/assessment_01.json`,
`diagnosis_01/assessment_01.json`, `native_01.json`, `compile_01/result.json`,
`tests_01.json`, `deployment_tests_01.json`, and the install manifest/receipt.
Final sources and proofs are pinned; use successors. No public release update.
