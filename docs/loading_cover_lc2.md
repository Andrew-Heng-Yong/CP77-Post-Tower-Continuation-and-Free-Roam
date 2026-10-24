# LC2: loading stall repair and setup progress

The October 24, 16:30–16:38 session reached the cover but never finished setup.
The installed LC1 native graph reset `PTFRLC1_CoverReady` to zero at node 180,
then immediately evaluated it with a one-shot condition at node 181. The false
output had no connection. A later UI acknowledgement could not revive that branch.
LC2 replaces only node 181 with a native waiting condition, retaining its ID,
predicate, incoming/cut connections and the original fade/Tier1 sequence.
The archive's other 615 resources, including the repaired 2.5 lighting sector,
are unchanged. No ending, teleport or camera replay is added.

The two stage-only log entries do **not** prove the simulation was paused.
LC2 acknowledges rendering after an opaque UI animation rather than elapsed
simulation time and logs both engine and simulation elapsed times every five
seconds, along with exact native handoff facts and the current wait reason.
The existing notification input blocker remains; no pause, time dilation,
movement restriction or scene-tier override is introduced.

The progress bar displays **12 actual setup checkpoints**, not a time estimate:
cover, player, ending/module health, verified history snapshot, arrival, profile,
housing, local world, handoff, job classification, player control, and stability.
Refund counters remain in the stage text. A failed check stops progress; the
percentage may move backward if a prerequisite becomes invalid. Only the complete
barrier followed by one stable simulation second reaches 100% and removes the
cover. At two minutes, the current wait reason stays visible with an exit hint.
Esc returns to the main menu without certifying or exposing unfinished gameplay.

The current game also has 194 perk enum entries instead of 189. The old Body,
Relic and profile catalogue checks would reject it even after the gate repair.
LC2 reads the current base and EP1 databases: 1,626 checked existing fields match;
the Cool roster gains five perks and Cool Central Milestone 3 loses its previous
prerequisite. The validators bind those exact changes and all five added records.
The selected refund policy, transaction code, persistent fields and profile
fingerprint are preserved. The new Cool branch is retained. Old 189-entry saved
refund ledgers and previously faulted transactions are not silently reset or
reindexed.

Five replacements are installed: the main archive, loading-cover script, and
three catalogue scripts. The full 87-source stack including Equipment-EX compiles.
The final proof is `prealpha/loading_cover_lc2/candidate_01/compile_02`; candidate
`compile_01` predates the shorter error text. `changes_01.json` contains an
intermediate cover hash; the installation manifest contains final hashes.
Source/compiled validators, actual serialized wait-node semantics, preservation
checks and installer failure fixtures are offline evidence, not a live pass.

Cold-launch and retry the retained save from before the failed transition, or
retained post-ending AutoSave 8/9. Keep originals and use a new manual slot after
successful setup. A save already stranded on LC1's finished false branch is not
automatically replayed. Check that the bar advances, inputs stay blocked, Esc
returns to the menu, and profile/housing/world setup finishes before reveal.
First-frame opacity, UI layout, snapshot export, input behavior, full setup and
save/death reload still need live validation. No end-to-end speedup is measured.

Read-only status: `PTFR.LoadingCoverLC1.StartupCoverLC1.Status()` through the
scriptable-systems container. The class/module name is retained for compatibility;
new log lines use `PTFR_LoadingLC2`.

Recovery order: run `prealpha/loading_cover_lc2/deploy_01.ps1 -Action ValidateRollback`
then `-Action Rollback` **before** LC1, HS1, or older Tower packages. Backups are
in `recovery/loading_cover_lc2_01`. Undoing LC2 alone restores LC1, including its
known loading bug; to remove the loading-cover implementation, subsequently
roll back LC1 using its guarded installer. Never restore the obsolete crashing
sector archive. Framework/cosmetic recovery is separate; file undo is not save undo.
