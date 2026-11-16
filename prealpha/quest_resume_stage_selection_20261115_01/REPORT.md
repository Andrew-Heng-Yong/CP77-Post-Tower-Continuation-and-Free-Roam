# Step 1 fixture selection for mid-quest resume

15 November 2026. Select **The Gig — collect the free tattoo from Cassius Ryder** as the first fixture for the new shared handoff. It is an earned item waiting for collection. **AutoSave-13** is the preferred start if its body still matches the recorded hash. **Manual Save 31** is the manual fallback. The observed 15 November run saved AutoSave-13 about 72 seconds before the genuine Reed cutoff. Manual Save 26 provides an independent earlier control. The save names and hashes identify test inputs only. [Stage evidence](stage_contract.json) · [Live cutoff from MS31](../universal_resume_native_registration_20261115_01/observations_01/REPORT.md) · [Earlier Reed cutoff](../universal_resume_checkpoint_probe_20261114_01/observations_03/REPORT.md)

| Pre-ending fixture | SHA-256 of sav.dat |
| --- | --- |
| AutoSave-13 | `054A32A43CC4C2F55CA09A25832F1C47288F2C3DDA181BA6354328641F3ED8FE` |
| ManualSave-31 | `2E0F3C99AF3E98601CFC6363BBC068635D0C50ABB32F8E81B2A57B056B02F43D` |
| ManualSave-26 | `6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4` |

The three starting bodies have the root, phase and tattoo objective Active, with the first two objectives Succeeded. Wakako's payment and tattoo entitlement are recorded. An inventory scan found neither tattoo variant in the inspected saved inventories. The collection wait still needs a live inventory and earned-stage check at the cutoff. [Inventory readback](run_02/inventory.json) · [Existing earned-stage contract](../resume_dispatcher_rd2_20261112_01/contract.json)

## Original listener and progression

The unique native phase is `base\quest\main_quests\prologue\q001\phases\q101_wakako_reward.questphase`, path `[0,2,82,3,17,151,9,2,5]`, phase hash `1462110622`. RC2 identifies its stock payload in `basegame_4_gamedata.archive` with SHA-256 `CF475689697B624DE0C9DDE71BBD2E67FC92FA8AA798638C2BD051CE581C073D`. The two preserved live Reed exports each contain the same original body and four registered ancestor owners. The body has exactly one listener, node 29 in slot 4519, with no timer or saved instance rows in that body and no quest notifications or resource requests in either sampled export. Physical slot 4519 is evidence from the prior runs. The new runtime must resolve its own current slot. [Source contract](../quest_resume_contracts_rc2_20261114_01/REPORT.md) · [Selected rows and source pins](stage_contract.json)

Node 29 is an inventory OR condition waiting for the player to own at least one `Items.YakuzaTattoo` or `Items.AdvancedYakuzaTattoo`. The authored continuation is `29 → 18 → 4 → 26 → 27 → 1`. It succeeds the collection objective and quest, clears the active fact, sets the done fact and exits. The earlier cash grant and old messages lie outside this reachable tail. Preserve the already-issued histories and let collection complete through this native path. [Provider and graph evidence](stage_contract.json) · [Earlier reward-stage review](../resume_dispatcher_rd2_20261112_01/REPORT.md)

## Cleanup and other owners

| Body from the 15 November run | Recorded state |
| --- | --- |
| AutoSave-13, before Reed cutoff | Native node 29 registered. Collection still Active. S22/S24 have waiting pre-claim registrations and no Issued receipts. |
| AutoSave-14, during The Tower | The root, phase and pending objective have changed to Failed. The original collection listener still exists. |
| AutoSave-15, after cleanup | Original listener absent. The three interrupted journal entries still read Failed. Existing S22/S24 have not claimed the reward. |
| AutoSave-17, after credits | S22 issued at the private owner and now has its own node 29 listener. The collection is Active again. Cassius's service reports enabled/active. |

