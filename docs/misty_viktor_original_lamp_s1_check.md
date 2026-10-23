# Original police-light alias S1 — one-site opt-in check

This is a **single-lamp mechanism test**, not yet the pink-to-blue neon fix or
the seven-light cleanup. The new archive changes one official sector only by
giving original police light 3362 / placement 3901 a private reference. It does
not change the lamp's color, geometry, variant, or visibility on installation.
The controller is idle until Start. Keep the working Misty/Viktor R7 package.

Use disposable saves and **do not save** during this test. If the game crashes,
relaunch and report the last command; do not repeat it automatically.

## 1. Pre-Tower visual baseline

Cold-launch after installation and load your normal pre-Tower comparison save.
Visit the police-line area near (-1544, 1169, 17). Do not call S1 Start or
change lighting facts. Check that the original police-area lighting and
nearby neon are not missing or visibly changed just from loading the patch.
Report any discrepancy. Before toggling this original lamp, continue that
disposable pre-ending save through the **normal** Tower finale, credits,
cleanup and retained-session return with S1 still idle. Confirm there is no
new visual/transition problem and that q307 completed naturally. Do not force
facts or start S1 during the ending. If a suitable pre-ending fixture is not
available, stop after the baseline and report that the transition is untested;
do not proceed to the Hide step yet.

## 2. Post-Tower readiness

After the natural return, activate the already-tested R7 world opt-in if it is
not active:

```lua
GetMod("PTFR_MistyViktor_World").Inspect()
```

Only if it reports R7 not applied, run its existing Start procedure from
`docs/misty_viktor_details_r7_check.md`. Do not force any q307 facts or use
RedHotTools visibility toggles in this comparison.

At the target, use this previously reported standing position if needed:

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), ToVector4{x=-1543.79248,y=1170.06689,z=17.17,w=1}, ToEulerAngles{roll=0,pitch=0,yaw=0})
```

Only teleport if the floor is visibly present. This is near light 3362, not
the other six lamps. For a clear visual comparison, use after-dark conditions
and hold the same camera view of the pavement and police-line area.

```lua
GetMod("PTFR_MistyViktor_Original_Lamp_S1").Inspect()
```

Expected before Start: `Rev=1`, `Enabled=0`, `Applied=0`; the existing light
should still look normal. If Rev is 0, stop here and report it.

## 3. One Show, Hide, Show, Stop

```lua
GetMod("PTFR_MistyViktor_Original_Lamp_S1").Start()
```

Close CET, wait two seconds, then Inspect. Expect `Enabled=1`, `Applied=1`,
`Ready=1`, and ShowRequests at least 1. If not, do not Hide; Stop and report
the output. A request counter alone is not proof of visible control.

```lua
GetMod("PTFR_MistyViktor_Original_Lamp_S1").Hide()
```

Close CET, wait two seconds. Compare the same view, then Inspect. HideRequests
should increase by one and only this lamp's local yellow contribution should
disappear or diminish. Do not expect all police glow or pink hotel neon to go
away in this singleton test.

```lua
GetMod("PTFR_MistyViktor_Original_Lamp_S1").Show()
```

Wait two seconds, compare the same view, and Inspect. ShowRequests should
increase; the same local contribution should return. If anything unexpected
happens, stop here and report it.

```lua
GetMod("PTFR_MistyViktor_Original_Lamp_S1").Stop()
```

Wait two seconds and Inspect. Expect `Enabled=0`, `Applied=0`, `Ready=0`,
Releases increased, and the original local light restored. Then:

```lua
GetMod("PTFR_MistyViktor_Original_Lamp_S1").Finish()
```

Quit without saving. Report: pre-Tower baseline, natural Tower return,
post-Tower Start/Inspect, Hide/Show visual changes, Stop restoration and any
crash. Include the S1 log if readily available; console output and paired
screenshots are enough for the first pass.
No automatic seven-lamp/pink-neon rollout follows from counters alone.
