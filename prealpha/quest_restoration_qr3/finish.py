"""Finish the Q01 deliverable with exact scope checks and continuation evidence."""
from pathlib import Path
import sys,json,datetime,ast,re,uuid,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'EVIDENCE.json').exists(),'Preserve final evidence'
q=read(O/'queue.json');cp=read(O/'checkpoint.json');rows=read(O/'contract_status_matrix.json');manifest=read(O/'candidate_01/package_manifest.json')
assert q['selected_count']==161 and q['deep_reviewed_count']==16 and len(rows)==1610
assert cp['Q01_deep_reviewed']==cp['Q01_total']==16 and q['static_verified_count']==0
assert q['gameplay_repairs']==2 and manifest['paths']==51 and len(manifest['changed_resources'])==2
assert read(O/'protection_after.json')['status']=='PASS'
assert read(O/'compile_reuse.json')['status'].startswith('PASS')
all_review=[O/'agents'/p for p in ['agent_d/reviews/racing.json','agent_e/reviews/vehicles.json','agent_b/reviews/brendan_quarantine.json','agent_f/reviews/communications.json','agent_b/reviews/progression.json','agent_e/reviews/boxing.json','agent_d/reviews/brendan_serialized.json','agent_d/reviews/mq030_serialized.json','agent_d/final_package_review_01/evidence/review.json']]
for p in all_review:
 assert p.is_file(),str(p)
 assert read(p)['status'].startswith(('PASS','APPROVE_')),str(p)
write(O/'review_resolutions.json',{'status':'RESOLVED_SOURCE_AND_VERIFIER_CORRECTIONS_STATIC_LIMITS_RETAINED','items':[
 {'id':'QR3-MQ037-EXCLUDED-FRESH','resolution':'Independent raw review and actual serialized review approve preclaim Refused containment; valid later earned-history adapter remains explicit implementation blocker.','evidence':'defects_and_repairs.json'},
 {'id':'QR3-MQ030-VENDOR-LEASE','resolution':'Native retirement acknowledgement plus pending-wait decisions serialized; independent actual-resource and final packaged-byte checks pass. No engine/saved-state success claimed.','evidence':'agents/agent_d/reviews/mq030_serialized.json'},
 {'id':'REVIEW-B-ANCESTRY','resolution':'Two historical global parents superseded by fresh current native payloads; B preserved original docs and corrected top-caller wording. Saved-owner conditional boundary remains.','evidence':'agents/agent_b/ancestry_update_02.json'},
 {'id':'QR3-CHECKER-SOCKET','resolution':'Checker expected generic In instead of actual native journal Inactive; corrected assertion, not resource edges.','evidence':'verification_corrections.json'},
 {'id':'QR3-D-INPUT-AND-TRIGGERS','resolution':'MQ049 parent is quest_bugfixing root/3; raw/JSON path lookup and precise trigger names corrected with previous evidence preserved.','evidence':'agents/agent_d/finding_corrections.json'},
 {'id':'QR3-F-REVIEW-PROBES','resolution':'Independent reviewer corrected scalar record probe and abbreviated direct-edge assumptions against full raw reachability; original communication findings supported.','evidence':'agents/agent_f/reviews/communications.json'},
 {'id':'QR3-F-S22-SEAM','resolution':'Current S22 primary root is Inactive; only bounded child failure states are allowed. Child-failure provenance remains CONDITIONAL, not a speculative reset repair.','evidence':'agents/agent_f/REPORT.md'}],
 'not_resolved_by_agreement':'Missing world/target-data/localization/saved-runtime evidence remains CONDITIONAL or OPAQUE; no contract promoted based solely on reviewer agreement.'})
