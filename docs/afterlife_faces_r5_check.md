# Afterlife Faces R5 — focused playtest

Use only after `research/afterlife_world/faces_r5/install_receipt.json` confirms
the actual installation. Cold-launch Cyberpunk and use a disposable completed-
Tower save. Keep your master save untouched. No forced facts or crowd resets.

1. Visit Afterlife and allow15 seconds of unpaused gameplay for streaming and
   acknowledgement. Check ordinary random patrons, especially the repeated
   cyberpunk group. Faces should differ; shared outfits are allowed. R5 does
   not fix the four fixed booth actors or their unresolved routines.
2. In CET run this read-only status command:

```lua
local s=Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.AfterlifeFacesR5.AfterlifeFacesR5")); if s then print(s:GetStatus()) else print("R5 system unavailable; check redscript compile log") end
```

Expected candidate evidence: `enabled=true`, `owned` greater than0,
`confirmed=owned`, `pending=0`, `duplicateReservations=0`, `errors=0`.
Do not expect exactly50 people:50 is the configured quota across these four
entries, not the visible population. `tracked` can include ignored actors
with a matching record but different ownership. Reservations/readback are
not visual proof: report both the line and whether faces actually differ.
If values do not settle after30 seconds unpaused, send the status; do not
reroll, force facts or change community states.

3. Once the first check succeeds, leave far enough to unload Afterlife and
   return. Check the line and faces again. Short-lived initial duplicates
   may be visible: this supported script hook corrects after attachment,
   not before the first rendered frame. Report any persistent duplicates.
4. Quit without saving for the first smoke test. Later, use a separate
   disposable save for save/quit/reload persistence. Neither repeat streaming
   nor saved reload is proven by installation or first-visit success.

If a repeated face remains, scan both patrons and capture community ID,
entry, phase, entity ID, record and appearance. No root-component screenshot
is needed. A fixed resident outside the four random entries is a separate
case, not permission to modify named/story actors.

## Recoverable rollback

Close the game. From the workspace, the default command checks only:

```powershell
./tools/rollback_afterlife_faces_r5.ps1 -ValidateOnly
```

Explicit removal moves only the two hash-verified R5 scripts to a timestamped
workspace recovery folder:

```powershell
./tools/rollback_afterlife_faces_r5.ps1 -Rollback
```

No R1/R2/R3, Nix, density or Zetatech payload is removed. No save file is
rewritten. Use the untouched/disposable test save after rollback rather than
assuming an experimental saved appearance has been reverted by file removal.
