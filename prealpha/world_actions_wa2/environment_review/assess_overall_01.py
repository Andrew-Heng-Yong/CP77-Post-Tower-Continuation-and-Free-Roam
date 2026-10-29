"""Bind every selected action actor to fresh registry data and all shooting targets to world proof."""
from pathlib import Path
from hashlib import sha256
import copy,json
H=Path(__file__).resolve().parent; C=H.parent/'candidate_01'; W=H.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
checks=[];pins=[]
def check(label,value):
    assert value,label
    checks.append(label)
def pin(p):
    p=Path(p)
    if not p.is_absolute():p=W/p
    pins.append(p.resolve())
def walk(x,path='$'):
    if isinstance(x,dict):
        yield path,x
        for k,v in x.items():yield from walk(v,path+'.'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,path+'['+str(i)+']')

cohort=read(C/'cohort_proof_01.json');semantic=read(H.parent/'native_review/final_assessment_01.json')
contracts=read(H.parent/'native_review/action_contracts_02.json')
registry_report=read(H/'registry_all_02/report_01.json');registry_census=read(H/'registry_fresh_01/report_01.json')
candidate_inputs=read(H/'candidate_refs_input_01.json');candidate_hashes=read(H/'candidate_refs_hashes_01.json')
hashes=candidate_hashes['hashes']
environments=read(H/'assessment_01.json');rebinds=read(H/'community_rebinds_01.json')
support=read(H.parent/'coverage_review/support_assessment_01.json')
check('Frozen semantic cohort independently passes',semantic['status']=='PASS_INDEPENDENT_26_RESOURCE_WA2_SEMANTIC_COHORT')
check('Exactly25 new action owners plus250 support',len(cohort['resources'])==26 and len(cohort['shooting_groups'])==5 and len(cohort['vehicle_groups'])==20)
check('Semantic cohort matches frozen source cohort',semantic['resources']==cohort['resources'])
check('Candidate reference input pins frozen cohort',candidate_inputs['cohort_sha256']==digest(C/'cohort_proof_01.json'))
check('Engine hashes pin exact reference inputs',candidate_hashes['input_sha256']==digest(H/'candidate_refs_input_01.json'))
check('Fresh current125 archive registry census has only official base andEP1 winners',registry_census['archives']==125 and sorted(Path(r['archive']).name for r in registry_census['hits'])==['basegame_3_nightcity.archive','ep1_1_nightcity.archive'])
check('Expanded registry proof pins same census',registry_report['registry_census_sha256']==digest(H/'registry_fresh_01/report_01.json'))
check('Expanded registry proof pins fresh native contracts',registry_report['contract_sha256']==digest(H.parent/'native_review/action_contracts_02.json'))
registries=[]
for row in registry_report['rows']:
    check('Fresh registry bytes pinned '+Path(row['archive']).name,digest(Path(row['raw']))==row['raw_sha256'] and digest(Path(row['json']))==row['json_sha256'])
    registries.append(read(Path(row['json']))['communities']);pin(row['raw']);pin(row['json'])
check('All25 complete native registry definitions identical in base andEP1',len(registries)==2 and len(registries[0])==25 and registries[0]==registries[1])
communities={r['communityId']['entityId']['hash']:r for r in registries[0]}
contract_by_id={r['group']:r for r in contracts['contracts']}
groups=[];all_actor_refs=0;vehicle_refs=0;shooting_refs=0
def valid_actor(identity,entry_map,reference,names,vehicle=False):
    return hashes.get(reference)==identity and bool(names) and all(n in entry_map for n in names) and (not vehicle or all(entry_map[n]['characterRecordId']['$value'].startswith('Vehicle.') for n in names))
for selected in candidate_inputs['groups']:
    gid=selected['group'];contract=contract_by_id[gid];identity=contract['spawner_hashes'][0]
    p=Path(selected['path']);check(str(gid)+': exact final binary readback JSON pinned',digest(p)==selected['sha256']);pin(p)
    data=read(p);community=communities[identity]
    entries={r['Data']['entryName']['$value']:r['Data'] for r in community['template']['Data']['entries']}
    actor_refs=[];own_refs=[];empty_refs=0;player_refs=0
    for path,obj in walk(data):
        if obj.get('$type')=='gameEntityReference':
            ref=obj['reference']['$value'];names=[n['$value'] for n in obj['names']]
            if ref=='#player':player_refs+=1;continue
            if ref in ('0','') and not names:empty_refs+=1;continue
            check(str(gid)+': actor/condition community resolves exact registered spawner '+path,hashes.get(ref)==identity)
            own_refs.append(ref)
            if names:
                check(str(gid)+': all named actors exist in exact community '+path,valid_actor(identity,entries,ref,names))
                is_vehicle=gid in cohort['vehicle_groups'] and ('.objectRef' in path or '.vehicleRef' in path) and '.condition.' not in path
                if is_vehicle:
                    check(str(gid)+': event/door targets authored vehicle record '+path,valid_actor(identity,entries,ref,names,True));vehicle_refs+=1
                if gid in cohort['shooting_groups'] and '.entityReference' in path:
                    check(str(gid)+': AI commands target authored character record '+path,all(entries[n]['characterRecordId']['$value'].startswith('Character.') for n in names));shooting_refs+=1
                actor_refs.append({'path':path,'reference':ref,'names':names,'records':[entries[n]['characterRecordId']['$value'] for n in names]})
        if obj.get('$type') in ('questSpawnerReady_ConditionType','questSpawnerNotReady_ConditionType'):
            check(str(gid)+': readiness guard uses own registry community '+path,hashes.get(obj['spawnerReference']['$value'])==identity)
    check(str(gid)+': native named actor actions actually checked',bool(actor_refs))
    native_names={n['$value'] for _,obj in walk(contract['nodes']) if obj.get('$type')=='gameEntityReference' and obj['reference']['$value']!='#player' for n in obj['names']}
    check(str(gid)+': every named native actor retained in registry',native_names<=entries.keys())
    all_actor_refs+=len(actor_refs)
    groups.append({'group':gid,'spawner_hash':identity,'readback_sha256':selected['sha256'],'native_actor_names':sorted(native_names),'candidate_actor_refs':actor_refs,'empty_native_optional_refs':empty_refs,'player_refs':player_refs,'entry_records':{name:e['characterRecordId']['$value'] for name,e in entries.items()}})

