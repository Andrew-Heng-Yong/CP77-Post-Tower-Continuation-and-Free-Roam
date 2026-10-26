# H10 services and snapshot reload repairs — 25 October 2026

Live follow-up: the user reported “it works” after installation, then confirmed
persistence after the requested manual-save/reload check. H10 ownership and
interactions, including successful reload, are now a user-reported pass for
this fixture. The exact slot and post-reload balance were not provided. No new
log or save inspection accompanied this confirmation. This supersedes the
pending live-test status below; broader save/interaction coverage and the
separate CD1 investigation are unchanged.

H5 purchase dialogue and the door worked in the user's test. The owned map icon
appeared after leaving and returning, but interior prompts remained absent.
AutoSave 19 and AutoSave 2 both contain one successful €$25,000 payment
(219,342 → 194,342), purchase state 3 and native AccessApplied/Entitled 1.
Ownership therefore transferred. The map status log describes the requested
variant; it does not prove an immediate rendered UI refresh.

The apartment interaction owner has Ready 1, but Enabled/Active/Interrupted
are absent from the serialized fact tables. Absent entries alone are not live
zero readbacks. No H10 interaction scene hash occurs in the saved scene instances.
AutoSave 19 contains Wilson's vendor scene while V is near the apartment.
The former service admission ran inside general Startup, once per ten one-second
polls, and returned early for any scene membership. This is a concrete source
blocker consistent with the scene=true logs; the exact failing predicate at each
missed tick was not recorded.

H6 moves only the existing H10 entitlement/revocation block to each eligible
one-second poll. It substitutes actual dialogue participation for ambient scene
membership and retains combat, workspot, mounted, high/tier, save-lock, token,
ownership, location, native acknowledgement and idle-owner guards. It only
publishes the existing reusable permission. Native apartment/phone gates and
all scene/action ownership remain unchanged. It logs outstanding service gates.
Payment, dialogue, door and map classes remain compiled-identical to H5.
The delayed map refresh was observed working and was not changed here.

During investigation the user loaded AutoSave 2 and crashed before gameplay.
No candidate had been installed then. The 15:18:10 dump confirms a native null
read at Cyberpunk2077.exe+0x7bb890 during SnapshotStateHS1.RowJSON. Its caller
was copying SnapshotRowHS1.facts, at index 150 of a previously read count 179,
while the source array header in the dump was already zeroed. The specific
clearing writer is not identified; a load/restore race is inferred. The old CET
onUpdate exporter checked saved ready/frozen flags and could enter the payload
during loading. Lua pcall cannot catch this native exception.

HS2 serializes the frozen payload into a transient JSON cache from the scheduled
game callback, at most 16 rows per tick, after player attachment. CET's public
JSON getters read only the completed cache. Restore/detach invalidate readiness;
CET also checks attachment and pregame status before entering the system.
All saved fields, snapshot origin, capture/eligibility rules, file verification,
epoch/revision acknowledgements and existing snapshot files are preserved.
No baseline regeneration, manual facts, payment retry or save edit was performed.

Validation: HS2 full 91-source SCC including Equipment-EX, 30 checks including
actual Lua exporter lifecycle/file tests, and 14 real installer fixture actions
passed. H6 full combined 91-source SCC, 53 checks and 14 installer fixture actions
passed. Both packages passed Validate, Install, Verify and ValidateRollback.
HS2 protected 679 files; H6 protected 680, including 265 save files each.
User loading changed user.gls between the initial capture and crash; the final
closed baseline was used for deployment. All captured save-slot files remained
unchanged. One initial H6 CLI string-comparison error and test-parser issues
were corrected before packaging; no failed candidate was installed.

Installed: two HS2 files (SnapshotStateHS1.reds and the snapshot CET init.lua),
one H6 file (RestorationBaseline.reds). No archive, framework or game cache edits,
assistant launch or public release. Native in-game verification remains pending.
First test AutoSave 19 (already paid, near H10); check interior prompts, then a
new manual save/reload. AutoSave 2 is the preserved crash fixture.

After these installs, the separately authorized CD1 task installed two diagnostic
scripts. Their hashes match its recovery receipt; they were retained. A fresh
combined full 91-source compilation including H6, HS2 and CD1 passed (compile_04,
SHA-256 1AB2995A3D18E1F6F2A13E0E1EF6A8D753C679544A81F0A1B1B63E0A44629115).
The final reconciliation is diagnostics/h10_services_20261025_01/assessment_02.json.
WolvenKit's dynamic snapshot export omits custom struct row arrays; that omission
does not establish missing snapshot data in the save.

Evidence is private under diagnostics/h10_services_20261025_01 and the two
candidate_01 folders. Final sources/proofs are pinned; use successor revisions.

Rollback H6 before older baseline packages:
`prealpha/h10_h6/deploy_01.ps1 -Action ValidateRollback`, then `-Action Rollback`;
backup recovery/h10_h6_01. Rollback HS2 before older HS1 snapshot packages:
`prealpha/snapshot_reload_hs2/deploy_01.ps1` with the same actions;
backup recovery/snapshot_reload_hs2_01. These targets are disjoint. Rolling HS2
back restores the known unsafe exporter. File rollback does not undo saved
ownership, money or snapshots. H5/FS1 rollback chains remain separate.
