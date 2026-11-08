# QR7 evidence and reproducible checks

Start with completion.json, REPORT.md and HANDOFF.md. The staged candidate is QR7:04/candidate_01; installedPH3 is unchanged. Reusable scripts below read existing exact pinned inputs and write only fresh evidence directories. They require the current repository, existing ignored raw/native/worker exports, Python3.14, and for PowerShell captures WolvenKit9.1 at research/sidejobs_s28/tooling/wolvenkit_9_1_0/package. Helpers load tools/build_phase2a.ps1 only with -HelpersOnly. Run from the repository root; output directories must not exist. A mismatching pin fails closed: investigate a new provider/version rather than changing the old pins.

Use `C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B` for each Python command.

```powershell
# Actual serialized Nitro source/native gate;32checks/80fixtures/three raw-document mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/check_nitro.py --output prealpha/quest_restoration_qr7/reproduce/nitro_01
# Frozen CVI04 raw readback/native protocol;75checks/three document mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_a/verify_listener_v4.py --output prealpha/quest_restoration_qr7/worker_a/reproduce_listener_01
# Exact pinned native actor/community/marker binding;29checks/two typed controls.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_a/verify_actor_context.py --output prealpha/quest_restoration_qr7/worker_a/reproduce_actor_01
# Ronald raw buffer/native selected protocol;10checks/three packed controls;83checks/seven document mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_bar.py --out reproduce_bar_check_01
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_future.py --out reproduce_future_check_01
# Independent complete final archive extraction and51fileZIP validation;1738checks on current inputs.
pwsh -NoProfile -File prealpha/quest_restoration_qr7/worker_a/run_final_independent.ps1 -Epoch prealpha/quest_restoration_qr7/source_epoch_04.json -ApprovedChanges prealpha/quest_restoration_qr7/approved_changes_03.json -FinalManifest prealpha/quest_restoration_qr7/candidate_01/package_manifest.json -Output prealpha/quest_restoration_qr7/worker_a/reproduce_package_01
# Protected bytes and complete game/save metadata (read-only); expect zero discrepancies on unchanged inputs.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/verify_preservation.py --output prealpha/quest_restoration_qr7/reproduce/preservation_01
```

Expected output: each fresh directory contains a result/evidence JSON, individual assertions, exact pins and private mutation evidence where applicable. None of these commands deploys, rebuilds the candidate, changes game resources or runs the game. The CVI/Ronald proposal checks are tied to frozen source/readbacks; the final package verifier is the independent link to actual final payloads. Broad prior prerequisites and LIVE_ONLY limitations are not converted to PASS by these checks. See worker_c/REPRODUCE.md for four native-journal/remaining-input checks and exact native capture procedures. Shared registry entries identify producing scripts; script presence alone is not an executable procedure.

Historical one-shot recipes: initialize.py, prepare_nitro.py, patch_nitro.ps1, integrate_cvi.py, integrate_ronald.py, readback_* coordinator scripts, freeze_source.py, rebuild_candidate.ps1, package_candidate.py, publish_findings.py, publish_support.py and write_reports.py. They have fixed/pinned outputs and must not be blindly rerun. Prior worker experiments/prototypes are evidence, not installation instructions. Failed CSV publication/readback/prototype attempts remain preserved; authoritative later manifests supersede them explicitly.
