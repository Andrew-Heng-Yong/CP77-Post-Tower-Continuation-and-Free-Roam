"""Bounded final ledger/input/correction audit; does not rerun group verifiers."""
from pathlib import Path
import sys,json,collections,argparse,re,csv,hashlib
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent;F=H.parents[2]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
KEYS={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
VALID={'PASS','APPROVED_DEVIATION','FAIL','CONDITIONAL','OPAQUE','UNKNOWN','LIVE_ONLY'}
def run(O):
 assert not O.exists();checks=[];issues=[];rows=[];groups=[];cache={};inputs={};source_rows=[];source_seen=set()
 def check(name,ok,e,severity='ERROR'):
  row=dict(name=name,status='PASS' if ok else 'FAIL',evidence=e);checks.append(row)
  if not ok:issues.append(dict(severity=severity,**row))
 def pin(p):
  p=Path(p);key=str(p)
  if key not in cache:cache[key]=sha(p)
  return cache[key]
 def take(p):p=Path(p);inputs[str(p)]=pin(p);return read(p)
 def resolve(p,base):
  p=Path(p);return p if p.is_absolute() else base/p
 progress=take(F/'progress.json');queue=take(F/'queue.json');matrix=take(F/'contract_status_matrix.json');cp=take(F/'checkpoint.json');epoch=take(F/'source_epoch_00.json');q={x['id']:x for x in queue['quests']};mx={(x['quest_id'],x['stage']):x for x in matrix};allids=set(q);newids=set();statuses=collections.Counter()
 check('selected catalogue identities unique',len(allids)==len(queue['quests'])==queue['derived_selected_count'],dict(discovered=len(allids),declared=queue['derived_selected_count']))
 check('complete ten-stage selected matrix',len(matrix)==len(allids)*len(KEYS) and len(mx)==len(matrix) and set(mx)=={(q,k) for q in allids for k in KEYS},dict(rows=len(matrix),selected=len(allids),contracts_per_quest=len(KEYS)))
 for gn,gr in progress['groups'].items():
  gp=Path(gr['output']);result=take(gp/'results.json');ids=gr['ids'];check('disjoint group assignment '+gn,not newids.intersection(ids),ids);newids.update(ids)
  review=gr.get('review')or{};check('independent peer review pin '+gn,bool(review) and Path(review['path']).is_file() and pin(review['path'])==review['sha256'],review)
  if review:
   reviewer=next((r['worker'] for n,r in progress['groups'].items() if Path(review['path']).is_relative_to(Path(r['output']))),None);check('different worker peer review '+gn,reviewer is not None and reviewer!=gr['worker'],dict(worker=gr['worker'],reviewer=reviewer))
  t=result['tests'];tp=resolve(t.get('path') if isinstance(t,dict) else t,gp);tests=take(tp);testlist=tests.get('checks') if isinstance(tests.get('checks'),list) else tests.get('results',tests.get('tests',[]));declared=tests.get('total_checks',tests.get('count',tests.get('checks') if isinstance(tests.get('checks'),int) else len(testlist)))
  check('actual final test result count '+gn,len(testlist)==declared and not any(x.get('status')=='FAIL' or x.get('pass')is False or x.get('ok')is False for x in testlist),dict(path=str(tp),reported=declared,actual=len(testlist)))
  expected_test_sha=result.get('tests_sha256') or (t.get('sha256') if isinstance(t,dict) else None)
  if expected_test_sha:check('final test artifact pin '+gn,pin(tp)==expected_test_sha,str(tp))
  mut=tests.get('mutations',[]);muts=mut if isinstance(mut,list) else [x.get('evidence',{}) for x in testlist if 'mutation' in x.get('name','').lower()];check('mutation results detected '+gn,bool(muts) and all(x.get('detected',True) is not False for x in muts),dict(declared_mutations=len(mut) if isinstance(mut,list) else mut,logged_mutation_checks=len(muts)))
  code=gp/'verify.py';code_text=code.read_text(encoding='utf8');inputs[str(code)]=pin(code);footprint=[dict(line=i,text=s.strip()) for i,s in enumerate(code_text.splitlines(),1) if 'deepcopy' in s or 'mutation' in s.lower()][:14]
  if tests.get('verifier_sha256'):check('recorded executed verifier hash '+gn,pin(code)==tests['verifier_sha256'],dict(code=str(code),actual=pin(code),recorded=tests['verifier_sha256']))
  check('mutation code bound to structured inputs '+gn,'deepcopy' in code_text or 'copy' in code_text,dict(code=str(code),sha256=pin(code),footprint=footprint,limit='Code/input/result provenance check; not a rerun or proof every mutation models engine behavior. Normalized graph mutations are distinguished from raw-source controls.'))
  sp=result.get('source_pins') or (result.get('evidence')or{}).get('source_pins') or str(tp.parent/'source_pins.json');sp=resolve(sp,gp);pincontainer=take(sp);pinlist=pincontainer['sources'] if isinstance(pincontainer,dict) else pincontainer
  check('nonempty source inventory '+gn,isinstance(pinlist,list) and len(pinlist)>0,str(sp))
  for s in pinlist:
   binary=s.get('binary',s.get('path'));want=s.get('sha256',s.get('resource_sha256'));j=s.get('source_json',s.get('json'));jh=s.get('json_sha256');d=s.get('depot');record=dict(group=gn,depot=d,binary=binary,expected_sha256=want,kind='binary_resource' if s.get('binary') else 'script_or_document')
   check('actual pinned binary '+gn+str(d),bool(binary and want) and Path(binary).is_file() and pin(binary)==want,record)
   if j and jh:check('actual pinned source JSON '+gn+str(d),Path(j).is_file() and pin(j)==jh,dict(path=j,sha256=jh))
   if d in epoch['source_resources']:check('epoch0 current-private equality '+gn+d,want==epoch['source_resources'][d],record)
   if s.get('raw_pin_in_original_manifest')is False or ('historical_raw_hash'in s and s['historical_raw_hash']is None):record['provenance_limit']='Original manifest raw hash absent; pinned native JSON/fresh export or measured raw provenance must remain explicit.'
   if binary and (binary,want) not in source_seen:source_seen.add((binary,want));source_rows.append(record)
  for f in gr.get('findings',[]):
   quest=f['id'];path=Path(f['contracts']);actual=pin(path);doc=take(path);entry=q[quest];revision=entry.get('explicit_finding_revision');same=actual==f['sha256']
   if not same and revision:
    rv=take(revision['revision']);same=actual==revision['sha256'] and pin(revision['revision'])==revision['revision_sha256'] and pin(rv['prior_contract'])==f['sha256'];check('explicit reconstruction revision preserves old/current pins '+quest,same,dict(original_coordinator_sha=f['sha256'],actual=actual,revision=revision,original_is_reconstructed=True))
   check('active finding input pin '+quest,same and entry['finding_sha256']==actual and entry['finding_path']==str(path),dict(path=str(path),actual=actual,coordinator_original=f['sha256']))
   contracts=doc['contracts'];check('ten nonmissing specific contracts '+quest,set(contracts)==KEYS,sorted(contracts))
   for k,c in contracts.items():
    eff=mx[(quest,k)];proven=json.dumps(c.get('proven'),ensure_ascii=True);ev=json.dumps(c.get('evidence'),ensure_ascii=True);remaining=json.dumps(c.get('remaining'),ensure_ascii=True)
    check('specific evidence-backed contract '+quest+'/'+k,c.get('status')in VALID and bool(c.get('proven')) and bool(c.get('evidence')) and len(proven)>40 and not re.search(r'DEEP_CONTRACTS?_PENDING|not yet investigated|placeholder findings',proven,re.I),dict(status=c.get('status'),proven_chars=len(proven),evidence_chars=len(ev),limit='Schema/lexical specificity validation complements source investigations and peer reviews; not semantic reproof of every sentence.'))
    if c['status'] in ['CONDITIONAL','OPAQUE','UNKNOWN','LIVE_ONLY']:check('specific unresolved evidence visible '+quest+'/'+k,bool(c.get('remaining')) and len(remaining)>45,dict(remaining=c.get('remaining')))
    check('effective queue/matrix stages agree '+quest+'/'+k,entry['contracts'][k]['status']==eff['status'] and eff['findings_source']==str(path),dict(queue=entry['contracts'][k]['status'],matrix=eff['status'],findings=str(path)))
    statuses[eff['status']]+=1;rows.append(dict(group=gn,quest_id=quest,contract=k,epoch0_status=c['status'],effective_status=eff['status'],source_epoch_investigated=eff.get('source_epoch_investigated'),effective_epoch=eff.get('effective_source_epoch'),source=str(path),source_sha256=actual,proven_chars=len(proven),remaining_chars=len(remaining)))
  groups.append(dict(group=gn,quests=len(ids),checks=declared,mutations=len(mut) if isinstance(mut,list) else mut,sources=len(pinlist),peer_review=review,test_path=str(tp),test_sha256=pin(tp),verifier_sha256=pin(code)))
 check('all assigned quests have final findings',len(rows)==len(newids)*len(KEYS) and newids==set(progress['completed_quests']),dict(assigned=len(newids),contracts=len(rows),ledger_completed=len(progress['completed_quests'])))
 deep=set(queue['deep_reviewed_ids']);pending=allids-deep;check('64 deep 97 not-yet-investigated independently reconciled',len(deep)==cp['total_deep_reviewed']==queue['deep_reviewed_count'] and len(pending)==cp['remaining_not_deep_reviewed'],dict(deep=len(deep),pending=len(pending),selected=len(allids)))
 check('no completed group awaits peer review',set(queue['pending_review_ids'])==set(progress['completed_quests'])-{q for g in progress['groups'].values() if g['status']=='REVIEWED_WITH_LIMITS' for q in g['ids']},dict(pending_review_ids=queue['pending_review_ids'],meaning='Completed investigation awaiting peer review, not remaining uninvestigated catalogue IDs.'))
 check('48 new checkpoint and distribution reconciled',len(newids)==cp['newly_deep_reviewed']==queue['new_investigated_count'] and dict(statuses)==cp['new_contract_status_counts'],dict(new=len(newids),contracts=len(rows),statuses=dict(statuses)))
 check('zero full-static quests no blanket PASS',cp['fully_static_verified']==queue['static_verified_count']==0 and not any(x.get('fully_static_verified') for x in queue['quests']),dict(checkpoint=cp['fully_static_verified'],queue=queue['static_verified_count']))
 canonical=take(F/('source_epoch_%02d.json'%cp['source_epoch']));metadata_correction=take(F/'metadata_corrections.json');manifest=take(F/'candidate_01/package_manifest.json');archive=F/'candidate_01/package/archive/pc/mod/zzzz_PTFR_Combined.archive'
 check('canonical metadata archive pin matches actual package',canonical['archive_sha256']==manifest['archive_sha256']==pin(archive),dict(epoch=cp['source_epoch'],canonical_archive_sha256=canonical['archive_sha256'],actual=pin(archive),correction=str(F/'metadata_corrections.json')))
 # Active corrections, preserving historical evidence rather than rewriting it.
 corrected=[]
 for quest in progress['groups']['G02']['ids']:
  r=mx[(quest,'communications')];active=json.dumps(r['proven']);original=json.dumps(r.get('original_proven',[]));ok='SupportIssued is claimed before fresh native body' not in active and 'SupportIssued is claimed before fresh native body'in original and ('concurrent'in active.lower() or 'parallel'in active.lower());check('G02 concurrency correction active '+quest,ok,dict(active=r['proven'],original_preserved=bool(r.get('original_proven'))));corrected.append(quest)
 race=take(F/'groups/G03/verification_01/hypothesis_correction.json');check('rejected phone race explicitly preserved',race['status'].startswith('REJECTED') and all(x['proposed_patch_rejected'] for x in race['correct_evidence']),str(F/'groups/G03/verification_01/hypothesis_correction.json'))
 facts=take(H/'MQ007_serialized/facts_default_zero_01/FACTSDB_DEFAULT_ZERO_CORRECTION.json');check('reviewer missing-zero overclaim explicitly corrected',facts['status']=='CORRECTED_FIXTURE_INTERPRETATION_NO_RESOURCE_CHANGE' and facts['checks']==52 and pin(facts['preserved_original']['path'])==facts['preserved_original']['sha256'],facts['correction'])
 revision=take(F/'groups/G12/revisions/stable_fences_01/revision.json');attest=take(F/'groups/G11/reviews/G12_revision_01.json');check('LifeWork current revision independently attested',attest['status'].startswith('APPROVED_EXACT_DOCUMENTATION_SUPERSESSION') and not revision['contract_statuses_changed'] and not revision['runtime_or_source_epoch_changed'],dict(revision=str(F/'groups/G12/revisions/stable_fences_01/revision.json'),attestation=str(F/'groups/G11/reviews/G12_revision_01.json'),checks=attest['checks']))
 rootcheck=take(F/'candidate_01/repair_mq007/verification_02/tests.json');code=F/'check_mq007_repair.py';check('root current focused checker input/code pins',all(Path(p).is_file() and pin(p)==h for p,h in rootcheck['input_pins'].items()) and str(code) in rootcheck['input_pins'] and 'f.get(x[\'factName\'],0)' in code.read_text(),dict(code_sha256=pin(code),checks=rootcheck['checks'],mutations=len(rootcheck['mutations'])))
 check('root checker final package stage gate present',any(t['name']=='final package50otherfiles unchanged and archive matches readback' for t in rootcheck['tests']),rootcheck['limits'])
 for p in [F/'groups/G11/reviews/QR4_package/REPORT.json',F/'groups/G11/reviews/QR4_package_supplement_03/REPORT.json']:
  pkg=take(p);check('independent package review exists '+str(p),bool(pkg),dict(path=str(p),sha256=pin(p),status=pkg.get('status'),checks=pkg.get('checks')))
 # Epoch0 investigations stay valid under their immutable inputs; only the
 # exact MQ007 pair is allowed to differ in the current staged source.
 successor=F/'candidate_01/archive_source';patch=take(F/'candidate_01/repair_mq007/patch.json');allowed={x['depot']:x['after'] for x in patch['resources']};delta=[];bad=[];frozenbad=[]
 for d,expected in epoch['source_resources'].items():
  old=Path(epoch['candidate'])/'archive_source'/d;new=successor/d
  if pin(old)!=expected:frozenbad.append(d)
  actual=pin(new)
  if actual!=expected:delta.append(d)
  if actual!=allowed.get(d,expected):bad.append(d)
 check('frozen epoch0 resources preserved',not frozenbad,dict(resources=len(epoch['source_resources']),mismatches=frozenbad))
 check('successor only approved MQ007 pair changed',not bad and set(delta)==set(allowed),dict(resources=len(epoch['source_resources']),changed=delta,unchanged=len(epoch['source_resources'])-len(delta)))
 # Protect the snapshot boundary if coordinator integration changed during read.
 unstable=[p for p,h in inputs.items() if sha(p)!=h];check('review input snapshot stable',not unstable,unstable)
 summary=dict(selected=len(allids),new_investigated=len(newids),new_contracts=len(rows),total_deep=len(deep),pending=len(pending),matrix_rows=len(matrix),fully_static=0,new_contract_statuses=dict(statuses),groups=len(groups),unique_binary_pins=sum(x['kind']=='binary_resource' for x in source_rows),unique_script_document_pins=sum(x['kind']=='script_or_document' for x in source_rows),group_focused_checks=sum(g['checks'] for g in groups),group_mutations=sum(g['mutations'] for g in groups),corrected_G02_communications=len(corrected))
 report=dict(status='PASS_BOUNDED_COVERAGE_INPUT_AND_CORRECTION_REVIEW' if not issues else 'REVIEW_WITH_EXPLICIT_FINDINGS',reviewer='qr4_worker_a',scope='Read-only independent ledger/480-contract schema and specificity/input/hash/test/mutation provenance/correction review. Does not rerun all group verifiers or claim semantic/gameplay verification of every sentence.',summary=summary,checks=checks,issues=issues,groups=groups,input_pins=inputs,unique_source_inputs=source_rows,root_checker_review=dict(path=str(code),sha256=pin(code),result='verification_02 is current final-package-aware stage; verification_01 remains historical prepackage evidence',facts_semantics='Missing scalar zero requirements accept under f.get(key,0); positive provenance still required. Original conservative missing-fact fixtures remain preserved and explicitly superseded.',remaining_limits='Native11/51/95 admission, already-entered/returned timers, sector contents and live scheduler/loot behavior remain unresolved. Correct package/source parity is not gameplay success.'),epoch_adjudication='Epoch0 group inputs and historical MQ007 FAIL rows are preserved. Canonical epoch'+str(cp['source_epoch'])+' carries source-identical1572 payloads and the independently reviewed native-continuation pair; no full quest becomes static-complete. The stale inherited archive metadata is explicitly superseded by metadata_corrections.json without changing package bytes.',risks=['The final review checks evidence completeness, source versions, explicit limits and known corrected assumptions; it does not prove every native predicate satisfiable or every save/engine lifecycle.','Native JSON-only historical pins, opaque world/TDB targets, catalogue gaps and native non-ack/retry semantics remain case-specific CONDITIONAL/OPAQUE findings.','Normalized graph-copy mutations are useful structural controls, not all serialization tests. Raw helper/timer/guard mutations and independent WK readbacks cover the actual MQ007 repair; broader CR1/PH1/PH2/PH3 controls remain reused evidence.'],runtime_changes=[],central_files_edited=False)
 write(O/'review.json',report);write(O/'contracts.json',rows)
 with (O/'contracts.csv').open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (O/'REPORT.md').write_text(f'# QR4 bounded final coverage review\n\n{report["status"]}. {len(newids)} new investigations / {len(rows)} contracts across {len(groups)} groups; {len(deep)} total deep / {len(pending)} pending of {len(allids)} selected; {len(matrix)} matrix rows; zero fully static quests. Effective new statuses: {dict(statuses)}.\n\nAll active source/review/test pins and per-contract findings were reconciled. Five G02 concurrency claims are superseded while originals remain. Rejected S24 race, MQ007 missing-zero model correction and LifeWork exact documentation revision remain explicit. The root72-check/6-mutation repair result now pins code/JSON inputs and supports final-package validation; original163-check reviewer evidence remains bounded by its52-check default-zero correction.\n\nNo blanket parity/gameplay PASS. MQ007 applies only to future supported entry before done; old timers/owners, exact11/51/95 admission, opaque sector/item targets and engine delivery remain unresolved. No central/runtime/game/save files were edited by this review.\n',encoding='utf8')
 return dict(status=report['status'],summary=summary,issues=len(issues))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
