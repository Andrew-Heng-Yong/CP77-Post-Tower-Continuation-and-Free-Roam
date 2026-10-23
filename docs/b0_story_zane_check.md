# Zane — combined service and future-quest handover check

Use only after the StoryZane install receipt exists. Cold-launch with a disposable
post-Tower save; no Enable/Arm needed. Keep the original save untouched.
Visit Jinguji/Zane in Downtown via its map location; no unverified teleport.
Wait ten seconds in normal gameplay. If absent, do not change vanilla facts.

1. Before using the shop, capture:

```lua
GetMod("PTFR_B0_StoryZane").Observe("before-service")
```

2. Check one Zane, available unique dialogue, actual Trade inventory and wardrobe.
   Close every menu. Request the simulated future quest lease (mod-owned only):

```lua
Game.GetQuestsSystem():SetFactStr("PTFRB0ZAN_QuestOwns",1)
```

3. Walk at least 100–150 m away from the shop, wait five seconds, then:

```lua
GetMod("PTFR_B0_StoryZane").Observe("outside-quest-lease")
```

Expected: QuestOwns=1, OwnerActive=0, Inside=0, Released=1. If not, stop and
report; do not force Released or any vanilla gate. Entries/Exits should reflect
one native shop lifecycle, not necessarily the count of menu openings.

4. Return to the shop with QuestOwns still 1. Zane's restored service should not
   respawn. This tests exclusion; there is no actual future quest actor yet.
   If another actor/service appears, report it and do not continue the handoff.
   Walk out again, then release the simulated lease:

```lua
Game.GetQuestsSystem():SetFactStr("PTFRB0ZAN_QuestOwns",0)
```

5. Return, check one Zane and reopen Trade/wardrobe. Close menus, walk out, run:

```lua
GetMod("PTFR_B0_StoryZane").Observe("service-returned")
```

Expected OwnerActive=1, Released=0 and a second native entry/exit. The original
`mq030_zane_met` value must match before-service. An already-earned gratitude
discount may legitimately set its original discount latch once.

6. Quit **without saving**; report first/return service success and whether Zane
   stayed absent during the lease. Durable logs start automatically in the new
   CET module directory. No full ending or actual Bullets replay is requested.

This tests normal service, departure, cooperative release, lease exclusion and
re-entry in one run. Cold-save persistence and a real future quest handoff are
separate unproven integration checks, not implied by this smoke test.
