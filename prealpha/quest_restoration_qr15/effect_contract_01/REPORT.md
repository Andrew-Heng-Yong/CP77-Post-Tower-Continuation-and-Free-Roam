# Jason Foreman prepared entry — startup effect contracts

5 November 2026. **The investigation now distinguishes safe repeated scalar assignments from the unproved full startup lifecycle. No prepared-entry repair is justified yet.** The new evidence concerns the exact native effects and all startup branches, rather than repeating the rejected fact, path, PS-key or queue probes.

Installed QR13:02 and QR10D01/D00E remain selected. No runtime resource, script, diagnostic, save, fact or installation was changed. No game/process API, game launch, CUA, compiler, package builder or installer was used. No repeat gameplay test is requested.

## New findings

### The broken-car setup is not a missing-only operation

Pinned original gameplay graph `root/1` still has `101.Out→102.In→103.In→104.In`. Node103's exact `VehicleQuestVisualDestructionEvent` has `accumulate=0`. Current base script passes that argument to both native 15-point grid layers.

The actual executable registration at RVA `0x18AF314` binds thunk `0x2B9981C`, which calls `0x2BB2D84`. The false-accumulate path at `0x2BB2E0B..0x2BB2E0D` directly replaces each selected point. The true path instead adds. The setter subsequently calculates the old/new grid difference, updates associated components and attempts to queue a typed `vehicleGridDestructionEvent` at `0x2BB2E96`. It has no already-applied-node or equal-grid early return around that attempt.

This closes an earlier uncertainty about the actual setter:

- Applying the same template twice to an otherwise unchanged grid produces the same scalar grid. The report does not call that scalar operation inherently non-idempotent.
- That property does not preserve an intervening different grid. The source-derived control changes one point and shows that another false-accumulate application overwrites it. This is an abstract store counterexample, **not a claim that the user's car was subsequently damaged**.
- Even an equal grid still passes through the update/event path. Full event, physics, persistence and observer equivalence has not been proved by scalar equality.
- Skipping node103 unconditionally also fails the pending/unapplied case: its authored template contains nonzero values.

The typed consumer is additionally bound through `0xB4E1DE..0xB4E211`, `0x18400AC` and `0xA1BE2C`. Its state-copy path obtains the vehicle-owned PS handle at `vehicle+0x538`, then copies the current destruction grid into the native `vehiclePersistentDataPS` block at `PS+0x100`. This reuses the independently established owner binding in [the identity investigation](../identity_01/vehicle_data_native/REPORT.md). It does not create a durable quest-node completion receipt or close the existing save-filtering boundary. No claim is made that every downstream callback or cold branch is fully audited.

The executable remains SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. Exact bytes, addresses, provider/export pins and source hashes are retained in `native_01.json` through `native_18.json` and [the analysis result](run_01/result.json).

### Prevention-area enabling has a narrower, positive contract

Current `PreventionSystem.OnToggleQuestPreventionTrigger` forwards the area and Boolean to the installed native method. Its registration/thunk chain is `0x18CC1D8→0x2BC310C→0x2BC4040`.

For a resolved target, `0x2BC408F` assigns the Boolean directly to the area's state byte. Repeating enable on the same valid target does not add a subscription or increment a counter through this setter. The thunk also has explicit missing-area and missing-component returns before the setter. Therefore an issued event is not application proof, and this bounded same-target assignment result does not establish persistence, acquisition or whole-dispatch safety.

This applies to startup152→154→155 and the later157→158 path. It does not apply to the different crowd-null-area service at141/138. The exact native cleanup actions are recorded as authored: nodes261/262/263/265 disable their areas, while266 retains `enable=1` for the meet-Wagner area. That last value is **not silently normalized or declared a new defect**.

### All16startup branches now have explicit dispositions

[BRANCH_MATRIX.md](run_01/BRANCH_MATRIX.md) records every direct output from native startup input0, with exact downstream node IDs and full JSON payload evidence. Independent raw connection traversal agrees with the established normalizer on all62edges. The graph has61nodes; the sole unreachable node162 is an authored deletion marker.

The branches include the separate population car, four other vehicle waits, two initial community activations, pre-gunfight deactivation, eight environment variants, radio ForceOFF, crowd exclusion, prevention areas and conditional progression. The matrix distinguishes preservation, conditional listener/support rebind and held effects. **None of these dispositions is an implemented or approved adapter.** In particular, node104's proved normal door-enum route is not silently applied to four other nodes whose authored `door=invalid` payload differs.

There is no fact-writing node anywhere in this startup graph. `sts_ep1_03_start_community` is written in the parallel openworld graph; it is not a barrier confirming these effects completed. The separate shared courier branch retains its non-exact increment. Rearming that wait still needs its own consumed/pending history and geometry contract.

## Repair decision

A full fresh-style restart is not justified by the fact that ordinary already-active population/community Activate is guarded. A blanket skip is also unproved because some original effects may still have been pending. Relaxing only the current admission gate would additionally leave the frozen HS1 fresh gate unresolved, as already demonstrated in QR15.

A compatible solution must preserve the exact current actor/device/variant states and distinguish pending listeners from consumed ones, while restoring the native support and approach lifecycle. The new Boolean-assignment result can be used as one component of that design; it cannot certify the other15branches. Preserve original identities, histories, timers, one-time rewards, shared courier state, U9/HS1 catalogue fingerprint and existing QR3–QR13 repairs.

No new evidence ties the historical AutoSave-8 body to the JF01/JF02 live session. This investigation does not claim such a binding, a new current-owner observation, a native gig failure, or Ronald-induced entry gating.

## Reproduction and verification

Prerequisites are Python3.14, the existing locally provisioned Capstone package, the pinned executable file, retained QR15 native providers, current base-script decompile and `tools/parity_audit/{common,model}.py`. No new dependency installation is needed. The scripts inspect file bytes only.

From `C:\Users\Ayong\Documents\cp77 modding\tower ws`, reproduce the analysis into an unused output directory:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha\quest_restoration_qr15\effect_contract_01\analyze.py' --out run_02
```

Expected outputs are `run_02/result.json` and `run_02/BRANCH_MATRIX.md`, with status `STARTUP_EFFECT_CONTRACT_NARROWED_NO_SAFE_PREPARED_ADAPTER`. Occupied output directories are refused. The recorded `run_01` passes69bounded checks, including four deliberately damaged source/graph controls. It independently rechecks2,181captured instruction records against executable bytes and Capstone decoding. Three small scalar controls describe only the proven stores, not a simulated engine or repaired gameplay.

The first analysis attempt selected the wrong exported connection-type name and stopped before writing output. `attempt_01.json` preserves that failure. The corrected reader selects actual `graphGraphConnectionDefinition` records and retains the full independent edge-equality assertion.

These are source, framing and preservation checks, not independent-agent review, a failing-before/passing-after runtime repair, or gameplay acceptance. The actual preservation results and final source/readback hashes are recorded in `preservation.json`, `completion.json` and `verification.json`. No unchanged baseline ZIP is rebuilt.
