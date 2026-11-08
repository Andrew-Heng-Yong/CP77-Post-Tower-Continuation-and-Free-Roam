# Diagnostic-only installation and rollback preflight

Status: **prepared, not installed**. Core QR8:02 and installed QR9B04 remain unchanged. This task prepared a read-only preflight, not a general installer or a release ZIP.

Selected payload: [manifest_02.json](manifest_02.json), candidate_02, two stable paths under `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/`:

| Leaf | Installed QR9B04 SHA256 | Prepared QR10D01 SHA256 |
| --- | --- | --- |
| init.lua | ACCE8B7E4E1E355BBC6D6F4752FDBCC7BB3034F594B13AB055EC35742D333718 | 1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90 |
| watch.json | AEC4D4921AC64B0C37006E7839DD3F9466457B44A735DFFD4637C4261D5EAED2 | A1AAB30B9F896CD24687D82CC2160D773C04B7193BDDCA71CC933A4C93997AAA |

Candidate_01/manifest.json are preserved superseded preparation: identical Lua, initially broad unqualified contact aliases. Candidate_02 narrows D00 to the sourced Regina ID. Use manifest_02 only. No Core, REDscript, archive, XL or save byte belongs to this replacement.

## Verified read-only procedure

Prerequisites: exact pinned current inputs, existing Python3.14, game and RED launcher closed naturally, fresh QR10 output leaf. No approval is needed to read; approval is required for a later deployment. The script has **no install action**.

```powershell
$py = 'C:\Users\Ayong\.local\bin\python3.14.exe'
& $py -X utf8 -B prealpha/quest_restoration_qr10/preflight.py --expected before --out preflight_before_NEXT.json
```

Expected: `PASS_READ_ONLY_BEFORE_PREFLIGHT`; exact installed before/candidate/rollback-donor hashes; resolved containment and no reparse chain; source/config readback;51 Core +6 dependency pins; all310 QR10-baseline save hashes. The save count is a measured baseline, not a permanent expected project count. Later legitimate gameplay changes require a fresh reviewed preservation baseline, never restoring saves to satisfy this check. Output is one fresh JSON in QR10.

Current result: [preflight_before_final_01.json](preflight_before_final_01.json). [19 negative/fixture controls](preflight_fixtures_03/results.json), independently repeated, cover before/after state, game/launcher running, allowlist, unknown bytes, preserved unknown log, containment/junction and Windows report-output paths/devices. They do not simulate an atomic deployment or crash recovery.

## Authorized deployment requirements — not executed

After explicit authorization, a fresh guarded two-leaf transaction must revalidate before hashes immediately before replacement, acquire an exclusive lock shared with any other deployment, record rollback copies and their SHA pins in a new recovery receipt, stage/hash both files on the target volume, replace only the two leaves, read back both after hashes and confirm protected Core/dependencies/saves/external files remain unchanged. Exercise that actual transaction's interruption recovery on workspace fixtures before using it on the game. Do not create a new Core package or rerun the QR9 installer, whose diagnostics manifest requires an absent target.

The exact reversible change is reviewable now; **a new installation transaction/crash-recovery gate is still required before actual writes**. Existing QR9 recovery remains untouched. The reviewed preflight alone does not authorize or certify an installer.

## Rollback preflight and scope

Before deployment, exact QR9B04 rollback donors already exist at `../quest_restoration_qr9/worker_b/addon/` with the before hashes above; current preflight verifies them. After a separately authorized installation, read-only verification can use:

```powershell
& $py -X utf8 -B prealpha/quest_restoration_qr10/preflight.py --expected after --out preflight_after_NEXT.json
```

Expected: exact QR10D01 target bytes, exact candidate and old donors, unchanged protected inputs. This is a prospective command: it has not been run on the installed game, which still has B04. The fixture after-state did pass.

An authorized rollback must require exact current QR10D01 hashes and the actual recovery receipt, restore only the two recorded B04 files, and verify their before hashes plus preservation. Refuse unknown/changed target bytes. Preserve every QR9/QR10 capture, unknown file and directory. Do not remove the addon folder or roll back the Core. File rollback does not undo gameplay or saves.

## Reproduce candidate and fixture controls

Prerequisites: unchanged pinned QR9B04 source files, current QR10 scripts and existing LuaJIT toolchain. Fresh names only:

```powershell
& $py -X utf8 -B prealpha/quest_restoration_qr10/prepare_successor.py --candidate candidate_NEXT --manifest manifest_NEXT.json
& $py -X utf8 -B prealpha/quest_restoration_qr10/test_diagnostics.py --out tests_NEXT
& $py -X utf8 -B prealpha/quest_restoration_qr10/test_preflight.py --out preflight_fixtures_NEXT
```

Builder writes only a fresh QR10 candidate/manifest. It changes no installed file. The diagnostic test selects candidate_02, so a different regenerated candidate must first be byte-compared to manifest_02; do not label tests of candidate_02 as execution of another source. No wholesale REDscript compilation or unchanged Core archive rebuild was needed.
