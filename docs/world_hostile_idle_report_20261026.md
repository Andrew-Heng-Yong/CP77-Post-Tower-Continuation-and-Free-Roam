# Post-Tower hostile NPC ambient behavior — 26 October 2026

## Live observations

The user reports that many nonquest hostile NPCs near the Grand Imperial Mall
and El Coyote stand idle until V approaches. Detection, combat and dialogue
then work. Comparable NPCs animate normally before the Tower ending with the
same mod setup. Pedestrians and traffic move normally after the ending.

Two targeted Pacifica actors are distinct:

| Actor | Record | Workspot / scene / combat | Position |
| --- | --- | --- | --- |
| Scav 9016721 | `Character.sa_ep1_courier_loop_enemies_scav_fmelee2rare_knife_ma` | true / false / false | -2396.396, -2306.591, 10.415 |
| Scav 9007265 | `Character.cvi_scavenger_grunt1_ranged1_nova_wa` | false / false / false | -2150.092, -1919.787, 5.908 |

A further post-ending Scav sample using
`Character.cvi_scavenger_grunt1_melee1_fists_wa` is in the normal `Relaxed`
high-level AI state, outside a workspot, with no active time dilation. The
user clarified that affected actors **animate in place but do not patrol**.
The game clock is not paused (`timePaused=false`, PTFR time-unpause done=1).
Later persistent-spawner readings identified the exact community for the
melee Scav on both saves. The offline AutoSave-15 audit also identifies the
ranged Scav and its two neighbors as members of that same community.

## Source trace and exclusions

The installed JC1 combined archive has no `.community` replacement and no
Pacifica or El Coyote encounter-sector override. The consolidated scripts do
not issue a global hostile-AI command. The courier record belongs to a
different EP1 vehicle-courier enemy family; its workspot state cannot be used
to diagnose all gang actors.

The original `open_world_content.questphase` enters
`open_world_combat_events.questphase` at node 12. That combat-event root enters
Pacifica Coastview at node 2 and Heywood Vista del Rey at node 12. The Tower
ending terminates the original main-game content parent. Our consolidated
package does not currently restart those combat-event roots. This is a
credible **owner-lifetime gap**, not yet proof that it causes the reported
loss of patrol movement in actors that remain spawned.

The two native district phases are not safe to restart wholesale. Their
embedded loops contain 27 Pacifica and 32 Heywood `Reactivate` actions, paired
with 27 and 32 `ResetKillCount` actions. Reissuing the phases can reset cleared
encounters and respawn enemies. Offline WolvenKit NodeRef hashing maps the
registry item containing a matching `goon2` ranged Scav record to
`#ce_pac_cvi_116/cs_goons_cars_com` (hash `13399962301655001666`). That
community's native owner loop has only `Reactivate` and `ResetKillCount`
actions; it does not command patrol or animation.

A direct Codeware community query showed `#ce_pac_cvi_116` active with the
same five entry states on both saves, while its entry-ID arrays reported zero.
A later direct persistent-state read of the targeted actor returned spawner ID
`13399962301655001666` and entry `goon1`, confirming that this **is** its
community despite empty wrapper arrays. The community remains active on both
saves; restoring a disabled community is therefore not the fix. The user says
these same Scavs patrol before Tower and only animate in place afterward.
The registry entries for that car-goon community use `cs_goons` markings and have no explicit patrol initializer. Among the 27
Pacifica repeat loops, the only `cs_patrol_com` group is a Voodoo Boys vehicle
patrol with two gang members and a vehicle; the sampled Scavs are not that
patrol group. Vista del Rey's 32 loops are cars, stand, sit, couch, cards,
shooting and similar staged groups, with no named patrol group. These source
labels do not establish whether an actor should remain stationary: the native
idle AI itself selects and moves between community workspots without requiring
`AIPatrolRole`. The later workspot trace below replaces the earlier inference
that the lack of a patrol initializer could explain the symptom.

The apparent unmatched `q307_cutscene` crowd Disable is a disconnected node
in the shipped `q307_09_cutscene` phase. All input-reachable q307 crowd Disable
sources have matching input-reachable Enables, including
`q307_misty_cutscene` in `q307_cleanup`. Pedestrians and traffic also move
normally, so a global crowd reset is not supported by this evidence.

## Diagnostic status

