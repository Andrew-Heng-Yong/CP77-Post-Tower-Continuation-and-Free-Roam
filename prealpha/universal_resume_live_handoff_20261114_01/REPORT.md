# Step 3 save boundary and paired quest waits

15 November 2026. A workspace-only v0.1.5 save observer compiled from the pinned, installed v0.1.4 source. The build passed **10 save-window fixtures, 51 checkpoint regressions and 15 registration regressions**. A separate fixture using two saved timers from The Beast in Me passed **10 native clock checks**. The installed baseline readback matched 51 Core files, the v0.1.4 checkpoint DLL and 26 required files. [Observer build](run_build_01/assessment.json) · [Paired timer results](run_pair_01/fixture_checks.txt) · [Installed manifest](../universal_resume_checkpoint_probe_20261114_01/deployment_01/installed_manifest_01.json)

## Native save boundary

The pinned engine's save pipeline at RVA `0x2FC88A0` submits PreSaveSystems, SaveSystems and PostSaveSystems. The SaveSystems worker reaches `0x2FC8524` and calls each configured system's writer at virtual slot `+0x138`. The quest writer at `0x2C9F364`, real-time writer at `0x2AAC958` and game-time writer at `0x2AA8D00` occupy that slot in their respective vtables. The build checks the function boundaries, call sites, vtable pointers and hook prefixes against the exact executable. [Engine and source pins](run_build_01/assessment.json)

The observer forwards each original call. It records which of the three writers ran within each native save job, duplicate writer calls and writers observed outside that job. Its fixtures cover nested invocations, concurrent workers and exceptional return. This supplies a way to verify serialization coverage in game. Activating timer suspension still requires a verified save admission path that can defer a request while the native wait and its callback are changing owners. It also requires handling a save already in progress. [Observer implementation](NativeSaveObservation.inc) · [Scope fixtures](run_build_01/SaveWindowChecks.txt)

## Saved quest fixture

The read-only search inspected 24 manual and point-of-no-return saves. It bound eligible stock phase paths and direct timer registrations against the current registry, then checked saved timers and journal evidence. Point of No Return Save 0 had the sole matching Active quest with a bound direct timer. Its save version is 269. The inspected facts include `q115_active=1` and no recorded positive `q307_ready`. The original race remains an offline fixture until access to a genuine Tower route and original owner support are verified for the playtest. [Save search](run_saves_03/fixture_assessment.json) · [Original race source and dependencies](../quest_restoration_qr3/agents/agent_a/quests/07_nc_underground/contracts.json)

The active branch of **The Beast in Me** waits for the Santo Domingo race at native address `[0,2,82,5,50,77]`. Node 7 starts the two pauses in parallel. Node 8 waits 12 game hours before requesting a content token. Node 9 requires both a Fixer content token and its own 11-hour delay. The old save's clock is 6,119,899 game seconds. Its event-manager rows match the original timer and logical condition.

| Authored wait | Saved node-instance key | Native timer ID | Game seconds remaining |
| --- | --- | --- | ---: |
| Node 8 direct wait | `0E0014EF00000008` | `177D3` | 41,162 |
| Node 9 logical child | `0E0014EF00020009` | `177D2` | 37,562 |

The native phase lookup uses the low 16 bits to find the top-level handler and passes the original 32-bit key to the handler's sublookup when the upper bits are present. The timer constructor includes that full key in the native node-instance address. The existing checkpoint samples direct registrations, so it would omit the logical child from its timing samples even when its raw node-instance map contains that timer's ID. A live handoff for this branch must carry both timer identities and the Fixer-token condition. [Saved keys and native checks](run_pair_01/assessment.json)

The clock fixture installs both records on the same native-layout clock, exercises a failed hold when the earlier timer is already due, then holds both together. Both resume with their original remaining time and the one-hour separation. Each fires once after the modeled reload. The actual race controller, content-token delivery, game save job and ending were outside the fixture. Live deployment and gameplay qualification remain pending. [Paired checks](run_pair_01/fixture_checks.txt)
