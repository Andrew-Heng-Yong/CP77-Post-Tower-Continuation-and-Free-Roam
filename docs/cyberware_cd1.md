# Alpha cyberware setup stop and CD1 diagnostics

The subsequent local attempt reproduced exact enhanced-item loss during native
unequip. CF1 is now installed and both target removals pass locally; see
[the diagnosis, fix and recovery record](cyberware_cf1.md). The original CD1
diagnostic files and tester ZIP remain unchanged.

## Correction to the equip verification command

The user clarified that they are before q307's thug scene and supplied live
R1 status `mode=0 active=false pending=0 fault=false`. The prior inference from
the last flushed log that the current attempt was blocked by PTFR after ending
completion was incorrect. The assistant also supplied the wrong equipment area
for readback: both target records resolve to `MusculoskeletalSystemCW` (Skeleton)
in the local stock database, while the command inspected `IntegumentarySystemCW`
(Skin). Empty skin slots do not establish failed equipment of these targets.
Check the record-derived area or Skeleton slots next. Both records have a native
`HumanityAvailable` variant prerequisite, but its failure has not been shown.
Read-only inspection evidence: `equip_area_03.json` in the investigation folder.

## Local reproduction log, 25 October 2026

The user's 15:31:47–15:40:30 Toronto session ran game 2.50, compiled successfully,
and shut down normally. Setup reached Ready at 15:37:38 after 42.968750 simulation
seconds. CD1 recorded successful removals of only `Items.MaskCWPlusPlus` and
`Items.AdvancedSmartLinkLegendary`, preserving quantity and all prior part
identities/slots. This session contains no CD1 FAIL, negative removal result, or
setup stop.

CET recorded four equip requests for the two tester-failing records, but neither
`Items.AdvancedT1000Legendary2` nor `Items.AdvancedPainDistributorLegendary2`
entered CD1 removal. Submission without a visible Lua error does not establish
successful equip or continued equipment through the ending. Refused equip and
later native removal cannot be distinguished from these logs. The tester's
failure remains unresolved; the successful local run did not exercise those
target removals. Verify actual skin-slot contents after equip and before the
ending, or obtain the tester's own CD1 failure rows.

Copied logs and their hashes are retained in
`diagnostics/alpha_cyberware_20261025_01/local_repro_01/assessment_01.json`.
Both installed CD1 hashes still match the package. This inspection made no
runtime, save, fact or installation changes and did not launch the game.

## Local installation, 25 October 2026

At the user's explicit request, the two CD1 files are now installed locally.
The current H5/FS1 stack passes full 91-source compilation including EquipmentEx;
compiled SHA-256 is
`9C07BDB0A24D3D850063BC7D0A98615FF681B05DA0EF3B76242AE88732B0BFA6`.
All 14 installer fixture actions and actual Validate, Install, Verify and
ValidateRollback pass. All 679 protected files, including 265 save files, remain
unchanged. The game was closed; it was not launched and no CET commands ran.

Recovery uses `prealpha/cyberware_cd1/deploy_local_01.ps1` with
`-Action ValidateRollback` followed by `-Action Rollback`, restoring the two
original files from `recovery/cyberware_cd1_local_01`. Local installation proof
is under `prealpha/cyberware_cd1/build/local_install_01`; the prior alpha-only
package and evidence remain unchanged. The runtime failure is still unresolved;
the next step is one controlled reproduction and the CD1 log rows.

## Original tester investigation

The tester supplied a log excerpt on 25 October 2026 after running the published
`v0.1.1-alpha.20261024` from a pre-ending save. Their screenshot shows `Setup
stopped`, arrival/optics/housing faults `0/0/0`, blank Body details, and inactive
HP overrides. The tester reportedly has a body mod; their exact game patch and
mod/framework versions remain unconfirmed.

## Confirmed blocker

The excerpt contains three negative cyberware removal results:

- `Items.AdvancedT1000Legendary2` fails twice.
- `Items.AdvancedPainDistributorLegendary2` fails once in an intervening attempt.

Each `result=-1` immediately precedes `Setup stopped`. In both fresh transition
attempts, five other implants pass quantity and part conservation first. Camera
and control acknowledgements reach `1`; the three displayed native fault flags
stay zero. The cover returns from check 5 to check 2 because its early fault guard
rejects the cyberware policy's latched fault. The percent is a checkpoint count.

`EquipmentSystemPlayerData.PTFRR1Remove` returns `-1` if the item readback is
missing, quantity changes, part count changes, or an original part identity/slot
pair is absent after ordinary unequip. `CyberwarePolicy.Poll` latches a fault on
that result. The original popup omits this cyberware fault and strips the state
prefixes from Body/Profile status. `Smart Link stat=0` is expected policy output;
HP overrides being off does not identify a health failure.

The excerpt does not distinguish the failed comparison or prove actual item
loss. It does not establish that the body mod caused the issue. A read-only local
stock TweakDB inspection finds both records, with a shared variant and equipment
area; that is not a read of the tester's loaded overrides or evidence of cause.

## Diagnostic package

`prealpha/cyberware_cd1/prepare_01.py` derives two successor files directly from
the pinned published alpha ZIP. Historical sources and the release ZIP remain
unchanged. CD1 logs bounded pre/post item and part identities, quantity, equipment
slot readback and the exact negative-return branch. The popup names all six fault
checks and logs unabridged Body/Profile/Cyberware status on entry into the stop.

The package is `dist/cyberware-cd1/PTFR-CD1-diagnostics-for-alpha.zip`, SHA-256
`989E5B3E196698F6B872CC2EC3E35A854DB9D7F67EA6E6532B806229B80EEEF8`.
It contains two REDscript replacements, instructions and before/after hashes.
It is a diagnostic overlay, not a gameplay repair, and is expected to retain the
same safety stop. Its original preparation did not install it or publish it
online; the subsequent local installation is recorded above.

## Verification and next step

Full local SCC compilation of 90 sources, including EquipmentEx, passes. The
compiled removal method matches the previous alpha compiler output after only
the added diagnostic log statements are removed. Source comparison preserves
every removal gate, native call, inventory comparison, return value and saved
field, and all cover fault/readiness conditions. ZIP readback passes. Compiled
SHA-256: `B99B66B86D1CF9C7589E8621D20CA854B6428ED449AA4DF32AEF1CE83671D3ED`.
This does not establish live compatibility with the tester's exact stack.

Close the tester's game, back up the two files outside `r6/scripts`, install the
overlay and run one attempt from the original untouched pre-ending test save.
After the stop, preserve `bin/x64/plugins/cyber_engine_tweaks/gamelog.log` before
another launch. The `[PTFR_CyberwareCD1]` rows will identify the failed comparison
for a narrowly scoped repair. Do not clear the fault or force completion. File
rollback restores the two original alpha files; it cannot reverse saved gameplay.

Private evidence is retained under `diagnostics/alpha_cyberware_20261025_01` and
build proof under `prealpha/cyberware_cd1/build/candidate_01`. During that
preparation no save, runtime fact, archive, framework or local game file was
edited, and the game was not launched.
