# QR9B04 read-only CET diagnostic — prepared, not deployed

The optional addon is exactly the two files in `addon_manifest_04.json`. It is
separate from QR8's unchanged51-path core. Install/rollback belong to Worker A's
guarded transaction after explicit authorization. The dependency is the existing
exact CET ASI; no new REDscript, native plugin, archive or compiler run is needed.
Expected QR8 hashes in the header are declarations. Actual installed core hashes
come from the separate installer **Core Verify** receipt, not CET or this header.

After authorized installation and the user's own game launch, paste:

```lua
GetMod("PTFR_QR9_Diagnostics").start("S00")
```

At the main menu this arms for an attached player; it does not claim to observe
earlier restoration/ArchiveXL graph startup. The user loads normally. At the end:

```lua
GetMod("PTFR_QR9_Diagnostics").stop()
```

Optional commands require no fact inspection:

```lua
GetMod("PTFR_QR9_Diagnostics").mark("visible-call-working-save-label")
GetMod("PTFR_QR9_Diagnostics").status()
```

`start(profile, label, seconds)` also accepts an optional short user label and
duration1..900seconds; default300. Profiles S00–S08 match the test cards. Never
keep a capture running for several game days: stop after the relevant event,
then start a fresh labeled segment near the expected later callback.

**Stop before a deliberate load/reload; start a new segment afterward.** Observed
PlayerPuppet.OnDetach or attached/pregame/entity changes stop capture, but the
hook is not runtime-certified and identical player IDs are not save identities.
No automatic cross-save continuity or saved graph/clock inspection is claimed.

Logs are created inside:

`GAME/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/`

Names are `QR9_capture_<UTC>_<serial>.jsonl`. Every row is flushed; stop, normal
shutdown and auto-stop print the filename. Existing nonempty files are skipped
and never truncated. Default limits:300wall-seconds,2048rows,8MiB,131072bytes/row.
Duration ends on the next update/callback if the game is not pumping callbacks.
Shutdown may still be abrupt; an absent terminal cleanup is incomplete evidence.

Fact listeners are event-driven. The2-second timer checks only session guards,
journals, phone state and S03 vehicle getters; there is no fact polling fallback.
Missing mandatory fact/listener API stops the capture after cleaning earlier
registrations. Missing context guards produce deduplicated SESSION_WAIT reasons.
Failed unregister calls block further starts in that Lua environment and retain
only inert proxy objects, not player/system handles across teardown. The user
should stop testing and report that failure; do not manipulate native listeners.

Observation limits:

- Initial readings are baseline values. Default zero does not prove absent or
  unearned history. Delivery timestamp/sequence is not native-write order.
- A fact named Request/ACK/Issued/Retired has a pinned authored role, but its
  value/callback is not an actual graph-node/controller/lease query.
- Actual graph activation, native ownership, numeric ArchiveXL engine receipt,
  save identity, native pending clock and phone queue are NOT_OBSERVED.
- Journals and phone manager are guarded getters, not UI/audio/notification
  evidence. Two-second snapshots can miss transient states; absence is not FAIL.
- Four S03 native vehicle record identities are queried through the locally
  supported player-unlocked getter. This is not inventory presence, proof of
  native VehicleAvailable evaluation, or full Nitro eligibility.
- Current ManualSave23 metadata already completes CVI02 and Ronald01/08. Those
  fresh tests are NOT_TESTABLE there;03/12/Nitro absence is not eligibility proof.

The existing CET API pattern is pinned in `api_proof_02.json`, with current ASI
literal exports and current compiled REDS getter use. The official
[CET export source](https://github.com/maximegmd/CyberEngineTweaks/blob/master/src/scripting/Scripting.cpp)
corroborates NewProxy/Observe names; exact upstream-binary equivalence is not
asserted. All real API availability, callback delivery and cleanup remain unrun.

`verification_04/result.json` records39 standalone LuaJIT assertions and five
actual Lua-source mutants. Private tooling is official lupa2.8/LuaJIT2.1;
`tooling_provenance_01/manifest.json` pins the wheel and metadata. No CET/game DLL
was loaded for fixtures. `snapshots/` preserves uninstalled earlier prototypes.
Only version04 is selected by the final manifest.

Safe fresh-output offline replay from workspace root:

```powershell
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr9/worker_b/test_offline.py --out verification_FRESH
```

The root read-only `collect_observation.py` collects one stopped capture and
bounded support-log candidates. Its analysis is capture integrity and declared
metadata applicability, never gameplay PASS. Root's human card gives its exact
command. If the addon cannot load/start and no JSONL exists, preserve CET's
`scripting.log` and the console error; do not use external dofile loaders or
change the frozen addon to make it run. No collector or diagnostic was run
against the real game during preparation.