A workspace-only CET Lua probe was attempted, but CET's console has no
`dofile` global, so the one-line loader failed without changing game state.
The unused probe was removed. `diagnostics/world_npc_idle_20261026_01/combat_ref_hashes.csv` contains the offline NodeRef-to-registry mapping.
The direct persistent-spawner ID identifies the actor and confirms its
community. On a disposable post-ending branch, the user reissued `ActivateCommunity`
for the confirmed spawner. The group changed, but the actors still only
animated in place. They were asked to reload without saving. This rejects
a simple active-community refresh as a repair. No `Deactivate` or
`ResetCommunity` command was issued. A direct pre-ending spawner-ID reading
later confirmed the same record, spawner ID, and `goon1` entry in both saves.

A read-only source census of all 16 districts under
`open_world_combat_events` is in
`diagnostics/world_npc_idle_20261026_01/combat_owners/district_matrix.json`.
It identifies hundreds of `Reactivate`/`ResetKillCount` actions and confirms
that a blanket restart would disturb completed encounters.

Current status: WA1 was installed for a disposable test, and the user
reports the Scavs **still idle**. WA1 was rolled back; JC1 is installed and
verified across all 51 paths. See [WA1](world_combat_wa1.md) for the negative
result and automatic-save recovery. No production ambient-behavior fix is
claimed. The original 16-district controller cannot safely be restarted
wholesale.

## Offline follow-up; no further user tests

The game's Pacifica combat-event community resources were extracted read-only
under `diagnostics/world_npc_idle_20261026_01/combat_communities`, with their
standalone templates under `combat_templates`. Of the 18 standalone encounter
communities, `ce_pac_cvi_10.community` contains two
`communityPatrolInitializer` entries with `AIPatrolRole` and a path. The
others do not have a patrol initializer. The confirmed `#ce_pac_cvi_116`
spawner is an embedded prefab community, so these standalone entries do not
establish its authored role. The shared Scav template has no initializer;
it also cannot establish the embedded instance's final role.

The previous request for a further CET role comparison is **withdrawn**. The
user instructed us to stop asking for in-game tests. Source, saved evidence and
offline checks are sufficient to continue investigating.

Fresh official `root.behavior` and `idle_work.behavior` show that autonomous
idle AI selects a community workspot, moves to it, then uses it. A missing
available workspot can leave the actor in ordinary idle while detection and
combat remain functional. The sampled saved AI records `StoryTier=Gameplay`,
no mount/unmount request and `IsInAlerted=false`; a saved cinematic-tier lock
does not explain that actor.

The exact native Coastview owner at `root/28/18` owns
`phaseInstancePrefabs=[#ce_pac_cvi_116]`. **WA1 omitted this property.** Fresh
world extraction maps that prefab to
`quest_8ea3914adf5e218a.streamingsector`. Its three human workspot IDs match
the three saved Scavs' usage tokens exactly:

| Saved entity | Original workspot ID | Native node |
| --- | --- | --- |
| 9007265 | 11153878992642244015 | 3 |
| 9007266 | 11153880092153872226 | 4 |
| 9007264 | 3463634463554437331 | 2 |

The actual community spawn area is a separate default-world node. This explains
how the NPCs could remain present while their original quest-owned ambient
support disappears. The exact prefab has 24 nodes, including five human/vehicle
spots, shooting smart objects, security/guard support, a reset trigger and two
preview vehicle spawners. Both preview spawners have `spawnOnStart=0` and
`alwaysSpawned=false`. The reset trigger only notifies quest listeners; it
contains no reset action. All three current native workspot resources are
unpaused. Scanning 57 native and 68 mod archives found no mod override of the
seven exact resources checked.

This is a strong source-supported cause candidate, **not a live-confirmed
repair**. The saved prefab-handler payload is opaque and identical in the
compared saves; it does not independently prove the exact prefab's runtime
enabled state. The aggregate saved workspot-instance count falls from 23 to
zero, but that count is not a per-NPC runtime trace. The courier-family Scav
and the unsampled El Coyote group require separate owner binding.

`prealpha/world_workspots_ww1/candidate_02` contains the reviewed local exact-group owner
prototype: completed-Tower guards precede a persistent child owning the
original prefab. It has no community activation, kill reset, NPC role change
or native fact writer. Its serialized graph passes 16 admission-condition checks
and four negative controls. The accompanying admission scaffold compiles with
the complete 64-source stack and public Codeware; it uses the existing baseline
driver to find a living NPC near the exact site, prove its original spawner and
active entry, then require two settled safe samples. It adds no global NPC
wrapper and preserves the existing module/file layout. Neither prototype is
installed or registered in the game. Broader encounter eligibility still needs
separate review before a production candidate is selected. Evidence is under
`diagnostics/world_npc_idle_20261026_02`.

