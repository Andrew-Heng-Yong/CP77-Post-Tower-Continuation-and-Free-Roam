import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
checks=[]
def ck(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 assert ok,name
# Additional generic speech dependency (not part of original fifteen groups).
rep=read(R/'outside_conversation_scenes_native_01/report_01.json');scenes=[]
for name in (R/'outside_conversation_scenes_01.txt').read_text().splitlines():
 hits=[x for x in rep['hits'] if x['depot']==name];ck('native speech winner '+name,len(hits)==1 and '\\mod\\' not in hits[0]['archive'])
 hit=hits[0];p=Path(hit['copy']+'.json');j=read(p);types={x.get('$type','') for x in walk(j)}
 ck('speech only '+name,all(x['Data']['$type'] in ['scnStartNode','scnSectionNode','scnEndNode'] for x in j['Data']['RootChunk']['sceneGraph']['Data']['graph']) and not any(t.startswith('quest') for t in types) and {t for t in types if t.endswith('Event')}<={'scnDialogLineEvent'})
 scenes.append({'depot':name,'binary':hit['copy'],'sha256':hit['sha256'],'json_sha256':sha(p)})
baseconv=read(R/'conversation_assessment_01.json');allowed_conv={x['depot'] for x in baseconv['groups']}|{'base\\open_world\\scenes\\conversations\\conversation_groups\\prostitutes.conversations'}
candidates=read(R/'outside_prefab_candidates_01.json');hashes={x['id']:x for x in read(R/'outside_prefab_hashes_01.json')};dec={x['resource']:x for x in read(R/'outside_prefab_decoded_01/report_01.json')['rows']};reg=read(R/'outside_registry_01/report_01.json');found={x['hash']:x for a in reg['rows'] for x in a['found']};ident={x['id']:x for x in reg['identities']}
eligible={1001,1003,1005,1006,1007,1013,1014};cohort=[];rows=[]
for row in candidates:
 i=row['id'];out=dict(row)
 if i not in hashes:out['disposition']='UNRESOLVED_NATIVE_PREFAB_ALIAS';rows.append(out);continue
 h=hashes[i];d=dec[h['resource']];out.update(resource=h['resource'],prefab=h['ref'])
 if not d.get('parsed'):out['disposition']='NO_CURRENT_COMPILED_SECTOR';rows.append(out);continue
 j=read(d['json']);out['types']=dict(collections.Counter(x['definition']['$type'] for x in j['nodes']))
 out['decoded']=d['json'];out['sector_sha256']=d['winner']['sha256'];out['communities']=[]
 spots={p['quest_ref'] for p in j['placements'] if p['type']=='worldAISpotNode'};defs={n['index']:n['definition'] for n in j['nodes']}; marks={m['$value'] for n in j['nodes'] for m in n['definition'].get('markings',[])}
 for c in ident.get(i,{}).get('candidates',[]):
  if c['hash'] not in found or not c['within_prefab']:continue
  f=found[c['hash']];data=read(f['json']);entries=[]
  for ee in data['template']['Data']['entries']:
   e=ee['Data'];refs={n['$value'] for ph in e['phases'] for t in ph['Data']['timePeriods'] for n in t['spotNodeRefs']};mm={m['$value'] for ph in e['phases'] for t in ph['Data']['timePeriods'] for m in t['markings']};bindings=[]
   for ref in sorted(refs):
    suffix=ref.replace('~/../','');hits=[s for s in spots if s==ref or s.endswith('/'+suffix)]
    bindings.append({'native_ref':ref,'matches':hits})
   entry={'entry':e['entryName']['$value'],'spot_bindings':bindings,'markings':sorted(mm),'unmapped_markings':sorted(mm-marks)};entries.append(entry)
   if i in eligible:ck(f'{i}/{c["hash"]}/{entry["entry"]} exact spots and markings',all(len(b['matches'])==1 for b in bindings) and not entry['unmapped_markings'])
  out['communities'].append({'ref':c['ref'],'hash':c['hash'],'registry':f['json'],'registry_sha256':sha(f['json']),'entries':entries})
 if i in eligible:
  ck(f'{i} exact community present',bool(out['communities']))
  ck(f'{i} no auto spawned actors',all(n['definition']['spawnOnStart']==0 and n['definition']['alwaysSpawned'] in ['false_','default__false_'] for n in j['nodes'] if n['definition']['$type']=='worldPopulationSpawnerNode'))
  ck(f'{i} no device or entity creation',not any(t in out['types'] for t in ['worldDeviceNode','worldEntityNode']))
  conv={n['$value'] for n in walk(j) if n.get('$type')=='ResourcePath' and n['$value'].endswith(('.scene','.conversations'))};ck(f'{i} reviewed conversations',conv<=allowed_conv)
  binary=R/'outside_phases_native_01/basegame_4_gamedata.archive'/Path(row['source'].replace('\\','/')).name.removesuffix('.json')
  ck(f'{i} current native phase binary exists',binary.exists())
  out['disposition']='ELIGIBLE_EXACT_EXISTING_ACTOR_NATIVE_SUPPORT'
  cohort.append({'id':i,'prefab':h['ref'],'community_refs':[c['ref'] for c in out['communities']],'spawner_hashes':[c['hash'] for c in out['communities']],'native_binary':str(binary.resolve()),'native_binary_sha256':sha(binary),'node_path':row['node_path'],'resource':h['resource'],'support_sector_resource':h['resource'],'support_sector_raw':d['winner']['raw'],'support_sector_sha256':d['winner']['sha256'],'support_sector_json':d['json'],'proof':str((R/'outside_support_assessment_01.json').resolve()),'prefix':f'PTFRWA3_{i}_','native_admission_facts': ([{'fact':'sts_hey_gle_tier_2','comparison':'Equal','value':0}] if i==1005 else [{'fact':'gle_05_finished','comparison':'Greater','value':0},{'fact':'gle_05_el_gallo_killed','comparison':'Greater','value':0}] if i==1006 else []),'communities':out['communities']})
 else:out['disposition']='REVIEW_PENDING_EXACT_DEPENDENCY'
 rows.append(out)
report={'status':'PASS_SEVEN_OUTSIDE_FAMILY_SUPPORT_BINDINGS','checks':checks,'rows':rows,'eligible_ids':sorted(eligible),'additional_speech_scenes':scenes,'limits':['Support only: no district activation, scene launch, native fact, encounter or reward replay.','Exact living actor/active entry admission is mandatory; these support resources cannot recreate absent communities.','Sibling communities outside the authored prefab are intentionally not bound to this owner.','Static source validation is not restored-game runtime proof.'],'game_writes':0,'save_writes':0}
(R/'outside_support_assessment_01.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
(R/'outside_cohort_01.json').write_text(json.dumps(cohort,indent=2)+'\n',newline='\n')
print(json.dumps({'checks':len(checks),'eligible_ids':sorted(eligible),'additional_speech_scenes':len(scenes)}))
