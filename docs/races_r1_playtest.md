# R1 — stock repeatable-race interaction playtest

Candidate covers the four **repeatable** races: City Center, Badlands,
Santo Domingo and Westbrook. It does not restart Claire's story quest.
Installation/live status is recorded separately in `research/races_r1/assessment.json`.

**15 October update: user-reported functional pass.** The user reports the test
passed using Johnny's car and no Johnny appeared. Exact route, voice delivery,
all four starts, payout, repeat and reload coverage were not specified. Preserve
R1; do not repeat basic startup merely to reconfirm this result. Evidence:
`research/races_r1/live_result_20261015.json`. The checklist below remains for
unverified coverage.

## First short check

1. Cold-launch after installation. Load your normal working **post-Tower** save,
   preferably the untouched save made **before** the cyberpsycho disposable-test
   command. Do not overwrite that save or replay the ending for this check.
2. Close CET and menus and stay out of combat. Visit the City Center race start
   marker on foot. Look for the stock **wait/start race** interaction.
3. Use it and check that the waiting transition, announcer and starting grid
   appear. A visible map icon alone is not a pass.
4. If convenient, finish one race; verify checkpoints, opponents, placement,
   reward and return to ordinary gameplay. Do not force win/reward facts.

The stock prerequisite is `sq024_done > 0`. A previously delivered race
invitation resumes the available-races controller without resending the SMS.
If no delivered invitation is recorded, the original **three in-game-day**
invitation delay and content-availability checks remain. No timer is forced.
Santo Domingo retains the native `mq059_freedom_active` exclusion. Native
courier/race coordination and waiting-area conditions are also retained.

Read-only CET diagnostic if no prompt appears:

```lua
local q=Game.GetQuestsSystem(); for _,f in ipairs({"PTFRR1_Ready","PTFRR1_Issued","PTFRR1_Resumed","sq024_done","mq056_test_drive","mq056_cour_active","mq056_active","mq056_prevention_fail"}) do print(f.."="..q:GetFactStr(f)) end
```

`Issued=1` means the controller was admitted, not that a rendered prompt or race
has worked. `Resumed=0` can mean the original invitation path is still running.
For `Issued=0`, send the values; do not clear guards. Interrupted old races and
active saved race phases are intentionally not migrated/reset by this revision.

## Deferred coverage

- All four starts, including Badlands vehicle requirements and Santo Domingo's
  native activity exclusions.
- Finish/payout once; loss/abort/prevention interruption and stock cleanup.
- A second race after its native rearm/cooldown, without repeated payout.
- New disposable save and reload before start, during a race and after finish.
- Johnny's permitted voice lines still play, with no visible body or detached
  props. The existing JV1 visual policy is unchanged; new scenes need live proof.
- Claire's Afterlife service/outcome remains unchanged.
- Regression: courier contract, NCPD, airdrop, gigs, H10, nerfs and ending handoff.
- Fresh pre-ending -> Tower -> post-ending integration remains separate.

No custom race rewards, forced story unlocks, automatic save/reload or periodic
CET output are added. After testing, load the untouched normal branch if you
do not wish to retain race progress.
