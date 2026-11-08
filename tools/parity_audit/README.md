# PTFR static parity auditor

Read-only analysis of a pinned consolidated installation and its vanilla providers. This tool writes only fresh diagnostic outputs. It never builds, deploys, launches the game, decodes/writes saves, changes facts, or repairs quest resources. Python uses the standard library; archive access uses the existing WolvenKit API through `build_phase2a.ps1 -HelpersOnly`.

## Run

Prerequisites: PowerShell 7, Python 3.14, existing WolvenKit 9.1 package under `research/sidejobs_s28/tooling/wolvenkit_9_1_0/package`, a current candidate containing `package`, `archive_source`, and `install_manifest_01.json`, and the local native archives. Historical cache exports are optional acceleration only: payload and JSON hashes must match. Work from the repository root. Use a **new** output name and never point it at a previous candidate or release directory.

```powershell
$audit = 'diagnostics/vanilla_parity_NEW'
$py = 'C:/Users/Ayong/.local/bin/python3.14.exe'
& $py -B tools/parity_audit/__main__.py prepare --out $audit --candidate prealpha/phone_studios_ph3/candidate_01
pwsh -NoProfile -File tools/parity_audit/capture.ps1 -OutputRoot (Join-Path $PWD $audit)
pwsh -NoProfile -File tools/parity_audit/capture_parents.ps1 -OutputRoot (Join-Path $PWD $audit)
& $py -B tools/parity_audit/__main__.py refine --out $audit --capture capture.json --next-pass pass_02
```

`prepare` pins installed/package/source bytes, the current whitelist pointer, historical decisions, mappings and protected inputs. `capture` emits all archive providers, raw hashes, exports, errors, missing references and readbacks. `capture_parents` obtains native parent IDs separately without expanding the entire global quest. `refine` independently walks **exported JSON**, detecting references missed by binary string scanning. If it creates another pass, execute:

```powershell
pwsh -NoProfile -File tools/parity_audit/capture.ps1 -OutputRoot (Join-Path $PWD "$audit/pass_02") -ResumeCapture (Join-Path $PWD "$audit/capture.json")
& $py -B tools/parity_audit/accept_incremental.py $audit capture.json pass_02/capture.json pass_02_closure_check.json
```

If incremental acceptance emits `next_pass`, capture that directory with `-ResumeCapture` pointing to the latest capture, then call acceptance with previous/current capture paths and its emitted `incremental_closure_pass_NN.json`. Repeat in bounded passes until `capture_pointer.json` exists. Every extension retains prior provider/hash evidence and independently reads new exports. Missing references and decode failures remain in the result even when the query closure is complete. Final protection checks must validate reused installed inputs. A changed baseline requires a new run.

```powershell
& $py -B tools/parity_audit/test_auditor.py
& $py -B tools/parity_audit/corpus_tests.py $audit
& $py -B tools/parity_audit/run_tests.py $audit
& $py -B tools/parity_audit/__main__.py analyze --out $audit
& $py -B tools/parity_audit/source_inventory.py $audit
& $py -B tools/parity_audit/xl_inventory.py $audit
& $py -B tools/parity_audit/reconcile.py $audit $audit
& $py -B tools/parity_audit/full_handlers.py $audit
& $py -B tools/parity_audit/evidence_index.py $audit
& $py -B tools/parity_audit/review.py $audit
& $py -B tools/parity_audit/scan_embedded.py $audit
& $py -B tools/parity_audit/__main__.py review --out $audit
& $py -B tools/parity_audit/__main__.py protect --out $audit
& $py -B tools/parity_audit/report.py $audit
```

Expected evidence: `summary.json`, resource/provider/dependency inventories, normalized models, complete catalogue and quest/stage JSON+CSV, tagged original/private handler JSONL+CSV, source identities, difference registry, mutation results, independent review, protection result, and `REPORT.md`. Verification is bounded by the statuses below. The current run additionally retains failed extractor trials and a corrected analysis successor; see its report rather than treating intermediate files as final.

## Interpretation

- `PASS`: named static comparison proved; never gameplay success.
- `APPROVED_DEVIATION`: exact reference-only relocation or hash-pinned corrected donor with evidence. Target behavior is reviewed separately. Installation alone never authorizes a delta.
- `FAIL`: structural/contract invariant fails under the recorded model. MAY-execution does not prove the route actually runs in a save.
- `CONDITIONAL`: source route/owner/admission feasibility not universally established.
- `OPAQUE`: asset/format is unsupported or presence-only; content parity is unproved.
- `UNKNOWN`: missing source identity, dependency, provider precedence, authorization or other evidence.
- `LIVE_ONLY`: playback, serialized-owner liveness and actual runtime migration need external evidence.

The model preserves handles, nested phases, edge multiplicity, named entry sockets, scene socket stamps, conditions, facts, journals, rewards, metadata and root/instance prefabs. Cut edges do not activate their destination. A separate raw traversal checks omitted graphs and references; literal fixtures provide independently specified edge/reachability oracles. Corpus mutations exercise real pinned resources and historical CR1/PH1/PH2/PH3 fault classes in memory.

This is an executable conservative auditor, **not a proof of universal vanilla parity**. It does not solve arbitrary REDscript/control-flow conditions, timed concurrency, interrupt fairness, shared leases, complete actor/world placement, all YAML variants, dynamic references, saved-owner liveness or one-time reward delivery. Native data can itself contain dangling/cut/localization references. These remain visible rather than being silently repaired or counted as gameplay defects. Root association uses ID/path/journal candidate evidence; identity ambiguity prevents certification. See the per-run adversarial report and unresolved coverage.
