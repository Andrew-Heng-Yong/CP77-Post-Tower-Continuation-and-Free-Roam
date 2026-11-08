# Voodoo Treasure restored first-claim pass

**QR19 passed the ordinary first-claim route on the tested post-Tower branch.** The player opened the closed door after PTFR entered, took the money, shard and Rook, and reported Entered 1, Finished 1 and Fault 0. The earlier Rook-only opening was a separate attempt while the wrapper still waited. [Earlier attempt](NOV06_ROOK_ONLY.md)

At 11:58:51 AM on 6 November, VT01 recorded Permit 1, Issued 1, Entered 1, Finished 0 and Fault 0 while the exact door was attached, closed and enabled. The S23 inspector reported `currentMatch=true safe=true`. The test card designated AutoSave-14 as the closed-door start. The console excerpt confirms the relevant starting conditions and does not independently identify the loaded save body. [Console evidence](nov06_pass_console.json), [test card](../voodoo_entry_20261106_01/REPORT.md)

**AutoSave-19 at 12:00:19 PM corroborates the successful loot path partway through the claim.** It saves the keypad authorization and private Issued/Entered receipts. The Rook is in inventory 1, and exactly €$8,000 and the stash shard are still in the exact stash container. The door controller is open and Disabled. The keypad and stash-shell controllers are also Disabled, while the loot container remains enabled. The captured states support the native cleanup path on this loaded-door fixture, including the disable outcome despite the authored controller class difference. These are saved outcomes, rather than individual event acknowledgements. [Save pins](nov06_pass_pins.json), [saved states and loot](nov06_pass_readback.json)

The user's subsequent report establishes the completed live result. AutoSave-19 predates that result and has no serialized Finished receipt. Use a fresh manual save made after taking all three rewards and observing Finished 1 for the single persistence check. On reload, check that the rewards remain claimed and Finished stays 1.

The previously claimed, subsequently closed stash case still needs a separate genuine fixture. This pass requires no runtime patch or installation. The save and game files were read only.
