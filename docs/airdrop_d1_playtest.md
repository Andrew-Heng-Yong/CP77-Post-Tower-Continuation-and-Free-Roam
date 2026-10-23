# Dogtown airdrops — D1 playtest

Installed 14 October 2026. **User-reported functional pass:** "airdrop worked"
after the supplied drop-zone teleport command. Keep the working D1 build.
Exact crate/loot/reward coverage, an unforced repeat cycle, all locations,
new-save/reload and fresh-ending integration remain unverified. The earlier 5/5
counter screenshot does not establish natural timer progression: whether the
provided fact-setting command was used is unconfirmed. No timer fix is claimed.
See `research/airdrop_d1/live_result_20261014.json`. Scanner and courier passes
are recorded separately; no need to repeat basic airdrop startup immediately.

## Short test / remaining coverage

1. Start the game and load the **post-Tower save used for the working scanner/car
   theft tests**. Do not use a pre-ending comparison save. No ending replay or CET
   activation is needed.
2. Travel to Dogtown and roam with menus closed. Allow roughly **five real-time
   minutes**, then move between nearby areas. Stock location, pause and content
   gates can delay a drop; five minutes is not a guaranteed spawn deadline.
3. Look/listen for an incoming drop, follow its smoke/beacon, deal with enemies
   if present, and interact with/loot the crate. Report any missing interaction,
   empty event, stuck crate or crash.
4. Later, leave the area and verify another natural cycle. Make a **new save** and
   reload it to check continued operation without duplicate rewards. Keep the
   earlier save as a test fixture.

These are local repeatable events, not a permanent set of citywide map markers
or journal jobs. Do not force cooldowns, active flags, counters or completed facts.

Optional read-only CET check if no drop appears:

```lua
local q=Game.GetQuestsSystem(); for _,f in ipairs({"PTFRD1_Ready","PTFRD1_Issued","PTFRPA2_Finished","ep1_airdrop_pause","mq304_airdrops_active","mq304_ep1_airdrop_pause","ep1_airdrop_cooldown","ep1_airdrop_cooldown_counter","sa_ep1_counter","sa_ep1_reward_counter"}) do print(f.."="..q:GetFactStr(f)) end
```

`Issued=1` confirms startup was issued, not that a visible drop spawned.

## Implementation boundary

One additive archive/XL pair contains the stock airdrop controller in a mod-owned
resource and a completion-gated one-shot entry. All 172 native node payloads are
unchanged. One initial connection enters the existing repeatable route instead
of replaying the introductory drop. The fifteen ordinary location phases remain
official references; their loot, variants, rewards, used-location cycle, delays
and cleanup are unchanged. Special mq304 drop routing retains its native guards;
no side-job story root is restored.

Historic completion/loot counters are not cleared. Admission refuses an unmatched
reward backlog or active mq304 special event. Old per-location active facts can
survive the Tower teardown; they are not treated as proof of a still-live owner
and are not force-cleared. This does **not** reconstruct an interrupted old drop.
The original five-minute startup cooldown is used, not the exact pre-Tower remainder.

No new REDscript/CET polling, console chatter, shader/camera changes, or edits to
the working courier/scanner/gig packages. All existing saves remain unchanged.

## Recovery

Close the game. Recover **D1 first** with `prealpha/airdrop_d1/deploy.ps1`, using
`ValidateRollback` and then `Rollback` with `recovery/airdrop_d1_01`. This moves
only its two added files recoverably. Then N22, N21, C1, N2, N1, FO1 and PA6/older
transactions, if needed. File rollback does not undo gameplay in a later save.

Evidence: `research/airdrop_d1/assessment.json`. Installed build/tools/tests are
pinned; any repair must use a new revision.
