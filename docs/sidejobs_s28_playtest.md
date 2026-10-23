# S28 side-job restoration

Status: installed on 23 October 2026; live gameplay verification is pending.
Build `s28_01` contains 20 private resources and four entry paths in three added
files. Full installed-script compilation, resource checks, and 96 deployment
cases passed. All 716 protected files, including 215 save files and five cache
files, stayed unchanged. See [installation evidence](../research/sidejobs_s28/assessment_01.json).

This package adds bounded native beginnings for Space Oddity, Ezekiel Saw the
Wheel, The Highwayman, and I'm in Love with My Car. It preserves completed jobs,
earned progress, existing owners, items, and vehicle ownership. Unsupported
unfinished jobs defer; they are not restarted. A missing or unsettled observation
also defers admission.

Use the same working post-Tower branch and a new manual test save. There is no
need to replay the ending or force quest facts. Visit the original job locations
normally. Completed jobs are preservation checks, not fixtures for new starts.

For Space Oddity, check the native approach, laptop/coordinates, fight, loot,
dialogue and completion. For Ezekiel, check the diner interaction, confrontation
choices, and the barman's service returning after the encounter. For The
Highwayman, follow the native garage/photo, James/Josie and bike route. For I'm
in Love with My Car, approach the warehouse, collect the original keys and
complete the native vehicle interaction. An already-owned reward vehicle or
evidence of a previous start should not produce a duplicate restoration.
Hoon admission requires its original loot crate to be loaded and contain no
quest key; visit the warehouse normally. An unloaded crate deliberately defers
the job rather than guessing that earlier progress is absent.

Johnny's dialogue is retained under the existing voice-only policy. Check for
unwanted independent cigarettes, glasses or other props, and confirm that scene
timing and objectives still advance. Reload the manual test save after a normal
checkpoint and check that jobs do not start twice.

H10 arrival, existing restored gigs, vendors, races and Dogtown remain regression
checks. Report the job, last objective, location and whether the problem happened
before or after a reload; do not reset facts to force a route.

The approved Patch 2.5 framework package uses Codeware PR63, TweakXL PR22,
ArchiveXL PR31 and official redscript 0.5.32. Separate framework testing was
skipped at the user's request. ArchiveXL PR31 currently disables its journal
extension and hot reload. This is separate from the game's existing native
journal entries used by these jobs. The framework backup receipt is
`recovery/framework_pr63_01/receipt.json`.

Game-file rollback does not undo progress saved during gameplay. S28 recovery
comes first: run `prealpha/sidejobs_s28/deploy_02.ps1 -Mode ValidateRollback` and
then `-Mode Rollback`, using the absolute path to `recovery/sidejobs_s28_01` as
`-RecoveryRoot`, while the game is closed. The installation receipt is
`recovery/sidejobs_s28_01/install_receipt.json`. U10, S27, DT1 and older mod
recoveries follow only if needed. The framework package has its separate
`research/framework_pr63_01/deploy.ps1 -Action Rollback` recovery.
