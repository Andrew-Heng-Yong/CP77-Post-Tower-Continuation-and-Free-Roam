# GG1 — general gig log capture

External, read-only capture of the existing CET/game/REDscript logs. It adds no game polling, installs no mod, makes no CET/game API calls and never starts quests or changes facts, saves, settings or third-party mods. The current QR13 Core and validated QR10D01/D00E sampler remain installed unchanged.

The user may choose any naturally available, uncompleted gig without supplying its ID. Source logs are copied without quest filtering; the final summary suggests matching catalogue titles from logged fact names. A suggested title is not proof of quest completion. Uncatalogued gigs remain in the raw evidence.

## Human steps

When Codex confirms **RECORDING**, launch/load normally if necessary and do one naturally available gig. Note its name, whether calls/objectives/completion/reward behaved normally, and any death/reload or problem. Exit the game normally afterward so its own buffers flush, then report **done + gig name + problems, if any**. No CET start/stop or eligibility command is needed.

Do not use a developer Start command, replay a completed/failed job or reset facts to create a test. Preserve original ManualSave-23 and24; use the working branch. Do not repeat already accepted Ronald enrollment/reload, Bullets/Jinguji, Wilson, Zane, Cynthia or D00E tests.

Default capture limit:90 minutes or64MiB of new source bytes. A hard limit produces a visible stop reason; it is not a gameplay failure. No game is automatically closed or launched. Ordinary deaths/reloads are allowed and must be reported; possible log/source/loading boundaries remain explicit rather than claiming uninterrupted owner observation.

## Exact operator commands

Working directory: `C:\Users\Ayong\Documents\cp77 modding\tower ws`.

Start a fresh bounded capture (long-running command; do not wait for completion before human play):

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\general_gig_probe_gg1\probe.py' record --seconds 5400
```

Require JSON status **RECORDING**, then independently check heartbeat:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\general_gig_probe_gg1\probe.py' status
```

Stop after the human exits normally/reports done:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\general_gig_probe_gg1\probe.py' stop
```

Expected first **STOP_REQUESTED**, then within a few seconds **STOPPED** on `status`. Only an owned workspace request file is created; no process is killed. A lock excludes a second recorder. If the heartbeat is stale and no summary exists, preserve that interrupted capture rather than assuming success or deleting evidence.

## Outputs and limits

`active.json` selects the current capture beneath `captures/GG1_.../`. Each capture stores:

- `identity.json`: run/input/catalogue identity and bounded limits.
- `context/`: bounded bytes that predate the new-source cursors, explicitly separate from gameplay capture.
- `stream/`: exact appended source bytes, retained without filtering.
- `events.jsonl`: source availability/rotation/truncation and stop information.
- `status.json`: current heartbeat; `summary.json`: final evidence, hashes, likely gig fact prefixes, gaps, errors and limitations.

Sources: CET `gamelog.log`, `scripting.log`, `cyber_engine_tweaks.log`, and `r6/logs/redscript_rCURRENT.log`. Missing or linked sources are reported/refused, never followed outside the intended read root. Source files are briefly opened `rb`; output writes are confined to this workspace. Known core/sampler/FactFinder source hashes are checked without changing them. A renamed old log's unread suffix is recovered only by matching file identity within that same directory; an unrecoverable rewrite/truncation gap stays visible.

This is a capture around **existing** instrumentation. FactFinder supplies batched getter differences, with a source-default limit of3reports per fact per game session; the user's current setting is not assumed or altered. Transient, suppressed, unlisted or unflushed notices can be missed. This is not a native-callback recorder, journal-state census, exact write-order trace, executing-owner/timer decoder, inventory/reward auditor or automatic gameplay PASS. Human observations and source investigation remain necessary to interpret a gig. Error-like lines are candidates, not automatic failures.

## Verification and recovery

`test_probe.py --run <fresh_name>` exercises workspace byte fixtures only. It checks exact append/no duplication, context separation, truncation/same-size rewrite, rename recovery, missing/appearing files, split UTF8, byte limits, source/output symlinks, escaping paths, unknown control preservation, OS lock contention and summary classification. Run results pin the exact probe/test bytes. A separate short real read-only capture verifies actual source access/control lifecycle.

There is no deployment or game rollback. Stop the recorder to disable capture. Keep its output for analysis; do not remove or change the existing game logger, Core, saves or prior observations.
