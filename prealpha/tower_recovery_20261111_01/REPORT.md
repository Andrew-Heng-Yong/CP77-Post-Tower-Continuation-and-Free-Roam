# Tower recovery and cyberware

Installed as `QP2_TOWER_RECOVERY` over `QP2_JOHNNY_LOAD_REPAIR`. One transaction replaced the two consolidated restriction scripts, the combined archive and its ArchiveXL registration. The other 47 Tower paths and all 26 required dependencies matched the predecessor. All 331 save files matched their pre-install hashes. Rollback copies of the four replaced files verified. [Installed manifest](deployment_02/installed_manifest_01.json) · [Rollback readiness](deployment_02/rollback_readiness.json)

## Recovery

The save-local clock starts when V has genuinely completed The Tower and the retained session has restored normal control. An existing post-Tower save starts its clock on its first eligible load because older versions recorded no recovery start time. The clock advances by whole elapsed in-game days, counts time skips and retains the highest elapsed day in the save.

| Day | Maximum Health | Maximum Stamina |
| --- | ---: | ---: |
| 0 | 25 | 25 |
| 14 | 71.67 | 48.33 |
| 15 | 75 | 50 |
| 30 and later | 125 | 75 |

The defaults use a linear curve. Duration, starting caps, ending caps, curve and bruise day are adjustable in [RecoverySettings](RecoveryVitals.reds). The caps use owned, unsaved stat modifiers that are reapplied from the saved day. The existing downward-only Health pool correction guards against a refill when the engine rescales the pool. Stamina uses native regeneration and consumption. Saved no-vitals opt-outs remain eligible for the profile and facial recovery without the cap modifiers.

## Facial injury

The stock final scene sets `CCBN_FinalScene` using `questCharacterManagerVisuals_SetBrokenNoseStage`. A private ArchiveXL phase waits for verified Tower completion and the recovery request, then uses the same native node with `CCBN_Disabled`. REDscript sends the request at the first safe opportunity on or after day 14. The phase writes its own receipt after the native action returns. No stock ending resource or quest fact is replaced by the phase. The receipt establishes native action dispatch. The visible result and cold-reload behavior require in-game verification. [Serialized action and guard](scope_review.json) · [Archive readback](archive_01/archive_readback.json)

## Cyberware and verification

The combined build carries forward the [four treatment levels](../cyberware_treatment_20261111_01/REPORT.md), including the initial removal receipt, cosmetic tattoo refits and provisional limited-function bonuses. Implants already unequipped by the prior profile remain in inventory. A native perk sale can hold fresh covered setup when it would remove an installed Cellular Adapter or an implant in the perk-owned third Skeleton slot.

All 148 registered REDscript inputs compiled. Archive readback verified the 1,737 retained payloads and one private phase. The generated phase ID 51547 passed collision checks against the native root and all 828 previous bindings. Thirteen transaction fixture actions passed, including exact rollback, interruption between replacements, interruption before the receipt and running-game refusal. Health and Stamina pool behavior, implant effects, and visible bruise removal remain unverified in game. [Compile result](compile_01/result.json) · [Transaction fixtures](fixture_results_02.json) · [Installed readback](deployment_02/verify.json)
