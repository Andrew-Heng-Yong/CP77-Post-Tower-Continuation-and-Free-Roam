"""Write bounded QR7 handoff and reviewable final reports from measured evidence."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not(O/'REPORT.md').exists()
cov=read(O/'coverage.json');p=read(O/'candidate_01/package_manifest.json');pres=read(O/'verification/preservation_01/result.json')
table='\n'.join(f"| {s} | {cov['before_status_counts'].get(s,0)} | {cov['after_status_counts'].get(s,0)} |"for s in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL'])
report=f'''# QR7 — targeted repairs and static hardening

Implemented **three justified repairs in a fresh consolidated successor**: Nitro eligibility, CVI02's alternate Hands listener/lifecycle, and future Ronald news for four selected gigs. The current staged source/package is **QR7:04**, `candidate_01`. **Nothing was installed or launched.**

All **21 original targeted contracts** received specific source-backed dispositions: the13 original FAILs now have **conditional prospective repair scopes**; three of eight original UNKNOWNs were narrowed to two approved deviations and one conditional result; **five UNKNOWNs remain**. This does not mean that all historical states, first-time Ronald subscription, or gameplay are repaired. Those limitations remain explicit below and in [remaining_blockers.json](remaining_blockers.json).

The161-quest/1,610-contract catalogue and prior deep investigations were reused. QR7 did not repeat that census or claim new whole-whitelist coverage. **Zero quests are fully STATIC_VERIFIED.**

| Disposition | QR6 baseline | QR7 staged scope |
| --- | ---: | ---: |
{table}

See [all21 targeted findings](targeted_dispositions.json), [complete contract CSV](contract_status_matrix.csv), [quest CSV](quest_status_matrix.csv), [coverage](coverage.json), and [persistent queue](queue.json). Each target retains its original QR6 finding, actual node/predicate evidence, worker result, cross-review and source epoch. The change to CONDITIONAL is a bounded prospective result, not deletion of the original failure or certification of unsupported histories.

## Implemented source changes

**Nitro — mq060_nitro.** Fresh positive startup proof identifies the current `cyberpunk2077.gamedef` registered main quest and connected root82/4→bugfixing9→root/3 native93 OR-three-Kusanagi AND104 `carbought_counter>=3`→89.Start. The unregistered standalone four-bike donor is not the selected original entry authority. Both pre-Issued65003/65004 guards now append the exact registered native predicates. All existing nodes, edges, receipts and already-issued downstream selectors remain unchanged. Actual condition fixtures show47/80 divergences before and0 after. This is supported by new authority evidence; QR6's rejected stricter-intersection proposal was not accepted merely because it was stricter. [Authority](worker_c/nitro_authority_03/evidence.json), [serialized checks](candidate_01/repair_nitro_01/verification_01/result.json), [independent review](worker_a/reviews/nitro_serialized_gate_01/review.json).

**Two Wrongs Makes Us Right — sts_pac_cvi_02.** Future fresh EP1 entry gets the original specialized16-node listener/outcome owner that the generic Hands controller does not replace. Admission requires no old entered/request/outcome or private inflight history. Eight outer IDs65007–65014 and six private inflight helpers are additive. Real selected scene inputs set inflight; six exact real terminal outputs clear it in parallel with direct native ACK edges. Native INT/RET paths remain. OwnerFinished waits only this controller's three flights before cutting its new child; muted/no-scene paths require no unrelated PhoneEndCall. A prior prototype with an unscoped global end-call dependency was rejected and preserved as failure evidence. [Source plan](worker_a/proposal_04/plan.json), [independent82-check/three-mutation review](worker_b/reviews/CVI02/verification_05/review.json), [actual candidate readback](candidate_01/repair_cvi_02/readback.json).

Fresh packed world/provider evidence corrects the earlier physical FO1 marker assumption: the exact Hands static animation marker is in the current AlwaysLoaded EP1 sector, descriptor2185, not the separately leased physical-office sector1941. Exact actor community/compiled definitions are also always loaded; inactive physical state is preserved. No new physical-office/default-owner clone or forced marker activation was added. Source support and matching bindings do not prove rendered actors or a delivered call.

**Saints, The Man Who Killed Jason Foreman, Spy in the Jungle, Treating Symptoms — sts_ep1_01/03/08/12.** One isolated prospective owner restores only four selected native news branches. Each existing admission65002.Out now passes through new65007 writing its private Armed fact before original65003 ParentEntered. The owner requires actual new Armed history plus genuine existing enrollment/contact; it refuses old entered/done/sent/pending clocks. It preserves all73 selected native node identities and the original selected protocol, with the documented terminal join changing from five inputs to four and eight delivery spatial predicates substituting the private trigger refs. Native timing/queue/cancel/rearm/callback paths, exact SMS children and sent-before-two-game-day ordering remain. Only two native trigger definitions/shapes/transforms are privately rehomed; a single Quest descriptor leases those two nodes. No whole-bar owner, fluff branch, AddContact, synthetic enrollment or timer reset is copied. [Native protocol and controls](worker_b/future_check_04/evidence.json), [independent306-check/64-fixture/four-mutation review](worker_c/reviews/ronald_01/verification_02/review.json), [integrated source preservation](candidate_01/repair_ronald_01/verification.json).

**Important partial scope:** B0 subscription1755 remains unreachable. First contact/new subscription is not repaired. Already-entered jobs without Armed and sent/done/pending native clocks are deliberately not adopted. Exact complete dialogue/contact ownership and save-transition evidence are required before extending this scope. Missing enrollment is never manufactured. Real streaming/occupancy, queue concurrency, notification display and cold reload remain LIVE_ONLY.

## Five retained static UNKNOWNs

| Quest / contract | Proven narrowing | Exact unresolved evidence |
| --- | --- | --- |
| Career Opportunities / persistence | Exact current native JournalQuestEntry path rejects equal Active state before state changes/listener notifications; actual trackQuest0 path and SMS7/56 identities checked. | Retirement and saved/concurrent state of the original early congratulations owner6→68→7→57→56→8 before first-place admission. State idempotence alone does not prove old owner retirement or every postprocessing path. |
| Cuckoo's Nest / shared dependencies | Correct ID is sts_std_rcr_02, Rancho; earlier “Arroyo courier” label was wrong. Four native source-null endpoints are genuinely serialized; recipients11/13/15/2 are unreachable from root. Both Dixon inventory branches reach choice6. | Provenance/current native invalid-record query semantics for exact numeric inventory predicate114327022403, absent from both direct stock DBs; original intended sources for four null edges. It is a condition, not a missing reward grant. |
| Voodoo Treasure / eligibility | Guard90 requires loaded original door and NOR(IsOpen); native query3 uses DoorControllerPS. | Exact door/controller binding and a source-realizable prior-claim history satisfying later admission. Cleanup21 targets the same ref with TerminalControllerPS ForceDisabled; generic DoorController behavior is insufficient. |
| Voodoo Treasure / completion-rewards-cleanup | Native22 Inject contains exactly8000 money, shard and Rook; original phase is called by the wrapper. | Native hub12 dispatch and downstream context/transaction/container merge or injection idempotence for a previously emptied stash. No duplicate grant is asserted. |
| Voodoo Treasure / persistence | Actual opened/device-state persistent fields and native close/disable behavior captured. | Exact entity persistent IDs/controller resolution, original owner retirement and retained container/door state; four journal states alone do not prove historical entitlement. |

[Exact follow-ups](worker_c/BLOCKER_FOLLOWUPS.md), [C's final source applicability](worker_c/final_scope_03/applicability.json), [independent eight-disposition review](worker_a/reviews/unknowns_final_01/review.json). No speculative repair was made for these five rows. All917conditional and162opaque full-matrix records remain visible, with inherited continuation blockers retained in the ledger.

## Reusable hardening and independent gates

[Shared evidence registry](shared_evidence_registry.json) adds nine bounded units; [regression evidence](regression_evidence.json) indexes20 source-specific gates without summing overlapping assertion events. Fresh packed-layout checks show that a successful WolvenKit9.1 export can still report incorrect modern NodeDataIndex/distances. Read original decompressed144-byte setups: global@0x58, low19 index@0x70, distances@0x78/0x7C. Current native bytes, raw mutants, framework/SDK source pins and actual typed mismatches are retained. Known community default-member events are narrowed by prefix-accept/refuse probes rather than empty event reflection. Exact native equal-state journal proof and unresolved stock predicate/provider/persistence semantics are separate reusable checks. [Static hardening notes](STATIC_HARDENING.md).

Cross-review roles were independent: B reviewed A's CVI controller, C reviewed B's Ronald owner/markers, A reviewed C's UNKNOWNs/Nitro. A's final package verifier extracted all1,577 archive members and compared approved proposal models to actual final bytes; **1,738 checks passed**. B's independent matrix phase checked21 targets, the full161/1,610 grid, CSVs, old provenance and frozen source; **4,615 checks passed**. These event counts are not unique gameplay coverage. A stale cached Spy JSON was rejected as baseline authority; fresh actual QR6 binary readback confirmed all previous Mark/Ana fixes and saved nodes remain. [Package review](worker_a/final_package_02/verification/evidence.json), [matrix review](worker_b/final_matrix_02/review.json).

ArchiveXL registration semantics must be read with [REGISTRATION_BOUNDARY.md](REGISTRATION_BOUNDARY.md): the active installed DLL differs from the old PR63 package. Old source is not silently claimed as current runtime proof. Standard append-only syntax and generated IDs are verified independently; save-restore engine behavior remains separately bounded by the current-source follow-up. Final completeness review and any registration addendum are pinned by completion.json after review; neither is inferred from the earlier matrix/package PASS.

## Exact staged successor and preservation

- Canonical epoch: [source_epoch_04.json](source_epoch_04.json); source1577payloads,51package files.
- Six existing payloads changed, three added; **1,568 baseline payloads unchanged**. Only archive and XL package bytes differ from QR6;49 other package files are exact. All prior eight repairs across nine resources are preserved: eight resource hashes match; the Spy resource retains every existing graph/node/socket/payload and phone fix, with only the new future Armed splice.
- Existing825 phase registrations/15 streaming blocks retain order and identity. One new EP1 `[1].Out` phase19913 and one private streaming block are appended. Three new depot keys are absent from all134 current archive indexes;55XL files were parsed without unsupported quest shapes. No full native/external world-global collision census is claimed. Retained sourcePrefabHash is source metadata; descriptor/private globals provide the ownership evidence, with live streaming still untested.
- Archive SHA256: `{p['archive_sha256']}`.
- XL SHA256: `{p['xl_sha256']}`.
- Staged ZIP SHA256: `{p['zip_sha256']}`. All51unique ZIP members passed CRC, exact bytes and size verification.
- REDscript was unchanged. All131 source bytes,134 current compiler/cache/source pins,46managed scripts and QR6's actual compiled output hash matched; the exact fresh QR6 compilation was reused. **No fresh QR7 SCC invocation is claimed.** [Compile reuse](compile_reuse_01.json).
- Preservation: **{pres['protected_sha256_files']} protected hashes**, all{pres['whole_game_metadata_files']} game and{pres['whole_save_metadata_files']} save filenames/sizes/mtimes,134compile pins and preexisting tracked Git diff unchanged. Zero discrepancies. This is protected-file SHA plus whole-tree metadata, not a SHA of every multi-GB unlisted game file. [Result](verification/preservation_01/result.json).

InstalledPH3 remains unchanged and distinct from this staged candidate. No game/launcher launch or auto-close, deployment, save/fact edit, external-mod edit, release publication or Git push occurred. [Repair ledger](defects_and_repairs.json), [repair queue](repair_queue.json), [fresh-session handoff](HANDOFF.md), [prioritized future live checklist](INGAME_VALIDATION_PLAN.md).
'''
(O/'REPORT.md').write_text(report,encoding='utf-8')
(O/'STATIC_HARDENING.md').write_text('''# QR7 reusable static hardening

Use shared_evidence_registry.json and regression_evidence.json for exact source hashes, producing scripts and applicability. These are bounded proofs, not a global actor, TweakDB or owner certification.

1. **Modern packed world setups:** current2.5 raw arrays use144-byte records; globalNodeID offset0x58, low19 nodeIndex bits at0x70, distance floats at0x78/0x7C. Native Hands record4670 maps definition2577, while WolvenKit's old typed interpretation reports13935. Bar source records1/3 and their two private successors are checked from decompressed GetBytes buffers. Do not serialize a current world sector solely to normalize a misleading typed export. The full current sector hash and exact framework/SDK source are pinned in worker evidence. Check three packed mutants with worker_b/check_bar.py.
2. **NodeRefs and ownership:** depot FNV, ArchiveXL CRC and RED4ext NodeRef hashing are distinct namespaces. NodeRef hashing skips# and semicolon variants as defined by the pinned SDK; two private full refs match distinct packed globals. Descriptor.questPrefabNodeRef, current streaming category/ranges/variants, ancestor phasePrefabs/phaseInstancePrefabs and actual actor registry bindings must all be traced. sourcePrefabHash alone is not lease proof. Full world-global collision closure remains open.
3. **Successful decoding is not complete decoding:** actor sector initially failed only at communityCommunityTemplateData.entries default mismatch. The observed InvalidDefaultValueEventArgs class has no event fields, so empty reflection was rejected. Prefix probes accept exactlyN observed events and refuseN+1 to recover the exact exception member; all11 names match. Existing populated target registry/compiled areas are independently checked. This is a narrow read-only decoder allowance for the pinned input, not a universal error suppression rule. The separate non-EP1 bar DynamicBaseClass failure remains opaque and was not promoted into an owner.
4. **Phone cleanup and ownership:** CVI real terminal scene outputs are different from global PhoneEndCall. Exact inflight receipts wrap real selected scene invocations; nativeACK stays direct, interrupts remain native, cleanup waits only these flights. Actual support marker is AlwaysLoaded, separate from FO1 physical office; source metadata alone must not invent a new physical lease. Actual acquisition/render/reload remains live.
5. **News history:** sent1 is written before the native two-game-day delay; it is not delivery proof and cannot be reset to replay. Actual admission-produced Armed facts distinguish newly supported events from historical completion with identical done/sent defaults. Genuine contact/enrollment is required; no AddContact/bootstrap is inferred from a retired controller. Four selected branches require a four-way private terminal join, not the native all-news join with fluff branches.
6. **Current native authority:** exact current game definition registration plus connected root ancestry establishes Nitro's native entry source. Search/reverse-reference absence alone did not. Cached JSON can omit an embedded graph; current raw resource freshly decoded is authoritative. Current donor byte equality carries prior semantic analysis only for the exact matching resource, not another donor/version.
7. **Journal/target/persistence limits:** current equal-state native journal rejection narrows Career notification risk; it does not prove saved early-owner retirement or other postprocessing. Cuckoo's numeric inventory condition lacks a current direct stock record; it is not a missing grant. Voodoo DoorControllerPS vs TerminalControllerPS and downstream Inject/context/transaction semantics remain explicit. No broad effective TweakDB, economic or vehicle closure was newly established.
8. **Registration lifecycle:** final phase input shape, parent IDs, complete installed additions and exact append-only order are checked. Bind restore/forced-start source proof to the actual installed ArchiveXL lineage, not whichever old source tree is available. See REGISTRATION_BOUNDARY.md and the final completion seal.

Commands, prerequisites and fresh-output expectations are in README.md and worker_c/REPRODUCE.md. Proposal builders and coordinator one-shot mutators are immutable recipes, not replayable validation commands.
''',encoding='utf-8')
(O/'REGISTRATION_BOUNDARY.md').write_text('''# ArchiveXL registration and restore evidence boundary

Final package readback proves the new phase and streaming block are appended without changing existing order, paths, registrations or generated IDs. New phase path towercontinued\\quest_restoration_qr7\\ronald_news_future.questphase targets the actual EP1 root quest [1].Out; CRC19913 is clear of native IDs and all current installed additions. No synthetic forceStart YAML option was added.

The active ArchiveXL DLL is the current installed official1.28.0 build, not the older local PR63 package. The initial PR63 equality assertion correctly failed and is not a current runtime proof. A separate worker_a source-applicability follow-up is in progress at this report checkpoint; completion.json will pin the final disposition/addendum. If no exact current source/binary binding can be established, it remains an explicit UNKNOWN engine-registration boundary rather than a fabricated PASS.

Even if standard new-root forced startup is confirmed, that only starts the private wait graph. It does not authorize adopting old quest owners. Genuine Tower/native-retirement/contact/enrollment/idle guards and actual future admission-produced Armed signals bound the reviewed new owner. Existing entered/sent/done/pending histories defer; no native facts, enrollment, clocks or rewards are reset.

Actual save restoration/scheduling, private streaming and old-owner concurrency were not executed. They remain LIVE_ONLY independently of an archive/package syntax PASS.
''',encoding='utf-8')
(O/'INGAME_VALIDATION_PLAN.md').write_text('''# Prioritized future in-game validation — not executed or authorized by QR7

Use only under separately authorized deployment/testing scope and preserve genuine user saves. File rollback is not save rollback. Do not manufacture facts or replay a pre-Tower save to create fixtures. Record candidate/archive/XL/framework hashes, genuine history, observations and reload boundaries. No repeated request for previously successful generic Spy phone tests is implied; target the new QR7 changes.

1. **CVI02 future eligible EP1 fixture:** original not-entered/no-request history, exact default marker available. Observe prebrief, both success/failure debriefs, real acknowledgements, muted/no-scene branch, rejection/INT/RET and reload during a call. Confirm cleanup waits only this controller's real flights and never an unrelated phone event. Preserve original reward/van outcomes and saved identities.
2. **Ronald existing enrolled/contact-active future fixtures:** before fresh admission of each Saints/Jason/Spy/Symptoms case, observe actual positive Armed production then native completion. Confirm native1/2/3-second preclaim, sent-before-two-game-day clock, exact two game days across reload, token/outside-bar gate, correct native outcome variant/SMS identity and its original notification flags, pause release and cancel/rearm. Observe private two-trigger lease acquisition/release with no native bar/patrons owner replay. Exercise two simultaneous completions/queue interruption without duplicating notifications.
3. **Negative history fixtures:** old entered/Armed0, native done1/sent1 or pending native timer, absent subscription/contact and busy old queue must remain unchanged/deferred. Do not reset a fact or simulate eligibility to obtain the fixture. Original first-contact/subscription1755 is still blocked; that is not a successful QR7 route.
4. **Nitro genuine eligible and ineligible fixtures:** registered OR-three bikes plus purchases>=3 must govern new admission; Tyger-only and fewer-purchases histories must not newly enter. Already-issued owner waiting downstream must retain its original selector/progress; reload must not replay setup/rewards.
5. **Save-version transitions:** genuine predecessor supported state to QR7 during new controller waiting, inflight scene, news timer, callback and cleanup; verify old identities/Mark/Ana/PH3 support persist. Installed-version file rollback cannot undo new persisted private owner/receipt state. Conservative future-version compatibility remains a commitment requiring these fixtures.

Resolve five static UNKNOWNs with the exact evidence in worker_c/BLOCKER_FOLLOWUPS.md before proposing gameplay fixes. Runtime observations cannot substitute for missing native authority, intended null endpoints or transaction/controller bindings. Existing unrelated917conditional/162opaque records and inherited continuation blockers are outside this targeted live checklist.
''',encoding='utf-8')
(O/'HANDOFF.md').write_text(f'''# After QR7 — targeted repairs staged, partial histories explicit

Read applicable AGENTS.md, completion.json first, then REPORT.md, checkpoint.json, source_epoch_04.json, approved_changes_03.json, targeted_dispositions.json, remaining_blockers.json and relevant knowledge procedures. completion.json is the terminal authority; working checkpoints and private proposal NOT_FOR_INTEGRATION manifests are historical states.

Canonical staged source/package: `prealpha/quest_restoration_qr7/candidate_01`, epoch **QR7:04**. Source1577payloads;51package paths; archiveSHA `{p['archive_sha256']}`; stagedZIP SHA `{p['zip_sha256']}`. InstalledPH3 remains unchanged. No deployment, launch, save/fact edit, publication or Git push is authorized by QR7.

Three staged repairs: Nitro native pre-Issued eligibility; CVI fresh alternate Hands real-flight listener/cleanup; future Armed Ronald news only for existing genuine subscribers/contact. Six existing payloads changed/three added;1568old payloads unchanged. Preserve eight inherited repairs across nine resources: eight byte-identical, all Spy old nodes/Mark/Ana phone fixes preserved with only future Armed splice. No Sandra/Delamain counter resets or rejected Delamain admission patch.

The full161-quest deep audit was already complete. Do not repeat it. Original21 QR7 targets are reconciled;13FAIL→prospective CONDITIONAL, three UNKNOWNs→2AD/1COND, fiveUNKNOWN retained. Full grid349PASS/177AD/917CONDITIONAL/162OPAQUE/5UNKNOWN; zero fullySTATIC_VERIFIED quests. No gameplay success is inferred.

Next static work, only if chosen by a new user task:
- Career persistence: exact original early SMS owner retirement/saved concurrency, not merely equal-state journal behavior.
- Cuckoo sts_std_rcr_02: numeric inventory114327022403 provenance/invalid-query semantics and original four NULL-source endpoints. Earlier “Arroyo courier” label was wrong; do not invent a grant/item.
- Voodoo: exact DoorControllerPS/TerminalControllerPS binding, source-realizable prior-claim eligibility, hub/Inject/context/transaction merge and persistent entity IDs/owner retirement.
- Ronald partial scope: original B0 subscription1755 remains unreachable. First-contact/new enrollment and old entered/sent/done/pending native clocks are explicitly unsupported; source/ownership evidence must precede any adapter. Do not clone whole bar, reset clocks/sent/pause or fabricate contact consent.
- Current registration restore-source boundary and any final addendum are in REGISTRATION_BOUNDARY.md/completion.json. Never promote old PR63 source to the different installed DLL by name alone.

README.md lists replayable fresh-output checks. Do not rerun initializers, coordinator integration/freezing/packaging/publishing scripts or historical proposal builders against pinned outputs. Reuse exact source/peer evidence, including failed prototypes and stale cached-JSON corrections. All131REDS/134compiler input pins/46managed sources match QR6's actual fresh compile; reuse evidence rather than rebuild unchanged code. Full final artifact/matrix reviews and preservation are pinned in completion.json after final independent review.

No new chat/archive/cleanup was authorized. Preserve all staged candidates, private failure evidence and existing user changes. Future deployment/testing requires its own explicit scope and current gates; see INGAME_VALIDATION_PLAN.md.
''',encoding='utf-8')
(O/'README.md').write_text('''# QR7 evidence and reproducible checks

Start with completion.json, REPORT.md and HANDOFF.md. The staged candidate is QR7:04/candidate_01; installedPH3 is unchanged. Reusable scripts below read existing exact pinned inputs and write only fresh evidence directories. They require the current repository, existing ignored raw/native/worker exports, Python3.14, and for PowerShell captures WolvenKit9.1 at research/sidejobs_s28/tooling/wolvenkit_9_1_0/package. Helpers load tools/build_phase2a.ps1 only with -HelpersOnly. Run from the repository root; output directories must not exist. A mismatching pin fails closed: investigate a new provider/version rather than changing the old pins.

Use `C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B` for each Python command.

```powershell
# Actual serialized Nitro source/native gate;32checks/80fixtures/three raw-document mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/check_nitro.py --output prealpha/quest_restoration_qr7/reproduce/nitro_01
# Frozen CVI04 raw readback/native protocol;75checks/three document mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_a/verify_listener_v4.py --output prealpha/quest_restoration_qr7/worker_a/reproduce_listener_01
# Exact pinned native actor/community/marker binding;29checks/two typed controls.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_a/verify_actor_context.py --output prealpha/quest_restoration_qr7/worker_a/reproduce_actor_01
# Ronald raw buffer/native selected protocol;10checks/three packed controls;83checks/seven document mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_bar.py --out reproduce_bar_check_01
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_future.py --out reproduce_future_check_01
# Independent complete final archive extraction and51fileZIP validation;1738checks on current inputs.
pwsh -NoProfile -File prealpha/quest_restoration_qr7/worker_a/run_final_independent.ps1 -Epoch prealpha/quest_restoration_qr7/source_epoch_04.json -ApprovedChanges prealpha/quest_restoration_qr7/approved_changes_03.json -FinalManifest prealpha/quest_restoration_qr7/candidate_01/package_manifest.json -Output prealpha/quest_restoration_qr7/worker_a/reproduce_package_01
# Protected bytes and complete game/save metadata (read-only); expect zero discrepancies on unchanged inputs.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr7/verify_preservation.py --output prealpha/quest_restoration_qr7/reproduce/preservation_01
```

Expected output: each fresh directory contains a result/evidence JSON, individual assertions, exact pins and private mutation evidence where applicable. None of these commands deploys, rebuilds the candidate, changes game resources or runs the game. The CVI/Ronald proposal checks are tied to frozen source/readbacks; the final package verifier is the independent link to actual final payloads. Broad prior prerequisites and LIVE_ONLY limitations are not converted to PASS by these checks. See worker_c/REPRODUCE.md for four native-journal/remaining-input checks and exact native capture procedures. Shared registry entries identify producing scripts; script presence alone is not an executable procedure.

Historical one-shot recipes: initialize.py, prepare_nitro.py, patch_nitro.ps1, integrate_cvi.py, integrate_ronald.py, readback_* coordinator scripts, freeze_source.py, rebuild_candidate.ps1, package_candidate.py, publish_findings.py, publish_support.py and write_reports.py. They have fixed/pinned outputs and must not be blindly rerun. Prior worker experiments/prototypes are evidence, not installation instructions. Failed CSV publication/readback/prototype attempts remain preserved; authoritative later manifests supersede them explicitly.
''',encoding='utf-8')
write(O/'checkpoint.json',{'state':'QR7_SOURCE_PACKAGE_MATRIX_PRESERVATION_FROZEN_FINAL_REVIEW_PENDING','source_epoch':'QR7:04','source_epoch_manifest':str(O/'source_epoch_04.json'),'candidate':str(O/'candidate_01'),'targets_completed':len(read(O/'targeted_dispositions.json')),'remaining_UNKNOWN':5,'pending_gates':['Installed ArchiveXL1.28.0 restore-source applicability disposition','Independent final reports/ledger/preservation completeness review','Completion seal'],'installed':'PH3 unchanged','next_action':'Finish source applicability and independent final report review; correct only evidenced gaps. No deploy or further broad audit.'})
print({'status':'REPORT_HANDOFF_CHECKLIST_AND_REPRODUCTION_WRITTEN','remaining_final_gates':3})
