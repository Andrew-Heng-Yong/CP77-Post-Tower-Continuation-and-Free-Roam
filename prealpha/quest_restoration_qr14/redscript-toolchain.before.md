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

The inspected script stages every `.reds` from:

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
