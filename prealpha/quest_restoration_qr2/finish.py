"""Finalize bounded QR2 evidence and the requested continuation packet."""
from pathlib import Path
import sys,datetime,ast,uuid,json
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'EVIDENCE.json').exists(),'Preserve final checkpoint'
q=read(O/'queue.json');cp=read(O/'checkpoint.json');rows=read(O/'contract_status_matrix.json')
assert len(q['quests'])==161 and len(rows)==1610 and q['deep_reviewed_count']==3
assert q['static_verified_count']==0 and q['gameplay_repairs']==0
assert read(O/'protection_after.json')['status']=='PASS'
assert read(O/'reuse_validation.json')['status']=='PASS'
assert not list(O.rglob('*.zip')) and not (O/'candidate_01').exists()
quest_dirs=['mq045_victor_debt','mq038_neweridentity','mq035_ozob']
for i in quest_dirs:
 f=read(O/'quests'/i/'contracts.json');assert len(f['contracts'])==10
 assert f['contracts']['completion']['status']=='CONDITIONAL'
 assert all(x['proven'] and x['evidence'] for x in f['contracts'].values())
tested={
 'paid':O/'quests/mq045_victor_debt/verification_02/tests.json',
 'big_in_japan':O/'quests/mq038_neweridentity/tests_04.json',
 'ozob':O/'quests/mq035_ozob/verification_02/tests.json',
 'ancestor':O/'ancestor_review.json',
 'paid_review':O/'reviews/paid_in_full.json',
 'big_review':O/'reviews/big_in_japan.json',
 'ozob_review':O/'reviews/send_in_clowns.json'}
for name,p in tested.items():
 t=read(p);assert t['status'].startswith('PASS'),(name,t['status'])
write(O/'review_resolutions.json',{
 'status':'RESOLVED_VERIFIER_AND_STATUS_FINDINGS_NO_RUNTIME_DEFECT',
 'issues':[
 {'id':'REVIEW-PAID-001','resolution':'Full completion now CONDITIONAL; unresolved EconomicAssignment target definition distinguished from preserved native debit data and live execution.','evidence':'quests/mq045_victor_debt/contracts.json'},
 {'id':'QR2-MQ038-R1','resolution':'Full completion now CONDITIONAL; exact reward record and katana token/loot variant static inputs carried within completion.','evidence':'quests/mq038_neweridentity/contracts.json'},
 {'id':'QR2-MQ038-R2','resolution':'Test helper rejects absent journal/fact; fresh157-check output includes explicit missing-state controls. Current S23 runtime was already fail closed.','evidence':'quests/mq038_neweridentity/tests_04.json'},
 {'id':'QR2-MQ035-REPRO','resolution':'Checker requires --output fresh directory; original evidence hashes unchanged; missing/existing output refusal and50-check reproduction pass.','evidence':'quests/mq035_ozob/verification_02/reproducibility.json'},
 {'id':'QR2-MQ035-COMPLETION','resolution':'Full completion CONDITIONAL pending QuestRewards target definition; native recipe and reward branches remain proven.','evidence':'quests/mq035_ozob/contracts.json'}],
 'review_snapshots':'Original reviews and earlier tests remain immutable evidence. Corrections supersede the indicated claims; no gameplay source patch is implied.'})