## Broader encounter census

The offline pass inventories 473 native prefab-owner nodes containing 477
prefab references. It resolves 385 references to 374 unique prefab paths and
decodes 353 current native sectors. The remaining 92 references are explicitly
unresolved; 21 resolved paths have no matching native sector in the scanned
archives. Neither category is silently admitted to a repair.

| Unique resolved prefab classification | Count |
| --- | ---: |
| Support-shaped source; eligibility still unproven | 254 |
| Additional ambient conversation/audio review needed | 87 |
| Resource unavailable | 21 |
| Other payload or membership review needed | 10 |
| Automatic content spawning; withheld | 2 |

The two automatic-spawn cases are `ce_pac_cvi_07_openworld` and
`ce_pac_cvi_09_openworld`, containing three vehicle population nodes with
`spawnOnStart=1`. Restoring every encounter prefab unchanged would therefore
create additional content. Other sectors contain patrol splines, ambient
conversation zones, security devices, triggers and crowd exclusions; a node's
population-spawn flag alone does not establish that the entire prefab is safe.

The initial 116 simple-loop subset is retained separately: 110 sectors decoded,
107 source candidates and nine withheld references. That subset is not an
allowlist either. The full matrix lists every reference, its original owner,
resolved resource, binding status and exclusion/review reason:
`diagnostics/world_npc_idle_20261026_02/families/matrix_477_03.csv`.
Its associated census rechecks 706 raw/decoded file hashes and the three saved
inputs. All saved inputs are unchanged. JC1's current 51 installed paths also
pass Verify; no ambient repair was installed in this investigation.

Fresh source also traces all 16 district encounter owners through
`additional_game_elements` and `open_world_content` to the main-game subtree
terminated after Tower completion. This establishes a shared retirement path,
not identical symptoms or repair eligibility for every descendant. The courier
record appears in three registry communities with many location phases; the
preserved saves contain no matching stub for the sampled courier actor. Exact
El Coyote actors likewise remain unbound. Those cases, quest/scene actors,
NCPD/gig owners and city-scene families are explicitly outside the exact Scav
prototype rather than claimed repaired.

Final pinned assessment:
`diagnostics/world_npc_idle_20261026_02/assessment_01.json`, SHA-256
`38B609AD0C1B1E92D7EC0682DEB67077C3277D9DDC83F58B3950F1D3B81CE0E7`.
The selected owner is candidate 02 and the compiled admission helper is
`ai/compile_admission_03`; earlier prototype iterations are retained as history.
The helper is also copied into candidate 02's `script_source` for inspection.
These are development sources, not a deployable full-package ZIP. A future
production successor must undergo manifest, packing/readback, collision,
save-preservation and rollback checks while retaining the 51-path layout.

## Packaging clarification and separate probe

The user permits temporary additional files for a one-community workspot
prototype. The complete production ambient fix must still replace files
within the **51-path consolidated package**, with no prototype overlay left in
the game. The selected optional additive probe is
`prealpha/world_workspots_ww1/probe_04`: one archive containing the original
prefab owner, one ArchiveXL quest registration, and one REDscript file for
automatic scoped admission. Three files are required because the quest
resource, its registration, and the script use distinct engine paths.

The first additive build (`probe_03`) had no guaranteed startup call and is
historical workspace evidence only. Probe 04 uses a single player-load hook
to initialize its own scriptable system, without any NPC attach wrapper. Its
complete 65-source script stack compiles against public Codeware 1.21.1. The
archive was reopened and its only resource matched the reviewed candidate 02
bytes. The private depot path had zero collisions in 68 installed mod archives.
The three-file ZIP reopened with every member hash matching its manifest; all
51 installed JC1 files matched before packaging. Its SHA-256 is
`1214D5CEFA35F6A80264900AF7DDDA60F5928829170D3A15B9F63226D051E5F1`.
It is now **locally installed but unreleased**; there is no claim of live patrol
recovery. When moving to a full fix, remove all three optional probe paths and
fold only reviewed functionality into a new 51-file successor.

