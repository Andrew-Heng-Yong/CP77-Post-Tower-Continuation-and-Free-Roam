"""Publish reconciled source inventories/reports, before independent completeness QA."""
from pathlib import Path
import sys,collections,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
assert not(O/'REPORT.md').exists(),'Fresh report publication only'
q=read(O/'queue.json');cov=read(O/'coverage.json');p=read(O/'progress.json');defs=read(O/'defects_and_repairs.json');ep=read(O/'source_epoch_00.json');pr=read(O/'verification/preservation_01/result.json')
assert cov['deep_total']==len(q['quests'])and not cov['remaining']and all(g['status']=='REVIEWED_WITH_LIMITS'for g in p['groups'].values())
findings=[]
for x in q['quests']:
 for stage,v in x['contracts'].items():
  if v['status']not in ['FAIL','UNKNOWN']:continue
  family='CVI02_ALTERNATE_HANDS'if x['id']=='sts_pac_cvi_02'else'RONALD_POST_GIG_NEWS'if v['status']=='FAIL'else'MQ060_NATIVE_SOURCE_AUTHORITY'if x['id']=='mq060_nitro'else'CAREER_EARLY_NOTIFICATION_HISTORY'if x['id']=='mws_wat_08_trauma_drama'else'RETAINED_STATIC_UNKNOWN'
  findings.append({'priority':'HIGH'if family=='CVI02_ALTERNATE_HANDS'else'MEDIUM','classification':'CONFIRMED_DEFECT_REPAIR_BLOCKED'if v['status']=='FAIL'else'UNRESOLVED_STATIC_PROPERTY_NOT_CONFIRMED_GAMEPLAY_DEFECT','family':family,'quest_id':x['id'],'title':x['title'],'stage':stage,'status':v['status'],'proven':v['proven'],'missing_evidence':v.get('remaining',[]),'source_evidence':v['evidence'],'findings_source':v.get('findings_source'),'findings_source_sha256':v.get('findings_source_sha256'),'independent_review':v.get('independent_review'),'effective_source_epoch':v.get('effective_source_epoch')})
findings.sort(key=lambda x:(x['priority']!='HIGH',x['classification']!='CONFIRMED_DEFECT_REPAIR_BLOCKED',x['quest_id'],x['stage']))
write(O/'prioritized_discrepancies.json',{'scope':'Confirmed blocked defects and exact UNKNOWN properties. OPAQUE/CONDITIONAL records remain fully visible in complete matrices; they are not silently passed or called confirmed bugs.','rows':findings});csvwrite(O/'prioritized_discrepancies.csv',findings)
inventory=[];input_pins={};missing=[];seen=set();hashcache={}
def pin(f):
 f=str(Path(f).resolve())
 if f not in hashcache:hashcache[f]=sha(f)
 return hashcache[f]
for gid,g in p['groups'].items():
 result=read(g['result']);paths=result.get('source_pin_paths',result.get('source_pins_paths',[]))
 for sp in paths:
  input_pins[sp]=pin(sp);d=read(sp);rows=d if isinstance(d,list)else d.get('resources',d.get('sources',[]))
  for r in rows:
   if not isinstance(r,dict)or not r.get('depot'):continue
   raw=r.get('binary',r.get('raw'));h=r.get('sha256',r.get('raw_sha256',r.get('resource_sha256')));jp=r.get('json');jh=r.get('json_sha256')
   if not raw or not h:
    missing.append({'group':gid,'input_manifest':sp,'depot_or_alias':r['depot'],'reason':'Nonstandard pin schema; exact original record retained','record':r});continue
   assert pin(raw)==h,(raw,h)
   if jp and jh:assert pin(jp)==jh,jp
   key=(gid,r['depot'],str(raw),h,jp,jh)
   if key in seen:continue
   seen.add(key);inventory.append({'group':gid,'group_quest_ids':g['ids'],'depot_or_recipe_alias':r['depot'],'binary':raw,'resource_sha256':h,'json':jp,'json_sha256':jh,'provider':r.get('provider'),'input_manifest':sp,'input_manifest_sha256':input_pins[sp],'scope':'Group input observation; exact per-quest executing-route relevance is in original contract and handler evidence, not inferred from membership.'})
 for fn in ['missing_inputs.json','inspection_01/missing.json']:
  fp=O/'groups'/gid/fn
  if fp.is_file():missing.append({'group':gid,'historical_input_limits_manifest':str(fp),'sha256':pin(fp),'scope':'Initial capture/search limits, not automatically all unresolved final quest contracts. Consult exact final contract findings/supplements.'})
