"""Consolidate the tested vehicle prototype and current source blockers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
 out=ROOT/'research/sidejobs_s28/vehicles/assessment_01.json';assert not out.exists()
 paths=['prealpha/sidejobs_s28/vehicles/contracts_01.json','research/sidejobs_s28/vehicles/plan_01.json','prealpha/sidejobs_s28/vehicles/build/vehicles_01/component.json','prealpha/sidejobs_s28/vehicles/build/vehicles_01/tests.json','research/sidejobs_s28/vehicles/presentation_01.json','research/sidejobs_s28/vehicles/world_03/inventory.json','research/sidejobs_s28/vehicles/workspots_01/inventory.json','research/sidejobs_s28/vehicles/animations_01/inventory.json']
 pins={p:sha(ROOT/p) for p in paths};pins[str(Path(__file__).relative_to(ROOT)).replace('\\','/')]=sha(__file__)
 component=read(ROOT/paths[2]);tests=read(ROOT/paths[3]);presentation=read(ROOT/paths[4]);world=read(ROOT/paths[5])
 assert tests['component_sha256']==pins[paths[2]] and not component['boots']
 result={
  'status':'SOURCE_PROTOTYPE_COMPLETE_ADMISSION_BLOCKED',
  'component':paths[2],'tests':paths[3],'source_pins':pins,
  'candidate':{'resources':len(component['resources']),'boots':0,'proposed_entries':len(component['proposed_boots']),'checks':tests['checks'],'policy_cases':tests['policy_cases'],'native_payload_checks':tests['native_payload_checks'],'contract_unchanged':True},
  'retained_native_behavior':[
   'Highwayman original main reference retains setup plus garage/James/corpse/stolen-bike branches and its Dakota workshop prefab context. Original photograph, device code, optional confrontation, bike entitlement, journal and checkpoint nodes remain native.',
   'MQ050 original main reference retains offsite discovery wait, named-car spawn, CameraFocus key placement, Johnny scene, exact key inventory check, mount alternative, vehicle entitlement, checkpoint and native cleanup. Exact original q101_done parent pause is retained.',
   'Wrappers set only private Ready/Revision/Issued/Entered/Finished fields. They add no quest fact or journal reset, item grant, vehicle unlock, reward modification, or debug entry.',
   'Completed/progressed/unknown states defer. No continuation slice for unfinished vehicles has been source-proven.'
  ],
  'resolved_since_candidate01':{
   'world_workspot_references':presentation['world_references'],
   'world_scan':{'archives':world['archives'],'errors_retained':len(world['errors']),'requested_vehicle_nodes_resolved':True},
   'presentation':'The three world NodeRefs now resolve. The remaining issue is confirmed animation item actions, rather than missing workspot identity. MQ029 corpse equips Items.crowd_cigarette_i_stick; MQ050 equips Items.crowd_int_apparel_002__h0_001_ma_specs__silverhand. MQ029 garage gun-named workspot has no item action in its exact idle clip.',
   'encounter_assistance':'Two MQ003 workspots and their actual animation libraries audited in presentation_01.json, with current exact source pins. Johnny spawnSet owner witness from encounters/johnny_owner_01.json bound. Generic stand animation transition library requires bounded event muting or source-proven transition exclusion; grave workspot contains no item actions in its selected clips.'
  },
  'blocking_checks':[
   {'id':'vehicle_entitlement_atomicity','status':'UNPROVEN','detail':'Runtime IsVehiclePlayerUnlocked exact record checks are authoritative but sampled. Native SpecificVehicle VehicleAvailable NOR is an additional conservative condition; no claim of durable ownership equivalence is made.'},
   {'id':'vehicle_johnny_props','status':'CONFIRMED_REMEDIATION_REQUIRED','detail':'JV1 actor body policy does not itself suppress these workspot animation equip events. Need private scene/workspot binding preserving original location/voice/flow; no global world or shared workspot override is authorized.'},
   {'id':'mq050_prejournal_owner','status':'UNPROVEN_RESUME','detail':'Native controller may spawn car and inject world-container keys before journal activation. Named-car Spawned NOR and player key-zero protect concrete contradictions, but unowned car disappearance/world key persistence is not a certified fresh or continuation slice.'},
   {'id':'patch25_native_compile','status':'CURRENT_PROOF_PENDING','detail':'Official archives and original script cache changed during work. WK9.1 resolved targeted world/workspot/animation resources; final native source byte/semantic compatibility and full current-game script compilation remain external integration requirements.'}
  ],
  'recommendation':'Do not add proposed_boots to an XL loader yet. Retain both source candidates and exact contracts while closing the named blockers. Keep existing restored content and earned vehicle/items unchanged.',
  'game_writes':0,'save_writes':0,'native_fact_writes_performed':0,'installs':0,'launches':0
 }
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'path':str(out),'sha256':sha(out),'status':result['status']}))
if __name__=='__main__':main()
