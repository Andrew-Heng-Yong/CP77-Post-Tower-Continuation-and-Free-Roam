# REDscript compilation and dependency resolution

## R1 — Inspect the proven full-input compilation

**Status:** recorded PASS, 28 October WA3/CO1; current-input recompilation not performed in this documentation task.

**Prerequisites:** local ignored evidence, game SCC/cache, all source dependencies, and the exact staged candidate. Read `prealpha/world_support_wa3/compile_script_02.py`, `candidate_02/compile_inputs_01.json` and `candidate_02/compile_01/result.json`.

Read-only evidence commands from the repository root:

```powershell
Get-Content prealpha/world_support_wa3/candidate_02/compile_01/result.json -Raw
Get-Content prealpha/world_support_wa3/candidate_02/compile_inputs_01.json -Raw
```

**Expected outputs:** recorded status PASS, exit 0, 112 staged `.reds` sources, compiled cache hash and exact input hashes. The result also pins the approved CO1 `SetupNewTab.reds` hash. These commands read evidence; they do not compile.

**Verify:** the result/input manifest correspond to one another, candidate source hash matches, and each current dependency has the recorded bytes before reusing that result. Later archive-only successors do not constitute a fresh REDscript compilation. A count alone is not equivalence.

## R2 — Compile a fresh successor offline

**Status:** derived procedure from the proven WA3 script. There is no parameterized current all-project compile command; the historical script hardcodes an existing output and must not be rerun.

**Prerequisites:** a separately authorized build task; fresh task/candidate output; proposed source replacements; readable `GAME/engine/tools/scc.exe`, `r6/cache/final.redscripts` and `final.redscripts.ts`; dependency census. Never write the installed cache.

The historical WA3 script stages `.reds` from these five roots. **This list is incomplete for the3November installed runtime:** LizziesBDs adds17 sources. A fresh dependency census is mandatory; see R4. Historical roots:

1. `GAME/r6/scripts`
2. `GAME/red4ext/plugins/Codeware/Scripts`
3. `GAME/red4ext/plugins/ArchiveXL/Scripts`
4. `GAME/red4ext/plugins/TweakXL/Scripts`
5. `GAME/red4ext/plugins/mod_settings`

Adapt a **copy** of `prealpha/world_support_wa3/compile_script_02.py` into the new engineering task. Change `HERE`, `OUT` and intended candidate replacements deliberately. Preserve installed input hashes, stage the complete set, replace only proposed candidates in staging, and copy both cache inputs into that fresh directory. Do not append one prototype folder to an unrelated old dependency list.

The exact proven SCC argument shape is below. Variables must point to the fresh staged files described above; this is not a ready-to-run command with invented directories:

```powershell
& "$game/engine/tools/scc.exe" -compile $scripts -compilePathsFile $paths `
  -customCacheDir $cache -outputCacheFile "$cache/compiled.redscripts" `
  "$cache/final.redscripts"
```

The WA3 script uses an empty `compile_paths.txt` because the complete copied tree is already under its staged scripts root. This is not permission to omit SDK or external-mod source dependencies.

**Expected outputs:** staged `scripts/`, `cache/compiled.redscripts`, `compile_paths.txt`, `scc.log`, and a new result/input-hash manifest. Require exit 0 and `Compilation complete`; check for compiler errors, warnings relevant to changed behavior, output existence and output hash. Rehash installed sources and cache to prove the compile stayed offline.

**Dependency failures:** inspect the first meaningful error, resolve missing symbol/module to its installed source/SDK version, and verify the complete source tree. Avoid duplicate old/new PTFR modules, omitting EquipmentEx/Atelier, patching external mods silently, or replacing frameworks to make a compile pass. Missing `lupa.luajit21` in Python graph utilities is a separate Python dependency issue, not a REDscript compile failure.

## R3 — Headless compiler/decompiler references

**Status:** historical prototype workflow, not current combined-pipeline certification.

`tools/compile_activity_state_r3.py` records `research/finalboards_dismissal/tooling/redscript-cli.exe` calls:

```text
redscript-cli.exe compile -s SOURCE [-s DEPENDENCY ...] -b BASE_CACHE -o OUTPUT
redscript-cli.exe decompile -i COMPILED_CACHE -o FLAT_SCRIPT
```

**Prerequisites:** the matching executable, base cache and explicitly complete source list. **Outputs/checks:** compiler log and flat script, successful-save markers, expected classes/symbols and unchanged protected inputs. Do not assume its old list of R1/R2/R3 folders is the modern dependency closure. Use the current SCC pattern for modern full-input evidence unless a separate tool/version comparison justifies another path.


## R4 — Current registered-source closure (QR14,3November)

**Status:** verified offline integration PASS for the exact unchanged QR13:02 candidate and current installed dependencies; no installation or gameplay certification.

Independent QR14 review found that `r6/logs/redscript_rCURRENT.log` listed17 `red4ext/plugins/LizziesBDs/Scripts/*.reds` inputs omitted by the earlier five-root offline compile. The logged runtime set is119 ordinary +29 plugin sources =148. QR13's immutable131-source result remains valid only for its narrower input set; its former complete-input wording is superseded.

**Prerequisites:** authorized offline verification, current game compiler/cache and actual registered source evidence, pinned candidate overlay, no source/reparse drift, and a fresh workspace output. Inspect `prealpha/quest_restoration_qr14/compile_integration.py` before adaptation. It verifies the current log set equals both the six staged roots and all `.reds` across enclosing `r6/scripts`/`red4ext/plugins`, copies sources/cache, overlays46candidate scripts and writes only workspace files.

The exact executed command was:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr14/compile_integration.py
```

Its occupied `verification/compile_01` refuses rerun. For a later candidate, adapt an inspected copy into a fresh task and reconcile the **current** registered source set; do not hardcode148 or assume the same frameworks remain installed.

**Expected outputs:** `verification/compile_01/{result.json,scc.log,runtime_redscript.log,compile_paths.txt,scripts/,cache/compiled.redscripts}`. The result records151 installed input pins (148sources +SCC +two cache inputs),148staged source hashes, original-to-staged linkage,17added sources, exact runtime-log bytes and installed-input preservation. Current compiled SHA256 is `6185E254BDB1F98A4371A0DEDB76E09D2958EF6006ECA5D5E8C8EABDE83E6F0F`.

**Verify:** exit0, `Compilation complete`, exact candidate46 overlay, all148 registry/inventory/staging identities and151 current input hashes, output hash, and unchanged game/cache/save files. `prealpha/quest_restoration_qr14/verification/compile_01/result.json` is the current proof, with independent review linked from QR14 readiness. Installer manifest02 additionally refuses added/deleted/linked `.reds`, including a new plugin source root. Missing compiler closure must remain a deployment blocker until resolved; a prior successful compile does not cover an omitted source or a changed dependency.
