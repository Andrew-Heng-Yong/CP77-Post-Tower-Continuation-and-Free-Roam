# QR10 manual capture

**Preparation only. QR10D01 is not installed.** Do not run this against QR9B04. Any later installation needs separate authorization and the diagnostics-only preflight. Codex does not operate the game or CET.

## D00 — one ordinary natural phone event

Purpose: validate the new getter-difference sampler economically. This does **not** test CVI, restore a quest or prove native callbacks work.

Prerequisites: exact QR10D01 candidate_02 installed and verified; normal user working branch of genuine Tower lineage; Core unchanged. In the ordinary phone UI, Regina Jones must already offer **Call**. If she does not, skip D00 and report that prerequisite; do not reset history or substitute a quest test. Current callability cannot be established offline. No master overwrite is requested.

1. On the loaded working branch, check that existing Call option, then close the phone. In CET, run:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("D00", "QR10-natural-Regina", 120)
   ```

   Expect `Recording: QR10_capture_...jsonl`. If it says NOT_RUNNING or the installed module lacks D00, stop; do not use the old observer as the successor.

2. Close CET. Use the normal phone UI to make **one** ordinary Regina call. Allow at least six seconds of ringing/conversation when possible. Let it end normally; choose no quest-starting dialogue. Wait about six seconds afterward.

3. Run:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop("D00_DONE")
   ```

   Quit normally before collection. Return the log filename, whether the call was available/rang/answered, and the working save label. No repeat Wilson, Bullets, Zane or completed-state reload test is requested.

Expected log: explicit callback-unavailable row, attached baseline, one or more `FACT_SAMPLE_CHANGE` rows for `phonecall_player_with_regina_jones` if the native state remains different across a sampling boundary, STOP and CAPTURE_CLEANUP. No numeric phone-state enum is guessed. A very short/reverted state can be missed. Zero sampled changes is **INCONCLUSIVE**, requiring correlation with broad logs/phone behavior; it is not a failed quest or proof of a broken getter. Even positive sampled changes never certify native callback delivery.

Fact naming is grounded in the native `contacts/regina_jones` binding, `MessengerUtils.contactId`, the current-style phone UI call path and `PhoneSystem.GetPhoneCallFactName`. Those historical source inputs are pinned in [provenance](provenance.json); exact current compiled phone behavior is still a natural-test boundary.

## Other capture profiles

Existing S00–S08 watch catalogues are preserved. After a **qualified** future card, use the relevant profile with a bounded duration, for example `start("S02", "actual-stage-label", 900)`, then `stop("USER_STOP")`. Maximum900 wall seconds,2048rows,8MiB,450 sample passes and96facts. Default300 seconds. Long native waits use separate short captures near events, not a continuous multi-day trace. Start after load where possible; stop before deliberate load and manually start a new segment afterward. Automatic resume is absent.

Logs stay under the stable installed diagnostics directory:
`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR10_capture_*.jsonl`.

This JSONL is schema2. Old QR9 schema1 collection/analysis results must not be used to certify it. A future collector should read bounded bytes, preserve a fresh copy/hash, verify schema/module/version/sequence/STOP, then separate sampled transitions, annotations, state getters and unavailable capabilities. `declared_build` is metadata, not an executed-byte measurement; use the separate installation verification.

## Quest queue

[runtime_queue.json](runtime_queue.json) reuses the exact QR9 acceptance cards and records current missing prerequisites. **No new quest card is qualified now.** CVI/Nitro lack fresh fixtures; Ronald lacks subscription/stage proof; Skippy lacks exact supported pre1101 proof; Brendan lacks earned/unearned history proof; pending-owner and reward alternatives need a genuine independent supported stage. Do not spend gameplay time on these blocked tests or replay completed fixtures.