The game was closed for installation. The separate probe passed full 65-source
compilation with public Codeware 1.21.1, one-resource archive readback, zero
collisions in 68 installed mod archives, and 3-file ZIP readback. The installer
passed six interruption/rollback fixtures and refused an existing target.
Actual Validate, Install, Verify and ValidateRollback passed. All 51 JC1 files
still match; 301 saved files and names are byte-identical before and after.
`prealpha/world_workspots_ww1/probe_04/installed_assessment_01.json` pins the
installed evidence (SHA-256
`FA9203120D310D60E10C4D311C3E20E24731F2C2BCC0F8860DA268669DBA31EA`).
The prior files and receipt are under
`recovery/world_workspots_ww1_probe_04_01`. When the game is closed, first
run `prealpha/world_workspots_ww1/deploy_probe_04.ps1 -Action
ValidateRollback`, then `-Action Rollback` to remove precisely these three
probe files. File rollback does not undo an in-game saved quest owner. No game
launch, fact editing, Git push or release occurred in this installation.

## Probe 04 live failure and probe 05 successor

The user checked the exact car-goon Scavs and reports they **still animate in
place without patrols** under probe 04. That is a live negative result for the
first installed workspot prototype. It does not establish whether the native
prefab owner entered: probe 04 did not log its admission stages.

Captured game logs confirm probe 04's REDscript compiled and ArchiveXL merged
its private quest phase. At the same Pacifica location, the activity logger
reported `scene/dialogue/sceneCameraEnabled=true/false/true` for V during
ordinary play. Probe 04's safety gate rejected `IsEntityInScene(player)`;
scene membership therefore could have prevented its request. The snapshot does
not prove that this gate stayed true on every tick. The quest phase could also
be present but not entered on an already progressed save.

Probe 05 replaces **only** `r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds`.
Its safety gate checks `IsEntityInDialogue(player)` and it logs stage changes
through `PTFR_WW1`: system attachment, near-area owner `Ready`, admission
waiting, eligible Scav count, request, and owner receipts. The probe archive
and ArchiveXL registration are byte-identical to probe 04. Full 65-source
REDscript compilation with public Codeware 1.21.1 passed. The installer passed
four interruption/rollback fixtures and actual game-closed Validate, Install,
Verify, and ValidateRollback. All 51 JC1 production file hashes match and all
301 save files remained byte-identical across installation. The installed
script SHA-256 is
`53923E0F1E1F6A760ABFA3FF6278B50B5882A4B51A2394DE4764038ACB68D8EB`.

At this historical stage, probe 05 was **installed, not yet live verified**. No further in-game test or CET
command is requested from the user. The current installation has 51 production
files plus three temporary probe files. For file rollback when the game is
closed, run `prealpha/world_workspots_ww1/deploy_probe_05.ps1 -Action
ValidateRollback`, then `-Action Rollback`; this restores the exact probe 04
script. Then run the equivalent two actions with `deploy_probe_04.ps1` to
remove all three temporary paths. File rollback does not undo saved game state.
The eventual production ambient fix still requires a 51-file consolidated
successor and removal of every prototype-only path.

Pinned logs and assessment are in
`diagnostics/world_npc_idle_20261026_03/assessment_01.json`; probe 05 build,
manifest, compilation and deployment evidence are in
`prealpha/world_workspots_ww1/probe_05`. No assistant game launch, saved-fact
edit, Git push, or release occurred.

## W2 production-layout successor

The user later confirmed probe 05 restored patrol for the sampled Scavs after
dismounting from a motorcycle. Its game log records three matching actors,
owner request and `Claimed/Entered=1/1`. W2 now folds that exact resource into
the combined archive and adds 205 more source-matched prefab-only owners. The
full 51-file successor is locally installed; all three temporary probe paths
are removed. The new groups have no live patrol proof. The separate courier,
El Coyote and other NPC families are not claimed fixed. Full source, package,
rollback and save evidence is in [W2](world_workspots_w2_20261026.md).
# Current installed successor: W3

The user reports the Pacifica car-goon patrol resumed after dismounting from a
motorcycle. The verified production layout now contains W3: 237 source-verified
native combat-event prefab owners in the same 51 installed mod paths. Only the
original Scav group has live patrol proof; other families remain unverified.
See [W3 deployment and scope](world_workspots_w3_20261026.md).
