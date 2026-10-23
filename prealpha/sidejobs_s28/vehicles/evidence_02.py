"""Consolidate existing current source extractions and bounded admission evidence."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
def write(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
 folder=ROOT/'research/sidejobs_s28/vehicles';pins={}
 def pin(p):pins[p]=sha(ROOT/p)
 rows=read(folder/'current_donors_02.json')['rows']
 for name in ['official_02','world_03','workspots_01','animations_01']:pin(f'research/sidejobs_s28/vehicles/{name}/inventory.json')
 pin('prealpha/sidejobs_s28/vehicles/evidence_02.py')
 donors={'status':'PASS_CURRENT_OFFICIAL_VEHICLE_DONORS','rows':rows,'source_pins':pins,'historical_comparison_sources':[],'metadata_only_sources':[],'limitations':['Records exact current archive extractions only; aggregate must compare final current archive bytes again. No runtime or gameplay claim.']}
 write(folder/'current_donors_03.json',donors)
 report=read(folder/'presentation_01.json')
 for p,h in report['source_pins'].items():
  assert sha(ROOT/p)==h;pin(p)
 # Bind transitive community witness as source data, not a new native controller.
 owner=read(ROOT/'research/sidejobs_s28/encounters/johnny_owner_01.json')
 for p in [owner['source'],owner['raw']]:pin(p)
 contract=read(ROOT/'prealpha/sidejobs_s28/vehicles/contracts_02.json')
 for p,h in contract['source_pins'].items():assert sha(ROOT/p)==h;pin(p)
 mainrow=contract['native_resources'][r'base\quest\minor_quests\mq050\mq050.questphase'];main=read(ROOT/mainrow['json'])['Data']['RootChunk']
 prefabs=[value(p['prefabNodeRef']) for p in main['phasePrefabs']]
 assert len(prefabs)==1 and prefabs[0].endswith('/loc_mq050_ken_block_tribute_questdesign_prefabBHPOTLQ')
 named=contract['native_runtime_predicates']['hoon_world_key']['node_ref']
 assert '/loc_mq050_ken_block_tribute_gameplay_prefabJPVRKTI/loc_mq050_ken_block_tribute_loot_prefabPU3FSXA/' in named
 references=[]
 for n in walk(main):
  if n.get('$type')=='questItemManagerNodeDefinition' and '#mq050_main_loot' in json.dumps(n):references.append(n['id'])
 assert references==[51],references
 evidence={'status':'PASS_BOUNDED_VEHICLE_SOURCE_CONTRACT','source_pins':pins,'current_donors':'research/sidejobs_s28/vehicles/current_donors_03.json',
 'native_runtime_predicates':contract['native_runtime_predicates'],
 'mq050_world_ownership':{'native_main_prefabs':prefabs,'crate_world_reference':named,'crate_item_write_node':51,'crate_spawn_or_activation_in_main':False,'reason':'Native main owns questdesign context, while its existing target crate is under sibling gameplay/loot context. Full main has no create/activate operation for that crate. Only its original key injection is gated behind admission.','scope_limit':'This establishes native ownership separation. Actual streaming availability and gameplay require live verification; absent or unresolved crate refuses admission.'},
 'prejournal_progress':{'named_car':'Original node42 vehicleSpawned predicate negated before entry.','world_key':'Immediate custom native predicate requires defined loaded crate and exact key quantity zero.','player_key':'Original node80 inventory predicate changed only to quantity Equal0.','vehicle_reward':'Immediate native script predicate and stable runtime samples both query exact durable unlock record.','safe_nonfresh_behavior':'Defer without claiming an owner, resetting facts/items/journals, respawning a car or replaying reward.'},
 'presentation':{'resources':3,'world_overrides':0,'technique':'Private clones of exact workspots with animation-event filter Mute; scene-native Global marker bound to original world NodeRef at identity transform. All original workspot command settings, stop operations, dialogue, timing and player photo clue preserved.','body_events_muted':5,'world_anchor_api_donor':r'base\open_world\street_stories\heywood\glenn\sts_hey_gle_03\scenes\sts_hey_gle_03_scene.scene'},
 'restrictions':['Fresh beginnings only; unsupported progress and existing owners defer.','No inventory grants, entitlement writes, fact resets, journal resets, debug inputs, owner restarts or gameplay reward changes.','No game, cache, save, framework or installed file writes.']}
 write(folder/'evidence_02.json',evidence)
 print(json.dumps({'donors':len(rows),'source_pins':len(pins)}))
if __name__=='__main__':main()
