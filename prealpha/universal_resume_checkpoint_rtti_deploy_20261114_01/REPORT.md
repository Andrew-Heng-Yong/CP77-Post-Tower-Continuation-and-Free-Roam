# Checkpoint registration repair installation

Installed the repaired Step 2 checkpoint build on 14 November 2026 at 20:27 Toronto time. The verified transaction replaced the two matching history files and installed the repaired checkpoint DLL. It verified all 51 Core paths, the DLL, 26 dependencies, and all 379 existing save files. Sixteen deployment fixture actions passed and file rollback to RD10 is ready. The user authorized this repair and will run the first startup and capture test. [Installed manifest](deployment_01/installed_manifest_01.json) · [Installation verification](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json) · [Repair evidence](../universal_resume_checkpoint_rtti_20261114_01/REPORT.md)

## Step 2 game test

1. Launch Cyberpunk and confirm it reaches the main menu. The repaired DLL should log “PTFR execution checkpoint registered both native functions.” If startup stops, report the error.
2. Load **Manual Save 26** and go straight to Reed. North Oak, Coastview, and The Glen are already complete. Continue **The Tower** normally through credits and return to free roam.
3. Make a new manual save in free roam before doing any more Epistrophy objectives. Reload that new save once and report its slot or timestamp.

The evidence review will check the registrar log, pre-cleanup checkpoint commit, Epistrophy’s three completed and four pending inputs, and whether the same checkpoint survives the reload. [Manual Save 26’s saved controls](../quest_resume_contracts_rc2_20261114_01/REPORT.md)