remaining='\n'.join('- `'+r['id']+'` — '+r['title'] for r in cp['remaining_Q01'])
handoff=f'''# Codex Context Handoff

Created: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
Source thread: 01a187f9-62cf-7710-94f5-b14c888b3237
Source host: local

## Goal

Continue the incomplete comprehensive161-quest PTFR restoration task, using QR2's successor queue. This is the same project. Read prealpha/quest_restoration_qr1/REQUEST.md and QR2 REPORT.md/checkpoint.json/queue.json. First three Q01 investigations are finished with bounded static findings, not full certification. Continue remaining Q01 in later batches and repair only source-confirmed defects.

## Acceptance criteria

Verify all ten contracts per selected quest: entry, eligibility, communications, native ownership, progression, presentation, journal, completion/rewards/cleanup, persistence and shared dependencies. A repair needs exact original/current route evidence, smallest compatible change, defective-versus-repaired regression, serialization/readback, affected full-package/static checks, current-input compile and independent review. No speculative repair or UNKNOWN-to-PASS conversion. Full scope161 remains;0 are STATIC_VERIFIED.

## Communication preferences

- Reply language: English.
- Locale or time zone: America/Toronto from user environment.
- Concise and candid; continue authorized work without redundant confirmation.

## Applicable constraints

Root/prealpha AGENTS.md and developer knowledge apply. Source repairs, scoped tests and staged builds are authorized. No deployment, game launch, saves/facts, release changes, publication or Git pushes. Multi-agent work explicitly allowed. Preserve native Tower, histories/outcomes/rewards, saved identities, original owners and PH3 fixes. No rejected Delamain admission patch, Sandra/Delamain counter resets or unchanged baseline-only ZIP.

## Workspace identity

- Path: C:/Users/Ayong/Documents/cp77 modding/tower ws
- Source workspace kind: saved checkout; no worktree change.
- Destination compatibility: use this exact workspace with ordinary permissions.
- Repository or artifact: PTFR, current installed PH3 candidate prealpha/phone_studios_ph3/candidate_01.
- Branch and HEAD: main;ff336a14675b3385b1a4a6b4a27ce23086b61ce3.
- Working-state summary: pre-existing dirty AGENTS.md/PROJECT.md/README.md/ROADMAP.md preserved; QR1 remains pinned; all QR2 edits under prealpha/quest_restoration_qr2. No commit.

## Source lifecycle

- Goal status: none
- Goal status evidence: get_goal returned null in QR2.
- Source archival authorization: unspecified; do not archive.
- Source closure status: documentation handoff only; no new chat created.

## Completed and verified

- VERIFIED — deep ten-contract investigations for mq045_victor_debt, mq038_neweridentity and mq035_ozob; see each quests/ID/contracts.json and REPORT.md.30contracts:12PASS,5APPROVED_DEVIATION,10CONDITIONAL,3OPAQUE. No gameplay patch justified;0full static certifications.
- VERIFIED — Paid native six-node debt chain and current Viktor payment route preserved; Big in Japan native progression/Dennis protocol/reward pointers preserved; Ozob native q110/StreetCred, actual phone connections, progression/journal/reward branches preserved.
- VERIFIED — independent cross-agent reviews and corrections in reviews/ and review_resolutions.json. Test-helper missing-state handling and claim statuses corrected; no runtime defect established.
- VERIFIED — Paid7propertygroups+45negatives+8mutations;Big157checks incl4mutations;Ozob50checks incl4mutations/fresh-output guards;independent reviews27/24/56checks;native ancestor12checks. Exact evidence paths in REPORT.md. Do not add counts as gameplay coverage.
- VERIFIED — fresh134archive bounded lookup313queries/304providers/277hashedgraphpayloads,0pin mismatch/differingprovider hashes.15native-declared English lipsync literalpaths unresolved. Fresh parent ancestry: genuine Tower journal→receipt109→Terminating107 encloses native minorquests/bugfix trees.
- VERIFIED — reuse_validation.json proves QR1's131source/compiler/cache inputs,1574payloads,51package+installed paths unchanged. QR1 compile/reproduction/38controls reused, not rerun. No QR2 ZIP exists. Protection2595hashes and entiregame/save metadata unchanged.

## Unverified and open

- UNVERIFIED — all three require exact streamed prefab/actor/marker/workspot placement, locale resolution and reward/economic TweakDB target definitions before full static certification. Quest-specific NodeRefs/record IDs are listed in contracts, not generic UNKNOWN.
- UNVERIFIED — saved executing-owner adoption, transition/reload, interrupt arbitration and actual payment/reward delivery are live/engine boundaries. No save was decoded or modified and no gameplay test is requested here.
- UNVERIFIED — remaining158quests have not had deep contracts investigated. QR1's general evidence remains valid but is not a substitute.

## Failures and discarded approaches

No source-confirmed gameplay defect in this batch. Do not alter preserved native routes to clear opaque warnings. MQ038 test helper previously treated absent journal as Inactive; final tests_04 and verify.py now reject unknown inputs, matching already-correct runtime S23. Full completion statuses were corrected to conditional because referenced economic/reward data are not independently resolved. Ozob checker now refuses existing output paths. Earlier tests/reviews remain evidence, not current assertions when superseded.

## Next action

Begin next Q01 batch with07_nc_underground(The Beast in Me),mq046_cave_vehicle(Murk Man Returns Again Once More Forever),mq037_brendan(Coin Operated Boy), using QR2 queue identity/evidence routes. Do not repeat three completed deep investigations unless addressing an explicit listed blocker. Exact remaining Q01:

{remaining}

## Destination sentinel

Read-only: verify workspace/HEAD; QR2 queue selected_count161,deep_reviewed_count3,static_verified_count0,gameplay_repairs0;30newcontractrows;QR1 files unchanged. Read EVIDENCE.json,protection_after.json,reuse_validation.json and review_resolutions.json. Do not rerun fixed-output checkpoint scripts or QR1 builds; focused quest verifiers require fresh outputs. PH3 archiveSHA18B855B55A62771F146B9BA518F8DB782832606AA7666755303EEBA91D9F66C7,XL C55FB23E72710FD0FC8D348C62E2118C2E3FAD04DE3FCE2E6B459E6AB2A1F720.

## Recovery

All work/evidence under prealpha/quest_restoration_qr2;QR1/PH3 remain intact. No install or runtime delta to roll back. Source-side backup outside repository is recorded in handoff_backup_path.json; use this workspace packet, not the backup path, in a continuation. No new chat or source archival was performed.
'''
(O/'HANDOFF.md').write_text(handoff,encoding='utf-8')
backup=Path(r'C:\Users\Ayong\.codex\visualizations\2026\10\29\01a187f9-62cf-7710-94f5-b14c888b3237')/('ptfr-qr2-handoff-'+str(uuid.uuid4())+'.md')
assert backup.parent.is_dir();backup.write_text(handoff,encoding='utf-8')
write(O/'handoff_backup_path.json',{'path':str(backup),'scope':'Source-side recoverable packet; no new chat created'})
py=[]
for p in O.rglob('*.py'):
 ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));py.append(str(p))
files=[p for p in O.rglob('*') if p.is_file()]
write(O/'EVIDENCE.json',{'status':'PASS_BOUNDED_QR2_DELIVERY','overall_161_quest_task':'INCOMPLETE','investigated_quests':3,'new_contract_findings':30,'contract_status_counts':cp['contract_status_counts'],'static_verified':0,'gameplay_repairs':0,'package_created':False,'protected_hashes':read(O/'protection_after.json')['hashes_verified'],'tested_artifacts':{n:{'path':str(p),'sha256':sha(p)} for n,p in tested.items()},'python_syntax_checked':py,'artifacts':{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files},'scope':'Verified static per-quest findings with explicit unresolved/live boundaries; no universal gameplay or save-transition success claim'})
print({'status':'PASS_BOUNDED_QR2_DELIVERY','artifacts':len(files),'python_files':len(py),'handoff_characters':len(handoff)})
