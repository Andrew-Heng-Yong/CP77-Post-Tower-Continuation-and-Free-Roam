# MS31 build and installation checks

The build lane targets checkpoint v0.1.8. It checks the precise v0.1.7 predecessor, including 51 Tower paths, the checkpoint DLL and 26 external dependencies. It also validates the executable, address table, RED4ext loader and untouched MS31 save body. The staged write set consists of the checkpoint DLL. [Installed predecessor](../universal_resume_save_session_20261115_01/deployment_01/installed_manifest_01.json)

The build driver compiled the pinned v0.1.7 source to exercise the actual compiler and output paths. The x64 PE and three RED4ext exports passed readback. All 87 checkpoint, registration and save-admission regressions passed. An integration build runs these same regressions against the new runtime source and records its exact dependencies. It binds workspace headers to the installed compile inventory or the new integration fixture assessment. A compile-only result was correctly refused before staging. [Build driver](build_live.py) · [Driver fixture](fixture_03/assessment.json)

All 17 transaction actions passed on eight synthetic trees. They cover clean rollback, interruption before and after DLL replacement, exception recovery, running-game refusal, and drift in the installed DLL, staged DLL or MS31. The synthetic fixture paths are isolated from the live game and saves. [Fixture receipts](fixture_01/fixture_results.json) · [Staging driver](stage_live.py)

The package provider check found the expected seven resource hashes across the current 137 archives. Staging refreshes this scan and binds it to the exact installer manifest. [Provider readback](provider_01/provider_result.json)

## Staged candidate

Build 06 compiled the exact runtime and passed 87 checkpoint regressions. Its integration proof records 20 handoff checks, 17 quest-job checks and 21 world-support checks. Stage 01 verified the DLL package, refreshed the seven-resource provider scan and passed all 17 transaction actions. The closed-game preflight returned `PREFLIGHT_READY` with 52 managed files, one replacement, 26 dependencies and a 403-file save snapshot. The candidate is staged for authorized installation. [Build 06](run_06/assessment.json) · [Stage manifest](staged_01/core_manifest_01.json) · [Preflight](staged_01/preflight_01.json)

## Prepare the exact candidate

Use the production `NativeCheckpoint.cpp` path from the integration workspace and the fixture assessment for that exact source. Each command writes to a fresh attempt directory.

```powershell
& $python -B prealpha/universal_resume_live_candidate_20261115_01/build_live.py --attempt 1 --source-sha $sourceSha --proof $integrationProof --proof-sha $integrationProofSha
& $python -B prealpha/universal_resume_live_candidate_20261115_01/stage_live.py --attempt 1 --build $buildAssessment --build-sha $buildAssessmentSha
```

The staging driver checks the compiled DLL and proof bytes, exercises the transaction against its own synthetic roots and writes `readiness.json` for the exact installer and manifest. Run the staged installer’s `Preflight` for closed-game and preservation readback. Actual `Install` requires the user's authorization for that candidate. Follow with `Verify` and `ValidateRollback` against the same staged installer. The game test starts after those checks. [MS31 test card](TEST_CARD.md)

## Record a verified installation

Keep the authorization record and full `-ReportFile` JSON from each transaction action in stage 01. The recorder binds all four to the committed recovery journal, rechecks every managed and required file, and reads back the preserved saves and unmanaged metadata. Its default output is `staged_01/deployment_01/installed_manifest_01.json`. The complete recorder passed against a fresh isolated install, verification and rollback-ready receipt. [Recorder](record_install.py) · [Recorder fixture](fixture_04/installed_manifest_01.json)

```powershell
& $python -B prealpha/universal_resume_live_candidate_20261115_01/record_install.py --authorization $authorization --install $installedReport --verify $verificationReport --rollback-ready $rollbackReport
```
