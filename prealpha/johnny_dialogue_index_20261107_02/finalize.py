"""Select only a successor that passed source and normal-interface verification."""

import sqlite3
from datetime import datetime, timezone

from common import *


def main():
    if (TASK/'summary.json').exists():raise SystemExit('Preserve the sealed summary')
    verification=read(INDEX/'verification.json')
    cli=read(INDEX/'cli_verification.json')
    manifest=read(INDEX/'database_manifest.json')
    assert verification['status']==cli['status']=='PASS'
    assert verification['database']==manifest and cli['database_sha256']==manifest['sha256']
    assert cli['search_sha256']==sha(TASK/'search.py')
    assert cli['normal_interface_and_guard_checks']==16
    db=sqlite3.connect(Path(manifest['path']).as_uri()+'?mode=ro',uri=True)
    assert dict(db.execute('SELECT key,value FROM metadata'))['status']=='VERIFIED'
    counts={name:db.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0] for (name,) in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'search_fts%' AND name NOT LIKE 'sqlite_%'")}
    resource_kinds=dict(db.execute('SELECT kind,count(*) FROM resources GROUP BY kind'))
    summary={'schema':1,'recorded_utc':datetime.now(timezone.utc).isoformat(),
        'status':'STEP2_SUCCESSOR_VERIFIED_WITH_EXPLICIT_SOURCE_LIMITS','selected_index':'index_05',
        'database':manifest,'counts':counts,'resource_kinds':resource_kinds,
        'additional_subtitle_providers':29,'reused_subtitle_providers':12,
        'subtitle_providers_examined':41,'additional_subtitle_entries':1202,
        'additional_localization_variants':2404,'text_items_requalified':1347,
        'new_english_dialogue_events':308,'new_english_stored_lines':10,'new_english_johnny_source_events':3,
        'unresolved_english_items':verification['unresolved_english_items'],
        'voiceset_source_payloads':412,'voiceset_dispatch_params':3433,
        'role_leads':dict(db.execute('SELECT role_lead,count(*) FROM dispatches GROUP BY role_lead')),
        'dispatch_target_statuses':dict(db.execute('SELECT status,count(*) FROM dispatch_targets GROUP BY status')),
        'candidate_event_links':572,'literal_null_socket_boundaries':6,
        'opaque_scene_hold':'q303_10_concert_braindance.scene',
        'source_verification':'index_05/verification.json','cli_verification':'index_05/cli_verification.json',
        'normal_interface_and_guard_checks':16,
        'scope_limit':'Indexed source evidence includes pre-Tower, inactive, historical and external-mod branches. Binding, actual post-Tower routes, provider winners and saved owners require later review.',
        'game_writes':0,'save_writes':0,'parent_index_writes':0,'step3_started':False}
    db.close()
    write(TASK/'summary.json',summary)
    paths=[*TASK.glob('*.py'),*TASK.glob('*.ps1'),PREVIOUS/'search.py',COVERAGE/'verify.py',COVERAGE/'prepare.py',
           WORKSPACE/'tools/build_phase2a.ps1']
    write(TASK/'provenance.json',{'files':[{'path':str(p),'sha256':sha(p)} for p in sorted(paths)],
        'prepared_inputs_sha256':sha(TASK/'evidence_01/prepared.json'),
        'source_verification_sha256':sha(INDEX/'verification.json'),
        'cli_verification_sha256':sha(INDEX/'cli_verification.json'),
        'parent_preserved':True,'failed_candidates':['index_03','index_04'],
        'failure_evidence':['evidence_03','evidence_04','evidence_05'],
        'game_writes':0,'save_writes':0})
    write(TASK/'checkpoint.json',{'schema':1,'step':2,'status':summary['status'],
        'plan':'docs/johnny_dialogue_removal_plan_20261107.md','selected_index':'index_05',
        'database_target':'index_05/dialogue.sqlite3','database_manifest':'index_05/database_manifest.json',
        'summary':'summary.json','report':'REPORT.md','verification':'index_05/verification.json',
        'interface_checks':'index_05/cli_verification.json','step3_started':False,
        'next_action':'Wait for the user to start Step 3. Preserve the source holds and all native/shared/private route candidates when preparing the planned editable review document.'})
    print(encode({k:v for k,v in summary.items() if k not in {'counts','scope_limit'}}))


if __name__=='__main__':
    main()
