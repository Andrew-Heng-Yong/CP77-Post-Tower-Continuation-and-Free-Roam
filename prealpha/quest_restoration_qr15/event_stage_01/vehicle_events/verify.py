"""Source/byte controls for the bounded pending/sent/applied distinction.

These are source-proof controls, not game execution or gameplay tests.
No save, process, build or installed runtime writes are performed.
"""
from pathlib import Path
import argparse, copy, hashlib, json, re, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SCRIPT=ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01'
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source'))
from analyze import method
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
def rows(f):return f['instructions']
def text(f):return '\n'.join(r['mnemonic']+' '+r['operands'] for r in rows(f))
def row(f,rva):return next(r for r in rows(f) if int(r['rva'],16)==rva)
def exact(f,rva,mnemonic,operands):
 r=row(f,rva);return r['mnemonic']==mnemonic and r['operands']==operands
def pure_forward(body):
 return re.sub(r'\s+','',body.split('{',1)[1].rsplit('}',1)[0])=='returnEntityNotificationType.SendThisEventToEntity;'
def six_disable(body):
 return all(s in body for s in ['let size: Int32 = 6;', 'while i < size', 'IntEnum<EVehicleDoor>(i)', 'VehicleDoorInteractionState.Disabled', 'this.QueuePSEvent(this, InteractionStateChangeEvent);']) and body.index('this.QueuePSEvent')<body.index('i += 1;')
def consumes_before_dispatch(f):
 return exact(f,0x1A5160,'dec','dword ptr [rbx + 0x10]') and exact(f,0x1A519F,'call','0x1401a5200')
def native_out_is_immediate(f):
 return exact(f,0x565BF6,'call','rbx') and exact(f,0x565C05,'call','0x1404f1d80') and exact(f,0x565C13,'call','0x1405649f4') and exact(f,0x565C1D,'xor','al, al')
