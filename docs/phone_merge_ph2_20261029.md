# Mark Bana listener registration correction

29 October 2026. The user retried Organitopia after PH1 and reported no Mark Bana call and a closed entrance. Latest logs confirm a PH1 registration failure.

ArchiveXL rejected `towercontinued\phone_support_ph1\mark_bana.questphase` at 17:20:50 and again at 17:23:20 Toronto time: “node with the same id already exists.” Its generated phase-node ID is **40560**, already assigned to `towercontinued\native_gigs_u9\sts_wat_kab_101_map1.questphase`. The five other PH1 listeners logged successful merges. The prior depot collision scan did not check these generated 16-bit registration IDs; that was a validation omission.

The attempts at 17:22:21 and 17:25:54 set `audio_mark_bana_calls_v_start_activate` and `sts_ep1_08_show_bana_avatar` from zero to one. No Mark start/end acknowledgement or end request appears afterward in the captured log. The 17:23 reload separates the attempts. This confirms the missing listener registration and reproduces the request-without-acknowledgement symptom. It does not prove that every other runtime gate will pass once registration is corrected.

## Correction

PH2 registers the byte-identical listener through `towercontinued\phone_merge_ph2\mark_bana_listener.questphase`, which generates **61197**. The original resource remains packed for preservation but is no longer registered. The existing Watson map registration remains unchanged. PH1 receipt names, admission guards, native controller and cleanup, and gig admission checks are unchanged.

The registration inventory checks 824 additions to the EP1 root and its five native node IDs. Two independent CRC implementations reproduce the old collision and agree on the new ID. All six phone listener registrations are unique in the corrected inventory. The XL differs by one path substitution only.

Full readback preserves all 1,572 PH1 members byte-for-byte and adds one identical alias, for 1,573 members. A fresh 134-archive scan found no alias depot collision. No REDscript changed and no new compilation is claimed. The earlier PH1 native graph/state proofs remain applicable because their resource payloads are unchanged.

Build and deployment evidence is under `prealpha/phone_merge_ph2/candidate_01`; the final installation state is recorded in `installed_assessment_01.json`. Raw captured logs are under `diagnostics/organitopia_ph1_failure_20261029_01`. The beta ZIP remains unchanged.

## Recovery

With the game and launcher closed, roll back **PH2 before PH1**, then PH1 before LR2 if further rollback is wanted:

```powershell
pwsh -NoProfile -File prealpha/phone_merge_ph2/deploy_01.ps1 -Action ValidateRollback
pwsh -NoProfile -File prealpha/phone_merge_ph2/deploy_01.ps1 -Action Rollback
```

Recovery files: `recovery/phone_merge_ph2_01`. File rollback does not undo saved gameplay. No game launch, direct quest-fact write, force-open operation, or save editing is part of this correction. Actual call delivery and native door opening remain live unverified after installation.
