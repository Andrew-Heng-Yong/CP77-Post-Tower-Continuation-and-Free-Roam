# Big in Japan â€” QR2 deep contract review

**No source-confirmed repair is justified by this investigation.** Five contracts have specific static proofs or an established Tower adaptation; five retain named evidence limits. The quest is **DEEP_REVIEWED_CONDITIONAL**, not STATIC_VERIFIED. No runtime bytes, native facts, saves or packages were changed.

The read-only trace covers 14 named resources and 499 normalized nodes, including the complete MQ038 body, briefing/village/ending/combat phases, all three dialogue scenes, native MQ038 corrective handlers and Dennis controller/scene/cleanup. [contracts.json](contracts.json) contains ten individual findings with exact depot/hash/JSON path, graph and node citations. [trace.json](trace.json) records sockets, edges, predicates, journal paths, writes, rewards and references. Current PH3 private bytes were checked against each decoded source; native binaries were checked against pinned hashes.

| Contract | Result and specific finding |
| --- | --- |
| Entry | APPROVED_DEVIATION. Current 1002â†’1003â†’54â†’80â†’55â†’1004â†’1005â†’1006â†’11 preserves native q001_done/q005_done/q101_enable_side_content predicates and original In1 target. Native parent node11 payload and instance-prefab list match exactly. |
| Eligibility | APPROVED_DEVIATION. Two identical admission predicates require seven untouched native facts and all thirteen journal entries Inactive. Actual predicates reject each journal's Active/Succeeded/Failed states and each progressed native fact. S23 scheduler denies unsettled journals, requires consecutive samples, and stops changing Permit after Issued. |
| Communications | PASS for static protocol. Caller122â†’143 start requestâ†’137 real start_done waitâ†’138 clear; normal144â†’139 end waitâ†’140 clear, interruption285â†’272â†’268â†’270. Native listener32/2 consumes requests and invokes native sockets; scene480/481 reaches real acknowledgements41/42. Current cleanup1301/1302 matches native439/303 modulo IDs. Failure SMS157 and contact marker159 remain native. |
| Ownership | CONDITIONAL. Real native main-root terminating ancestry and exact parent binding are established; actual saved-owner descendants and legacy orphan/adoption behavior are unobserved. Killed facts alone are not accepted as ownership proof. |
| Progression | PASS for native delegation. Native2â†’96 briefingâ†’97 villageâ†’99 ending and both early quest_ends routes remain unchanged. Optional combat/failure/vehicle/carry paths stay in original native resources. Historical corrective actions are already in native village158,182/184,202; they do not justify replaying migration handlers. |
| Presentation | CONDITIONAL. Native actor, workspot, reference-point and interruption declarations are recorded for all four scenes. World NodeRef/streamed variant resolution is incomplete. Twelve unchanged native en-lipsync declarations have no literal provider in the fresh134-archive lookup; localization/engine resolution remains unproved. |
| Journal | PASS for static transitions. Native POI, objective, description, contact-marker and terminal paths are preserved. Failure SMS157 precedes Failed43; ending8/12 succeeds objective/root. Private adapter does not rewrite journals. |
| Completion | CONDITIONAL: authored reward/cleanup graph checks pass; target TweakDB reward data and katana-token placement remain unresolved. Ending7â†’33 contact removalâ†’8â†’12 root successâ†’16 single native rewardâ†’20 checkpoint has no normal cycle returning to16. Scene222 enables native katana token. Root104/105â†’122â†’121â†’102 preserves deactivation, distance waits, variants and message-visited cleanup before private Finished. |
| Persistence | CONDITIONAL. Durable one-time receipt/node/resource identities are unchanged, and terminal/issued guards reject restart. Native saved child/scene/delay/mount/carry state and exactly-once reward execution across an actual reload remain unverified. |
| Shared dependencies | CONDITIONAL. Dennis native request/ack/cleanup and current PH3 studios remain present. Already-issued MQ038 bypasses its own held interruption flags; fresh owner waits for idle. Actual saved PhoneSystem leases, render marker and streaming/interrupt scheduling remain unobserved. |

The successful static checks do not certify native engine execution, actual actor placement, phone rendering or a particular save. The established one-time fresh seam remains restrictive; this review does not authorize unfinished-state relaxation, counter synthesis or duplicate controllers.

## Tests and reproducibility

[tests_04.json](tests_04.json) records **157 checks**, including binary/source pins, native-parent prerequisite comparisons, all thirteen journal-state refusals, seven progressed-fact refusals, native phone protocol/cleanup, branch/reward/SMS paths and four in-memory mutations of the real graphs:

- Add an interruption-zero gate to the already-issued Dennis branch: existing-owner admission fails, detecting the prior deadlock class.
- Remove caller143â†’137: the native call no longer reaches its start acknowledgement-clear path.
- Remove shared-cleanup1301â†’1302: owned Dennis cleanup becomes unreachable.
- Change native q001 prerequisite comparison: the native payload comparison fails.

The mutations never touch a CR2W file. To rerun against these exact inputs, use a fresh output path:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -B 'prealpha\quest_restoration_qr2\quests\mq038_neweridentity\verify.py' --output 'prealpha\quest_restoration_qr2\quests\mq038_neweridentity\tests_successor.json'
```

The cross-review found a test-helper assumption: missing journal inputs defaulted to Inactive. The helper now fails closed on any absent journal/fact input, and two explicit missing-state controls pass. Runtime S23 already rejects missing entries, so this was a test-only correction.

No compile or baseline ZIP was recreated. QR1's unchanged PH3 compilation/readback/regressions remain reused evidence. Root integrates the fresh provider/ancestor/preservation review and the persistent161-quest queue.

## Remaining exact evidence

- Resolve [dependency_depots.json](dependency_depots.json) world NodeRefs against current descriptor/sector/community entries: Darryl/surgeon/car/Tygers, hook and delivery triggers, scene markers, forbidden vehicle trigger, variant prefabs and katana token. [actor_bindings.json](actor_bindings.json) preserves the actor acquisition and workspot definitions to compare.
- Resolve exact QuestRewards.mq038_surgeon_saved TweakDB data and #mq038_katana_token/#wnid_01_loot variant placement before certifying reward delivery.
- Resolve twelve literal native en-lipsync references through localization/engine behavior, without treating absence of a literal archive key as a new PTFR omission.
- Review an actual retained-save owner tree/transition fixture for the original MQ038 and Dennis descendants, existing issued-owner adoption and repeated reload. Do not restart the quest or change facts to manufacture it.
- Later authorized runtime observation: native call acceptance/rejection/interrupt cleanup, actor/vehicle/carry progression, katana visibility/acquisition, terminal state and reward continuity. No gameplay test is requested in this session.
