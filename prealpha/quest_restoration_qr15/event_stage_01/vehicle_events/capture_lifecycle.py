"""Bounded successor native capture; preserves native_01 unchanged."""
from pathlib import Path
import json, struct, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

FUNCTIONS={
 'presave_parallel_job_callback':0x2164F30,
 'presave_parallel_job_builder':0x2164A00,
 'presave_record_callback':0x2165040,
 'presave_completion_callback':0x2164E10,
 'presave_record_serialization_gate':0x21650D0,
 'persistency_destructor':0xA21FF0,
 'persistency_queue_destructor_thunk':0xA21484,
 'persistency_queue_clear':0xA21490,
 'persistency_queue_release_items':0x2182A4,
 'entity_queue_append':0x1A6820,
 'toggle_door_component_name':0x8029A0,
 'toggle_door_component_name_init':0x136E60,
 'native_door_state_setter_registration':0x5E5FE4,
 'native_door_state_setter':0xEE2A70,
}
SPANS={'presave_record_refresh_complete':(0x2164C10,0x2164D1B)}

def main():
 out=HERE/'native_02.json';assert not out.exists()
 im=Image();functions={}
 for name,addr in FUNCTIONS.items():
  f=im.disasm(addr)
  if f.get('end_rva') is None:
   rows=[]
   for row in f['instructions']:
    rows.append(row)
    if row['mnemonic'] in ('ret','jmp'):break
   f['instructions']=rows
   f['boundary_limit']='No unwind boundary; bounded at first unconditional JMP/RET, at most256 bytes'
  functions[name]=f
 spans={}
 for name,(a,b) in SPANS.items():
  spans[name]={'begin_rva':hex(a),'end_rva':hex(b),'boundary_limit':'Explicit local continuation span, not inferred function boundary','instructions':[{'rva':hex(i.address-im.base),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in im.md.disasm(im.data[im.off(a):im.off(a)+b-a],im.base+a)]}
 out.write_text(json.dumps({'exe_sha256':im.sha,'functions':functions,'spans':spans,'static_read_only':True},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(out),'functions':len(functions),'spans':len(spans)}))
if __name__=='__main__':main()
