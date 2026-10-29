"""Bounded action slices, dependencies, and exhaustive W3 owner disposition."""
import collections, copy, hashlib, json
from pathlib import Path
OUT=Path(__file__).resolve().parent
WS=OUT.parents[2]
helpers=(OUT/'census_01.py').read_text()
scope={'__file__':str(OUT/'census_01.py')}
exec(helpers[:helpers.index('\nmanifest=read')],scope)
read,sha,walk,handles,norm,lookup,phases,refs=[scope[n] for n in ('read','sha','walk','handles','norm','lookup','phases','refs')]
A=read(OUT/'census_raw_01.json')
R={r['id']:r for r in A['owners']}

# Complete the sole external-phase owner from the fresh 125-archive census.
ep=WS/'prealpha/world_actions_wa2/coverage_review/external_01/basegame_4_gamedata.archive/ce_cct_cpz_02_phase.questphase.json'
ed=read(ep);eh=handles(ed)
fake={'$type':'questPhaseNodeDefinition','id':-1,'phaseGraph':ed['Data']['RootChunk']['graph'],'phaseInstancePrefabs':[]}
external=phases(fake,'external:root',eh)
R[1]['external_source']=str(ep);R[1]['external_binary_sha256']=sha(Path(str(ep)[:-5]));R[1]['external_phases']=external

# Outside-W3 supplemental candidate 250: no new support admission is approved here.
src=Path(R[246]['source']);d=read(src);hs=handles(d);n=lookup(d['Data']['RootChunk'],'root/24/95',hs)
R[250]={'id':250,'node_path':'root/24/95','source':str(src),'native_binary':R[246]['native_binary'],'native_binary_sha256':R[246]['native_binary_sha256'],
 'prefix':None,'prefab':None,'community_refs':['#ce_arr_ast_122_com'],'spawner_hashes':['3323904054656225535'],'phases':phases(n,'root/24/95',hs),'outside_W3':True}

def meaningful(n):
    return n['$type'] in ('questCombatNodeDefinition','questMovePuppetNodeDefinition','questVehicleNodeDefinition','questEventManagerNodeDefinition','questWorldDataManagerNodeDefinition','questCharacterManagerNodeDefinition')
def allphases(r):return r['phases']+r.get('external_phases',[])
def nodes(p):return (p['payload'].get('phaseGraph') or {}).get('nodes',[])
def phase(r,path):return next(p for p in allphases(r) if p['path']==path)
def typenames(v):return sorted({v['$type'] for _,v in walk(v) if isinstance(v,dict) and '$type' in v})
contracts=[]
def slice_contract(g,path,ids,kind,gate,notes):
    r=R[g];p=phase(r,path);nn={n['id']:n for n in nodes(p)};ids=set(ids)
    assert ids<=set(nn),(g,ids-set(nn))
    selected=[nn[i] for i in sorted(ids)]
    internal=[e for e in p['edges'] if e[0] in ids and e[2] in ids]
    incoming=[e for e in p['edges'] if e[0] not in ids and e[2] in ids]
    outgoing=[e for e in p['edges'] if e[0] in ids and e[2] not in ids]
    assert not any(n['$type'] in ('questSpawnManagerNodeDefinition','questFactsDBManagerNodeDefinition','questCheckpointNodeDefinition','questSceneNodeDefinition') for n in selected),(g,path)
    if kind.startswith('flat_shoot'):
        assert all(e[0]==gate for e in outgoing),(g,outgoing)
        assert not any(e[1]=='CutSource' for e in incoming+outgoing),(g,'boundary cut')
    c={'group':g,'kind':kind,'source':r['source'],'native_binary':r['native_binary'],'native_binary_sha256':r['native_binary_sha256'],
       'owner_path':r['node_path'],'graph_path':path,'node_ids':sorted(ids),'node_count':len(ids),'internal_edges':internal,'internal_edge_count':len(internal),
       'native_incoming_boundary_edges':incoming,'native_outgoing_boundary_edges':outgoing,'entry_gate_id':gate,
       'payload_types':typenames(selected),'dependencies':refs(selected),'nodes':selected,'notes':notes,
       'status':'STATIC_SLICE_CONTRACT_REQUIRES_WRAPPER_AND_DEPENDENCY_VERIFICATION'}
    contracts.append(c);return c

