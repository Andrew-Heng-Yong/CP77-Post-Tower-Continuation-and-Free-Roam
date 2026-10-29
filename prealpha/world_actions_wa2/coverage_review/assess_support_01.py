"""Independent support/identity/environment proof for outside-W3 shooter250."""
import collections,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;WS=OUT.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
checks=[]
def check(name,v):
    checks.append({'name':name,'pass':bool(v)});assert v,name
source=read(OUT/'shooting_sources_01/report_01.json')
registry=read(OUT/'registry_01/report_01.json')
coverage=read(OUT/'coverage_01.json')
row=next(r for r in coverage['rows'] if r['candidate_index']==250)
prefab=row['full_ref'];community=prefab+'/#cs_std_arr_goons_shooting_com';compound=community+';#ce_arr_ast_122_com'
check('125 installed archives scanned',source['archives']==125)
check('No mod overrides in exact shooting resource census',all('\\archive\\pc\\mod\\' not in r['archive'].lower() for r in source['hits']))
old_support=WS/'diagnostics/world_npc_idle_20261026_02/families/decoded_02/quest_b6fab76541bd1bdb/nodes.json'
support=read(old_support)
hits=[r for r in source['hits'] if r['depot'].endswith('quest_b6fab76541bd1bdb.streamingsector')]
check('Single current native support sector matches decoded support',len(hits)==1 and hits[0]['sha256']==support['raw_sha256']==sha(Path(hits[0]['raw'])))
types=collections.Counter(n['definition']['$type'] for n in support['nodes'])
check('Six support nodes only',types=={'worldAISpotNode':3,'worldCrowdNullAreaNode':1,'worldTriggerAreaNode':1,'worldGuardAreaNode':1})
check('Every exact support member belongs to authored prefab',all(r.startswith(prefab+'/') for r in support['node_refs']) and all(p['quest_ref'].startswith(prefab+'/') for p in support['placements']))
check('No population spawner, entity, device, fact or scene payload in support',not any(any(x in str(v.get('$type','')) for x in ['PopulationSpawner','worldEntityNode','worldDeviceNode','FactsDB','Scene']) for v in walk(support['nodes'])))
check('Trigger notifier is quest notification only',all(v['$type']=='questTriggerNotifier_Quest' for n in support['nodes'] for h in n['definition'].get('notifiers',[]) for v in [h['Data']]))
alias_rows=[];reg_rows=[]
for archive in ['basegame_3_nightcity.archive','ep1_1_nightcity.archive']:
    z=read(OUT/('shooting_sources_01/'+archive+'/always_loaded_0.streamingsector.json'))['Data']['RootChunk']
    aliases=[r['$value'] for r in z['nodeRefs'] if r.get('$value')==compound]
    check(archive+': one exact native compound alias',len(aliases)==1)
    alias_rows.append({'archive':archive,'compound_ref':aliases[0],'canonical_ref':community})
    r=read(OUT/('registry_01/'+archive+'_3323904054656225535.json'))
    check(archive+': exact community ID',r['communityId']['entityId']['hash']=='3323904054656225535')
    check(archive+': three active default entries',[(v['entryName']['$value'],v['initialPhaseName']['$value'],v['entryActiveOnStart']) for v in r['entriesInitialState']]==[(e,'default',1) for e in ('goon1','goon2','goon3')])
    entries=[h['Data'] for h in r['template']['Data']['entries']]
    check(archive+': same three native template entries', [e['entryName']['$value'] for e in entries]==['goon1','goon2','goon3'])
    check(archive+': one Day actor per entry, native markings',all(len(e['phases'])==1 and e['phases'][0]['Data']['phaseName']['$value']=='default' and len(e['phases'][0]['Data']['timePeriods'])==1 and e['phases'][0]['Data']['timePeriods'][0]['quantity']==1 and e['phases'][0]['Data']['timePeriods'][0]['hour']=='Day' for e in entries))
    reg_rows.append(r)
check('Base and EP1 native registry definitions identical',reg_rows[0]==reg_rows[1])
check('Canonical native NodeRef hash verified',registry['hashes']['250']=='3323904054656225535')

envprefab='$/03_night_city/#c_santo_domingo/arroyo/arr_cs_prefab4OUIGHQ/cs_goons_shooting_env_prefabNV7JR4Q/'
suffixes=['target_object_001_prefabG6AJLQI','target_object_prefabG6AJLQI','cs_goons_shooting_sec_system','cs_goons_shooting_sec_area']
env=[];descriptors=[]
for archive in ['basegame_3_nightcity.archive','ep1_1_nightcity.archive']:
    stem='shooting_decode_01/'+archive+'_exterior_0_-17_0_0.streamingsector'
    defs={r['node']:r['definition'] for r in read(OUT/(stem+'.nodes.json'))['nodes']}
    positions=read(OUT/(stem+'.placements.json'))['placements'];selected=[]
    for suffix in suffixes:
        matches=[p for p in positions if p['quest_ref']==envprefab+suffix]
        check(archive+': unique dependency '+suffix,len(matches)==1)
        placement={k:v for k,v in matches[0].items() if k!='id'}
        selected.append({'placement':placement,'definition':defs[placement['node']]})
    block=read(OUT/('shooting_sources_01/'+archive+'/all.streamingblock.json'))['Data']['RootChunk']
    desc=next(d for d in block['descriptors'] if d['data']['DepotPath']['$value'].endswith('exterior_0_-17_0_0.streamingsector'))
    check(archive+': environment is default Exterior, no quest prefab',desc['category']=='Exterior' and desc['questPrefabNodeRef']['$value']=='0')
    check(archive+': variants belong to separate card environment',all('cs_goons_cards_env_prefabW7BSSAQ' in v['nodeRef']['$value'] for v in desc['variants']))
    env.append(selected);descriptors.append(desc)