write(O/'source_resource_inventory.json',{'scope':'Pinned resource inputs used by nineQR6groups; aliases/overlap retained. This is not a whole-game dependency closure, actor-placement audit or unique gameplay coverage count.','observations':inventory,'input_manifest_pins':input_pins,'explicit_input_limits':missing,'unique_depot_or_alias_and_hash_pairs':len({(r['depot_or_recipe_alias'],r['resource_sha256'])for r in inventory})});csvwrite(O/'source_resource_inventory.csv',inventory)
count=cov['all_contract_status_counts'];new=cov['new_contract_status_counts'];table='\n'.join('| '+s+' | '+str(count.get(s,0))+' | '+str(new.get(s,0))+' |'for s in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY'])
gt=[];checks=mut=peerchecks=peermut=0
for gid,g in p['groups'].items():
 d=read(g['result']);rv=read(g['review']['path']);checks+=d['total_checks'];mut+=d['mutations'];peerchecks+=rv['checks'];pm=rv.get('mutations',rv.get('raw_mutations',rv.get('raw_document_mutations',0)));peermut+=pm
 gt.append(f"| {gid} | {len(g['ids'])} | {d['total_checks']} / {d['mutations']} | {rv['checks']} / {pm} |")
report=f'''# QR6 — final whitelist source-verification report

Completed **33/33 new deep investigations**, bringing cumulative coverage to **161/161 selected quests** and **1,610 unique ten-contract records**. All nine QR6 groups received independent actual-resource review. The previous128 investigations and their original provenance were retained, not claimed as33new investigations or freshly replayed gameplay.

**Zero quests are fully STATIC_VERIFIED.**524contracts have PASS or APPROVED_DEVIATION dispositions;1,086remain conditional, opaque, unknown or failed. These are measured source-verification dispositions, not a gameplay-success percentage.

| Contract disposition | All161quests | New33quests |
| --- | ---: | ---: |
{table}

The [complete quest matrix](quest_status_matrix.csv), [ten-contract matrix](contract_status_matrix.csv), [coverage JSON](coverage.json), [quest queue](queue.json) and [group evidence index](group_evidence_index.json) preserve every exact disposition, source/finding/peer hash and supporting graph evidence. [Source resource inventory](source_resource_inventory.json) indexes input aliases and explicit limits; group membership is not executing-owner proof.

## Defects, unresolved evidence and repair decisions

**No new gameplay defect was confirmed and no new repair was justified in QR6.** All eight prior staged repairs/containments across nine resources remain byte-identical. The two confirmed QR5 failure families remain blocked, with all13FAILrecords visible. No newcandidate or ZIP was created.

| Priority | Finding | Exact result and missing evidence |
| --- | --- | --- |
| High | CVI02 alternate EP1 Hands controller | Five FAILcontracts remain. Native specialized listener/outcome owner is retired; generic Hands does not substitute. Exact FO1 scene-marker path is identified, but independent marker acquisition and native/FO1/saved-owner arbitration are not proved. Four abstract default-state models show only gate non-implication, not a reachable genuine save or absent marker. Selected scene inputs remain holo-only. |
| Medium | Ronald optional post-gig news | Eight FAILcontracts across Saints, Jason Foreman, Spy and Treating Symptoms remain. Current B0 omits native news11/12, lacks the reviewed native bar lease, and copied subscription writer1755 is unreachable from all seven scene inputs; first lost native route edge839:0:4→1451:0:0. Native sent1 precedes the2game-day clock and cannot prove delivery. Scoped marker ownership, pause/cancel/rearm and old-timer arbitration remain unresolved; no unfiltered bar or synthetic enrollment is approved. |
| Investigate | Nitro native entry authority | Three UNKNOWNcontracts. Current/native standalone four-Kusanagi parent conflicts with reachable global three-Kusanagi OR plus carbought_counter>=3 AND gate to the same body.47of80bounded fixtures differ. No captured reverse-reference is not proof the native .quest cannot start through an engine registry. The stricter intersection would suppress a native-authored Tyger route; no patch is approved. |
| Investigate | Career Opportunities notification history | One new UNKNOWNpersistence contract. Native congratulatory message states7/56 may precede first-place admission while rootInactive/started0. Exact journal reactivation idempotence and saved early-owner evidence are missing. No duplicate notification/reward is asserted; no receipt/reset is introduced. |

Four earlier UNKNOWNrecords remain unchanged: Arroyo courier/shared dependency and Voodoo Treasure eligibility, container injection/loot history and persistence. All162OPAQUE and903CONDITIONALrecords remain in the matrix. Static world-placement, effective external TweakDB winners, saved-owner liveness, scheduling, interruption, timers/reload and receipt behavior are not certified.

[Prioritized machine-readable discrepancies](prioritized_discrepancies.json), [defect/repair ledger](defects_and_repairs.json), [repair queue](repair_queue.json), [MQ060 adjudication](adjudications/MQ060_source_authority_01.json), [CVI02 follow-up](groups/C03/CVI02_context_01/evidence.json), [Ronald follow-up](blockers/ronald_01/evidence.json) and [independent Ronald review](groups/A03/reviews/RONALD/verification_01/review.json) retain exact paths, hashes, predicates, callbacks and limits.

## Source-specific verification and independent controls

The33investigations produced **{checks}assertion events/{mut}raw-document mutation controls**. Nine independently implemented peer reviews produced **{peerchecks}events/{peermut}controls**. Counts reuse shared inputs/properties and are not unique gameplay coverage. Mutants alter actual readback documents/conditions in fresh outputs, not resource binaries or the game.

| Group | Quests | Investigation checks / mutants | Independent checks / mutants |
| --- | ---: | ---: | ---: |
{chr(10).join(gt)}

Investigations trace actual entry sockets and predicates, both phone directions/custom callbacks, original retirement and saved owners, whole/nested graphs, ancestor root/instance prefabs, actors/scenes/workspots, journals, rewards and cleanup. Examples include exact Raymond/MQ028/MQ018 partial-state deferrals; native Nix service release; documented CC1/JC1/SC1/SR1 coaster adaptations; Stout2197farewell excluding unreachable Meredith3300 and its no-output limit; three Sinnerman journals sharing one native chain; and Delamain's exact post-scan body without Epistrophy/scan-reward replay. Current Rachel/Delamain cleanup aliases were verified against their real current IDs, not substituted native node numbers. Failed verifier attempts and corrections are preserved.

The bounded shared reward supplement resolves four exact new targets and15related stock definitions (19total, depth2), with20next-depth references still uncaptured. Base/EP1direct fields agree. An independent20check addendum binds the exact native nodes. CareerXP is separate from outfit/toy grants; Pony's currency package is separate from vehicle entitlement; SpaceOddity's empty briefcase reward fields are native. No status was promoted from stock-definition presence. See [shared registry](shared_evidence_registry.json) and [applicability](groups/B02/reward_applicability_01/addendum.json).

## Exact candidate, compilation and preservation

Canonical QR6source is **QR6:00**, SHA256`{sha(O/'source_epoch_00.json')}`, byte-identical to QR5:08/candidate03. All1,574payloads,51managed paths, ArchiveXL registrations,46managed REDS and nine inherited repaired resources were independently hashed/read back; ZIP CRCs and every member SHA agree. Independent package/compile review: **2,019checks, zero failures**. [Review](groups/C01/reviews/QR6_final_package/verification_02/review.json).

- Archive SHA256:`{ep['archive_sha256']}`.
- Existing staged ZIP SHA256:`{ep['zip_sha256']}`.
- Installed baseline remainsPH3; all51installed paths plus required Atelier bytes match their installation evidence.

All131source bytes remain unchanged. A preexisting compiler timestamp differed from QR5, so one fresh **offline131-source SCC compilation** was performed using134exact compiler/source/cache input pins; it passed, and the final independent review remapped every staged source to current input bytes. Compiler output:`34D753E0343A55BB2B6C797AD5CD5FB95B992C3D0EF457C13F21694D0EFB29E9`. No installed cache was written. [Compile](verification/compile_01/result.json).

Preservation passed for **{pr['protected_sha256_files']}protected SHA256files**, all855game and307save filenames/sizes/mtimes, and all134current compile inputs: zero discrepancies. Branch/HEAD and preexisting tracked diff are unchanged. Five files already differed from the historical QR5 snapshot at session start (compiler timestamp and four save files); their current bytes were pinned and preserved. This is protected-file SHA plus complete tree metadata, not a SHA of every unlisted game byte. [Preservation](verification/preservation_01/result.json), [preexisting drift](external_drift_since_QR5.json).

No game launch, deployment, save/fact edit, installed-mod write, published-release change, whitelist expansion or Git publication occurred. Previous regression evidence is retained by exact unchanged resource identity; no unchanged-baseline package/build was recreated.

The separate final completeness review is pinned by [completion.json](completion.json), written only after that independent gate. Continue from [HANDOFF.md](HANDOFF.md). [Static hardening](HARDENING_PLAN.md) and [in-game validation](INGAME_VALIDATION_PLAN.md) are future plans; no gameplay behavior was certified.
'''
(O/'REPORT.md').write_text(report,encoding='utf-8')
handoff=f'''# After QR6 — complete whitelist coverage, bounded static findings

Read root/prealpha AGENTS.md, `completion.json`, `REPORT.md`, `checkpoint.json`, `coverage.json`, `defects_and_repairs.json`, `repair_queue.json` and `shared_evidence_registry.json`. Select relevant knowledge procedures; do not reread the entire diary or begin another generic catalogue audit.

Primary coverage is complete:161/161deeply investigated; QR6added33, all independently reviewed,1,610unique contracts. **No remaining Q09/Q10/Q11 quest queue exists.** Zero quests are fully STATIC_VERIFIED. All statuses remain visible:349PASS,175approved deviations,903conditional,162opaque,13FAIL,8UNKNOWN. Source verification is not gameplay success.

## Exact current artifacts

- Staged runtime candidate: `prealpha/quest_restoration_qr5/candidate_03`; no newQR6candidate/ZIP or runtime edit.
- Canonical QR6epoch: `source_epoch_00.json`, SHA256`{sha(O/'source_epoch_00.json')}`; predecessor QR5:08 SHA`B8BC8D6630F51E07125789FAB5A54D188EB45CE7044F35E2E6F09DE460B91D83`.
- Archive SHA`{ep['archive_sha256']}`; existing ZIP SHA`{ep['zip_sha256']}`.
- All1,574payloads/51package paths/46managed REDS/XL unchanged. Preserve eight staged repairs/containments across nine resources. InstalledPH3 remains distinct and unchanged.
- `approved_changes_00.json` has an emptyQR6delta and exact inherited resource pins. Independent package/compile gate: `groups/C01/reviews/QR6_final_package/verification_02/review.json`,2,019checks.
- Fresh offline current-input SCC PASS: `verification/compile_01/result.json`;131sources/134pins/46managed. Only preexisting compiler timestamp changed sinceQR5; all source bytes match. Do not falsely reuse old134pin equality or rerun unchanged compilation merely for ceremony.
- Current-session preservation: `verification/preservation_01/result.json`,13,475protected hashes plus full game/save metadata, zero discrepancies. `external_drift_since_QR5.json` explains five preexisting changes; never restore the user's older saves to match an old snapshot.

## Remaining evidence priorities

1. CVI02 alternate Hands: five failed contracts, exact specialized listeners/real outcomes, FO1default marker path known. Independent marker acquisition and shared/native/saved-owner arbitration remain blocked. Abstract gate countermodels are not reachable histories or absent-marker evidence; no default/PIP clone or fakeACK approved.
2. Ronald optional news after Saints/Jason/Spy/Symptoms: eight failed contracts, original news11/12missing underB0, copied subscription1755unreachable from all inputs, native sent1before2game days. Need exact scopedbar markers and future/sharedqueue/cancel/rearm/savedtimer arbitration. No wholebar/fluff replay, sent/timer reset or fabricated enrollment.
3. MQ060: three UNKNOWNcontracts, conflicting native standalone/global parents. Exact startupregistry authority or dated policy is missing.47/80boundedmodels differ; conservative intersection would suppress authoredTyger-onlyroute. No patch approved.
4. Career: saved early congratulations7/56 history/idempotence UNKNOWN. No duplicate notification/reward established; no receipt/reset approved. Preserve four prior UNKNOWNrecords and all opaque/conditional limits.
5. Shared definitions:19record depth2supplement closes four exact reward IDs;20next-depthrefs and effective overrides remain open. Existing stock1200capture and MovingHeat alias supplement retain separate bounds. No reward/vehicle/receipt or world-placement certification from definitions alone.

Use `HARDENING_PLAN.md` and the separate `INGAME_VALIDATION_PLAN.md` only under a fresh user's chosen scope. There is no authorization to deploy, launch, modify saves/facts, expand whitelist or publish. File rollback is not save rollback. Do not retry Delamain admission or Sandra/Delamain counter resets.

## Reproduction and immutable evidence

`README.md` names exact supported fresh-output checks. Reuse source-specific findings and peer pins via `group_evidence_index.json`; old128contracts retain their original source/epoch/review. Source and peer mutation controls operate on actual readback documents, not game binaries. Source-resource inventory membership is not executing-owner proof.

Do not rerun QR6initializers, target publishers, `record_group.py`, `seal_ledger.py`, `finalize.py` or `publish_reports.py`; they are one-shot evidence/pointer operations. Do not rerun pinned QR5builders/patchers/finalizers/packagers, stale `sync_progress_metadata.py`, or import `groups/G15/inspect.py`. Preserve failed checker attempts and all baseline evidence. No newunchangedZIP is needed.

The last deliverable `completion.json` pins the final independent completeness review and frozen final artifacts without circular self-hashes. Read it before interpreting an earlier working-checkpoint state. No new chat/archive/cleanup was authorized.
'''
(O/'HANDOFF.md').write_text(handoff,encoding='utf-8')
cp=read(O/'checkpoint.json');cp.update(state='QR6_ALL161_SOURCE_PEER_PACKAGE_PRESERVATION_FROZEN_FINAL_COMPLETENESS_GATE_EXTERNAL',remaining_final_gates=['Independent final161/1610completeness review','Post-review completion.json seal'],independent_package_review=q['independent_package_review'],preservation=q['preservation'],report=str(O/'REPORT.md'),report_sha256=sha(O/'REPORT.md'),handoff=str(O/'HANDOFF.md'),handoff_sha256=sha(O/'HANDOFF.md'));write(O/'checkpoint.json',cp)
p.update(status='QR6_FROZEN_FINAL_INDEPENDENT_COMPLETENESS_GATE_PENDING');write(O/'progress.json',p)
write(O/'publication_01.json',{'status':'FROZEN_FOR_INDEPENDENT_COMPLETENESS_REVIEW','report_sha256':sha(O/'REPORT.md'),'handoff_sha256':sha(O/'HANDOFF.md'),'queue_sha256':sha(O/'queue.json'),'coverage_sha256':sha(O/'coverage.json'),'checkpoint_sha256':sha(O/'checkpoint.json'),'source_inventory_observations':len(inventory),'source_inventory_limits':len(missing),'discrepancy_rows':len(findings),'investigation_assertion_events':checks,'investigation_raw_document_mutants':mut,'peer_assertion_events':peerchecks,'peer_raw_document_mutants':peermut,'limits':'Event counts overlap and are not unique gameplay/semantic coverage; final completeness review and completion seal follow separately.'})
print({'status':'FROZEN_REPORTS_AND_INVENTORIES','quest_rows':len(q['quests']),'source_observations':len(inventory),'priority_rows':len(findings),'investigation_events':checks,'peer_events':peerchecks})
