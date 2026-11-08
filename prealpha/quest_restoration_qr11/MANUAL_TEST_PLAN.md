# PTFR QR11 — manual test plan

**Readiness: PREFLIGHT_READY. Nothing has been installed by Codex.** The two-file QR10D01 update passed normal-install, interruption, recovery and rollback fixtures. You must separately approve deployment or choose to run the installation command yourself. Do not launch the game until installation and verification succeed.

This session contains **one short test: D00**. It checks whether the new logger detects an ordinary phone-state change. It does not retest quests. You operate the game and CET throughout.

## Before launching

Use **ManualSave-24**, metadata dated **2 November 2026, 16:37:02 / 4:37 PM**, **level51**. The file is:

`C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-24\sav.dat`

This existing working save records completed Bullets and matches the confirmed Tower master's playthrough ID. Its exact files and metadata were checked in QR11. Do not choose **Continue**, an ending/PONR slot, or the protected **ManualSave-23 — 29 October,7:23 PM**. If the Load Game list cannot uniquely identify the2November4:37PM manual save, stop and report that; do not guess. Metadata alone is not independent proof of Tower completion; the existing confirmed lineage is reused.

Close Cyberpunk2077 and the RED launcher normally. Use PowerShell; an Administrator window may be needed for Program Files write permissions. The verified PowerShell7 executable is specified below, so PowerShell5 can also invoke these commands. Keep this window open for the final collection command.

```powershell
Set-Location -LiteralPath 'C:\Users\Ayong\Documents\cp77 modding\tower ws'
$ps7 = 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$installer = 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\deploy_diagnostics.ps1'
$py = 'C:\Users\Ayong\.local\bin\python3.14.exe'
& $ps7 -NoProfile -File $installer -Action Preflight
```

Require **`PREFLIGHT_READY`** and exit code0. A hash/state/refusal is a stop condition; do not bypass it or delete recovery data. The preflight checks the actual B04 files, exact D01 source,51Core files,6 dependencies, game EXE, original master, selected working save, pinned manifests and source proofs. It reads current saves for transaction preservation.

**Only after you authorize or elect to perform deployment**, run:

```powershell
& $ps7 -NoProfile -File $installer -Action Install
if ($LASTEXITCODE -ne 0) { throw 'Installation stopped. Do not launch the game; preserve the error and recovery folder.' }
& $ps7 -NoProfile -File $installer -Action Verify
if ($LASTEXITCODE -ne 0) { throw 'Verification failed. Do not launch the game.' }
& $ps7 -NoProfile -File $installer -Action ValidateRollback
if ($LASTEXITCODE -ne 0) { throw 'Rollback readiness failed. Do not launch the game.' }
```

Require **`INSTALLED_VERIFIED`**, **`VERIFIED_AFTER`**, then **`ROLLBACK_READY`**. These are file/backup checks, not gameplay results. The installer replaces only these existing files:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\init.lua`

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\watch.json`

Expected version is **QR10D01 candidate_02**. Verified rollback copies and the journal are retained under:

`C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\recovery\diagnostics_qr10d01_01\`

A fresh game launch is required after the closed-game installation. Do not use CET “Reload all mods.” Do not edit facts, saves, journals, Core files, other mods, configuration or log files. Never overwrite ManualSave-23. This is not permission to replay completed quests.

## D00 — start, call, stop

Allow about **one minute** of gameplay; the logger has a120-second cap.

1. Launch Cyberpunk2077 normally from your usual Steam/launcher shortcut. Open **Load Game** and select the verified **ManualSave-24,2Nov4:37PM,level51** working save.
2. Wait for normal player control. Be out of combat, dialogue and any incoming call. Open the phone with **T** (hold it to open contacts) and select **Regina Jones**. Check whether her ordinary **Call** option is already available. **No Call option → D00 NOT_TESTABLE.** Do not force a call, change history, choose another quest or wait days to create eligibility. Close the game normally and report that result; no capture is required in that case.
3. If Call is available, close the phone. Press **`\` — backslash** to open CET, and select its **Console** tab. The configured CET binding is VK0xDC, mapped to backslash on the current keyboard layout. It is not the tilde key. If you have since changed the binding/layout, use your existing CET overlay key; do not reset configuration for this test.
4. Enter this single start command:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").start("D00", "QR11-D00-Regina", 120)
   ```

   Require **`[PTFR QR10] Recording: QR10_capture_...jsonl`**. `QR9` in the module name is intentional; its installed name is stable. `Armed` is not yet recording on the loaded player; `NOT_RUNNING`, an unknown D00 profile, or an error means stop the test and report the text. If uncertain, this supported optional status check must say `RECORDING`:

   ```lua
   print(GetMod("PTFR_QR9_Diagnostics").status().state)
   ```

