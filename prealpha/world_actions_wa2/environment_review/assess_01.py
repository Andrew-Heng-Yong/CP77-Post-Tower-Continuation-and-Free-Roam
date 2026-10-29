"""Prove exact default-world dependencies and bounded native NodeRef corrections."""
from pathlib import Path
from hashlib import sha256
import copy,json
H=Path(__file__).resolve().parent;W=H.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
inputs=read(H/'inputs_01.json');hashes=read(H/'reference_hashes_01.json')['hashes'];census=read(H/'extract_01/report_01.json')
checks=[];pins=[H/'inputs_01.json',H/'reference_hashes_01.json',H/'extract_01/report_01.json',H/'decode_01/report_01.json',H/'decode_02/report_01.json']
def check(name,value):checks.append(name);assert value,name
def ps(node,name):return next(c['persistentState']['Data'] for c in node['instanceData']['Data']['buffer']['Data']['Chunks'] if c.get('persistentState',{}).get('Data',{}).get('$type')==name)
def equalref(a,b):return a==b or (a in hashes and b in hashes and hashes[a]==hashes[b])
check('All125 current installed archives inventoried',census['archives']==125)
for resource in census['resources']:
    hits=[r for r in census['hits'] if r['depot']==resource]
    check('No mod override: '+resource,sorted(Path(r['archive']).name for r in hits)==['basegame_3_nightcity.archive','ep1_1_nightcity.archive'])
decoded={}
for folder in ['decode_01','decode_02']:
    for row in read(H/folder/'report_01.json')['rows']:
        if row['parsed']:decoded[Path(row['raw']).name]=(folder,row)
hits={Path(r['raw']).name:r for r in census['hits']}
allrows=[];blocks={}
for hit in census['hits']:
    name=Path(hit['archive']).name
    if hit['depot'].endswith('.streamingblock'):
        bp=Path(hit['raw']+'.json');blocks[name]=read(bp)['Data']['RootChunk']['descriptors'];pins.extend([Path(hit['raw']),bp])
for stem,(folder,raw) in decoded.items():
    pfile=H/folder/(stem+'.placements.json');nfile=H/folder/(stem+'.nodes.json')
    ns={n['node']:n for n in read(nfile)['nodes']}
    for p in read(pfile)['placements']:
        if any(equalref(p['quest_ref'],ref) for g in inputs['groups'] for ref in g['context_refs']):
            check('Decoded target node has complete definition '+p['quest_ref'],'definition' in ns[p['node']])
            allrows.append({'archive':Path(hits[stem]['archive']).name,'depot':hits[stem]['depot'],'placement':p,'definition':ns[p['node']]['definition']})
            pins.extend([Path(raw['raw']),pfile,nfile])
groups=[]
for group in inputs['groups']:
    gid=group['id'];wanted=[ref for ref in group['context_refs'] if not ref.startswith('$/decoset/')]
    selected={};descriptors={}
    for archive in ['basegame_3_nightcity.archive','ep1_1_nightcity.archive']:
        selected[archive]=[];descriptors[archive]=[]
        for ref in wanted:
            matches=[r for r in allrows if r['archive']==archive and equalref(r['placement']['quest_ref'],ref)]
            check(str(gid)+': one exact/hash-equivalent placement '+archive+' '+ref,len(matches)==1)
            r=copy.deepcopy(matches[0]);r['placement'].pop('id');r.pop('archive')
            selected[archive].append(r)
        for depot in sorted({r['depot'] for r in selected[archive]}):
            ds=[d for d in blocks[archive] if d['data']['DepotPath']['$value']==depot]
            check(str(gid)+': unique default block registration '+archive+' '+depot,len(ds)==1)
            desc=ds[0];descriptors[archive].append(desc)
            check(str(gid)+': default Exterior level0 not quest-owned',desc['category']=='Exterior' and desc['level']==0 and desc['questPrefabNodeRef']['$value']=='0')
            check(str(gid)+': named variants do not select shooting environment',all('cs_goons_shooting' not in v['nodeRef']['$value'] for v in desc['variants']))
    check(str(gid)+': base and EP1 exact placement/definition equivalence excluding cooker ID',selected['basegame_3_nightcity.archive']==selected['ep1_1_nightcity.archive'])
    check(str(gid)+': base and EP1 default block descriptor equivalence',descriptors['basegame_3_nightcity.archive']==descriptors['ep1_1_nightcity.archive'])
    rows=selected['ep1_1_nightcity.archive']
    for r in rows:
        if 'target_object' in r['placement']['quest_ref']:
            n=r['definition'];check(str(gid)+': native visible AI target entity',n['$type']=='worldEntityNode' and n['entityTemplate']['DepotPath']['$value']==r'base\gameplay\ai\ai_objects\target_object.ent' and n['isVisibleInGame']==1 and n['instanceData'] is None)
    system=next(r for r in rows if r['placement']['quest_ref'].endswith('/cs_goons_shooting_sec_system'))
    area=next(r for r in rows if r['placement']['quest_ref'].endswith('/cs_goons_shooting_sec_area'))
    links={c['deviceClassName']['$value']:[r['$value'] for r in c['nodeRefs']] for c in system['definition']['deviceConnections']}
    check(str(gid)+': system links its exact sibling area',links['SecurityAreaControllerPS']==['~/../cs_goons_shooting_sec_area'])
    check(str(gid)+': system links exact W3 community or its authored global alias',all(any(equalref(x,own) or (';'+x in own and x.startswith('#')) for own in group['community_refs']) for x in links['CommunityProxyPS']))
    sp=ps(system['definition'],'SecuritySystemControllerPS');ap=ps(area['definition'],'SecurityAreaControllerPS')
    check(str(gid)+': initial security system ON without strict quest control',sp['deviceState']=='ON' and sp['isUnderStrictQuestControl']==0)
    check(str(gid)+': initial security area ON and RESTRICTED',ap['deviceState']=='ON' and ap['securityAreaType']=='RESTRICTED')
    check(str(gid)+': selected objects share same authored environment prefab',len({r['definition']['sourcePrefabHash'] for r in rows})==1)
    native_resolved=[ref for ref in group['native_dependencies'] if any(equalref(r['placement']['quest_ref'],ref) for r in rows)]
    groups.append({'id':gid,'native_dependencies':group['native_dependencies'],'resolved_native_dependencies':native_resolved,
                   'actual_security_system':system['placement']['quest_ref'],'selected':rows,'descriptors':descriptors['ep1_1_nightcity.archive'],
                   'status':'PASS_EXACT_ENVIRONMENT' if len(native_resolved)==len(group['native_dependencies']) else 'REQUIRES_EXACT_246_SECURITY_REBIND'})
