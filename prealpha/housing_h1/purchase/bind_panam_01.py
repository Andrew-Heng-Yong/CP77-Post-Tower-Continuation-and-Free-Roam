"""Bind exact Panam home stash child paths to current native entity/template evidence."""
import argparse, copy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
def val(o):return o.get('$value',o) if isinstance(o,dict) else o
STASH=r'base\gameplay\devices\stash\stash.ent'
def target_nodes(root):
 out=[]
 for i,h in enumerate(root['nodes']):
  n=h['Data']
  if val(n.get('entityTemplate',{}).get('DepotPath'))!=STASH:continue
  assert n['$type']=='worldEntityNode' and n['instanceData'] is None
  name=val(n['debugName']);assert name in {'stash','stash_001'}
  assert val(n['appearanceName'])=='stash_appearance_nomad_camps'
  assert n['sourcePrefabHash']=='1918402835303260458'
  paths=[(j,val(r)) for j,r in enumerate(root['nodeRefs']) if '/#nomad_camp_0' in val(r) and val(r).endswith('/'+name+'_prefabGP6AWTI')]
  assert len(paths)==1
  j,path=paths[0]
  assert '/#nomad_camp_01_stash_prefab/' in path or '/#nomad_camp_02_stash_prefab/' in path
  out.append({'path':path,'node_index':i,'node_ref_index':j,'typed_node':n})
 assert len(out)==2
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('decode_report');args=ap.parse_args()
 base='research/housing_h1/native/relationship_scope_01.json'
 world='research/housing_h1/purchase/panam_world_01/inventory.json'
 template='research/housing_h1/purchase/panam_template_01/inventory.json'
 old=read(base);inv=read(world);tin=read(template);dec=read(args.decode_report)
 assert len(dec['rows'])==4 and all(r['parsed'] for r in dec['rows'])
 assert len(tin['rows'])==1 and tin['rows'][0]['depot']==STASH
 tr=tin['rows'][0];tobj=read(tr['json'])
 types={v.get('$type') for v in walk(tobj)}
 assert {'Stash','StashController','StashControllerPS'}<=types
 assert all(val(v['controllerTypeName'])=='StashController' for v in walk(tobj) if v.get('$type')=='Stash')
 pins=copy.deepcopy(old['source_pins'])
 for p in [base,world,template,args.decode_report,Path(__file__).relative_to(ROOT).as_posix(),'prealpha/housing_h1/purchase/lookup_panam_01.ps1','prealpha/housing_h1/purchase/extract_panam_template_01.ps1',tr['raw'],tr['json']]:pins[p]=sha(p)
 pins.update(dec['source_pins'])
 archives={a['path']:a['sha256'] for a in inv['archives']}
 for a in tin['archives']:assert archives[a['path']]==a['sha256']
 witnesses=[];by_path={};checks=0
 for row in dec['rows']:
  official=next(r for r in inv['rows'] if r.get('raw')==row['raw'])
  for k in ['raw','json']:
   assert sha(row[k])==row[k+'_sha256'];pins[row[k]]=row[k+'_sha256'];checks+=1
  assert row['raw_sha256']==official['raw_sha256'];checks+=1
  root=read(row['json'])['Data']['RootChunk'];targets=target_nodes(root)
  for target in targets:
   path=target['path'];typed=target['typed_node']
   if path in by_path:assert by_path[path]['typed_node']==typed;checks+=1
   else:by_path[path]=target
   witnesses.append({'archive':official['archive'],'archive_sha256':official['archive_sha256'],'depot':official['depot'],'raw':row['raw'],'json':row['json'],**target});checks+=5
  # Negative control: a matching debug name cannot substitute a different entity template.
  bad=copy.deepcopy(root)
  bad['nodes'][targets[0]['node_index']]['Data']['entityTemplate']['DepotPath']['$value']='base\\gameplay\\devices\\generic\\empty_visible_object.ent'
  try:target_nodes(bad)
  except AssertionError:checks+=1
  else:raise AssertionError('wrong template admitted')
 assert len(by_path)==4
 devices=copy.deepcopy(old['devices'])
 for path,target in sorted(by_path.items()):
  witnesses_for_path=[w for w in witnesses if w['path']==path]
  assert len(witnesses_for_path)==2
  preferred=next(w for w in witnesses_for_path if '\\ep1\\' in w['archive'])
  devices.append({'id':'panam','kind':'stash','path':path,'source':preferred['json'],'index':preferred['node_ref_index'],'native_template':STASH,'runtime_type':'Stash/StashControllerPS','world_node_index':preferred['node_index'],'base_ep1_typed_payload_equal':True})
 assert len([d for d in devices if d['kind'] in {'stash','wardrobe'}])==9
 result={'status':'PASS_CURRENT_TYPED_RELATIONSHIP_DEVICES','devices':devices,'source_pins':pins,'official_archive_pins':archives,'panam_stash_witnesses':witnesses,'template_witness':tr,'checks':checks,'negative_cases':4,'scope':['Four exact full home stash child paths: stash and stash_001 variants at each native camp.','Current basegame and EP1 stock worldEntityNode definitions have equal stash template, appearance and prefab identity; extracted current stash.ent contains actual Stash/StashControllerPS types.','Runtime interception is additionally restricted to actual Stash and StashControllerPS methods. No car/public stash, shared inventory deletion, map-marker-as-container assumption, or generic area guard.'],'limits':['The world nodeData custom buffers remain opaque/unverified and are not used for positions, instance IDs or matching.','Six irrelevant new cooked render/collision/acoustic types are adapted only to read the containing resource; no world resource is rebuilt.','NodeRef runtime resolution and device lifecycle remain subject to in-game verification.'],'game_writes':0}
 out=ROOT/'research/housing_h1/purchase/relationship_devices_02.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'path':out.relative_to(ROOT).as_posix(),'checks':checks,'typed_devices':9,'panam_stash_paths':4}))
if __name__=='__main__':main()
