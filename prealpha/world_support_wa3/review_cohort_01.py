"""Per-node payload and per-entry native admission binding review."""
import json,collections,hashlib,posixpath
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1]
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
checks=[]
def ck(name,value):checks.append({'name':name,'pass':bool(value)});return bool(value)
d=R(H/'identity_cohort_01.json');rows=[]
private=R(H/'private_sectors/verification_06.json');removed={g['group']:set(g['removed_nodes']) for g in private['groups']}
allowed={'worldAISpotNode','worldSmartObjectNode','worldTriggerAreaNode','worldGuardAreaNode','worldCrowdNullAreaNode','worldInterestingConversationsAreaNode','worldPopulationSpawnerNode','worldPatrolSplineNode','worldDeviceNode','worldSaveSanitizationForbiddenAreaNode','worldEntityNode','worldAudioSignpostTriggerNode','worldPreventionFreeAreaNode','worldSplineNode','worldCookedCollisionNode'}
allowed.add('worldSpeedSplineNode')
conv=R(H/'native_review/conversation_assessment_01.json');speech={g['depot'] for g in conv['groups']}
speech|={'base\\open_world\\scenes\\dancefloors\\dancefloor_cs_goons_rave_party.scene','base\\open_world\\scenes\\conversations\\conversation_groups\\prostitutes.conversations'}
for g in d['groups']:
 i=g['id'];s=R(g['support_sector_json']);defs={n['index']:n['definition'] for n in s['nodes'] if n['index'] not in removed.get(i,set())};spots={p['quest_ref']:defs[p['node']] for p in s['placements'] if p['type']=='worldAISpotNode'}
 marks={m['$value'] for n in spots.values() for m in n.get('markings',[])}
 local=[];unbound=[]
 for h,ref in zip(g['spawner_hashes'],g['community_refs']):
  if 'registry' in g:reg=next(r['json'] for r in g['registry'] if r['hash']==h)
  else:reg=next(c['registry'] for c in g['communities'] if c['hash']==h)
  data=R(reg);entries=[]
  ck(f'{i}/{h} registry exact id',data['communityId']['entityId']['hash']==h)
  for ee in data['template']['Data']['entries']:
   e=ee['Data'];em=set();explicit=[]
   for ph in e['phases']:
    for tp in ph['Data']['timePeriods']:
     em.update(m['$value'] for m in tp['markings']);explicit.extend(n['$value'] for n in tp['spotNodeRefs'])
   bound=[]
   for r in sorted(set(explicit)-{'0',''}):
    suffix=r.replace('~/../','');matched=[p for p in spots if p==r or p.endswith('/'+suffix)]
    bound.append({'native_ref':r,'matches':matched})
   missing=sorted(em-marks);entry={'entry':e['entryName']['$value'],'markings':sorted(em),'unmapped_markings':missing,'explicit_spots':bound,'has_authored_local_support':bool(em&marks or any(len(b['matches'])==1 for b in bound))}
   if missing or any(len(b['matches'])!=1 for b in bound):unbound.append({'community':h,**entry})
   entries.append(entry)
  local.append({'hash':h,'ref':ref,'registry':reg,'registry_sha256':sha(reg),'entries':entries})
 types=collections.Counter(n['$type'] for n in defs.values());ck(f'{i} all node families inspected',set(types)<=allowed)
 ck(f'{i} exact native payload pinned',sha(g['support_sector_raw'])==g['support_sector_sha256'])
 auto=[ni for ni,n in defs.items() if n['$type']=='worldPopulationSpawnerNode' and (n['spawnOnStart']!=0 or n['alwaysSpawned'] not in ['default__false_','false_'])]
 ck(f'{i} no auto population in selected payload',not auto)
 scenes={v['$value'] for n in defs.values() for v in walk(n) if v.get('$type')=='ResourcePath' and v['$value'].endswith(('.scene','.conversations'))}
 ck(f'{i} speech and scene dependencies reviewed',scenes<=speech)
 entities=[n for n in defs.values() if n['$type']=='worldEntityNode'];ck(f'{i} static entities only separately reviewed corpses',not entities or (i==393 and all(n['instanceData'] is None for n in entities) and R(H/'native_review/corpse_assessment_01.json')['status'].startswith('PASS')))
 device_refs=[]
 for n in s['nodes']:
  if n['index'] not in defs or n['definition']['$type']!='worldDeviceNode':continue
  node=n['definition'];template=node['entityTemplate']['DepotPath']['$value']
  ck(f'{i}/{n["index"]} native security device only',template in ['0','base\\gameplay\\devices\\security_systems\\security_area\\security_area_1.ent','base\\gameplay\\devices\\security_systems\\security_system.ent'])
  for c in node['deviceConnections']:
   ck(f'{i}/{n["index"]} device connection class',c['deviceClassName']['$value'] in ['SecurityAreaControllerPS','CommunityProxyPS'])
   device_refs.extend(v['$value'] for v in c['nodeRefs'])
 rows.append({'id':i,'node_types':dict(types),'communities':local,'unmapped_entry_support':unbound,'autospawn_nodes_requiring_private_filter':auto,'conversation_dependencies':sorted(scenes),'security_connection_refs':sorted(set(device_refs)),'spot_count':len(spots)})
report={'status':'PASS_NATIVE_SUPPORT_PAYLOAD_REVIEW' if all(c['pass'] for c in checks) else 'FAIL_NATIVE_SUPPORT_PAYLOAD_REVIEW','checks':checks,'rows':rows,'limits':['Registry alternate phases can name absent native B/C workspots. Preserve authored available support without inventing replacement spots or changing phases.','A wholly unbound entry must not admit new support; entry exclusions are mirrored in runtime proof.','Security area/system entities retain native IDs and connections; no state reset or command is issued.','Native save-sanitization areas remain unchanged to preserve authored location behavior.'],'game_writes':0,'save_writes':0}
(H/'payload_review_01.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'groups':len(rows),'checks':len(checks),'failed':[c for c in checks if not c['pass']],'unmapped':[(r['id'],len(r['unmapped_entry_support']))for r in rows if r['unmapped_entry_support']]},indent=2))
