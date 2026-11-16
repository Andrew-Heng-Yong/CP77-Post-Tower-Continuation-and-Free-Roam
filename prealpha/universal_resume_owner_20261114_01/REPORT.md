# Go Your Own Way through Tower cleanup

14 November 2026. Exact graph and save readback identifies the ordinary pre-ending owner of Go Your Own Way and the separate S23 entry that remains registered after the cut. A workspace diagnostic records those owners, Hasan's dialogue phases and the original timer at the q307 cutoff. There is no captured live playthrough with the timer pending yet.

## Connected paths through EP1 cleanup

| Phase | Full address | Evidence |
| --- | --- | --- |
| Original quest | `[1,0,10,5,14,5]` | The open-world branch enters the world stories through node 14. The EP1 cleanup condition reaches cut node 9, which cuts parent 5 before the native killed receipt. |
| Vehicle bugfix reference | `[1,0,10,2,3,16,5,6,14,5]` | Parent 2 is outside that cut. Its only connected input into the copy of `ep1_open_world` is `CP77-63752` at node 47. That input routes to the vehicle phase at node 29 with no graph edge to world stories. The resource reference alone does not run Hasan's quest. |
| S23 replacement quest | `[1,19107,100,5]` | ArchiveXL attaches the existing `hasan_boot` beside the ordinary EP1 phase. The boot waits for its permit, records issue and entry, then calls the stock quest and a separate Hasan default-dialogue loop. Its current admission requires the Inactive journal and the existing prerequisite facts. |
| Default dialogue | `[1,0,10,4,1,9]` → `[1,19107,100,9]` | The early saves contain two registrations for the original default dialogue. The cut retires parent 4. The installed S23 route can later claim the same dialogue resource from its own phase. Other source references to that resource are tracked separately. |

Manual Save 26 and the pinned first hospital save contain the same original quest slot for node 81. That node's `travelling_merchant_lives > 999` wait has no outgoing edge. Its registration establishes the presence of the original phase and gives no evidence of a pending story timer. The later hospital and after-credits samples retain the original path in their catalogues and contain no registration for that phase or the original default dialogue. S23 node 2 stays registered in all six samples. There are no S23 quest or dialogue child registrations in those samples. [Saved registrations and paths](evidence_03/assessment.json)

The later hospital save contains **52 queued quest notifications for 40 physical slots**. None resolve to a watched Hasan phase in that save. This is a direct reminder to tie a handoff to the affected slot and drain boundary. The root cut and the saved result do not establish a point when all quest queues are empty. [Queue readback](evidence_03/assessment.json)

## Timer and surrounding state

The quest starts a 3-day, 16-hour game-time wait at node 47. The later one-hour real-time wait at node 69 begins when Mr. Hands' choice group is activated, in parallel with two claimable reply listeners. At expiry, the graph checks both replies before inactivating the choice group. Visiting the apartment can also inactivate that group. The later phases use Hasan's dialogue, the `#wst_ep1_05_com` community and the original gun variants and inventory check leading to `wst_ep1_05_gun_taken`. Preserving just node 69 cannot reconstruct those parallel branches, the phone state or the gun receipt. [Graph contract](evidence_03/assessment.json)

The native probe records actual child creation and removal at the engine calls that own those handles. It matches a registered handler to its full phase path, handler map and physical slot. It records original, bugfix and S23 timer samples independently on the delay worker and logs relevant Tower and S23 fact transitions. The REDscript overlay can save a diagnostic record of the normal original real-time wait just before the existing direct Tower acknowledgement. The native reader rejects a record when a competing owner also has a current timer sample. The record remains diagnostic evidence until the live owner, parallel replies and world support can be qualified. [Probe](CutoffProbe.cpp) · [Save-local sample](cutoff_members.reds)

## Validation and remaining live check

The workspace build passed **27 isolated checks**, verified **19 native hook prefixes**, matched **14 unique providers across 137 archives**, and checked **six** saved projections. The cutoff script compiles against all **148** installed script sources. The probe uses the same pinned Cyberpunk 2077 2.5 executable as the timer fixtures. No deployment, full ending run, timer suspension, gameplay restore or save writes occurred. [Build receipt](build_05/build.json) · [Validation](evidence_03/assessment.json) · [Script compile receipt](compile_01/receipt.json)

The read-only fixture search checked current Manual Saves 23 through 27 and AutoSave-0. All six parsed and matched their original hashes after inspection. Manual Save 26 was the only pre-ending body in this selection and contains only the independent node 81 registration for the quest. The five other bodies have Tower completion and retirement facts. None contains the target real-time wait. [Current save search](fixture_search_01.json)

A live qualification needs a genuine pre-Tower save with Mr. Hands' choice group open and node 69 still pending. The trace can then identify the exact original registration and remaining duration before journal cleanup and observe its retirement and the S23 entry through credits. The game-time clock and coordinated restoration of the reply listeners, journal and world ownership remain open.
