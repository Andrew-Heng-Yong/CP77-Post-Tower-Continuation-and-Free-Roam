"""Seal QR12 local documentation/evidence; no game/save reads or changes."""
from pathlib import Path
import collections,datetime,hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    dest=H/'completion.json';assert not dest.exists()
    preservation=read(H/'preservation.json');assert preservation['status']=='PASS_READ_ONLY_PRESERVATION'
    review=read(H/'review/result.json');assert review['blocking_findings_remaining']==[]
    for name,key in [('read_saves.ps1','main_reader_sha256'),('read_history_package.ps1','history_reader_sha256'),('classify.py','classifier_sha256'),('analysis_final_02/verified_fixture_inventory.json','final_inventory_sha256'),('analysis_final_02/coverage.json','final_coverage_sha256'),('analysis_final_02/runtime_test_queue.json','final_queue_sha256')]:assert sha(H/name)==review[key]
    assert len(read(H/'classification_controls_02.json')['checks'])==12
    queue=read(H/'analysis_final_02/runtime_test_queue.json');assert queue['ready']==[]
    links=[]
    for name in ['MANUAL_TEST_PLAN.md','REPORT.md','HANDOFF.md','DEVELOPMENT_BLOCKERS.md']:
        p=H/name
        for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in ref:
                target=(p.parent/ref.split('#',1)[0]).resolve();assert target.exists(),(name,ref);links.append({'document':name,'target':ref})
    old=H/'checkpoint.in-progress.json';assert not old.exists();old.write_bytes((H/'checkpoint.json').read_bytes())
    artifacts=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(H.rglob('*'))if p.is_file()and p.name not in('completion.json','checkpoint.json')]
    result={'state':'QR12_COMPLETE_NO_READY_TEST','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'current_analysis':'analysis_final_02','current_slots':102,'retained_backup_locations':102,'distinct_saved_bodies':171,'parse_failures':0,
        'scenarios_per_source':9,'current_scenario_status_counts':read(H/'analysis_final_02/coverage.json')['game_slot_classifications'],'ready_scenarios':[],
        'current_manual_plan':str(H/'MANUAL_TEST_PLAN.md'),'human_Brendan_native_history':'UNKNOWN_DONT_REMEMBER',
        'independent_review':review['status'],'preservation':preservation['status'],'operations':preservation['operations'],
        'validated_local_document_links':links,'current_state_pointer':{'path':str(W/'docs/knowledge/current-state.md'),'sha256':sha(W/'docs/knowledge/current-state.md'),'before_sha256':sha(H/'current-state.before.md')},
        'next':'No immediate special test/capture. Qualify genuinely existing supported history/stage from ordinary gameplay or new read-only evidence before issuing a READY card.',
        'artifacts':artifacts}
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (H/'checkpoint.json').write_text(json.dumps({'state':result['state'],'completion':str(dest),'completion_sha256':sha(dest),'analysis':'analysis_final_02',
        'manual_plan':str(H/'MANUAL_TEST_PLAN.md'),'handoff':str(H/'HANDOFF.md'),'next':result['next'],'runtime_installed_changes':0,'game_launches':0,'save_or_fact_writes':0,'CUA_calls':0},indent=2)+'\n',encoding='utf-8')
    print({'status':result['state'],'artifacts_pinned':len(artifacts),'local_links_verified':len(links),'ready_scenarios':0})
if __name__=='__main__':main()
