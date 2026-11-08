# Shoot to Thrill completion and immediate shop unavailability

**The final winning contest route completed; actual post-contest shopping remains INCONCLUSIVE.** The user reports completing the quest but being unable to shop immediately. That symptom is preserved. A source-confirmed mod defect has not been established, and no runtime repair or forced vendor command was applied.

## Runtime evidence — November 2, EST

The copied CET log contains two scoring segments, with the game clock moving backward between them and a new load-related snapshot. They must not be combined into one continuous attempt or used as proof of duplicate rewards. The earlier segment reports second place at15:23:47. The later segment reports:

| Time | Logged transition |
| --- | --- |
|15:30:09|`mq011_shooting_over`0→1 and `mq011_competition_won`0→1|
|15:30:31|`mq011_took_reward_from_wilson`0→1|
|15:33:08|`wat_lch_gunsmith_01_default_on`0→1|
|15:33:14|`mq011_active`1→0 and `mq011_done`0→1|

The shop-enable callback is157 wall-seconds after the reward callback. That is an observed gap, **not a source-defined157-second timer**. Callback timestamps do not identify exact node execution or every intervening player/actor movement.

AutoSave-8 metadata at15:30:31 still tracks talking to Wilson; AutoSave-6 at15:33:12 and AutoSave-9 at15:34:35 list `mq011` finished. Metadata and callback clocks are not strict event-order clocks. Together with the user's report, this supports a bounded progression/winning/reward-receipt/completion PASS. Exact item quantity, full payout idempotence and every outcome remain unproven.

The enable flag returning disproves a permanent default-on0 latch in this recorded final segment. It does **not** prove Wilson's actual shop conversation opened, that the vendor owner reacquired Wilson, or that the reported immediate symptom recovered. The user was asked whether leaving/waiting, reload or neither restored shopping; that answer remains pending.

## Exact pinned native and private handoff

`native_trace.json` records raw/JSON source hashes and node/socket evidence. The pinned vanilla quest raw SHA is `F432989578A0D071A8C273AE0B67128FBE51B1271C4F839269A8D1E7B1299FBD`; the scene raw SHA is `D40F1E9F65C970A91CBF38C2A3ACE5A9F48E8354DECD24EE881B3446C3BBBD89`. Their pinned raw/JSON hashes were checked. Current QR8 private MQ011 wrapper and B0 vendor-owner payloads exactly match the reviewed source pins. No resource was edited, serialized or rebuilt.

The native reward receipt is a separate scene node1653; it is not the competition scene's terminating output. The relevant native handoff is:

- Scene end338 emits `mq011_01_competition_out`. Its predecessor is AND1267. Incoming ordinal0 can come from the Wilson-door cleanup route1279 or player-distance fallback1538; ordinal1 comes from five-second realtime wait1290. Door-route ancestors1259/1261 wait for **Wilson**, not V, inside/outside `#mq011_tr_wilson_door_trigger`, with native door operations between them. Fallback1538 checks player-to-`#wilson` distance Greater100. This is a scene/actor exit condition, not a promise of immediate trade after reward collection.
- Quest root/27 scene69's competition-out socket reaches reward85 (`QuestRewards.mq011_finished`) then output1. Root27.Out1 enters root24.In1.
- Native cleanup root24 input0 reaches33(default_on1)→2(active0)→3(done1), then the retained content-token/checkpoint path reaches distance wait6 (player-to-Wilson Greater99) before actor/community cleanup and termination. A separate branch waits for the player outside the range-end trigger. Shop-enable/done facts therefore precede full owner retirement.
- The private wrapper delegates the complete native body at15. Only15.Out1 reaches1007Finished1→1012QuestOwns0. The B0 vendor owner waits at102 for QuestOwns0 after recording Released1; no second actor/controller may be forced in to make trading appear early.

These conditions explain why immediate trading can be unavailable while scene/owner cleanup is incomplete. They do not prove which route executed in the user's run or establish that the private lease's visible latency is perfectly vanilla-equivalent. Actual vendor UI behavior and owner/lease execution remain a live limitation. In particular, default_on1 or done1 alone is insufficient to certify the handoff.

## Status and next observation

- **PASS, bounded:** user-completed final contest route; logged win, reward-receipt and completion; finished metadata.
- **Observed symptom:** immediate shop unavailable.
- **INCONCLUSIVE:** eventual shop usability/native-parity and exact private-owner retirement. No blanket vendor PASS and no confirmed stuck-shop FAIL.
- **Preserved:** Core51, Diagnostics2, six pinned core dependencies, original ManualSave-23 and offline backup all pass the guarded Verify commands after the user quit. Analysis performed no game/save/fact writes, launches, CUA or deployment.

If shopping has not already recovered, use the existing completed working branch: leave H10 and move well away from Wilson, then return normally and try trading. This exercises the ordinary distance/retirement boundary; it does not replay the contest. Keep the original master untouched and do not force facts, despawn actors or call arbitrary vendor commands. Record whether the trade screen opens; if it does not, preserve that branch for a focused owner/lease observation. No completed quest reset or fresh reward is needed.