The transition makes AutoSave-17 a legacy-owner control. A new native restore there would compete with the already-issued S22 route. The earlier RD2 run proved Cassius collection through that adapter and persisted completion. The native fixture must establish its own executing owner and qualification. [Before and after readbacks](stage_contract.json) · [RD2 gameplay result](../resume_dispatcher_rd2_20261112_01/observations/cassius_20261112_2355/REPORT.md)

The two existing entry paths are S22 `[1,27465]` and S24 `[1,24609]`. The installed S22 poll can grant its permit after two qualifying samples of the earned stage. S24's fresh path has its own eligibility and pre-claim listener. A successor needs a coordinated claim that covers the actual native entry gates as well as the permit readers. Preserve an existing issued owner, tolerate its observed pre-claim listeners, and keep both legacy routes ineligible to claim while the shared handoff owns or is restoring this family. Release the reservation for an independently eligible fallback after rollback and listener teardown. Verify that reload still detects the committed native owner without altering the existing receipt meanings. The observed startup ordering gives no basis to depend on winning a race against the poll. [Prior S22/S24 trace](../resume_dispatcher_rd2_20261112_01/contract.json) · [Resume contract](../../docs/quest_resume_contract.md)

Cassius is served by the separate story-service owner at `[1,32493]` and `#pr_wat_nid_ripperdoc_01`. Preserve that owner and confirm vendor readiness. The original reward phase also has `#sq_q001_pr_wakako_reward`, and an ancestor references `#loading_conditions`. The old private adapter omits the separate reward-phase prefab, whose individual placement and lifecycle remain unresolved. The new native plan needs exact lease, retirement and streamed-support handling for those references and must leave unrelated descendants under shared ancestors alone. [RC2 support map](../quest_resume_contracts_rc2_20261114_01/analysis_05/owner_map.json) · [Prefab evidence and limits](../quest_restoration_qr4/groups/G05/quests/sq_q001_wakako/REPORT.md)

## Stage classification and next gate

| Selected type or control | Step 1 disposition |
| --- | --- |
| Earned item waiting for collection | **The Gig, Cassius** selected. Original inventory wait, settled payment, unclaimed starting state and observed Reed cutoff established. |
| Travelling or waiting to talk | **Rite of Passage, Get to the clinic** retained as an EP1 candidate. Existing evidence covers the earned briefing, keycard and successful adapter route. The native pending owner and actor/support state need a separate review. |
| Simple timer | Existing both-clock fixtures remain usable for testing timer primitives. A gameplay candidate needs a verified start state and a supported successor. Falco/Reyes and Claire reply states are excluded controls even though they contain timer evidence. |
| Multiple unfinished objectives | **Epistrophy** retained as a candidate. The MS26 Reed capture has In2, In3 and In7 satisfied. Reconnecting the outstanding owners and preserving the family payout require their own qualification. |
| Terminal or existing owner | The earlier RD2 Cassius completion and the newer S22-issued AutoSave-17 provide distinct controls. Current stage selection excludes a new claim on both. |

[Rite of Passage adapter](../resume_dispatcher_rd5_rite_20261113_02/REPORT.md) · [Timer fixture](../universal_resume_step3_20261114_01/REPORT.md) · [Epistrophy and scoped source evidence](../quest_resume_contracts_rc2_20261114_01/REPORT.md) · [Scope notes](../../docs/mid_quest_resume_four_types_20261115.md)

Carry this contract into a fresh successor. Observe the same pending listener and settled state at the genuine cutoff. After genuine completion, verify retirement, replacement inventory-listener enrollment, correct readiness and sole ownership. Review how the three entries changed by Tower become playable under that same owner. Require exact pre-cleanup history and preserve the two Succeeded objectives and any genuine failure. Qualify collection through a normal Cassius interaction, one native completion, unchanged earlier payment, and save/reload with no duplicate owner or reward. The exact lease, journal handling, legacy-owner arbitration and live advancement are implementation and gameplay qualifications still ahead.

The read-only assessment matched nine unchanged save bodies and two verified Reed cutoff exports. Seven installed manifest paths relevant to this fixture and the engine matched their recorded hashes. Stage selection is complete for this fixture. The new shared handoff still requires a successor before a gameplay test. [Selected stage evidence](stage_contract.json)
