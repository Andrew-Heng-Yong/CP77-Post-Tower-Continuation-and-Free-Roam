# Welcome to Paradise!

The staged Core restores the unstarted Night City tour in post-Tower free roam. It uses the original Street Cred gates, the 21-game-hour delay, the quest token scheduler, and Aera’s introductory call. The delay begins again when a qualified post-Tower entry gets its permit. The native quest handles the callback, the tour stops, the shard, the rewards, and cleanup. [Candidate manifest](candidate_01/core_manifest.json)

## Save compatibility

ManualSave-31 held the native timer at node 128 under the main game’s bugfix phase. ManualSave-32, AutoSave-10, and AutoSave-16 had no registered handler on that route. The four saves had no serialized tour journal entries or nonzero tour progress facts in the checked set. The corresponding pre-cleanup history capture recorded stable zero values for `mq061_start` and `mq061_07_rancho_done`. [Saved owners](owner_evidence.json) · [Save projection](quest_evidence_02.json)

The entry requires the original side-content prerequisite and genuine Tower completion. It checks the archived beginning, the tour’s token block, 190 journal entries, 70 facts, and four item IDs. Two settled runtime samples must agree before the timer starts and again before it hands off. While the timer runs, the script suspends those inventory and journal scans. Previously started, completed, failed, or ambiguous histories defer. An issued entry has a saved receipt and cannot issue another tour. An unfinished tour carried across The Tower still needs a stage-specific resume review.

## Dialogue and visual presentation

Johnny’s recorded reactions, V’s replies, choices, and scene connections remain in place for the requested later audit. The four private scene copies suppress four Johnny-bound visual events and mute embedded animation events on six Johnny performances. His three shared workspots have private visual variants. The existing post-Tower Johnny presentation script handles his character mesh. Richard Night and Haze keep their original holograms, including Richard’s glitch effect at Corpo Plaza.

Serialized scene readback preserved all 94 dialogue events in the four edited scenes, their localization stores, and actor bindings. The three scenes with native English lip-sync mappings received matching private entries. The fourth scene has Johnny as its sole actor and has no native English lip-sync entry. Other spoken languages and in-game playback have not been tested.

## Verification and first playtest

The compiler accepted the current 149 registered script sources. All 1,764 archive members passed byte readback, and the wrapper preserved all seven Street Cred branches and all 15 root tour prefab references. The private entry passed collision checks across the 135 installed archives and the EP1 phase registrations. Separate fixtures exercised each of the 70 progress facts, active and terminal journal states, and the issued receipt. They also compared all 50 previous English lip-sync mappings and the three additions against their donors. [Verification](candidate_01/verification.json) · [Guard and lip-sync fixtures](candidate_01/gate_and_lipmap_fixtures.json)

On an eligible existing post-Tower save, reach Street Cred 15 and let 21 in-game hours pass, then return to ordinary on-foot play outside the first tour trigger area. Aera’s call is the first gameplay check. The call, tour stops, Johnny presentation, completion rewards, and a mid-tour reload still need an in-game playthrough.

Read-only CET status for that playtest:

```lua
print(Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS30")):Inspect("mq061"))
```

`ready=2` covers the native prerequisites and timer. `issued=1` records the handoff into MQ061. The first phone call can still be waiting for the game’s scheduler at that point.
