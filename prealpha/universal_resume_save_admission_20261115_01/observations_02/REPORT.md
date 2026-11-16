# v0.1.6 idle probe retry

15 November 2026, Toronto time. The user reported CET returned `true` on the retry after the save indicator cleared. At 01:02:05.550 the same v0.1.6 log recorded 4,061 phases, 9,994 live handlers and 18 wait handlers, then `PTFR native save handoff admission: deferred`. The first attempt returned the same guard status. Startup, the checkpoint reader and Manual Save 30 save and reload had already been exercised. [First observation](../observations_01/REPORT.md) · [Installed manifest](../deployment_01/installed_manifest_01.json)

The installed probe looks up `CGameEngine` and compares its vtable against the checked `gsmState_Session` table. The exact provider identifies these as different native objects. The successor probes the session received by the native save dispatcher. [Session-owner correction](../../universal_resume_save_session_20261115_01/REPORT.md)
