# Developer knowledge base

Maintained 29 October 2026. Start with [current state](current-state.md). This is a navigation layer over preserved source and evidence, not a claim that historical commands can be rerun unchanged.

| Task | Read |
| --- | --- |
| Behavior, ownership, saves, profiles, housing | [Invariants](invariants.md) |
| Resolve requirements or conflicting status | [Conflicts and supersessions](conflicts.md) |
| Compile REDscript, collect dependency inputs | [REDscript toolchain](redscript-toolchain.md) |
| Extract/decode/edit/cook vanilla resources | [Vanilla resource workflow](vanilla-resources.md) |
| Trace a quest, entry, phone or cleanup | [Quest and phone investigation](quest-investigation.md) |
| Apply the reviewed marker/encounter setup rule | [Boolean setup admission policy](../prepared_encounter_policy_20261108.md) |
| Inspect native saved graph stores and their limits | [Native saved graph state](native-saved-graph-state.md) |
| Build/read back the combined archive, validate XL IDs | [Consolidated build](consolidated-build.md) |
| Perform or design a static parity audit | [Static parity audits](static-parity-audits.md) |
| Remove Johnny dialogue and V responses after The Tower | [Implementation plan and dialogue index](../johnny_dialogue_removal_plan_20261107.md) |
| Package, install, preserve files, roll back | [Packaging and deployment](packaging-deployment.md) |
| Find relevant historical evidence | [History index](history-index.md) |

## Procedure status vocabulary

- **Recorded PASS:** a preserved result for exact historical inputs. It is not a fresh verification of today's inputs.
- **Current baseline verified:** the instruction-maintenance preservation report checked the named current files; no build or gameplay run is implied.
- **Derived procedure:** the command/API shape is taken from inspected successful scripts, but a fresh staging directory and current inputs still need validation. Do not execute placeholders literally.
- **Historical/obsolete:** retained for explanation or regression tests; not a current build/deployment recipe.
- **Blocked/unverified:** missing input, stale path, decoding failure or absent runtime evidence. Do not turn it into PASS by inference.
- **User-reported PASS:** bounded to what the user actually tested. The latest PH3 success does not certify all contacts, saves or future upgrades.

Every workflow below names prerequisites, existing commands/source references, outputs and checks. Commands that mutate outputs are for separately authorized engineering work, not this documentation-maintenance task. No generic “build everything” command has been established for the current consolidated successor.

## Local conventions

Repository root: `C:\Users\Ayong\Documents\cp77 modding\tower ws`.
Game root: `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077`.
Save root: `C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077`.

Verified Python executable used by recent local procedures:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' --version
```

`python` can resolve to a broken WindowsApps alias. Recheck executables and required libraries before use; do not install dependencies or change global configuration implicitly. PowerShell scripts use `pwsh -NoProfile -File <existing-script>`; inspect parameters and top-level behavior first. Paths in historical JSON may be absolute and machine-specific. Report missing ignored/local evidence rather than inventing it.

Keep one current pointer in `current-state.md`; keep proof JSON, manifests and dated reports immutable. Put new observations in a new dated report. Do not rewrite old PASS/UNVERIFIED records to reflect later knowledge.