g=next(g for g in groups if g['id']==246)
old=next(r for r in g['native_dependencies'] if r.startswith('$/decoset/'));new=g['actual_security_system']
check('246 stale source-prefab security ref differs from actual city system hash',hashes[old]!=hashes[new])
native=read(H.parent/'native_review/census_raw_01.json');owner=next(r for r in native['owners'] if r['id']==246)
nodes={n['id']:n for n in owner['phases'][0]['payload']['phaseGraph']['nodes']}
corrections=[]
for node in [219,220,221,222]:
    c=nodes[node]['condition']['type']
    check('246 exact security condition '+str(node),c['objectRef']['$value']==old and c['deviceControllerClass']['$value']=='SecuritySystemControllerPS' and c['deviceConditionFunction']['$value']==('IsSystemAlerted' if node==222 else 'IsSystemInCombat'))
    corrections.append({'group':246,'node':node,'field':'condition.type.objectRef','old':old,'old_hash':hashes[old],'new':new,'new_hash':hashes[new],'function_unchanged':c['deviceConditionFunction']['$value']})
g=next(g for g in groups if g['id']==289)
check('289 native target/security references match authored #rancho paths by engine hash',all(ref in hashes and any(equalref(ref,r['placement']['quest_ref']) for r in g['selected']) for ref in g['native_dependencies']))
pins.extend([H/'assess_01.py',H/'prepare_01.py',H/'extract_01.ps1',H/'decode_01.ps1',H/'decode_02.ps1',H/'reference_hashes_01.ps1',H.parent/'native_review/census_raw_01.json'])
pins=list(dict.fromkeys(pins))
result={'status':'PASS_STATIC_ENVIRONMENTS_WITH_REQUIRED_246_SECURITY_REBIND','checks_passed':len(checks),'checks':checks,'groups':groups,'required_candidate_corrections':corrections,
        'native_unmodified_ready_groups':[172,173,289],'native_rebind_required_groups':[246],
        'archive_census_count':125,'new_mod_overrides':0,'decoded_sectors':len(decoded),'extracted_sectors':72,
        'limits':['Static world ownership does not prove currently streamed/intact live objects or persisted security state.',
                  'Group246 city system is exact community-connected counterpart; source decoset ref was not resolved in nearby decompressed sectors. This is not a claim of global absence.',
                  'Two nearby exterior_-11_-20 base/EP1 copies still have an unrelated widget RTTI decode error; all selected dependency sectors decoded successfully.',
                  'Group289 native goon3 target remains the security-system object; its native behavior is preserved, not diagnosed as a gameplay defect.',
                  'Shooting and speech for the broader cohort are live unverified.'],
        'game_writes':0,'save_writes':0,'candidate_edits':0,'pins':[{'path':str(p),'sha256':digest(p)} for p in pins]}
out=H/'assessment_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks_passed':len(checks),'required_corrections':corrections,'sha256':digest(out)},indent=2))
