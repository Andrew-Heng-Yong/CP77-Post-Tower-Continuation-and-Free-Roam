"""Bind native 256/319 predicates to their own proved actors and registry IDs."""
from pathlib import Path
from hashlib import sha256
import json
H=Path(__file__).resolve().parent;W=H.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
manifest_path=W/'prealpha/world_workspots_w2/manifest_03.json'
census_path=H.parent/'native_review/census_raw_02.json'
manifest=read(manifest_path);native=read(census_path)
registry=read(H/'registry_fresh_01/report_01.json');refproof=read(H/'community_ref_proof_01.json');hashes=refproof['hashes']
checks=[]
def check(label,value):checks.append(label);assert value,label
check('All125 current archives scanned for exact community registry',registry['archives']==125)
check('Only official base+EP1 registry winners',sorted(Path(r['archive']).name for r in registry['hits'])==['basegame_3_nightcity.archive','ep1_1_nightcity.archive'])
registries={Path(r['archive']).name:read(Path(r['json']))['communities'] for r in registry['hits']}
check('Fresh base+EP1 selected complete registry definitions identical',registries['basegame_3_nightcity.archive']==registries['ep1_1_nightcity.archive'])
communities={r['communityId']['entityId']['hash']:r for r in registries['ep1_1_nightcity.archive']}
groups=[];corrections=[]
for gid in (256,319):
    m=next(r for r in manifest['groups'] if r['id']==gid);n=next(r for r in native['owners'] if r['id']==gid)
    own=m['community_refs'][0];identity=m['spawner_hashes'][0]
    check(str(gid)+': exact own community engine hash equals W3 identity',hashes[own]==identity)
    c=communities[identity]
    entries={e['Data']['entryName']['$value']:e['Data'] for e in c['template']['Data']['entries']}
    quantities={key:sum(t['quantity'] for p in e['phases'] for t in p['Data']['timePeriods']) for key,e in entries.items()}
    check(str(gid)+': native car_01 actor is authored vehicle',entries['car_01']['characterRecordId']['$value'].startswith('Vehicle.') and quantities['car_01']==1)
    check(str(gid)+': registry is streamable and no automatic activation changed',c['communityAreaType']=='Streamable' and all(r['entryActiveOnStart']==0 for r in c['entriesInitialState']))
    bypath={p['path']:p for p in n['phases']}
    if gid==256:
        check('256 exact five native community entries',set(entries)=={'car_01','car_02','goon1','goon2','goon3'})
        check('256 native car_02 is a single authored vehicle',entries['car_02']['characterRecordId']['$value'].startswith('Vehicle.') and quantities['car_02']==1)
        alias=own+';#cs_std_arr_124_com'
        check('256 current registry declares native actor shorthand on exact own community',all(alias in r['registry_refs'] for r in refproof['rows']))
        check('256 declared alias retains exact own community hash',hashes[alias]==identity)
        inner=bypath[n['node_path']+'/27'];nodes={r['id']:r for r in inner['payload']['phaseGraph']['nodes']}
        check('256 radio addresses authored car_02 via proved native shorthand',nodes[3]['objectRef']['reference']['$value']=='#cs_std_arr_124_com' and [r['$value'] for r in nodes[3]['objectRef']['names']]==['car_02'])
        for node in (4,5):check('256 door action addresses authored car_02 '+str(node),nodes[node]['type']['vehicleRef']['reference']['$value']=='#cs_std_arr_124_com' and [r['$value'] for r in nodes[node]['type']['vehicleRef']['names']]==['car_02'])
        targets=[(n['node_path'],26,'questSpawnerReady_ConditionType'),(n['node_path']+'/27',2,'questSpawnerReady_ConditionType'),(n['node_path']+'/27',6,'questSpawnerNotReady_ConditionType')]
        for graph,node,typename in targets:
            payload=next(r for r in bypath[graph]['payload']['phaseGraph']['nodes'] if r['id']==node)['condition']['type']
            old=payload['spawnerReference']['$value']
            check('256 predicate is wrong113 community '+str(node),'/#ce_arr_std_113/' in old and payload['$type']==typename and payload['communityEntryNames']==[] and hashes[old]!=identity)
            corrections.append({'group':gid,'graph':graph,'node':node,'field':'condition.type.spawnerReference','old':old,'old_hash':hashes[old],'new':own,'new_hash':identity,'condition_type_unchanged':typename,'entry_names_unchanged':[]})
    else:
        authored=own.replace('/rancho_coronado/','/#rancho_coronado/')
        check('319 fresh native authored #rancho and registry spelling hash-identical',hashes[authored]==identity)
        nodes={r['id']:r for r in bypath[n['node_path']]['payload']['phaseGraph']['nodes']}
        check('319 native radio car_01 actor uses exact own registry identity',hashes[nodes[32]['objectRef']['reference']['$value']]==identity and [r['$value'] for r in nodes[32]['objectRef']['names']]==['car_01'])
        spawn=nodes[31]['condition']['type'];old=spawn['objectRef']['reference']['$value']
        names=[r['$value'] for r in spawn['objectRef']['names']]
        check('319 native Spawned actor names exist without guessing',names==['goon1','goon3'] and set(names)<=entries.keys())
        check('319 native required seven actors exactly match authored4+3 quantities',quantities['goon1']==4 and quantities['goon3']==3 and spawn['comparisonParams']=={'$type':'questComparisonParam','comparisonType':'GreaterOrEqual','count':7,'entireCommunity':0})
        check('319 Spawned targets stale decoset and different identity',old.startswith('$/decoset/') and hashes[old]!=identity)
        corrections.append({'group':gid,'graph':n['node_path'],'node':31,'field':'condition.type.objectRef.reference','old':old,'old_hash':hashes[old],'new':own,'new_hash':identity,'condition_type_unchanged':spawn['$type'],'entry_names_unchanged':names,'comparison_unchanged':spawn['comparisonParams']})
        nr=nodes[33]['condition']['type']
        check('319 NotReady uses same stale decoset guard',nr['spawnerReference']['$value']==old and nr['$type']=='questSpawnerNotReady_ConditionType' and nr['communityEntryNames']==[])
        corrections.append({'group':gid,'graph':n['node_path'],'node':33,'field':'condition.type.spawnerReference','old':old,'old_hash':hashes[old],'new':own,'new_hash':identity,'condition_type_unchanged':nr['$type'],'entry_names_unchanged':[]})
    groups.append({'id':gid,'community':own,'spawner_hash':identity,'entries':[{'name':key,'record':e['characterRecordId']['$value'],'quantity':quantities[key]} for key,e in entries.items()],
                   'native_actor_binding_proved':True,'fresh_registry_item':c})
pins=[manifest_path,census_path,H/'registry_fresh_01/report_01.json',H/'community_ref_proof_01.json',H/'registry_fresh_01.ps1',H/'community_refs_01.ps1',H/'assess_community_rebinds_01.py']
for r in registry['hits']:pins.extend([Path(r['raw']),Path(r['json'])])
result={'status':'PASS_EXACT_256_319_COMMUNITY_REBINDS','checks_passed':len(checks),'checks':checks,'groups':groups,'required_candidate_corrections':corrections,
        'limits':['Group256 outer native node26 belongs to its parent; apply this correction if that gate is copied, or make the new wrapper Ready guard use the exact same own community.',
                  'The patch changes NodeRefs only. Native actor names, phase conditions, vehicle actions and319 comparison count7 remain unchanged.',
                  'Fresh authored registry entries prove identities and counts, not current saved runtime spawn counts or live action completion.'],
        'game_writes':0,'save_writes':0,'candidate_edits':0,'pins':[{'path':str(p),'sha256':digest(p)} for p in pins]}
out=H/'community_rebinds_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks_passed':len(checks),'corrections':corrections,'sha256':digest(out)},indent=2))
