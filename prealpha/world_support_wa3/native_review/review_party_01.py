import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

source=ROOT/'initial_native_01/basegame_3_nightcity.archive/dancefloor_cs_goons_rave_party.scene.json'
doc=read(source);scene=doc['Data']['RootChunk']
nodes={x['Data']['nodeId']['id']:x['Data'] for x in scene['sceneGraph']['Data']['graph']}
edges=[]
for i,n in nodes.items():
    for s in n.get('outputSockets',[]):
        for d in s['destinations']:
            edges.append([i,s['stamp']['name'],s['stamp']['ordinal'],d['nodeId']['id'],d['isockStamp']['name'],d['isockStamp']['ordinal']])
types={x.get('$type') for x in walk(scene)}
checks=[]
def check(name,ok):
    checks.append({'name':name,'pass':bool(ok)})
    assert ok,name
check('20 authored nodes and22 edges',len(nodes)==20 and len(edges)==22)
check('No NPC scene actors',scene['actors']==[])
check('No native progress, reward, spawn or persistent-device operation',not any(any(y in t for y in ['FactsDBManager','SetVar_Node','Journal','Reward','SpawnManager','InteractiveObjectManager']) for t in types if t))
check('Optional dance choice',nodes[6]['options'][0]['caption']['$value']=='dance' and len(nodes[6]['options'])==1)
check('Only selected choice output enters HUD and dance audio',[(x[3]) for x in edges if x[0]==6]==[108,121])
def quest(i):return nodes[i]['questNode']['Data']
add=quest(71)['type']['Data'];rem=quest(72)['type']['Data']
check('Restriction removal matches same source and exact IDs',add['action']=='AddRestriction' and rem['action']=='RemoveRestriction' and add['restrictionIDs']==rem['restrictionIDs'] and add['source']==rem['source'])
check('Native full-gameplay exit tier',quest(57)['type']['Data']['tier']=='Tier1_FullGameplay')
check('HUD visibility restored',quest(108)['type']['Data']['visibility']=='ForceHide' and quest(110)['type']['Data']['visibility']=='TierVisibility')
check('Audio mix start/stop paired',quest(121)['type']['Data']['mixSignpost']['$value']=='dance_start' and quest(124)['type']['Data']['mixSignpost']['$value']=='dance_stop')
check('Only player workspot commands',all(quest(i)['entityReference']['reference']['$value']=='#player' for i in [135,146]))
check('Native stop workspot on exit',quest(135)['paramsV1']['Data']['function']=='StopWorkspot')
check('Four movement-axis exit conditions',len([x for x in walk(quest(65)) if x.get('$type')=='questInputAction_ConditionType'])==4)
check('Movement cuts both dance section and loop hub',set(x[3] for x in edges if x[0]==137 and x[1]==1)=={15,127})
check('Exit branch restores tier restrictions HUD then End',all(any(x[0]==a and x[3]==b for x in edges) for a,b in [(132,57),(132,124),(132,135),(57,72),(72,110),(110,2)]))
rows=read(ROOT/'prefab_inventory_01.json');party=[]
for row in rows:
    conv=[x for x in row['special'] if x['definition']['$type']=='worldInterestingConversationsAreaNode']
    if not any('dancefloor_cs_goons_rave_party.scene' in json.dumps(x) for x in conv):continue
    full=read(row['json']);sp=row['spawners']
    check(f"group{row['id']} preview spawners remain inactive",all(x['definition']['spawnOnStart']==0 and x['definition']['alwaysSpawned']=='default__false_' for x in sp))
    check(f"group{row['id']} no entity/device creation nodes",not any(t in row['types'] for t in ['worldEntityNode','worldDeviceNode']))
    party.append({'id':row['id'],'resource':row['resource'],'prefab':row['prefab'],'json':row['json'],'json_sha256':sha(row['json']),'node_types':row['types'],'verdict':'FULL_NATIVE_PREFAB_ELIGIBLE_WITH_EXISTING_LIVING_ACTOR_ADMISSION','ancillary_controller_required':False,'reason':'NPC dancing supplied by native AISpots; optional player dance choice retains unchanged native cleanup. Disabled preview spawner, no progress writes.'})
check('Eight exact native party prefab rows',len(party)==8)
report={'status':'PASS_PARTY_PREFAB_AND_OPTIONAL_DANCE_SCENE_REVIEW','checks':checks,'parties':party,'scene':{'json':str(source),'json_sha256':sha(source),'binary':str(source)[:-5],'binary_sha256':sha(str(source)[:-5]),'edges':edges},'limits':['Static source proof; restored gameplay and save/reload remain unverified.','Support owner must persist; do not safety-cut an active optional player dance scene before native cleanup.','Native prefab and scene preserved byte-exact; no new scene launch, AI command or native fact write is needed.'],'game_writes':0,'save_writes':0}
(ROOT/'party_assessment_01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'groups':[x['id'] for x in party]}))
