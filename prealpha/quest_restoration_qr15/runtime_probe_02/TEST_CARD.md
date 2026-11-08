# JF02 — one read of the exact Jason Foreman car spawner

**Purpose:** distinguish JF01's unresolved short alias from the exact, freshly source-bound world reference. This is a lookup check, not a replay of the gig or a quest-start command. No diagnostic installation, capture start/stop, fact change or save change is needed.

1. Use your current working post-Tower playthrough, preferably the same loaded session as JF01. Open CET while a player is loaded. The exact JF01 save slot was not recorded; the separately inspected AutoSave-8 is not claimed to be that loaded body. Do not load a protected master solely for this check.
2. Copy the complete single line from `car.command.txt` into CET and press Enter once.
3. Send back the complete `[JF02]` line. Mention if you changed saves/reloaded since JF01; give the current slot if known. No need to run JF01, do a quest, start the sampler or save/reload for this check.

The command reports either `ABSOLUTE_CAR_UNRESOLVED`, `LOAD_SAVE_FIRST`, `WORLD_NOT_READY`, a visible `ERROR:...`, or `car initialized=... active=... spawned=... restored=... reserved=...`. A false value and an empty list remain distinct from an unresolved/error result. Stored entity-ID lists may overlap and are not a count of unique or living cars.

**Interpretation:** a resolved result establishes delivery of this exact getter query and a snapshot of its exposed fields. It does not establish the native VehicleSpawned predicate, completion of visual destruction or door setup, an executing owner, or released prefab leases. An unresolved result remains UNKNOWN; it does not prove an absent car. There is no gameplay PASS/FAIL criterion here.

CET prints are also logged automatically at:
`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\scripting.log`
The file may flush later; copying the whole output line is sufficient. This command creates no QR10 capture JSONL. Close CET afterward and continue normally; no cleanup/rollback is required.

## Offline readiness

`validation_01.json` records21 primary syntax/control-flow/source checks. `review_01/review.json` records23 independent checks and no blocking findings. These validate the proposed command, not native live delivery. The reference is bound to typed vanilla sector node98/globalID17433794865907239043 by the separate34-control car review. The command has one spawner lookup and three stored-array getters; arrays are materialized before Lua counts them, so no hard native allocation cap is claimed.

Reproducibility (workspace root): the exact command and fixture script are `prealpha/quest_restoration_qr15/runtime_probe_02/car.command.txt` and `validate.py`. The validation script refuses to overwrite its result; use a reviewed fresh evidence output for any rerun. No runtime binary/resource was compiled or installed.