5. Close CET with **`\`**. Remain in normal gameplay for about **four seconds**. Open the phone with **T** and place **one ordinary call to Regina**. Do not choose a new job or quest-starting conversation option.
6. Observe whether it rings, connects, has voice, receives no answer or stalls. Allow at least **six seconds** of ringing/conversation when possible. Let the call end normally, or choose the normal Goodbye when offered. Do not force it with a console command. An unanswered call alone is not a restoration defect.
7. After the call ends, remain in normal gameplay for another **six seconds**. Do not pause in menus for that settling window. Reopen CET and enter:

   ```lua
   GetMod("PTFR_QR9_Diagnostics").stop("D00_DONE")
   ```

   Expect **`[PTFR QR10] Stopped: QR10_capture_...jsonl`**. Keep that filename. If capture already stopped at120seconds or on a session change, report that; do not replay a completed quest or immediately repeat the test to hide it.
8. Close the game and RED launcher normally. **No manual save or reload is needed.** Do not overwrite either manual slot. Normal gameplay may create autosaves; do not delete or restore them.
9. In the same PowerShell window, collect the evidence automatically:

   ```powershell
   & $py -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\collect_d00.py'
   ```

   It selects the newest matching D00 capture, preserves a fresh copy/hash, checks its structure, records current installed hashes, copies bounded CET log tails and metadata, and prints the new evidence-folder path. It never launches the game or changes game/save files. No manual fact list is needed. If collection fails, preserve the printed error and original capture; do not clean up logs.

## Expected observations and decision

In-game: one ordinary attempted Regina call, followed by return to normal phone/player control. No quest completion, reward, reset or journal transition is required or requested.

The logger reads one watched fact approximately every **two seconds of observed updates**: `phonecall_player_with_regina_jones`. It can miss changes that occur and revert between reads. These are **sampled value changes**, never native callbacks, exact write timestamps or precise native event order.

| Log record | Expected meaning |
| --- | --- |
| CAPTURE_START, ATTACHED_BASELINE | QR10D01/D00 and the initial fact value. Initial value is not a transition. |
| NATIVE_CALLBACK_UNAVAILABLE | Expected capability declaration. Native callbacks are not provided by this Lua probe. |
| FACT_SAMPLING_STARTED | Two-second interval and bounded capture. |
| FACT_SAMPLE_CHANGE | Previous/current sampled value for the phone fact. At least one is needed for a positive sampling result; no numeric phone-state enum is guessed. |
| BOUNDED_STATE_CHANGE | Global `phone_active` may change. It may miss short states and does not identify a controller. |
| STOP, CAPTURE_CLEANUP | Capture closed; no native quest subscriptions were created. |

D00 watches no journal entry. A journal change is not a required success signal.

| Result | Rule |
| --- | --- |
| **PASS — sampled observation only** | You placed the natural call; exact installation verified; valid complete capture contains a coherent phone-fact sampled difference with no getter/log errors. Your observation and logs agree. No-answer can still provide valid sampler evidence. This never proves native callbacks or general quest restoration. |
| **FAIL — diagnostic** | Start/log/getter error, wrong observer version, malformed/inconsistent capture or failed installation verification. Preserve evidence. This is not automatically a gameplay defect. |
| **Behavior anomaly** | Unexpected quest/reward replay, duplicate call or phone remaining stuck after the normal call. Stop and report; do not repair it with facts. Cause requires analysis. |
| **INCONCLUSIVE** | Call attempted but no sampled difference, capture missed the window, premature stop, installation drift, or insufficient correlation. Do not infer a failed call from absent samples. |
| **NOT_TESTABLE** | Regina's genuine Call option is unavailable, or the verified working save cannot be identified. No forced substitute. |

The collector deliberately reports a provisional sampled-evidence status, not an automatic gameplay PASS. Codex will classify the result using your short observation below.

## Where the logs are and what to return

Original log directory:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\`

Original filenames: **`QR10_capture_*.jsonl`**. Collected evidence:

`C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\evidence\D00_<UTC timestamp>_<suffix>\`

Return the printed evidence-folder path or capture filename plus this one line, filling in the choices:

> D00 | ManualSave-24,2Nov16:37 | Call available yes/no | rang/answered/no answer/stalled | recording started/stopped/auto-stopped | unexpected behavior none/details

The workspace is shared, so you do not need to upload dozens of files or transcribe facts. If Call was unavailable, just report **D00 NOT_TESTABLE — no Regina Call option**. Screenshot only an unexpected error or UI anomaly.

No cleanup or rollback is normally needed. A stopped logger is idle; retain all logs. If rollback becomes necessary, close the game first and use the exact reviewed procedure in `DEPLOYMENT_AND_ROLLBACK.md`; it restores only B04 diagnostic files, never Core or saves.

## After D00: remaining priority list

**No additional quest test currently has a qualified genuine fixture.** Do not start another quest test in this session. The following are NOT_TESTABLE on current evidence; these are missing prerequisites, not instructions to manufacture them.

| Priority | Future test | Exact missing prerequisite |
| --- | --- | --- |
|1 | CVI02 specialized Hands calls | Separate genuine fresh, unadmitted CVI02 history with earned prerequisites and no old pending owner/request. CVI02 is completed on the selected history. |
|2 | Ronald future news/timer | Genuine existing subscription + Active contact and exact eligible future gig/owner stage. Earlier snapshot had Inactive contact/messages_enabled0. Saints/Spy are completed; first enrollment/old clocks remain held. |
|3 | Skippy return | Genuine supported pre1101 return/handoff stage and earned Regina history. Kill totals and owner_known0 do not prove that stage; old11/51/95 seams are unsupported. |
|4 | Brendan containment/progression | Verified unearned pre-Tower history for containment, or a separate earned/progressed descendant. Post-ending all-Inactive/zero history does not prove either. |
|5 | Pending-owner interruption/reload/reward | Separate genuinely supported pending stage with normal saving permitted and actual before/after reward evidence. Completed-state reload successes are already accepted. |
|6 | Nitro | Fresh unissued fixture with an already earned allowed Kusanagi and at least3native purchases; selected history is already-issued with purchase counter1 and guarded unlocksfalse. Existing selector liveness is also unproven. |

Do not repeat Bullets completion/reload, Zane shop recovery, Wilson invitation/completion/reload or confirmed Cynthia delivery. No current additional tests can be grouped without inventing eligibility.
