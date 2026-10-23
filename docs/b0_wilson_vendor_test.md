# Wilson's 2nd Amendment opt-in test

2026-09-24. One-shop disposable-save probe. The archive is inert until `Start()` writes its own opt-in flag. The normal H10 apartment and mirror packages stay separate.

## One short in-game run

1. Cold-launch Cyberpunk 2077 and load a **disposable post-Tower save**. Approach Wilson's H10 shop while V is outside combat, a workspot and another scene. If Wilson or a physical Shop prompt is already there before arming, stop and report that baseline.
2. Run `GetMod("PTFR_B0_Wilson_Vendor").Inspect()` in CET. If it says READY, run `GetMod("PTFR_B0_Wilson_Vendor").Start()`. If it refuses, send the printed reason; do not change any facts to bypass it.
3. Close CET, walk to the counter. Observe whether exactly one Wilson appears and the physical Shop choice works. Open the actual trade menu and buy or sell one inexpensive item on this disposable save. Close the menu normally. Run `GetMod("PTFR_B0_Wilson_Vendor").Mark("first-trade-closed")`.
4. Walk more than 84 m from the shop, allowing a few seconds for despawn. Run `GetMod("PTFR_B0_Wilson_Vendor").Mark("outside-after-first")`. Return to the counter. Verify one Wilson, Shop, and the trade menu again; run `GetMod("PTFR_B0_Wilson_Vendor").Mark("second-trade-closed")`.
5. Leave the 84 m area again. Run `GetMod("PTFR_B0_Wilson_Vendor").Stop()` and quit **without saving**. Tell me whether the seller, prompt, menu, item transaction, and second visit each worked.

If the initial interaction fails, stop after one attempt and quit without saving; the log will tell us which gate was reached. Do not teleport while the trade menu is open. No fresh ending playthrough or save modification is required for this first test.

The CET logger writes `wilson_vendor_<UTC>.jsonl` in its own mod directory and flushes every record. The native flags `SpawnActionOut` and `ActorDistanceGate` mean only that those native graph stages returned. They do **not** certify a visible actor or completed transaction. The tester's direct observation and trade menu are required for those results.

Installed at 2026-09-24 16:43:40 UTC. The installation receipt with exact file hashes is `research/b0_wilson_vendor/validation/install_receipt.json`. Static graph/archive checks and all three installed hashes passed. On first game load, CET reported `Mod PTFR_B0_Wilson_Vendor failed to load`; `GetMod(...)` was nil and no `Start()` ran. An out-of-sandbox Lua parser identified one extra `)` in the `Stop()` logger call at source line 135. The workspace copy was corrected, passed the full static test with Lua parsing enabled, and replaced only the installed `init.lua` after game exit; its new installed hash matches the updated receipt. No vendor runtime result has been observed. A later save/reload test depends on a clean two-visit result here.

2026-09-24 two-visit result: **physical seller, Shop prompt, and trade menu passed on both visits**; tester saw exactly one Wilson after returning. Durable log `wilson_vendor_20260924T170148Z.jsonl` records one opt-in Start, native near entry twice, `SpawnActionOut=1` and `ActorDistanceGate=1` twice, two departures with both gates returning to zero, then Stop with `Enabled=0` and process shutdown. The second visit used CET teleport back to the tester's earlier safe standing position after they encountered missing map stitching/fast travel near Misty's shop. No item transaction or save/reload result was explicitly confirmed, so this is a successful disposable two-visit interaction test, not final vendor permanence or economy validation.
