"""S25 Inactive service-sidejob contract; no inferred save history or resets."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
CAP='research/sidejobs_s23/live_20261016_01/capture.json'
DEBT='research/sidejobs_s25/services/native_01/raw/base/quest/bugfixing/minor_quests/mq033/mq033_quest_bugfixes.questphase'
VICTOR='research/b0_vendor_rollout/special_scene_sources/raw/base/quest/tertiary_characters/default_dialogues/victor_vector_default.scene'
B0VICTOR='archive/b0_story_eight/source/towercontinued/b0_story_eight/viktor.scene'
GUN='research/sidejobs_s24/services/native_01/raw/base/quest/main_quests/prologue/q001/phases/q001_wilson.questphase'
CONTACT='research/sidejobs_s24/services/native_01/raw/base/quest/main_quests/prologue/q001/q001.questphase'
WILSON='research/b0_wilson_vendor/dialogue_extract/raw/base/open_world/vendors/watson/little_china/wat_lch_gunsmith_01/wat_lch_gunsmith_01.scene'
BODY='archive/b0_wilson_vendor/source/towercontinued/b0_wilson_vendor/body.questphase'
SHOP='archive/b0_wilson_vendor/source/towercontinued/b0_wilson_vendor/shop.scene'
LEASE='prealpha/sidejobs_s23/base_b/build/base_b_02/source/towercontinued/b0_wilson_vendor/owner.questphase'
BASELINE='redscript/PTFR_RestorationBaseline/RestorationBaseline.reds'

def gun_contract(captured):
 from inspect import graphs,SafeResource,reach
 job=next(j for j in captured if j['id']=='sq_q001_wilson')
 original=graphs(ROOT/(GUN.replace('/raw/','/json/')+'.json'))['root']
 ids=[41,46,49,50,51,52,53,54,55,56,61,65]
 r=SafeResource(read(ROOT/(WILSON.replace('/raw/','/json/')+'.json')))
 ns={n['nodeId']['id']:n for n in r.payload(r.obj['Data']['RootChunk'])['sceneGraph']['graph']}
 # Retain original output sockets, changing only these bounded routes.  The
 # full first-meet staging/prop is deliberately not a claim of this adapter.
 changed={0:[[[678,0]]],678:[[[224,1]]],224:[[[42,0],[415,1]]],277:[[[281,1]]],455:[[[447,0]]],215:[[[190,0]]],190:[[],[[177,0]]]}
 for i,outs in changed.items():
  for k,dests in enumerate(outs):
   ns[i]['outputSockets'][k]['destinations']=[{'nodeId':{'id':a},'isockStamp':{'ordinal':b}} for a,b in dests]
 keep=sorted(reach(ns,[0]))
 assert not ({44,408,658,653,39,169,172,582}&set(keep))
 scene_edges={str(i):[[[d['nodeId']['id'],d['isockStamp']['ordinal']] for d in o['destinations']] for o in ns[i]['outputSockets']] for i in keep}
 return {'id':job['id'],'ids':[job['id']],'title':'The Gun','key':'GUN','tag':'PTFRS25_GUN',
 'depot':r'towercontinued\sidejobs_s25\services\gun_fresh.questphase',
 'facts_equal':dict.fromkeys(['wilson_met','q001_wilson_shop_tutorial_seen','q001_wilson_sms_tut','wat_lch_gun_01_met','q001_spawn_wilson_attention','q101_spawn_wilson_attention','q001_wilson_shooting_range','wilson_default_shooting_tutorial','mq011_active','PTFRB0WV_QuestOwns','PTFRB0WV_Near','PTFRB0WV_SpawnActionOut','PTFRB0WV_ActorDistanceGate','PTFRB0WV_Excluded','PTFRBASE_Suspended'],0)|{'PTFRB0WV_Ready':1,'PTFRB0WV_Enabled':1,'wat_lch_gunsmith_01_default_on':1},
 'fact_ranges':{'q001_used_mb_elevator':{'min':1,'max':2147483647}},
 'journals':[{'path':j['path'],'class':j['class'],'states':[1]} for j in job['journals']]+[{'path':'contacts/wilson/q001_new_gun/01_wilson_msg_gun','class':'gameJournalPhoneMessage','states':[1]}],
 'reactivate_paths':[],'phone_dependencies':[],'native_source':GUN,'source_graph':'root','native_ids':ids,
 'native_edges':[e for e in original['edges'] if e[0] in ids and e[2] in ids],
 'native_depot':r'base\quest\main_quests\prologue\q001\phases\q001_wilson.questphase',
 'scene_native':WILSON,'scene_depot':r'towercontinued\sidejobs_s25\services\gun_order.scene','scene_ids':keep,'scene_edges':scene_edges,
 'body_current':BODY,'shop_current':SHOP,'body_depot':r'towercontinued\b0_wilson_vendor\body.questphase',
 'contact_source':CONTACT,'contact_source_node':168,'contact_target':'contacts/wilson',
 'native_inventory_gate':{'source_scene_node':281,'item':'Items.Preset_Q001_Lexington','quantity_less_than':1},
 'sourcepins':{p:sha(ROOT/p) for p in [GUN,WILSON,BODY,SHOP,CONTACT,LEASE,BASELINE]},
 'seam':'Inactive root/all native journal children and absent reward weapon; no native greeting/tutorial/progress facts. Existing B0 vendor is sole actor/distance owner; original bounded order/vendor/inventory/reward route.',
 'notes':['Original SMS/map/objective/tutorial startup retained. Eager q001_attention Reactivate/attention1 staging omitted: existing B0 identity supplies Wilson and baseline remains sole Near writer.',
 'Bounded native Ask about order path restored, not the first-meet greeting or held-gun prop staging. No synthetic item, payment or reward.',
 'Current Gun Succeeded remains protected. Native inventory check prevents already held Dying Night from admitting; native objective/fact/root guards additionally protect prior progress.',
 'S23 MQ011 lease/root unchanged; new body selector is false when S25 unissued/completed and leaves ordinary shop path exact.']}
def main():
 rev=sys.argv[1] if len(sys.argv)>1 else 'contract01'
 path=HERE/(rev+'.json');assert not path.exists(),path
 captured=read(ROOT/CAP)['second']['jobs']
 job=next(j for j in captured if j['id']=='mq045_victor_debt')
 paid={'id':job['id'],'ids':[job['id']],'title':'Paid in Full','key':'PAID','tag':'PTFRS25_PAID',
 'depot':r'towercontinued\sidejobs_s25\services\paid_fresh.questphase',
 'facts_equal':{'victor_debt_paid_full':0,'victor_debt_talk_active':0,
 'PTFRB0S4VIKTOR_Ready':1,'PTFRB0S4VIKTOR_Enabled':1,'PTFRB0S4VIKTOR_Excluded':0,
 'PTFRB0S4VIKTOR_QuestOwns':0,'PTFRB0S4_Suspended':0,'PTFRBASE_Suspended':0},
 'fact_ranges':{'q001_just_after_rd_scene':{'min':1,'max':2147483647},'victor_vector_default_on':{'min':1,'max':2147483647}},
 'journals':[{'path':j['path'],'class':j['class'],'states':[1]} for j in job['journals']],
 'reactivate_paths':[],'phone_dependencies':[],
 'native_source':DEBT,'source_graph':'root/21','native_ids':[13,8,9,12,10,11],
 'native_start':13,'native_finish':11,'native_start_socket':'In',
 'native_edges':[[13,'Out',8,'Active'],[8,'Out',9,'Active'],[9,'Out',12,'In'],[12,'Out',10,'Succeeded'],[10,'Out',11,'Succeeded']],
 'native_depot':r'base\quest\bugfixing\minor_quests\mq033\mq033_quest_bugfixes.questphase',
 'scene_native':VICTOR,'scene_current':B0VICTOR,'scene_depot':r'towercontinued\b0_story_eight\viktor.scene',
 'scene_options':[[351,1],[840,1]],
 'sourcepins':{p:sha(ROOT/p) for p in (DEBT,VICTOR,B0VICTOR)},
 'seam':'Inactive debt root/objective/description, unpaid and no active payment dialogue. Original native debt activation/completion slice and payment choices; no actor owner duplication.',
 'notes':['Native obsolete CYB-571237 bugfix-marker increment is excluded; all six actual quest payloads and edges kept.',
 'Only two previously hidden debt options are restored in the existing Viktor scene, preserving native payment conditions and adding owned Issued/Active-root gating.',
 'No money debit, reward, completion, actor spawn, inventory or cyberware policy is fabricated by wrapper.',
 'Current capture Succeeded is a protected negative control, not a fresh fixture.']}
 contract={'schema':1,'status':'BUILT_SOURCE_NOT_LIVE_PROOF','policy':'Only Inactive R4 roots may newly activate; all prior owners and restored progress stay unchanged.',
 'capture':CAP,'capture_sha256':sha(ROOT/CAP),'owners':[paid,gun_contract(captured)],
 'override_donors':{r'towercontinued\b0_story_eight\viktor.scene':{'source':B0VICTOR,'sha256':sha(ROOT/B0VICTOR),'archive':'TowerContinued_PreAlpha.archive'},r'towercontinued\b0_wilson_vendor\body.questphase':{'source':BODY,'sha256':sha(ROOT/BODY),'archive':'TowerContinued_PreAlpha.archive'}}}
 path.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8');print(json.dumps({'contract':str(path),'owners':len(contract['owners'])}))
if __name__=='__main__':main()
