# Post Tower Continuation and Free Roam — integrated restoration baseline R1

One versioned development baseline for the restorations already implemented.
This is not a finished release or an expansion to untested special services.

## Included

- Existing retained-session post-credit return, unchanged.
- H10 floor/living/entrance/bedroom/bathroom resources and persistent interaction
  scene: mirror/actions, shower, sleep, sofa/TV/hologram and wardrobe.
- Existing Afterlife A2, public El Coyote C2 and 25 ordinary C4 mirrors.
- Wilson, the four early regional shops, junk/melee, the tested six ripperdocs
  and Coastview/Japantown netrunners now automatically enabled through redscript.
- Existing automatic 25-vendor cohort, Christine's gated owner and the six
  ordinary variants. Their implementation and evidence levels are unchanged.

The original archive filenames, depot paths and quest registrations remain
unchanged for compatibility with saved owners. R1 combines distribution and
startup, not the archives' internal graphs. No second copy of any scene owner
is introduced. All 25 installed archives are byte-identical to the pre-R1 set;
some contain dormant probes retained for save compatibility, not new features.

## Startup and migration

Native resources still own spawning, prompts, scenes and cleanup. Redscript
supplies the former manual opt-in facts and legacy proximity jobs. CET is no
longer required for those jobs; optional CET diagnostics only observe them.

Ten legacy CET controllers become non-writing compatibility shims. Old
Start/Enable/Stop/Disable commands report that the probe is retired; they do
not reset gameplay state. Two superseded redscript jobs (A4 bootstrap and
four-shop Far driver) retain their serialized classes but are dormant. The
previous automatic vendor batches retain their own tested drivers and explicit
suspension/exclusion handling. R1 does not silently clear their suspensions.

R1 requires the existing genuine Tower/direct-return guard facts. It waits
through the ending rather than forcing them or permanently giving up on a
pre-ending attach. New opt-ins defer during combat, scenes, workspots, mounting,
blocked content, save locks or unsafe tiers. Existing enabled/in-flight state,
native counters, interruptions, vanilla eligibility, inventory and dialogue
history are not reset. A failure or missing prerequisite remains blocked.

H10 geometry is acquired in its established order only from the supported
same-floor corridor, outside the apartment's collision footprint. Existing
claimed geometry is left alone. Persistent actions arm when V enters H10 with
all prerequisites met. If an old save starts inside an unrestored apartment,
R1 does not rebuild a floor beneath V. Housing loss/reacquisition/pricing and
restriction-profile enforcement remain separate unfinished roadmap work.

Afterlife can now start from an unarmed completed-Tower save, or hand off the
saved v5/v6 fallback when idle and outside the mirror. It will not request A2
while the A1 audit or old scene is active. Coyote likewise waits until outside
its mirror. C4 remains unchanged and automatic under its native guards.

## Still excluded

Vista del Rey netrunner has no successful local eligibility test, so R1 does
not newly auto-enable it. Its existing owner remains compatible if previously
armed. Chang remains subject to his existing rescue/market/story gates and is
not newly forced open. Streetkid mirror, special vendors, unrepaired properties,
ambient-NPC fixes, activities and new story content are not added. Time-unpause
and old one-action H10 probes remain dormant; there is no blanket clock reset.

The six most recent variants have only a partial user-reported smoke pass.
Bundling them does not upgrade that evidence. No new restriction-profile bypass
is introduced, but unimplemented profile enforcement is not claimed complete.

## One combined manual check — no arming commands

1. Cold-launch with a **disposable copy/slot of a known-working post-Tower save**.
   Manual Save 17 is one previously reported combined fixture; preserve its
   original. A save missing completion guards will not be forcibly repaired.
2. Wait 10 seconds outside an interaction. Visit H10/Wilson: use an apartment
   action and open Wilson's Trade. Close each normally. An uninitialized H10
   shell may take about 25–30 seconds in the corridor to acquire in sequence.
3. During the same session, check one world mirror and one other vendor you
   already know. No full retest of every mirror/vendor is requested.
4. Walk away, make a **new disposable manual save** while idle, fully quit,
   reload that new slot and repeat the same representative interactions without
   CET Start/Enable. Report any missing prompt, duplicate actor or stuck state.

Optional read-only command (logging starts automatically when CET is installed):

```lua
GetMod("PTFR_RestorationBaseline").Observe("baseline-r1-check")
```

Logs: CET mod folder `PTFR_RestorationBaseline/baseline_r1_*.jsonl`.
No ending replay is required for this integration smoke check. A genuine fresh
ending → credits → retained return regression remains a later release gate.

## Build, install and rollback

Workspace tools: `plan_restoration_baseline.py`, `render_restoration_baseline.py`,
`build_restoration_baseline.ps1`, `test_restoration_baseline.py`,
`install_restoration_baseline.ps1`. Build inputs are frozen with hashes under
`research/restoration_baseline/frozen`; raw game assets/saves are not collected.

Package: `build/RestorationBaseline_R1/game`, with a full file manifest and
offline test report. Dependencies are the existing working game frameworks;
their binaries are not bundled. Use the scoped installer for this installation,
not an uncontrolled copy of legacy and renamed archives. Keep the package in
the workspace; this is not a public-release compatibility claim.

The installer refuses unknown changed files or a running game, backs up all
12 replacements, adds two files, preserves every archive, verifies all hashes,
and records an installation receipt. Rollback with the game closed uses
`tools/install_restoration_baseline.ps1 -Rollback`; it restores the exact prior
12 files and removes only the two new files. Backups are retained. No save is
edited or reverted by install/rollback; loading a prior disposable fixture is
the cleanest gameplay rollback.
