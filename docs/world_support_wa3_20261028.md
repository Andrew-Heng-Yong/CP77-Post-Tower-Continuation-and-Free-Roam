# Native NPC support successor WA3

WA3 extends the restored world's native NPC support beyond the shooting and
vehicle controllers in WA2. The reported Coastview party is a specific target:
the hostile `goon_m` and neutral `junkie_f` share community
`13790632485457691133`, and their observed positions match the original dance
workspots. WA2 did not own that support prefab. WA3 adds its native support
without resetting the encounter or changing either actor's AI role.

WA3 and the selected CO1 computer compatibility fix were installed together on
28 October after the game and launcher were closed. The [installed assessment](../prealpha/world_support_wa3/candidate_02/installed_assessment_01.json)
records the exact hashes, package scope, save comparison and rollback state.
After installation, the user reported that both fixes worked as expected in a
recent run. The [live observation](../prealpha/world_support_wa3/candidate_02/user_live_observation_01.json)
records that report without assigning it to every individual NPC family.

The audit extends the original 477 combat-event prefab references through the
complete external-phase closure: 247 native resources, including 101 additional
prefab references. It also reviews the 16 base-game district community routines,
Phantom Liberty routines and nine additional world roots. Earlier ambient,
audio and conversation exclusions are reviewed against their actual native
dependencies. This source census is not a claim that every NPC works in gameplay.

The repair preserves the 1,212 resources already in WA2, existing support
owners and saved receipts. Additional owners require exact current native
community identities and authored workspot bindings. Source equivalence and
successful compilation do not establish that every restored activity works
in gameplay.

## Reviewed support

| Support | Treatment |
| --- | --- |
| Party, idle, service and patrol workspots | Use the current native support prefab and exact community/entry mappings. Do not invent workspots for missing vanilla alternatives. |
| Ambient speech and conversations | Review the referenced scenes for quest, actor and reward operations before restoring their triggers. |
| Audio signposts and patrol splines | Retain native support after dependency and actor-binding review. |
| Preview spawners in groups 160 and 161 | Use private sector copies that omit three automatic preview spawners while preserving native workspot identities and retained placement data. |
| Glen support group 1004 | Omit the specific story-conversation trigger that writes native facts and performs actor operations; retain the 61 workspots and the other reviewed ambient conversations. |
| Environmental variants for groups 200, 202, 210 and 461 | Copy the exact native visibility event behind existing support receipts, native readiness and a private one-time receipt. Preserve the native assets, variants and placements. |
| West Wind receptionist greeting | Preserve the exact native player trigger, living-receptionist check and one-game-day cooldown. Omit community activation; this controller requires the original receptionist entry to be active already. |
| Group 393 corpse props | Retain the exact static corpse templates and appearances after component review. They are plain entities with corpse collision and visual components, without NPC or inventory components. |
| Border-crossing support group 1000 | Retain 41 workspots and passive support in a private sector. Omit the respawn, kill, combat and security triggers and the three security devices connected to external cameras and turrets. Preserve the native prologue-completion gate. |
| Phantom Liberty support | Restore four exact native support families with their original progress gates. Filter story, respawn and security triggers; retain six reviewed HillSpa conversations. |
| Northside convoy support group 1246 | Omit two automatic vehicle preview spawners. Retain passive support for already-active NPC entries without replaying the convoy or its fight setup. |

The environmental review covers 124 selected current placements, including
furniture, destructibles, lights, sound and two televisions. Group 461's
variants already default to visible. The controller follows the original
show-once operation; it does not replay encounter spawning. Base-game and
Phantom Liberty placement payloads differ, so the review uses the current
winning sectors rather than asserting that both versions are identical.

Private sector filtering preserves all retained workspot IDs, node references,
payloads and placement bytes apart from the necessary node-index relocation.
The private streaming block preserves the native root and descriptor indices
independently. Earlier candidate blocks and interrupted artifacts are retained
as rejected evidence and must not be packaged.

