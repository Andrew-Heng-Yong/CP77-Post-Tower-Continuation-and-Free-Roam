# Independent QR10 review

Status: static callback-contract finding verified; QR10D01 Lua approved for offline preparation only. No blocking source defect found. Live sampled-difference validation remains pending; native delivery is unsupported and unverified.

Scope: one independent reviewer, exact installed binaries read as bytes, no DLL/game loading, gameplay, deployment, save access or edits to QR9. The primary implementation agent owns the successor and its tests.

## Callback registration finding

The installed `Cyberpunk2077.exe` SHA256 is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. Independent Windows PE `.pdata` parsing identifies the registration function at VA `0x140255dac`–`0x1402560a9`. Its guard at `0x140255e94` is `test byte ptr [rax + 0x70], 4`. If bit2 is unset, the function selects the exact `RegisterListener() called with non-scripted object.` error literal at `0x14369a650`, then jumps to its error path rather than normal registration. This is decoded from the installed executable, not inferred from an online implementation.

The installed CET ASI SHA256 is `ACB12B25CFCF77C3F5A84DF7CD4F4AE5074B8269E7C7389F349E12B237F88D6E`. A separate full static instruction walk finds `$LuaProxy$` through `movsd`/`movzx` literal copies in the generated class constructor at `0x1800b2de0`. That constructor sets `r9d = 2` at `0x1800b2e52` and calls the base constructor at `0x1800bb4c0`. The base copies `r9d` to `ebx`, then stores `ebx` at `[this + 0x70]` at `0x1800bb65c`. Thus the exact installed generated class initializes its flags to `2`, without the required bit `4`. The pinned official CET source independently agrees: `NativeProxyType` constructs `CClass` with only `isNative = true`. The local RED4ext SDK maps bit2 to `isScriptedClass` and offset `0x70` to class flags.

This establishes a receiver-class contract incompatibility. Renaming `Callback`, adding another argument, changing the table shape, retaining proxies longer or claiming the returned ID proves registration does not address that guard.

The original observer already retains `NativeProxy` instances in `regs` and suppresses callbacks from retired generations. Its direct `{args={"Int32"},callback=...}` declaration is supported by the official constructor. The game function's name lookup attempts a suffixed signature and then the original supplied name, so a full name is not demonstrated to be the failure. These are source-backed exclusions, rather than guesses about APIs.

## Observation boundary

The Bullets captures recorded counts of returned IDs, not their individual values, live class flags or a registration-error transcript. Do not rewrite the historical evidence as an observed ID0 rejection. The binaries prove the static interface mismatch and explain why that proxy receiver cannot be relied upon. They do not measure actual native callback delivery, nor rule out later third-party RTTI mutation. Native event delivery remains unverified/unavailable for this implementation.

The QR9 offline double accepted a proxy without modeling the class guard and accepted ID0. Its invocation of a Lua closure therefore never tested the actual engine API boundary. A new offline control must model this independent guard, not merely rename the same mock callback.

## Successor design assessment

A narrow sampling-only Lua successor is appropriate: remove the incompatible receiver path, explicitly report native callback capability as unavailable, and read watched fact getters on a bounded interval. Label initial values as a baseline, later changes as sampled differences, never native events or exact write order. Do not require a new REDscript bridge, current Core compilation or package rebuild merely to make the observation useful.

A future true callback bridge would require a genuinely scripted receiver, conservative lifecycle management, separate compile/package validation and a natural in-game event before claiming delivery. Modifying CET class flags, executing quest nodes or writing facts would be unjustified here.

## Independent evidence

- `inspect_installed_game.py` → `installed_game_guard.json`: exact EXE hash, function boundaries, guard bytes, branch decode and literal; asserts the key instructions directly.
- `inspect_installed_cet.py` → `installed_cet_proxy_02.json`: exact ASI hash, PE-boundary constructor disassembly and base-constructor flag store. `installed_cet_proxy.json` is the preserved earlier narrower inspection.
- `../evidence/cet/src/reverse/NativeProxy.cpp`: pinned official source corroboration, not a substitute for the installed ASI proof.

Both scripts refuse to replace an existing evidence output. Their imports load only the existing Capstone disassembler library; they never load the game or CET binary.

For reproduction, prerequisites are the exact installed binaries above and the existing `research/finalboards_dismissal/tooling/python/capstone` runtime. From the workspace, use the verified Python executable and a fresh output pathname for each command:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr10/review/inspect_installed_game.py --out prealpha/quest_restoration_qr10/review/recheck_game_01.json
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr10/review/inspect_installed_cet.py --out prealpha/quest_restoration_qr10/review/recheck_cet_01.json
```

Expected outputs are JSON with exact input hashes and bounded function disassemblies; the game script additionally asserts the guard and error branch. Compare the input hashes and key instructions with the preserved evidence. A changed binary requires a new investigation, not reuse of these addresses as an API guarantee.

## Actual successor review

Reviewed `candidate_01/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua`, SHA256 `1A366E1075A9EBCA46686EF76AB724B7F5C3EE51445E13A3BC02B97194D21F90`, its configuration, generator and primary offline controls. The Lua removes the unsupported API path entirely and creates zero quest subscriptions. Its capability and sampled-change labels are explicit. Initial values remain a baseline; errors retain the previous successful value and recovery is distinguished from a native event. Sampling occurs once per observed two-second interval without catch-up loops; a separate 450-round cap limits getter work even if the wall clock stalls. Event/byte and capture-duration limits remain. Stop, observed detach, pregame, changed player entity and shutdown suppress subsequent sampling, with no automatic resume. Missing actual save identity remains disclosed.

The stable module name, diagnostic-only leaves and fresh `QR10_capture_*` pattern preserve prior QR9 evidence. No quest setters, graph execution, native ownership commands, save APIs or input automation appear in the source. This assessment does not certify a later installer; installation requires its separate exact-hash, containment, preservation and rollback checks and user authorization.

Executed the primary test script independently with `--out review/primary_controls_recheck_01`: **44 checks and 6 source mutants passed**. Its before control models the independently decoded receiver-class guard: the old implementation reports 17 returned registrations although all 17 proxy registrations are rejected and a changed fact yields zero deliveries. This is a synthetic reproduction of the established mismatch, not a retroactive claim that the original capture recorded individual ID0 values.

Added and ran `review/test_successor.py`: **15 additional adversarial assertions passed**, output `successor_controls_01.json`. They cover the 96/97-fact boundary, large update without catch-up, reverted intermediate values, invalid later Int32 values and deduplicated errors, same-value recovery, signed Int32 extremes, last-success provenance after error, missing-player stop before further getters, idempotent stop, fresh capture preservation and absence of callback-shaped event/registration APIs. These cases reuse the primary deterministic world stub but use separate assertions; the binary contract checks are independent of that stub.

Remaining limits and action: no live sampling latency or engine scheduling was measured; transitions between reads can disappear, and simultaneous changes have no inferred write order. Player entity ID is not a save identity. No actual native/private graph owner, listener registry, pending timer, phone queue, controller termination or reward idempotence is proven by sampled facts. The implementation agent is tightening the D00 natural-call card against real callable-contact evidence; the initial list alone must not be described as an available fixture. Do not ask for completed Wilson/Bullets/shop/reload tests again.
