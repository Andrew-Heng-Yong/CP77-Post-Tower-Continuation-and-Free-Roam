# Reproduce the bounded QR8 Worker C checks

Run from `C:\Users\Ayong\Documents\cp77 modding\tower ws` in PowerShell. Use a fresh destination name on every run. Existing output trees are intentionally immutable.

Prerequisites: exact current game executable SHA D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4, exact current script cache B78043064AE90FB80861B0D885D1C8DBCD22070F1DB71F20664D19F2D83C4AAC, pinned QR7:04 baseline, local Python3.14 and Capstone/pefile under `research/finalboards_dismissal/tooling/python`, verified WolvenKit9.1 helper dependencies. No game launch is needed.

Replay all frozen input checks and native scalar controls:

```powershell
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/worker_c/verify_five.py --output prealpha/quest_restoration_qr8/worker_c/replay_01
```

Expected:457 assertion events,3 detected actual-byte mutants,5 updated contracts and5 UNKNOWN rows. `evidence.json` lists all limits. An executable/cache/source pin mismatch must fail rather than carry old RVAs or claims to a new input.

Fresh baseline preparation:

```powershell
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/worker_c/prepare.py --output prealpha/quest_restoration_qr8/worker_c/baseline_replay_01
```

Expected:5 original rows,8 pinned staged sources,8 selected new capture targets. Preparation reads exact epoch04/completion and native input hashes, and makes no baseline copy or package.

Optional current-provider recapture (read the script before invoking; fresh own output only):

```powershell
& prealpha/quest_restoration_qr8/worker_c/capture_resources.ps1 -Targets baseline_01/new_targets.json -Output capture_replay_01
& prealpha/quest_restoration_qr8/worker_c/capture_resources.ps1 -Targets exterior_targets_01.json -Output exterior_replay_01
```

Expected initial8 decoded unique targets; exterior3 extracted but OPAQUE with the same documented worldNode cast failure. Index metadata/order alone is not provider precedence proof; collisions must be adjudicated. Whole large archive SHA operations remain0.

Generic native tools accept exact types/RVAs from pinned evidence, not addresses assumed valid for another executable:

```powershell
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/worker_c/resolve_context_systems.py --output prealpha/quest_restoration_qr8/worker_c/context_replay_01
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/worker_c/trace_native_type.py --type gameContainerManager --output prealpha/quest_restoration_qr8/worker_c/container_replay_01
```

Expected context class globals identify gameITransactionSystem/gameIContainerManager/gameIPersistencySystem. The generic type capture identifies the concrete constructor/vtable; a capture alone is not a gameplay interpretation. See `capture_slots.py` for slot targets and `capture_native_functions.py` for bounded .pdata or leaf-thunk captures. Failed earlier capture/check attempts are retained rather than overwritten.