check('Four original shooting environments independently resolve exact city targets/security',environments['status']=='PASS_STATIC_ENVIRONMENTS_WITH_REQUIRED_246_SECURITY_REBIND' and {r['id'] for r in environments['groups']}=={172,173,246,289})
check('Fifth shooting environment250 resolves own default-world targets/security',support['status']=='PASS_250_SUPPORT_IDENTITY_ENVIRONMENT__130_WITHHELD_UNRESOLVED_WORLD' and support['candidate250']['spawner_hash']=='3323904054656225535')
check('256 and319 bounded corrections have native exact actor evidence',rebinds['status']=='PASS_EXACT_256_319_COMMUNITY_REBINDS')
corrections=environments['required_candidate_corrections']+rebinds['required_candidate_corrections']
for correction in corrections:
    selected=next(r for r in candidate_inputs['groups'] if r['group']==correction['group'])
    values={o['$value'] for _,o in walk(read(Path(selected['path']))) if o.get('$type')=='NodeRef'}
    check(str(correction['group'])+': repaired candidate contains corrected target hash '+str(correction['node']),any(hashes.get(v)==correction['new_hash'] for v in values) and correction['old'] not in values and not any(hashes.get(v)==correction['old_hash'] for v in values))

# Independent negative controls verify identity/name/type rejection, not builder output shape.
first=next(g for g in groups if g['group']==256);entry_map={r['Data']['entryName']['$value']:r['Data'] for r in communities[first['spawner_hash']]['template']['Data']['entries']};good=first['candidate_actor_refs'][0]
negative_controls={
 'unknown actor name rejected':not valid_actor(first['spawner_hash'],entry_map,good['reference'],['not_an_authored_entry']),
 'sibling community rejected':not valid_actor('964700094188757487',entry_map,good['reference'],good['names']),
 'character cannot stand in for vehicle event':not valid_actor(first['spawner_hash'],entry_map,good['reference'],['goon1'],True),
 'unqualified stale community rejected':not valid_actor(first['spawner_hash'],entry_map,'$/decoset/area/area_openworld/#cs_goons_cars/cs_goons_cars_com',['car_01'])}
for label,passed in negative_controls.items():check('Negative control: '+label,passed)

for relative in ['assessment_01.json','community_rebinds_01.json','registry_all_02/report_01.json','registry_fresh_01/report_01.json','candidate_refs_input_01.json','candidate_refs_hashes_01.json','registry_all_02.ps1','prepare_candidate_refs_01.py','candidate_refs_01.ps1','assess_overall_01.py']:
    pin(H/relative)
for p in [C/'cohort_proof_01.json',H.parent/'native_review/final_assessment_01.json',H.parent/'native_review/action_contracts_02.json',H.parent/'coverage_review/support_assessment_01.json']:pin(p)
for proof in (environments,rebinds):
    for item in proof['pins']:
        p=Path(item['path']);check('Existing environment evidence remains pinned '+str(p),digest(p)==item['sha256']);pin(p)
for item in support['evidence']:
    p=W/item['path'];check('250 environment evidence remains pinned '+str(p),digest(p)==item['sha256']);pin(p)
result={'status':'PASS_ALL_25_NEW_ACTION_ENVIRONMENTS_AND_NATIVE_ACTORS_STATIC_ONLY','checks_passed':len(checks),'checks':checks,'shooting_groups':cohort['shooting_groups'],'vehicle_groups':cohort['vehicle_groups'],'groups':groups,'candidate_named_actor_references_checked':all_actor_refs,'vehicle_event_or_door_references_checked':vehicle_refs,'shooting_command_references_checked':shooting_refs,'negative_controls':negative_controls,'required_corrections_verified':corrections,'registry_communities':25,'registry_archive_winners':['basegame_3_nightcity.archive','ep1_1_nightcity.archive'],'resources':cohort['resources'],'limits':['Static source/environment proof does not establish streamed live actors, undamaged targets, persisted security state or runtime/reload behavior.','Native actor aliases are explicitly qualified to each reviewed own community in the candidate; candidate engine hashes and registered entry names are checked directly.','Two unrelated nearby sector copies remain undecodable; all actual selected shooting dependency sectors are decoded.','Only the25 selected action owners plus new250 support are added. ExistingBA1 group179 remains byte-preserved; other NPC families are outside this proof.'],'game_writes':0,'save_writes':0,'candidate_edits':0,'pins':[{'path':str(p),'sha256':digest(p)} for p in dict.fromkeys(pins)]}
out=H/'overall_assessment_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'actor_refs':all_actor_refs,'vehicle_refs':vehicle_refs,'shooting_refs':shooting_refs,'sha256':digest(out)},indent=2))
