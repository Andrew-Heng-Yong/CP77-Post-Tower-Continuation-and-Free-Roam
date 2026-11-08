"""Bounded acceptance-document review and exact five-row successor applicability.

No package rebuild, game probe, collector invocation or shared artifact mutation.
"""
from pathlib import Path
import sys,argparse,csv,json,collections
from prepare import ROOT,HERE,Q7,GAME,read,sha,write

def main(out,draft):
    assert out.resolve().is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
    checks=[];pins=[];issues=[]
    def ck(n,v,ev=None):checks.append({'check':n,'pass':bool(v),'evidence':ev});assert v,n
    def pin(p,h=None):
        p=Path(p);actual=sha(p);ck('Pinned artifact '+p.name,h is None or actual==h);pins.append({'path':str(p.resolve()),'sha256':actual});return p
    task=ROOT/'prealpha/quest_restoration_qr8';jp=pin(task/(draft+'.json'));cp=pin(task/(draft+'.csv'));a=read(jp)
    ep=read(pin(task/'source_epoch_02.json',a['candidate_binding']['manifest_sha256']));old=read(pin(Q7/'source_epoch_04.json'));candidate=Path(ep['candidate'])
    ck('Acceptance binds actual frozen successor epoch',ep['epoch_key']=='QR8:02' and a['candidate_binding']['epoch']==ep['epoch_key'] and ep['package_state']=='REBUILT_ALL_PAYLOADS_READ_BACK_STAGED_NOT_INSTALLED')
    ck('Candidate archive/XL/ZIP bindings match exact source epoch',all(a['candidate_binding'][k]==ep[k]for k in ['archive_sha256','xl_sha256','zip','zip_sha256']))
    ck('Exact source/package sizes derive current manifest',len(ep['source_resources'])==1577 and len(ep['package_files'])==51)
    delta=[d for d in set(ep['source_resources'])|set(old['source_resources'])if ep['source_resources'].get(d)!=old['source_resources'].get(d)]
    ck('Only one existing resource changes from QR7 final',delta==[r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'],delta)
    ck('Changed phase is exact peer-approved serialized proposal',ep['source_resources'][delta[0]]=='6CEB6AC9FA2909771AEEF09D33A36241E1396D26A072725317374837AB79B0EC')
    # Do not recompute unaffected archive/ZIP SHA; coordinator already verified package byte inventories.
    pin(candidate/'archive_source'/delta[0].replace('\\','/'),ep['source_resources'][delta[0]])
    base=read(pin(HERE/'baseline_01/baseline.json'));app=[]
    for r in base['targeted_sources']:
        d=r['depot'];p=candidate/'archive_source'/d.replace('\\','/');pin(p,r['sha256'])
        ck('Five-row targeted resource retains exact epoch hash '+d,ep['source_resources'][d]==r['sha256'] and old['source_resources'][d]==r['sha256'])
        app.append({'depot':d,'path':str(p),'sha256':r['sha256'],'same_as':'QR8:00/QR7:04 investigated source'})
    for r in base['native_inputs']:pin(r['path'],r['sha256'])
    coverage=read(pin(HERE/'findings_03/contract_updates.json'));ck('Five exact UNKNOWN dispositions remain applicable',len(coverage)==5 and all(r['status']=='UNKNOWN'for r in coverage))
    ck('No unresolved row belongs to changed Ronald news resource',not any(r['quest_id']in delta[0]for r in coverage))
    metadata=[]
    for r in read(HERE/'capture_01/manifest.json')['archive_index_inventory']:
        st=Path(r['path']).stat();actual=[st.st_size,st.st_mtime_ns//100+621355968000000000]
        ck('Current provider metadata stable '+Path(r['path']).name,actual==r['metadata']);metadata.append({'path':r['path'],'metadata':actual})
    tests=a['tests'];ck('Exactly nine unique planned tests',len(tests)==9 and {t['id']for t in tests}=={'S'+str(i).zfill(2)for i in range(9)})
    fields=['id','priority','system','fixture_class','required_save_baseline','actions_after_authorization','expected_observations','diagnostics','rollback_precautions','requires_prior_tests','execution_status','variants']
    rows=list(csv.DictReader(cp.open(encoding='utf-8-sig',newline='')));ck('CSV has nine unique matching test rows',len(rows)==9 and len({r['id']for r in rows})==9)
    for t in tests:
        for f in ['required_save_baseline','actions_after_authorization','expected_observations','diagnostics','rollback_precautions']:ck(t['id']+' concrete '+f,bool(t[f])and all(isinstance(x,str)and len(x)>15 for x in t[f]))
        ck(t['id']+' remains prepared/unrun',t['execution_status']=='PREPARED_NOT_RUN')
        row=next(r for r in rows if r['id']==t['id'])
        for f in fields:
            want=t.get(f,[]);got=json.loads(row[f])if isinstance(want,list)else int(row[f])if isinstance(want,int)else row[f]
            ck(t['id']+' JSON/CSV consistency '+f,got==want)
    ck('Minimal first pass is S00–03 before larger second pass',a['minimal_first_pass']==['S00','S01','S02','S03']and a['second_pass']==['S04','S05','S06','S07','S08'])
    order=a['minimal_first_pass']+a['second_pass'];prior=set()
    for tid in order:
        t=next(t for t in tests if t['id']==tid);ck(tid+' prerequisites occur earlier',set(t['requires_prior_tests'])<=prior);prior.add(tid)
    ck('No current game/save/deployment action authorized or observed',a['game_launches']==0 and a['save_or_fact_writes']==0 and a['deployment_authorized_by_this_document']is False)
    common=' '.join(a['common_controls']);ck('Global controllers and unresolved-family risk explicit','All restored controllers load' in common and 'three unresolved quest families' in common and 'master-save safety' in common)
    ck('Immutable genuine master and no synthetic fixture policy explicit','immutable master' in common and 'No pre-ending reload' in common and 'Never set/reset facts' in common and 'NOT_TESTABLE' in common)
    ck('Rollback is closed-game file transaction, never save undo','closed-game deployment transaction' in common and 'does not undo' in common and 'never overwrite' in common)
    s0=tests[0];s2=tests[2];s4=tests[4];s6=tests[6];s7=tests[7]
    ck('New plugin receipt explicitly proves dispatch attempt, not ACK/activation',any('Receipt1 proves the attempt' in x and 'not successful private-owner activation' in x for x in s0['diagnostics']))
    variants={v['id']:v for v in s2['variants']};late=variants['late_future_pre_gate'];ordinary=variants['ordinary_future'];timer=variants['timer_reload_and_queue']
    ck('Exact first-evaluation late-future boundary explicit',any('Issued1 is allowed without root reentry' in x for x in late['required_baseline'])and any('already-skipped' in x for x in late['required_baseline'])and any('saved-handler predicate refresh' in x for x in s2['expected_observations']))
    ck('S02 variant alternatives replace contradictory shared fresh/done baseline',set(variants)=={'ordinary_future','late_future_pre_gate','timer_reload_and_queue'} and 'alternatives' in s2['required_save_baseline'][0]and 'not simultaneous' in s2['required_save_baseline'][0]and any('not-yet-entered' in x for x in ordinary['required_baseline'])and any('done1/sent0' in x for x in late['required_baseline']))
    ck('S02 late variant forbids entering or rearming existing completed owner',any('never enter/rearm' in x for x in s2['actions_after_authorization'])and any('Do not enter/reaccept/rearm' in x for x in late['actions']))
    ck('S02 distinguishes sent0 admission from its own new sent1 timer continuation',any('Ordinary_future and late_future_pre_gate start with native sent0' in x and 'same newly started supported sent1 timer' in x and 'never an old historical clock' in x for x in s2['required_save_baseline'])and any('own new native sent1/timer' in x for x in timer['required_baseline']))
    nv={v['id']:v for v in tests[3]['variants']};ck('S03 prospective/old-Issued fixtures and actions are alternatives',set(nv)=={'prospective','already_issued'}and any('do not impose both' in x for x in tests[3]['required_save_baseline'])and any('do not restart prospective admission' in x for x in nv['already_issued']['actions']))
    ck('First-enrollment FAIL/held extension remains unapproved',any('explicit FAIL/held subroute' in x and 'not repaired by QR8' in x for x in s7['expected_observations']))
    ck('Inherited MQ007 admission/opaque-world proof limits explicit',any('11/51/95' in x and 'unresolved' in x for x in s4['required_save_baseline'])and any('opaque' in x for x in s4['expected_observations']))
    ck('MQ037 test stays containment and preservation, not continuation',s6['fixture_class']=='CONTAINMENT_AND_UNSUPPORTED_CONTINUATION_NEGATIVE' and any('no approved general stage adapter' in x for x in s6['required_save_baseline'])and any('negative safety check' in x for x in s6['expected_observations']))
    ex={x['id']:x for x in a['static_exclusions']};ck('All required static exclusions visible',{'FIRST_ENROLLMENT','FIVE_QUEST_UNKNOWN','MQ037_CONTINUATION','MQ007_ADMISSION'}<=set(ex))
    collector=pin(a['diagnostic_collector']['path'],a['diagnostic_collector']['sha256']);ct=collector.read_text();ck('Collector described syntax-only and no gameplay PASS','syntax parsed; not run' in a['diagnostic_collector']['validation'] and 'READ_ONLY_EXISTING_LOG_SNAPSHOT_NOT_GAMEPLAY_PASS' in ct)
    ck('Collector cannot manufacture facts/quests/save fixtures','This does not start/stop the game' in ct and 'Never overwrite an observation' in ct and 'Output must be a fresh QR8 subdirectory' in ct and 'Stale logs remain explicitly labelled' in ct)
    ck('Collector example includes required current-run parameters','-RunId 'in a['diagnostic_collector']['future_example']and '-SinceUtc 'in a['diagnostic_collector']['future_example']and 'Illustrative' in a['diagnostic_collector']['example_boundary'])
    observer=pin(ROOT/a['engine_observer']['path'],a['engine_observer']['sha256']);ot=observer.read_text();ck('Observer remains prospective and separately authorized','prepared only' in ot.lower() and 'debugger attachment each require their own authorization' in ot and 'No debugger command syntax' in ot and 'No game was launched' in ot)
    ck('Current engine observer supersedes predecessor candidate prerequisite','QR8:02' in ot and ep['archive_sha256'] in ot and ep['xl_sha256'] in ot and ep['zip_sha256'] in ot and 'candidate prerequisite replaced by QR8:02' in ot)
    ck('Observer unchanged DLL/XL registration and receipt-not-ACK boundary explicit','C07DA66DF4E4D57401FA3DF0F6288F3B780F01102A98807B6ADAABAEF45F69BF' in ot and 'generatedID19913' in ot and 'not** a successful-owner acknowledgement' in ot and 'before the first corresponding root/202:200–203' in ot and 'NOT_OBSERVED/NOT_TESTABLE' in ot)
    table=pin(ROOT/a['engine_observer']['original_pinned_table'],a['engine_observer']['original_table_sha256']);ck('Original exact field/register table is retained as evidence',table.exists())
    follow=a['blocked_static_followups'];ck('Current blocker pointers supersede old candidate TransactionSystem chain',follow['current_report']==r'prealpha\quest_restoration_qr8\worker_c\REPORT.md' and follow['current_contracts']==r'prealpha\quest_restoration_qr8\worker_c\findings_03\contract_updates.json' and 'current phase-context170 binds ContainerManager' in follow['supersession'])
    for k in ['current_report','current_findings','current_contracts']:pin(ROOT/follow[k])
    issues=[]
    write(out/'five_contract_applicability.json',{'epoch':'QR8:02','epoch_manifest_sha256':sha(task/'source_epoch_02.json'),'targeted_source_pins':app,'native_inputs_unchanged':True,'current_provider_metadata_unchanged':metadata,'contracts':[{'quest_id':r['quest_id'],'stage':r['stage'],'status':'UNKNOWN','investigation':str(HERE/'findings_03/contract_updates.json'),'applicable_to_new_epoch':True}for r in coverage],'changed_resource':delta[0],'limits':['Applicability carries exact static evidence forward; no unknown saved history, entity ownership, hub/consumer lifecycle or gameplay success is resolved.','Full archive/ZIP/package verification is coordinator/other-worker evidence, not repeated by this bounded review.']})
    write(out/'review.json',{'status':'APPROVED_PREPARED_ACCEPTANCE_PLAN_WITH_EXPLICIT_UNRUN_AND_HISTORY_LIMITS','draft':draft,'checks':checks,'checks_passed':len(checks),'issues':issues,'resolved_prior_findings':['Ordinary/late-future/timer variants separated, no reentry/rearm or old-clock adoption.','Prospective/already-Issued Nitro histories separated.','Current five-UNKNOWN pointers supersede candidate TransactionSystem chain.','Current QR8:02 observer addendum supersedes predecessor prerequisite; original exact register table retained.'],'tests_reviewed':9,'C_unknown_rows_exactly_applicable':5,'runtime_or_shared_candidate_writes':0,'collector_execution':'NOT_RUN; PowerShell AST syntax-only parsing separately returned zero errors. Allowed command inventory comprises filesystem log read/copy and own-output writes; no setter/game invocation.','observer_execution':'NOT_RUN; future separately authorized debugger procedure and exact native boundary only.','source_pins':pins,'code_sha256':sha(__file__)})
    print({'checks':len(checks),'tests':9,'C_applicable_UNKNOWN':5,'issues':len(issues),'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--draft',default='acceptance_draft_05');args=ap.parse_args();main(args.output,args.draft)
