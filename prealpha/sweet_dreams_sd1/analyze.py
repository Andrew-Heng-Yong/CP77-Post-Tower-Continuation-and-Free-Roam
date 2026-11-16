"""Pin Sweet Dreams source findings for the presentation-only proposal."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
sys.path.insert(0,str(WS/'tools/parity_audit'))
from model import Resource
from common import walk


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest().upper()


def main():
    output = HERE/'analysis_02'
    assert not output.exists()
    output.mkdir()
    capture_path = HERE/'source_01/manifest.json'
    capture = read(capture_path)
    assert capture['status'] == 'PASS_SD1_CURRENT_AND_NATIVE_PROVIDERS' and not capture['issues']
    models, rows = {}, []
    for row in capture['resources']:
        assert sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256']
        model = Resource(read(row['json'])).normalize()
        assert not model['errors'],(row['depot'],model['errors'])
        # An entry wrapper and native root can share their basename. Use the
        # exact depot key and scope; the first exploratory basename exports
        # under analysis_01 are not selected evidence.
        path = output/(row['scope']+'_'+row['key']+'.model.json')
        path.write_text(json.dumps(model,ensure_ascii=False),encoding='utf-8')
        rows.append({'depot':row['depot'],'scope':row['scope'],'raw_sha256':row['sha256'],'source_json':row['json'],'source_json_sha256':row['json_sha256'],'model':str(path),'model_sha256':sha(path),'root_prefabs':model['root_prefabs'],'graphs':{p:len(g['nodes']) for p,g in model['graphs'].items()}})
        if row['scope'] == 'CURRENT_PRIVATE':
            models[row['depot']] = model
    prefix='towercontinued\\sidejobs_s29\\native\\base\\quest\\minor_quests\\mq036\\'
    scene=models[prefix+'scenes\\mq036_scavengers.scene']
    phase=models[prefix+'phases\\mq036_02_scavengers.questphase']
    actor,=[a for a in scene['metadata']['actors'] if a['actorId']['id']==0]
    assert actor['actorName']=='Johnny' and actor['spawnDespawnParams']['dynamicEntityUniqueName']['$value']=='a_mq036_scavengers_Johnny'
    actor_events=[];actor_nodes=[];journal_paths=[];wake_events=[]
    for depot,model in models.items():
        for gp,g in model['graphs'].items():
            for nid,node in g['nodes'].items():
                payload=node['payload']
                journal_paths.extend(x['realPath'] for x in walk(payload) if x.get('$type')=='gameJournalPath' and 'johnny' in x.get('realPath','').lower())
                if depot.endswith('mq036_scavengers.scene'):
                    quest=payload.get('questNode')
                    if quest and 'johnny' in json.dumps(quest).lower():
                        actor_nodes.append({'node':nid,'type':quest['$type'],'incoming':[e for e in g['edges'] if e[2]==nid],'outgoing':[e for e in g['edges'] if e[0]==nid]})
                    for event in payload.get('events',[]):
                        refs=[x for x in walk(event) if (x.get('$type')=='scnActorId' and x.get('id')==0) or (x.get('$type')=='scnPerformerId' and x.get('id')==1)]
                        if refs:actor_events.append({'node':nid,'event_id':str(event['id']['id']),'type':event['$type'],'start_time':event['startTime'],'duration':event['duration']})
                        if nid=='3':wake_events.append({'event_id':str(event['id']['id']),'type':event['$type'],'start_time':event['startTime'],'duration':event['duration'],'johnny_target':bool(refs)})
    # The two private native roots have no Johnny objective; do not introduce
    # an invented journal adaptation just because the KOLD pilot needed one.
    assert not journal_paths
    g=phase['graphs']['root']
    assert ['170','payback_johnny_out','173','In2'] in g['edges']
    assert ['269','Out','173','In1'] in g['edges']
    assert g['nodes']['173']['type']=='questLogicalAndNodeDefinition'
    summary={'status':'SOURCE_CONFIRMED_PRESENTATION_ONLY_PROPOSAL','capture_sha256':sha(capture_path),'resources':rows,'johnny_actor':actor,'johnny_event_targets':actor_events,'johnny_scene_wait_workspot_nodes':actor_nodes,'independent_scene_props':scene['metadata']['props'],'effect_definition_count':len(scene['metadata']['effectDefinitions']),'effect_instance_count':len(scene['metadata']['effectInstances']),'johnny_cigarette_workspot_id':4231323113,'named_entries':scene['graphs']['scene']['entries'],'exit_points':scene['metadata']['exitPoints'],'wake_events':wake_events,'wake_duration_stu':scene['graphs']['scene']['nodes']['3']['payload']['sectionDuration']['stu'],'johnny_journal_paths':journal_paths,'critical_owner_cleanup_contract':{'scene_caller':'root/170','cleanup_exit':'payback_johnny_out','and_node':'root/173','other_input':'root/269 -> In1 (native Stefan community activation)','requirement':'Preserve the existing no-actor cleanup completion callback. Do not bypass the AND, setup, inventory processing, escape or Stefan outcomes.'},'user_scope_revision':'User reviewed the playthrough and says no gameplay rewiring is needed. Preserve the existing quest sequence, player recovery animation/timing, choices and journals. Remove Johnny presentation and only resolve waits/cleanup that would otherwise depend on a removed actor.','explicit_visual_targets':['entity','shadow','smoke','cigarette','title/nameplate','spawn/glitch effect','scanner presence'],'hook_status_effect_context':'The hook uses JohnnySickness-named player status effects for the defective braindance route. A keyword alone is not a Johnny actor dependency. No hook/status-effect or Relic-mechanic change is proposed by this presentation cleanup.','exploratory_export_limit':'analysis_01 used duplicate basenames for an entry and native root; select analysis_02 exact-key exports only. Captured raw/JSON inputs were unique and unchanged.','game_writes':0,'save_writes':0,'candidate_built':False,'installed':False}
    (output/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':summary['status'],'pinned_resources':len(rows),'johnny_presentation_events':len(actor_events),'johnny_scene_wait_workspot_nodes':len(actor_nodes),'johnny_journal_paths':0,'critical_cleanup_and':173,'game_writes':0}))


if __name__=='__main__':
    main()
