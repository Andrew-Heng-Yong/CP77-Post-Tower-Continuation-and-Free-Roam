# Quest snapshot cutoff repair

11 November 2026. One REDscript replacement for the installed QP2 build. Offline verification passed. Installation and in-game qualification are pending.

## Native quest mutations

| Stage | Traced operation |
| --- | --- |
| Rooftop commitment | In `q307_01_pickup.scene`, nodes 2777 and 2781 write `q307_point_of_no_return=1`. Node 2777 leads to node 2029, which writes `q307_confirm_av_start=1`. The scene graph establishes the order even though the two fact messages appear in the opposite order in the game log. |
| Direct Reed pickup | In `q307_01_pickup.questphase`, root nodes 11 → 43 → 56 → 47 react to q307's cutoff. With `q115_point_of_no_return=0`, node 47 enters inline phase 10. Its nodes 96 → 99 → 97 restrict the phone, wait for `holo_setup_started=0`, and wait 500 ms. Node 169 then removes contacts except Reed and Viktor. Node 59 starts the bulk journal updates. |
| Bulk journal updates | The chain marks Active base-game and EP1 quests Failed and propagates those changes. It covers main jobs, minor jobs, gigs, other activity folders and selected meta quests. It also makes Active points of interest Inactive. Node 62 covers Beat on the Brat and Small Man, Big Mouth under `quests/minor_quest`. Node 128 covers Moving Heat under `ep1/quests/minor_quest`. When q115 has already crossed its cutoff, q307 takes node 47's True branch to the separate Sickness update. |
| Coma and hospital | After AV departure, the coma sets `air_traffic_off=1` and the 2079 internet phase updates its journal entries. At the hospital, the success of `q307_before_tomorrow` releases the base-game and EP1 shutdown paths. Base `cyberpunk2077.questphase` nodes 106 → 109 → 107 write `q307_main_game_killed` and terminate. The parallel `q307.quest` path 16 → 18 → 17 writes the same fact and cuts its base-game child. EP1 inline phase 10 nodes 8 → 9 → 10 cut the original children and write `q307_ep1_killed`. |
| Ending cleanup | `q307_cleanup.questphase` writes `q307_active=0`, `q307_done=1`, and `q307_finished=1` before the final boards. These are later than the journal changes and native root cuts. |

The provider check searched 134 installed archives. All 16 stock trace resources matched the pinned vanilla payloads. The existing combined archive also supplies an override for the later final-boards phase. The four observed saves are from the same playthrough. Beat on the Brat, Moving Heat, and Small Man, Big Mouth have matching journal path hashes and raw state fields of 2 in ManualSave-26 and 4 in AutoSave-10. Those values agree with the native Active and Failed enums and the traced bulk writers. AutoSave-10 is the first hospital checkpoint and precedes both native root-kill facts. The three records are byte-identical in AutoSave-11 after both kills. The save comparison spans ordinary gameplay as well as the ending transition. [Provider evidence](evidence_01/native_providers.json) · [Game log excerpt](evidence_01/runtime_timeline.json) · [Save facts](evidence_01/save_checkpoints.json) · [Journal records](evidence_01/journal_comparison.json)

## Snapshot behavior

QP2 had captured revision 161 as `pre_ending_candidate` on the observed run. Its only freeze attempt required a sample at most six seconds old and a settled journal. The five-second refresh interval plus two batched reads can leave a gap in that age window. The exact failed predicate on this run was unlogged.

At the direct Reed cutoff the repair rechecks the last settled, same-session pre-ending sample immediately. That path uses exact row equality in place of the six-second age test. A pending journal update or delayed fact readback can retry during pickup, up to AV departure. Each retry compares against the already captured pre-ending data. A row that differs remains uncertain, including any row already changed by the native bulk update. The single expected difference is the cutoff fact's observed transition from 0 to 1. The stored value stays the sampled pre-ending value. A restore clears the pending attempt, and a save that already missed the cutoff remains eligible for the existing, separately labelled post-ending fallback.

The replacement preserves the 158-row catalogue, persistent layout, JSON format, exporter, and admission methods. Moving Heat and Beat on the Brat's current resume adapters still require Inactive live roots. Small Man, Big Mouth's fresh entry requires an Inactive baseline. The observed Failed roots and the unsupported Active Small Man stage remain separate from the capture repair. [Source patch](source.patch)

## Verification

The targeted checks passed against the pinned pickup scene and phase, the matching save records, and the exact staged script. SCC compiled all 148 registered sources offline with the one-file overlay. The 51 installed Core files, 26 dependencies, compiler inputs and inspected saves matched their original SHA-256 hashes. The game still runs the QP2 build. The next live check is the `pre_ending` freeze and JSON acknowledgement during a genuine Reed pickup, followed by persistence through hospital and save reload. [Checks](test_cutoff.py) · [Compile result](compile_02/result.json)
