# Checkpoint v0.1.2 installation and test

Installed on 14 November 2026 at 21:14 Toronto time. The installer applied both history-file replacements and the checkpoint DLL from the verified v0.1.2 candidate. The latest RD10 launch refreshed two compiler metadata files. The fresh 148-source compile and verification reproduced the same three candidate file hashes. [Candidate](../universal_resume_checkpoint_runtime_20261114_01/candidate_05/receipt.json) · [Exact installed manifest](deployment_01/installed_manifest_01.json)

All 16 deployment fixture actions passed. The real transaction and independent readback verified 51 Core files, the checkpoint DLL and 26 dependencies. All 379 save files matched across the install, and Manual Save 26 still matches the pinned Epistrophy fixture. RD10 rollback is ready. [Deployment fixtures](fixture_results.json) · [Verification](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

## Step 2 player test

1. Launch Cyberpunk and stop at the main menu. Confirm the latest checkpoint plugin log says `PTFR execution checkpoint runtime ready: capture and decode registered` before starting the ending run.
2. Load **Manual Save 26** and go straight to Reed. North Oak, Coastview and The Glen are already complete. Leave Epistrophy alone and finish **The Tower** normally through the credits and the return to free roam.
3. Make a **new manual save** in free roam before doing any more Epistrophy objectives. Reload that new save once and report its slot or timestamp.

The evidence check will look for a pre-cleanup checkpoint commit, the same three completed and four pending Epistrophy inputs, and the same checkpoint identity and payload after reloading the new save. [Saved Epistrophy controls](../quest_resume_contracts_rc2_20261114_01/REPORT.md) · [Checkpoint behavior](../universal_resume_checkpoint_runtime_20261114_01/REPORT.md)
