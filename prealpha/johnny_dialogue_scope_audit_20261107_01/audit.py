"""Audit Steps 1/2 scope claims using the sealed index, without modifying it."""

import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[1]
INDEX_TASK=ROOT/'prealpha/johnny_dialogue_index_20261107_02'
COVERAGE=ROOT/'prealpha/johnny_dialogue_coverage_20261107_01'
OUT=TASK/'evidence_01'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest().upper()


def write(path,data):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')


def rows(db,sql,args=()):
    return [dict(r) for r in db.execute(sql,args)]


def main():
    if OUT.exists():raise SystemExit('Use fresh audit evidence')
    manifest=read(INDEX_TASK/'index_05/database_manifest.json')
    assert sha(manifest['path'])==manifest['sha256']
    pointer=read(ROOT/'research/gig_restoration/lore_whitelist_current.json')
    selection=ROOT/pointer['selection_file']
    assert sha(selection)==pointer['sha256']
    dbpath=Path(manifest['path']);before=dbpath.stat()
    db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    assert dict(db.execute('SELECT key,value FROM metadata'))['status']=='VERIFIED'
    unresolved=rows(db,"""SELECT r.scope,s.kind,count(*) count FROM search_items s
        JOIN resources r ON r.resource_id=s.resource_id WHERE s.text_source='UNRESOLVED'
        AND s.kind IN ('DIALOGUE_EVENT','CHOICE') GROUP BY r.scope,s.kind""")
    dispatch_scopes=rows(db,'''SELECT r.scope,d.role_lead,count(*) count FROM dispatches d
        JOIN resources r ON r.resource_id=d.resource_id GROUP BY r.scope,d.role_lead''')
    johnny=rows(db,"""SELECT d.dispatch_key,d.resource_id,d.graph_path,d.node_id,d.voiceset_name,
        r.depot,r.scope,r.raw_sha256 FROM dispatches d JOIN resources r ON r.resource_id=d.resource_id
        WHERE d.role_lead='JOHNNY_REFERENCE_LEAD' ORDER BY r.depot,d.dispatch_key""")
    q115=[r for r in johnny if r['depot'].startswith('base\\quest\\main_quests\\part1\\q115\\')]
    assert len(johnny)==20 and len(q115)==6
    private_gaps=rows(db,"""SELECT s.item_key,s.kind,s.depot,s.speaker_role,s.root_id,s.node_id
        FROM search_items s JOIN resources r ON r.resource_id=s.resource_id
        WHERE r.scope='CURRENT_PTFR_PAYLOAD' AND s.text_source='UNRESOLVED'
        AND s.kind IN ('DIALOGUE_EVENT','CHOICE') ORDER BY s.kind,s.depot,s.item_key""")
    private_english=Counter(r['kind'] for r in private_gaps)
    assert dict(private_english)=={'CHOICE':92,'DIALOGUE_EVENT':5}
    private_events=[r for r in private_gaps if r['kind']=='DIALOGUE_EVENT']
    assert all(r['depot'].endswith('mq059_play_vos.scene') for r in private_events)
    assert Counter(r['speaker_role'] for r in private_events)=={'JOHNNY':1,'V':4}
    graph_boundaries=rows(db,"""SELECT b.boundary_id,r.depot,b.details_json FROM coverage_boundaries b
        JOIN resources r ON r.resource_id=b.resource_id WHERE b.kind='SOURCE_SOCKET_INTERFACE_BOUNDARY'""")
    assert len(graph_boundaries)==6
    for r in graph_boundaries:r['details']=json.loads(r.pop('details_json'))
    issue_scopes=rows(db,'''SELECT r.scope,i.kind,count(*) count FROM issues i
        LEFT JOIN resources r ON r.resource_id=i.resource_id GROUP BY r.scope,i.kind''')
    external_choice_definitions=rows(db,"""SELECT r.depot,i.details_json FROM issues i
        JOIN resources r ON r.resource_id=i.resource_id WHERE i.kind='CHOICE_OPTION_REFERENCE'""")
    for r in external_choice_definitions:r['details']=json.loads(r.pop('details_json'))
    assert len(external_choice_definitions)==2 and all(r['depot'].startswith('mod\\arman3_lizzies_bds\\') for r in external_choice_definitions)
    recovered=read(COVERAGE/'evidence_07/additional_english_subtitles.json')['unresolved_spoken_or_stored_items_with_new_candidates']
    recovered_johnny=[]
    for r in recovered:
        if r['kind']=='DIALOGUE_EVENT' and r['speaker_role']=='JOHNNY':
            recovered_johnny.extend(rows(db,'SELECT item_key,depot,resource_id FROM search_items WHERE item_key=?',(r['item_key'],)))
    assert len(recovered_johnny)==3
    boundaries=read(COVERAGE/'evidence_09/boundary_ledger.json')['boundaries']
    assert len(boundaries)==11
    outside=read(COVERAGE/'evidence_07/outside_scene_review.json')
    provider_groups=read(COVERAGE/'evidence_07/provider_collision_review.json')
    differing=[r for r in provider_groups if not r['payloads_identical']]
    assert len(outside)==4513 and len(differing)==25
    missing=read(COVERAGE/'evidence_07/missing_reference_review.json')
    literal_external=[r for r in missing if r['classification']=='EXTERNAL_LEXICAL_REFERENCE_WITHOUT_PROVIDER']
    assert len(literal_external)==10
    recovered_english_stats=read(INDEX_TASK/'index_05/verification.json')
    assert recovered_english_stats['new_english_providers']==29
    assert recovered_english_stats['reused_parent_resources']=={'SCENE':26,'ENGLISH_SUBTITLES':12}
    selection_data=read(selection)
    selected_controls=[{k:r.get(k) for k in ['id','title','decision','requirements']}
        for r in selection_data['decision_registry'] if r['id'] in {'mq019_paparazzi','mq056_race_replay','mq059_freedom','mq303_addict'}]
    assert {r['id']:r['decision'] for r in selected_controls}=={
        'mq019_paparazzi':'INCLUDE','mq056_race_replay':'SEPARATE_SCOPE',
        'mq059_freedom':'INCLUDE','mq303_addict':'EXCLUDE'}
    policy_paths=[ROOT/'AGENTS.md',ROOT/'PROJECT.md',ROOT/'docs/knowledge/invariants.md',
        ROOT/'docs/johnny_dialogue_removal_plan_20261107.md',
        INDEX_TASK/'README.md',INDEX_TASK/'REPORT.md',INDEX_TASK/'checkpoint.json',
        INDEX_TASK/'scope_20261107_01.json',COVERAGE/'REPORT.md',COVERAGE/'STEP2_HANDOFF.md',
        ROOT/'prealpha/johnny_dialogue_removal_20261107_01/REPORT.md',
        ROOT/'prealpha/johnny_dialogue_index_20261107_01/REPORT.md']
    OUT.mkdir();(OUT/'snapshots').mkdir()
    document_pins=[]
    for ordinal,path in enumerate(policy_paths):
        destination=OUT/'snapshots'/(str(ordinal).zfill(2)+'_'+path.name)
        destination.write_bytes(path.read_bytes())
        document_pins.append({'path':str(path),'sha256':sha(path),'preserved_copy':str(destination)})
    write(OUT/'inputs.json',{'database':manifest,'documents':document_pins,
        'selection_pointer':{'path':pointer['selection_file'],'sha256':pointer['sha256']},
        'audited_steps':[1,2],'step3_started':False})
    write(OUT/'source_count_partitions.json',{'unresolved_english_by_source_scope':unresolved,
        'dispatches_by_source_scope':dispatch_scopes,'private_source_english_gaps':private_gaps,
        'source_issue_scopes':issue_scopes,'source_scope_is_not_runtime_eligibility':True})
    write(OUT/'case_evidence.json',{'johnny_dispatch_source_records':johnny,
        'q115_ending_owned_dispatches':q115,'source_null_connections':graph_boundaries,
        'external_missing_choice_definitions':external_choice_definitions,
        'new_english_johnny_source_records':recovered_johnny,
        'existing_selection_controls':selected_controls,
        'unprovided_external_lexical_candidates':literal_external,
        'differing_provider_groups':differing})
    unresolved_totals=Counter()
    for r in unresolved:unresolved_totals[r['kind']]+=r['count']
    outside_stats={'scenes':len(outside),'scenes_with_johnny_bound_source_events':sum(r['johnny_events']>0 for r in outside),
        'johnny_bound_source_events':sum(r['johnny_events'] for r in outside),
        'scope_limit':'The other scenes cannot be discarded solely for lacking a Johnny-bound line: shared calls, bindings and indirect V reactions remain possible.'}
    summary={'status':'AUDITED_SCOPE_REPORTING_AND_QUEUE_ERRORS_FOUND',
        'recorded_utc':datetime.now(timezone.utc).isoformat(),'audited_steps':[1,2],
        'full_corpus_english_gaps':dict(unresolved_totals),
        'private_payload_english_source_candidates':dict(private_english),
        'private_dialogue_gap_speaker_roles':dict(Counter(r['speaker_role'] for r in private_events)),
        'private_payload_is_not_entire_post_tower_scope':True,
        'johnny_dispatch_source_leads':len(johnny),'excluded_native_q115_dispatch_contexts':len(q115),
        'other_johnny_dispatch_leads_still_need_scope_qualification':len(johnny)-len(q115),
        'private_dispatch_source_parameters':sum(r['count'] for r in dispatch_scopes if r['scope']=='CURRENT_PTFR_PAYLOAD'),
        'outside_scene_source_prioritization':outside_stats,
        'differing_provider_source_types':dict(Counter(Path(r['depot']).suffix for r in differing)),
        'external_missing_option_definitions':len(external_choice_definitions),
        'external_lexical_missing_candidates':len(literal_external),
        'historical_boundary_categories_reviewed':len(boundaries),
        'completed_work_still_appearing_in_historical_boundary_statuses':[
            'BOUNDARY-ENGLISH','BOUNDARY-DISPATCH-GRAPHS'],
        'previous_denominator_corrections_verified':{'new_english_providers':29,'reused_english_providers':12,
            'case_aliases':26,'private_phase_case_aliases':25,'external_entity_case_aliases':1},
        'actual_post_tower_coverage_denominator':'NOT_YET_MEASURED',
        'scope_audit_is_not_an_exchange_or_reaction_review':True,
        'game_writes':0,'save_writes':0,'database_writes':0,'step3_started':False}
    assert dict(unresolved_totals)=={'CHOICE':8828,'DIALOGUE_EVENT':375}
    write(OUT/'summary.json',summary)
    db.close();after=dbpath.stat()
    assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
    write(OUT/'verification.json',{'status':'PASS','database_open_mode':'READ_ONLY',
        'database_sha256':manifest['sha256'],'database_metadata_unchanged':True,
        'all_eleven_historical_boundary_categories_accounted_for':True,
        'selection_hash_verified':True,'source_count_partitions_reconcile':True,
        'twenty_johnny_dispatches_reviewed_by_source_owner':True,
        'q115_native_dispatch_exclusion_count':6,'step3_started':False,
        'game_writes':0,'save_writes':0,'database_writes':0})
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
