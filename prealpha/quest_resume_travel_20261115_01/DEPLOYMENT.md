# Checkpoint v0.1.13 installation

15 November 2026. Installed the authorized v0.1.13 checkpoint DLL. Post-install readback verified the DLL, all 51 Core paths and 26 required files, including the three existing Cassius scripts among the Core paths. The before and after snapshots matched all 415 save files by name and SHA-256. The unmanaged game inventory matched across the transaction. [Installed manifest](staged_01/deployment_01/installed_manifest_01.json) · [Post-install verification](staged_01/verify_01.json)

The installer passed 17 actions across eight isolated fixtures, including interruption recovery and rollback. The v0.1.12 DLL backup verified and file rollback is ready. [Installer fixtures](staged_01/fixture_results.json) · [Rollback readiness](staged_01/rollback_readiness_01.json)

The 146 native checks cover the shared code and the offline Moving Heat fixture. Moving Heat runtime admission remains deferred. The live handoff test is scheduled for the end of Step 5 after all four resume types pass offline. [Travel fixture result](REPORT.md)
