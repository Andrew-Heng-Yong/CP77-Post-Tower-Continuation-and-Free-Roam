# Afterlife population R2 — density passed, remaining validation

2026-10-05: user confirms crowd density is fixed. The initial route below is
retained for reference; do not repeat the accepted basic density check.
Repeated returns, fast travel, saved reload and natural-ending coverage were
not reported. The four idle booth routines remain a separate unresolved issue.

User-approved installation completed 2026-10-05T14:49:38Z. The actual receipt is
`research/afterlife_world/population_r2/install_receipt.json`; hashes and
two-file rollback preflight pass. Basic visible crowd density is USER-pass;
the broader lifecycle checks remain unverified.
R2 is a two-file replacement of R1, not a second archive installed beside it.
No story-fact, community-toggle, appearance-change or spawning commands.

## First visit: disposable, no save

1. Cold-launch a backed-up/disposable completed-Tower save. If it loads inside
   Afterlife, leave the whole area first. Travel far enough that the old private
   workspots unload (roughly 300m is a starting point, not proof). Stand normally
   for a few seconds outside combat/dialogue/vehicles. The controller deliberately
   withholds its new population requests until this departure barrier passes.
2. Read migration state; do not force it:

   ```lua
   local q=Game.GetQuestsSystem(); for _,f in ipairs({"q103_done","q103_active","q005_done","q005_plan_finished","PTFRAL2_Registered","PTFRAL2_Migration","PTFRAL2_LocalActive","PTFRAL2_RetireRequests","PTFRAL2_Visits","PTFRAL2_Acquires","PTFRAL2_Releases"}) do print(f,q:GetFactStr(f)) end
   ```

   Expected supported story state is 1,0,1,1. Registered=1 and Migration=2 mean
   the native controller reached the departure barrier, **not an actor census**.
   If Migration remains 0 after leaving, report the readings; do not repeat
   active-count commands or manually set facts. That is a readiness defect to
   investigate before judging the roster.
3. Walk into Afterlife. Compare entrance, booths and bar using the same route,
   game time and Medium crowd setting as the pre-ending reference. Capture
   screenshots from the same camera positions. Do not change density to hide
   a mismatch. Give the unchanged dancer staggering approximately 40 seconds.
4. Record density, repeated visible appearances, obvious overlapping actors,
   and ordinary workspot behavior. There is no required visible count of 71:
   66 background allocations + five extras share 70 workspots, and native
   budgeting/conditional scene actors affect what is present.
5. For any suspicious actor, look directly at it and label the existing audit:

   ```lua
   GetMod("PTFR_Afterlife_Audit").Observe("r2-entrance-actor-A")
   ```

   Use distinct labels for each actor/visit and capture its appearance visually.
   This log has target entity ID, record and workspot/scene state. Its position
   is the **player's**, not the actor's. Record ID alone cannot prove duplicate
   ownership. Empty community-ID getter arrays remain UNKNOWN, not zero NPCs.
6. Leave the whole area and return twice. Record the same viewpoints and whether
   density grows, actors accumulate, routines stop, or a cohort fails to return.
   Include one fast-travel departure/return after the first ordinary return.
7. Quit without saving. Report only population/return findings and any new
   regression. Do not repeat accepted Rogue/Nix presence or Zetatech tests;
   simply report if a previously accepted feature has regressed.

The four old frozen scene-owned mercenaries were not individually changed.
Hologram visibility already passed in the later R1 visit: do not repeat that
basic test; report only any regression. Scanner names alone do not establish
a wrong actor; vanilla tube holograms are NPC-based.

## Required follow-up after initial pass

Use a separate backed-up disposable slot for save -> quit -> cold reload,
both inside and outside the club, and repeated departure/return cycles. Compare
the same snapshots to the pre-ending baseline. Test natural Tower completion
separately without forcing facts. Offline saved-token modeling does not prove
native engine persistence or duplicate-free rendering.

## Recovery

Close the game. `tools/rollback_afterlife_population_r2.ps1 -ValidateOnly`
checks the exact R2 backup; `-Restore` restores only the two prior R1 files.
Do **not** use `rollback_afterlife_r1.ps1`, which also undoes the accepted Nix
change. Load the pre-R2 save after rollback; compatibility of R2-saved native
quest tokens after removing its resources has not been established.
