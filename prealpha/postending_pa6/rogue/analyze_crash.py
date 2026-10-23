"""Bounded read-only Rogue crash evidence; never exports arbitrary heap strings."""
import json
from pathlib import Path
import struct
import sys
import hashlib

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'research/finalboards_dismissal/tooling/python'))
from inspect_native_crash import Dump
import pefile
import capstone

REPORT = 'Cyberpunk2077-20261013-210855-2864-25716'
DUMP = ROOT/'research/postending_pa6/live_20261014T011540242Z/crash/Cyberpunk2077.dmp'
d = Dump(DUMP)
r = d.report()
regs = {k:int(v,16) for k,v in r['registers'].items()}
base = next(b for b,_,n in d.modules if n == 'Cyberpunk2077.exe')
def u32(a): return struct.unpack('<I', d.read(a,4))[0]
def u64(a): return struct.unpack('<Q', d.read(a,8))[0]
requested = u32(regs['r9'])
table = u64(regs['r8'] + 0x70)
capacity, count = u32(regs['r8']+0x78), u32(regs['r8']+0x7c)
player = u64(regs['rsp']+0xf8)
r.update(report=REPORT, dump_sha256=hashlib.sha256(DUMP.read_bytes()).hexdigest().upper(), requested=requested, count=count, capacity=capacity,
         index_matches=regs['rdx']==table+requested*16,
         counter_matches=u64(regs['rdx']+8)==regs['rax'],
         descriptor_rva=hex(regs['r14']-base),
         player_actor_id=u32(player), player_lipsync_index=u32(player+0xd8))
exe = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe')
pe=pefile.PE(str(exe),fast_load=True)
decoder=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
r['fault_caller_disassembly']={hex(start):[f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in decoder.disasm(pe.get_data(start,size),start)] for start,size in [(0x1d173a0,48),(0x544510,220),(0x545480,100),(0x1225a3c,40)]}
out=ROOT/'research/postending_pa6/rogue/crash_probe_v2.json'
r['table_slots']=[{'slot':i,'object_null':u64(table+i*16)==0,'counter_null':u64(table+i*16+8)==0,'object_type_vtable':d.module(u64(u64(table+i*16))) if u64(table+i*16) and d.read(u64(table+i*16),8) else 'not in bounded dump'} for i in range(count)]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r,indent=2))
