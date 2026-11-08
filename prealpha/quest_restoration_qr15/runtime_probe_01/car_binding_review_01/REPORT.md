# Exact broken-car binding

**The original car is now bound to an exact typed native node and quest prefab.** Its current live registration and completed startup state remain unknown; JF01's short-reference result is not evidence that the car is absent.

The exact EP1 vanilla streaming-block descriptor2179 names `base\worlds\03_night_city\_compiled\default\ep1\quest_f9f56e7ec2bde6db.streamingsector`, under the Quest-category owner `#sts_ep1_03_gunfight_streetstory`. That same prefab appears in the original `sts_ep1_03_phase.questphase` ancestor's three prefab declarations. The sector's sole current provider is `ep1_1_nightcity.archive`; its raw SHA256 is `DF1953FF62B1CC18949F797B3D70981CA39457335178860D11E96D8D06A0ECA9`.

Native node98 is **worldPopulationSpawnerNode**, `isVehicle=1`, `spawnOnStart=0`, record `Vehicle.v_standard2_archer_quartz_disabled_interactions`, appearance `archer_quartz__basic_poor_2_4`. Actual setup datum98 binds it to globalNodeID **17433794865907239043** and this full reference:

```text
$/03_night_city/c_pacifica/combat_zone_prefabUEX7DCY/container_zone_prefab4PZIADQ/loc_sts_ep1_03_gunfight_prefabDSNH7OA/loc_sts_ep1_03_gunfight_openworld_prefab3P2OSDA/#sts_ep1_03_gunfight_streetstory/#sts_ep1_03_gunfight_broken_car
```

The car is in the base node range before boundary99, rather than the descriptor's optional `interior_trigger` range. It is still quest-prefab scoped. This is a source binding, not proof of a currently acquired prefab lease.

## Important decoding correction

The captured sector is version0x44. Default WolvenKit9.1 JSON decodes its setup NodeIndex using an older layout and returns101out-of-range indices. The actual current2.5 layout is pinned in `codeware/src/Red/StreamingSector.hpp`: stride0x90, packed node index at0x70 masked with0x7FFFF, globalNodeID at0x58. An independent Python reader verifies the .NET byte extraction and all101indices. NodeRefs array order is also different from node-definition order: the car reference is array entry96, while its definition is node98. Joining by array position would bind the wrong node.

No resource was corrected, repacked or promoted. The extraction is inspection-only. A first diagnostic guard failed because PowerShell treats a boxed CBool as truthy; `binding_01` remains preserved. `binding_02` checks serialized numeric values and passed. `binding_evidence.json` records34passing input/layout/graph checks and a wrong-node-property mutation control.

## Native lifecycle and read-only discriminator

Original gameplay root/1:101.Activate→102.VehicleSpawned(count1)→103.visual destruction(`accumulate=0`)→104.door interaction disable is exact. Later openworld root/4:575/578 Deactivate the same spawner; native clue handling references it as an entity. The selected55fact projection supplies no dedicated completion receipt for the car startup chain.

`GetPopulationSpawner` is the correct supported getter family for the typed population-spawner target. A single query using the exact **full reference string** can discriminate short-alias/context resolution from a registered full target. If resolved, existing `IsActive`, `IsInitialized` and entity-ID getters add current spawner evidence. A full-reference UNRESOLVED result remains unknown, and does not authorize creating/resetting it. Use a string reference rather than a bare Lua numeric globalID, which exceeds exact double-integer precision. No new game API was called here.

The empty sector `persistentNodes` list does not prove the car's population/save state absent; registry, restored/spawned entity IDs and executing quest owners are separate. Neither active flags nor a full binding alone proves earlier visual-destruction/door commands completed, or justifies replaying them.

## Bounded native-semantics lookup

An exact `gameCommunitySystem` name lookup found string RVA0x32deb48 and registration function0x16cdd44. Its metadata-table candidate was not established as the concrete system instance vtable; candidate slot bodies were rejected rather than labelled as activation implementations. After this one exact mapping attempt, Activate-versus-Reactivate idempotence remains UNKNOWN. Distinct facade slots and a boolean active field do not prove ordinary Activate safe to replay. Raw lookup and rejection evidence are preserved under `native_semantics_01`.

Two vanilla providers exist for the exact all.streamingblock depot. The basegame provider lacks this sector descriptor; the EP1 provider contains it. Both payloads are retained. This report explicitly establishes the EP1 vanilla descriptor association; it does not claim an independent executing mount-precedence trace.

No runtime source, package, installed file, save, fact, game process or gameplay was changed. The next decision should use this exact car/prefab binding, not repeat the generic JF01 short-reference test.
