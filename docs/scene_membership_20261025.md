# H10 scene-membership investigation — 25 October 2026

Follow-up: [FS1's scoped vendor-scene release](fred_scene_fs1.md) is installed;
in-game verification is pending. The findings below record the unchanged
pre-repair evidence.

The strongest identified source of the H10 `scene=true` observation is **PTFR's
restored Coach Fred vendor scene**, `towercontinued\b0_story_services\fred.scene`.
The engine maintains scene membership; `IsEntityInScene(V)` reads that state.
It is not a quest fact that a REDscript `SetFact` call sets or clears.

The confirmed purchase defect was the old housing guard treating any scene
membership as a reason to hide the offer. The failing H3 log showed normal
movement state (`high=1`, `tier=1`), no dialogue and no combat, but `scene=true`.
H4 already removed this one condition from purchase eligibility while retaining
the other player checks. No new runtime repair was installed in this investigation.

## Evidence from retained saves and logs

All three saves were copied and hash-verified before read-only inspection.
The current 117 installed PTFR files match the published Alpha Test manifest.

| Evidence | AutoSave 15 | AutoSave 16 | AutoSave 17 |
| --- | --- | --- | --- |
| Fred scene hash in saved `SceneSystem/instances` | Present | Absent | Absent |
| Fred entry/choice names in saved inspection services | Present | Absent | Absent |
| Fred inner-owner Entries / Exits | 2 / 1 | 2 / 2 | 3 / 2 |
| Fred SceneRequests counter | 1 | 1 | 1 |
| Fred wrapper OwnerActive | 1 | 1 | 1 |
| Subsequent matching-position load diagnostic | Oct 24, 19:09:22: `scene=true` | No matching load diagnostic used | Oct 25, 11:23:59: `scene=false` |

The saved instances count falls from 20 to 19. AutoSave 15 includes the exact
64-bit depot-path hash of Fred's PTFR scene and its `#wat_sm_lch_melee_01`
marker. Its inspection-services data also names
`wat_lch_melee_01_default_start` and `wat_lch_ch_wat_lch_melee_01_ch_main`.
AutoSaves 16 and 17 have byte-identical instances blobs. The first 19 records
are not byte-identical between AutoSave 15 and 16, so this is not a controlled
experiment in which only Fred changed.

The counters distinguish an enabled vendor wrapper from an actual scene:
AutoSave 16 records a completed departure, and AutoSave 17 records another
nearby owner entry without another scene request. A wrapper can remain active
while waiting for its distance condition.

At the later apartment visit, the log also shows scene membership switching
false/true around interactions, including the mirror. This rules out a boolean
that is permanently stuck true across every observed session; those later
interaction transitions are not evidence that Fred caused every `scene=true`.

## Activation path found in installed resources

1. `PTFR.B0StoryServices.StoryServiceDriver` enables Fred's restored service
   after its Tower and safety prerequisites pass, provided the original
   `wat_lch_melee_01_default_on` gate is available.
2. The Fred questphase's outer node 17 waits until V is less than 100 metres
   from `#loading_conditions_ent_wat_lch_melee_01`. Its inner phase activates
   Fred's spawn set, then node 4 waits until V is less than 50 metres from
   `#wat_lch_melee_01` before requesting the scene.
3. In the installed S25 override, node 301 chooses the original vanilla scene
   only for its issued, nonfaulted fresh boxing owner. The other branch starts
   the private PTFR Fred scene at node 3. The saved scene hash identifies the
   private branch in AutoSave 15; missing serialized S25 facts alone would not
   establish a runtime branch value.
4. The private scene declares Fred as actor 0 and **V as player actor 1**,
   acquired from the `Player` context. Its modified service entry goes from
   node 1 to section 96, which references both actor IDs, then to the trade and
   small-talk choice loop. This service route has no reachable scene-end node;
   the owner controls departure.
5. The inner owner's node 5 waits until V is more than 100 metres from the
   loading marker, deactivates Fred's spawn set, increments Exits and reaches
   its terminating output. The distinct entry/exit distances explain how a
   scene requested near Fred can remain present after V walks farther away.

These are two different distance targets, not a measured radius around the
apartment door. No current runtime distance or actor-ownership table was read.

The current private scene SHA-256 is
`9BE6FC14EF8A24FFAE956B682308423FDF2B90986803C6300E0289479AA51C15`.
The installed S25 Fred questphase SHA-256 is
`06DE4B05E7325614D9DB4AE7FB17D3F1C1D35D1AF188AF1B587F7325E999A2AF`.
The main archive also contains the earlier Fred owner; both were extracted
read-only, and the newer S25 override was examined explicitly.

## Conclusion and limits

Fred is a **high-confidence source candidate**, supported by the saved scene
identity, player binding, owner graph, departure counters and later false
query. This is not a captured engine call stack or a decoded live
entity-to-scene ownership table. WolvenKit exposes these SceneSystem save nodes
as opaque blobs; matching resource hashes and stored names does not fully
decode their runtime actor state. Other saved scene records also change.

The evidence supports keeping H4's distinction between ambient membership and
actual loss of player control. Do not clear global scene state or remove V from
Fred's scene without auditing the retained dialogue and player references.
For the planned explicit H10 dialogue-style purchase interaction, retain the
exact door/context, dialogue, combat, control and payment guards rather than
reintroducing a blanket scene-membership veto.

If direct runtime attribution is needed before changing Fred, observe the
read-only query alongside his SceneRequests/Entries/Exits while approaching
Fred, leaving the native departure range, and returning to H10. No manual fact
changes, owner restarts or save edits are needed for that check.

Private evidence is under `diagnostics/scene_membership_20261025_01/`:
hash-verified save/log copies, parsed save-node blobs, saved fact tables,
installed native resource exports, graph summaries and `assessment_01.json`.
All 265 original save-folder files and all 117 installed PTFR files remained
unchanged. No game launch, deployment or public release occurred.
