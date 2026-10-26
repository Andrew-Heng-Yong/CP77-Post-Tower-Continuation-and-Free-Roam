# S29: remaining 18 side-job entry points

Installed on 25 October 2026. All 18 remaining selected journal entries now have
native entry adapters: 16 quest owners, because the three Sinnerman jobs share
one native quest tree. Entry coverage is now 80/80 gigs and 78/78 side jobs.
This is implementation coverage; quest-tree gameplay verification is pending.

The combined 93-source SCC compile includes EquipmentEX and the installed CF1,
H6/HS2, H5 and FS1 fixes. Native readback checks passed (17,664 checks), as did
archive packing/load order and 14 real installer fixture actions. The package
adds one archive, its XL and one runtime script, and adds a read-only method to
the existing snapshot script. Existing saved fields and snapshot catalogue
fingerprint are unchanged. No game launch, save edit or manual quest-fact edit
was performed. Evidence: [assessment](../prealpha/sidejobs_s29/candidate_01/assessment_01.json).

## Test from the retained post-Tower save

Cold-start the game and load the working save from before S29 installation.
Let normal setup finish. There is no need to replay the ending. Complete the
parent job normally, wait its original time, and check the call/message and
next journal entry. Use a new manual slot at a checkpoint, reload it, and check
that progress continues without a duplicate call, reward, item transfer or owner.

Already completed/failed jobs remain preserved. Jobs active in the accepted
history baseline are not restarted. Unsupported unfinished states defer. A
missing entry can therefore mean an unmet native prerequisite or protected
existing progress; it is not automatically a broken follow-up.

| Entries | Native route to exercise |
| --- | --- |
| Venus in Furs | Earned Meredith outcome → original invitation and No-Tell encounter; no replay of The Pickup rewards. |
| These Boots Are Made for Walkin’ | Nomad route → original car messages, encounter and outcome. |
| Freedom | Original story/race gates, messages, vehicle investigation and resolution. |
| Sweet Dreams | Stefan encounter → original payment, inventory escrow and recovery; check exact belongings after recovery and reload.stfo |
| Nitro (Youth Energy) | Original world trigger/prerequisite → robot sequence, control return and reward. |
| Where Eagles Dare | Original race/vehicle gates → Claire messages and CrystalCoat route. |
| Raymond Chandler Evening | Heroes prerequisite → Pepe encounter, investigation and return; confirm bar service returns. |
| Every Breath You Take | Earned Us Cracks outcome → native delay, Blue Moon call and encounter. |
| Small Man, Big Mouth | Streetkid/Heroes route → Kirk call, meeting and encounter. |
| KOLD MIRAGE | Original freezer encounter → Nix handoff and recovery outcome; check his service returns. |
| Killing In The Name | Original concert/alternate native branches → messages and investigation. |
| Sinnerman → There Is A Light That Never Goes Out → They Won’t Go When I Go | Follow the original choices, delays and Rachel calls through one native owner. Native refusal/failure branches still apply. |
| Don’t Lose Your Mind | Completed Epistrophy → original messages and Delamain sequel; no replay of cab retrieval or Epistrophy payout. |
| This Corrosion | Earned component/recipe breadcrumb → original Yoko route; no forced Canto equipment. |
| One Way or Another | Roads to Redemption outcome → original Nele follow-up. |
| Corpo of the Month | Treating Symptoms outcome → original follow-up reward/pickup branch. |

Johnny's existing voice-only policy is retained. Check for visible independent
props as well as dialogue, objectives, calls and completion. Native actors and
actor IDs remain present for dialogue and scene logic.

Read-only CET status:

```lua
print(Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")):Status())
print(Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")):Inspect("sq025b_delamain_insurgence"))
```

`Issued` means the owner was claimed, not that its quest completed. `Entered=0`
after issuance can mean the original parent gate/timer is still waiting. The
fresh-admission diagnostic becomes false after an owner is issued by design.
For a missing follow-up, record the parent/last objective, chosen outcome,
elapsed in-game time, save/reload point and the relevant Inspect output. Keep
the CET gamelog before the next launch.

## Recovery

With the game closed, run `prealpha/sidejobs_s29/deploy_01.ps1 -Action
ValidateRollback`, then `-Action Rollback`. Backup: `recovery/sidejobs_s29_01`.
Roll back S29 before HS2/HS1 or older phone-support packages. File rollback does
not undo quest progress saved during testing; retain the pre-S29 save.

Final native build: `build/native_04`; runtime: `runtime_06`; compile:
`candidate_01/compile_04`. Earlier workspace candidates were corrected before
installation (serialization references, compiler annotation/imports, Delamain
idle names, one injection-ID collision and load-order comparison). No failed
candidate was installed. Final inputs/proofs are pinned; use successors.
