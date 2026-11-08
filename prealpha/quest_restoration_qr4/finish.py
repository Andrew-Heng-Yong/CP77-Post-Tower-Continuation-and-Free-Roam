"""Publish the reviewed QR4 result and bounded next-session handoff once."""
from pathlib import Path
import ast,datetime,json,sys,uuid,re
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'EVIDENCE.json').exists(),'Preserve completed evidence'
q=read(O/'queue.json');cp=read(O/'checkpoint.json');idx=read(O/'group_evidence_index.json');m=read(O/'candidate_01/package_manifest.json');p=read(O/'progress.json')
assert len(q['quests'])==161 and len(read(O/'contract_status_matrix.json'))==1610
assert cp['newly_deep_reviewed']==48 and q['deep_reviewed_count']==64 and cp['remaining_not_deep_reviewed']==97 and q['static_verified_count']==0
assert read(O/'protection_after.json')['status']=='PASS' and read(O/'compile_reuse.json')['status'].startswith('PASS')
assert all(g['status']=='REVIEWED_WITH_LIMITS' for g in p['groups'].values())
reviewpaths=[O/'groups/G11/reviews/QR4_package/REPORT.json',O/'groups/G11/reviews/QR4_package_supplement_03/REPORT.json',O/'groups/G11/reviews/G12_revision_01.json',O/'groups/G10/reviews/QR4_coverage/verification_02/review.json',O/'groups/G11/reviews/QR4_package/epoch03_linkage.json',O/'groups/G11/reviews/QR4_package/FINAL_REVIEW.json',O/'groups/G12/reviews/QR4_delivery_02.json']
for r in reviewpaths:
 assert r.is_file(),str(r)
 assert read(r)['status'].startswith(('PASS','APPROVE','INDEPENDENT')),read(r)['status']
assert sha(m['zip'])==m['zip_sha256']
group_rows=[]
for g in idx['groups']:
 ids=g['quest_ids'];names=', '.join(next(x['title'] for x in q['quests'] if x['id']==i) for i in ids)
 group_rows.append(f"| {g['group']} | {len(ids)} | {g['checks']} / {g['mutations']} | [{names}](groups/{g['group']}/results.json) |")
