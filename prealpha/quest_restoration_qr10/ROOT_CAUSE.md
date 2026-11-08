# QR10 callback observation failure

**Finding: unsupported receiver class, confirmed against both installed binaries.** The failure is in the diagnostic binding. It is not evidence that Bullets or its fact writers failed.

## Evidence chain

| Evidence | Exact result |
| --- | --- |
| Installed game EXE | SHA256 `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4` |
| Installed CET ASI | SHA256 `ACB12B25CFCF77C3F5A84DF7CD4F4AE5074B8269E7C7389F349E12B237F88D6E` |
| Game registration guard | Function `0x140255dac`–`0x1402560a9`; at `0x140255e94`, `test byte ptr [rax+0x70],4`. Without the bit, selects the non-scripted-object rejection literal and jumps to the error path. |
| CET generated receiver | Constructor `0x1800b2de0`; `r9d=2` at `0x1800b2e52`, base-constructor call at `0x1800b2e5b`. Base stores those flags at class offset `0x70` at `0x1800bb65c`. Required mask0x04 (bit2) is absent. |
| SDK/source corroboration | Local RTTITypes maps bit2 to `isScriptedClass`. Pinned official CET `NativeProxyType` supplies only `isNative=true`. |
| QR9 observer | `NewProxy({args={"Int32"},callback=...})`, target passed to `QuestsSystem:RegisterListener`; accepts every non-nil return, including0. Individual IDs were not logged. |
| QR9 tests | Mock accepts that target, omits the scripted-class guard and manually invokes Lua closures. It did not test native delivery. |

The independent [review](review/REVIEW.md), [game disassembly](review/installed_game_guard.json) and [CET disassembly](review/installed_cet_proxy_02.json) establish the installed contract. The initial primary LEA-only string scanner did not locate CET's MOVSD string-copy reference; its incomplete outputs are preserved as discovery attempts. The independent PE function-boundary analysis resolves that limitation.

Official source is pinned at [CET commit b160d68](https://github.com/maximegmd/CyberEngineTweaks/blob/b160d68cf923f2535cb3a6ebe006de86ef21e359/src/reverse/NativeProxy.cpp). It corroborates the binary findings; it is not claimed to reproduce the entire installed HEAD build. Exact local input hashes and historical phone-card sources are in [provenance.json](provenance.json).

## Other hypotheses

- **Table shape/signature:** the shorthand declaration is supported; Int32 matches the native argument check. The game tries a suffixed function name and the supplied name. No evidence justifies adding arguments or renaming the callback.
- **Lifetime:** QR9 retains proxies in `regs`; CET's proxy holds the generated instance. No missing strong Lua reference was found. Old generations are suppressed.
- **Filtering/logging:** no fact-value filter precedes QR9 delivery logging. Its journal getters and log output operated during Bullets. The receiver guard precedes actual registration.
- **Registration:** a returned/default value is insufficient evidence. The original observer did not log historic individual IDs or live class flags. Do not rewrite the Bullets record as an observed ID0 rejection or an observed error message.

## Historical observation

The immutable `../quest_restoration_qr9/observations/S05_20261102_02/` capture spans 21:28:55–21:36:51 UTC. Its journal getter advanced to Succeeded, while broader CET logs recorded watched completion/active transitions. The probe recorded zero `FACT_DELIVERY`. The static class-contract incompatibility explains why this listener implementation was unreliable. There is no need to repeat Bullets to establish the diagnostic defect.

## Correction and boundary

QR10D01 removes the unsupported NativeProxy registration path. It reports `NATIVE_CALLBACK_UNAVAILABLE`, creates zero native quest subscriptions and samples `GetFactStr` every observed two-second update interval. Only changed getter values produce `FACT_SAMPLE_CHANGE`. These are sampled differences, not callbacks, write counts, exact write times or engine order. Intermediate/reverted changes can be missed.

A genuinely scripted REDscript receiver could support a future native-event bridge, but requires separate compilation, lifecycle validation and natural delivery evidence. This narrow Lua successor does not create one, modify RTTI flags, patch CET or change the Core. **Native callback delivery remains unsupported and unverified. Live sampling also remains untested until human gameplay.**

## Reproduction

Prerequisites: pinned installed EXE/ASI above, existing Capstone under `research/finalboards_dismissal/tooling/python`, existing LuaJIT under QR9 `worker_b/tooling`, Python3.14, and a fresh output name. No binary is loaded as an engine module.

```powershell
$py = 'C:\Users\Ayong\.local\bin\python3.14.exe'
& $py -X utf8 -B prealpha/quest_restoration_qr10/review/inspect_installed_game.py --out prealpha/quest_restoration_qr10/review/recheck_game_NEXT.json
& $py -X utf8 -B prealpha/quest_restoration_qr10/review/inspect_installed_cet.py --out prealpha/quest_restoration_qr10/review/recheck_cet_NEXT.json
& $py -X utf8 -B prealpha/quest_restoration_qr10/test_diagnostics.py --out tests_NEXT
```

Expected: exact binary hashes/guard/store assertions; 44 Lua controls and six detected source mutants. The QR9 before control reports17 IDs despite17 modeled native receiver rejections and misses an external value change; the successor observes that same change by sampling. These are offline controls, not engine dispatch tests. Scripts refuse occupied result outputs. Existing verified outputs should be reused unless inputs change.
