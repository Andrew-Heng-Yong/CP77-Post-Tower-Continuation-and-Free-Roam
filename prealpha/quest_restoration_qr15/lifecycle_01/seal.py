"""Seal the completed source step; update only workspace continuation pointers."""
from pathlib import Path
import datetime, hashlib, json

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
WORK=BASE.parents[1]


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def pin(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def fresh(p,value):
    assert not p.exists(),'Fresh output required: '+str(p)
    p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def manifest_check(directory):
    p=directory/'manifest_01.json'
    rows=read(p)['files']
    for row in rows:
        path=Path(row['path'])
        if not path.is_absolute():
            path=(WORK/path) if (WORK/path).is_file() else directory/path
        assert sha(path)==row['sha256'],str(path)
    return len(rows)


def main():
    for n in ['completion.json','preservation.json','verification.json']:
        assert not (HERE/n).exists(),'Fresh output required'
    baseline=read(BASE/'baseline.json')
    protected={}
    for kind in ['installed','original_saves']:
        rows=[]
        for row in baseline[kind]:
            actual=sha(row['path'])
            assert actual==row['sha256'],row['path']
            rows.append({'path':row['path'],'expected':row['sha256'],'actual':actual})
        protected[kind]=rows
    epoch=read(WORK/'prealpha/quest_restoration_qr13/source_epoch_02.json')
    candidate=Path(epoch['candidate'])
    for depot,expected in epoch['source_resources'].items():assert sha(candidate/'archive_source'/depot)==expected,depot
    for row in epoch['package_files']:assert sha(candidate/'package'/row['path'])==row['sha256'],row['path']
    assert sha(epoch['zip'])==epoch['zip_sha256']
    active=read(WORK/'prealpha/general_gig_probe_gg1/active.json')
    assert active['state']=='STOPPED'
    extraction=read(HERE/'save_community/capture_01/capture.json')
    assert sha(extraction['source'])==extraction['source_sha256'] and sha(extraction['metadata'])==extraction['metadata_sha256']
    assert sha(extraction['trailing_path'])==extraction['trailing_sha256']
    decompile=read(HERE/'script_source/current_01/manifest.json')
    assert sha(decompile['input'])==decompile['input_sha256'] and decompile['input_unchanged']
    decoded=read(HERE/'save_community/decode_02/result.json')
    assert decoded['unparsed_bytes']==0 and decoded['consumed_bytes']==extraction['trailing_bytes']
    assert decoded['saved_active'] and decoded['target_record']['array_0x20']==['10229047']
    assert len(decoded['checks'])==15 and all(c['pass']for c in decoded['checks'])
    source=read(HERE/'script_source/event_contract_01.json')
    assert len(source['checks'])==9 and all(c['pass']for c in source['checks'])
    # These are distinct source/decoder reviews; do not sum their counts into
    # a quest-coverage claim. Earlier proofs are reused without recompilation.
    directories=['prefab_native','installed_wrapper_review','spawn_action_review']
    readback={name:manifest_check(HERE/name)for name in directories}
    candidates=read(HERE/'save_community/vehicle_ps_01/result.json')
    assert candidates['status']=='CANDIDATE_PS_HASH_LOOKUP_NO_STAGE_CERTIFICATE' and not candidates['matches']
    preservation={
        'status':'CURRENT_RUNTIME_ORIGINALS_AND_CANDIDATE_PRESERVED',
        'checks':protected,'source_resources_match':len(epoch['source_resources']),
        'package_files_match':len(epoch['package_files']),'zip_match':True,
        'pinned_historical_save_match':True,'historical_metadata_match':True,
        'base_script_cache_match':True,'evidence_manifests_read_back':readback,
        'recorder_state':active['state'],'runtime_changes':0,'save_or_fact_writes':0,
        'limits':'Only named protected originals and the pinned historical body checked; normal user working-save advances are not treated as corruption. No new installed build or gameplay validation.'
    }
    fresh(HERE/'preservation.json',preservation)
    authoritative=[
        HERE/'REPORT.md',HERE/'HANDOFF.md',HERE/'preservation.json',
        HERE/'prefab_native/manifest_01.json',HERE/'prefab_native/verification_01.json',
        HERE/'community_native/capture_01.json',HERE/'community_native/supplement_02.json',
        HERE/'community_native/schema_02.json',HERE/'community_native/verification_02.json',
        HERE/'installed_wrapper_review/manifest_01.json',HERE/'installed_wrapper_review/verification_01.json',
        HERE/'spawn_action_review/manifest_01.json',HERE/'spawn_action_review/verification_01.json',
        HERE/'save_community/capture_01/capture.json',HERE/'save_community/decode_01/result.json',
        HERE/'save_community/decode_02/result.json',HERE/'save_community/review_01/review.json',
        HERE/'save_community/vehicle_ps_01/result.json',HERE/'script_source/current_01/manifest.json',
        HERE/'script_source/event_contract_01.json',HERE/'script_source/review_01/review.json'
    ]
    completion={
        'status':'NATIVE_LEASE_AND_SAVED_CAR_BOUND_SETUP_STAGE_UNRESOLVED',
        'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence':[pin(p)for p in authoritative],
        'source_step_complete':True,'restoration_complete':False,'runtime_candidate':None,
        'saved_car_active':True,'saved_associated_id':'10229047','loaded_live_body_bound':False,
        'ready_human_tests':[],'runtime_changes':0,'save_or_fact_writes':0,'automated_game_calls':0,
        'next':'Bind saved ID10229047 to exact native entity/stub/PersistentID and vehicle visual/door/queued-event state. Establish a non-replaying setup-stage contract; no repeated console tests or unsafe guard bypass.',
        'closed':['Native shared prefab lease path and delayed release boundary','Exact population/community action distinctions and limited Activate guards','Complete current-version saved CommunitySystem byte traversal and target active byte','Installed flag ABI correct; local header stale','Current-script event paths and limits of generic visual flag'],
        'unresolved':['Vehicle actor/stub/PersistentID identity','Pending versus applied visual/door setup and relevant queued events','Complete16branch preserve/rearm/hold design','Shared courier saved-stage contract','Current live owner/body beyond bounded source/historical evidence']
    }
    fresh(HERE/'completion.json',completion)
    checkpoint=read(BASE/'checkpoint.json')
    checkpoint['status']=completion['status'];checkpoint['next']=completion['next']
    checkpoint['latest_lifecycle_step']={'completion':pin(HERE/'completion.json'),'handoff':str((HERE/'HANDOFF.md').resolve())}
    (BASE/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    queue=read(BASE/'development_queue.json')
    queue['status']=completion['status'];queue['latest_evidence']=pin(HERE/'completion.json')
    queue['ready_human_tests']=[];queue['runtime_candidate']=None
    queue['items'][0]['status']='NATIVE_LEASE_AND_SAVED_ACTIVATION_BOUND_VEHICLE_STAGE_UNRESOLVED'
    queue['items'][0]['required']=completion['next']
    for value in completion['closed']:
        if value not in queue['source_closed']:queue['source_closed'].append(value)
    (BASE/'development_queue.json').write_text(json.dumps(queue,indent=2)+'\n',encoding='utf-8')
    for row in completion['evidence']:assert sha(row['path'])==row['sha256'],row['path']
    fresh(HERE/'verification.json',{
        'status':'SEALED_SOURCE_STEP_AND_PRESERVATION_READBACK_PASS','completion':pin(HERE/'completion.json'),
        'checkpoint':pin(BASE/'checkpoint.json'),'queue':pin(BASE/'development_queue.json'),
        'runtime_candidate':None,'restoration_complete':False,'ready_human_tests':[]
    })
    print(json.dumps({'status':completion['status'],'saved_active':True,'saved_associated_id':'10229047',
                      'installed_preserved':len(protected['installed']),'protected_originals_preserved':len(protected['original_saves']),
                      'source_resources_preserved':len(epoch['source_resources']),'runtime_changes':0,'ready_manual_tests':0}))


if __name__=='__main__':main()
