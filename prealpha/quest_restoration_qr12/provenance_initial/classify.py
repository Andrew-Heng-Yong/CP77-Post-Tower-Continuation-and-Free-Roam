"""Evidence-bounded fixture classification, no game/save/runtime operations."""
from pathlib import Path
import collections,csv,hashlib,json
H=Path(__file__).resolve().parent;W=H.parents[1]
ALLOWED={'READY','REQUIRES_MANUAL_PREREQUISITE','BLOCKED_BY_HISTORY','NOT_TESTABLE','UNKNOWN'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def put(name,x):
    p=H/name;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def values(p,name):return [v['value_u32']if v['value_u32']<2147483648 else v['value_u32']-4294967296 for v in p['facts'].get(name,[])]
def positive(p,name):return any(v>0 for v in values(p,name))
def classify(row,p):
    finished=set(row['finished_quests']);realm='q307'in finished and not row['metadata'].get('isPointOfNoReturn')
    known=row['lineage']in('USER_CONFIRMED_MASTER','USER_CONFIRMED_WORKING_BRANCH')
    result=[]
    def add(id,priority,status,reason,names,missing):
        assert status in ALLOWED
        if row['kind']=='OFFLINE_BACKUP':status='NOT_TESTABLE';reason='Offline retained backup is not an existing Load Game slot. '+reason
        elif not realm and status!='BLOCKED_BY_HISTORY':status='NOT_TESTABLE';reason='No qualifying completed-Tower continuation fixture: checkpoint/pre-ending history. '+reason
        result.append({'scenario':id,'priority':priority,'status':status,'reason':reason,'missing_genuine_prerequisite':missing,
            'fact_evidence':{name:{'saved_values_i32':values(p,name),'rows':p['facts'].get(name,[]),'absent':name not in p['facts']}for name in names},
            'scope_limits':['Serialized absence is not runtime zero.','Journal raw hashes are not decoded state labels.','Native questSystem/saved executing owners remain opaque.']+([]if known else['Genuine retained Tower lineage not independently confirmed for this slot.'])})
    cvi=['cvi_02_finished','cvi_02_start','PTFRU9_sts_pac_cvi_02_ParentEntered','PTFRQR7_CVI02_CustomControllerIssued','PTFRQR7_CVI02_PrebriefInFlight','PTFRQR7_CVI02_PerfectInFlight','PTFRQR7_CVI02_FailedInFlight']
    if 'sts_pac_cvi_02'in finished or positive(p,'cvi_02_finished'):
        add('CVI02_fresh_specialized_calls',1,'BLOCKED_BY_HISTORY','Native completion/finished metadata forbids fresh replay.',cvi,'Another genuine future-fresh CVI02 history with no entered/request/outcome/controller history; then full source eligibility/ownership precheck.')
    elif any(positive(p,n)for n in cvi[1:]):
        add('CVI02_fresh_specialized_calls',1,'BLOCKED_BY_HISTORY','Saved entered/request/private owner evidence is outside fresh-only specialized controller admission.',cvi,'Supported separate unadmitted history; no old custom request adoption or reset.')
    else:add('CVI02_fresh_specialized_calls',1,'UNKNOWN','No terminal record found, but absent markers are not proof of fresh eligibility or owner retirement.',cvi,'Genuine retained Tower lineage plus complete native prerequisites and positive no-old-owner evidence.')
    ron=['q302_ronald_messages_enabled','PTFRQR7_RonaldNews_Issued','PTFRQR7_RonaldNews_Retired']+[n for n in p['facts']if n.startswith('PTFRQR7_RonaldNews_')and'Armed'in n]
    if positive(p,'q302_ronald_messages_enabled'):
        add('RONALD_prospective_news',2,'REQUIRES_MANUAL_PREREQUISITE','Saved subscription value is present, but Active contact and exact future/helper/clock stage still need evidence.',ron,'Existing genuine subscription/Active contact, selected not-entered future job, or exact Armed first-gate stage; no historical clock adoption.')
    else:add('RONALD_prospective_news',2,'REQUIRES_MANUAL_PREREQUISITE'if known else'UNKNOWN','No saved positive subscription evidence. Selected live reports show Inactive contact/disabled messages; first enrollment is held.',ron,'Genuine pre-existing subscription plus Active contact; first enrollment is an unimplemented development blocker, not a fixture-making instruction.')
    sk=['mq007_done','mq007_skippy_owner_known','mq007_skippy_re_acquiring_done','mq007_skippy_enemies_total','mq007_skippy_enemies_non_lethal','mq007_skippy_50_enemies_defeated','PTFRS23_MQ007_Issued','PTFRS23_MQ007_ModeTalkConfirmed']
    if 'mq007_smartgun'in finished or positive(p,'mq007_done')or positive(p,'mq007_skippy_re_acquiring_done'):
        add('SKIPPY_supported_return_1101',3,'BLOCKED_BY_HISTORY','Already completed/returned/reacquired evidence cannot be replayed.',sk,'Separate genuine supported pre1101 return stage, earned native outcomes and owner continuity.')
    else:add('SKIPPY_supported_return_1101',3,'UNKNOWN','Kill progression does not identify the saved native pre1101 owner/stage. No exact executing-stage decoder is available.',sk,'Source-supported exact pre1101 return/handoff state and earned Regina history; old11/51/95 admissions/opaque loot remain unsupported.')
    br=['mq037_brendan_introduced','mq037_01_05Sure','mq037_vandal_painted_brendan','mq037_done','PTFRS23_MQ037_Issued','PTFRS23_MQ037_Entered']
    progress=any(positive(p,n)for n in br[:4])or any(x.startswith('mq037')for x in finished)
    add('BRENDAN_unearned_fresh_containment',4,'BLOCKED_BY_HISTORY'if progress else'REQUIRES_MANUAL_PREREQUISITE'if known else'UNKNOWN',
        'Positive earned/progress evidence is not an unearned negative fixture.'if progress else'No positive progression found; absence/post-ending cache cannot prove never-earned history. User does not remember pre-Tower Brendan history.',br,
        'Known genuine never-started pre-Tower Dumpster history with no contradictory progress. User replied Don’t remember; do not infer it.')
    add('BRENDAN_earned_descendant_preservation',5,'REQUIRES_MANUAL_PREREQUISITE'if progress else'UNKNOWN',
        'Needs exact already-earned descendant stage and ownership; no general sequel adapter.'if progress else'No positive earned descendant evidence. Opaque journal bytes do not supply the missing history.',br,
        'Already-earned Dumpster completion and genuinely progressed Spray Paint/Coin Operated Boy descendant, exact journal/owner stage; no fresh excluded chain.')
    nt=['PTFRS29_mq060_nitro_Issued','PTFRS29_mq060_nitro_Entered','PTFRS29_mq060_nitro_Finished','carbought_counter','mq060_done','mq060_fail']
    terminal=positive(p,'mq060_done')or positive(p,'mq060_fail')or positive(p,'PTFRS29_mq060_nitro_Finished')
    issued=positive(p,'PTFRS29_mq060_nitro_Issued')
    add('NITRO_fresh_admission',6,'BLOCKED_BY_HISTORY'if terminal or issued else'REQUIRES_MANUAL_PREREQUISITE',
        'Already-issued/terminal history is not a fresh admission fixture; do not impose new fresh prerequisites on its preserved selector.'if terminal or issued else'Native purchases/allowed earned bike entitlement and fresh owner are not fully established.',nt,
        'A separate unissued genuine history with an earned allowed native Kusanagi and >=3native purchases. No purchases/counter changes are requested to create a test.')
    add('NITRO_existing_issued_preservation',7,'BLOCKED_BY_HISTORY'if terminal else'UNKNOWN',
        'Terminal Nitro history cannot be replayed.'if terminal else'Issued marker, where present, does not reveal exact saved selector/owner liveness.',nt,
        'Actual compatible already-issued selector/owner stage and reload continuity; do not reset Issued or reapply fresh gates.')
    pend=[n for n in p['facts']if ('InFlight'in n or 'RonaldNews'in n or ('holo_'in n and ('activate'in n or'interrupt'in n)))]
    add('PENDING_owner_interrupt_reload_rewards',8,'UNKNOWN','Saved receipts/counters and raw journal records do not prove a currently pending supported native owner, timer or clean reward baseline.',pend,
        'A separate genuine supported pending request/callback/cleanup fixture; natural save permitted; exact reward/item/currency baseline and owner review.')
    add('OTHER_shared_owner_lifecycles',9,'UNKNOWN','No verified saved native graph/listener/studio/lease enumeration; prior successful phone/vendor routes are not repeated.',[],
        'Named source-supported untested route with genuine eligibility and exact ownership/interrupt prerequisites; unresolved Career/Cuckoo/Voodoo evidence stays separate.')
    return result
def main():
    inv=read(H/'inventory.json');jobs=read(H/'parse_jobs.json')['jobs'];parsed={};inputs=[]
    for p in [H/'probe_01.json',*sorted(H.glob('batch_*.json'))]:
        j=read(p);assert j['parser_sha256']=='E607F058C74822B157CAE97F827310C4353CB323D440AE1E3A591307717645FD'
        for r in j['results']:assert r['sha256']not in parsed;parsed[r['sha256']]=r
        inputs.append({'path':str(p),'sha256':sha(p)})
    assert set(parsed)=={j['sha256']for j in jobs}and all(p['status']=='PARSED_SAVED_FACTS_AND_OPAQUE_SURFACES'and p['unchanged_after_read']for p in parsed.values())
    rows=[];flat=[]
    for row in inv['rows']:
        p=parsed[row['sha256']];cases=classify(row,p)
        rows.append({**row,'saved_parse':{'status':p['status'],'source':p['source'],'fact_tables':p['fact_tables'],'fact_entries':p['fact_entries'],'facts':p['facts'],
            'journal_raw_matches':p['journal_raw_matches'],'owner_surface':p['owner_surface']},'scenarios':cases})
        for c in cases:flat.append({'source':row['source'],'kind':row['kind'],'slot':row['slot_directory'],'timestamp':row['metadata'].get('timestampString'),'save_sha256':row['sha256'],
            'scenario':c['scenario'],'priority':c['priority'],'status':c['status'],'reason':c['reason'],'missing_prerequisite':c['missing_genuine_prerequisite']})
    assert not any(x['status']=='READY'for x in flat)
    summary={'slots':inv['counts']['game_slots'],'offline_backups':inv['counts']['offline_backups'],'unique_bodies':len(parsed),'parse_failures':0,
        'excluded_fixture_or_crash_paths':len(inv['excluded_backups']),'fact_names':len(read(H/'catalogue.json')['facts']),'journal_paths':len(read(H/'catalogue.json')['journals']),
        'game_slot_classifications':dict(collections.Counter(x['status']for x in flat if x['kind']=='GAME_SAVE')),'ready_scenarios':[],
        'game_scenario_counts':{id:dict(collections.Counter(x['status']for x in flat if x['kind']=='GAME_SAVE'and x['scenario']==id))for id in sorted({x['scenario']for x in flat})},
        'saved_positive_counts':{name:{'distinct_bodies':sum(positive(p,name)for p in parsed.values()),'game_slots':sum(positive(parsed[r['sha256']],name)for r in inv['rows']if r['kind']=='GAME_SAVE')}for name in ['cvi_02_finished','q302_ronald_messages_enabled','mq007_skippy_owner_known','mq007_done','mq037_brendan_introduced','mq037_done']},
        'CVI_game_nonterminal':[r['slot_directory']for r in inv['rows']if r['kind']=='GAME_SAVE'and not positive(parsed[r['sha256']],'cvi_02_finished')],
        'purchases_observed_values':sorted({v for p in parsed.values()for v in values(p,'carbought_counter')}),
        'evidence_limits':'All matching fact tables retained. No missing=zero rule. Journal state/owner liveness not decoded. Offline backups not automatically loadable/genuine. Same metadata IDs not ancestry.',
        'parser_inputs':inputs}
    put('verified_fixture_inventory.json',{'status':'VERIFIED_READ_ONLY_INVENTORY_WITH_VISIBLE_LIMITS','summary':summary,'rows':rows})
    put('coverage.json',summary)
    for filename,data in [('fixture_scenarios.csv',flat),('save_slots.csv',[{'kind':r['kind'],'slot':r['slot_directory'],'source':r['source'],'timestamp':r['metadata'].get('timestampString'),'sha256':r['sha256'],'playthrough_id':r['metadata'].get('playthroughID'),'tower_finished_metadata':'q307'in r['finished_quests'],'CVI_finished_metadata':'sts_pac_cvi_02'in r['finished_quests'],'lineage':r['lineage']}for r in rows])]:
        p=H/filename;assert not p.exists()
        with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    put('runtime_test_queue.json',{'status':'NO_READY_TEST','ready':[],'human_Brendan_history_answer':'Don’t remember',
        'prioritized':[{'scenario':id,'priority':min(x['priority']for x in flat if x['scenario']==id),'current_game_status_counts':summary['game_scenario_counts'][id],
            'working_ManualSave24':next(x for x in flat if x['kind']=='GAME_SAVE'and x['slot']=='ManualSave-24'and x['scenario']==id)}for id in sorted(summary['game_scenario_counts'],key=lambda s:min(x['priority']for x in flat if x['scenario']==s))],
        'accepted_do_not_repeat':['D00E natural El Capitan sampler PASS','Wilson invitation/completion/eventual shop/reload','Bullets completion/Zane shop/post-line/reload','Cynthia delivered call','Until Death Do Us Part observed completion'],
        'next':'No immediate special test. Await genuine history/stage evidence arising from ordinary play; do not manufacture it.'})
    print({k:summary[k]for k in ['slots','offline_backups','unique_bodies','parse_failures','saved_positive_counts','CVI_game_nonterminal','purchases_observed_values']})
if __name__=='__main__':main()