The expanded safety review found 481 native encounter notifier triggers across
222 new base-game support sectors and another 126 across the 94 additional
combat-event sectors. Those triggers can reach native reset, spawn, fight or
cleanup consumers. The comprehensive private copy omits them and two automatic
vehicle previews in Northside group 1246. Independent readback passes 19,780
checks on 315 sectors, 5,514 retained workspot placements, placement bytes, variant index
relocations and descriptor identities. Group 1013 is withheld because WolvenKit
9.1 fails to parse its native world node; an unfiltered copy is not an
acceptable substitute. See `private_sectors/verification_comprehensive_01.json`.

## NPC-versus-NPC fights

Actual scripted fights are separate from boxing and training workspots. The
expanded audit found reciprocal NPC threats and combat targets in Northside's
staged convoy and Charter Hill's guards-versus-bots encounter. Their native
controllers also mount vehicles, change faction attitudes, enable loot, reset
security or advance encounter completion. An idle actor does not establish a
safe point from which to resume these sequences. WA3 therefore does not inject
their combat commands or restart those encounters.

The support driver rejects a sampled actor already in combat and does not force
an entered support owner to restart when combat begins. Admission from one
eligible actor does not establish that every other member of its community is
out of combat. Retained native security and guard metadata can still affect
ordinary perception and area behavior. Of 35 reviewed boxing/training workspots,
29 have preserved or added support; six belong to quest-specific dojo staging.

## Computer compatibility component

CO1 addresses the native News page remaining visible under Virtual Atelier.
The selected candidate changes only `PopulateAtelierView` in
`r6/scripts/virtual-atelier-full/SetupNewTab.reds`. It clears the full native page
body before drawing Atelier while retaining the outer computer browser frame.
The user reports that the installed computer fix works as expected. The report
does not itemize every News, Atelier and Messages interaction.

The Tower package retains its 51 existing paths. CO1 is a separately pinned
existing-path compatibility component, not a redistribution of Virtual Atelier.
The combined installer manages 52 paths and replaces four files in one guarded
transaction: the Tower archive, its XL registration, the existing Baseline
script and the selected Atelier script. Compilation must include both candidate
scripts and the complete current installed script inventory.

## Validation and deployment record

Candidate 02 adds 296 reviewed passive support owners with 421 exact community
bindings, while retaining 238 WA2 owners and all 1,212 previous archive
resources. The archive has 351 added resources and 1,563 total. A complete
112-source compile with CO1, 128-archive winner scan, 10,469 independent owner
checks, 19,780 private-sector checks and 26 deployment fixture actions passed.
The actual guarded install, verification and rollback-readiness checks passed.
All 301 save files and names matched the read-only capture made before install.
The local 51-path ZIP is unreleased. No game launch, native-fact edit, save edit,
Git push or public release was performed.

The user-reported live pass covers the installed NPC and computer fixes in their
recent run; it is not a test of every support owner. Twenty-four additional
families with native progress or lifetime fact gates remain
withheld, as does core group 1013 because WolvenKit 9.1 cannot decode its
native world node. The two scripted NPC-versus-NPC fights require their own
stateful encounter handoff; the support owner does not restart them.

Source and evidence are under `prealpha/world_support_wa3`. In particular:

- `environment_variants/assessment_01.json` and `independent_01.json`: current native variants and the four bounded environment owners.
- `native_review/conversation_assessment_01.json` and `party_assessment_01.json`: native conversation and party dependency review.
- `native_review/corpse_assessment_01.json`: exact static corpse component and appearance review.
- `greeting/assessment_01.json`: native greeting, current community/trigger binding and negative controls.
- `private_sectors/verification_comprehensive_01.json` and `verification_ep1_01.json`: installed default and EP1 private sector readback checks.
- `combat_review/payload_assessment_02.json`: 94 additional reviewed support candidates, with encounter trigger filtering. Twenty-four remain withheld pending exact native fact-lifetime handling.
- `native_review/npc_fight_assessment_01.json`: the two scripted fight controllers and their excluded stateful dependencies.

File rollback restores installed bytes. It does not undo gameplay or saves
created after using the mod.
For this installed successor, run `prealpha/world_support_wa3/deploy_02.ps1`
with `-Action ValidateRollback`, then `-Action Rollback`, with the game closed.
The recovery folder is `recovery/world_support_wa3_02`.