nextlist='\n'.join('- `'+r['id']+'` — '+r['title'] for r in cp['next_batch_quests'])
handoff=f'''# Codex Context Handoff

Created: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
Source thread: 01a187f9-62cf-7710-94f5-b14c888b3237
Source host: local

## Goal

Continue the same comprehensive 161-quest PTFR restoration project after QR3. All Q01 quests are deep-reviewed (16/16); 145 other quests remain. Read QR3 REPORT.md, checkpoint.json, queue.json and REQUEST.md. Preserve the original acceptance criteria in QR1 REQUEST.md and the applicable AGENTS.md/knowledge files.

## Acceptance criteria

Each selected quest needs ten evidence-backed contracts: entry, eligibility, communications, ownership, progression, presentation, journal, completion/rewards/cleanup, persistence and shared dependencies. Verify actual native/current nodes, sockets, predicates, writers and owners. Repairs require source-confirmed faulty route, minimal compatible change, failing-before/passing-after regression, independent review, serialization/readback and affected final-package/input verification. Preserve unknown and live-only limits. No quest is fully STATIC_VERIFIED yet.

## Communication preferences

- Reply language: English.
- Locale or time zone: America/Toronto, supplied by the user environment.
- Use concise, candid progress and complete authorized work without redundant confirmation.

## Applicable constraints

Root and prealpha AGENTS.md apply. User authorizes multi-agent investigations, source-confirmed repairs, scoped tests and staged builds. No game launch, deployment, installed-file edits, save/fact edits, release changes or Git publication. Do not change selection or restore excluded/held jobs; do not replay setup/rewards or fabricate history/acknowledgements. Preserve saved identities, original ownership and PH3 fixes. Do not retry rejected Delamain patch or synthetic Sandra/Delamain resets. Reuse unchanged QR1/QR2 compilation, identity, reproduction and general-provider work.

## Workspace identity

- Path: C:/Users/Ayong/Documents/cp77 modding/tower ws
- Source workspace kind: saved checkout, no worktree or branch change.
- Destination compatibility: use this exact workspace with ordinary permissions.
- Repository or artifact: PTFR. Installed baseline remains PH3. Working staged successor is prealpha/quest_restoration_qr3/candidate_01.
- Branch and HEAD: main; ff336a14675b3385b1a4a6b4a27ce23086b61ce3.
- Working-state summary: pre-existing dirty AGENTS.md/PROJECT.md/README.md/ROADMAP.md preserved. QR1/QR2 are pinned. QR3 edits are isolated under its directory; no commit. Six assignments used three concurrent workers; tool limits required four distinct worker threads, A reused for E and C for F.

## Source lifecycle

- Goal status: none
- Goal status evidence: get_goal returned null at QR3 close.
- Source archival authorization: unspecified; do not archive.
- Source closure status: requested documentation handoff only; no new chat created.

## Completed and verified

- VERIFIED — all 13 remaining Q01 quests have ten initial dispositions, raw source evidence, focused tests and independent cross-review. QR2's three are retained. Queue covers all 161; Q01 has 45 PASS, 24 APPROVED_DEVIATION, 75 CONDITIONAL and 16 OPAQUE contract dispositions. 0 full static certifications. Counts are not gameplay coverage.
- VERIFIED — six assignment investigations ran 1,510 focused assertions including 35 mutations. Exact tests/source pins and independent reviews are indexed in REPORT.md; original baseline fault reproductions remain visible.
- VERIFIED — Brendan excluded-fresh leak contained by only1004.True→existing1008.Refused. All 13 saved node payloads remain; no new native issuance. Valid later earned-Dumpster adapter is still unsupported. Do not call the sequels restored.
- VERIFIED — MQ030 helper now wakes on real Finished and retires through native Terminating output before lease release; pending rearm uses a separate finished decision. Old IDs preserved; two new local graph IDs1022/1023. Engine/save transitions untested.
- VERIFIED — independent final archive review: same1,574keys, exactly two approved changes (MQ030/MQ037), other1,572payloads and50packagefiles unchanged, including REDscript and XL. ZIP51paths/CRC/hashes pass. No new depot or ArchiveXL registration IDs. Source allowlist approved_changes_02.json.
- VERIFIED — staged ZIP {Path(manifest['zip']).name}; SHA256 {manifest['zip_sha256']}. NOT installed/published. Current candidate archive SHA256 {manifest['archive_sha256']}.
- VERIFIED — exact131REDscript/compiler/cache inputs and46staged managed scripts match QR1's successful compile; no unchanged SCC rebuild. 2,676protected hashes and complete game/save metadata unchanged.
- VERIFIED — native_owner_gap_resolution.json replaces two stale historical global parents with current unique native providers and proves world-activity ancestor containment. All six vehicle input pins match current providers. Prior exports are historical, not current vanilla.

## Unverified and open

- UNVERIFIED — earned-history Brendan sequel adapter: exact native stage, retired/adoptable owner, choices/rewards and persistent identity review required. Do not restore excluded Dumpster or run fullIn1 from invented history.
- UNVERIFIED — exact TweakDB reward/economic/vehicle/keycard target definitions, streamed actor/prefab/workspot/camera bindings and localization/JV1 semantics remain per-quest static limits. Source/reference equality is not target-definition proof.
- UNVERIFIED — actual owner cancellation, saved already-passed preclaim or preexisting vendor overlap, interruption, playback/fights/driving, reward/debit and reload/version transitions require runtime fixtures. No game was launched or save inspected/changed.
- UNVERIFIED — remaining145quests await deep review. Q02 boxing siblings may reuse F's shared graph evidence but still need their own contract dispositions.

## Failures and discarded approaches

Do not present baseline14FAIL contract entries as14bugs: they describe two shared defects; repaired dispositions remain CONDITIONAL where implementation/evidence is incomplete. No direct cut/release fanout was used for MQ030; native retirement acknowledgement is authoritative. Two stale parent hashes and checker/prose errors are recorded in review_resolutions.json. MQ049 trigger names and S22 rootInactive semantics were corrected from actual raw inputs. Original revisions remain preserved. Working checkpoint predates final checkpoint and is historical.

## Next action

Begin Q02 in bounded parallel assignments using QR3 queue and staged candidate as the working source successor, while distinguishing still-installed PH3. Do not discard the two staged repairs or reinstall/rebuild unchanged baselines. Exact Q02:

{nextlist}

## Destination sentinel

Read-only: confirm workspace/HEAD; queue.selected_count161, deep_reviewed_count16, static_verified_count0, gameplay_repairs2; Q01deep16/16. Read EVIDENCE.json, approved_changes_02.json, candidate_01/package_manifest.json, compile_reuse.json and protection_after.json. Verify the ZIP hash above and final independent review pointer. Inspect candidate MQ030/MQ037 source hashes against allowlist; all other PH3 payloads must remain exact. Do not rerun pinned checkpoint/build scripts or overwrite evidence. Fresh verifiers need fresh output directories.

## Recovery

QR1/QR2/PH3 and game installation remain intact. QR3 candidate is staged only, so no game rollback is needed or authorized. Keep candidate/proofs recoverable. Source-side backup is recorded in handoff_backup_path.json; continuation should use this workspace packet, not require the backup. No automatic new chat, archive, commit or publication occurred.
'''
(O/'HANDOFF.md').write_text(handoff,encoding='utf-8')
backup=Path(r'C:\Users\Ayong\.codex\visualizations\2026\10\29\01a187f9-62cf-7710-94f5-b14c888b3237')/('ptfr-qr3-handoff-'+str(uuid.uuid4())+'.md')
backup.write_text(handoff,encoding='utf-8');write(O/'handoff_backup_path.json',{'path':str(backup),'purpose':'Source-side recovery packet; no chat created'})
missing=[]
for target in re.findall(r'\]\(([^)]+)\)',(O/'REPORT.md').read_text(encoding='utf-8')):
 if not (O/target).exists():missing.append(target)
