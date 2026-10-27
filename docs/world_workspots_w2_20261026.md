# Ambient workspot W2 — local production-layout installation

Historical predecessor: W3 is now installed and adds the 31 Rancho Coronado
owners after proving their authored and registry native resources byte-identical.
See [W3](world_workspots_w3_20261026.md). This W2 record describes the earlier
scope and its own rollback step; roll W3 back first if reverting both.

## Observed result and scope

The user reports that the Pacifica `#ce_pac_cvi_116` car-goon Scavs resumed
patrolling after dismounting from a motorcycle with WW1 probe 05. The captured
game log shows the probe waiting while mounted, then finding three matching
actors, requesting the native prefab owner, and receiving
`Request/Claimed/Entered/Hold=0/1/1/0`. This is a live pass for **one group**.
The pinned log is
`diagnostics/world_npc_idle_20261026_04/gamelog_probe05_live_success.log`.

W2 is the first broad, installed successor. It preserves that exact private
owner resource and adds 205 source-matched prefab-only owners in nine district
quest phases. Its actor scanner requests an owner only when a living streamed
NPC has the exact native community spawner and an active entry. It requires two
settled samples after V is out of combat, dialogue, vehicles and workspots.
Owners write only their private request/claim/entry facts and hold their
original prefab. They do not restart the native combat loop, reactivate an
encounter, reset a kill count, or change an NPC role.

The 206 figures are **prefab owners, not NPC counts**. Only the original Scav
group has a live patrol result. El Coyote actors, the GIM courier family, and
other NPC families have not been matched to this result and are not claimed
repaired. Do not describe W2 as a verified fix for every NPC.

## Source audit

The original combat-event census lists 477 prefab references. W2 first screened
for decoded support assets, bounded original community identity, and no
automatic population spawning. It then required the actual quest owner's
serialized prefab path to match the decoded world path. That leaves 206 exact
owners. Thirty-one Rancho Coronado cases use an authored `/#rancho_coronado`
path while the registry/community path uses `/rancho_coronado`; their exact
authored resources exist but the mapping is not equivalent, so W2 withholds
them. Other excluded rows have unresolved resources or bindings, conversation
or audio content needing review, side-effect payloads, duplicate references,
or automatic spawning. These are source rows, not a count of broken NPCs.

The private graphs were read back from all nine resources. Checks proved 205
original prefab paths, 3,280 bounded admission conditions, private-only fact
writers and exact owner edges. The existing WW1 resource is byte-identical to
the successful prototype and uses its saved claim facts. The REDscript driver
was compiled in the full 64-source stack with public Codeware 1.21.1. This
static work does not prove the 205 newly admitted groups will patrol in game.

## Package and installation

The local unreleased ZIP is
`prealpha/world_workspots_w2/candidate_02/dist/Post-Tower-Continuation-and-Free-Roam-W2-unreleased.zip`,
SHA-256 `9931A611F7E2DAF73CB13DF0C78A0A27CE5A49F4324C0A387418B6ED3A312A52`.
It contains the complete **51-file** PTFR package. Installation replaced only
the combined archive, its ArchiveXL file, and the existing
`PTFR_RestorationBaseline.reds`. It removed the three temporary WW1 probe files.
The combined archive has 1,182 members: the previous 1,172 plus ten private
owner resources, all read back against source bytes. The nine new W2 resources
had no collision in 69 installed mod archives; the WW1 resource's only
collision was the probe archive removed by installation.

Full compilation, 23 deployment fixture actions including six interrupted
install/rollback points, actual Validate/Install/Verify/ValidateRollback, and
all 51 installed file hashes passed. All 301 save files and names remained
byte-identical across installation. The game was closed; no assistant game
launch, quest-fact or save edit, Git push, or public release occurred.

The previous production files and all three probe files are preserved in
`recovery/world_workspots_w2_01`. For a file rollback with the game closed,
run `prealpha/world_workspots_w2/deploy_01.ps1 -Action ValidateRollback`, then
`-Action Rollback`. File rollback does not undo any quest owner that a later
game session may write to a save. The installed assessment and hashes are in
`prealpha/world_workspots_w2/assessment_01.json`.

## Remaining work

Audit the excluded combat-event owners and the separate courier, city-scene,
quest and El Coyote families against their actual spawned actors before adding
them. W2 supplies a reusable exact-spawner admission pattern, but its 205 new
owners and save/reload behavior remain live unverified. The user's instruction
not to request more in-game tests remains in effect.
