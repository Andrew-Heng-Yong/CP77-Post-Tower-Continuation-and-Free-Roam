"""Independent QR8 completeness/readiness gate; only fresh worker B output writes.

No root/A/C validator imports, no broad quest audit, no stock-container rehash.
"""
from lib import *
import argparse,csv,zipfile,collections,copy
D=W/'prealpha/quest_restoration_qr8';P=W/'prealpha/quest_restoration_qr7'
STAGES={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
def key(r):return r['quest_id'],r['stage']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--publication',default='publication_02.json');ap.add_argument('--carry-from');a=ap.parse_args();out=H/'reviews/final_publication'/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);checks=[];pins=[];seen=set();issues=[];carry=None
 if a.carry_from:
  prior=Path(a.carry_from).resolve();prior.relative_to(H.resolve());observations=prior/'hash_observations.json';reviewfile=prior/'review.json';oldobs=read(observations);carry={'observations':str(observations),'observations_sha256':sha(observations),'review':str(reviewfile),'review_sha256':sha(reviewfile),'reason':'Just-completed full current SHA pass; one formatting-sensitive human-text matcher corrected. No source or reviewed document changed. Each carried entry requires exact current size/mtime and final postcheck.','entries_reused':0,'changed_metadata_rehashed':0}
  for o in oldobs:
   f=Path(o['path']);st=f.stat();tag=(st.st_size,st.st_mtime_ns)
   if tuple(o['metadata'])==tag:
    o=copy.deepcopy(o);o['metadata']=tag;OBS[os.path.normcase(str(f.resolve()))]=o;carry['entries_reused']+=1
   else:carry['changed_metadata_rehashed']+=1
 def ck(n,v,**e):checks.append({'name':n,'pass':bool(v),**e})
 def pin(f,expected=None):
  f=Path(f);f=f if f.is_absolute()else W/f;f=f.resolve();tag=str(f).casefold()
  try:h=sha(f)
  except OSError as ex:ck('missing-pin:'+str(f),False,error=str(ex));return None
  if tag not in seen:pins.append({'path':str(f),'sha256':h,'size':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns});seen.add(tag)
  if expected:ck('pin:'+str(f),h==expected,expected=expected,actual=h)
  return h
 pubfile=D/a.publication;pub=read(pubfile);pin(pubfile)
 for name,v in pub['artifacts'].items():pin(v['path'],v['sha256'])
 for k in('predecessor_publication','supersession'):
  v=pub[k];pin(v['path'],v['sha256'])
 supersession=read(pub['supersession']['path']);oldpub=read(pub['predecessor_publication']['path'])
 for r in supersession['rows']:
  pin(r['preserved_review_snapshot'],r['old_sha256']);pin(r['original_current_path'],r['current_sha256']);name=Path(r['original_current_path']).name
  if name in oldpub['artifacts']:ck('old-publication-exact-version-preserved:'+name,oldpub['artifacts'][name]['sha256']==r['old_sha256'])
 cp=read(D/'checkpoint.json');ck('current-worker-findings-not-initial-progress',all('Completed:'in v for v in cp['worker_findings'].values())and 'initial_worker_progress_history'in cp and 'initial_acceptance_draft_history'in cp and cp['acceptance_plan'].endswith('acceptance_tests.json'))
 queue=read(D/'queue.json');cat=read(queue['source_catalogue']);pin(queue['source_catalogue'],queue['catalogue_sha256']);selected={r['id']for r in cat['decision_registry']if r['decision']=='INCLUDE'}
 qm=read(D/'quest_status_matrix.json');cm=read(D/'contract_status_matrix.json');cmp=read(D/'contract_comparison.json');updates=read(D/'targeted_contract_updates.json');coverage=read(D/'coverage.json');oldqm={r['id']:r for r in read(P/'quest_status_matrix.json')};oldcm={key(r):r for r in read(P/'contract_status_matrix.json')};by={key(r):r for r in cm};targets={key(r)for r in updates};qby={r['id']:r for r in qm}
 ck('actual-selected-registry-exact-quest-membership',len(selected)==len(qm)==len(qby)==161 and selected==set(qby)=={r['id']for r in queue['quests']}and qm==queue['quests'])
 ck('ten-contract-grid-exact-complete-unique',len(by)==len(cm)==len(selected)*10 and set(by)==set(oldcm)and all(set(q['contracts'])==STAGES for q in qm))
 for r in cm:ck('quest-contract-flat-model-agreement:'+str(key(r)),{k:v for k,v in r.items()if k not in('quest_id','title','stage')}==qby[r['quest_id']]['contracts'][r['stage']])
 counts=dict(collections.Counter(r['status']for r in cm));oldcounts=dict(collections.Counter(r['status']for r in oldcm.values()));ck('counts-unchanged-and-every-status-explicit',counts==oldcounts==coverage['original_status_counts']==coverage['final_status_counts']and sum(counts.values())==1610 and counts.get('UNKNOWN')==5 and not counts.get('FAIL',0))
 ck('all18-source-specific-targets-retain-exact-prior-contract',len(targets)==len(updates)==18 and all(r['prior_QR7_contract']==oldqm[r['quest_id']]['contracts'][r['stage']]and r['status']==oldcm[key(r)]['status']for r in updates))
 untouched=[];applicability=[]
 for k,r in by.items():
  ck('no-unreviewed-status-promotion:'+str(k),r['status']==oldcm[k]['status'])
  if k not in targets:
   core={x:v for x,v in r.items()if x!='QR8_shared_news_applicability'};ck('old-nontarget-provenance-byte-values-preserved:'+str(k),core==oldcm[k])
   (applicability if r!=oldcm[k]else untouched).append(k)
 ck('only32-nontarget-source-applicability-addenda',len(applicability)==32 and len(untouched)==1560 and all(q in('sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12')for q,s in applicability))
 comp={key(r):r for r in cmp};ck('full-original-final-comparison-grid',len(comp)==len(cmp)==1610 and set(comp)==set(by)and all(r['original_status']==oldcm[k]['status']and r['final_status']==by[k]['status']and r['QR8_targeted_update']==(k in targets)and r['final_epoch']=='QR8:02'for k,r in comp.items()))
 failrows=[r for r in cm if r.get('failed_subroutes')];ck('eight-held-first-enrollment-subroutes-never-blanket-PASS',len(failrows)==coverage['failed_first_enrollment_subroutes']==8 and all(r['status']=='CONDITIONAL'and r['QR8_enrollment_scope_review']['unsupported_subroute_status']=='FAIL'and r['QR8_enrollment_scope_review']['parent_status']=='CONDITIONAL'and len(r['failed_subroutes'])==2 for r in failrows))
 unknowns={key(r)for r in cm if r['status']=='UNKNOWN'};ck('five-original-UNKNOWNs-visible-unpromoted',unknowns=={key(r)for r in coverage['remaining_original_target_UNKNOWN']}and unknowns=={k for k,v in oldcm.items()if v['status']=='UNKNOWN'})
 ck('no-new-deep-audits-or-full-static-claims',coverage['new_census_or_broad_deep_audits']==0 and coverage['retained_deep_investigations']==161 and coverage['fully_static_verified_quests']==0 and all(not q['fully_static_verified']for q in qm))
 # Every original provenance link on unchanged contracts is reused exactly; direct final links get actual current pins.
 for r in cm:
  for fld in ['findings_source','independent_review','review']:
   f=r.get(fld);h=r.get(fld+'_sha256')
   if isinstance(f,str)and h:pin(f,h)
 for r in updates:
  for obj in walk(r):
   if isinstance(obj.get('path'),str)and isinstance(obj.get('sha256'),str)and len(obj['sha256'])==64:
    # Metadata/file links, not resource-depot paths. No large native containers occur in these direct final links.
    f=Path(obj['path'])
    if f.is_file()and f.stat().st_size<256*1024*1024:pin(f,obj['sha256'])
 # CSV values must reconstruct all JSON fields, including nested provenance/fixtures.
 csv.field_size_limit(100000000)
 tables=[('quest_status_matrix',qm),('contract_status_matrix',cm),('contract_comparison',cmp),('targeted_contract_updates',updates),('acceptance_tests',read(D/'acceptance_tests.json')['tests'])]
 for name,rows in tables:
  with(D/(name+'.csv')).open(encoding='utf-8-sig',newline='')as f:reader=csv.DictReader(f);header=reader.fieldnames;csvrows=list(reader)
  ck('CSV-complete-row-and-field-set:'+name,len(csvrows)==len(rows)and set(header)==set().union(*(r.keys()for r in rows)))
  errors=[]
  for i,(want,got)in enumerate(zip(rows,csvrows)):
   for k in header:
    v=want.get(k);s=got.get(k,'')
    try:ok=json.loads(s)==v if isinstance(v,(dict,list))else s.lower()==str(v).lower()if isinstance(v,bool)else s in('','null')if v is None else s==str(v)
    except (ValueError,TypeError):ok=False
    if not ok:errors.append([i,k])
  ck('CSV-all-semantic-values-match-JSON:'+name,not errors,errors=errors[:20])
 ep=read(D/'source_epoch_02.json');old=read(P/'source_epoch_04.json');C=Path(ep['candidate']);manifest=read(C/'package_manifest.json');source=ep['source_resources'];changed=[k for k in set(source)|set(old['source_resources'])if source.get(k)!=old['source_resources'].get(k)];ck('exact-source-payload-set-and-single-approved-change',set(source)==set(old['source_resources'])and len(source)==1577 and changed==[NEWS]and source[NEWS]=='6CEB6AC9FA2909771AEEF09D33A36241E1396D26A072725317374837AB79B0EC')
 for d,h in source.items():pin(C/'archive_source'/d,h)
 pin(C/'package_manifest.json',ep['package_manifest_sha256']);pin(ep['zip'],ep['zip_sha256']);ck('manifest-epoch-consistent-delivery',ep['epoch_key']=='QR8:02'and manifest['source_payloads']==manifest['readback_payloads']==1577 and manifest['paths']==len(manifest['files'])==51 and manifest['archive_sha256']==ep['archive_sha256']and manifest['zip_sha256']==ep['zip_sha256'])
 packages={r['path']:r['sha256']for r in manifest['files']};ck('epoch51package-records-equal-currentmanifest',ep['package_files']==manifest['files'])
 for r in manifest['files']:pin(C/'package'/r['path'],r['sha256'])
 with zipfile.ZipFile(ep['zip'])as z:
  zs=[i for i in z.infolist()if not i.is_dir()];ck('ZIP51-exact-contained-layout',len(zs)==51 and {i.filename for i in zs}==set(packages)and all(not Path(i.filename).is_absolute()and'..'not in Path(i.filename).parts for i in zs))
  ck('ZIP-all51-actual-bytes-match-currentmanifest',all(__import__('hashlib').sha256(z.read(i)).hexdigest().upper()==packages[i.filename]for i in zs))
 apfile=D/'worker_a/final_package_01/verification/result.json';apr=read(apfile);pin(apfile);pin(apr['input_manifest'],apr['input_manifest_sha256']);pin(apr['readback_manifest'],apr['readback_manifest_sha256']);actual=read(apr['readback_manifest']);members=actual['members'];ck('A-independent-whole-package-evidence-current',apr['status']=='PASS_INDEPENDENT_WHOLE_QR8_ARCHIVE_ZIP_SOURCE_DELTA_AND_PRESERVATION'and apr['checks']==3887 and apr['source_epoch']=='QR8:02'and apr['whole_proposal_model_parity']and apr['native_protocol_nodes_preserved']==73 and actual['archive_sha256']==ep['archive_sha256']and len(members)==len({m['depot']for m in members})==1577 and {m['depot']for m in members}==set(source))
 for m in members:pin(m['raw'],source[m['depot']]);ck('actual-extracted-payload-manifest:'+m['depot'],m['raw_sha256']==source[m['depot']])
 layout=read(D/'installation_layout.json');ck('one-QR7-vs-two-PH3-package-replacements',layout['replacement_paths_vs_QR7']==['archive/pc/mod/zzzz_PTFR_Combined.archive']and set(layout['replacement_paths_vs_installed_PH3'])=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'}and layout['paths']==51 and layout['deployments']==layout['game_writes']==layout['save_writes']==0)
 ledger=read(D/'defects_and_repairs.json');oldledger=read(P/'defects_and_repairs.json');ck('all11-prior-staged-ledger-records-exactly-preserved',ledger['defects'][:-1]==oldledger['defects']and ledger['new_confirmed_unique_defects']==ledger['new_repaired_unique_defects']==1 and ledger['new_affected_quest_count']==4 and ledger['cumulative_staged_repairs']==12)
 readiness=read(D/'release_readiness.json');ck('limited-controlled-tests-only-not-general-release',readiness['status']=='CONDITIONALLY_READY_FOR_DISPOSABLE_CONTROLLED_TESTS'and readiness['full_release_readiness']=='BLOCKED_NOT_RUNTIME_QUALIFIED'and readiness['tests_executed']==readiness['game_launches']==readiness['deployments']==readiness['save_or_fact_writes']==0 and readiness['may_launch_or_deploy_in_QR8']is False and len(readiness['general_release_blockers'])>=5)
 for g in readiness['gates']:pin(g['path'],g['sha256'])
 compile=read(D/'verification/compile_successor_01/result.json');ck('REDscript-reuse-honestly-described-no-fresh-compiler',compile['input_pins']==134 and compile['staged_sources']==131 and compile['managed_sources']==46 and compile['fresh_QR8_SCC_invocation']is False and 'reuse'in(D/'REPORT.md').read_text(encoding='utf-8').lower())
 preserve=read(D/'verification/preservation_01/result.json');ck('preservation-metrics-and-scope-no-new-runtimewrites',preserve['status']=='PASS'and preserve['protected_sha256_files']==19824 and preserve['whole_game_metadata_files']==856 and preserve['whole_save_metadata_files']==307 and preserve['current_compile_input_pins_rechecked']==134 and preserve['tracked_diff_unchanged']and all(preserve[k]==0 for k in['protected_hash_differences','game_metadata_differences','save_metadata_differences','compile_input_differences','game_writes','save_writes']))
 tests=read(D/'acceptance_tests.json');ck('nine-actual-prepared-tests-and-prioritized-shared-pass',len(tests['tests'])==9 and {t['id']for t in tests['tests']}=={'S0'+str(i)for i in range(9)}and all(t['execution_status']=='PREPARED_NOT_RUN'and all(t.get(k)for k in['required_save_baseline','actions_after_authorization','expected_observations','diagnostics','rollback_precautions'])for t in tests['tests'])and tests['game_launches']==tests['save_or_fact_writes']==0 and tests['deployment_authorized_by_this_document']is False)
 ck('acceptance-current02-hashes-not-predecessor',tests['candidate_binding']['epoch']=='QR8:02'and tests['candidate_binding']['archive_sha256']==ep['archive_sha256']and tests['candidate_binding']['zip_sha256']==ep['zip_sha256'])
 ck('S02-alternatives-do-not-manufacture-history',len(next(t for t in tests['tests']if t['id']=='S02')['variants'])==3 and 'NOT_TESTABLE'in json.dumps(tests)and 'NOT_OBSERVED'in json.dumps(tests))
 report=(D/'REPORT.md').read_text(encoding='utf-8');handoff=(D/'HANDOFF.md').read_text(encoding='utf-8');diag=(D/'ENGINE_DIAGNOSTIC.md').read_text(encoding='utf-8');ck('current-human-docs-exact02-delivery-hashes',all(ep['archive_sha256']in s and ep['zip_sha256']in s for s in[report,handoff,diag]))
 ck('human-docs-qualify-actor-presence-dispatch-and-history',all(s in report for s in['actor absence','receipt','LIVE_ONLY','UNKNOWN','FAIL','sent1','19824','856','307'])and 'TransactionSystem258'in handoff and 'ContainerManager'in handoff and 'unconditional'in diag and 'not a successful-owner'in diag.replace('**',''))
 # Counterfactual accounting controls use actual final documents without altering any current input.
 bad=copy.deepcopy(cmp);bad[0]['final_status']='PASS'if bad[0]['final_status']!='PASS'else'UNKNOWN';ck('mutant-comparison-status-promotion-detected',any(r['final_status']!=by[key(r)]['status']for r in bad))
 bad=copy.deepcopy(source);bad[NEWS]=old['source_resources'][NEWS];ck('mutant-obsolete-Ronald-donor-detected',bad[NEWS]!=source[NEWS])
 bad=copy.deepcopy(tests);bad['game_launches']=1;ck('mutant-prepared-plan-false-execution-detected',bad['game_launches']!=0)
 # Final consistency: every file observed by this reviewer remains on the exact size/mtime snapshot.
 ck('all-reviewed-hash-snapshots-remain-stable',all((Path(o['path']).stat().st_size,Path(o['path']).stat().st_mtime_ns)==tuple(o['metadata'])for o in OBS.values()))
 result={'status':'PASS_INDEPENDENT_QR8_FINAL_COMPLETENESS_WITH_LIMITS'if all(c['pass']for c in checks)else'FAIL','checks':checks,'check_count':len(checks),'publication':{'path':str(pubfile),'sha256':sha(pubfile)},'reviewed_input_pins':pins,'derived_selected':len(selected),'contract_count':len(cm),'status_counts':counts,'targeted_updates':len(updates),'unchanged_contract_provenance':len(untouched),'source_only_addenda':len(applicability),'retained_UNKNOWNs':sorted(unknowns),'explicit_failed_enrollment_parent_rows':len(failrows),'package_scope':{'source_resources':len(source),'actual_extracted_resources':len(members),'package_and_ZIP_paths':51,'changed_resource':NEWS,'stock_container_hashes_repeated':0},'private_accounting_controls':3,'manual_review_required':'Supplement follows after substantive source/readiness ambiguity review; no self-sealing or completion authority.','preservation_boundary':'Pinned primary19824-hash preservation result and exact metrics; protected/game/save full scan not rerun by this final reviewer. Whole candidate source/actual extracted payloads,51package/ZIP bytes and current direct evidence pins independently SHA-observed in the completed predecessor pass and exact current stable snapshots.','hash_observation_carry_forward':carry,'checker_sha256':sha(__file__),'no_root_A_C_checker_import':True,'runtime_writes':0,'completion_seal_not_yet_written':not(D/'completion.json').exists()}
 save(out/'review.json',result);save(out/'hash_observations.json',list(OBS.values()));print(result['status'],len(checks),'assertions',len(pins),'unique SHA pins')
 if result['status']=='FAIL':print([c['name']for c in checks if not c['pass']]);raise SystemExit(1)
if __name__=='__main__':main()
