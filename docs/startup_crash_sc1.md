# SC1: crash during covered startup

The October 24, 17:07:29 crash is traced to the private H1 Corpo Plaza purchase
scene, `towercontinued\housing_h1\native\corpo_purchase.scene`. The setup cover
was visible at 41% / five of twelve checks. That is the last displayed setup
stage, not the identity of the crashing subsystem.

The native dump identifies `scnSceneResource` and its depot hash
`831467AE67C510EA`. The resource contains zero NPC definitions and one player
definition, still numbered **3** after the NPCs were removed. The current native
caller passes that ID directly to a lookup that subtracts the NPC count and
indexes a 176-byte runtime entry. It therefore accesses player entry 3 in a
one-entry table. The dump confirms both addresses and the incorrect definition
pointer. Its bogus facial-animation array count, 410,592,809, exactly matches
the engine assertion: 9,854,227,416 bytes at 24 bytes per entry. The actual
player definition's facial-animation array is empty.

This is a defect in our scene pruning. It is not evidence that the loading UI,
perk-refund operation, graphics driver, or current cosmetic workarounds caused
this crash. The profile and housing systems run concurrently.

SC1 repairs all nine H1 scenes with this defect: four purchase scenes, four
apartment service scenes, and Kerry's earned-access service scene. Actors keep
their definitions and behavior; their local indices and every typed actor or
performer reference now agree with the native tables. Eighteen stale debug
symbols for removed actors are omitted. No excluded NPC is restored. Scene node
IDs, connections, purchase conditions, prices, payment receipts, quest-owner
resources and persistent REDscript fields are preserved.

The installed change is one archive:
`archive/pc/mod/00000000_TowerContinued_Housing_H1.archive`.
Its previous SHA-256 was
`E8F4F535A9A24B8C080360D68C8993B19EDE12366118284E5A9CE683A0CA523E`;
the installed SHA-256 is
`76A4DE057573AE13CB698AED6E757454A07D95DBC00A94F9D5F63DA484CBDA07`.
Nine private scene resources change; the other eight archive members remain
byte-for-byte identical. The LC2 cover/main archive, scripts, core frameworks,
cosmetics, caches and saves are unchanged.

Validation includes 1,531 native/index/semantic checks, packed-resource readback,
and 14 real installer fixture actions including interrupted installation and
rollback protection. Every repaired scene rejects the old out-of-range index,
and reversing only the documented index/debug-symbol edits reproduces its full
original decoded data. Validate, Install, Verify and ValidateRollback passed;
636 protected files, including all 241 save-directory files, were unchanged.
There are no REDscript changes, so the successful installed script stack does
not need another compilation for this archive repair.

An audit covered 89 scenes in the installed Tower archives. The nine H1 scenes
are repaired. An additional non-dense actor list exists in the legacy
`streetkid_seat_s1/seat.scene` resource; it was not the resource in this crash
and is unchanged. Its reachability and any separate repair remain unverified.

The same session also confirms useful LC2/HS1 progress: the cover rendered,
native fade/control/camera handoff advanced, Body and Relic refund journals
completed, and a verified 158-row JSON snapshot was exported with origin
`post_ending_fallback`. This is not a pre-ending-history capture. The remaining
profile, housing, final readiness barrier and full gameplay transition have
not yet passed live testing. No measured full-startup speedup is claimed.

Next test: cold launch and load the same retained save used for the failed
attempt. Let the cover finish, check gameplay and housing, then use a new manual
slot for a reload test. Previously active H1 service-scene save/reload behavior
still needs live validation; no saved owners are reset or restarted by SC1.

Recovery: run `prealpha/startup_crash_sc1/deploy_01.ps1 -Action ValidateRollback`,
then `-Action Rollback` if needed. Backup: `recovery/startup_crash_sc1_01`.
Undo SC1 before undoing the older H1 archive package. The separate cover chain
remains LC2 → LC1 → HS1; SC1 rollback restores the defective H1 scene indices.
File rollback does not undo changes made by gameplay to a save.

Evidence: `prealpha/startup_crash_sc1/candidate_01/assessment_01.json`,
`diagnosis_01/cause_02.json`, `diagnosis_01/cause_02.asm`, `scene_audit_01/audit.json`,
`build_02.json`, `tests_01.json`, and `deployment_tests_01.json`.
The initial workspace build stopped because a readback directory was missing;
build_02 is the completed package. Native opcode transcription assertions were
corrected against actual executable bytes before the final checks passed.
No failed candidate was installed. Final proofs are pinned; use successors.
No public package or release was updated.
