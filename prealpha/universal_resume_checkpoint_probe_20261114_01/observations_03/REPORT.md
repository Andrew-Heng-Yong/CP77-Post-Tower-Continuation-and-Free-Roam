# v0.1.4 Reed cutoff capture from Manual Save 26

14 November 2026, Toronto time. The user resumed the live Step 2 test. At 22:43:25 v0.1.4 observed the inline writer, captured route 1, ticket 1 and history revision 4, and logged the save-local execution checkpoint commit before native cleanup. The CET writer independently logged its verification of the matching recovery export. [Native log](checkpoint.log) · [Game and CET log excerpts](cutoff-lines.txt)

The recovery export is 716,749 bytes with checkpoint ID `27f5fb2228de1ee652b9aeabde09705f` and SHA-256 `41B2D601602926C8128A480BFDAE63DBBD90C579B5CC1779947FB042104A53E9`. An exact local copy is retained for reload comparison. [Backup receipt](../../../recovery/ms26_v014_reed_checkpoint_20261114_01/receipt.json)

| Capture observation | Result |
| --- | --- |
| Phases and handler registration slots | 4,040 phases and 10,048 registrations |
| Sampled waits | 8 real-time and 13 game-time, with sample ages from 7 to 12 ms |
| Epistrophy AND node 198 at `[0,2,82,5,48,79]` | One matching phase and one table-4 row at key `3673229151` |
| Saved partial input mask | 70, matching Manual Save 26 with In2, In3 and In7 signaled and four inputs pending |

The user set 3× time dilation at 22:45:40, after this capture. Capture and export passed for the observed Reed route. Step 2 also requires a genuine post-Tower manual save and reload with the same checkpoint. That result will be recorded separately. [Pinned MS26 control](../../quest_resume_contracts_rc2_20261114_01/analysis_06/saved_witness.json)
