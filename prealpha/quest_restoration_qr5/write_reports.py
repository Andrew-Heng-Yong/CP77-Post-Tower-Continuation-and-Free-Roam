"""Render concise final report and exact next-session handoff from verified state."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
c=read(O/'checkpoint.json');q=read(O/'queue.json');defs=read(O/'defects_and_repairs.json');pro=read(O/'protection_after.json');C=Path(q['working_candidate']);m=read(C/'package_manifest.json');e=read(q['source_epoch_manifest'])
assert pro['status']=='PASS';assert q['package_verification'].startswith('PASS')
new=defs['defects'][-defs['new_confirmed_unique_defects']:]
def summary(d):return d.get('status','UNKNOWN').replace('_',' ')
lines=['# QR5 — source verification and staged repair report','',f"Completed **{c['new_deep']} new deep investigations**, bringing the total to **{c['deep_total']}/{c['selected']}**. Primary coverage: {c['primary']['reviewed']}/{c['primary']['required']}; stretch: {c['stretch']['reviewed']}/{c['stretch']['required']}. {c['remaining']} selected quests remain for the next session.",'',f"Every new quest has ten source-specific dispositions and independent actual-resource review. **{c['fully_static_verified']} quests have all ten contracts statically resolved**. Deep reviewed does not mean fully restored or proven playable.",'','## Confirmed defects and dispositions','',f"{defs['new_confirmed_unique_defects']} new unique defects affecting {defs['new_affected_quest_count']} quests: {defs['new_repaired_unique_defects']} repaired in staged resources; {defs['new_blocked_unique_defects']} explicitly blocked. Prior QR3/QR4 corrections remain preserved.",'','| Defect | Affected quest | Disposition |','| --- | --- | --- |']
for d in new:lines.append('| '+d['id']+' | '+', '.join(d['affected'])+' | '+summary(d)+' |')
lines += ['','Repair evidence, exact before/after hashes, source proposals, independent reviews and limits are in [the ledger](defects_and_repairs.json), [allowlist](approved_changes_04.json) [primary repair adjudication](adjudications/repairs_01.json) and [MovingHeat adjudication](adjudications/moving_heat_01.json). Original defective resources and frozen findings remain available.','',
'The five packaged QR5 changes restore native ARR12 failure monitoring, Steven’s future U9 actor consumer, Cheetah’s fallback monitor, NID02’s van-failure monitor and MovingHeat’s dedicated accepted-body prefab lease. They preserve native callbacks, joins, journal/reward/cleanup payloads and saved identities. Only future attachment edges gain support; already executing child descendants are unchanged. A claimed MovingHeat owner still pending before9.True can use the new wrapper if its late guards pass.','',
'CVI02’s alternate EP1 Hands calls have real request producers but a retired specialized listener/outcome owner. Its three selected scene inputs are holo-only; metadata containing Johnny/physical Hands is not evidence of a visual failure. Existing FO1 can provide the required default-scene marker under earned conditions, but CVI02 does not prove that lease. Safe independent marker acquisition and saved-owner arbitration remain blocked. See [independent context review](groups/G11/reviews/CVI02_EP1/verification_03/review.json).','',
'A second blocked family affects Ronald’s optional news after Dogtown Saints, Jason Foreman, Spy in the Jungle and Treating Symptoms. Main gig/call/reward proofs remain valid. Native controller11 is retired; B0 restores services but omits news11/12. The native root owns the bar prefab and area-marker lease; SMS children require no physical actor, yet that marker support and shared pause/timer cleanup are not established by B0. Native sent1 precedes the two-game-day delay and cannot prove delivery. No unfiltered bar/controller clone, fake receipt or timer reset is approved. [Four-quest family adjudication](adjudications/ronald_01.json) and [independent context review](groups/G21/reviews/RONALD/verification_05/review.json) retain exact routes and units.','',
'## Validation and source identity','',f"Canonical candidate: `{C.relative_to(W)}`; epoch `{e['epoch_key']}`. Package has {m['paths']} stable paths and {m['readback_payloads']} payloads; {len(m['changed_resources'])} payloads differ from QR4. All others, XL registrations and 46 managed REDS files remain identical. Independent readback verifies every packed payload and ZIP member.",'',f"- Archive SHA256: `{m['archive_sha256']}`\n- ZIP SHA256: `{m['zip_sha256']}`\n- Canonical source epoch SHA256: `{sha(q['source_epoch_manifest'])}`",'',
'Root repair checks: 324 assertion events and 17 mutations of actual readback documents. Independently implemented serialized checks: 513 assertion events and 30 raw-document mutations. These are fault-detection controls, not unique gameplay coverage. The independent final package review checks all packed keys, bytes, ZIP members, unchanged files, prior repairs, compile-input equality and canonical epoch08 linkage. Metadata-only scope corrections are explicit and do not change package bytes. See [independent package review](groups/G21/reviews/QR5candidate03/verification_01/REPORT.json).','',
'Compilation was reused only after exact equality of 131 source files, 134 compiler/cache input pins and 46 packaged managed sources. No new SCC invocation or unchanged-baseline rebuild was performed. [Compile reuse](compile_reuse_03.json) records the boundary.','',
'The main stock TDB capture is bounded: 1,200 records, 1,197 found, three missing direct targets and 1,469 uncaptured immediate descendants. A separate one-record depth0 supplement resolves the exact native MovingHeat vehicle alias; its child references remain open. These are source definitions, not runtime merged winners or executed rewards. Exact per-quest applicability is in the [shared registry](shared_evidence_registry.json). DynamicBaseClass/worldNode placement and engine scene/lease semantics remain opaque where recorded.','',
'Independent review corrected the outgoing Padre call description, WWD05 Embedded-versus-Soft donor envelope, Cheetah XOR-versus-AND shorthand, Hasan’s timer arithmetic (88 game hours), the flattened-fact false tier-cohort restriction, and inherited source-epoch prose. Originals and failed verifier attempts are retained; source-specific supersessions are indexed in [review issues](review_issues.json), [adjudications](adjudications/) and [group evidence](group_evidence_index.json).','',
'[Coverage JSON](coverage.json), [161-quest matrix](quest_status_matrix.csv), [1,610-contract matrix](contract_status_matrix.csv) and [queue](queue.json) retain FAIL, CONDITIONAL, OPAQUE, UNKNOWN and live-only limitations. The bounded [phone-family census](phone_family_census_02/inventory.json) covers 47 primary evidence schemas plus a separately reviewed Steven case; name matching is not exhaustive semantic or live-owner proof.','',
'## Preservation and remaining limits','',f"Protected-file verification passed for **{pro['hashes_verified']} hashes**. Entire game/save filename, size and modification-time snapshots have no differences. No game launch, deployment, save/fact change, release update or Git publication occurred. PH3 remains installed. [Preservation evidence](protection_after.json).",'',
'Native topology, input equality and static reachability do not certify phone scheduling, interruption, timers/reloads, streamed actor/workspot/camera behavior, effective external TDB overrides, rewards or future-version save transitions. Unresolved prior MQ007 saved states, Brendan earned-history admission, Delamain parent evidence and native timing/context discrepancies remain unchanged.','',
'Continue from [HANDOFF.md](HANDOFF.md); do not repeat QR1’s census/compile/reproduction or rebuild the unchanged QR4/PH3 baseline.']
assert not (O/'REPORT.md').exists();(O/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
remaining='\n'.join('- `'+x['id']+'` — '+x['title']for x in c['next_batch_quests'])
handoff=f'''# QR6 continuation handoff

Continue the same 161-quest restoration project. Read root/prealpha AGENTS.md, this file, `checkpoint.json`, `queue.json`, `REPORT.md`, `defects_and_repairs.json`, `shared_evidence_registry.json` and relevant knowledge procedures.

## Verified checkpoint

- {c['deep_total']}/161 deeply reviewed; {c['remaining']} remain. QR5 added {c['new_deep']} real investigations, all independently reviewed. All ten contracts remain source-specific; {c['fully_static_verified']} quests have all ten statically resolved.
- Staged source: `{C.relative_to(W)}`. Canonical epoch: `{Path(q['source_epoch_manifest']).name}`, SHA256 `{sha(q['source_epoch_manifest'])}`.
- Archive `{m['archive_sha256']}`; ZIP `{m['zip_sha256']}`. {m['readback_payloads']} payloads, 51 paths. Installed PH3 is unchanged; nothing deployed or launched.
- {defs['cumulative_staged_repairs']} cumulative staged repairs: preserve MQ037 containment, MQ030 retirement/lease ordering, both MQ007 continuation wrappers, and the five QR5 repairs. Exact source/serialized/package evidence is in the allowlist and ledger.
- {defs['new_blocked_unique_defects']} new repair blockers remain; read each ledger entry and independent review. CVI02’s marker provider exists conditionally; neither blanket marker absence nor Johnny visual failure is established.
- Ronald optional-news family affects `sts_ep1_01`, `sts_ep1_03`, `sts_ep1_08`, `sts_ep1_12`: eight communications/shared FAIL dispositions, one unique defect. Native whole tree owns bar area markers; B0 service-only copy has no matching bar lease. SMS children have no physical scene requirement. Shared pause/cancellation/rearm and old sent-before-timer state need an exact isolated adapter; no proposal is approved. Native preclaim real-time pauses differ from the two-game-day delays (Spy112=1second then115=2days; Saints114=3seconds then119=2days).

## Next exact batch: {c['next_batch']}

{remaining}

`checkpoint.json.next_all_unreviewed` contains the complete ordered remainder. Reuse the three-worker pool pattern with independent rotation and coordinator-only integration; do not create one worker per quest.

## Start and evidence boundary

1. Verify workspace, branch/HEAD and exact canonical epoch/manifest/source hashes. Read `sentinel.json`, `source_epoch_identity.json` and current `source_epoch_*.json`; QR5:00 pins QR4:03 and is a distinct local epoch namespace.
2. Check package/epoch linkage and prior repair hashes; reuse existing complete-input compilation and whole-package reproduction while exact inputs remain unchanged. Do not rebuild PH3/QR4 or recreate a baseline ZIP.
3. Investigate the next jobs against actual pinned native/effective resources. Cover every ten-contract route, all request families/directions, actor/PIP ancestor ownership, journals, rewards, cleanup, history and saved owners. Static unknowns need exact missing evidence; do not manufacture a PASS or speculative fix.
4. New source-confirmed defects need a failing-before control, smallest compatible proposal, independent source review, serialized readback/mutations, explicit resource allowlist, fresh successor and independent final package preservation. No shared candidate edits by workers.

## Important carry-forward details

- Native scalar missing facts read zero; positive receipts/events supply provenance. Missing journals do not prove Inactive history.
- Generic `holo_`/`audio_` checks missed CVI02's `new_sts_*`/`new_q110` branch. Trace custom requests and real callbacks plus executing listener/support owner. No synthetic ACKs, counter resets or force-open workarounds.
- Keep exact native XOR/AND types and recursive connections. Cheetah17 is XOR;24 is AND. ARR12 uses terminating descendants32, not the earlier rejected cut interpretation.
- Steven’s actor-only helper is inside the Spy entry carrier, with ordered initial enrollment and late Ana0/history fences. Original S23 owner, timer, SMS, reward and excluded stadium route are preserved.
- Hasan timer is3days16hours=88gamehours; explicit correction preserves the old erroneous84h report label. WWD05 parent12 is Embedded with three body comparisons; CVI02 parent3 is Soft.
- `source_epoch_08.json` is a metadata-only correction of epoch07 inherited source-stage package-pending prose. Same1574source/51package bytes. Package manifest's `new_unique_defects=5` describes packaged repairs; full ledger has{defs['new_confirmed_unique_defects']} new confirmed defects including both blocked families. Epoch05 is the preserved earlier candidate02 metadata correction. Metadata notes record counts at their publication time; the final ledger is authoritative for later shared findings.
- Do not rerun `sync_progress_metadata.py`, old installers/builders, source-epoch publishers or candidate patch scripts. They are pinned one-shot evidence. `groups/G15/inspect.py` has top-level effects and shadows stdlib inspect; never import it.
- Do not retry rejected Delamain admission or synthetic Sandra/Delamain resets. Do not admit excluded content or invent pre-Tower evidence. Preserve unresolved prior saved-state/timing policies.

## Reproducible focused rechecks

Use `C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B`. Each command requires a fresh output directory; inspect top-level effects before running other scripts.

```powershell
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr5/check_bounded_monitors.py --output diagnostics/qr6_recheck_NEW/monitors
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr5/check_steven_actor.py --output diagnostics/qr6_recheck_NEW/steven
& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr5/check_moving_heat.py --output diagnostics/qr6_recheck_NEW/moving_heat
```

Expected:126checks/6raw mutations,91checks/2raw mutations and49checks/5raw mutations, respectively, using actual pinned readbacks/binaries. They do not certify gameplay or old-owner adoption. Do not rerun these unaffected checks solely for ceremony.

## Scope and restrictions

Current deliverables are staged only. No game/deployment/save/fact/published-release/Git publication permission follows from this handoff. Obtain current user scope before new runtime work. Preserve all candidates, original failures and independent reviews. File rollback is not save rollback.
'''
assert not (O/'HANDOFF.md').exists();(O/'HANDOFF.md').write_text(handoff,encoding='utf-8')
c['remaining_final_gates']='NONE_WITHIN_QR5_STATIC_SCOPE';c['preservation_result_sha256']=sha(O/'protection_after.json');c['report_sha256']=sha(O/'REPORT.md');c['handoff_sha256']=sha(O/'HANDOFF.md');write(O/'checkpoint.json',c)
p=read(O/'progress.json');p['status']='QR5_COMPLETE_STATIC_SCOPE_WITH_EXPLICIT_BLOCKERS_AND_LIVE_LIMITS';write(O/'progress.json',p)
print({'report':str(O/'REPORT.md'),'handoff':str(O/'HANDOFF.md'),'deep':c['deep_total'],'remaining':c['remaining']})
