# QR6 evidence and reproduction

Continue from [REQUEST.md](REQUEST.md), root/prealpha AGENTS.md and the exact [QR5 handoff](../quest_restoration_qr5/HANDOFF.md). QR6 completes the remaining33 source investigations; the previous128 investigations and their independent reviews are retained with original provenance. Read [REPORT.md](REPORT.md), [coverage.json](coverage.json), [checkpoint.json](checkpoint.json) and [HANDOFF.md](HANDOFF.md) for final reconciled coverage. A deep investigation is ten specific findings with peer review, not ten PASSes or gameplay certification.

Canonical runtime inputs are identified by [source_epoch_identity.json](source_epoch_identity.json), [source_epoch_00.json](source_epoch_00.json) and the exact changed-resource [allowlist](approved_changes_00.json). QR6's local epoch00 is byte-identical to QR5canonical08/candidate03, including all eight earlier repairs across nine resources. Installed PH3 is separate. No unchanged-baseline candidate or ZIP needs to be recreated.

The [group evidence index](group_evidence_index.json) selects each immutable per-quest contract file, original/current resource hashes, exact tests and independent review. Source-specific checks live under `groups/A01`, `A02`, `A03`, `B01`, `C01` and `C03`; shared parsers are pure local helpers. Read scripts before use. Preserve failed verifier attempts and original evidence; never overwrite a frozen output to obtain a new PASS.

Prerequisites for a recheck are the exact pinned local raw resources/readback JSON, QR5candidate03, relevant recipe/source inventories and the existing Python/WolvenKit toolchain. Missing local ignored evidence is a blocker, not an empty dependency set. Run from the repository root with the explicit Python executable. The following commands are supported read-only resource rechecks with fresh diagnostic outputs; replace `NEW` with a genuinely unused directory. They are examples for an affected investigation, not a requirement to repeat unaffected controls.

```powershell
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr6/groups/A01/verify.py --output diagnostics/qr6_recheck_NEW/A01
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr6/groups/B01/verify.py --group B01 --output diagnostics/qr6_recheck_NEW/B01
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr6/groups/C01/verify_u10.py --group C01 --output diagnostics/qr6_recheck_NEW/C01
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr6/check_ronald_boundary.py --output diagnostics/qr6_recheck_NEW/Ronald
```

Expected outputs include exact input pins, source comparisons, node/socket/predicate evidence, tests and source-document mutation controls. Require the pinned hashes, no unexpected graph differences and successful declared controls. The complete frozen totals include supplements beyond the representative commands; compare each exact output's summary rather than expecting a single command to reproduce a whole group's aggregate event count. JSON mutations are fault-detection controls, not binary/gameplay execution.

[Current compile evidence](verification/compile_01/result.json) records one fresh offline SCC run because an existing compiler timestamp changed since QR5. All131source bytes and46managed sources still match; all134current compiler/source/cache pins are explicit. Reuse that successful result only while those exact inputs match. `verify_compile.py` can stage a fresh offline check when inputs change; it never writes the installed cache. Do not rerun a compiler solely to refresh a date.

[Installed/staged verification](verification/baseline_01/result.json) and [session preservation](protection_before.json) distinguish installed PH3, staged QR5 and preexisting external save/cache drift. Old success reports do not certify the new external state. A separate current-session preservation result is required before final delivery.

`initialize.py`, `capture_protection.py`, `prepare_reward_targets.py`, `record_group.py` and `finalize.py` are coordinator evidence/publication operations. Their historical invocations are not generic reproduction commands. Do not rerun pinned historical initializers, patchers, builders, installers or finalizers. No deployment, game/save/fact modification, release change or Git publication is authorized by a verifier command.

Follow-up work is separated into [static hardening](HARDENING_PLAN.md) and [in-game validation](INGAME_VALIDATION_PLAN.md); neither plan was executed as a game run.
