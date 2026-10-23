"""Bounded numeric evidence from the original cheer lookup fault; no save data."""
import json
import struct
from pathlib import Path
from inspect_native_crash import Dump

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'Cyberpunk2077-20260926-164546-34572-12060'
d = Dump(Path(r'C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue') / REPORT / 'Cyberpunk2077.dmp')
r = d.report()
assert r['fault'] == 'Cyberpunk2077.exe+0x1cf71f'
regs = {k: int(v, 16) for k, v in r['registers'].items()}
def value(a, kind='Q'):
    data = d.read(a, struct.calcsize(kind))
    return struct.unpack('<'+kind, data)[0] if data is not None else None

container = regs['rsi']
array = value(container + 0x50)
capacity, count = value(container+0x58, 'I'), value(container+0x5c, 'I')
assert count is not None and count <= 32
bad_pointer = regs['rcx']-0x100  # 1cf64c adds animset+100 before lookup
entries = []
for i in range(count):
    ptr = value(array+i*16)
    ref = value(array+i*16+8)
    vtable = value(ptr) if ptr is not None else None
    entries.append(dict(index=i, pointer=hex(ptr) if ptr is not None else None,
                        reference_counter=hex(ref) if ref is not None else None,
                        captured_memory=vtable is not None,
                        reference_count_words=[value(ref+j*4,'I') for j in range(2)] if ref else None,
                        vtable_module=d.module(vtable) if vtable is not None else None,
                        fault_slot=ptr==bad_pointer))
base_owner = value(container+8)
base_resource = value(base_owner) if base_owner else None
result = dict(status='CONFIRMED_INVALID_ANIMATION_LOOKUP_HANDLE_SOURCE_UNRESOLVED',
              report=REPORT, fault_rva='0x1cf71f',
              requested_name_hash=hex(value(regs['rdx'])),
              handle_capacity=capacity,handle_count=count,entries=entries,
              base_resource_captured=bool(base_resource and d.read(base_resource,16)),
              limitation='Numeric slots establish invalid handle before lookup, not the writer or scene resource index. No safe cinematic restoration follows from this alone.')
out=ROOT/'research/b0_world_interactions/coaster_animation_audit/cinematic_lookup/crash_evidence.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