for g,child,outer in [(172,64,65),(173,61,62),(179,61,62)]:
    r=R[g];p=phase(r,r['node_path']+'/'+str(child))
    c=slice_contract(g,p['path'],[n['id'] for n in nodes(p)],'existing_BA1_preserve' if g==179 else 'isolated_shoot_phase',0,
      ['Copy whole native phase object; no DeepCopy of connected graph.','Own lifetime Ready30/NotReady31->Terminating1; outer Ready wait rearm retained.',
       'Qualify only exact community shorthand through manifest community_ref. Preserve security/target references and all other payload.',
       'BA1 group179 must remain unchanged and must not receive a second owner.'])
    c['outer_ready_gate_id']=outer;c['controller_node_id']=child;c['community_refs']=r['community_refs'];c['spawner_hashes']=r['spawner_hashes']
    assert len(c['nodes'])==32 and len(c['internal_edges'])==43

for g,gate,lo,hi in [(246,174,194,230),(289,30,46,73),(250,174,212,239)]:
    r=R[g];p=r['phases'][0];ids=[n['id'] for n in nodes(p) if lo<=n['id']<=hi]+[gate]
    c=slice_contract(g,p['path'],ids,'flat_shoot_action_closure',gate,
      ['Retain exact native CharacterSpawned gate and only action successors; omit its parallel encounter cleanup successor.',
       'No authored NotReady termination in this flat branch: wrapper must cut the entire gate/action branch on community NotReady and safety/support loss.',
       'Rearm only after native community Ready returns; preserve every native timer, hit condition, security condition, permanent cut, and combat target.',
       'Requires target/security default-world resolution before deployment. Outside group250 additionally requires separately verified support owner.'])
    c['community_refs']=r['community_refs'];c['spawner_hashes']=r['spawner_hashes']

for g,ch,ready in [(251,147,145),(253,143,142),(256,27,26)]:
    r=R[g];p=phase(r,r['node_path']+'/'+str(ch))
    c=slice_contract(g,p['path'],[n['id'] for n in nodes(p)],'isolated_vehicle_radio_door_phase',0,
      ['Seven native nodes preserve Ready2, radio3, ForceOpen door4/5, and NotReady6->Terminating1.',
       'No vehicle spawn, mount, AI-role, native fact, scene, reward or invulnerability change.',
       'Use one new owner per W3 group, exact actor/vehicle community entries, support Claimed/Entered/Hold gates, whole-phase cut and Ready rearm.',
       'Vehicle must still belong to the exact existing native community; do not target a player-owned replacement.'])
    c['outer_ready_gate_id']=ready;c['controller_node_id']=ch

# Direct radio/light branches: gate included, but exclude all encounter successors.
direct={98:(29,[30]),122:(12,[13]),199:(23,[19,20,21,22]),204:(27,[24,25]),242:(124,[125]),243:(124,[125]),
252:(124,[125,127,129]),275:(30,[31]),311:(29,[30]),318:(32,[33]),319:(31,[32]),342:(4,[5]),343:(4,[5])}
for g,(gate,acts) in direct.items():
    c=slice_contract(g,R[g]['node_path'],[gate]+acts,'direct_vehicle_ambient_event_branch',gate,
      ['Retain native Spawned/Ready condition; event body applies only to existing exact community vehicle.',
       'No spawn/reset/fact/reward/attitude/mortality operations copied. Outgoing encounter kill/reset branches are intentionally excluded.',
       'Wrap as one issuance per community-ready lifetime; wait NotReady before rearm. Cut pending gate on safety/support loss.',
       'On saved issued owner, resume serialized wait instead of resetting receipt and replaying commands.'])

# Tiny radio phases have no connected terminating output. Their exact event can be
# transplanted with the native outer condition, but do not claim a native rearm loop.
for g,ch,gate in [(280,33,32),(287,31,29),(291,36,29),(305,35,29)]:
    p=phase(R[g],R[g]['node_path']+'/'+str(ch))
    c=slice_contract(g,p['path'],[2],'nested_vehicle_radio_event_only',None,
      ['Copy native radio event2 only. Original tiny phase has no terminating output; do not falsely treat its NotReady/deletion marker as a working rearm path.',
       'Retain separate exact outer Spawned/Ready admission condition; new wrapper must own stream-out cancellation/rearm.',
       'One issuance per ready lifetime, exact native existing vehicle only; no native encounter restart.'])
    c['outer_ready_gate_id']=gate;c['outer_gate_payload']=next(n for n in nodes(R[g]['phases'][0]) if n['id']==gate);c['controller_node_id']=ch

