# Stock hands after the Tower handoff

## Reported run

On 11 November 2026 at 23:58:56 Toronto time, the installed profile repair unequipped `Items.AdvancedNanoWiresElectricLegendary` and verified conservation of the item and all three attached parts. Arms and Hands treatment completed at 23:58:57. The game logged the remaining profile refunds and the day-zero Health and Stamina readback at 23:59:26. The setup cover reached Ready at 23:59:32. The user reported that V's hands were invisible in the retained session and visible after a save and reload.

The read-only comparison found the Monowire and its holstered proxy in `EndGameSave-70` and the stock fists and their stock holstered proxy in `AutoSave-0`, with both Arms and Hands equipment slots empty in the latter. The matching stock TweakDB maps the fists' `holsteredItem` to `89036944176` and the Monowire's to `122871210708`. The save comparison identifies the logical equipment state. The initial live attachment and rendered mesh were unobserved.

## Repair

The matching native equipment code handles the holstered model through `AttachmentSlots.RightArm`. `UpdateArmSlot` normally leaves a matching attachment in place. The reported Monowire's stock `usesVariants` flat is true, and the native unequip path places its bare-fists fallback in the alternative to variant stat removal. This makes the in-session hand attachment a repair target even when the saved equipment slots are correct.

On the first Arms and Hands treatment receipt, the repair schedules a transient refresh for the same player. It waits for the final native arrival acknowledgement, normal player control, settled arm customization and the existing safe gameplay checks. It uses the native fist and holstered-slot helpers when equipment needs repair. For a matching owned stock model, it rebuilds the live attachment through the native slot API and checks the resulting attachment on a subsequent tick. It allows up to four safe checks. The cover and refund ledger keep their existing completion checks.

## Verification

The patch changes `PTFR_RestrictionsR1.reds`. Source comparison verified the completion gates, initial unequip and item-conservation code, refund admission, and persistent fields. All 148 registered scripts compiled against the current stock cache. Nine transaction fixture actions covered install and verification, rollback, interrupted-write recovery and the running-game guard. The first two preflights stopped before any writes when game startup refreshed or locked the REDscript timestamp. The third attempt compiled the same patch against the refreshed cache and passed preflight. The closed-game guard deferred installation until the game exited. [Source patch](candidate_01/source.patch) · [Compile result](compile_01/result.json) · [Transaction fixtures](fixture_results.json)

The 12 November install and independent readback verified all 51 Core paths and 26 dependencies. The transaction changed one script and verified all 343 save files against their pre-install names and hashes. The verified predecessor copy is in `recovery/core_tower_hand_appearance_01/`. [Installed manifest](deployment_01/installed_manifest_01.json) · [Installed readback](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

Visible hands on the first return to gameplay still need confirmation on a genuine Tower handoff. Attachment readback records the engine slot state.
