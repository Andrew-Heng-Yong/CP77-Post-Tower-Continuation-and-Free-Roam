# Step 3 Cassius handoff offline result

15 November 2026. Checkpoint **v0.1.12** implements the shared handoff for The Gig at Cassius and passes its offline test. The fixture uses the original collection listener and ancestor registrations from the preserved Manual Save 31 Reed cutoff export. The offline test used the installed v0.1.11 baseline. [Subsequent v0.1.12 deployment](DEPLOYMENT.md) · [Selected stage and lifecycle](../quest_resume_stage_selection_20261115_01/REPORT.md) · [Installed baseline](../quest_resume_cassius_shared_20261115_01/staged_01/deployment_01/installed_manifest_01.json)

The handoff reserves the Cassius family at the genuine cutoff. After Tower completion it waits for confirmed original-listener retirement, quiet stock updates, both replacement prefab leases and the live Cassius service owner. It reattaches the native inventory wait and requests a journal change for the quest, phase and pending tattoo objective. The earlier payment and two succeeded objectives stay settled. Fresh journal readback and the native owner receipt gate callback release. On failure, the replacement listener is removed and the fallback stays fenced until journal rollback is confirmed and the callback queue has drained. The two existing adapters still require their own permits at all four native entry and recheck nodes. [Ownership and transaction source](source_01/NativeStageSelection.inc) · [Journal and adapter bridge](CassiusScript.reds.inc) · [Legacy entry checks](run_07/legacy_entry_gates.json)

| Check | Result |
| --- | --- |
| Native build and exact compiler inputs | PASS. Candidate DLL SHA-256 `0FBB3A38AFED941CA34F588D1CDE0BFCFFD272F159A27A5FEDC14019042742EB`. The v0.1.11 baseline, pinned engine, 51 Core paths, Atelier companion and 26 dependencies were checked before and after. [Native assessment](run_07/assessment.json) |
| Native fixtures | 130 passed, including 13 handoff cases. Covered early removal, a competing owner, incorrect or unready prefab support, a fresh journal acknowledgement, partial rollback, late callbacks and modeled load. [Handoff cases](run_07/CassiusHandoffChecks.txt) |
| REDscript | All 148 registered sources compiled with the three candidate overlays. The compile used isolated copies with readback of installed inputs. [Compile assessment](compile_02/assessment.json) |

## Run the offline test

Run from the workspace root in PowerShell. The executable runs the 13 handoff cases against controlled native objects with the recorded cutoff layout. It prints one `PASS` per case and returns exit code 0 on success. [Fixture source](CassiusHandoffChecks.cpp)

```powershell
& '.\prealpha\quest_resume_cassius_handoff_20261115_01\run_07\CassiusHandoffChecks.exe'
```

To rebuild with the pinned v0.1.11 installation, its compiler and the preserved cutoff export, run the three scripts below. Use unused attempt numbers for `run_*` and `compile_*`. These scripts produce the overlay, verify its script hash header and write their build products and assessments under this workspace directory.

```powershell
$candidate = '.\prealpha\quest_resume_cassius_handoff_20261115_01'
$testPython = 'C:\Users\Ayong\AppData\Roaming\uv\python\cpython-3.14.6-windows-x86_64-none\python.exe'
& $testPython "$candidate\prepare_overlay.py"
& $testPython "$candidate\build.py" --attempt 8
& $testPython "$candidate\compile_redscript.py" --attempt 3
```

## Remaining acceptance

Real prefab streaming and lease behavior, journal delivery, the original inventory listener's response to normal tattoo collection, and in-game save/reload still require gameplay evidence. Step 4 covers offline implementation and qualification across all four selected resume types. The final Step 5 check runs the integrated handoff through genuine Reed cutoff, Tower cleanup and credits in the same session. It verifies quest advancement, reload and one-time rewards. [Roadmap](../../ROADMAP.md#mid-quest-resume-after-the-tower)
