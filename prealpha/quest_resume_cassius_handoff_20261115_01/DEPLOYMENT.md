# Cassius checkpoint v0.1.12 installation

15 November 2026. Installed the authorized v0.1.12 checkpoint DLL and the three Cassius REDscript overlays. Post-install verification matched all 51 Core paths, the checkpoint DLL and 26 dependencies. Before and after snapshots matched the names and SHA-256 hashes of all 415 save files. The transaction changed only its four listed paths, and the unmanaged game inventory matched before and after. [Installed manifest](staged_01/deployment_01/installed_manifest_01.json) · [Transaction](staged_01/install_01.json) · [Post-install verification](staged_01/verify_01.json)

The installer fixtures passed 12 actions across five trees, including clean rollback and recovery from both an exception and a hard interruption after the second replacement. Backups of all four v0.1.11 files were verified and file rollback is ready. [Fixtures](staged_01/fixture_results.json) · [Rollback readiness](staged_01/rollback_readiness_01.json)

Gameplay remains scheduled for the final Step 5 check after all four resume types pass offline. The earlier workspace result covers the Cassius fixture. [Offline handoff result](REPORT.md) · [Roadmap](../../ROADMAP.md#mid-quest-resume-after-the-tower)