assert not missing,missing
python_files=[]
for p in O.rglob('*.py'):
 ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));python_files.append(str(p))
files=[p for p in O.rglob('*') if p.is_file()]
write(O/'EVIDENCE.json',{'status':'PASS_QR3_Q01_DELIVERY_WITH_EXPLICIT_LIMITS','overall_project':'INCOMPLETE_145_QUESTS_AWAIT_DEEP_REVIEW','new_deep_quests':13,'Q01_deep_quests':16,'Q01_total':16,'full_queue':len(q['quests']),'contract_rows':len(rows),'new_contract_status_counts':cp['new_contract_status_counts'],'Q01_contract_status_counts':cp['Q01_contract_status_counts'],'fully_static_verified':0,'confirmed_unique_defects':2,'changed_resources':2,'protected_hashes':2676,'installed':False,'published':False,'independent_reviews':{str(p.relative_to(O)):sha(p) for p in all_review},'python_syntax_checked':python_files,'artifacts':{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files},'scope':'Static graph/source/package evidence only; no gameplay/save-transition success claim'})
print({'status':'PASS_QR3_Q01_DELIVERY','artifact_hashes':len(files),'python_files':len(python_files),'handoff_characters':len(handoff),'Q01':'16/16','changes':2,'remaining_quests':145})
