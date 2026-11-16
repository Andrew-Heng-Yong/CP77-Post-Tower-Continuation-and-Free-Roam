# Post-Tower cyberware treatment

Candidate 06 is an offline-compiled, two-script overlay for the pinned `QP2_JOHNNY_LOAD_REPAIR` installation. It implements the [four treatment levels](../../docs/cyberware_treatment_20261111.md) with stock items. The overlay is staged under [candidate_06/overlay](candidate_06/overlay). The installation and saves were untouched.

| Level | Candidate behavior |
| --- | --- |
| 1 · Remove | Native unequip for all combat arms, arm styles and all Hands cyberware at the initial handoff. The item and attached parts stay owned. The stock arm customization state is switched off after slot clearance. |
| 2 · Disabled | The exact installed instance stays in its slot. Equip packages, attached-part packages, native variant stats and identified active abilities are suppressed. Fitting, upgrades and part changes are blocked. Manual ripperdoc removal follows native unequip and preserves parts. |
| 3 · Limited | The three stock tattoo families can be refitted for appearance after the one-time handoff receipt. Titanium Bones retain +20 carry capacity. Chitin retains +15 Armor, Subdermal Armor +5 Armor and Carapace +10 Armor. The candidate also locks upgrades and part changes for limited items. |
| 4 · Functional | The stock Personal Link and Basic Kiroshi Optics use the native behavior. |

The residual bonuses are provisional flat values in [CyberwareTreatmentSettings](CyberwareTreatment.reds). The policy preserves native capacity and equipment admission. Existing saves keep their current inventory and loadout. If the prior profile already unequipped an implant, this migration leaves it in owned inventory because the old equipped-slot identity cannot be reconstructed. The new receipt applies only to the initial Arms and Hands handoff. HP and stamina progression is separate work.

## Verification

- The two overlay sources compiled with all 148 registered REDscript inputs. The [compile result](compile_06/result.json) pins the source registry, compiler, base caches, source inputs and compiled output. The [overlay verification](candidate_06/verification.json) pins both changed files.
- Source comparison preserved the Tower admission and safe-state gates, the R3 profile identity and saved perk fields, and the existing vitals code. The installed hashes matched all 51 core files and 26 required files after compilation.
- The [TweakDB audit](scope_records_02.json) matched 72 named stock records and 11 License to Chrome side upgrades to their expected equipment areas. The three tattoo families retain their stock attachment and appearance records.
- Runtime verification still needs retained item and part readback, arm and tattoo appearance, disabled action and passive-stat readback, one residual modifier per instance across reload and removal, and the explicit No Nerf transition. Compilation does not establish the runtime effects of the native per-item stat calls.

## Native perk dependencies

The scoped License to Chrome refund preserves inert implants in the first two Skeleton slots while keeping native sale admission. An occupied perk-owned third Skeleton slot, an installed Cellular Adapter that requires Built Different, or another native capacity refusal can hold a fresh covered setup at its refund step. The controller reports the waiting perk and leaves the equipment and refund ledger intact. A live fixture for those cases is required before deployment.
