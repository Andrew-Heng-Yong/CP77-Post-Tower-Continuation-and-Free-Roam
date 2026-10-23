# Coaster revision6: direct cheer entry

Completed: user reports no motion, no crash and free walking after Exit.
Trace confirms5/5 requests/starts and one Return, but still no observer
callbacks despite SelfTest PASS/mode8192/12 attempts. Do not repeat this test
without a new evidence-backed change; instructions below are historical.

This is a new playback candidate, not another run of the unchanged revision5
scene. Only the two gesture entry targets changed from sequence2 to clip5.
Ride/exit and all nine other native payloads are unchanged. Diagnostic observer
revision2 waits for an active workspot; real callbacks, not a returned Void call,
determine its acknowledgement. No visual repair is claimed before this check.

Cold-launch the same original disposable gate0 save. While standing at the
coaster platform, run:

```lua
GetMod("PTFR_WorldInteractions_Audit").Start()
```

Expected: `WAITING_FOR_WORKSPOT; queue self-test: PASS`. This is normal outside
the cart. If it says UNAVAILABLE or self-test FAILED, stop and send the message;
do not ride for this diagnostic. No need to interpret native animation events.

Enable the previously authorized temporary gate:

```lua
Game.GetQuestsSystem():SetFactStr("mq006_enable_repeatable_rollercoaster", 1)
```

Get in. Choose Raise arms once when offered. If it visibly works, try once more
on a later offer; do not mash the choice. Finish the ride and Exit normally.
Report whether the arms moved and whether V can walk after Exit. If a crash or
stuck state occurs, do not force cleanup/teleport/save; quit without saving.

After a normal Exit:

```lua
Game.GetQuestsSystem():SetFactStr("mq006_enable_repeatable_rollercoaster", 0)
GetMod("PTFR_WorldInteractions_Audit").Mark("revision6-after-exit")
GetMod("PTFR_WorldInteractions_Audit").Stop()
```

Quit without saving. The agent reads the durable trace; no user classification
of played/skipped/missing is required. If callbacks stay absent despite verified
native mode8192, self-test PASS and active-instance attachment attempts, record
the channel as inconclusive and do not request an identical rerun.
