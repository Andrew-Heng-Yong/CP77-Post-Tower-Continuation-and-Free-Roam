"""Stage presentation-only Sweet Dreams cleanup on the accepted KM2 baseline."""
from pathlib import Path
import copy
import importlib.util
import json
import sys

HERE=Path(__file__).resolve().parent
WS=HERE.parents[1]
KM2=WS/'prealpha/kold_mirage_km2'
BASE=KM2/'candidate_02'
OUT=HERE/'candidate_02'
INSTALLED=KM2/'deployment_01/installed_manifest_01.json'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
PREFIX='towercontinued\\sidejobs_s29\\native\\base\\quest\\minor_quests\\mq036\\'
SCENE=PREFIX+'scenes\\mq036_scavengers.scene'
PHASE=PREFIX+'phases\\mq036_02_scavengers.questphase'
spec=importlib.util.spec_from_file_location('km2_pure_authoring',KM2/'prepare.py')
api=importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
read,sha,write=api.read,api.sha,api.write
sys.path.insert(0,str(WS/'prealpha/quest_restoration_qr13'))
from resource_edit import Edit
from model import Resource
from common import walk


def prepare_scene(row):
    doc=read(row['json']);editor=Edit(doc);r=editor.r
    actor,=[r.d(a) for a in r.root['actors'] if r.d(a)['actorId']['id']==0]
    assert actor['actorName']=='Johnny' and actor['acquisitionPlan']=='spawnDespawn'
    for flag in ['isEnabled','alwaysSpawned','spawnOnStart']:
        actor['spawnDespawnParams'][flag]=0
    graph=r.d(r.root['sceneGraph']);nodes={str(r.d(h)['nodeId']['id']):r.d(h) for h in graph['graph']}
    removed=[];rewires=[];conditions=[]
    for nid,node in nodes.items():
        if 'actorBehaviors' in node:
            node['actorBehaviors']=[a for a in node['actorBehaviors'] if a['actorId']['id']!=0]
        kept=[]
        for h in node.get('events',[]):
            event=r.d(h);payload=r.clean(event)
            johnny=any((x.get('$type')=='scnActorId' and x.get('id')==0) or (x.get('$type')=='scnPerformerId' and x.get('id')==1) for x in walk(payload))
            if johnny:removed.append({'node':nid,'id':str(event['id']['id']),'type':event['$type']})
            else:kept.append(h)
        if 'events' in node:node['events']=kept
    def dest(nid,stamp,targets):
        socket,=[s for s in nodes[str(nid)]['outputSockets'] if (s['stamp']['name'],s['stamp']['ordinal'])==stamp]
        old=copy.deepcopy(socket['destinations']);socket['destinations']=[api.destination(*t) for t in targets]
        rewires.append({'node':str(nid),'stamp':list(stamp),'before':old,'after':copy.deepcopy(socket['destinations'])})
    # Keep the exact named-entry API, all authored section durations and player
    # animation/VO/HUD callbacks. Remove only acquisition of the absent actor.
    for start,target in [(1,3),(22,21),(26,28),(1048,1055)]:
        dest(start,(0,0),[(target,0)])
    for section,stamp in [(3,(6,0)),(21,(2,0)),(28,(2,0))]:
        dest(section,stamp,[])
    # A nonterminating gameplay exit must be delivered before its terminating
    # actor-cleanup exit. Keep both IDs/ports; use the existing pause nodes for
    # a one-tick delay instead of camera-focus/StopWorkspot on a missing Johnny.
    for source,main,pause,cleanup in [(60,2,105,110),(21,23,125,129),(28,27,117,121)]:
        dest(source,(0,0),[(main,0),(pause,1)])
        q=r.d(nodes[str(pause)]['questNode'])
        assert q['$type']=='questPauseConditionNodeDefinition' and 'Johnny' in json.dumps(r.clean(q['condition']))
        old=r.clean(q['condition'])
        q['condition']=editor.h({'$type':'questTimeCondition','type':editor.h({'$type':'questRealtimeDelay_ConditionType','hours':0,'miliseconds':50,'minutes':0,'seconds':0})})
        conditions.append({'node':str(pause),'before':old,'after_ms':50,'reason':'No-actor cleanup after the original gameplay callback; no quest-state or inventory acknowledgement is fabricated.'})
        dest(pause,(0,0),[(cleanup,0)])
    api.cleanup_event_ids(doc,{e['id'] for e in removed})
    current=Resource(doc);current.handles=r.handles|current.handles
    edited=api.ordered(doc,current);m=Resource(edited).normalize();assert not m['errors'],m['errors']
    return edited,{'johnny_actor_id':0,'johnny_performer_id':1,'spawn_flags':{'isEnabled':0,'alwaysSpawned':0,'spawnOnStart':0},'removed_events':removed,'rewires':rewires,'cleanup_waits':conditions,'section_durations_changed':0,'retained_speech_changed':0,'independent_scene_props':[]}


