# Investigating native quests, entries, phones and cleanup

## Q1 — Trace an owner and its complete lifecycle

**Status:** procedure derived from verified investigations; each new quest needs its own source/provider evidence.

**Prerequisites:** exact native quest/journal ID, current installed owner/entry depot, matching vanilla providers, fresh investigation outputs and a precise symptom/time window. Follow [V1/V2](vanilla-resources.md) for extraction/export. Do not start a new quest audit merely by reading this guide.

Start with the current source/manifest, then use deterministic queries:

```powershell
rg -n 'EXACT_FACT_OR_DEPOT' tools redscript docs -g '*.ps1' -g '*.py' -g '*.reds' -g '*.md'
```

Replace the search token with the actual identity. Ignored native evidence may require `rg --no-ignore` against a **specific** research/diagnostic directory. Avoid an unbounded model read of every dump.

Existing graph readers: `prealpha/phone_support_ph1/model.py` provides `model(path)` for quest-phase JSON with handle dereferencing, nested graphs and edge validation. `diagnostics/phone_restoration_preparation_20261029_01/analyze_01.py` also parses scene graphs. The former does not replace the latter for scenes. Old `tools/test_rite_g2.py` imports `lupa.luajit21`; importing that module is not a dependency-free way to reuse one helper. Inspect imports/top-level actions before reuse.

**Procedure:** identify actual connected entry sockets; traverse nested phases and external dependencies; locate original admission conditions, local prefab/scene ownership, saved receipts, triggers, cut/termination routes, outcome branches, cleanup and rewards. Preserve AND/OR semantics. Review unreachable branches separately. Trace resource-root and ancestor prefabs as well as individual nodes.

**Expected outputs:** source-pinned inventory, normalized graphs and a path/condition/lifecycle report. **Verify:** no dangling handles, missing external graph silently treated as empty, duplicate providers, unmatched NodeRefs or forgotten nested edges. Actor presence, active journal and receipt facts alone do not prove executing ownership. The Raymond native trace is a regression example: two writers of the same killed fact retired different trees.

## Q2 — Trace phone request → handler → acknowledgement → cleanup

**Status:** recorded mechanism from PH1–PH3, with bounded runtime observations.

**Prerequisites:** caller phase/scene, contact's initializer/controller/scene, native cleanup integration and shared phone/studio ownership. Exact fact names may be `audio_...` or `holo_...`; do not assume a visible character name equals the internal contact identifier.

Inspect these existing records before changing phone support:

- `diagnostics/phone_restoration_preparation_20261029_01/cases_02.json`: controller/request/acknowledgement bindings and native init/cleanup nodes. `cases_01` is preliminary.
- `prealpha/phone_support_ph1/build_03.ps1` and `semantic_01.py`: scoped listener/cleanup mechanism; historical, not a current rerun command.
- `prealpha/phone_merge_ph2/regression_01.py`: generated-ID failure/alias regression.
- `prealpha/phone_studios_ph3/build_01.ps1`, `semantic_01.py`, and `diagnostics/phone_expansion_ph3_20261029_01/ownership_census_01.json`: shared prefab obligations.

**Procedure:**

1. Find the exact positive start/end request writers and actual connected caller input. Check both scene and phase branches, rather than scanning whole-resource strings as if every branch executes.
2. Find the handler's read conditions and scene input, then the **real** start/end acknowledgement writer and caller wait/clear. Include reveal flags, counters, rejection and interruption handling.
3. Trace matching cleanup in the existing shared reset chain, including counter comparisons. Mark/Janet cleanup is inline in native EP1 cleanup; looking only for external cleanup resource references misses it.
4. Check existing/native/saved owner retirement, persistent claim, fresh versus already-issued admission, and required actor/studio/marker/workspot/camera/lighting support. A copied initializer node's empty instance-prefab array does not remove the native resource root's studio prefabs.
5. Verify resource and generated-registration IDs, then use timestamped merge/fact observations to locate the actual stall. Preserve queued calls; never fake their acknowledgements or bypass downstream doors/objectives.

**Expected output/checks:** per-contact contract and negative controls for inactive/completed/failed/non-Tower contexts, already-issued requests, pending ends, interruptions, duplicate owners and reload. Static condition evaluation is not an engine scheduling simulation. A call can consume its request and increment counters yet still stall on missing presentation support.

Concrete regressions to preserve:

- PH1 missing listeners/cleanup, PH2's Mark `40560` injection collision, and PH3's missing shared root studios are three different failure layers.
- Dennis already-issued admission must not wait on its own unfinished-call interruption flag.
- Meredith's raw request node3300 is unreachable from the actual Stout farewell input2197; do not report it as another active-call defect.
- Organitopia's native `phone end 01` reaches checkpoint/journal steps and the two authorization/open commands. Restore the dependency; do not force the doors.

## Q3 — Interpret logs without inventing live proof

**Status:** verified read-only capture convention. **Prerequisites:** existing user run and readable logs; no game launch required.

Copy the relevant logs to a fresh diagnostic directory, record source/copy times and SHA256, then query the copies:

```powershell
rg -n 'EXACT_CONTACT|EXACT_QUEST|holo_setup|holo_interrupt' $copiedScriptingLog
rg -n 'EXACT_PHASE|Can.t merge phase' $copiedArchiveXLLog
```

Source examples: `diagnostics/organitopia_ph1_failure_20261029_01/` and `diagnostics/phone_expansion_ph3_20261029_01/`. Separate attempts at reload boundaries. A snapshot before the request or after a reload cannot establish the failed attempt's live state. Absence of a logged transition is not guaranteed observation of every fact or proof of a measured wait duration. Logs showing counters do not transcribe spoken dialogue or prove rendered holograms.

**Expected output/checks:** concise timeline, exact matching sources/owners and explicit uncertainty. Keep the user's report alongside the logs, including apparent disagreement; do not erase one to make the diagnosis simpler.
