"""Finalize QR11 preservation, queue and checkpoint. No game/save writes."""
from pathlib import Path
import datetime, hashlib, json, sys
H=Path(__file__).resolve().parent;W=H.parents[1];Q10=H.parent/'quest_restoration_qr10';Q9=H.parent/'quest_restoration_qr9'
sys.path.insert(0,str(Q10))
from capture_baseline import meta,sha
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,data):
    p=H/name;assert not p.exists();p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');return p
def main():
    b=read(H/'baseline.json');ready=read(H/'readiness.json');manifest=read(H/'diagnostics_manifest_01.json')
    assert ready['installer_sha256']==sha(H/'deploy_diagnostics.ps1')and ready['manifest_sha256']==sha(H/'diagnostics_manifest_01.json')
    assert read(H/'preflight_real_01.json')['status']=='PREFLIGHT_READY'
    for p,s in b['protected_sha256'].items():assert sha(p)==s,p
    for p,s in b['save_sha256'].items():assert sha(p)==s,p
    for key,p in [('game_metadata',b['game_root']),('save_metadata',b['save_root']),('QR9_metadata',Q9),('QR10_metadata',Q10)]:assert meta(Path(p))==b[key],key
    for row in manifest['files']:assert sha(Path(b['game_root'])/row['path'])==row['before']
    assert not(H/'recovery/diagnostics_qr10d01_01').exists(),'Real recovery must remain uncreated'
    source=read(Q10/'runtime_queue.json')
    queue={'status':'D00_CONDITIONAL_OTHER_QUESTS_NOT_TESTABLE_CURRENT_EVIDENCE','source':str(Q10/'runtime_queue.json'),'source_sha256':sha(Q10/'runtime_queue.json'),
        'selected_save':'ManualSave-24,2Nov2026 16:37:02 level51','D00':{'status':'CONDITIONAL_EXISTING_REGINA_CALL_OPTION','duration_s':120,'profile':'D00','card':'MANUAL_TEST_PLAN.md','native_fact':'phonecall_player_with_regina_jones'},
        'additional_qualified_tests':[],
        'prioritized':[{'id':x['id'],'priority':x['priority'],'status':'NOT_TESTABLE_CURRENT_EVIDENCE','previous_status':x['status'],'basis':x['basis'],'missing_prerequisites':x['missing_prerequisites']}for x in source['prioritized']],
        'do_not_repeat':source['accepted_do_not_repeat'],'limits':'No new gameplay. No blanket claim that all uninspected historical save slots are impossible; no additional genuine fixture is currently qualified.'}
    write('runtime_test_queue.json',queue)
    preservation={'status':'PASS_PRESERVATION','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'protected_hashes_equal':len(b['protected_sha256']),'save_files_byte_equal':len(b['save_sha256']),
        'game_metadata_unchanged':len(b['game_metadata']),'QR9_metadata_unchanged':len(b['QR9_metadata']),'QR10_metadata_unchanged':len(b['QR10_metadata']),
        'installed':'QR8:02 Core and QR9B04 unchanged','real_recovery_target':'ABSENT','save_or_fact_writes':0,'game_launches':0,'CUA_calls':0,
        'limits':'All saves/protected bytes hashed; complete game/QR9/QR10 metadata compared. Other bulk game files not all byte-hashed. Workspace fixtures intentionally mutated; only current-state doc pointer changed outside QR11.'}
    write('preservation_final_01.json',preservation)
    artifact_names=['MANUAL_TEST_PLAN.md','REPORT.md','HANDOFF.md','DEPLOYMENT_AND_ROLLBACK.md','deploy_diagnostics.ps1','diagnostics_manifest_01.json',
        'readiness.json','preflight_real_01.json','run_02_results.json','runtime_test_queue.json','preservation_final_01.json','save_selection.json','controls_evidence.json',
        'collect_d00.py','test_collector.py','collector_controls_02.json','test_deployment.py','prepare.py','seal_ready.py','finalize.py','review/REVIEW.md','review/result.json','review/adversarial_results_02.json']
    result={'status':'READY_NOT_INSTALLED_AWAITING_USER_DEPLOYMENT_AND_D00','utc':preservation['utc'],'primary_plan':str(H/'MANUAL_TEST_PLAN.md'),
        'readiness':'48fixturechecks/86actions +8independent/7actions +13collectorcontrols; actualread-onlyPREFLIGHT_READY',
        'runtime_actions':{'real_Install':0,'real_Rollback':0,'real_Recover':0,'game_launch':0,'CUA':0,'save_or_fact_write':0},
        'artifacts':[{'path':str(H/n),'sha256':sha(H/n),'bytes':(H/n).stat().st_size}for n in artifact_names],
        'native_callbacks':'UNSUPPORTED_NOT_VERIFIED','live_sampling':'NOT_TESTED','next':'User authorizes or performs exact diagnostic-only deployment, then conditional D00. No other qualified quest tests.'}
    p=write('completion.json',result)
    write('checkpoint.json',{'status':result['status'],'completion_sha256':sha(p),'handoff':str(H/'HANDOFF.md'),'manual_plan':str(H/'MANUAL_TEST_PLAN.md'),
        'installed':'QR8:02 +QR9B04 unchanged','prepared':'QR10D01 candidate02 + guarded QR11 installer','next':result['next']})
    print({'status':result['status'],'protected':len(b['protected_sha256']),'save_files':len(b['save_sha256']),'artifacts':len(artifact_names)})
if __name__=='__main__':main()
