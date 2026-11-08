# Career Opportunities transition follow-up

The current vanilla archive identifies the original early message owner. Its normal campaign ancestry is a descendant of the native base-game phase that The Tower terminates. The installed QR19 copy is wired to the retained Phantom Liberty root and waits for genuine Tower completion before it can claim the earned score. This resolves the missing static owner ancestry. A natural retained-session transition with the early score and messages already earned remains the open test.

## Normal owner and termination

| Resource | Native route |
| --- | --- |
| `base\quest\cyberpunk2077.quest` | `0.Out → 2.Start`, calling `cyberpunk2077.questphase` |
| `base\quest\cyberpunk2077.questphase` | `0.Out → 82.In1`. Embedded `82:9.Out1 → 3.Input` calls `additional_game_elements.questphase`. |
| `base\quest\additional_game_elements.questphase` | `0.Out → 19.In1`, calling `open_world_content.questphase` |
| `base\open_world\phases\open_world_content.questphase` | `0.Out → 92.In → 93.In1`, calling `ow_mini_world_stories.questphase` |
| `base\open_world\mini_world_stories\ow_mini_world_stories.questphase` | `13.Out1 → 7.In1`, calling the Watson phase |
| `base\open_world\mini_world_stories\watson\watson_mini_world_stories.questphase` | `60.Out → 63.Input`, calling `mws_wat_08.questphase` |

The native base-game phase independently wires `108.Out1 → 106.In`. Node 106 waits for the native Before Tomorrow journal to succeed, then `106.Out → 109.In` writes `q307_main_game_killed=1` and `109.Out → 107.In` reaches the **Terminating** output of the same phase that contains node 82. The marker write precedes the terminating output. The later Tower cleanup, called through `q307.questphase:30.In1`, writes `q307_finished=1` at cleanup node 20.

The archive also contains a separate `mws_wat_08.gamedef` and `mws_wat_08.quest`. That definition spawns at the apartment test marker. The test quest starts the native body from `54.Out → 48.Input` after writing `mws_wat_08_debug_run=1`, or uses its toy AV test input. The captured campaign root list contains `cyberpunk2077.quest` and `ep1.quest`. The standalone test route is separate from the campaign ancestry above.

QR19’s ArchiveXL registration attaches the S30 entry to `ep1.quest`, node `[1]`, socket `Out`. Its gates at `65003` and `65004` require both `q307_main_game_killed=1` and the later `q307_finished=1`, alongside post-Tower state and the existing private eligibility guards. The wrapper issues the private owner and enters its unchanged `64000.Input` route. The private phase retains the original contact, both message nodes, first-place gate, journal actions and reward.

## Early score and messages

`Shooter.ShooterData.arcadeScoreboardScreenTDBID` names `Shooter.ShooterScoreboard`. Its stock `arcadeScoreboardQuestFactList` contains `shooter_appeared_on_leaderboard` and the ten `shooter_position_N` entries. The stock board shows 82,500 at tenth place and 401,210 at first place. Use the actual leaderboard placement shown in-game to qualify a fixture. The current `r6/cache/tweakdb.bin` SHA256 is `0D48B6ACC1A40430AFBFF77EF41B00B7F06759C297425A6E6767F56446C6075D`.

- Native node 6 waits for `shooter_appeared_on_leaderboard > 0`. Node 68 adds the manufacturer contact, node 7 activates `congratulations_for_playing_the_game`, node 57 waits two real seconds, and node 56 activates the follow-up. Node 6 also starts the separate Trauma Team website setup branch at 83.
- Node 8 waits for `shooter_position_1 > 0`. Node 9 activates the first-place message, node 66 writes `mws_wat_08_started`, and the original objective and description lead to the native reward at 64. Reading the first-place message advances a later objective through the native visited wait at 27.
- QR8 established equal-state suppression for the existing journal message activations. The separate contact operation at 68 requests a notification. Its actual behavior with a retained contact and the pending timer/listener behavior across the ending remain gameplay observations. A duplicate contact notification or reward is still unobserved.

The frozen November 4 post-Tower AutoSave-8 extract used by QR15 contains the two ending facts. Its serialized fact table contains neither score key, and the graph stores have no matching keys for early Career nodes under `[0,2,82,3,19,93,7,63]`. This sample lacks the earned history needed for the early handoff test.

## Later playtest

Use a normal pre-Tower branch. Place on the Trauma Drama leaderboard below first and let both manufacturer messages arrive. Keep the quest Inactive and first place unearned. Record the contact and the two messages before a genuine Tower transition. Compare those same entries and any fresh toasts after the credits, then earn first place normally. Observe the first-place message and progression, claim the native rewards once, and use one reload to check persistence. The fresh-score control uses a separate no-score branch and earns the leaderboard entry after The Tower. [Persistent playtest queue](../playtest_queue_20261106_01/PLAYTEST.md)

The source shows the retirement route and a gated replacement. A patch would need evidence of a live duplicate notification, loss of an earned message, or a stalled first-place route. The later test retains a genuine score and message history so it can distinguish those outcomes.

## Evidence and reproduction

The final scan indexed 134 archives and inspected 6,469 quest and game-definition resources in the two stock gamedata archives and the installed consolidated archive. The 35 matching or targeted assets had no extraction or decode failures. The verifier passed 84 checks. [Capture manifest](capture_04/manifest.json) · [Verification](verification.json) · [Earlier journal replay analysis](../quest_restoration_qr8/remaining_blockers.json)

From the workspace root, use the installed QR19 archive and ArchiveXL file, local WolvenKit 9.1.0, and the existing QR15 extracts for the frozen-save checks. The capture and verifier take fresh output names.

~~~powershell
$stage = '.\prealpha\career_opportunities_20261106_01'
$ptfrPython = 'C:\Users\Ayong\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe'
pwsh -NoProfile -File "$stage\trace.ps1" -OutputName capture_05
& $ptfrPython -B "$stage\verify.py" "$stage\capture_05" "$stage\verification_02.json"
~~~