check('Base+EP1 environment selected definitions and placements equal',env[0]==env[1])
check('Base+EP1 exterior ownership registration equal',all(descriptors[0][k]==descriptors[1][k] for k in descriptors[0] if k!='variants'))
def variant_semantics(d):
    return sorted(({k:v for k,v in x.items() if k!='rangeIndex'} for x in d['variants']),key=lambda x:x['variantId'])
check('Unrelated card variants differ only in range order',variant_semantics(descriptors[0])==variant_semantics(descriptors[1]))
check('Both targets use native AI target object',all(r['definition']['entityTemplate']['DepotPath']['$value']==r'base\gameplay\ai\ai_objects\target_object.ent' for r in env[1][:2]))
check('Native security system references exact community alias and exact area',{v['$value'] for v in walk(env[1][2]['definition']['deviceConnections']) if v.get('$type')=='NodeRef'} >= {'#ce_arr_ast_122_com',envprefab+'cs_goons_shooting_sec_area'})
check('Source phase current single winner equals reviewed native', len([r for r in source['hits'] if r['depot'].endswith('ce_std_arr_phase.questphase')])==1 and next(r for r in source['hits'] if r['depot'].endswith('ce_std_arr_phase.questphase'))['sha256']==sha((WS/row['source']).with_suffix('')))
check('250 has no existing W3 support admission', not row['existing_W3_shared_community_owners'])
check('130 all four explicit sector path probes absent',all(not any(h['depot']==v['resource'] for h in source['hits']) for v in source['candidate130_variants']))
check('130 exact community hash absent from both current registries',all(not any(r['community_id']==registry['hashes']['130'] for r in a['found']) for a in registry['rows']))

pins=[OUT/'shooting_sources_01/report_01.json',OUT/'registry_01/report_01.json',old_support,OUT/'coverage_01.json']
pins += list((OUT/'registry_01').glob('*_3323904054656225535.json'))
pins += list((OUT/'shooting_decode_01').glob('*exterior_0_-17_0_0.streamingsector.*json'))
assessment={'status':'PASS_250_SUPPORT_IDENTITY_ENVIRONMENT__130_WITHHELD_UNRESOLVED_WORLD',
 'checks_passed':len(checks),'checks':checks,'candidate250':{
 'native_owner_path':'root/24/95','prefab':prefab,'native_binary_sha256':next(r['sha256'] for r in source['hits'] if r['depot'].endswith('ce_std_arr_phase.questphase')),
 'support_sector':hits[0],'support_node_types':dict(types),'community_ref':community,'compound_alias':compound,'spawner_hash':'3323904054656225535','entries':['goon1','goon2','goon3'],'entry_phase':'default','quantity_per_entry':1,'time_period':'Day',
 'environment_sector':r'base\worlds\03_night_city\_compiled\default\exterior_0_-17_0_0.streamingsector','environment_nodes':env[1],'environment_registration':descriptors[1],
 'support_recommendation':'Eligible for an explicit new support owner using the existing W3 exact living-actor/spawner/active-entry matching and two settled safe samples. Native support sector is copied byte-exact; no community activation/reset is needed. Action controller still requires independent isolated branch lifecycle verification before inclusion.',
 'native_caveats':['Guard-area relative reference is ~/../cs_goons_shooting_com although actual canonical community segment is #cs_std_arr_goons_shooting_com; preserve authored support bytes.', 'Native security connection class labels appear reversed: SecurityAreaControllerPS lists community aliases, CommunityProxyPS lists the absolute area. Preserve source and do not infer live combat detection correctness from these labels.']},
 'candidate130':{'native_owner_path':'root/24/21','native_binary_sha256':next(r['sha256'] for r in source['hits'] if r['depot'].endswith('ce_hey_rey_phase.questphase')),'community_hash':registry['hashes']['130'],'sector_probes':source['candidate130_variants'],'registry_counts':[{'archive':r['archive'],'entries':r['registry_entries']} for r in registry['rows']], 'decision':'WITHHELD. Authored action graph exists, but exact support resource and exact community registry identity are absent in bounded fresh scans. Do not fabricate actors/support or remap this graph onto another community.'},
 'limitations':['Static native source proof is not live runtime/reload proof.','This audit does not authorize full encounter replay or native fact/kill count resets.','Selected exterior source comparisons omit cooker placement IDs only; exact NodeRefs/node indices/types and positions agree.','Base and EP1 exterior registrations differ in range order of three unrelated card-environment variants; their state semantics and all exterior ownership fields agree.'],
 'game_writes':0,'save_writes':0,'implementation_changes':0,
 'evidence':[{'path':str(p.relative_to(WS)),'sha256':sha(p)} for p in pins]}
dest=OUT/'support_assessment_01.json';assert not dest.exists();dest.write_text(json.dumps(assessment,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':assessment['status'],'checks_passed':len(checks),'sha256':sha(dest)},indent=2))
