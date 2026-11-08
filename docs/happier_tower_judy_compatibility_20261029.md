# Happier Tower Ending (Judy) compatibility review — 29 October 2026

The ending-to-free-roam handoff looks structurally compatible, but the current
combination is not fully compatible without adaptation. There is a concrete
post-ending journal mismatch. This is a static assessment, not a gameplay pass.

Reviewed the user's downloaded `HappierTower Judy 29268 1.0.1 2026-10-28T12-17Z
9ka2kyrpO.zip` (SHA256
`DFC7A944E987F4397F87E6011FFDDD1D29AAFC9EBD7E2B425EA4F0E63065CDAC`)
against the current PTFR v0.2.0-beta / VD1 payload. All 51 installed and packaged
core files match the release manifest. The Judy mod's four install paths are
absent from the game. ZIP CRC passes. Its 102 archive keys have no intersection
with PTFR's 1,564 keys. A fresh scan of 133 installed archives finds no existing
mod archive providing any of those Judy keys. This does not establish that
different resources cannot interact at runtime.

The installed game executable reports ProductVersion 2.5, FileVersion
3.0.5813403. The author's [current page](https://www.nexusmods.com/cyberpunk2077/mods/29268?tab=description)
lists 1.0.1 as a world-data update for 2.5. Its alternate ending retains the
romance and has V and Judy prepare to leave Night City; the author does not
describe it as post-ending free roam. Earlier workspace references to 2.31 are
historical; a WolvenKit JSON export header is not executable-version evidence.

## Ending handoff

The downloaded q307 root sends the Judy branch through node47, whose Out1 still
enters native cleanup at node30. The cleanup reference and terminating Out1
node1 match the native root. Inside the custom phase, the final scene node488
ends through node533's fade-out and terminating output node2; the enclosing
phase returns normally. Native cleanup still writes q307_active=0,
q307_done=1 and q307_finished=1. The pre-existing native parent analysis routes
q307 Out1 to final_boards' Q307 input. The downloaded archive does not replace
the parent or PTFR's final_boards override.

These are positive indications for continuation. They do not prove scene
completion, watched/skipped credits, camera handback or save/reload behavior.
No combined redscript compile or gameplay run was performed.

## Concrete journal incompatibility

The supplied ArchiveXL journal adds eight new objectives under
`ep1/quests/main_quest/q307_tomorrow/01_hospital_cabride`:

- `05_pickup_1`
- `05_fetch_2`
- `05_follow_judy`
- `05_fetch_3`
- `05_dropoff_1`
- `05_dropoff_2`
- `04_call_receptionist_judy`
- `04_leave_with_judy`

PTFR_Global.reds lines178–213 validate an exact 88-row native hierarchy and
exact child counts, including all inactive/active/succeeded/failed children.
For this phase it expects 11 direct children. The intended journal merge yields
19. Completing the new objectives does not remove that mismatch.

The expected result is Prepare returning HIERARCHY_MISMATCH at line269.
PTFR_TowerJournalAuto.reds lines53–56 then refuses journal writes and records
PTFRTJA_State=2. That protects the unrecognized journal but disables PTFR's
automatic post-ending journal reconciliation. It is not evidence that the
independent free-roam transition itself fails; no other packaged REDscript
consumer of PTFRTJA_State was found. This result is source-derived, not observed
in a running combined installation.

## Other limits

PTFR_Housing.reds still restricts Judy's stash/wardrobe and closes/locks her
private apartment entrance. There is no Happier Tower exception. JD1 requires
post-Tower housing enforcement, readiness and released gameplay, so the source
does not indicate that it would lock out the alternate ending's packing scenes.
It would retain those restrictions afterward. This is a post-ending policy
difference, not proof of an ending softlock or of a restored Judy companion.

The alternate phase also relocates native Judy/Viktor actors and uses custom
communities, apartment hiding and world prefabs. Their cleanup and persistence
under retained-session free roam remain unverified. The absence of archive-key
collisions cannot settle those questions.

A compatibility change would first need to recognize the alternate journal
structure without bypassing its checks, then assess custom ending-state cleanup.
Apartment/romance behavior after continuation needs an explicit design choice.
Changing load order would not resolve the journal mismatch.

Evidence is in
`diagnostics/happier_tower_judy_compat_20261029_01/assessment_01.json`,
`resource_audit_01.json`, decoded resources and deterministic graph indexes.
Only workspace audit artifacts were written. No installation, production-source
change, game launch, game/save/fact edit, beta repack, commit, push or publication.
