# Raymond Chandler Evening: RC2 local test repair

**Installed locally on 26 October 2026. Entry appeared after the original 12-hour in-game delay; later quest play remains untested.** This is an unreleased successor of the 51-file combined Post Tower Continuation and Free Roam package. It replaces only the existing combined archive and `PTFR_SideJobsS29.reds`; it adds no installed paths.

## Observed problem

On the user's post-Tower save, `mq040_active=1`, `mq040_done=0`, `mq040_pepe_intro=0`, `mq040_gangers_scene_done=0`, `elcoyote_barman_default_on=0`, and `PTFRB0STPEPE_OwnerActive=0`. Pepe and the bar encounter actors are physically present but idle. S29 considered the journal inactive and rejected the job because its fresh-entry guard expected `mq040_active=0`. The earlier CET RTTI probe was invalid and supplies no evidence. The original native owner's current liveness remains uncertain; the save's `q307_main_game_killed=1` does not settle that question.

## Scoped change

RC2 admits `mq040_active=1` only when the barman default owner and PTFR Pepe owner are both off and the other original journal/progress guards pass. It checks this condition over two settled ticks. In the private MQ040 graph, the fresh `active=0` route keeps the original setup path. The stranded `active=1` route skips setup spawning and enters the existing native bar phase with the actors already in the world. It does not clear facts, restart the global quest initializer, or alter official game resources.

The full combined archive retains all 1,172 members; exactly two private MQ040 resources changed. All 30 earlier CR1 repairs and the other 1,170 members remain byte-identical. The second changed install file is the existing S29 REDscript. This is a targeted local test repair, not evidence that every MQ040 branch or an already serialized native owner behaves correctly.

## Live finding after installation

The user's first post-install inspection showed `ready/permit/issued/finished=1/1/1/0`, `entered=0`, and `currentMatch=true`. Thus the repaired admission succeeded, but the native parent had not yet entered the bar phase. Source tracing then found that the copied vanilla parent retains a **12-hour game-time delay after the Heroes prerequisite**. S29 starts that delay when it issues its new owner, even when `mq040_active=1` indicates that the original setup had already begun. The user skipped 12 in-game hours and reported that **the quest came back**. This confirms the entry handoff on their current fixture after the wait. It does not confirm all dialogue, rewards, completion, or reload. The current RC2 install deliberately remains untouched while the user tests those parts.

## Verification

- Full 64-source compilation with installed public Codeware 1.21.1: pass.
- Quest graph and admission truth-table checks: pass. No external mod archive collision on either changed resource path.
- Full 51-path package hashes checked against the installed CR1 predecessor before replacement; archive member readback: pass.
- Installer: 38 disposable fixture actions passed, including six interruption points, partial-stage recovery, later modification refusal, full package verification, and rollback.
- Actual closed-game install and 51-path verification: pass. All 301 save file names and hashes remain unchanged. `ValidateRollback` reports ready.

The complete unreleased package is [RC2 ZIP](../prealpha/raymond_rc1/candidate_03/dist/Post-Tower-Continuation-and-Free-Roam-RC2-unreleased.zip), SHA-256 `EC133E6CF8CC3A56196D95309B0B4F3E7462538A6B385EFB79D331736B28F8B7`. The selected manifest is `prealpha/raymond_rc1/candidate_03/install_manifest_03.json`, SHA-256 `77C8F53307DA42229E8006C6AE3D4FA193D600D41EBAE5C3E2ED1E3CB2199CBF`. Previous installed versions are in `recovery/raymond_rc2_01`. A first sandbox-denied attempt changed no game file; its rollback receipt is retained separately in `recovery/raymond_rc2_interrupted_01`.

## Live test and rollback

On another affected post-Tower save, allow 12 in-game hours after RC2 issues the quest, then approach Pepe and the Valentinos in El Coyote. The user has confirmed the quest returns on one fixture after Skip Time. Check whether the confrontation and conversation start, journal becomes active, choices and reward complete, and a new manual save reloads correctly. Watch for doubled actors or a second scene: the old native owner's liveness could not be proved from the captured facts. Do not force MQ040 facts from CET for this test. A future successor could avoid this repeated delay for proven prestarted setup states, but that change is not installed or validated.

If the scene duplicates or stalls, close the game, run `prealpha/raymond_rc1/deploy_03.ps1 -Action ValidateRollback`, then `-Action Rollback`. Roll back RC2 before CR1 or older layers. File rollback does not undo progress saved by the game after RC2 was installed. No GitHub Release was created.
