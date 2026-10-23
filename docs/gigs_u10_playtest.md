# Eight added gigs — U10

22 October 2026. Build `u10_02` is installed. All 712 protected files, including
215 save files and five cache files, stayed unchanged. Offline checks
are not a completed playthrough; live tests remain pending.

| Gig | Native ID |
| --- | --- |
| Psychofan | `sts_hey_gle_03` |
| Going Up or Down? | `sts_hey_gle_05` |
| Bring Me the Head of Gustavo Orta | `sts_hey_rey_01` |
| Sr. Ladrillo's Private Collection | `sts_hey_rey_02` |
| Race to the Top | `sts_std_arr_03` |
| Scrolls before Swine | `sts_wat_nid_07` |
| Family Heirloom | `sts_wbr_hil_06` |
| Greed Never Pays | `sts_wbr_jpn_12` |

U10 provides bounded original beginnings. Completed gigs, earned choices/items
and existing owners stay intact. Unsupported unfinished stages defer; U10 does
not reset them or silently restart them. Native fixer tiers, approaches, devices,
optional outcomes and rewards still apply. A permitted or issued owner does not
prove that a call or quest has played successfully.

Six exact quest items also protect existing progress: Psychofan's guitar,
Going Up or Down's scandium cores, Scrolls before Swine's recording, Family
Heirloom's bootleg and keys, and Greed Never Pays' cracker. Any retained item
blocks a fresh entry. The runtime uses variant-aware inventory queries, and the
native entry checks the inventory again immediately before dispatch.

Family Heirloom additionally requires genuine pre-Tower completion of its
excluded Ghost Town prerequisite. The new runtime can record this in a save
before either Tower journal starts, using two settled observations of the actual
completed Ghost Town root and native completion facts. It never fills in missing
history on an existing post-Tower save. Without that witness, Family Heirloom
defers even when Ghost Town currently appears completed. Journal timestamps are
not treated as completion-time evidence.

Psychofan uses a scoped copy of its scene and Johnny workspots to remove his
independent cigarette/lighter presentation while retaining voice, choices and
timing. The existing Johnny body policy remains in charge of his projection.
Its native post-gig crime-scene companion is retained. Family Heirloom keeps
Dan's native interaction, optional car outcome and complete embedded after-phase; no duplicate
vendor or Wakako completion credit is added.

Ladrillo and Greed retain their native retaliation consequences. The package
restores only their two previously disconnected selectors within the existing
mod-owned gang controller. It preserves the controller identity, other selectors,
native queues, cancellation, encounters and return loops. New admission waits
for the relevant native queue/chase/cancel state to be clear. Existing owners are
not restarted. Saved-owner use of this updated graph still needs a live test.

Use the same working post-Tower branch and make a new disposable manual save.
Close menus briefly to allow the ordinary safe activation checks. No ending
replay or forced facts are needed for regression checks. Truly unstarted gigs
need an eligible branch; completed gigs are protection controls, not fresh tests.
Do not reset completed quests to manufacture a fixture.

Optional read-only CET inspection:

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.GigsU10.GigsU10"); print(s:Status()); print(s:Inspect("sts_hey_gle_03"))
```

Substitute any ID from the table. `preTowerPrerequisiteKnown=false` on Family
Heirloom is an intentional deferral. No diagnostic command writes progress.

For each eligible gig, check its original approach and call, interactive objects,
completion/outcome choices, one-time reward and subsequent cold reload. For
Psychofan, check Johnny's voice without body or floating props. For Ladrillo and
Greed, test a naturally earned retaliation outcome, cleanup and reload. Verify
previously restored activities and the working H10 arrival remain intact.

Recovery starts with U10 before S27/DT1/S26/S25 and older packages. With the game
closed, validate the exact recovery transaction first:

```powershell
& '.\prealpha\gigs_u10\deploy.ps1' -Mode ValidateRollback -RecoveryRoot 'C:\Users\Ayong\Documents\cp77 modding\tower ws\recovery\gigs_u10_01'
```

Use the same command with `-Mode Rollback` only when rollback is wanted. File
rollback does not undo gameplay saved afterward. The
[final assessment](../research/gigs_u10/assessment_01.json) binds the installed
hashes and receipts. Final U10 source/build/test/deployment files are frozen;
future changes require successor versions.

The package contains 42 resources and 28 boot entries in three additive files,
with one existing mod-owned retaliation resource overlay and no official
resource overrides. Build `u10_02` binds native06, presentation03 and runtime02.
Validation passed 1,445 native payload checks, 3,532 policy cases and 1,522
independent review checks. Both the scoped compiler and full installed script
compiler passed, including EquipmentEx; 88 generated data arrays were read back.
The resource audit checked 104 exact native resources, both official journal
metadata variants and both Arroyo district variants, plus 86 installed archives
and all 62 XL files. Arroyo differs only in two explicitly checked cooking
metadata fields; every used graph and context is equal. All 42 packed resources
were read back, and 107 native source files were freshly decoded.
Installation and recovery passed 106 deployment cases and 125 checks, including
interrupted installation and path-link handling. Actual closed-game validation,
installation, three installed-file hashes and rollback validation also passed.