# Mount/deal and stateful secondary graphs are fully inventoried, with explicit
# gates/boundaries and concrete outstanding safety issues rather than type bans.
review=[]
for g in [3,4,203,239,240,296,328,329,343,174,175,176,189,191,214,200,202,210,308,461,256,319]:
    r=R[g]
    issue=[]
    if g in (3,4):issue.append('Actor refs are Corpo Plaza, but all three vehicle refs point into Glen116/cs_deal_com_*; do not silently retarget or issue until cross-owner vehicle identity is proved.')
    if g in (203,239,240,296,328):issue.append('Native phase begins with instant mount assignments then trigger/unmount/remount sequence; copying onto a saved W3 owner can remount actors after its original interaction. Need exact existing mount/vehicle state admission and no replay after combat or a completed deal; plain Ready is insufficient evidence of fresh encounter state.')
    if g==203:issue.append('Native two-community NotReady uses AND, so one missing community does not terminate; wrapper must handle either missing dependency safely without mutating the native subtree.')
    if g in (296,328):issue.append('Native tiny mount phases have no terminating output; require new lifetime boundary. Separate SetSecuritySystemState SAFE is killed-condition cleanup and must not run on admission.')
    if g==308:issue.append('Only extra event sets security SAFE after CharacterKilled18; it is defeat cleanup, not ambient startup, and must retain defeat transition/lifecycle ownership.')
    if g==329:issue.append('Attitude writes depend on mq008_v_starts_competition>=1 and v_offends_boss>=1; both may be true. Preserve native story owner/ordering; generic action entry cannot decide the correct final faction.')
    if g==343:issue.append('Nested24 sets vehicles Invulnerable, disables all door interactions and makes gangers friendly. No paired restoration in subtree; not a generic neutral animation fix. Independent radio branch is separately extractable.')
    if g in (174,175,176,189,191,214):issue.append('DANGEROUS security transition waits q110_var_maglev_escape>0. This is story-dependent security state, not a repeated NPC command. Requires exact current security-area/state ownership before reapplication.')
    if g==175:issue.append('Second event24 DISABLED is reached after Deactivate23 during encounter retirement; never pair it with startup DANGEROUS on a new action owner.')
    if g in (200,202,210,461):issue.append('TogglePrefabVariant shows environment assets, not an AI action. Can be separated from Reactivate, but first establish exact default-world prefab/variant ownership and save semantics; do not activate an unreviewed quest prefab.')
    if g==256:issue.append('Native inner Ready2/NotReady6 refers to group251 ce_arr_std_113, but action targets use own #cs_std_arr_124_com. Exact subtree copy is not an own-community lifecycle; explicit guard dependency proof/substitution or withholding required.')
    if g==319:issue.append('Native Spawned31 gate references $/decoset/area/area_openworld/#cs_goons_cars/cs_goons_cars_com rather than its actual ce_std_rcr_146 community. Resolve exact native mapping before copying or substituting its admission condition.')
    review.append({'group':g,'owner_path':r['node_path'],'issues':issue,'phase_paths':[p['path'] for p in r['phases']],
      'operations':[{'path':p['path']+'/'+str(n['id']),'payload':n,'incoming':[e for e in p['edges'] if e[2]==n['id']], 'outgoing':[e for e in p['edges'] if e[0]==n['id']]} for p in r['phases'] for n in nodes(p) if meaningful(n)]})

for c in contracts:
    c['review_issues']=[i for r in review if r['group']==c['group'] for i in r['issues']]
    if c['group'] in (256,319):c['status']='NATIVE_GUARD_MISMATCH_REQUIRES_EXPLICIT_DEPENDENCY_RESOLUTION'
    if c['group']!=250:
        c['community_refs']=R[c['group']]['community_refs'];c['spawner_hashes']=R[c['group']]['spawner_hashes']

