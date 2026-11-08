# D00E config-only continuation — 3 November 2026

**Installed, VERIFIED_AFTER and ROLLBACK_READY.** Applied as a one-file correction within the user's existing diagnostic-deployment approval. Only installed `watch.json` changed; no Lua/Core/quest/save modification, game launch or CUA occurred. [Preservation](deployment_01/verification.json) confirms all310save files, unchanged Lua/Core/dependencies,84protected files and old QR9/QR10 evidence. No rollback was executed.

User reported Regina absent, making D00 NOT_TESTABLE, then confirmed El Capitan callable with interaction lines. [Pinned evidence](evidence.json) identifies native parent node52/phone-condition node6, caller`contacts/player`, addressee`contacts/muamar_el_capitan_reyes`. Native PhoneSystem naming derives `phonecall_player_with_muamar_el_capitan_reyes`. Current save-slot identity was not independently confirmed by that reply; the known intended fixture remains ManualSave-24.

The new configuration adds **profiles/D00E only**. Removing it yields exact semantic equality with the previous config; no other setting/profile/version changed. New watch SHA256 `BBEFAEC2F1975EE0590BEC6D447293AF932DFBCCF2C228393133604F6D252DEA`. Logger Lua stays `1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90`.

Offline gates:10profile/transaction checks with12PowerShell actions, including actual Lua source sampling the new fact, one-file install/readback/rollback, hard-interruption recovery and drift/scope refusals.13collector parser controls pass. [Independent review](review/REVIEW.md) confirms the exact small installer diff, native IDs, profile equality, preserved58requirements and Lua as59thprotected dependency. Existing broad transaction and unchanged Lua controls were reused.

Actual gates: [preflight](deployment_01/preflight.json), [installation](deployment_01/install.json), [readback](deployment_01/verify.json), [rollback readiness](deployment_01/rollback_readiness.json). Manifest SHA `C4BC8A6AB6FDF2948DAF7C2F04EDDB34B8287FA9794040701D09E48E9160B5F5`; installer `A25BD28C015AD45401A8F1C16D58D58A769CC0C6BB1146E68EC44FDDF08AB66B`. Backups/hashed journal reside in `recovery/diagnostics_d00e_01/`.

**Use [MANUAL_TEST_PLAN.md](MANUAL_TEST_PLAN.md) and `collect_d00e.py`.** Do not use the older Regina-only D00 collector for D00E. Native callbacks remain unsupported; live sampler validation is not yet measured. No quest restoration/entitlement inference follows from a callable contact or sampled value.

If later authorized, roll this profile layer back first using `deploy_profile.ps1 -Action ValidateRollback`, then `-Action Rollback`, then `-Action Verify -ExpectedState Before`, with game/launcher closed and exact readiness/receipt retained. This restores the previous D01 config only; older parent two-file rollback can be reviewed afterward. File rollback never restores saves. Do not rerun Install or remove an occupied recovery directory.
