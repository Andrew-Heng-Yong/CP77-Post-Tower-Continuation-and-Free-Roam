# Afterlife R1 — one focused visit

2026-10-04 update: this initial smoke route is historical. Rogue/Nix presence
passed; user confirmed excessive crowd and remaining visual/idle defects.
Population-rule research found R1 selects the wrong q103 cohort for the saved
q103_done1 state. Do not repeat this entire visit or run crowd mutation tests
as part of the current research request. Read research/afterlife_world/assessment.md
and live_r1_result.md. No R2 is installed; keep already accepted results.

Use this only after `research/afterlife_world/install_receipt.json` confirms
installation. Cold-launch and load your disposable completed-Tower save.
Stand normally, outside a vehicle, combat, dialogue or seat, for 10 seconds.
Everything starts automatically; do not change quest facts.

Travel to Afterlife. Optional CET teleport to the approach position recorded
in the existing Afterlife check save (ManualSave-15):

```lua
Game.GetTeleportationFacility():Teleport(Game.GetPlayer(), Vector4.new(-1488.522216796875, 1021.6135864257812, 22.49634552001953, 1), EulerAngles.new(0, 0, 0))
```

Never teleport during dialogue or while seated. Walk down into the club and
allow about 40 seconds for the ten dancers' original staggered activation.

Check once:

1. Hologram dancers are visible and dancing in their original positions.
2. Emmerick is a single bouncer using his guard idle, not a frozen duplicate.
3. Ordinary patrons use the bar's sitting/standing routines without obvious
   overlapping duplicates or floating poses. This does not add Tiny Mike.
   If anyone still stands frozen, look directly at them for the audit below;
   the older four scene-owned mercenaries are outside this repair's cohort.
4. One Rogue sits/animates at her booth in the Tower-authored appearance.
   This is ambient presence, not restored old Rogue/Johnny quest dialogue.
5. Nix is present in his back room. Approach and try his ordinary Trade menu;
   close it and finish the conversation normally.

Look directly at a problematic actor for 8 seconds. The automatic read-only
audit records its identity and workspot state. Optional marker:

```lua
GetMod("PTFR_Afterlife_Audit").Observe("afterlife-first-visit")
```

Leave the club area, walk roughly 200 metres away, and return once. Check
that the repaired actors remain animated without duplicates and Nix can
interact again. Then quit **without saving** this first run. Report only the
five results above and any return-visit difference; no repeated Claire,
mirror, Zetatech-door or lighting test is required.

Logs are `afterlife_*.jsonl` under the installed `PTFR_Afterlife_Audit` CET
folder; Nix also retains the existing S4 service log. Request counters are
not spawn/animation acknowledgements. Empty community actor-ID lists are
not used to infer absence. Cold-reload persistence from a newly saved slot,
fresh-ending integrity and long-session stability remain separate tests.

If startup fails, close the game. The six-file rollback preflight is
`tools/rollback_afterlife_r1.ps1 -ValidateOnly`; actual rollback restores two
previous files and recoverably removes four additions. Do not force any
story facts or delete whole mod folders.
