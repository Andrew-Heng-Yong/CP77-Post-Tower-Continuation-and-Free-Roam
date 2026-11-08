# QR13 verification and reproduction

Working directory: `C:\Users\Ayong\Documents\cp77 modding\tower ws`.

The tested coordinator sequence was: `capture_baseline.py`, targeted provider captures, Ronald proposal/typed review and promotion, Brendan proposal/support-holder correction/typed review, `compile_successor.py`, `freeze_source.py`, `rebuild_successor.ps1 -Epoch prealpha/quest_restoration_qr13/source_epoch_01.json`, then `package_successor.py`. Each script's parameters, input pins, output paths and guards are available in its inspected source. The outputs now exist; these one-shot commands intentionally refuse overwriting them. Do not rerun historical builders or reconstruct the candidate from generic source folders.

The existing candidate and its compilation/build/review receipts are the verified result. The following commands perform a **fresh independent extraction and verification** without building, installing, launching the game or writing saves. Prerequisites: exact final candidate, frozen review inputs, unchanged installed files/saves within the QR13 preservation window, Python3.14, PowerShell7 and the pinned local WolvenKit9.1 package. Output directories must not exist.

```powershell
Set-Location -LiteralPath 'C:\Users\Ayong\Documents\cp77 modding\tower ws'
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoLogo -NoProfile -File 'prealpha/quest_restoration_qr13/worker_c/extract_final_archive.ps1' -Inputs 'prealpha/quest_restoration_qr13/worker_c/final_package_01/expected/inputs.json' -Output 'prealpha/quest_restoration_qr13/worker_c/reproduce_extract_01'
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'prealpha/quest_restoration_qr13/worker_c/verify_final_package.py' --inputs 'prealpha/quest_restoration_qr13/worker_c/final_package_01/expected/inputs.json' --capture 'prealpha/quest_restoration_qr13/worker_c/reproduce_extract_01/manifest.json' --output 'prealpha/quest_restoration_qr13/worker_c/reproduce_verify_01'
```

Expected outputs: an extraction manifest with all 1,577 actual member hashes and fresh typed exports for the three changed resources; then review/check/payload/ZIP JSON under `reproduce_verify_01`. The original independent run passed 2,390 checks and verified 51 ZIP files, the compile linkage, installed hashes and saved bytes. Check that the final result starts `PASS_INDEPENDENT_FINAL_QR13` and that the source epoch/archive/ZIP hashes match REPORT.md. Existing outputs are preserved on failure; do not bypass guards or change old pins to obtain PASS.

Later legitimate human gameplay can change saves/logs/cache timestamps and therefore invalidate preservation equality against this task's baseline. Record that later boundary explicitly; it does not authorize save rollback or prove the staged archive is defective. No current game command, deployment command or new gameplay test follows from these reproduction commands.

Detailed component controls: `worker_c/ronald_serialized_01/` has the actual Ronald allowlist/native-cast/cleanup tests and seven mutation controls. `worker_a/actual_brendan06_02/` has the final holder lifetime/old-owner completion tests and six mutation controls; `actual_brendan03_03/` contains the separate approved script semantics/negative controls while explicitly blocking resource03. These records are not interchangeable.
