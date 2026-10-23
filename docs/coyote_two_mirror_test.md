# El Coyote Cojo two-surface test (C2 candidate)

Status: C2 public-bathroom scene package and bounded two-surface logger installed on 2026-09-24 after confirming Cyberpunk was closed; not yet live-tested. The installed C1 shadow probe remains inert unless separately armed. The Streetkid-start surface is diagnostic-only in this candidate; it is not a second ordinary mirror leaf. Installer hash checks confirmed the working Afterlife packages and C1 remained unchanged; no save or story fact was changed.

Use a disposable post-Tower save and do not save during this test. Do not set q000 or world-variant facts, start the Streetkid prologue, or arm C1. The working Afterlife implementation stays installed unchanged.

1. Load outside the public bathroom, at least 8 m from its mirror (the Streetkid-start mirror is about 25 m away and is an acceptable starting location). Wait until V is idle, out of combat, scene and workspot.
2. Run one CET command: `GetMod("PTFR_Coyote_TwoMirrorProbe").Start()`. It refuses unless the Tower facts match, C1 is unarmed, C2 is fresh (`Boot=1`, `Requested=0`), and a durable log opens. On success, it changes only the mod-owned `PTFRCM2_Requested` fact and samples at 1 Hz for up to five minutes.
3. At the public bathroom mirror, try Look, a facial expression, and Stop; leave the mirror area, wait at least one second, then return and repeat. Report each physical action and whether the prompt appeared after leaving/re-entering.
4. At the Streetkid-start mirror, look squarely at its surface for at least three seconds so the probe can capture the live target/device class. Note whether any Look prompt exists. Do not force a quest variant. If a normal prompt appears, try it once and report what happened.
5. Run `GetMod("PTFR_Coyote_TwoMirrorProbe").Stop()`. Quit without saving and report that the game is closed. The JSONL log is in the probe's CET mod folder and is flushed on each sample.

The public-bathroom candidate passes only if both visits physically work and native `SceneRequests=2`, `SceneReturns=2`, `Rearms=2`, `Interrupted=0` after the second exit. Its first run is a disposable trial, not production persistence. The Streetkid surface has **no pass claim yet**: the log can show its live entity/PS state and proximity, but the current package does not attach a Look scene there. Do not present a fake-to-real visual variant toggle as restored interaction.
