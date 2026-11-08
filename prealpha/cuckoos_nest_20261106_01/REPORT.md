# Cuckoo’s Nest follow-up

The four missing connection sources are inherited vanilla data on branches outside the serialized entry route. The guard’s keycard now has a verified source and objective binding. The separate item ID in Dixon’s dialogue scene remains unresolved. The evidence supports retaining the existing route.

## Four orphan connections

The older vanilla export, current standalone vanilla phase and current district-embedded phase agree across all 20 story graphs. Each has a literal null source for the four edges below. The handles listed here belong to the standalone exports.

| Input | Connection / destination handle | Downstream path |
| --- | --- | --- |
| `2.In` | `2464 / 2463` | Reception trigger through `19.False` into scene node 3 |
| `11.In` | `2405 / 2404` | Upper trigger into scene node 12 |
| `13.In` | `2425 / 2424` | Computer-room trigger with no outgoing edge |
| `15.In` | `2444 / 2443` | Window trigger into scene node 16 |

Nodes 3, 12, 14 and 16 all refer to the same depot ending in `scenes\sts_std_rcr_02_scene.scene`. It had zero providers across 134 indexed archives. The standalone phase runs from `0.Out` to `17.In`, then from `17.False` into phases 8 and 9. That input reaches none of the orphan nodes. Within the active phases, the authored upper and window triggers, reception scene and Dixon scene have separate callers. Reconnecting the orphan upper trigger to `17.False` made its provider-less scene reachable in the negative control.

The installed QR19 entry, credit and two map resources match their original U9 payload hashes. Entry node `65004.Out` feeds `7.In1`, which calls the same native phase used by the Rancho Coronado parent. The resolved base-game phase SHA256 is `092E7837308FD4F4988A231AEBBFB0E24837B1108429EE10B554AFBA089B7792`. The installed and historical Dixon scene bytes match at `3C325491DDB2700BC9C6A61348482EDDECD108B9E86DF1A29783C6D6D831D13B`. The scan establishes a single provider for each of the 14 resolved target paths.

## Dixon’s inventory predicate

- The authored enemy community assigns `enemy_005` to `Character.rcr_02_enemy_security_keycard`. Its loot table `LootTables.rcr_02_keycard_loot_table` contains one guaranteed `LootTables.rcr_02_keycard_doc` item with no player prerequisite. The resulting item is `Keycards.rcr_02_keycard_doc` (`118782818377`). Native phase `root/9/3:49` waits for at least one and sends `49.Out` to the key objective’s `13.Succeeded` input.
- Native phase `root/9/5/22:52.dixon` calls the Dixon scene. After entering the room, scene node 86 checks whether the player holds at least one item with ID `114327022403`. Neither the current nor the historical base and expansion TweakDB contains a named definition for that ID. Prior QR8 analysis confirms that the native comparison can still test a well-formed numeric ID. The original name, provider and possible legacy or runtime inventory presence remain unknown.
- Node `86.True` leads through 158 directly to choice 6. Node `86.False` waits at 152 for the original `enemy_005` defeated, killed or unconscious condition, then proceeds through 88, the 4-meter proximity check at 244, and two authored dialogue lines at 192 before reaching choice 6. Both routes can reach the Jason-ready fact writer at 82. Substituting the known keycard would bypass the guard wait, proximity check and those lines for key holders. The identified stock drop comes from the same guard the fallback already checks.

A repair would require a donor that identifies the original item or orphan connections, or a repeatable failure on the active native route. An informative gameplay failure would be Dixon remaining unresponsive after taking the native guard’s keycard and approaching her within the authored distance after that guard is down. Graph reachability does not establish live scene or saved guard behavior.

## Reproduce

From the workspace root in PowerShell, use the installed QR19 archive and ArchiveXL file, both current and historical TweakDB pairs, and the pinned historical quest exports. The capture uses WolvenKit 9.1.0 through the helper-only entry point. The Python step checks the captured hashes, original graph, item records and two mutation controls. Use fresh output names.

```powershell
$stage = '.\prealpha\cuckoos_nest_20261106_01'
$ptfrPython = 'C:\Users\Ayong\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe'
pwsh -NoProfile -File "$stage\capture.ps1" -OutputName capture_02
& $ptfrPython -B "$stage\verify.py" "$stage\capture_02" "$stage\verification_02.json"
```

The recorded run passed 41 checks. [Verification](verification.json) · [Providers](capture_01/providers.json) · [TweakDB evidence](capture_01/tweakdb.json) · [Earlier numeric condition analysis](../quest_restoration_qr8/worker_c/REPORT.md)
