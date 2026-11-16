# First monk lip-sync repair for JB4

The two private Losing My Religion scenes had no entries in JB4’s English lip map. The update carries over the two native mappings from the reviewed ML1 repair. The opening has 27 retained monk lines and the epilogue has 14. The packed map contains the original 48 entries and the two new scene keys. [Source evidence](../monk_lipsync_ml1/plan.json) · [Animation clip checks](../monk_lipsync_ml1/candidate_01/prepared.json)

All 1,723 archive payloads read back. Only the English lip map differs from JB4. Both monk scene files, the other quest resources, the ArchiveXL registrations and the setup scripts retain their JB4 bytes. The provider check covered 17 depot keys across 134 archives and verified the two English lip-map configurations. The 51-file package also passed readback. [Package manifest](candidate_01/package_manifest.json) · [Archive readback](candidate_01/readback/archive.json)

The 10 November staging checks passed against JB4. All 22 installer actions passed in eight isolated fixtures, and the read-only preflight passed with Cyberpunk and its launcher closed. All 148 registered REDscript sources matched the verified JB4 compile. [Original installer fixtures](fixture_results.json) · [Original preflight](deployment_01/preflight.json)

## Follow-up on speech timing

The user reported visible mouth movement out of sync with speech. The 10 November 23:49 ArchiveXL log shows that the English merge still loaded the original 48 PTFR entries. Both monk scene keys were absent, and the installed archive hash matched JB4. The follow-up matched each of the 41 monk events to its stock node, start time, duration and dialogue ID. Each staged clip encodes the exact dialogue ID and has a duration within 18 ms of the stock event. This checks the scene schedule and clip data. Playback with the patched map is still pending.

## Installation on 11 November

Installed over JB4 at the user’s request. The installer refreshed the runtime timestamp check and passed all 22 fixture actions and a fresh closed-game preflight. The combined archive was the sole replacement. All 51 Core paths, 26 dependencies and 313 save files verified, and the JB4 rollback copy matches the original archive. The 148 installed REDscript sources retain the verified JB4 bytes. In-game English playback remains pending. [Installed manifest](../monk_lipsync_ml1_jb4_deploy_02/deployment_01/installed_manifest_01.json) · [Installation verification](../monk_lipsync_ml1_jb4_deploy_02/deployment_01/verification.json)
