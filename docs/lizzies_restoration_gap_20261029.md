# Lizzie's bar restoration audit — 2026-10-29

Read-only audit requested by the user. The user observed a bouncer without interaction, no receptionist, and no NPCs inside, and explicitly confirmed the visit was at night (18:00–06:00). No restoration was implemented or installed; no game launch, save edit or quest-fact write was performed.

The receptionist and interior population have a concrete gap in current PTFR coverage. The bouncer's native controller is also absent from that coverage, but a missing **Talk menu** alone is not proof of a bug: the native repeat routes are automatic lines rather than repeatable dialogue menus. The user's observation does not identify the actor's persistent community entry or establish whether these automatic lines were also missing.

## Current installation and evidence

The installed combined archive has 1,564 members and matches the current beta package, SHA256 `007CC2DFDBC1AB709ACFA34AB96E990E5ED210327AE2E15491C62D3BA672063E`. The installed ArchiveXL file and `PTFR_B0StoryEight.reds` also match the package. A scan of all 1,493 packed questphase, scene, community, sector and streaming-block payloads finds Lizzie-specific references only in `towercontinued\b0_story_eight\mateo.questphase` and its service scene. The other 71 members were indexed but were outside those payload types.

A fresh census of 134 installed archives finds exactly one provider for each of the 31 selected native/external resources. Full archive-key comparison finds no shared key between PTFR's 1,564 members and Lizzie's Braindances' 1,409 members. This rules out direct replacement collisions between those two archives, not all possible runtime interactions.

Primary evidence: `diagnostics/lizzies_restoration_audit_20261029_01/assessment_01.json`, `providers_01.json`, `ptfr_scan_01.json`, `installed_sidecar_hashes_01.json`, the raw/JSON extracts and compact graph records in the same directory.

## Native ownership and missing coverage

The native Kabuki community parent calls `wat_kab_lizzies_bar_phase.questphase` at `wat_kab_phase.questphase root/71/7`. That leaf separately starts the default communities, location/opening-hours controller, scenes, performance controller, and the q000/q004/q105 story states. The post-q105 `default` entry reaches the base controller and the after-q105 population. These are not combat-event workspot families restored by WA3.

| Area | Native controller and behavior | Current assessment |
|---|---|---|
| Receptionist | `lizzies_default.questphase root/19/2` activates `#wat_kab_com_lizzies_default:mox_reception`, record `Character.lizzies_mox_female_reception`. The community schedules zero at 06:00 and one at 18:00. `lizzies_scenes root/57→56→59→60` separately waits for the actor and reception trigger, plays `greeting_var_2`, and rearms after departure. | Both the population owner and greeting owner lack a PTFR counterpart. Nighttime confirmation excludes the ordinary daytime schedule explanation. |
| Interior NPCs | The `base` route in `lizzies_default` owns staff, DJ, patrons and waitresses. Its `after_q105` route uses root `29→14→24→25→26→27`, with departure cleanup `30→31…35→36→37→29`, for 12 additional Mox/customer entry groups. Their schedules are also zero by day and populated at night. | Missing community ownership explains the reported empty nighttime venue at source level. Workspot restoration alone would not activate these entries. No exact live headcount is claimed. |
| Bouncers | `lizzies_scenes root/29` activates `bouncer_quest_01/02`; root/17 controls approach, combat exclusion, opening-hours responses, first-entry state and q105 handoff. It calls `q004_01_meet_the_lizzies.scene` and `q105_01a_bouncer.scene`. | Controller coverage is missing, but the present actor was not identity-matched. The ordinary `in_club_opened` route has six reachable nodes, three random line sections, and no choice node; `in_club_closed` has a start and a line section, also no choice node. Restore appropriate automatic behavior if pursued, not an invented permanent Talk menu. |

The bouncer owner reads `q004_nightclub_accessed`, `q004_nightclub_entered`, `q105_01_active` and `lizzies_bar_closed`. Those values were not captured from this visit. The location owner ordinarily maintains opening/closing state, doors and a local no-combat restriction. Its absence is a related coverage gap, but no new door or restriction malfunction was reported or proven here.

## Mateo is already covered

The historical September exclusion was superseded by the S4 service implementation. Current PTFR contains Mateo's separate spawn set, service owner and adapted scene. It requires earned `wat_kab_foodshop_02_default_on > 0`, `q004_done > 0`, no competing `PTFRB0S4MATEO_QuestOwns`, and the normal Tower/safety guards. It activates `#wat_kab_foodshop_02` within 80 metres. It does not populate the club's community entries. If “no NPC inside” includes Mateo, his availability/owner/streaming state is a separate unresolved runtime question, not an absent implementation.

## Lizzie's Braindances interaction

The 13:50:23 RED4ext log records `LizziesBDs` loaded at 13:50:25 and successful script compilation at 13:50:30. That confirms the earlier DLL load failure is resolved for that run; it does not prove every mod quest/scene activated.

The installed ArchiveXL injects its launcher at the game quest roots. The launcher performs its script handshake and story-entry gates, and has a terminating wait on `q115_point_of_no_return >= 1`. Its main phase waits for the club trigger and 18:00–06:00 before starting the menus. Current launcher state and termination history were not captured; a successfully loaded DLL alone cannot settle them.

The add-on's `lizzies_bds_recepce.scene` contains no NPC actor definitions: it is a menu scene, not the native receptionist's population owner. A scoped scan of its questphase/scene/community/sector/entity payloads found no `mox_reception` or receptionist-record reference. It does add native mood-scene actors and extra Mox/outside groups and controls `lizzies_bar_waitresses_off`. Those shared controls would need coordinated ownership in any future PTFR restoration. No direct archive collision or proof that the add-on caused the missing receptionist was found.

## Scope of a future repair, not implemented

The narrow candidate would restore the eligible base/post-q105 community lifecycle, receptionist greeting, appropriate repeat bouncer responses and their required location/workspot support. Preserve schedules, departure cleanup, original story outcomes and existing Mateo service. Reconcile the add-on's shared actors/waitress flag before assigning another owner. Do not restart the full Kabuki root, replay q000/q004/q105, spawn Judy/Evelyn/Johnny indiscriminately, or change story facts just to make the bar busy.

This audit establishes source omissions and their consistency with the user's nighttime observation. It does not claim a live-tested repair, identify the observed bouncer conclusively, or prove the reason Mateo or the add-on menus might be absent in that save.
