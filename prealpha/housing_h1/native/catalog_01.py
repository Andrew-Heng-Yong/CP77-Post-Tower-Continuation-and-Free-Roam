"""Read-only, exact current native housing location and controller catalogue."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()
def main():
 out=ROOT/'research/housing_h1/native/catalog_01.json';assert not out.exists()
 invpath='research/housing_h1/native/official_01/inventory.json';inv=read(invpath);pins={invpath:sha(invpath),'prealpha/housing_h1/native/catalog_01.py':sha('prealpha/housing_h1/native/catalog_01.py')}
 sources={r['depot']:r for r in inv['rows']};world=[]
 for n in range(3):
  p=f'research/sidejobs_s28/vehicles/world_03/json/ep1_1_nightcity_always_loaded_{n}.streamingsector.json';raw=p.replace('/json/','/raw/').removesuffix('.json');pins[p]=sha(p);pins[raw]=sha(raw)
  d=read(p)['Data']['RootChunk']
  world.extend({'path':value(ref),'source':p,'index':i} for i,ref in enumerate(d['nodeRefs']))
 def exact(alias,where):
  hits=[r for r in world if r['path'].endswith('/'+alias) and where in r['path']];assert len(hits)==1,(alias,hits);return hits[0]
 specs=[('h10',None,'root',None,'points_of_interest/safehouses/v_room'),('northside','wat_nid','root/2',5,'points_of_interest/safehouses/dlc6_apart_wat_nid'),('japantown','wbr_jpn','root/1',6,'points_of_interest/safehouses/dlc6_apart_wbr_jpn'),('glen','hey_gle','root/2',4,'points_of_interest/safehouses/dlc6_apart_hey_gle'),('corpo','cct_dtn','root/2',2,'points_of_interest/safehouses/dlc6_apart_cct_dtn')]
 rows=[]
 for id,suffix,graph,scene,marker in specs:
  if suffix:
   depot=f'dlc\\dlc6_apart\\loc_dlc6_apart_{suffix}\\quest\\phases\\dlc6_apart_{suffix}.questphase';s=sources[depot]
   data=read(s['json']);r=SafeResource(data);gs={g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])};ns={n['id']:n for n in gs[graph]['nodes']}
   markerrows=[{'graph':g['path'],'node':n['id']} for g in gs.values() for n in g['nodes'] if any(v.get('$type')=='gameJournalPath' and v.get('realPath')==marker for v in walk(n))];assert len(markerrows)==1
   devices={'stash':exact(f'#dlc6_apart_{suffix}_dvc_stash','loc_dlc6_apart_'+suffix),'wardrobe':exact(f'#dlc6_apart_{suffix}_invis_wardrobe','loc_dlc6_apart_'+suffix)}
   if id=='northside':devices['purchase']=exact('#dlc6_apart_wat_nid_dvc_motel_screen','loc_dlc6_apart_wat_nid');devices['door']=exact('#dlc6_apart_wat_nid_dvc_door','loc_dlc6_apart_wat_nid')
   if id=='corpo':devices['door']=exact('#dlc6_apart_cct_dtn_dvc_door_main_entrance','loc_dlc6_apart_cct_dtn')
   row={'id':id,'native_purchase_fact':f'dlc6_apart_{suffix}_purchased','source':s,'home_marker':marker,'marker_source':markerrows[0],'service_graph':graph,'service_scene_node':scene,'service_wait_node':3,'service_scene':value(ns[scene]['sceneFile']['DepotPath']),'devices':devices,'root_prefabs':data['Data']['RootChunk']['phasePrefabs'],'purchase_assignment':'EconomicAssignment.vs_apartment_dlc6_apart_'+suffix}
   assert [3,'Out',scene,'in'] in gs[graph]['edges'] and [scene,'out',3,'In'] in gs[graph]['edges']
  else:
   s=sources[r'base\quest\minor_quests\mq000\mq000.questphase'];row={'id':id,'native_purchase_fact':None,'source':s,'home_marker':marker,'marker_source':{'graph':'root/12','node':2},'price':25000,'devices':{'door':exact('#q001_door_v_flat','loc_megabuilding_a_gameplay'),'stash':exact('#v_room_stash','loc_megabuilding_a_gameplay'),'wardrobe':exact('#apart_v_mb_wardrobe','loc_megabuilding_a_gameplay')}}
  for p in [s['raw'],s['json']]:pins[p]=sha(p)
  row['entitled_fact']='PTFRH1_'+id+'_Entitled';rows.append(row)
 out.write_text(json.dumps({'status':'CURRENT_SOURCE_BOUND_HOUSING_CATALOGUE','properties':rows,'source_pins':pins,'notes':['NodeRef registry witnesses establish exact target identities, not live entity presence.','Native purchase-history facts are documentary and must not be reset for repurchase.','Glen and Japantown have no named front-door registry witness; native purchase scenes have their own physical choice anchors.','Only five ordinary homes are mutable; Kerry access and all shared stash contents stay outside migration.']},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'properties':len(rows),'pins':len(pins),'output':str(out)}))
if __name__=='__main__':main()
