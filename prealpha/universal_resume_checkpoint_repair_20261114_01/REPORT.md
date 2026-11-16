# Execution checkpoint startup recovery — 14 November 2026

## Observation

The 15:45 Toronto startup completed RED4ext initialization and exited normally after a game session. RED4ext warned that Immersive First Person 0.2.0 requests runtime `3.0.80.51928` while the installed game is `3.0.88.46235`; that warning was already present in the successful startup. Its CET script had run in the preceding session with the native height component unavailable.

The 19:45 startup, after the execution checkpoint installation, compiled REDscript but failed validation on `PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint` and `DecodeExecutionCheckpoint`. RED4ext loaded `PTFR_ExecutionCheckpoint.dll`, but its own log said `PTFR execution checkpoint capture types unavailable`. The failure is in the checkpoint's native function registration, not a proven Immersive First Person startup failure. The C++ registrar chains seven `AddParam` calls and `SetReturnType`, so the present log does not identify which type lookup failed.

Source logs: game `red4ext/logs/red4ext-2026-11-14-15-45-08.log`, `red4ext/logs/red4ext-2026-11-14-19-45-45.log`, and `red4ext/logs/ptfr_executioncheckpoint-2026-11-14-19-45-49.log`.

## Recovery

The game's and launcher's processes were absent. The installed DLL hash matched the pinned manifest (`FB05DDE45E39BF83DFE3A94846675C4DC1BF8E06F1B214904180516FD8379860`). The guarded Core `ValidateRollback` returned `ROLLBACK_READY` against manifest SHA256 `6C0BE1797CE0A165677CF3353E273FD05E8FB24386A1FEF2BBBCCCDB59EAD83B`.

At the user's request to fix the checkpoint, the guarded `Rollback` restored the two predecessor history files and removed the private checkpoint DLL. It returned `ROLLED_BACK_VERIFIED`. A separate `Verify -ExpectedState Before` returned `VERIFIED_BEFORE` for 52 managed paths and 26 dependencies. The transaction made zero save writes and did not launch the game. Current saves and unrelated mods were protected by the script's before/after snapshots. The previous RD10 archive and cutoff gates remain installed.

## Startup result and remaining work

The user confirmed the game starts again. The 19:53 Toronto `red4ext-2026-11-14-19-53-03.log` shows normal plugin initialization, no script validation error, and normal shutdown after a game session. Immersive First Person still produces its patch compatibility warning; it did not stop this launch.

A logging-only RTTI diagnostic DLL was built in `probe_build_02` (SHA256 `1ED02F838004645C46F1E69733D80D1779416A6766BD6E8E2EB5E1F9CA9C51C4`). Its one-path install, verify and rollback fixture passed, and real preflight returned `PREFLIGHT_READY`. It has **not** been installed. Automatic approval review rejected the live DLL installation because the user's earlier authorization to fix the checkpoint did not specifically authorize this diagnostic addition. The user declined the explicit diagnostic install and asked to keep the game as it is. The installed game remains on the working RD10 predecessor.

The execution checkpoint still needs the exact failed RTTI lookup identified before a corrected successor can be built. The original candidate, manifest, receipt and recovery bytes remain preserved.
