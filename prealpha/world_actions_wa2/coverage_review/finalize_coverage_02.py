"""Complete concrete payload dispositions; retain earlier pinned review unchanged."""
import collections,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;WS=OUT.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
old=read(OUT/'assessment_01.json');full=read(OUT/'all_payloads_02.json');remaining=read(OUT/'remaining_payloads_01.json')
inline={r['ids'][0]:r for r in full['rows'] if r['scope']=='outside_inline'}
external={r['ids'][0]:r for r in full['rows'] if r['scope']=='external' and r['ids']}
groups={
 'SPAWN_REARM_CROWD_ONLY_NO_SEPARATE_ACTOR_ACTION':[41,42,46,153,192,196,254,255,286,299,303,304,307,310,312,313,314,317,323,346,439,442,444,449,450,451,454,455,458,469],
 'EMPTY_DELETION_PLACEHOLDER':[474,476],
 'ENVIRONMENT_VARIANTS_LIGHTS_NOT_NPC_ACTION_LOOP':[55,193,194,211,212,367],
 'VEHICLE_DAMAGE_VISUALS_NOT_NPC_ACTION_LOOP':[129,213,257,284,288,298,300,322,337,339,386],
 'DANCEFLOOR_SCENE_WITH_NATIVE_FACT_AND_REACTION_STATE':[187,188,241,258,279,341],
 'NATIVE_ATTITUDE_MUTATION_NOT_AMBIENT_ACTION_LOOP':[301],
 'WEAPON_USE_LOOP_WITH_NO_CURRENT_WORLD_BINDING':[306],
 'MULTI_COMMUNITY_VEHICLE_DEAL_ACTION_REQUIRES_SEPARATE_OWNER_PROOF':[471],
}
notes={
 'SPAWN_REARM_CROWD_ONLY_NO_SEPARATE_ACTOR_ACTION':'Only native spawn/reset, waits, control flow and optional crowd-null operations; no explicit actor action controller to restore. Missing prefab/support eligibility remains a different problem, and full encounter replay is excluded.',
 'EMPTY_DELETION_PLACEHOLDER':'Input/output/deletion-marker graph only; no executable actor action.',
 'ENVIRONMENT_VARIANTS_LIGHTS_NOT_NPC_ACTION_LOOP':'Authored assets_variant visibility changes;194 also sends VehicleLightQuestToggleEvent. These change scenery/vehicle light state, not repeated NPC behavior.',
 'VEHICLE_DAMAGE_VISUALS_NOT_NPC_ACTION_LOOP':'Nested VehicleQuestVisualDestructionEvent setup on burning cars, with security/variant state in parent. No ShootAt, UseWeapon, move or workspot command.',
 'DANCEFLOOR_SCENE_WITH_NATIVE_FACT_AND_REACTION_STATE':'Native dancefloor scene, cs_dancefloor_on write, reaction preset and vehicle-door/variant setup. This is a stateful scene family requiring its own player/actor ownership review, not a proven missing shooting loop.',
 'NATIVE_ATTITUDE_MUTATION_NOT_AMBIENT_ACTION_LOOP':'Six SetAttitudeGroupForPuppet writes for goon1/2/3 (None,6thStreet_ow,friendly); applying these would mutate faction state, not supply a missing repeated action.',
 'WEAPON_USE_LOOP_WITH_NO_CURRENT_WORLD_BINDING':'Native13-node UseWeapon Shoot loop is authored, but exact actor community15848539396956498445 is absent both current registries; exact support sector and three bounded naming variants absent125archives. Distinct current289 community2164557977367347990 exists. Do not remap or create actors.',
 'MULTI_COMMUNITY_VEHICLE_DEAL_ACTION_REQUIRES_SEPARATE_OWNER_PROOF':'Native seat-assignment/mount/unmount sequence spans corp/gang communities and vehicles, includes instant assignment and cleanup. Shared background community is insufficient proof of participant/support ownership; whole reset-bearing encounter must not be replayed.',
}
ids=[i for xs in groups.values() for i in xs]
assert len(ids)==58 and len(set(ids))==58 and set(ids)=={r['id'] for r in remaining['rows']}
checks=[]
def check(name,condition):
    checks.append({'name':name,'pass':bool(condition)});assert condition,name
