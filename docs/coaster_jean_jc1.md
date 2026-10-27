# Jean's Love Rollercoaster entry: JC1

**Installed locally on 26 October 2026; live quest play remains pending.** JC1 is a successor of the complete 51-file Post Tower Continuation and Free Roam package. It replaces the existing combined archive and `PTFR_SideJobsS29.reds` paths, adds no game files, and leaves saved quest facts unchanged.

## Observed blocker

On the user's post-Tower save, `SideJobsS30:Inspect("mq006_rollercoaster")` reported `ready=1`, `permit=0`, `issued=0`, `finished=0`, `fault=0`, `entered=0`, `baselineFresh=true`, and later `safe=true`. The refusal was `mq006_ride_no_quest=1 expected=0..0`. The user had **not** ridden the coaster. Their other checked MQ006 completion, repair, repeatable, and PTFR coaster ownership facts were all zero.

The shipped MQ006 graph sets `mq006_ride_no_quest=1` on its standalone-route setup before V rides. That flag alone is therefore not evidence of a completed Jean story. The previous S30 fresh-entry guard rejected an otherwise eligible save. The original scene also used the same flag for five no-quest finale choices, so relaxing the guard alone would risk choosing the wrong dialogue.

## Scoped repair

- The two private S30 entry guards and S30's read-only fact range now accept `mq006_ride_no_quest` values **0 or 1**. All other journal, completion, repair, repeatable, and owner-lease conditions remain.
- The five no-quest choices in the **private Jean finale scene** now test `PTFRWORLD_Coaster_QuestOwns==0`. JC1 sets that lease before its one-time native story and releases it after the native root returns. The saved native `mq006_ride_no_quest` fact is neither cleared nor overwritten.
- Existing issued/completed quest owners are never restarted. The independent repeatable-ride controller still has its own exclusion gate.

## Verification and limits

The original private finale JSON reproduced the RC2 binary byte for byte before modification. The serialized candidate scene differs in exactly 15 values: the comparison, fact name, and value in each of the five conditions. The entry graph differs only in the two ride-flag ranges and their added lower-bound checks; the S30 REDscript has one fact-range table change. The complete 1,172-member archive packed and extracted byte-exactly, and all 51 package files were checked. The full 64-source REDscript stack compiled with public Codeware 1.21.1.

The deployment fixture passed 38 actions, including six injected interruption points, partial-stage recovery, full-package verification, and rollback. A read-only scan found no collision for the two changed resources among 67 other installed mod archives. The first actual install attempt was denied while copying the staging file into the game folder: both installed files remained at RC2 hashes, rollback validated and completed, and that interrupted backup was archived separately. The elevated retry installed JC1; `Verify` checked all 51 installed paths and `ValidateRollback` reported ready. All 301 save files matched the preinstall hashes. The assistant did not launch the game, edit a save, set a quest fact, push GitHub, or publish a release.

Complete unreleased ZIP: [JC1 package](../prealpha/coaster_jean_jc1/candidate_01/dist/Post-Tower-Continuation-and-Free-Roam-JC1-unreleased.zip), SHA-256 `6AC85EA6A325DF78FEA39101C4313C4EAE39B17B676E74E0F2EF59316E36C431`. Source, static checks, compilation, deployment fixtures, and pinned installer manifest are under `prealpha/coaster_jean_jc1`.
The [assessment](../prealpha/coaster_jean_jc1/assessment_01.json) pins these checks with SHA-256 `B52D0DC4ABF87245A998CBFCEBACD027412B35FD80CA983C33F1AB382ADE8555`.

## Live test

Cold-load the same post-Tower save, stand in ordinary safe gameplay on foot, and inspect S30 again. After the settled ticks, `permit` and `issued` should become 1 while the native `mq006_ride_no_quest` stays 1. Approach Jean's group at the Pacifica coaster by the Grand Imperial Mall. Verify the introduction, repair objective, ride, Jean finale, reward, and a manual save/reload. Watch for a second cart or duplicate actors: static facts do not prove the previous vanilla standalone owner is retired. If entry does not issue, capture S30 Inspect and CET `gamelog.log` before altering any facts.

For file rollback, close the game and run `prealpha/coaster_jean_jc1/deploy_01.ps1 -Action ValidateRollback` then `-Action Rollback` **before** rolling back RC2 or older layers. The prior RC2 files are in `recovery/coaster_jean_jc1_01`; the earlier denied attempt is retained in `recovery/coaster_jean_jc1_interrupted_01`. File rollback does not undo save progress made during a live test.
