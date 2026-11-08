# GG1 readiness and handoff

General external read-only log capture is implemented and recording. No game installation, Core, diagnostic implementation, facts, saves or game controls were changed by this task. It uses existing CET/REDscript logs without a gig-specific filter. No CET command or game restart is needed.

Verification: run_02_results.json pins the current probe and tests; all 25 byte/safety/classification fixtures passed. real_control_01.json pins the real-file start/status/stop check: all four log sources were readable, clean USER_STOP, six protected Core/diagnostic/FactFinder hashes unchanged. That control recorded zero new bytes with the game closed and does not prove future game event delivery.

Active human capture: GG1_20261104T050208Z_7a4ab752, started 2026-11-04 05:02:08 UTC, 90-minute/64 MiB limit. readiness_01.json records the verified heartbeat and execution session18567. active.json selects its capture directory. Capture may end automatically at its limit; check current status rather than assuming it remains active.

Human next: choose one naturally available uncompleted gig on the existing working branch; note gig name, call/objective/reward behavior and any death/reload. Exit normally, then report done + gig name + issues. Preserve original master saves. Previously accepted tests remain closed. No further eligibility or CET commands are required.

Assistant continuation: run probe.py status; after human completion request probe.py stop if still recording. Wait for STOPPED and read the selected capture's summary.json, events.jsonl and stream files. Preserve these raw bytes. Correlate the human report to logged fact notices and source/attachment boundaries. No native callback, precise fact-write ordering, complete reward/owner proof or blanket gameplay PASS is provided by this recorder. Missing or capped FactFinder notices remain unknown.

See README.md for exact absolute commands, sources, controls and limitations. No deployment or rollback is necessary; stopping this workspace-only process disables capture. Existing installed diagnostics remain unchanged.