check('all240_inline_and168_external_payloads_resolved',len(inline)==240 and len(full['rows'])==408)
check('58_remaining_dispositions_exhaustive',len(ids)==58)
check('outside_shooting_families_exactly130250306',{i for i,r in inline.items() if r['shooting_payloads']}=={130,250,306})
check('no_external_weapon_shooting_payload',all(not r['shooting_payloads'] for r in external.values()))
for id in groups['SPAWN_REARM_CROWD_ONLY_NO_SEPARATE_ACTOR_ACTION']+groups['EMPTY_DELETION_PLACEHOLDER']:
    check(f'{id}_no_actor_action_payload',not inline[id]['special_payloads'])
for id in groups['VEHICLE_DAMAGE_VISUALS_NOT_NPC_ACTION_LOOP']:
    t=inline[id]['all_payload_types'];check(f'{id}_vehicle_damage_family',t.get('VehicleQuestVisualDestructionEvent',0)>0 and not inline[id]['shooting_payloads'])
for id in groups['DANCEFLOOR_SCENE_WITH_NATIVE_FACT_AND_REACTION_STATE']:
    t=inline[id]['all_payload_types'];check(f'{id}_scene_and_native_fact',t.get('questSceneNodeDefinition')==1 and t.get('questSetVar_NodeType',0)>0)
proof306=read(OUT/'candidate306_01/report_01.json')
check('306_registry_absent_and289_present',all({x['community_id'] for x in r['found']}=={proof306['hashes']['289']} for r in proof306['registry_rows']))
check('306_exact_and3bounded_sectors_absent_all125archives',proof306['archives']==125 and len(proof306['variants'])==4 and len(proof306['hits'])==1 and proof306['hits'][0]['depot'].endswith('.questphase'))
decisions=[]
for r in old['decisions']:
    id=r['candidate_index'];d=dict(r);p=inline[id]
    for key,values in groups.items():
        if id in values:d['decision']=key;d['reasons']=[notes[key]];break
    if id in (51,309):
        d['decision']='MULTI_COMMUNITY_VEHICLE_DEAL_ACTION_REQUIRES_SEPARATE_OWNER_PROOF';d['reasons']=[notes[d['decision']]]
    if id==250:
        d['decision']='ELIGIBLE_EXACT_SHOOTING_ACTION_AND_NEW_SUPPORT_OWNER_BUILT';d['reasons']=['Exact current native community/three active entries/support prefab/targets proven; minimal Baseline append and support owner pass64-source compilation and independent guard proof. Root owns final action implementation and deployment.']
    if id in external:
        e=external[id];p=e
        d['action_families']={k:v for k,v in e['all_payload_types'].items() if k in ('AISetCombatPresetCommandParams','AIAssignRoleCommandParams','AIClearRoleCommandParams','AIInjectCombatThreatCommandParams','questUseWorkspotNodeDefinition')}
        if d['decision']=='FULL_ENCOUNTER_PHASE_REPLAY_EXCLUDED':d['reasons']=['Native encounter state machine contains community reactivation/reset, completion/checkpoint and world writes. Authored patrol/combat/civilian workspot operations are explicitly inventoried; not action-free. No weapon-shooting controller. Replaying encounter or extracting unproved side-effect slice is excluded.']
    d['resolved_payload_types']=p['all_payload_types'];d['explicit_actor_action_node_paths']=list(p['special_payloads'])
    decisions.append(d)
