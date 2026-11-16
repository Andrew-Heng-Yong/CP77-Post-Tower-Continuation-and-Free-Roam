# Step 2 checkpoint installation and test

Installed checkpoint candidate 02 on 14 November 2026 at 19:34 Toronto time. The update replaced the two history files and added the private execution-checkpoint DLL. Verification matched 51 Core paths, the DLL, 26 dependencies and 379 existing save files. The 16 deployment fixture actions covered rollback, interruption recovery, a running game, and an occupied plugin path. File rollback to RD10 was verified ready. [Installed manifest](deployment_01/installed_manifest_01.json) · [Rollback readiness](deployment_01/rollback_readiness.json) · [Candidate checks](../universal_resume_checkpoint_20261114_01/REPORT.md)

## Epistrophy playtest

1. Start from a normal pre-ending save with **Epistrophy** active. Leave at least one Delamain car completed and at least one still pending. Keep a pre-ending manual save with that progress and note the completed car locations.
2. Take the direct Reed route and play through **The Tower** in the same session, including the credits and return to free roam.
3. Leave the pending cars alone for the capture test. Make a new manual save in post-Tower free roam and reload that save once.
4. Report the pre-ending and post-Tower save slots or timestamps and which cars were complete before the ending.

The evidence review compares the pre-ending AND mask and car journals to the checkpoint committed before cleanup. It checks for the same checkpoint ID and captured bytes after the post-Tower save and reload. The capture log uses “Save-local execution checkpoint committed before native cleanup.” The recovery record uses the filename pattern `checkpoint_execution_<id>.json`. Quest continuation through this checkpoint is the next implementation step.
