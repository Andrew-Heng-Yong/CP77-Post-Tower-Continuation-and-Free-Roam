# QR11 authorized diagnostic deployment — 3 November 2026

**QR10D01 candidate_02 is installed.** User authorization: “approved for deployment. you do the deployment for me”. Scope was the two diagnostic files only. No game launch, CUA, quest/fact/save edit, Core rebuild or actual rollback occurred.

| Gate | Result |
| --- | --- |
| Fresh exact-input preflight | [PREFLIGHT_READY](preflight.json) |
| Guarded installation | [INSTALLED_VERIFIED](install.json) |
| Separate installed readback | [VERIFIED_AFTER](verify.json) |
| Backup/rollback preflight | [ROLLBACK_READY](rollback_readiness.json); no rollback executed |
| Independent preservation | [PASS](verification.json): exactly two game paths changed; all310 save files byte-identical;84 protected files verified at expected states; Core/required dependencies unchanged |

Changed leaves, under `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/`:

| File | Installed SHA256 |
| --- | --- |
| init.lua | 1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90 |
| watch.json | A1AAB30B9F896CD24687D82CC2160D773C04B7193BDDCA71CC933A4C93997AAA |

Exact installer/manifest remained unchanged from reviewed readiness: installer400438835F72415A78D6604EC9551034A2967BEB42206132FC94714E8496806E; manifest8B42EAC8C161256534DB26F859A62447E8A9921104929B10ADFF83020C1B2DD0. Existing48primary and8independent fixture controls were reused, not rerun. Old QR9/QR10 evidence metadata and pinned critical hashes remained unchanged; all existing capture files were preserved. Full game metadata showed only the intended two file replacements. Unpinned bulk game files were not all byte-hashed.

Verified old/new payload backups and the flushed transaction journal are retained at:

`C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\recovery\diagnostics_qr10d01_01\`

Core remains QR8:02 with51 paths/1577 archive payloads. The protected ManualSave-23 master and selected ManualSave-24 working save remain exact. Source hashes/complete preservation snapshots are [before.json](before.json) and [after.json](after.json). Preparation completion/reports/readiness remain immutable historical records; the mutable checkpoint and current-state pointer now select this deployment.

**Live sampling has not yet been tested. Native callbacks remain unsupported by this Lua probe.** Installation verification proves bytes and recoverability, not gameplay or native delivery. Next is one human-operated D00 call only if Regina's genuine Call option is offered. No successful QR9 quest/vendor/reload test needs repetition. [Current practical steps](NEXT_STEPS.md).
