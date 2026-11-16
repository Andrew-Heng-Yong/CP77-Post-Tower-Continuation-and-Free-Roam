# Evening recovery and fast travel

## Recovery clock and caps

`PTFRRecovery_Day` now advances at 23:55 in-game. A saved day credited under the morning schedule stays credited. The calendar-day checkpoint therefore awards at most one increment for that date across the change. Forward skips count every crossed evening checkpoint, and the fact caps at 30.

The 12 November run logged day 1 at 11:02:39 Toronto time and a Health pool acknowledgement timeout at 11:02:42. The CET command to set `PTFRRecovery_Day` to 30 and the mod's day-30 readback both occurred at 11:08:55. The pool fault latched for the rest of that actor session and prevented subsequent Health cap updates.

The new cap is applied on the next eligible recovery pulse, even if the previous pool update is still settling. Once the pool maximum agrees with the stat, Health can receive a single downward correction for automatic refill. Healing or damage after that check proceeds through the native pool. The bounded correction window can expire without stopping the next cap update. Engine readback of both caps is logged when they settle.

The same CET command requests 125 maximum Health and 75 maximum Stamina.

```lua
Game.GetQuestsSystem():SetFactStr("PTFRRecovery_Day", 30)
```

## Fast travel

The user confirmed the blackout followed in-game fast travel and covered the menu. The game log shows the initial Tower cover reached Ready at 10:59:59. Fact changes and other scripted activity continued through 11:11:16, and RED4ext shut down normally. The specific trip and the native loading-finished callback are unobserved in that log. The earlier Buran St to El Coyote report had similar symptoms. [Earlier fast-travel report](../../docs/fast_travel_blackout_20261026.md)

An obsolete setup popup could draw its opaque root while waiting for deferred detachment. The owned popup now hides before detachment and checks its owner and epoch before showing or handling input. A read-only `PTFR_FastTravel` trace records the native start, finish callback and follow-up state for completed Tower saves. It records destination, player position, loading flags, menu state and the setup popup reference. The wrappers preserve both native callbacks and the native save request.

## Verification

Source checks verified the cap update order, one downward Health correction, saved field identities, first-arrival checks and native fast-travel callback preservation. The clock model covers exact 23:55, same-day migration, skipped days, reloads, rewinds and the override. All 148 registered scripts compiled. Nine installer fixture actions and closed-game preflight passed. The automatic approval review stopped installation before execution, citing the earlier hand-model task and missing deployment authorization for these two changes. Gameplay validation is pending. [Source patch](candidate_01/source.patch) · [Source checks](candidate_01/verification.json) · [Compile result](compile_01/result.json) · [Deployment readiness](readiness.json)

The user then explicitly approved installing the two staged scripts. The closed-game installation, independent readback and rollback check passed. All 51 Core paths and 26 dependencies verified, and all 349 save files matched their pre-install names and hashes. The evening checkpoint, Health cap update and fast-travel blackout still require an in-game check. [Installed manifest](deployment_01/installed_manifest_01.json) · [Installed readback](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json)
