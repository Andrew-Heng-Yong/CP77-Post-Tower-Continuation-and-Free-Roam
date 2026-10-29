"""Pin complete outside-W3 action coverage, decisions and remaining boundaries."""
import collections,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;WS=OUT.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(OUT/'coverage_01.json');e=read(OUT/'external_assessment_01.json');s=read(OUT/'support_assessment_01.json')
assert len(c['rows'])==240 and len(e['rows'])==168 and s['checks_passed']==40
external={i:r for r in e['rows'] for i in r['candidate_indices']}
assert len(external)==167
decisions=[]
for row in c['rows']:
    i=row['candidate_index'];decision='REQUIRES_INDIVIDUAL_CONTENT_AND_SUPPORT_REVIEW'
    reasons=[row['exclusion']]
    if i==250:
        decision='SUPPORT_IDENTITY_ENVIRONMENT_PROVED_NEW_OWNER_ELIGIBLE'
        reasons=['Exact compound alias and fresh community registry resolve former missing identity','Independent native reviewer supplies isolated 29-node/40-edge action contract','Requires new W3-pattern matched living actor + two settled safe samples support admission; no encounter replay']
    elif i==130:
        decision='WITHHELD_NO_CURRENT_EXACT_WORLD_RESOURCE_OR_COMMUNITY'
        reasons=['Exact support sector and three bounded path variants absent across125 installed archives','Exact authored community hash absent from both current native registries','No actor remapping or fabricated support']
    elif i in external:
        phase=external[i]
        if i==359:
            decision='NO_RESTORABLE_ACTION_PAYLOAD_DELETION_PLACEHOLDER'
            reasons=['External phase contains input/output/deletion marker only']
        else:
            decision='FULL_ENCOUNTER_PHASE_REPLAY_EXCLUDED'
            reasons=['Current external phase has native Reactivate/ResetKillCount, facts, checkpoint and world/event side effects','No ForceShoot controller anywhere in exact external phase','Individual action-slice proof would be needed before any future limited reuse']
    elif row['existing_W3_shared_community_owners']:
        decision='NO_DUPLICATE_ADMISSION_SHARED_EXISTING_W3_COMMUNITY'
        reasons+=['Same native community already has a W3 support owner; preserve single ownership','Shared community does not prove alternate prefab/action dependencies equivalent']
    elif i in (473,475):
        decision='FULL_ENCOUNTER_COMBAT_PRESET_GRAPH_EXCLUDED'
        reasons+=['Contains native combat-preset setup, community actions, facts, checkpoints and world writes; not ambient bottle-shoot loop']
    decisions.append({'candidate_index':i,'source':row['source'],'node_path':row['node_path'],'prefab':row['full_ref'],'decision':decision,'reasons':reasons,'external_resource':external[i]['resource'] if i in external else None})

pins=[OUT/x for x in ('coverage_01.json','external_assessment_01.json','external_01/report_01.json','support_assessment_01.json','shooting_sources_01/report_01.json','registry_01/report_01.json')]
checks={
 '240 outside references accounted':len(decisions)==240 and len({r['candidate_index'] for r in decisions})==240,
 '236 unique outside source owners':len({(r['source'],r['node_path']) for r in c['rows']})==236,
 '167 outside external phases fully parsed':len(external)==167,
 '168 exact external resources single native winners':e['counts']['unique_single_native_hits']==168 and e['counts']['mod_overrides']==0,
 'No deeper external resources omitted':e['counts']['resources_with_nested_external_phases']==0,
 'No external ForceShoot controllers':e['counts']['resources_with_ForceShoot']==0,
 'All outside inline combat nodes classified':not any(r['descendant_types'].get('questCombatNodeDefinition') and not r['ai_command_payloads'] for r in c['rows']),
 'Only two outside inline ForceShoot controllers':{r['candidate_index'] for r in c['rows'] if any(a['definition']['$type']=='AIForceShootCommandParams' for a in r['ai_command_payloads'])}=={130,250},
 'External166 outside full encounter phases require replay exclusion':sum('ResetKillCount' in r['community_actions'] for r in external.values())==166,
 '11 overlapping W3 community references identified':sum(bool(r['existing_W3_shared_community_owners']) for r in c['rows'])==11,
 '250 fresh support identity environment checks pass':all(x['pass'] for x in s['checks']),
}
assert all(checks.values()),checks
result={'status':'PASS_COMPLETE_OUTSIDE_W3_SOURCE_COVERAGE_WITH_EXPLICIT_LIMITS',
 'counts':{'native_prefab_references':477,'W3_restored_references':237,'outside_references':240,'outside_unique_owners':236,'external_resources_fresh_parsed':168,'outside_external_resources':167,'additional_W3_external_resource':1,'external_nodes_reviewed':sum(r['node_count'] for r in e['rows']),'outside_inline_ForceShoot_graphs':2,'new_support_identity_environment_eligible':1,'outside_with_shared_existing_W3_community':11},
 'checks':checks,'decision_counts':dict(collections.Counter(r['decision'] for r in decisions)),
 'decisions':decisions,
 'safe_candidate':{'candidate_index':250,'support_proof':'support_assessment_01.json','spawner':'3323904054656225535','entries':['goon1','goon2','goon3'],'parent_implementation_required':True},
 'withheld_shooter':{'candidate_index':130,'reason':'No current exact support resource or community identity in bounded fresh proof'},
 'coverage_boundaries':['477 rows count native combat-event prefab references, not477 NPCs or all world characters. Four outside references share an owner node.','This census covers all outside rows and their direct external phase resources; it does not qualify courier, traffic, pedestrian, quest-scene, gig or other non-combat-event NPC families.','Native external combat-preset/role/action nodes do not alone establish a missing ambient loop. Full encounter replay could respawn content, reset kills and rewrite completion/loot/world state.','Vehicle, radio, light, door, event, item and scene controllers need individual state/ownership and persistent-save review; their presence is not permission to replay them.','Previously restored W3 groups remain authoritative for their actor communities; alternate sibling prefab references must not create duplicate controllers.','Candidate250 static eligibility is not live proof or a completed deployment. Its support and action owner still require package, compiler, lifecycle, collision and rollback checks by the parent.','Native authored graph130 is not proof its world actors exist in the installed game. No broad reset or fallback actor binding is justified.'],
 'game_writes':0,'save_writes':0,'implementation_changes':0,
 'evidence':[{'path':str(p.relative_to(WS)),'sha256':sha(p)} for p in pins],
 'external_readback_json_pins':[{'resource':r['resource'],'path':r['source'],'sha256':sha(Path(r['source'])),'native_binary_sha256':r['sha256']} for r in e['rows']]}
dest=OUT/'assessment_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'decision_counts':result['decision_counts'],'sha256':sha(dest)},indent=2))
