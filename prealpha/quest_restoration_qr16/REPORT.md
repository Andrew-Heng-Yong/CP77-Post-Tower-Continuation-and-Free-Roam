# Brendan earned-history continuation

This stage moves from Jason Foreman's deferred adapter to the next actionable source investigation in the QR13 development queue. The scope is the earlier timed stages around Spray Paint, including the six-hour handoff to Coin Operated Boy. QR13:02 already covers one narrow, earned peaceful final-Theo case. [Prior Brendan implementation](../quest_restoration_qr13/REPORT.md)

## What the vanilla repair inputs do

| Input | Actual authored route | Disposition |
| --- | --- | --- |
| `CYB-640323` | Bugfix `root/14:21.False → 13.CYB-640323` targets body `root:61 → 23`, then `root/23:25 → 5`. At `root/23/5:54`, `mq037_post_girl_scene_on > 0` suppresses the connected False branch. The False branch arms proximity wait `17`, one-hour delay `26` and crowd action `44`. | This route can restore a narrow missing Theo follow-up, with a new authored delay. It has no input for preserving an existing timer's remaining duration. |
| `CYB-661474_girl` | Bugfix `root/38:12.Out1 → 7` targets body `62 → 23 → 5 → 55`. Scene input `1716` goes directly to terminating exit `1717`. The quest output feeds the cuts at `root/23/5:56` and `root:66`. | Scene and phase cleanup. The route has no connected continuation into Spray Paint. |
| `CYB-661474_hooligan` | Bugfix `root/38:10` requires Theo spawned and Spray Paint Succeeded or Failed. It enters body `63 → 25 → 62`, cuts scene branches `2/8`, then cuts parent handlers `105/13/78` and emits a terminating output to the body-level cut at `67`. | Terminal encounter cleanup. It does not resume an unfinished hooligan encounter or enter the six-hour handoff. |

The ordinary successful Spray Paint route marks the talk objective and quest Succeeded at `root/25:51/52`. It reaches checkpoint `37`, then starts the six-game-hour wait at `38`. Once that completes, `39` waits for the player to leave `#mq037_tr_quest_area`. Node `40` deactivates the hooligan community and `36` makes the POI Inactive. Its output eventually enters `root:28.In1`. Spray Paint Succeeded therefore covers time both before and after the six-hour wait. POI inactivity by itself also lacks timing evidence because `101.Out1` can reach `36.Inactive` separately. The machine result retains this route, the exact delay payloads and the other nearby timer branches. [Graph evidence](analysis_02/result.json)

## What the selected save shows

The selected November 4 AutoSave-8 has `CYB-640323=1` and `CYB-661474=1`. Vanilla writes both one-shot markers **before** testing the relevant journal or actor conditions. On reentry their `>0` branches have no outgoing edge. These values block those vanilla bugfix checks from running again and supply no evidence that either repair ran or that Brendan's progression was earned. The same save has private `Ready/Issued/Entered=1`, which supplies no native progress or clock position.

The source-bound saved registry has six interned paths under the original quest owner `[0,2,82,6,34]` and nine under its original bugfix companion `[0,2,82,4,9,3,55]`. Neither subtree nor its immediate owner slot has a retained registration. All seven exact original timer addresses also lack a retained registration. These are results for the selected body. They cannot distinguish an earlier timer that completed, a wait that was cut, or a wait that never began.

The existing QR12 inventory retains no record for the four queried native Brendan progress facts across 171 distinct save projections. This is a check of its already extracted named-fact projection. Journal and clock data outside that projection could still contain relevant evidence. No fresh earned-history fixture was established.

## Disposition and next evidence

Keep the earlier timed stages held. The installed wrapper's only connected entries into the vanilla body remain the existing `34.In1` path and QR13's `34.CYB-661474_reinject` final-Theo path. A future timed adapter needs a genuine earned fixture with an exact original wait and its remaining duration, or a positive post-wait stage with an independently safe continuation. It also needs the original encounter ownership and outcome preserved. A terminal journal value, an inactive POI, or a one-shot bugfix counter cannot select that route. No runtime candidate or immediate human test qualifies.

## Reproduce

Run from the workspace root with the existing Python, QR13/QR15 source captures, installed archive and selected save:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr16\analyze.py' --out analysis_03
```

The analyzer checks the source and capture hashes, binds the installed Core epoch, reads the save and metadata hashes before and after, and writes only the fresh result. Three edge-removal controls detect a missing delay arm, missing scene cut and missing hooligan cleanup cut. The final preservation check rehashed all 77 pinned installation paths and six protected save files. [Completion receipt](completion.json)