owners=[]
for g,r in sorted(R.items()):
    if r.get('outside_W3'):continue
    pp=allphases(r);nn=[n for p in pp for n in nodes(p)]
    action=[n for n in nn if meaningful(n)]
    facts=[n for n in nn if n['$type']=='questFactsDBManagerNodeDefinition']
    cc=[c for c in contracts if c['group']==g]
    if g==179:category='existing_BA1_preserved'
    elif g in (172,173):category='isolated_shooting_candidates'
    elif g in (246,289):category='flat_shooting_candidates'
    elif g==1:category='external_encounter_controller_review'
    elif cc:category='secondary_vehicle_ambient_candidates'
    elif action:category='stateful_or_mount_dependency_review'
    elif facts:category='native_encounter_fact_lifecycle_only'
    else:category='no_bespoke_action_controller_found'
    owners.append({'group':g,'prefix':r['prefix'],'owner_path':r['node_path'],'source':r['source'],'category':category,
     'phase_paths':[p['path'] for p in pp], 'action_nodes':[{'path':p['path']+'/'+str(n['id']),'type':n['$type'],'payload_types':typenames(n),'references':refs(n)} for p in pp for n in nodes(p) if meaningful(n)],
     'fact_write_nodes':[{'path':p['path']+'/'+str(n['id']),'payload':n} for p in pp for n in nodes(p) if n['$type']=='questFactsDBManagerNodeDefinition'],
     'contract_kinds':[c['kind'] for c in cc], 'review_issues':[x for rv in review if rv['group']==g for x in rv['issues']]})
    if g==1:owners[-1]['review_issues']=['External root/nested2 owns Reactivate/ResetKillCount, loot variants78/85, completion fact88 and checkpoints16/83. No AI command subtree. Do not rehost its encounter or reward/completion lifecycle for ambient actions.']
assert len(owners)==237 and len({r['group'] for r in owners})==237

# Verify homologous Coastview phase payload equality after substituting NodeRefs
# and the outer phase id only. Entries, functions, weights, timers and edges stay exact.
def normalized_shooter(g):
    c=next(c for c in contracts if c['group']==g);v=copy.deepcopy(c['nodes'])
    for _,x in walk(v):
        if isinstance(x,dict) and x.get('$type')=='NodeRef' and x.get('$value') not in ('0','#player'):x['$value']='<native-ref>'
    return v,c['internal_edges']
assert normalized_shooter(172)==normalized_shooter(179)
assert normalized_shooter(173)==normalized_shooter(179)

counts=dict(collections.Counter(o['category'] for o in owners))
out={'status':'PASS_237_OWNER_ACTION_CENSUS_STATIC_CONTRACTS_NOT_DEPLOYMENT_APPROVAL','owners':237,'cohort_counts':counts,
 'contracts':contracts,'review':review,'coverage':owners,'external_group1':{'source':str(ep),'binary_sha256':R[1]['external_binary_sha256'],'phases':external},
 'source_pins':A['sources'],'manifest_sha256':A['manifest_sha256'],'raw_census_sha256':sha(OUT/'census_raw_01.json'),
 'notes':['No general claim that every NPC needs a shooting controller. Five W3 shooting owners found; existing BA1 excluded from new ownership.',
          'All 237 W3 owners covered, including flat root nodes and sole external resource. Outside250 supplemental only.',
          'Secondary action slices do not authorize copying full encounter roots or reset/kill/reward/scene paths.',
          'Current winner/environment proofs and fresh binary readback remain separate deployment gates.'],
 'game_writes':0,'save_writes':0}
(OUT/'action_contracts_01.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
lines=['# W3 native action-controller census','',f'All 237 W3 owners audited. Source/graph evidence only; no game or save writes.','', '| Cohort | Owners |','|---|---:|']
for k,v in counts.items():lines.append(f'| {k} | {v} |')
lines+=['','Every row retains exact source node paths, payload types and reference dependencies in action_contracts_01.json.','', '| Group | Native owner | Disposition | Candidate slices |','|---:|---|---|---|']
for o in owners:lines.append(f"| {o['group']} | {o['owner_path']} | {o['category']} | {', '.join(o['contract_kinds'])} |")
(OUT/'coverage_01.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'cohort_counts':counts,'contracts':len(contracts),'contract_counts':dict(collections.Counter(c['kind'] for c in contracts))},indent=2))
