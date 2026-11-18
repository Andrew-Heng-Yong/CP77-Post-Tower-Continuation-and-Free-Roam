"""Bounded current-provider geometry/variant audit; no runtime or save writes."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent
WORK=HERE/'work'
OWNER='$/03_night_city/c_watson/little_china/wlc_01/wlc_01_b_env_prefab6TCITNI/#wlc_01_b_decoration'
SHIFT=(-0.86535,0.96045,0.357322)
TARGETS=[
 dict(sector=r'base\worlds\03_night_city\_compiled\default\ep1\exterior_-1_0_0_5.streamingsector',
      instance=120,node=87,inner=8,position=(-1407.215,888.410,0.357),
      mesh=r'base\environment\street\watson\little_china\wlc_01_crossroad_02.mesh'),
 dict(sector=r'base\worlds\03_night_city\_compiled\default\ep1\exterior_-12_8_0_1.streamingsector',
      instance=0,node=0,inner=0,position=(-1480.136,1149.382,19.207),
      mesh=r'base\worlds\03_night_city\sectors\_external\road_meshes\bended\br_1c2d1b36_rt_1x1_with_right_sidewalk_24m.mesh'),
]

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
def fnv(s):
 h=14695981039346656037
 for b in s.encode('utf-8'):h=((h^b)*1099511628211)&0xffffffffffffffff
 return str(h)
def asset(x):
 if not isinstance(x,dict):return None
 p=val(x.get('DepotPath'))
 if p in (None,'0',''):return None
 return p if str(p).isdigit() else fnv(p)
def write(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')

def main():
 capture=read(WORK/'final_scene_01/providers.json')
 decoded=read(WORK/'final_scene_decoded_01/manifest.json')
 ranges=read(WORK/'final_scene_ranges_01.json')
 assert len(decoded['rows'])==27 and all(r['json'] for r in decoded['rows'])
 for r in decoded['rows']:
  assert sha(r['raw'])==r['sha256'] and sha(r['json'])==r['json_sha256']
 by_depot=defaultdict(list)
 for r in decoded['rows']:by_depot[r['depot']].append(r)
 winners={}
 for depot,providers in by_depot.items():
  for provider in providers:
   assert Path(provider['archive']).name in ['basegame_3_nightcity.archive','ep1_1_nightcity.archive','zzzz_PTFR_Combined.archive']
  priority={'basegame_3_nightcity.archive':0,'ep1_1_nightcity.archive':1,'zzzz_PTFR_Combined.archive':2}
  winner=max(providers,key=lambda p:priority[Path(p['archive']).name])
  winners[depot]=winner
 # EP1 supersedes the base archive at shared depots; the installed R8 clinic
 # correction supersedes that one depot. No other mod supplies these 16 sectors.
 assert len(winners)==16
 geometry=[];members=[];all_types=Counter();max_bounds=[[],[],[]]
 source_pins=[]
 for depot,provider in winners.items():
  root=read(provider['json'])['Data']['RootChunk']
  assert root['version']==68
  nodes=root['nodes']; data=root['nodeData']['Data'];starts=root['variantIndices']
  assert starts==sorted(starts) and starts[0]==0
  memberships=defaultdict(list)
  for rr in [r for r in ranges if r['sector']==depot]:
   lo=starts[rr['range']];hi=starts[rr['range']+1] if rr['range']+1<len(starts) else len(data)
   for i in range(lo,hi):memberships[i].append(rr)
  for index,datum in enumerate(data):
   node_index=int(datum['nodeIdx']);node=nodes[node_index]['Data'];part=node
   buffer=node.get('buffer');bd=buffer.get('Data') if isinstance(buffer,dict) else None
   if isinstance(bd,dict) and 'InnerNodes' in bd:
    assert datum['instanceIndex']<len(bd['InnerNodes'])
    part=bd['InnerNodes'][datum['instanceIndex']]
    assert int(part.get('index',datum['instanceIndex']))==datum['instanceIndex']
   t=datum['transform'];pos=[t['position'][k] for k in ['X','Y','Z']]
   quat=[t['orientation'][k] for k in ['i','j','k','r']]
   scale=[datum['scale'][k] for k in ['X','Y','Z']]
   owner_rows=[r for r in memberships[index] if r['owner']==OWNER]
   row=dict(sector=depot,instance=index,node=node_index,inner=datum['instanceIndex'],
       type=node['$type'],position=pos,rotation=quat,scale=scale,
       mesh=val(part.get('mesh',{}).get('DepotPath')) if isinstance(part.get('mesh'),dict) else None,
       mesh_key=asset(part.get('mesh')),appearance=val(part.get('meshAppearance')),
       memberships=[dict(owner=r['owner'],variant=r['variant'],range=r['range']) for r in memberships[index]])
   if owner_rows:
    assert len(owner_rows)==1
    row['variant']=owner_rows[0]['variant'];members.append(row)
    all_types[(row['variant'],node['$type'])]+=1
    for axis in range(3):max_bounds[axis].append(pos[axis])
   if row['mesh_key']:geometry.append(row)
  source_pins.append(dict(depot=depot,archive=provider['archive'],raw=provider['raw'],sha256=provider['sha256'],
      json=provider['json'],json_sha256=provider['json_sha256'],definitions=len(nodes),instances=len(data),ranges=len(starts)))
 by_asset=defaultdict(list)
 for row in geometry:by_asset[row['mesh_key']].append(row)
 pairs=[]
 for row in geometry:
  if row.get('variant')!='q307_final_scene':continue
  expected=[a-b for a,b in zip(row['position'],SHIFT)]
  candidates=[]
  for other in by_asset[row['mesh_key']]:
   if other.get('variant')=='q307_final_scene':continue
   if math.dist(expected,other['position'])>0.004:continue
   if max(abs(a-b) for a,b in zip(row['scale'],other['scale']))>0.0001:continue
   # A quaternion and its negation are the same rotation.
   qdist=min(max(abs(a-b) for a,b in zip(row['rotation'],other['rotation'])),max(abs(a+b) for a,b in zip(row['rotation'],other['rotation'])))
   if qdist>0.0001:continue
   candidates.append(other)
  if candidates:
   best=min(candidates,key=lambda x:math.dist(expected,x['position']))
   pairs.append(dict(extra=row,original=best,translation=[a-b for a,b in zip(row['position'],best['position'])],
       match='same mesh resource, rotation and scale; common translation within 4 mm',
       limit='Mesh identity/transform comparison; not per-triangle visual or physical intersection proof.'))
 screenshots=[]
 for target in TARGETS:
  found=[r for r in geometry if r['sector']==target['sector'] and r['instance']==target['instance']]
  assert len(found)==1
  r=found[0]
  assert r['node']==target['node'] and r['inner']==target['inner'] and r['mesh_key']==fnv(target['mesh'])
  assert math.dist(r['position'],target['position'])<0.001
  assert r['variant']=='q307_final_scene'
  pair=[p for p in pairs if p['extra']['sector']==r['sector'] and p['extra']['instance']==r['instance']]
  assert len(pair)==1
  screenshots.append(dict(user=target,current=r,original=pair[0]['original'],translation=pair[0]['translation']))
 counts=[dict(variant=v,type=t,count=n) for (v,t),n in sorted(all_types.items())]
 write(WORK/'audit_01.json',dict(status='SOURCE_CONFIRMED_TRANSLATED_FINAL_SCENE_GEOMETRY',
     provider_archives=len(capture['archives']),decoded_providers=27,current_sectors=len(winners),
     owner=OWNER,source_pins=source_pins,range_records=[r for r in ranges if r['owner']==OWNER],
     members=members,type_counts=counts,paired_geometry=pairs,screenshot_matches=screenshots,
     member_origin_bounds=[[min(a),max(a)] for a in max_bounds],common_translation=SHIFT,
     limitations=['Full group includes props, vehicles, lights, collision and workspots; not a mesh-only deletion allowlist.',
       'Original q307 cleanup already authors final_scene off / final_scene_hide on using another owner spelling; runtime alias equivalence is not assumed.',
       'The two screenshots are user runtime evidence. Source membership and transformed-pair counts do not certify every rendered overlap.',
       'Cooked-collision shape/body equivalence and vehicle/interactive lifecycle require separate review before implementation.'],
     game_writes=0,save_writes=0))
 print(json.dumps(dict(status='SOURCE_CONFIRMED',sectors=len(winners),owner_ranges=sum(r['owner']==OWNER for r in ranges),
     variant_members=len(members),paired_mesh_instances=len(pairs),screenshot_matches=len(screenshots),bounds=[[min(a),max(a)] for a in max_bounds])))

if __name__=='__main__':main()
