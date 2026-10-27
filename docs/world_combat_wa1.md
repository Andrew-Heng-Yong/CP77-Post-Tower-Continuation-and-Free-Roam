# WA1: Gated Pacifica combat-event controller test — 26 October 2026

The user's before/after CET samples identify the **same** `goon1` Scav record,
spawner ID `13399962301655001666`, and community at the same Pacifica location.
The actor patrols before Tower and animates in place after Tower. The community
is active in both saves. Reissuing Codeware `ActivateCommunity` changed the
post-ending group but did not restore patrol; the user was told to reload the
disposable test without saving.

The original `open_world_content` combat-event owner ends with the Tower main
story. Its nested `#ce_pac_cvi_116` loop immediately issues `Reactivate`, then
waits for two kills and a random 12/24/36-hour game-time cooldown before a
proximity-conditioned `ResetKillCount` and repeat. The loop has no explicit
patrol command. Its loss is a plausible controller-lifetime cause, not yet a
confirmed cause of the idle symptom. Restarting all 16 districts would disturb
many completed encounters, so this candidate tests **one** original loop.

`prealpha/world_combat_wa1/candidate_04` is a **diagnostic successor**, not a
production behavior fix. It has the same 51 installed paths as JC1. The only
replaced game files are the combined archive and its XL file. One private
questphase was added inside the archive; all 1,172 previous resource payloads
are byte-identical. The private graph preserves all 11 vanilla nodes and 12
continuing edges, and places a pause condition before the original entry.
The gate requires `q307_main_game_killed=1`, `q307_ep1_killed=1`, and the
new disposable-test fact `PTFRWA1_TestRequest=1`. With the request unset, the
loop does not reactivate the group.

The full 64-source SCC compile passed. Archive member readback (1,173),
semantic node/edge comparison, unchanged 51-path manifest, new-path collision
scan against 67 other mod archives, and 38 deployment fixture actions
including six interruption points passed. Actual closed-game Install, Verify,
and ValidateRollback passed. The 301 pre-install save files remained unchanged.
The 20 autosave folders were copied into
`recovery/world_combat_wa1_01/autosaves_before_test`; all 60 files matched
source hashes at backup time. Previous installed files and receipt are in
`recovery/world_combat_wa1_01`. Installed archive SHA-256 is
`2F34E84042D6045B69A0E430C535D42F1A1CF824B78BF49AA7C3E3978BB896E3`;
XL SHA-256 is
`35114107AF2E137724DA71696B9871B427204D55D4CF96C61A0A5C4CCB4684BF`.

Live test was performed on a disposable post-ending load. The user stood
away from the Scavs and ran:

```lua
Game.GetQuestsSystem():SetFactStr("PTFRWA1_TestRequest",1)
```

The user reports **still idle**. Rehosting this exact native loop did not
restore patrol. The later offline audit found that WA1 omitted the enclosing
node's `phaseInstancePrefabs=[#ce_pac_cvi_116]`: it copied only `PhaseGraph`.
The result therefore does **not** reject missing native prefab/workspot
ownership as the cause. The game
was closed and WA1 file rollback completed; JC1's full 51-file package
verified. No production fix or GitHub release is claimed.

The game automatically rewrote `AutoSave-18` and `user.gls` during the test.
The test version of `AutoSave-18` is archived in
`recovery/world_combat_wa1_01/test_autosave_18`. Its original three files
were restored from the verified pre-test backup. A full rehash found all 300
other baseline files matching except `user.gls`, which changed with the game's
autosave operation. The current `user.gls` is archived as
`recovery/world_combat_wa1_01/user_gls_after_test.gls`; there was no prior
byte copy from which to restore its previous contents. Do not hand-edit this
index. File rollback does not undo any unrecorded in-session state, but the
restored autosave slot itself matches its original hashes.

The WA1 build remains workspace-only for diagnosis. Its negative live result
shows that community activation and the one-group combat loop alone are
insufficient. Fresh source and saved-state analysis now maps all three sampled
Scavs' saved workspot tokens to nodes in the omitted quest prefab. The native
community spawn area is separately retained in default world data. The follow-up
investigation is documented in [the hostile NPC report](world_hostile_idle_report_20261026.md).
The user has explicitly stopped further in-game test requests; continue with
source, archived saves and offline verification.
