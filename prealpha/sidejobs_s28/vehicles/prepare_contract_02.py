"""Bind preserved vehicle contracts to current native sources and immediate script predicates."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
HERE=Path(__file__).resolve().parent
PREFIX='PTFR.SideJobsS28.'
CRATE='$/03_night_city/c_watson/northside/loc_mq050_ken_block_tribute_prefabIK2VAKA/loc_mq050_ken_block_tribute_gameplay_prefabJPVRKTI/loc_mq050_ken_block_tribute_loot_prefabPU3FSXA/#mq050_main_loot'
def write(p,x):
 assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 old=read(HERE/'contracts_01.json');plan=read(ROOT/'research/sidejobs_s28/vehicles/plan_01.json');inv=read(ROOT/'research/sidejobs_s28/vehicles/official_02/inventory.json');rows={r['depot']:r for r in inv['rows']};pins={}
 def pin(p):pins[p]=sha(ROOT/p)
 for p in ['prealpha/sidejobs_s28/vehicles/prepare_contract_02.py','prealpha/sidejobs_s28/vehicles/contracts_01.json','research/sidejobs_s28/vehicles/official_02/inventory.json','research/sidejobs_s28/vehicles/plan_01.json','research/sidejobs_s28/vehicles/presentation_01.json']:
  pin(p)
 for r in rows.values():pin(r['raw']);pin(r['json'])
 for p in ['research/sidejobs_s28/vehicles/world_03/inventory.json','research/sidejobs_s28/vehicles/world_03/raw/ep1_1_nightcity_always_loaded_2.streamingsector','research/sidejobs_s28/vehicles/world_03/json/ep1_1_nightcity_always_loaded_2.streamingsector.json']:
  pin(p)
 world=read(ROOT/'research/sidejobs_s28/vehicles/world_03/json/ep1_1_nightcity_always_loaded_2.streamingsector.json');assert any(value(n)==CRATE for n in walk(world))
 native={d:{'depot':d,'json':r['json'],'raw':r['raw'],'json_sha256':r['json_sha256'],'raw_sha256':r['raw_sha256']} for d,r in rows.items()}
 for j in plan['jobs']:
  j['resources']=[native[r['depot']] for r in j['resources']]
  pd=r'base\quest\minor_quests\minorquests.questphase' if j['id']=='mq029_tourist' else r'base\quest\bugfixing\quest_bugfixing.questphase'
  j['parent']['json']=native[pd]['json'];j['parent']['raw']=native[pd]['raw'];j.pop('graphs')
 pred={
  'highwayman_vehicle':{'class':PREFIX+'PTFRS28HighwaymanVehicleUnownedPrereq','kind':'vehicle_unowned','record':'Vehicle.v_sportbike2_arch_tyger_player','hash':'167323116460'},
  'hoon_vehicle':{'class':PREFIX+'PTFRS28HoonVehicleUnownedPrereq','kind':'vehicle_unowned','record':'Vehicle.v_sport2_quadra_type66_nomad_tribute','hash':'189393478117'},
  'hoon_world_key':{'class':PREFIX+'PTFRS28HoonWorldKeyAbsentPrereq','kind':'loaded_world_inventory_zero','node_ref':CRATE,'record':'Keycards.mq050_car_keys','hash':'99716362400','unloaded':'DEFER','native_target_witness':{'depot':r'base\quest\minor_quests\mq050\mq050.questphase','node':51,'reference':'#mq050_main_loot'}}}
 old['status']='CURRENT_SOURCE_FRESH_CONTRACT_WITH_IMMEDIATE_NATIVE_PREDICATES';old['source_pins']=pins;old['native_resources']=native;old['native_runtime_predicates']=pred
 old['native_vehicle_gate']='Immediate questPrereq_ConditionType invokes read-only IScriptablePrereq.IsFulfilled on the native full admission condition. VehicleAvailable NOR remains an additional availability restriction.'
 for o in old['owners']:
  o['native_predicates']=[pred['highwayman_vehicle']['class']] if o['id']=='mq029_tourist' else [pred['hoon_vehicle']['class'],pred['hoon_world_key']['class']]
  o['native_world_inventory_zero']=[] if o['id']=='mq029_tourist' else [pred['hoon_world_key']]
 plan['source_pins']=pins;plan['native_runtime_predicates']=pred
 write(HERE/'contracts_02.json',old);write(ROOT/'research/sidejobs_s28/vehicles/plan_02.json',plan)
 donors=[]
 for r in inv['rows']:donors.append({'depot':r['depot'],'archive':r['archive'],'sha256':r['raw_sha256'],'raw':r['raw'],'current_byte_exact':True})
 for inventory in ['world_03','workspots_01','animations_01']:
  for r in read(ROOT/f'research/sidejobs_s28/vehicles/{inventory}/inventory.json')['rows']:
   if r.get('parsed',True):donors.append({'depot':r['depot'],'archive':r['archive'],'sha256':r['raw_sha256'],'raw':r['raw'],'current_byte_exact':True})
 write(ROOT/'research/sidejobs_s28/vehicles/current_donors_02.json',{'status':'CURRENT_OFFICIAL_EXTRACTIONS','rows':donors})
 print(json.dumps({'contract':'prealpha/sidejobs_s28/vehicles/contracts_02.json','sha256':sha(HERE/'contracts_02.json'),'predicates':pred}))
if __name__=='__main__':main()