group_table='\n'.join(group_rows)
report=f'''# QR4 quest verification and staged repair

All Q02, Q03 and Q04 entries received deep source-specific investigation and independent review: **48 additional quests, 64/161 total**. The remaining **97** await deep investigation. No quest is fully STATIC_VERIFIED, and no gameplay success is claimed.

One new confirmed defect affecting **one quest** was repaired in **two resources**: Machine Gun's native post-return Skippy continuation was absent from the restored executing owner. The staged QR4 successor preserves both QR3 repairs. It has not been installed or published.

## Coverage and evidence boundary

The coordinator-owned [queue](queue.json) includes all 161 selected identities. [Contract JSON](contract_status_matrix.json) and [CSV](contract_status_matrix.csv) contain 1,610 rows; [quest JSON](quest_status_matrix.json) and [CSV](quest_status_matrix.csv) support resumption. Each of the 48 new quests has ten specific findings with native/effective node, edge, condition, writer, binding or owner evidence. Frozen epoch00 results remain as investigated; final matrix adjudication uses canonical epoch03, with explicit supersessions.

An independent linkage check caught an inherited QR3 archive hash in epoch02's top-level metadata. Its actual resource hashes, package rows and package were correct. [Epoch03](source_epoch_03.json) explicitly supersedes that metadata; [correction evidence](metadata_corrections.json) preserves the original. No resource or package bytes changed for this correction.

| Contract dispositions | New480 | All640deep-reviewed |
|---|---:|---:|
| PASS, scoped static properties | 129 | 174 |
| APPROVED_DEVIATION | 55 | 79 |
| CONDITIONAL | 248 | 323 |
| OPAQUE | 48 | 64 |

PASS applies to the stated property, not every target's content or engine behavior. The 97 quests awaiting deep investigation retain their prior pending statuses; earlier bounded QR1 checks are preserved. Three epoch00 MQ007 FAIL dispositions describe one defect, not three. They are CONDITIONAL after the bounded repair because old saved owners and live behavior remain unresolved.

Three investigation workers continuously consumed 12 related groups, sharing pinned controller evidence and rotating cross-reviews. Current tool capacity was four agents including the coordinator. [Evidence index](group_evidence_index.json) records 4,525 focused assertion events including 80 mutations; these are overlapping test events, not independent gameplay proofs. Some investigation controls compare normalized graph copies with pinned native expectations; they do not demonstrate end-to-end serialized fault detection. The actual MQ007 repair additionally has raw-resource mutations and independent binary readbacks. Reviewer checks and repair checks are separately recorded.

| Group | Quests | Checks / mutations | Results |
|---|---:|---:|---|
{group_table}

## Confirmed repair and preservation

Native return5/66 emits`mq007_done1`. The sole native post-return consumer is bugfixMQ007root14, within the original hierarchy terminated by genuine Tower cleanup. The original route waits for done, then five game days, then outside Regina's reacquisition trigger AND MinorQuestAndSts; it enables the persistent gun-return container variant, sends three native messages and sets the native reacquisition receipt. Global discovery across5,136pinned normalized models and the bounded REDscript closure found no restored consumer. [Discovery](groups/G08/regina_followup_01/evidence.json).

The two wrappers now branch only from a **future1101entry event** through an immediate ANDguard, shared durable claim, exact recursive native14copy and owned finish receipt. Nodes1200–1203 are local to each wrapper. Existing IDs, payloads, sockets, nested graphs and edge multiplicities are preserved. No new depot or ArchiveXL injection registration was added. The copied nested14/3 helper lease`#mq007_pr_gun_re_acquiring` is retained; this differs from the persistent world container`#mq007_pr_gun_return`, for which no new owner was invented. [World ownership](groups/G08/regina_world_01/ownership.json), [approved differences](approved_changes_01.json).

The repair enrolls future supported fresh/resume starts **before** native return completion. It does not adopt previously-entered/returned saves, restart their timers, relax the native11/51/95resume seam, reset counters or grant items. Those states remain deferred/unsupported. Native world descriptors establish persistent placement, while the available sector decoder still fails DynamicBaseClass/worldNode; exact sector/loot content remains OPAQUE. Engine content context, scheduling, saved timer restoration, streaming and pickup need live fixtures.

[Root regression](candidate_01/repair_mq007/verification_02/tests.json):72checks and6mutations, reproducing missing-consumer failure before and exact native continuation after. [Independent serialized review](groups/G10/reviews/MQ007_serialized/verification_01/review.json):163checks and6raw-resource mutations, using fresh independent binary exports and separate socket traversal. The review's original missing-any-fact simulator policy is explicitly corrected: absent scalar facts satisfy expected0; only required positive receipts establish positive provenance. [Corrections](review_resolutions.json). No engine missing0 rejection is claimed.

## Prioritized unresolved discrepancies

| Priority | Finding | Disposition / next evidence |
|---|---|---|
| High | Existing MQ007 progressed seam / old entered-returned timer ownership | Unsupported admission and migration remain explicit; exact stage, original/saved owner and elapsed-time fixtures needed. No reset or retroactive enrollment. |
| High | Delamain native parent154 standalone-token OR administration-mail prerequisite omitted by direct S25inner entry | CONDITIONAL; exact Tower replacement approval/context is not established. Shared counters/listeners do not justify retrying rejected admission patches. |
| High | Q01 Brendan later earned-history adapter | QR3 excluded-fresh containment preserved; valid later stage/owner/reward adapter still absent. Do not call sequels restored. |
| Medium | Life's Work → Sex on Wheels corrective one-day route vs normal three-day route | Native main5/startup55 and S23final1100 fences exist. Timing/context and saved-owner provenance remain CONDITIONAL; alternate routes alone do not prove duplicate running story owners. No guessed timer/rehost change. |
| Medium | Gig EntrySafe omissions and journal targets | Exact missing objective/mappin/#fact targets remain visible in G09–G12. Writer and lifecycle evidence varies; absence from a guard alone is not replay proof. |
| Medium | Native Serial Suicide end-request wait and Cole foreign community cleanup | Native protocol oddity retained; engine scheduling conditional. Cole one-edge isolation pinned to prior approved U9 recipe, not a new QR4 repair. |
| Medium | The Gig reward-prefab content and other scenes/world/reward targets | Source/reference comparisons do not decode all streamed prefab/workspot/camera/TweakDB/localization definitions. OPAQUE/CONDITIONAL per quest. |
| Runtime | Actor, phone, reward, save and interruption transitions | Static reachability and exact native payloads are proven only where stated. Actual cancellation, reload, scene playback, timers and rewards require in-game evidence. |

The false Spellbound/Violence phone-race hypothesis was rejected after tracing the actual1003pause barrier; no patch. Delamain's listener and body fork concurrently; all five authoritative G02communications findings now supersede the earlier incorrect before-body sentence. G12's late owner-fence prose refinement has a byte-verified reconstructed prior and explicit independent revision attestation, rather than an ignored hash mismatch. [Review resolutions](review_resolutions.json), [revision](groups/G12/revisions/stable_fences_01/revision.json).

The separate [coverage review](groups/G10/reviews/QR4_coverage/verification_02/review.json) passes 2,597 bounded checks with no open issues. It verifies 454 distinct binary-resource pins plus 17 distinct script/document pins, all 480 specific contracts and their review/input provenance. Its first revision misclassified documentary pins as binaries and confused the peer-review queue with pending investigations; both schema assumptions were corrected against actual files, with the failed revision preserved. These checks establish evidence coverage, not gameplay completeness.

## Build, package and scope checks

- Current working successor: `candidate_01`; installed baseline remains PH3. [Manifest](candidate_01/package_manifest.json), [allowlist](approved_changes_01.json), [defect registry](defects_and_repairs.json).
- Full1,574source payloads packed once and read back. Independent actual QR3→QR4 archive comparison confirms the same1,574keys, exactly2approved changed payloads and1,572unchanged, including QR3MQ030/MQ037. Other50package files are identical; XL registration bytes unchanged. [Independent package review](groups/G11/reviews/QR4_package/REPORT.json), [supplement](groups/G11/reviews/QR4_package_supplement_03/REPORT.json).
- Staged51-path ZIP CRC and every file hash pass. ZIP SHA256:`{m['zip_sha256']}`. Archive SHA256:`{m['archive_sha256']}`. This is a fresh staged successor, not an installed or released build.
- All131REDscript sources,134compiler/cache/input pins and46managed staged scripts match QR1's successful compile. No unchanged SCC invocation was repeated. [Current-input verification](compile_reuse.json).
- All4,500protected hashes and entire game/save filename-size-modification metadata remain unchanged. [Preservation](protection_after.json). No launch, deployment, save/fact edit, release overwrite or Git publication occurred.

[Continuation handoff](HANDOFF.md) names exact Q05identities and the saved sentinel. Continue from QR4, preserving its two-resource repair plus QR3's two-resource repairs. Do not rebuild the unchanged baseline or treat deep review as completed gameplay restoration.
'''
(O/'REPORT.md').write_text(report,encoding='utf-8')
nextlist='\n'.join('- `'+x['id']+'` — '+x['title'] for x in cp['next_batch_quests'])
handoff=f'''# Codex Context Handoff

Created: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
Source thread: 01a187f9-62cf-7710-94f5-b14c888b3237
Source host: local

## Goal

Continue the same161-quest PTFR restoration project from QR4. Read REQUEST.md, REPORT.md, checkpoint.json, queue.json and relevant scoped AGENTS/knowledge files. QR4 finished all32Q02/Q03plus16Q04deep investigations:64total,97remaining. No quest fully STATIC_VERIFIED. Proceed with Q05, not another baseline audit.

## Acceptance criteria

Ten evidence-backed contracts per selected quest: entry, eligibility, communications, ownership, progression, presentation, journal, completion/rewards/cleanup, persistence and shared dependencies. Trace exact native/effective nodes, sockets, predicates, writers, journal paths and ownership. Confirmed repairs require minimal compatible source change, independent review, failing-before/passing-after regression, serialization/readback and affected final-package validation. Keep approved differences, unresolved static evidence, opaque assets and live-only behavior separate. Preserve the full original161selection requirement.

## Communication preferences

- Reply language: English.
- Locale or time zone: America/Toronto from the environment, independent of language.
- Concise, candid progress; continue authorized work without redundant confirmation.

## Applicable constraints

Root/prealpha AGENTS.md apply. Multi-agent investigation and confirmed source repairs/staged builds were authorized. No deployment, launch, saves/facts, release overwrite or Git publication. Preserve Tower completion, curedV/history, native ownership/outcomes, saved identities and all PH3fixes. Do not change whitelist or revive excluded/held content. Never retry rejected Delamain admission or synthetic Sandra/Delamain resets. No arbitrary acknowledgement, door/AI command or reset bypass. Future sessions must honor their own user's scope.

## Workspace identity

- Path: C:/Users/Ayong/Documents/cp77 modding/tower ws
- Source workspace kind: saved checkout, no worktree or branch change.
- Destination compatibility: use this exact workspace with ordinary permissions.
- Repository or artifact: PTFR; working successor prealpha/quest_restoration_qr4/candidate_01; installed remains PH3.
- Branch and HEAD: main; ff336a14675b3385b1a4a6b4a27ce23086b61ce3.
- Working-state summary: preexisting dirty AGENTS/PROJECT/README/ROADMAP and earlier untracked work preserved; QR4 isolated under its new directory, no commit. Three continuously replenished workers; all12groups cross-reviewed.

## Source lifecycle

- Goal status: none
- Goal status evidence: supported get_goal returned null at QR4 finalization.
- Source archival authorization: unspecified; do not archive.
- Source closure status: saved documentation handoff; no automatic new chat or archive.

## Completed and verified

- VERIFIED — 48new quests/480specific contract dispositions; allQ02/Q03/Q04deep-reviewed and independently reviewed, total64/161. New counts129PASS/55APPROVED_DEVIATION/248CONDITIONAL/48OPAQUE. All640deep contracts174PASS/79AD/323COND/64OPAQUE; full static certifications0. Investigation4525assertion events including80mutations, not independent gameplay coverage.
- VERIFIED — One new unique MQ007missing-native-postreturn-consumer defect, affecting one quest and two wrapper resources. Future1101event-only enrollment copies exact nativebugfix14including nested helper, five days, context, messages, variant and receipt. Old IDs/graphs/edges and admission are preserved. No retroactive saved-timer adoption.
- VERIFIED — Root72checks/6mutations; independent serialized163checks/6rawmutations. Native world descriptors prove persistent gun-return placement, distinct nested helper is retained; sector content remains opaque. FactsDB expected0 fixture correction is explicit.
- VERIFIED — Actual independent final archive/package/ZIP comparison: same1574keys, exactly2MQ007differences vsQR3, other1572payloads/50files unchanged. QR3MQ030andMQ037fixes intact. No new depot/XLregistration. Four cumulative changed resources vsPH3, three cumulative unique repairs/containments.
- VERIFIED — Staged ZIP SHA256 {m['zip_sha256']}; archive SHA256 {m['archive_sha256']}. ZIP51paths CRC/allhashes pass. Not installed/published.
- VERIFIED —131sourcecompile134inputpins/46managedsources hash-identical to QR1successful compile; no redundantSCC. Protection4500hashes and complete game/save metadata unchanged.
- VERIFIED — G02concurrency prose superseded, G03falsephone-race rejected, G12late evidence revision explicitly hash-reconciled; original evidence and corrections remain preserved.

## Unverified and open

- UNVERIFIED — MQ007known11/51/95progressed admission seam and already-entered/returned saved timers remain unsupported. Do not reset/adopt/restart to reduce unknowns. Engine timers/context/streaming/pickup and sector loot content remain live/opaque.
- UNVERIFIED — Delamain native parent154token/mail eligibility replacement not approved/proved; listeners/body are parallel. No rejected admission patch or synthetic counter reset.
- UNVERIFIED — Brendan earned-history sequel adapter remains blocked after valid excluded-fresh containment. Exact stage, owner, choices/reward and identity review needed.
- UNVERIFIED — LifeWork/MQ044one-day corrective vs three-daynormal timing/context remains conditional. Existing native main and final S23fences prevent claiming duplicate runtime stories solely from branch presence. No guessed rehost/timer patch.
- UNVERIFIED — Gig journal/mappin/#fact guard gaps, target definitions, prefab/world/camera/workspot bindings, rewards/localization and saved/shared ownership remain quest-specific conditional/opaque findings. Reference equality alone is not complete semantics.
- UNVERIFIED — All97remaining quests still need deep investigation; no runtime quest behavior, transition or gameplay certification was performed.

## Failures and discarded approaches

Do not repeat unchanged QR1 identity/admission/compile/reproduction/provider work. Epoch00 worker findings are against QR3; only the two MQ007 wrappers changed for the packaged successor. Canonical epoch03 explicitly corrects epoch02's inherited predecessor archive metadata, with identical resource/package bytes. Preserve original three FAIL contracts as one bounded repaired defect. False S24 phone race skipped the real 1003 barrier and was rejected. Empty outer prefabs did not mean the native nested helper was unnecessary. Original missing-any-fact simulator was conservative policy: the actual fixture uses absent scalar zero; positive receipts and the future event establish provenance. The G12 post-completion prose update triggered the hash gate; the exact prior was reconstructed byte-identically and the current version explicitly attested. Root checker supports both package stages and pins code/JSON inputs; use fresh outputs.

## Next action

Begin bounded parallel Q05investigations from QR4queue/candidate. Preserve MQ007future-only repair plus QR3MQ030/MQ037changes. Exact next batch:

{nextlist}

## Destination sentinel

Read-only: verify exact workspace/HEAD, queue 161/deep 64/static 0/new 48/remaining 97/source epoch3; 1,610 matrix rows; all 12 groups reviewed. Inspect approved_changes_01.json, canonical source_epoch_03.json and metadata_corrections.json. Candidate MQ007 fresh SHA0362F5C3016643007F3B36B0E9E9CC1DAE668B142D7C66BB79BF09B4650D1F89; resume SHA2A98C7B674C1BDC249CDACFEE44B53316E173E24E7F637DFC94698D16BA428AE. Check the staged ZIP hash above, preserved QR3 fixes and independent package/coverage pointers in EVIDENCE.json. Do not rerun pinned startup/patch/build scripts or overwrite proof outputs. A mismatch is HANDOFF REGRESSION, not permission to discard fixes.

## Recovery

PH3installation, saves, QR1/QR2/QR3evidence and releases remain untouched. QR4is staged only, so game rollback is neither needed nor authorized. Keep successor and proofs recoverable; source-side packet backup is recorded in handoff_backup_path.json. No chat creation, archive, branch change, commit or publication occurred.
'''
(O/'HANDOFF.md').write_text(handoff,encoding='utf-8')
backup=Path(r'C:\Users\Ayong\.codex\visualizations\2026\10\29\01a187f9-62cf-7710-94f5-b14c888b3237')/('ptfr-qr4-handoff-'+str(uuid.uuid4())+'.md');backup.write_text(handoff,encoding='utf-8');write(O/'handoff_backup_path.json',{'path':str(backup),'purpose':'Source-side recovery, no chat created'})
for match in re.findall(r'\]\(([^)]+)\)',report):assert (O/match).exists(),match
pyfiles=[]
for f in O.rglob('*.py'):ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f));pyfiles.append(str(f))
p['status']='QR4_STRETCH_COMPLETED_WITH_STATIC_LIMITS_STAGED_NOT_INSTALLED';p['final_checkpoint']=str(O/'checkpoint.json');p['independent_final_reviews']=[{'path':str(r),'sha256':sha(r)} for r in reviewpaths];write(O/'progress.json',p)
write(O/'WORKING_CHECKPOINT.json',{'state':'SUPERSEDED_BY_FINAL_CHECKPOINT','final':str(O/'checkpoint.json'),'queue':str(O/'queue.json'),'handoff':str(O/'HANDOFF.md'),'working_candidate':str(O/'candidate_01'),'installed':'PH3 unchanged'})
files=[f for f in O.rglob('*') if f.is_file()]
write(O/'EVIDENCE.json',{'status':'PASS_QR4_STRETCH_DELIVERY_WITH_EXPLICIT_STATIC_LIMITS','overall_project':'INCOMPLETE_97_QUESTS_AWAIT_DEEP_REVIEW','selected':161,'new_deep':48,'deep_total':64,'fully_static_verified':0,'contract_rows':1610,'new_dispositions':cp['new_contract_status_counts'],'all_deep_dispositions':cp['deep_contract_status_counts'],'new_unique_defects':1,'new_affected_quests':1,'new_changed_resources':2,'cumulative_unique_repairs_or_containments':3,'cumulative_changed_resources_vs_PH3':4,'protected_hashes':4500,'investigation_assertion_events':idx['investigation_checks'],'investigation_mutations':idx['investigation_mutations'],'independent_final_reviews':p['independent_final_reviews'],'syntax_checked_python':pyfiles,'artifacts':{str(f.relative_to(O)):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in files},'installed':False,'published':False,'game_writes':0,'save_writes':0,'scope':'Static source, graph, fixture and package properties only; not gameplay or save-transition success'})
print({'status':'PASS_QR4_STRETCH_DELIVERY_WITH_LIMITS','new_deep':48,'deep_total':64,'remaining':97,'artifacts':len(files),'python_syntax_checks':len(pyfiles),'backup':str(backup)})
