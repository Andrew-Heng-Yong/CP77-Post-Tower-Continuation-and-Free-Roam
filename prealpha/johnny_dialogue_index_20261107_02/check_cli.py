"""Exercise normal successor search/context commands and source-integrity guards."""

import importlib.util
import json
import sqlite3
import subprocess
import sys

from common import *


def main():
    out=TASK/'evidence_06'
    if out.exists():raise SystemExit('Use a fresh interface-check output')
    manifest=read(INDEX/'database_manifest.json')
    assert sha(manifest['path'])==manifest['sha256']
    db=sqlite3.connect(Path(manifest['path']).as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    out.mkdir()
    tests=[]
    def cli(*arguments,expect_success=True):
        process=subprocess.run([sys.executable,'-X','utf8','-B',str(TASK/'search.py'),*arguments],
            cwd=WORKSPACE,encoding='utf-8',capture_output=True,timeout=60)
        if expect_success:
            assert process.returncode==0,(arguments,process.stderr)
            return json.loads(process.stdout)
        assert process.returncode!=0
        return process.stderr or process.stdout
    johnny=cli('--speaker','johnny','--scope','CURRENT_PTFR_PAYLOAD','--limit','5')
    assert len(johnny)==5 and all(r['speaker_role']=='JOHNNY' and r['kind']=='DIALOGUE_EVENT' for r in johnny)
    tests.append({'test':'retained_johnny_query','rows':len(johnny)})
    replies=cli('--speaker','v','--addressee','johnny','--scope','CURRENT_PTFR_PAYLOAD','--limit','5')
    assert len(replies)==5 and all(r['speaker_role']=='V' and r['addressee_role']=='JOHNNY' for r in replies)
    tests.append({'test':'retained_v_addressee_query','rows':len(replies)})
    found=cli('--text','know','--limit','5')
    assert len(found)==5
    tests.append({'test':'retained_full_text_search','rows':len(found)})
    dispatches=cli('--kind','dispatch','--speaker','johnny','--limit','5')
    assert len(dispatches)==5 and all(r['speaker_role']=='JOHNNY_REFERENCE_LEAD' and r['text_source']=='NON_DIALOGUE_SOURCE' for r in dispatches)
    tests.append({'test':'johnny_dispatch_leads_are_distinct_from_dialogue','rows':len(dispatches)})
    key=db.execute("SELECT dispatch_key FROM dispatches WHERE role_lead='JOHNNY_REFERENCE_LEAD' AND voiceset_name='reaction_location_bad_var_1' LIMIT 1").fetchone()[0]
    detail=cli('--context',key,'--depth','0')
    assert detail['verified_source_export']['hash_verified']
    exact=[r for r in detail['target_binding_candidates'] if r['status']=='EXACT_NAMED_ENTRY_CANDIDATE']
    assert exact and any(r['dialogue_candidates'] for r in exact)
    assert all(not r['evidence']['binding_resolved'] for r in exact)
    tests.append({'test':'dispatch_exact_entry_and_candidate_dialogue_context','exact_targets':len(exact),
        'candidate_lines':sum(len(r['dialogue_candidates']) for r in exact)})
    player=cli('--kind','dispatch','--actor','PLAYER','--scope','CURRENT_PTFR_PAYLOAD','--limit','5')
    assert player and all(r['speaker_role']=='PLAYER_CONTEXT_REQUIRED' for r in player)
    player_detail=cli('--context',player[0]['item_key'],'--depth','0')
    assert player_detail['dispatch']['is_player']==1
    assert 'unproved' in player_detail['dispatch_limit']
    tests.append({'test':'player_context_not_assumed_to_be_v','rows':len(player)})
    tags=cli('--kind','voice-tag','--actor','JOHNNY','--limit','5')
    assert tags
    tag=cli('--context',tags[0]['item_key'],'--depth','0')['voice_tag']
    assert tag['tag_id']=='1103967280742240508' and tag['scene_depot'].endswith('vset_johnny.scene')
    tests.append({'test':'voice_tag_source_mapping','rows':len(tags)})
    sounds=cli('--kind','sound','--limit','1')
    sound=cli('--context',sounds[0]['item_key'],'--depth','0')
    assert sound['verified_source_export']['hash_verified'] and sound['source_ancestors']
    assert sound['sound_event']['payload']['$type']=='animAnimEvent_Sound'
    tests.append({'test':'support_sound_source_and_animation_context','ancestors':len(sound['source_ancestors'])})
    metadata=cli('--kind','metadata','--limit','1')
    metadata_detail=cli('--context',metadata[0]['item_key'],'--depth','0')
    assert metadata_detail['voice_metadata']['payload'] and metadata_detail['verified_source_export']['hash_verified']
    tests.append({'test':'voice_metadata_context','rows':len(metadata)})
    boundaries=cli('--kind','boundary','--scene','q303_10_concert_braindance','--limit','50')
    assert any(r['boundary_id']=='DECODE-Q303-CONCERT' for r in boundaries)
    opaque=cli('--context','DECODE-Q303-CONCERT')
    assert opaque['resource']['status']=='OPAQUE' and opaque['verified_boundary_source']['hash_verified']
    assert all(r['code']=='EXCEPTION' for r in opaque['boundary']['details']['attempts'])
    tests.append({'test':'opaque_scene_explicit_hold_and_raw_hash','rows':len(boundaries)})
    sockets=cli('--kind','boundary','--text','NULL_SOURCE_ENDPOINT','--limit','20')
    assert len(sockets)==6
    socket=cli('--context',sockets[0]['boundary_id'])
    assert socket['boundary']['kind']=='SOURCE_SOCKET_INTERFACE_BOUNDARY'
    tests.append({'test':'literal_null_endpoints_exposed','rows':len(sockets)})
    recovered=read(COVERAGE/'evidence_07/additional_english_subtitles.json')['unresolved_spoken_or_stored_items_with_new_candidates']
    selected=next(r for r in recovered if r['kind']=='DIALOGUE_EVENT' and r['speaker_role']=='JOHNNY')
    recovered_detail=cli('--context',selected['item_key'],'--depth','0')
    assert recovered_detail['item']['text'] and recovered_detail['item']['text_source']=='EXTERNAL_SUBTITLE_VARIANTS'
    assert any(r['locale']=='en_us' and r['root_id'] is None for r in recovered_detail['localization_candidates'])
    tests.append({'test':'new_english_johnny_text_visible_with_provenance','item_key':selected['item_key']})
    coaster=db.execute("""SELECT s.depot FROM search_items s JOIN resources r ON r.resource_id=s.resource_id
        WHERE r.scope='CURRENT_PTFR_PAYLOAD' AND s.depot LIKE '%mq006_02_finale.scene' AND s.kind='STORED_LINE'
        AND s.speaker_role='JOHNNY' GROUP BY s.depot HAVING count(*)=14""").fetchone()[0]
    unused=cli('--kind','stored','--speaker','johnny','--scene',coaster,'--limit','50')
    active=cli('--speaker','johnny','--scene',coaster,'--limit','50')
    assert len(unused)==14 and not active
    tests.append({'test':'coaster_stored_lines_not_playback','stored':len(unused),'dialogue':len(active)})
    stamp=db.execute("""SELECT root_id,source_node FROM edges WHERE output_stamp IN ('0:1','1:0')
        GROUP BY root_id,source_node HAVING count(DISTINCT output_stamp)=2 LIMIT 1""").fetchone()
    assert stamp
    stamps={r[0] for r in db.execute('SELECT output_stamp FROM edges WHERE root_id=? AND source_node=?',tuple(stamp))}
    assert {'0:1','1:0'}<=stamps
    tests.append({'test':'socket_name_and_ordinal_preserved','stamps':['0:1','1:0']})
    error=cli('--database',str(TASK/'index_03/dialogue.partial.sqlite3'),'--limit','1',expect_success=False)
    assert 'sealed' in error
    tests.append({'test':'unverified_successor_rejected'})
    # A small fixture exercises export-hash rejection without touching real sources.
    fixture=out/'changed_export.json';fixture.write_text('{}\n',encoding='utf-8')
    memory=sqlite3.connect(':memory:');memory.row_factory=sqlite3.Row
    memory.execute('CREATE TABLE supplemental_sources(resource_id TEXT,json_path TEXT,json_sha256 TEXT)')
    memory.execute('INSERT INTO supplemental_sources VALUES(?,?,?)',('fixture',str(fixture),'0'*64))
    spec=importlib.util.spec_from_file_location('successor_search_guard',TASK/'search.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:module.source_check(memory,{'resource_id':'fixture','kind':'VOICESET_DISPATCH'})
    except SystemExit as error:assert 'changed' in str(error)
    else:raise AssertionError('Changed source export was accepted')
    memory.close();tests.append({'test':'changed_export_rejected_without_modifying_sources'})
    db.close()
    assert sha(manifest['path'])==manifest['sha256']
    prepared=read(TASK/'evidence_01/prepared.json')
    assert sha(prepared['parent']['path'])==prepared['parent']['sha256']
    for row in prepared['protected']:assert sha(row['path'])==row['sha256']
    write(INDEX/'cli_verification.json',{'status':'PASS','normal_interface_and_guard_checks':len(tests),
        'tests':tests,'search_sha256':sha(TASK/'search.py'),'database_sha256':manifest['sha256'],
        'parent_and_current_installed_sources_unchanged':True,'game_writes':0,'save_writes':0,'step3_started':False})
    print(encode(read(INDEX/'cli_verification.json')))


if __name__=='__main__':
    main()
