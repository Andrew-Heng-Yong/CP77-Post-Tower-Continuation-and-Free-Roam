# User-requested Jinguji replay — 3 November 2026

**Earlier saves found and preserved; no installation is required.** The user explicitly requested an earlier-save replay after the previous no-repeat plan. Previous Bullets completion, Zane trading, post-quest dialogue and completed-state reload remain accepted. This run collects the encounter/cleanup with the corrected, already-validated getter sampler; it does not reset or replay completion on the current completed branch.

## Save and preflight

Use **AutoSave-18 — 2 November 2026, 16:20:12 / 4:20 PM**. It is an existing current Load Game slot, not a restored backup. Saved screenshot shows the player inside Jinguji facing a display table. It has `mq030_zane_met=4` and private Issued/Entered1; no selected saved positive native active/done/failed record or metadata completion. Absence is not runtime0. The archived QR9 run records met3→4 at16:19:20 and subsequent active0→1 at16:21:10. Actual body/metadata still match the QR12 reader inputs. These multiple facts and the recorded timeline corroborate the earlier post-Tower state; exact saved owner liveness and separate human lineage certification remain unobserved.

Do not use an ending/PONR save or the protected ManualSave-23. Keep current ManualSave-24. This is an earlier branch from before that branch's Bullets completion; no facts, journals, rewards or saved history are edited. Six exact original files were copied to `saved_inputs/` as evidence only, outside the game save directory, to preserve them if normal autosaves rotate. No copy was restored into the game.

All60 current installed manifest hashes matched: Core51, diagnostics and required dependencies remain unchanged. Existing installed S05 watches32facts and one native journal. No install/update/restart is required. No native callback or executing-owner proof is supplied by this logger.

Fixture qualification before progression: load the displayed save/date manually and check that it shows the expected unfinished Jinguji situation from the user's earlier post-Tower playthrough. If it is already complete, fails to load, shows unexpected history or is not that playthrough, stop and report; do not force activation. Saved metadata/receipts alone do not certify exact executing ownership. This is a conditional user-requested replay candidate, not a new blanket READY verdict on the nine original priority scenarios.

## Exact manual steps

1. If a capture is running, stop it before loading another save. The read-only fact commands did not start one. Through the normal Load Game menu, select **AutoSave-18, 2 Nov, 4:20 PM**. Do not overwrite either manual save.
2. After loading, confirm the expected unfinished Jinguji state. Before moving or speaking, open CET and run:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("S05", "QR12-Jinguji-Replay", 900)
   ```

   Require `[PTFR QR10] Recording: QR10_capture_...jsonl`. An error/NOT_RUNNING/unknown profile is a stop condition. If it says Already recording, stop that capture and start this one before progressing. Starting after load does not capture restoration before the command.
3. Close CET and continue **Bullets** normally: leave/return to Jinguji naturally if needed for the earlier met/away condition; handle the attack, MaxTac and the normal conversations/objectives. Do not use fact setters, forced starts, device commands, teleports or reward/item grants. If the ordinary route does not activate, report the visible state; no repeated forced attempts.
4. When Bullets is shown completed, wait **six seconds** in normal unpaused gameplay, then stop:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop("QR12_JINGUJI_DONE")
   ```

   Require `Stopped: QR10_capture_...jsonl`. Capture automatically stops after15minutes; report an auto-stop rather than treating later events as recorded. For an unexpected stuck quest, duplicate actor/reward or wrong state, stop then report instead of advancing to repair it.
5. No additional shop test, completed-state reload or manual save is requested. You may return to the current working save afterward **only after capture is stopped**. Keep ManualSave-23 and24 intact. Close the game normally when convenient so the logs are flushed.
6. Reply with **actual slot/date; activated yes/no; completed yes/no; normal MaxTac/dialogue yes/no; capture stopped/auto-stopped; anything unexpected**. A simple “done, AutoSave-18, normal, stopped” is sufficient if everything behaved normally. The assistant can collect the local logs; no dozens of fact values or manual file copying is needed.

Logs are automatically written under:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR10_capture_*.jsonl`

Expected logging: S05 CAPTURE_START and attached baseline, explicit native-callback-unavailable declaration, two-second sampled changes among relevant native progress/MaxTac/done/active and private/shared-vendor markers, native journal observations, clean STOP/CAPTURE_CLEANUP. Not every watched fact must change. Saved identity, actual native/private owner retirement and exact write ordering remain unobserved. Short/reverted changes may be missed.

Behavior PASS requires the reported normal encounter/completion; sampled logging PASS is assessed independently from coherent observations and absence of errors. Missing samples alone are INCONCLUSIVE, not a failed quest. Wrong/incompatible save is NOT_TESTABLE. No new result is recorded as PASS before the user's run.

## Reserved later candidate

**AutoSave-3 — 2 Nov, 16:33:46 /4:33PM**, debug `mq030_cyberpsycho_defeated`, is separately preserved. Saved active1, MaxTac-arrived1 and grateful1 with no positive done record make it a late pending-completion candidate. Its screenshot shows Melissa in Jinguji. This may support a separate pending-stage resume investigation, but exact owner/stage and immediate post-load behavior are not proved. Do not perform an additional test from this slot yet; a main-menu-armed capture may be needed to observe load-time transitions.