def prepare_phase(row):
    doc=read(row['json']);editor=Edit(doc);root=editor.graph('root');r=editor.r
    # This auxiliary wake->Johnny comment->Johnny elevator attachment branch
    # has no independent gameplay effect. The original main elevator path from
    # node176 through scene168 and its actual player-inside wait35 is retained.
    hub=editor.node(root,353);_,socket=editor.socket(hub,'Out1')
    model=r.normalize();edge,=[e for e in model['graphs']['root']['edges'] if e[0]=='353']
    assert edge==['353','Out1','78','In']
    target=editor.node(root,78);_,other=editor.socket(target,'In')
    removed_keys={r.hid(h) for h in socket['connections']}
    socket['connections']=[];other['connections']=[h for h in other['connections'] if r.hid(h) not in removed_keys]
    callers=[]
    for nid in [14,46,168,170]:
        node=editor.node(root,nid)
        assert node['$type']=='questSceneNodeDefinition' and not node['interruptionOperations']
        node['interruptionOperations']=[editor.h({'$type':'scnToggleInterruption_InterruptionOperation','enable':0})]
        node['reapplyInterruptionOperationsAfterGameLoad']=1
        callers.append(nid)
    current=Resource(doc);current.handles=r.handles|current.handles
    edited=api.ordered(doc,current);model=Resource(edited).normalize();assert not model['errors'],model['errors']
    return edited,{'removed_actor_only_edge':edge,'speaker_distance_disabled_for_callers':callers,'npc_chatter_callers_unchanged':True,'native_elevator_and_player_trigger_path_unchanged':True,'payback_cleanup_and_173_preserved':True,'native_journal_inventory_money_reward_writes_changed':0}


def main():
    assert not OUT.exists() and not (HERE/'input_02').exists()
    installed=read(INSTALLED);game=Path(installed['game_root'])
    for row in installed['core_files']+installed['required_files']:
        assert sha(game/row['path'])==row['sha256'],row['path']
    capture_path=HERE/'source_01/manifest.json';capture=read(capture_path)
    assert capture['status']=='PASS_SD1_CURRENT_AND_NATIVE_PROVIDERS' and not capture['issues']
    sources={r['depot']:r for r in capture['resources'] if r['scope']=='CURRENT_PRIVATE'}
    baseline=read(BASE/'package_manifest.json')
    for depot,digest in baseline['source_resources'].items():
        p=BASE/'archive_source'/depot;assert not (p.stat().st_file_attributes&0x400) and sha(p)==digest,depot
    import shutil
    OUT.mkdir();shutil.copytree(BASE/'archive_source',OUT/'archive_source')
    for row in baseline['files']:
        assert sha(BASE/'package'/row['path'])==row['sha256']
        if row['path']==ARCHIVE:continue
        p=OUT/'package'/row['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/'package'/row['path'],p)
    inp=HERE/'input_02';inp.mkdir();edits=[]
    for depot,prepare in [(SCENE,prepare_scene),(PHASE,prepare_phase)]:
        source=sources[depot];assert sha(source['raw'])==source['sha256']==baseline['source_resources'][depot] and sha(source['json'])==source['json_sha256']
        doc,changes=prepare(source);path=inp/(str(len(edits)).zfill(2)+'.json');write(path,doc)
        edits.append({'depot':depot,'source':source,'edited_json':str(path),'edited_json_sha256':sha(path),'changes':changes})
    plan={'schema':1,'epoch':'SD1','predecessor':'KM2','authorization':'User requested Sweet Dreams cleanup of Johnny smoke, cigarette, title, spawn effect and scanner presence, and clarified that no gameplay sequence rewiring is needed.','scope':'Presentation-only cleanup. Preserve authored section durations, V recovery/get-up, every retained V/scav line, quest choices/journals, inventory/payment/refund, escape, elevator and Stefan outcomes. Resolve only dependencies on an absent Johnny actor while retaining native completion ports.','candidate':str(OUT),'installed_baseline':str(INSTALLED),'installed_baseline_sha256':sha(INSTALLED),'baseline_package':str(BASE/'package_manifest.json'),'baseline_package_sha256':sha(BASE/'package_manifest.json'),'source_capture':str(capture_path),'source_capture_sha256':sha(capture_path),'edits':edits,'scripts_changed':[],'saved_stage_scope':'The source proposal starts before using Stefan\'s braindance player. User requested CET/reset testing; exact current state and a qualified test method remain under review. No reset/restart command or saved-history migration is included.','explicit_visual_targets':['smoke','cigarette','title/nameplate','spawn/glitch effect','scanner identity','Johnny entity/shadow'],'gameplay_sequence_changes':0,'section_duration_changes':0,'quest_progress_fact_or_journal_reset':0,'archive_payloads':1581,'new_depots':0,'new_ArchiveXL_phase_ids':0,'game_writes':0,'save_writes':0,'installed':False}
    write(inp/'plan.json',plan)
    cp=read(HERE/'checkpoint.json');cp.update(status='PRESENTATION_ONLY_CANDIDATE_PREPARED_PENDING_COOK_AND_VERIFICATION',candidate='candidate_02',plan='input_02/plan.json',scope=plan['scope'],explicit_visual_targets=plan['explicit_visual_targets'],user_test_intent='Requested CET/reset commands; read-only current quest/owner check pending.',next_action='Cook/read back two resources, constrain all player/NPC/quest/inventory/timing changes to zero, verify actor-free entry/exit contracts, and prepare the cleanup proposal. Do not reset or restart a quest.');(HERE/'checkpoint.json').write_text(json.dumps(cp,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'resources':len(edits),'johnny_presentation_events':len(edits[0]['changes']['removed_events']),'section_durations_changed':0,'scripts_changed':0,'game_writes':0}))


if __name__=='__main__':
    main()
