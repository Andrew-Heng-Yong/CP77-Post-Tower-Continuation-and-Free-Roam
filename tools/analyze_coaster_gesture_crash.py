"""Verify the revision4 gesture crash using bounded native socket records.

Cyberpunk 2.31 offsets are based on local fault/caller disassembly. Exports
indices and counts only, without full dump, user strings or save attachments.
"""
import json
from pathlib import Path
import struct
from inspect_native_crash import Dump

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'Cyberpunk2077-20260926-175947-44584-20280'
d = Dump(Path(r'C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue')/REPORT/'Cyberpunk2077.dmp')
report = d.report()
assert report['fault']=='Cyberpunk2077.exe+0xc34905'
r = {k:int(v,16) for k,v in report['registers'].items()}
def u32(a): return struct.unpack('<I',d.read(a,4))[0]
def u64(a): return struct.unpack('<Q',d.read(a,8))[0]
context = u64(r['rsp']+8) # caller's saved rbx from c348bc
node = u64(context+8)
node_id = u32(node+0x40)
table, count = u64(node+0x30), u32(node+0x3c)
stamps = [u32(table+i*24) for i in range(count)]
assert (node_id,count,stamps)==(559,1,[0x10000])
assert r['r8']==0 and r['rax']==table+count*24
assert r['rcx']==u64(r['rax']+8)==0
assert report['exception_parameters']==['0x0','0x0']
result = dict(status='MATCHED_MISSING_SUCCESS_OUTPUT',report=REPORT,
              build_specific='Cyberpunk 2.31 / P4CL9778208',fault_rva='0xc34905',
              scene_node=node_id,requested_stamp={'name':0,'ordinal':0},
              available_stamps=[{'name':0,'ordinal':1}],output_count=count,
              read_one_past_output_table=True,null_destinations_pointer=True,
              instructions=['c348c1/c348c8: load output table/count from node+30/+3c',
                            'c348d6..c348ef: find requested packed stamp',
                            'c348d9: end-of-table falls through to c348f1',
                            'c348f1/c348f4: read nonexistent record destination count/pointer',
                            'c34905: dereference NULL destination array'],
              repair='Keep both native Success0 and Work Started1 sockets; Success may have no destinations.',
              limitation='Gesture visuals and normal ride exit still require a live check.')
out=ROOT/'research/b0_world_interactions/coaster_repeat_gesture/crash_evidence.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
