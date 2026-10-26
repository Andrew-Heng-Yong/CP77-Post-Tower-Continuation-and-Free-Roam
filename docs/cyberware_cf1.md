# CF1: preserve enhanced Skeleton implants during PTFR removal

CF1 is locally installed, and the reproduced setup failure now passes in game
as of 25 October 2026. It adds only
`r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePreservationCF1.reds`.
Existing CD1, H6, HS2, H5, FS1 and other installed files remain unchanged.

## Local live result

The user reported "fixed". At 16:21:32 and 16:21:33 Toronto, CF1 logged its
native cleanup guard for T1000 and Pain Distributor respectively. CD1 confirmed
each exact item/data identity, hash and seed remained unchanged, quantity stayed
1, and both attached parts retained their exact identities and slots. Both
equipment slots emptied and both removals returned 1. Setup reached Ready at
16:22:07 after 42.312500 simulation seconds, with no CD1 failure in this attempt.
This also confirms that the wrapped native cleanup route is exercised by both
problem items. The installed script matches the pinned candidate.

Evidence: `diagnostics/alpha_cyberware_20261025_01/local_pass_01/assessment_01.json`,
SHA-256 `D702E467DE4387C3ACB3DB26906D84314E3B29641DE17217720E41E2CA72D141`.
This validates the local reproduction. It does not establish the remote tester's
installation, save/reload persistence, or exhaustive active-effect cleanup.
No repeat of the basic ending reproduction is needed.

## Reproduced failure

The user equipped `Items.AdvancedT1000Legendary2` in Skeleton slot 0 and
`Items.AdvancedPainDistributorLegendary2` in slot 1 before q307's thug encounter.
At 16:04:56 Toronto, CD1 recorded T1000 quantity 1 and two attached parts before
ordinary unequip, followed by `readbackDefined=false quantityBefore/after=1/0`
and an empty equipment slot. The conservation fault latched immediately; the
Pain Distributor was not attempted in this run. Faceplate removal had passed.
The exact enhanced instance disappeared; this does not establish the absence
of every native base item elsewhere in inventory.

The local native source and stock data identify a matching deletion path:
Skeleton slots' `OnInsertion` packages bind `PowerUpCyberwareEffector`.
`UnequipItem` removes slot packages before clearing the equipment slot.
The effector's `Uninitialize` reads that slot and deletes its item when the record
has no `SideUpgradeItem`. Both enhanced target records match this pattern.
The native power-up route ordinarily retains a base item while creating a side
variant. PTFR's exact-instance conservation promise did not account for this
cleanup. Directly spawning a variant can also leave no base companion.

The runtime loss is confirmed. Source/data tracing identified this native method;
the subsequent CF1 runtime logs confirm that route executes for both targets.
A body-mod cause has not been demonstrated.

## Change and verification

CF1 wraps only that effector's teardown. It skips deletion only when owner/data
match, the Skeleton slot is in range, and its exact ItemID matches the transient
ID already set around PTFR's native removal call with the denied policy active.
All other calls delegate to the unchanged native method. Native slot/item stat
cleanup, part retention and all CD1 quantity/part comparisons still run.
It retains the already-existing enhanced instance, creates no replacement item,
does not reconcile or replace a base companion, and does not clear faults.
No new saved fields are introduced.

Full 92-source SCC compilation, including EquipmentEx, passes. Compiled SHA-256:
`69048139F144775725FADF354506BB475C1CCE21746BC0B6646D5C649C5A574A`.
Readback comparison preserves 13,836 other class bodies after normalizing method
order/generated wrapper numbers, the original removal methods, the fallback
effector body, and every existing persistent field. Verifier 01 initially
treated compiler method ordering as a change; successor 02 resolves that without
changing the candidate. All 14 actual installer fixture actions pass.

Validate, Install, Verify and ValidateRollback pass. All 696 protected files,
including 277 save files, remain unchanged during deployment. No game launch,
save/fact edit, framework/archive change or public release update was performed.
Proofs: `prealpha/cyberware_cf1/candidate_01/assessment_01.json`, SHA-256
`6ECB083B73E883F4AAAE24F687E3B9A038C0457BF04A625F281CD8DFDD7A73A5`.
Diagnosis logs/data: `diagnostics/alpha_cyberware_20261025_01/local_repro_02`.
Final candidate/proofs are pinned; use successors for further work.

## Recovery and remaining coverage

The original pre-failure retry has passed as recorded above. Broader removed-effect
checks and persistence through a new test save/reload remain separate coverage.
Installing CF1 does not restore an item lost in an already-saved failed attempt.

Close the game. Roll back CF1 first, before CD1 or older R1 removal packages:
`prealpha/cyberware_cf1/deploy_01.ps1 -Action ValidateRollback`, then
`-Action Rollback`. The added file is recoverably moved under
`recovery/cyberware_cf1_01`; no existing script is replaced. File rollback does
not undo saved inventory changes. Other recovery chains remain separate.
