# Automatic pre-Tower history test

The local install replaces the two snapshot scripts in `QP2_QUEST_HISTORY_TEST`. The 12:10:56 p.m. Toronto crash reached `SnapshotStateHS1.Allows` line 3023 with the override inactive. The VM attempted to index a field of the temporary struct returned by `AdmissionRow`. The repaired build indexes the backing rows directly and returns primitive values to admission checks. The SCC output decompiled to direct indexing on both history paths. [Source diff](candidate_01/source.patch) · [Crash readback](crash_readback.json)

Load **AutoSave-2** at Viktor and finish The Tower in that session. Its saved snapshot flags have been cleared, and the save still contains the exact 80,702-byte revision 159 history payload. After the genuine ending and retained-session handoff, the game serializes that retained history and CET compares every row with the original revision 159 file. A match selects revision 159 in the same acknowledgement that releases history-dependent admission. The canonical post-ending export remains a record of the current journal. CET logs `Using verified pre-ending revision 159 for this session.` The test selection needs no console input and is recomputed on reload. [AutoSave-2 readback](autosave_2_readback.json)

## Remaining quest stages

**Moving Heat**, **Beat on the Brat**, and **The Gig** match the recorded first-door, pre-bout and pending tattoo reward inputs except for the live Failed root. Their script and quest graph checks both require Inactive. **Epistrophy** also needs an adapter for the unfinished Northside introduction. **Small Man, Big Mouth** needs an earned Meet Kirk entry instead of its fresh start. These are eligibility findings. Saved-owner retirement, cleanup and reward qualification still need review. [Stage and graph checks](../quest_history_test_20261112_01/REPORT.md)

**Machine Gun** was at Deliver Skippy to Regina. The installed adapter expects the earlier stage before the owner reveal, Inactive journal entries and the exact old counters. Revision 159 records the known owner and counts 12 lethal, 52 nonlethal and 97 total. In the matching vanilla return graph, node 11 starts the delivery journal, the Regina office and intercom marker chain, and the original return scene listener. The native `DeliveryTestIn` socket runs node 30, which grants a Skippy, before node 63 sets the owner-known fact and starts delivery. A delivery adapter needs the original downstream inventory checks, scene, markers and cleanup with the existing weapon. SC3's ambient owner needs its existing stop acknowledgement before a story owner can take over. The return scene, device and saved-owner path still require review. [Vanilla return graph](../../research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json) · [SC3 handoff checks](candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds)

All six interrupted gigs have Active rows in the exact indices used by `FreshU9`. The live gig entry guards also require Inactive state. No installed progressed-stage route was established for these objectives. The snapshot indicates what the player earned before the cutoff. Native owner and reward traces are still needed for each case.

| Gig | Active objective at the cutoff |
| --- | --- |
| Dancing on a Minefield | Find the car |
| A Lack of Empathy | Get inside the server room and avoid combat. Getting into the club was already complete. |
| Rite of Passage | Get to the clinic |
| Many Ways to Skin a Cat | Get inside |
| Talent Academy | Meet Mr. Hands’ contact |
| Treating Symptoms | Get inside the complex |

## Verification

All 148 registered REDscript sources compiled offline. Eight Lua fixtures covered exact automatic selection, reuse of an existing export, missing or mismatched evidence, the ordinary capture path and reload during comparison. Nine installer actions passed. The real deployment and rollback readback verified all 51 Core files, 26 dependencies and 349 byte-identical save files. The game has yet to run the repaired build through the AutoSave-2 ending. [Installed manifest](deployment_01/installed_manifest_01.json) · [Compile result](compile_01/result.json) · [Lua fixtures](candidate_01/test_readback.json) · [Deployment fixtures](fixture_results.json)