check('all240_have_final_disposition',len(decisions)==240 and not any(d['decision']=='REQUIRES_INDIVIDUAL_CONTENT_AND_SUPPORT_REVIEW' for d in decisions))
pins=['assessment_01.json','remaining_payloads_01.json','all_payloads_02.json','support_assessment_01.json','candidate306_01/report_01.json']
result={'status':'PASS_EXHAUSTIVE_OUTSIDE_W3_PAYLOAD_DISPOSITIONS_NOT_ALL_NPC_RUNTIME_PROOF',
 'counts':{'outside_W3_prefab_rows':240,'unique_outside_owner_nodes':236,'remaining_previously_unclassified':58,'external_phases_current_readback':168,'new_safe_support_owner':1,'new_support_group_id':250,'unbound_native_shooting_groups':[130,306]},
 'checks':checks,'check_count':len(checks),'decision_counts':dict(collections.Counter(d['decision'] for d in decisions)),
 'remaining58_family_ids':groups,'decisions':decisions,
 'external_actor_action_counts':{k:v for k,v in full['counts']['external'].items() if k in ('AISetCombatPresetCommandParams','AIAssignRoleCommandParams','AIClearRoleCommandParams','AIInjectCombatThreatCommandParams','questUseWorkspotNodeDefinition')},
 'external_patrol_role_candidate_ids':[id for id,r in external.items() if r['all_payload_types'].get('AIAssignRoleCommandParams')],
 'external_civilian_workspot_candidate_ids':[id for id,r in external.items() if r['all_payload_types'].get('questUseWorkspotNodeDefinition')],
 'limits':['Static exhaustive disposition within477combat-event prefab-reference census;237W3 owners are independently reviewed by native_review.','This does not prove everyNPC family repaired: quest/courier/scene/player-interaction families outside census remain outside verified coverage.','Vehicle-deal51/309/471, dancefloor scenes and encounter patrol/civilian actions are acknowledged authored behavior, but lack the separate safe ownership/lifecycle proof needed for this shooting repair.','No new in-game result inferred; BA1 group179 alone has user-confirmed shooting fix.'],
 'evidence':[{'path':str(OUT/p),'sha256':sha(OUT/p)} for p in pins],
 'game_writes':0,'save_writes':0}
dest=OUT/'assessment_02.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
md='''# Outside-W3 action coverage review

The240 previously excluded native prefab rows now have explicit payload dispositions. Full handle resolution also scanned168 current external phase resources. Only130,250 and306 contain weapon-shooting commands outside W3.250 has an exact current world identity and its added support owner/driver passed64-source compilation.130 and306 have no matching current native community or support resource; neither may be remapped to an existing group.

The58 formerly generic review rows divide into30 spawn/rearm/crowd-only graphs,2 empty placeholders,6 environment/light setups,11 burning-car visual setups,6 stateful dancefloor scene families,1 attitude-mutation graph,1 unresolved weapon-use loop306, and1 multi-community vehicle-deal sequence471.

There are real authored actions outside the shooting cohort:51/309/471 contain corp/gang vehicle seating sequences, and external phases contain47 patrol-role assignments,345 combat presets,5 role clears,1 injected threat and7 civilian workspot commands. Those operations belong to encounter or scene state machines. They must not be presented as restored by WA2, nor replayed with their community resets/checkpoints. The full per-row JSON records these boundaries and exact payload types.

306 uses two questUseWeapon Shoot commands in root/234/35/52. Its current community hash15848539396956498445 is absent from both native registries;289's different2164557977367347990 is present. Exact306 support resource and three bounded hashtag variants are absent across125archives. The current Rancho native source is pinned in candidate306_01. This supports withholding306, not substituting289 or fabricating actors.

No game/save writes or runtime success claims were made. This is an exhaustive disposition within the477-reference combat-event census, not an all-NPC gameplay guarantee. Existing237W3 action scope is separately reviewed by native_review.
'''
report=OUT/'coverage_02.md';assert not report.exists();report.write_text(md,encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'decision_counts':result['decision_counts'],'assessment_sha256':sha(dest)},indent=2))
