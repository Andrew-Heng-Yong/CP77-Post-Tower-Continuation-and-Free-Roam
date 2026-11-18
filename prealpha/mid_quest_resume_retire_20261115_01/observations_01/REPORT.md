# RD10 retirement startup and save-load smoke

15 November 2026, Toronto. Read-only review of the existing game logs after the `RD10_MID_QUEST_RESUME_RETIRED` installation. No game launch, save edit, build or deployment was performed for this review.

## Observed

- The installed manifest records the retirement build at 20:48:29. The six changed Core paths still match its recorded SHA-256 hashes, including the combined archive `C93D80F2EF0C5142139578E25536BB97B4E6BACD12885BE329A683339664F85B`.
- The 20:57:30 RED4ext session loaded five plugins, invoked `scc` successfully at 20:57:40 and shut down normally at 21:08:45. The matching REDscript log says compilation completed and the modded scripts blob was saved.
- CET loaded the PTFR modules at 20:57:41. The gameplay log shows the loading cover starting on a post-Tower save at 21:06:44. At 21:07:28 it recorded `2079=1`, `killed=1/1`, `Johnny=0`, `control=1`, `coverReleased=1` and `fault=0`. At 21:07:30 the loading stage became `Ready` with “All required setup checks passed.”

This supports **startup and one post-Tower save load reaching the ready gameplay state** for the exact installed retirement build. The earlier installation report and manifest retain their historical `STARTUP_AND_SAVE_LOAD_PENDING` values because they predate this run.

## Limits

This is log evidence, not a human visual assessment. It does not establish a save/reload cycle, quest advancement, all routes, reward uniqueness, or future-save compatibility. No new gameplay repair was made. The RED4ext warning about Immersive First Person concerns another installed plugin and was not attributed to PTFR.

## Sources

- [Installed manifest](../stage_08/deployment_01/installed_manifest_01.json) and six current installed-file hashes checked during this review.
- `red4ext/logs/red4ext-2026-11-15-20-57-30.log` — SHA-256 `87DCDCB05473F64624418D3CA2527A3D1D8354FB7F9B947130A2B162AD11F184`.
- `r6/logs/redscript_r2026-11-15_20-57-38.log` — SHA-256 `976FCA9EB9AB3D1F1365844E62D4510E64C92357D12F7C7A3E6B6EF6E7DF519F`.
- `bin/x64/plugins/cyber_engine_tweaks/gamelog.log` — SHA-256 `302EF42CB948C7F85A5EDAF5D9C4027FC76C480872AB7B52DE06FDD13757F3FD` when read. The mutable log was not copied into Git.
