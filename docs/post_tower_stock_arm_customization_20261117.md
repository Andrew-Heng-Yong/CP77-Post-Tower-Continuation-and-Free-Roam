# Post-Tower stock arm customization retest

RED4ext loaded ArchiveXL 1.28.7 on Cyberpunk 2077 2.50 at 14:04 Toronto time. The Tower handoff unequipped Advanced Electric Monowire at 14:42:23 and verified conservation of the implant and its three parts. The log confirmed the stock hands attachment at 14:42:55 and recorded the full automatic Photo Mode cycle through setup cover release at 14:43. The user reported missing arms in free roam while holstered, before a vehicle or console action. [ArchiveXL installation](../prealpha/archivexl_arm_state_20261117_01/REPORT.md)

| Console time | Test | User observation |
| --- | --- | --- |
| 14:47:26 | Vanilla personal link appearance event, with the link put away | Arms remained missing |
| 14:50:17 | Vanilla fists draw, then normal holster | Arms remained missing in both views |
| 14:52:54 | `CyberwareCustomizationSystem.RestoreCyberwareCustomization(true)` | Arms returned on foot |

CET recorded the requests and the accepted guard on the successful command. The saved switcher was `None` at index `0`. The stock guard also confirmed inactive customization, no MaxTac arm appearance and no equipped arm cyberware or arm style. The visual recovery is user-reported in this session. Running the final operation by itself on a fresh Tower handoff still needs its own check. [Vanilla customization apply](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/base.script#L221775)

The installed `CyberwarePolicy.ArmAppearanceSettled` checks the saved settings and can report ready when these fields are at their defaults. Its caller requests the native customization reset only when that check fails. The successful call reapplies the existing defaults to the live player. A prospective automatic repair can queue that call once after normal on-foot control and the stock hands attachment are ready. With the current Photo Mode flow, the equivalent checkpoint is after the return to the gameplay camera and before releasing the setup cover. Gate it on the same live player, default arm customization and the stock attachment. The command was tested with `switcherName=None`.
