"""Seal QR10 offline deliverables and checkpoint; no game/save writes."""
from pathlib import Path
import datetime, json, re, subprocess
from preflight import fresh_output, read, sha
H=Path(__file__).resolve().parent;W=H.parents[1]

def main():
    target=fresh_output('completion.json')
    primary=read(H/'tests_final_01/results.json');review=read(H/'review/review_result.json')
    addendum=read(H/'review/addendum_result_02.json');pre=read(H/'preflight_before_final_01.json');pres=read(H/'preservation_final_01.json')
    assert primary['status']=='PASS_OFFLINE_ONLY'and len(primary['passed_checks'])==44 and len(primary['mutations_detected'])==6
    assert review['blocking_lua_findings']==[]and addendum['remaining_blocking_findings']==[]
    assert pre['status']=='PASS_READ_ONLY_BEFORE_PREFLIGHT'and pres['status']=='PASS_PRESERVATION'
    assert addendum['manifest_sha256']==sha(H/'manifest_02.json')
    assert read(H/'runtime_queue.json')['status']=='NO_QUALIFIED_NEW_QUEST_CARD'
    for p in H.glob('*.md'):
        for url in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if url.startswith(('http:','https:','#')):continue
            assert (p.parent/url.split('#')[0]).exists(),(p.name,url)
    artifact_names=['REPORT.md','ROOT_CAUSE.md','OWNER_VERIFICATION.md','TEST_CARDS.md','DEPLOYMENT.md','HANDOFF.md',
        'manifest_02.json','runtime_queue.json','fixture_evidence.json','provenance.json','tests_final_01/results.json',
        'preflight_before_final_01.json','preflight_fixtures_03/results.json','preservation_final_01.json',
        'review/REVIEW.md','review/ADDENDUM_02.md','review/review_result.json','review/addendum_result_02.json',
        'review/installed_game_guard.json','review/installed_cet_proxy_02.json',
        'review/recheck_game_01.json','review/recheck_cet_01.json','review/successor_controls_01.json',
        'review_preflight_recheck_01/results.json','prepare_successor.py','test_diagnostics.py','preflight.py',
        'test_preflight.py','prepare_evidence.py','capture_baseline.py','verify_preservation.py','finalize.py']
    paths=[H/n for n in artifact_names]+[Path(r['source'])for r in read(H/'manifest_02.json')['files']]
    status=subprocess.check_output(['git','-c','safe.directory='+str(W).replace('\\','/'),'status','--short'],cwd=W,text=True)
    before=read(H/'baseline.json')['git_status_before']
    result={'status':'OFFLINE_ENGINEERING_COMPLETE_NOT_INSTALLED_NOT_LIVE_VALIDATED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'root_cause':'Exact installed QuestsSystem scripted-class mask0x04 rejects CET NativeProxy class flags2.',
        'selected_manifest':'manifest_02.json','candidate':'candidate_02','native_callback_delivery':'UNSUPPORTED_NOT_VERIFIED',
        'live_sampling':'NOT_TESTED','offline_checks':{'primary':44,'independent_additional':15,'source_mutants_detected':6,'preflight_controls':19},
        'preservation':{'protected_hashes':pres['protected_sha256_count'],'save_files_equal':pres['save_files_byte_equal'],
            'game_metadata_equal':pres['game_metadata_entries_unchanged'],'QR9_metadata_equal':pres['QR9_metadata_entries_unchanged']},
        'runtime_actions':{'install':0,'rollback':0,'game_launch':0,'game_API_execution':0,'CUA':0,'save_or_fact_write':0,'Core_rebuild':0},
        'qualified_new_quest_cards':0,'conditional_diagnostic_cards':1,
        'remaining_unknowns':['Natural getter-difference validation','Native fact callbacks require a separately verified scripted bridge',
            'Actual graph/listener/controller/shared-lease ownership and termination','Exact phone queue/ACK/native-write ordering',
            'Internal saved native timers and fast reload identity/liveness','Genuine remaining quest fixture histories and supported stages',
            'Unobserved runtime alternatives and exact reward idempotence','Fresh authorized two-leaf installation transaction/crash recovery before any game writes'],
        'artifacts':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in paths],
        'current_state_pointer':{'path':str(W/'docs/knowledge/current-state.md'),'after_sha256':sha(W/'docs/knowledge/current-state.md'),
            'before_backup':str(H/'documentation_before/current-state.md')},
        'git_status_new_entries':sorted(set(status.splitlines())-set(before.splitlines())),
        'non_successful_attempts':[{'command':'review/test_successor.py (existing fixed output)',
            'result':'Fresh-output assertion refused already occupied successor_controls_01.json after checks; no evidence overwritten. Original independently recorded15 assertions remain valid for unchanged Lua.'}],
        'next':'Await separate installation authorization; satisfy fresh transaction/recovery gates, then human D00 only if existing Regina Call option. No repeat successful quests.'}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    checkpoint={'state':result['status'],'completion':str(target),'completion_sha256':sha(target),
        'primary_handoff':str(H/'HANDOFF.md'),'selected_manifest':str(H/'manifest_02.json'),
        'installed':'QR8:02 + QR9B04 unchanged','prepared':'QR10D01 candidate_02; sampling only',
        'native_callbacks':'UNSUPPORTED_NOT_VERIFIED','live_sampling':'NOT_TESTED',
        'runtime_actions':result['runtime_actions'],'next':result['next'],
        'context':'One QR10 context compaction observed; earlier whole-project count unknown. Continuation state preserved; no thread/goal creation.'}
    (H/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'artifacts':len(paths),'protected_hashes':pres['protected_sha256_count'],'save_files':pres['save_files_byte_equal'],'new_git_entries':result['git_status_new_entries']})

if __name__=='__main__':main()
