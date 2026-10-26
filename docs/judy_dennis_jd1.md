# Judy private door and Dennis holocalls — JD1

Installed 25 October 2026 with explicit user approval. Gameplay testing remains pending.

The existing housing rule removed Judy's home services but did not lock the private
apartment door. JD1 binds only that upstairs entrance, closes and locks it when V
is outside, and releases its own lock for exit when a retained save loads indoors.
It does not change the street doors, bedroom doors, relationship history, stash
contents, or purchase rules. The exact door reference and interior anchor match
the installed native world data. Unknown geometry defers locking. Native visual
movement synchronizes a saved open state before updating to avoid a recursive
visual/persistent-state mismatch.

Big in Japan retained its original calls, but S23 omitted Dennis's phone controller
and all installed PTFR cleanup versions omitted his cleanup branch. The user's log
records `holo_dennis_calls_v_start_activate=1` without a subsequent call start.
JD1 starts the original Dennis controller once for an admitted fresh or existing
PTFR-owned unfinished MQ038. Fresh quest entry waits for its receipt. Existing
progress is not restarted, and queued calls are not cleared. Existing MQ038 may
hold interruption flags until its own call completes, so those flags cannot block
restoring the missing listener. Native setup/reset guards remain. Cleanup uses the
original condition and phase, gated on JD1's controller receipt.

Four installed files: one HousingPurchase tick-line replacement; one added
JudyDoorJD1 script; one added archive and XL. The archive contains one new phone
bootstrap and overrides only two existing PTFR resources: MQ038's dependency wait
and the current shared phone cleanup. Original quest nodes, rewards, actors,
progress, and other contact cleanup payloads remain intact.

Validation: full 94-source compilation including EquipmentEX; compiled class and
saved-field preservation checks; native graph comparison and admission cases;
packed readback/load-order/injection collision checks; 14 installer fixture
actions. Install, Verify, and ValidateRollback passed. All 721 protected files,
including 289 save files, were unchanged. No assistant game launch or manual
quest-fact writes. The earlier English lipsync candidate remains uninstalled.

Final evidence: `prealpha/judy_dennis_jd1/candidate_01/assessment_01.json`.
Final sources/proofs are pinned; use successors. Native build `native_02`, tests
`tests_02.json`, script compile `compile_04`. Earlier native admission and script
compilation candidates are historical and were never installed.

## Live checks

1. Cold launch and approach Judy's upstairs apartment door from outside; verify
   it stays closed and locked. Check a retained indoor fixture can exit, then
   verify the door locks after V leaves the threshold. Test a new save/reload.
2. Load an unfinished Big in Japan fixture. Check the next native Dennis call
   appears, speaks, and ends normally; test interruption and save/reload. Use a
   retained earlier fixture to retest a call already passed. Do not reset MQ038.
3. Check another restored contact still calls and ends normally.

Read-only CET status:

```lua
local q = Game.GetQuestsSystem(); for _, f in ipairs({"PTFRJD1_Dennis_Ready", "PTFRJD1_Dennis_Issued", "PTFRS23_MQ038_Issued", "PTFRS23_MQ038_Entered", "holo_dennis_calls_v_start_activate", "holo_dennis_calls_v_start_count", "holo_dennis_calls_v_end_count"}) do print(f .. "=" .. tostring(q:GetFactStr(f))) end
```

## Rollback

Close the game. Run `prealpha/judy_dennis_jd1/deploy_01.ps1` with
`-Action ValidateRollback`, then `-Action Rollback`. Backup:
`recovery/judy_dennis_jd1_01`. Roll back JD1 before S29, S23, or H5 purchase files.
File rollback does not undo saved door state or remove a newly saved native
phone owner; retain the pre-JD1 save for reverting the feature itself.
