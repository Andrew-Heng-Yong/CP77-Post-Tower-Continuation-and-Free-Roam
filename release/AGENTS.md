# Release documentation and packaging

Follow root AGENTS.md and `docs/knowledge/packaging-deployment.md`. The prepared `v0.2.0-beta` is the VD1 snapshot, separate from the newer local PH3 installation. Do not update manifests, dist artifacts or publication state during documentation-only work.

The final recorded beta ZIP contains exactly `archive`, `bin`, `r6`, `readme`; 51 core paths plus four readme files. No helper scripts, old ZIP, backups, release notes or persistence contract are bundled. Required Atelier correction remains explicitly documented with original/corrected hashes. Consumer cleanup removes only accepted path+hash matches after containment/link checks, keeps unknown/changed files and does not require old ZIP/backups.

Development deployment recovery is separate and retains rollback copies. Historical release builders/tests can overwrite artifacts and include a stale `TowerContinuation/FILES.json` test path; read conflicts C07/C08 before reuse. No automatic release/push/tag, cleanup, game installation or compatibility guarantee follows from a package PASS.
