# Ambient workspot W3 — installed local successor

W3 extends the W2 ambient workspot repair from 206 to **237 native combat-event prefab owners**. These are authored prefab owner groups, not individual NPCs. The Pacifica car-goon Scavs are the only group with a user-confirmed patrol return: they resumed after V dismounted from a motorcycle. The other owners remain unverified in gameplay.

The 31 new Rancho Coronado groups use the authored `/#rancho_coronado` prefab key in the original quest owners and the `/rancho_coronado` registry key in their communities. Both native prefab resources were extracted and compared byte for byte for each group. W3 keeps that original pairing, with exact native spawner and community identity checks. It still requests private prefab owners only for a living streamed actor under two settled, safe samples. It does not restart native combat encounters, reset kill counts, force quest facts, or change AI roles.

The wider native source census contained 477 combat-event prefab references. W3 supports 237 source-verified owners with 245 spawner IDs. The remaining 240 source rows include unresolved or content-bearing cases and are not claimed repaired. The GIM courier loop, El Coyote actor identity, other scene/quest families and non-combat NPCs remain separate questions. W3 is not a verified fix for every NPC.

## Validation and deployment

- The 31 Rancho owner graphs read back with 496 bounded admission gates and private-only fact writers. The W3 driver compiled with all 64 REDscript sources against public Codeware 1.21.1.
- The combined archive contains 1,183 winning resources: the W2 1,182 plus one Rancho quest phase. Every member was read back. The one new resource has zero collisions among 68 installed mod archives.
- The full unreleased ZIP contains the same 51 installation paths. The actual installation replaced only the combined archive, its ArchiveXL file, and `PTFR_RestorationBaseline.reds`. The previous versions are archived under `recovery/world_workspots_w3_01`.
- Twenty deployment fixture actions passed, including five interrupted-install rollback cases. Actual Validate, Install, Verify and ValidateRollback passed. All 301 saved-game files were byte-identical before and after installation. The game was not launched by the assistant.

The package is `prealpha/world_workspots_w2/candidate_04/dist/Post-Tower-Continuation-and-Free-Roam-W3-unreleased.zip`, SHA-256 `FDC18332867CADD84A6FC0ACE22E0FDF491B696173DBA8EF7A78ACF7ED29508D`. It has not been published or pushed. Roll back W3 first, with the game closed, using `prealpha/world_workspots_w2/deploy_w3_01.ps1 -Action ValidateRollback` then `-Action Rollback`. File rollback does not undo a saved game.

Pinned source and package evidence is under `prealpha/world_workspots_w2`: `audit_03.json`, `manifest_03.json`, `candidate_03/graph_validation_01.json`, and `candidate_04` compilation, package, collision, deployment, ZIP and save proofs. W2's rollback remains a second, separate step only after W3 has been rolled back.
