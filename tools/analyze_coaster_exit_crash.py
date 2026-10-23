"""Bounded build-specific evidence for the revision3 coaster exit crash.

Only native resource indices/counts/registers are read; no strings, saves,
screenshots or full memory exports. Stack addresses are not symbolized frames.
"""
import json
from pathlib import Path
import struct
from inspect_native_crash import Dump

ROOT = Path(__file__).resolve().parent.parent
REPORT = 'Cyberpunk2077-20260926-170811-19716-21228'
d = Dump(Path(r'C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue') / REPORT / 'Cyberpunk2077.dmp')
r = d.report()
assert r['fault'] == 'Cyberpunk2077.exe+0x1d173be'
regs = {k:int(v,16) for k,v in r['registers'].items()}
def u32(a): return struct.unpack('<I',d.read(a,4))[0]
def u64(a): return struct.unpack('<Q',d.read(a,8))[0]
requested = u32(regs['r9'])
table = u64(regs['r8']+0x70)
capacity, count = u32(regs['r8']+0x78), u32(regs['r8']+0x7c)
# Native copy instruction indexes this handle array by a 16-byte stride.
assert regs['rdx'] == table + requested*16
assert u64(regs['rdx']+8) == regs['rax'] == 0x1000100010001
assert (requested, capacity, count) == (6,1,1)
# Selected resource-kind descriptor is table-base + 7*0x28; native player
# init's final tailcall545480 reads definition+d8 and requests kind7.
base = next(b for b,_,n in d.modules if n=='Cyberpunk2077.exe')
assert regs['r14']-base == 0x47be1e8
player = u64(regs['rsp']+0xf8)
assert u32(player)==1 and u32(player+0xd8)==6
result = dict(status='MATCHED_OUT_OF_BOUNDS_PLAYER_LIPSYNC',report=REPORT,
              build_specific='Cyberpunk 2.31 / P4CL9778208',fault_rva='0x1d173be',
              resource_kind=7,player_actor_id=1,player_lipsync_index=requested,
              live_table_count=count,live_table_capacity=capacity,
              invalid_reference_counter='0x1000100010001',
              instructions=['1225a3c..1225a58: player definition+d8 -> tailcall545480',
                            '5454b4: resource kind7; 544164 ->544510',
                            '1d173a0..1d173be: index*16, read handle, increment invalid counter'],
              fix='Retain original V lipsync resource only and rebase player6->0; no exit animation/edge changes.',
              uncertainty='Why the live localized table has only one entry is not proven; repaired behavior requires live validation.')
out=ROOT/'research/b0_world_interactions/coaster_hands_binding/exit_crash_evidence.json'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
