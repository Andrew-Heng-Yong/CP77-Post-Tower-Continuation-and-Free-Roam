# Prospective ArchiveXL runtime observation

Prepared only. No game process was launched, attached, instrumented or modified.
The exact installed DLL instruction gate closes source-versus-DLL uncertainty for
the bounded registration methods. Runtime address resolution, actual callbacks,
receipt persistence and world lease timing still need observation.

Prerequisites: separately authorized deployment/testing and, for engine tracing,
separately authorized debugger attachment; the genuine supported post-Tower save;
the exact DLL SHA C07DA66DF4E4D57401FA3DF0F6288F3B780F01102A98807B6ADAABAEF45F69BF;
the pinned QR7:04 candidate; no live save/fact editor. Retain the original save and
installation rollback manifest. File rollback cannot reverse persisted owners.

First use coordinator's read-only log collector after an authorized run. Search the
copied ArchiveXL log for `Patching phase "ep1\quest\ep1.quest"`, `Can't merge phase`,
`Merging streaming block "towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock"`,
`All streaming blocks merged` and `Streaming blocks merged with issues`.
Require a matching run timestamp and installed source/XL hashes. A parent-patch
message alone does not prove that the new phase was inserted, started or retired;
the current ArchiveXL.log is empty while the game is closed, which is not a failed
runtime test.

For the remaining receipt boundary, a qualified debugger can observe these exact
RVAs after verifying the DLL SHA and its actual ASLR module base. Prefer hardware
execution observations; no software patch, fact change, callback injection or
forced quest execution is part of this proposal. No debugger command/API syntax
is certified here. The instrumenter must validate its own attachment procedure.

| Observation | Installed DLL RVA | Read-only fields / expected result |
| --- | --- | --- |
| Restore callback entry | 0xF5A10 | RCX is QuestsSystem. Read actual quest-list pointer at +0xA8 and uint32 length at +0xB4. Find the EP1 parent path FNV64; do not assume its saved index. |
| Actual receipt read result | 0xF5CC9 | Filter generated phase ID at uint32 `[RBP-0x65]` to 19913. EAX is GetFact result; receipt FactID is uint32 `[RBP+0x6F]`; store was 1. Nonzero follows 0xF5E1B and must skip this startup. |
| Zero-receipt start dispatch | 0xF5DB5 | RCX is QuestsSystem, RDX points to the real QuestNodeKey, R8 to the one-element In1 socket array. Filter the same phase ID. This proves dispatch attempt, not native execution success. |
| Receipt write | 0xF5DCF | RCX is FactManager, EDX=1, R8D=the same receipt FactID, R9D=1. The write belongs to ArchiveXL's native mechanism; the diagnostic never performs it. |
| Private streaming block append | 0x120D45 | Path copied from token at +0x48 into current blockRef; match the private block's depot FNV64. Observe token fields at 0x120D71/0x120D7E. A merged block does not prove a quest-scoped descriptor is acquired. |

Use bounded separate observation passes if hardware watchpoint slots are limited.
Record exact process/DLL identity, module base, native call site, parent quest index,
generated phase ID, numeric receipt key/value, merge path and timestamps. Repeat a
normal save/reload on the same separately backed-up test fixture: the receipt must
remain present and prevent a duplicate startup. Observe actual private owner/marker
acquisition and release through supported Ronald actions, including interruption;
do not infer that lease behavior from a block merge log.

`receipt_key.py --observed-quest-index N` computes the expected numeric identifier
offline from the externally observed real index using independently implemented
CRC/FNV. Its output is never save evidence. It accepts no process/save path, performs
no mutation and must not be used to manufacture an enrollment/receipt fixture.

Expected artifacts: copied version-matched logs, observer records if separately
authorized, genuine save-history declaration and action/observation timeline.
Missing observer evidence remains LIVE_ONLY; an empty log or a hypothetical
all-zero fact dictionary is not a substitute.
