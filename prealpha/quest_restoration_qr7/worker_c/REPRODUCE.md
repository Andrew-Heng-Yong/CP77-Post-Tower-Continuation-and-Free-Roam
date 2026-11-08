# Worker C targeted checks

Run from the workspace root using Python `C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B`. Each output path must be fresh. Inputs are the pinned readbacks and current native files named inside the evidence. A changed input fails closed; do not edit pins to turn a stale proof green.

```powershell
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_c/verify_nitro_replay.py --output prealpha/quest_restoration_qr7/worker_c/replay_nitro_01
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_c/verify_native_journal.py --output prealpha/quest_restoration_qr7/worker_c/replay_journal_01
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_c/verify_remaining.py --output prealpha/quest_restoration_qr7/worker_c/replay_remaining_01
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_c/verify_remaining_controls.py --output prealpha/quest_restoration_qr7/worker_c/replay_controls_01
```

Expected outputs:

- Nitro:109 assertion events,80 selector fixtures with47 baseline divergences, three controls and a private JSON proposal. This reproduces the pre-repair source-authority proof. The coordinator's `check_nitro.py` separately verifies actual serialized QR7 successor bytes and0 post-repair discrepancies.
- Journal:23 assertions, two controls, five actual native equality-block fixtures, exact dispatch disassembly and retained saved-owner limits.
- Remaining:88 assertions, current direct stock/provider pins, exact source-null connections, native persistent-field metadata and detailed unresolved Voodoo/Cuckoo findings. Its five simple property controls are supplemented by the next command.
- Raw controls:four actual raw-resource copies are mutated before normalization; one actual current native field-flag byte array is mutated. All baseline properties pass and all five mutants are rejected. No mutated resource or cache is written to a candidate or game path.

For fresh native captures, use the reviewed helper scripts only within this worker tree:

```powershell
& prealpha/quest_restoration_qr7/worker_c/capture_startup.ps1 -Output startup_replay_01
& prealpha/quest_restoration_qr7/worker_c/capture_quest_providers.ps1 -Output quest_providers_replay_01
& prealpha/quest_restoration_qr7/worker_c/capture_stock.ps1 -Output stock_replay_01
& prealpha/quest_restoration_qr7/worker_c/export_targets.ps1 -Output resource_exports_replay_01
```

The captures expect WolvenKit9.1 at the explicit local path in each script and load `build_phase2a.ps1` only with `-HelpersOnly`. They write fresh evidence, never rebuild or deploy. The main startup capture should find four resources across134 current archive indexes; the quest-provider capture should find four more, all unique for these targets. Counts are pinned observations, not permanent expected counts to hardcode into future inventory discovery.

The original `read_scripts.py` and `trace_*` scripts are one-shot capture records with guarded output names; inspect them before adapting a successor. The analysis-only fixed-reader bytecode representation is not an engine-valid cache, compile result or deployment artifact. All209157 original definition payloads, known string pools and uninterpreted seventh-table bytes were preserved; unknown seventh-table semantics were not inferred.

No command here starts the game, reads personal saves, writes facts, deploys, packages or repairs gameplay. Source/body/live behavior remain separate results. `results_01/` contains the bounded eight-contract disposition, not a repeat of the161-quest audit.
