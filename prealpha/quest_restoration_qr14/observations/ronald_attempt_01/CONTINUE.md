# Ronald continuation from counter3

Stay on this current working branch. While already besideRonald, run:

```lua
GetMod("PTFR_QR9_Diagnostics").start("S02", "QR14-Ronald-Topics8", 600)
```

Require Recording. CloseCET and continue unused Dogtown/information topics. Vanilla requires counter>=8 before the offer; current3 is incomplete. Choose the normal Yes if he offers future news. Let conversation finish; leave interaction range and return once if needed, then wait10seconds.

Stop:

```lua
GetMod("PTFR_QR9_Diagnostics").stop("RONALD_TOPICS_DONE")
```

Repeat the existing read-only getter command and send output. Report whether an offer appeared/was accepted, contact appeared and HUD behaved normally. Expected after successful route: native enabled1, private consent1/contactissued1, Active noncallable contact. No immediate news message is required. If no new topics/offer, stop and send a screenshot of available dialogue; do not force facts or reset history. A timed-out recording is not a reason to replay earned dialogue.