def fnv(text):
 result=0xCBF29CE484222325
 for value in text.encode():result=((result^value)*0x100000001B3)&0xFFFFFFFFFFFFFFFF
 return result

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--out-dir',type=Path,default=HERE)
 args=ap.parse_args()
 output_dir=args.out_dir.resolve()
 assert output_dir==HERE or output_dir.is_relative_to(HERE),'Output must stay in this evidence directory'
 output_dir.mkdir(parents=True,exist_ok=True)
 out=output_dir/'verification_01.json'; excerpts=output_dir/'source_contract_01.json'
 assert not out.exists() and not excerpts.exists(),'Fresh outputs required'
 checks=[]
 def ck(name,ok,evidence):
  checks.append({'name':name,'pass':bool(ok),'evidence':evidence})
  assert ok,name
 manifest=json.loads((SCRIPT/'manifest.json').read_text())
 ck('pinned_current_base_decompile',sha(SCRIPT/'base.script')==manifest['decompiled_sha256'],manifest['decompiled_sha256'])
 for record in manifest['classes']:
  ck('pinned_current_script_'+record['class'],sha(record['path'])==record['sha256'],record['path'])
 base=(SCRIPT/'base.script').read_text(); ps=(SCRIPT/'VehicleComponentPS.script').read_text(); actor=(SCRIPT/'VehicleComponent.script').read_text()
 method_names=['GetVehicleControllerPS','GetHasStateBeenModifiedByQuest','SetHasStateBeenModifiedByQuest','OnVehicleQuestVisualDestructionEvent','OnToggleDoorWrapperEvent','OnVehicleQuestChangeDoorStateEvent','DisableAllVehInteractions','OnVehicleDoorInteractionStateChange','SetDoorInteractionState','ResetVehicleInteractionState','ResetVehicle']
 methods={name:method(ps,name) for name in method_names}
 methods['actor_visual']=method(actor,'OnVehicleQuestVisualDestructionEvent')
 graph_pin=json.loads((ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source/event_contract_01.json').read_text())['native_graph']
 ck('pinned_gameplay_raw_and_json',sha(graph_pin['raw'])==graph_pin['sha256'] and sha(graph_pin['json'])==graph_pin['json_sha256'],graph_pin)
 normalized=Resource(json.loads(Path(graph_pin['json']).read_text())).normalize();assert not normalized['errors']
 g=normalized['graphs']['root/1'];p103=g['nodes']['103']['payload'];p104=g['nodes']['104']['payload']
 ck('native_startup_sequence',all(e in g['edges'] for e in [['101','Out','102','In'],['102','Out','103','In'],['103','Out','104','In']]),'root/1 edges')
 ck('node103_explicit_controller_ps_route',p103['PSClassName']['$value']=='VehicleComponentPS' and p103['componentName']['$value']=='controller' and p103['isUiEvent']==0 and p103['isObjectPlayer']==0,'node103 payload')
 ck('node103_exact_nonaccumulating_visual_event',p103['event']['$type']=='VehicleQuestVisualDestructionEvent' and p103['event']['accumulate']==0,'node103 event')
 ck('node104_exact_toggle_door',p104['type']['$type']=='questToggleDoor_NodeType' and p104['type']['door']=='seat_front_right' and p104['type']['doorAction']=='DisableAllInteractions' and p104['type']['doorID']['$value']=='None','node104 payload')
 ck('authored104_enum_uses_normal_branch','DisableAllInteractions = 9,' in base and re.search(r'enum EVehicleDoor \{\s*seat_front_left = 0,\s*seat_front_right = 1,',base) is not None,'9<15,1<6,doorID None')
 ck('visual_ps_handler_only_forwards',pure_forward(methods['OnVehicleQuestVisualDestructionEvent']),methods['OnVehicleQuestVisualDestructionEvent'])
 ck('visual_actor_calls_native_two_layers',methods['actor_visual'].count('SetDestructionGridPointValues(')==2 and '0u, pointValues, evt.accumulate' in methods['actor_visual'] and '1u, pointValues, evt.accumulate' in methods['actor_visual'],'actor event body')
 ck('wrapper_queues_children_then_sets_generic_flag',six_disable(methods['DisableAllVehInteractions']) and methods['OnToggleDoorWrapperEvent'].index('this.OnVehicleQuestChangeDoorStateEvent')<methods['OnToggleDoorWrapperEvent'].index('this.SetHasStateBeenModifiedByQuest(true);'),'wrapper plus DisableAllVehInteractions')
 ck('door_state_is_separate_native_controller_owner','CreatePersistentID(this.GetMyEntityID(), n"VehicleController")' in methods['GetVehicleControllerPS'] and 'this.GetVehicleControllerPS().SetDoorInteractionState(door, state);' in methods['SetDoorInteractionState'],'current PS owner getter and setter')
 ck('generic_flag_persistent_and_not_monotonic','persistent let m_stateModifiedByQuest: Bool;' in ps and 'this.m_stateModifiedByQuest = set;' in methods['SetHasStateBeenModifiedByQuest'] and all('this.SetHasStateBeenModifiedByQuest(false);' in methods[n] for n in ['ResetVehicle','ResetVehicleInteractionState']),'field declaration and native reset helpers')
 ck('other_natural_writers_can_disable_all','defaultState.DisableAllInteractions()' in base and 'this.CreateAndSendDefaultStateEvent(door, state);' in base,'VehicleComponent default-state path; not a unique quest receipt')
 ck('enum_dispatch_semantics','DoNotNotifyEntity = 0,' in base and 'SendThisEventToEntity = 1,' in base and 'SendPSChangedEventToEntity = 2,' in base,'EntityNotificationType enum')
 natives=[json.loads((HERE/f'native_0{i}.json').read_text())for i in (1,2,3)]
 f={k:v for d in natives for k,v in d['functions'].items()}
 im=Image(); verified_instructions=0
 for name,body in f.items():
  for ins in rows(body):
   addr=int(ins['rva'],16);data=bytes.fromhex(ins['bytes']);assert im.data[im.off(addr):im.off(addr)+len(data)]==data,(name,ins)
   verified_instructions+=1
 ck('all_retained_instruction_bytes_match_pinned_exe',verified_instructions>2000,{'instructions':verified_instructions,'exe_sha256':im.sha})
 vt=natives[0]['tables']
 ck('actual_instance_and_update_vtables',vt['EventManagerNodeDefinition']['slots']['0x158']=='0x565b5c' and vt['ToggleDoorNodeType']['slots']['0x108']=='0x18f3d54' and vt['PersistencySystem']['slots']['0x1c8']=='0x1a5568' and vt['PersistencyQueueCallback']['slots']['0x0']=='0xe6ec4c',vt)
 ck('event_node_pid_includes_component',exact(f['event_node_pid'],0x1817C86,'mov','rbx, qword ptr [rcx + 0xa8]') and exact(f['event_node_pid'],0x1817CBC,'mov','qword ptr [rdi + 8], rbx'),'componentName+A8 -> PersistentID+8')
 ck('event103_out_after_request_without_ack',native_out_is_immediate(f['event_node_execute']) and natives[2]['constants']['out_literal']['ascii']=='Out','565BF6 ->565C05/13->565C1D; nil paths also commonOut')
 ck('queue_request_record_layout_and_endpoint','add rcx, 0x218' in text(f['persistency_queue_append']) and 'qword ptr [rcx + 0x10], rax' in text(f['persistency_queue_copy']) and 'add rdx, 0x18' in text(f['persistency_queue_copy']),'PID16,classptr8,eventhandle16; no quest/node acknowledgement identity')
 ck('queue_pop_precedes_handler_dispatch',consumes_before_dispatch(f['persistency_queue_drain']),'1A5160 ->1A519F')
 ck('entity_absence_can_drop_visual_forward',exact(f['persistency_forward_original_event'],0xE366AE,'je','0x140e366b8') and exact(f['persistency_forward_original_event'],0xE366B3,'call','0x1401a67b0') and exact(f['persistency_forward_original_event'],0xE366B8,'lea','rcx, [rsp + 0x20]'),'nil entity skips queue call and returns')
 ck('entity_queue_has_additional_lifecycle_rejection',exact(f['entity_queue_event'],0x1A67BE,'jbe','0x1401a67cc') and exact(f['entity_queue_event'],0x1A67C7,'call','0x1401a67d4'),'states6/7 reject event before entity queue append; names not inferred')
 ck('toggle104_queues_and_returns_nonwaiting',exact(f['toggle_door_execute'],0x18F3E47,'call','r14') and exact(f['toggle_door_execute'],0x18F3E61,'xor','al, al') and exact(f['vehicle_node_execute'],0x9A159D,'jne','0x1409a164c') and exact(f['vehicle_node_execute'],0x9A1667,'call','0x1401cc5ac'),'normal action path return0 -> VehicleNode Out')
 ck('toggle104_native_component_name_is_controller',exact(f['toggle_door_component_name'],0x8029B4,'movabs',f'rdi, {hex(fnv("controller"))}'),'native component CName constructor independently matches controller FNV1a')
 ck('toggle104_native_class_is_vehicle_component_ps',exact(f['toggle_door_execute'],0x18F3DA1,'movabs',f'rdx, {hex(fnv("VehicleComponentPS"))}'),'native RTTI class lookup independently matches VehicleComponentPS FNV1a')
 ck('toggle_wrapper_exact_native_type',natives[2]['toggle_wrapper_vtable']['get_type']=='0x193a610' and natives[2]['constants']['toggle_wrapper_name']['ascii']=='vehicleToggleDoorWrapperEvent' and exact(f['toggle_wrapper_registration'],0x16DC15E,'mov','qword ptr [rip + 0x24ec16b], rdi') and exact(f['toggle_wrapper_type_getter'],0x193A610,'mov','rax, qword ptr [rip + 0x228dcb9]'),'constructor VT33F4CD8; registration/getter same RTTI global3BC82D0')
 ck('toggle_cold_errors_also_return_common_zero',exact(f['toggle_door_cold'],0x25F98EB,'jmp','0x1418f3e5c') and exact(f['toggle_door_cold'],0x25F9993,'jmp','0x1418f3e5c'),'cold paths retained; exact104 takes normal branch')
 ck('native_door_controller_state_store',exact(f['native_door_state_setter'],0xEE2B11,'shl','rbx, 6') and exact(f['native_door_state_setter'],0xEE2B15,'mov','dword ptr [rbx + rsi + 0xa0], edi'),'state DWORD per door at controller+0xA0+0x40*door')
 ck('presave_refresh_visits_ps_records_not_queue',exact(f['presave_record_callback'],0x2165095,'call','0x142164c10') and exact(natives[1]['spans']['presave_record_refresh_complete'],0x2164C2C,'add','rcx, 0x48') and exact(f['presave_record_serialization_gate'],0x216511C,'call','0x1404b5f70'),'PreSave -> record-snapshot job -> actual record serialization')
 ck('queue_destructor_drops_handles_and_clears_count',exact(f['persistency_destructor'],0xA22011,'lea','rcx, [rbx + 0x218]') and exact(f['persistency_queue_clear'],0xA214CB,'and','dword ptr [rbx + 0xc], 0') and exact(f['persistency_queue_release_items'],0x2182CA,'call','0x140198368'),'queue root+218; release eventhandles; clear queue count')
 ck('save_writer_requires_ps_selection_flags',exact(f['persistency_save'],0x2A35470,'mov','al, byte ptr [rdi + 0x79]') and any('al, 4'==r['operands'] for r in rows(f['persistency_save'])),'PS2 record selection source; queue is not a PS record')
 mutant=copy.deepcopy(f['persistency_queue_drain']);row(mutant,0x1A5160)['mnemonic']='inc'
 ck('mutation_pop_after_or_not_pop_rejected',not consumes_before_dispatch(mutant),'in-memory source-proof mutant only')
 mutant=copy.deepcopy(f['event_node_execute']);row(mutant,0x565C1D)['mnemonic']='mov';row(mutant,0x565C1D)['operands']='al, 1'
 ck('mutation_waiting_return_rejected',not native_out_is_immediate(mutant),'in-memory source-proof mutant only')
 ck('mutation_five_doors_rejected',not six_disable(methods['DisableAllVehInteractions'].replace('let size: Int32 = 6;','let size: Int32 = 5;')),'current loop contract independent of graph serialization')
 ck('mutation_visual_ps_receipt_writer_rejected',not pure_forward(methods['OnVehicleQuestVisualDestructionEvent'].replace('{','{ this.SetHasStateBeenModifiedByQuest(true);',1)),'added receipt changes source proof')
 excerpts.write_text(json.dumps({'source_pins':manifest['classes'],'base_script_sha256':sha(SCRIPT/'base.script'),'graph':graph_pin,'nodes':{'103':p103,'104':p104},'methods':methods,'generic_flag_writers':[{'line':i+1,'text':l.strip()}for i,l in enumerate(ps.splitlines())if 'm_stateModifiedByQuest =' in l or 'SetHasStateBeenModifiedByQuest(' in l],'limits':'Native handler delivery/byte controls establish source dataflow only. No event was dispatched. No original save or live object was inspected.'},indent=2)+'\n',encoding='utf-8')
 result={'status':'SOURCE_PATHS_VERIFIED_NO_SAFE_STAGE_GUARD','checks':checks,'controls':len(checks),'native_instructions_verified':verified_instructions,'decision':'No automatic replay or skip is justified from Out, pending-queue absence, generic flags or missing PS keys. These do not prove applied setup.','game_calls':0,'save_reads':0,'runtime_changes':0}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'controls':len(checks),'native_instructions_verified':verified_instructions}))
if __name__=='__main__':main()
