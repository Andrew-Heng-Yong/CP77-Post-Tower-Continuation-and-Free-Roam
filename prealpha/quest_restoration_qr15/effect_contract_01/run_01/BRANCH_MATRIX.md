# Jason prepared startup — all native branches

Derived from pinned native `sts_ep1_03_gameplay.questphase`, graph `root/1`. Dispositions are investigation results, not implemented or approved runtime actions.

| Entry target | Purpose | Reachable node IDs | Disposition and missing evidence |
| --- | --- | --- | --- |
| 16 | Hotel-area approach | 16, 97, 120, 123, 138 | Conditional listener rearm. IsInside can immediately re-fire. Its descendants activate friendly/combat entries and change security/crowd state; prior execution is not certified. |
| 30 | Cracked-shard progression | 1, 3, 25, 29, 30, 46, 47, 48, 51, 52, 94, 95, 96, 114, 115, 116, 117, 118, 119, 137, 157, 158 | Preserve native predicate; conditional listener rearm. Native shard>0, then hotel-area wait, authored delays, devices and actors. Do not substitute direct progression or replay elapsed timers. |
| 33 | Native debug alternate | 1, 3, 25, 29, 33, 46, 47, 48, 51, 52, 94, 95, 96, 97, 114, 115, 116, 117, 118, 119, 120, 123, 138, 157, 158 | Keep dormant. Original chicken-test OR only. No synthetic debug facts or use as a prepared-entry shortcut. |
| 54 | Parked-car interaction setup | 54, 57 | Hold pending actor/command state. CharacterSpawned→57, door=invalid. Do not transfer the separately proved node104 normal enum route to this different payload. |
| 86 | Gunfight community | 86 | Preserve activation intent; support rebind conditional. Already-active community Activate guard is proved. Initialization, materialization, saved actors and reacquisition are separate obligations. |
| 92 | Broken community-car interaction setup | 92, 93 | Hold pending actor/command state. CharacterSpawned→93, door=invalid; distinct from population-spawner car101 and node104. |
| 98 | Friendly car door actions | 98, 100, 106 | Hold pending actor/command state. CharacterSpawned→100→106 uses authored door commands. No completed-command certificate recovered. |
| 101 | Population car, visual grid and interactions | 101, 102, 103, 104 | Preserve state; no unconditional replay/skip. 101→102→103→104. False-accumulate replaces grid values and queues a vehicleGridDestructionEvent; scalar grid idempotence does not establish event/history preservation. |
| 113 | Memorial and environment variants | 64, 66, 112, 113, 139, 144, 145, 146 | Preserve existing variants; owner-specific restore conditional. Eight exact variants include memorial_shards and clues_turned_off. Current variant state/loot history cannot be inferred from start_community. |
| 133 | Friendly car01 interactions | 133, 134 | Hold pending actor/command state. CharacterSpawned>=1→134, door=invalid. Wait may already have fired before the cut. |
| 135 | Friendly car02 interactions | 135, 136 | Hold pending actor/command state. CharacterSpawned>=1→136, door=invalid. Wait may already have fired before the cut. |
| 141 | Gunfight crowd exclusion area | 141 | Preserve/rebind conditional. Crowd null-area enable is a different service from quest-prevention toggles; no imported proof from the latter. |
| 142 | Gunfight crowd community | 142 | Preserve activation intent; support rebind conditional. User observed50/50 active entries. This is not live actor count, handler ownership or permission to replay the full startup. |
| 143 | Pre-gunfight community deactivation | 143 | Hold full operation pending lifecycle proof. Existing source proves cancellation of pending matching pairs before the inactive guard. Final inactive state alone is insufficient. |
| 150 | Ambient radio ForceOFF | 150 | Preserve device state; no unconditional replay. Native ForceOFF is an action on an independent RadioControllerPS. A fresh-style restart would request it again without saved-history discrimination. |
| 152 | Three gunfight prevention areas | 152, 154, 155 | Conditional target rebind only. Exact native enable path assigns one Boolean when resolved. Missing area/component returns without application. Full dispatch and persistence are not proven idempotent. |

Shared descendants appear in multiple branches. Counts are not independent gameplay coverage. Node162 is an unconnected deletion marker. The startup graph has no fact-writing node; `start_community` is written in the parallel openworld graph and is not a barrier for these effects.

Native cleanup retains enable=1 at node266 for the meet-Wagner prevention area. That authored value is recorded, not changed or presented as an independently established bug.
