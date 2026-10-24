from pathlib import Path
import sys,struct,json,re,bisect
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
sys.path.insert(0,str(W/'tools'));from inspect_native_crash import Dump
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile,capstone
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
d=Dump(O/'report/Cyberpunk2077.dmp');r={k:int(v,16) for k,v in d.report()['registers'].items()};base=next(b for b,_,n in d.modules if n=='Cyberpunk2077.exe')
pe=pefile.PE(str(G/'bin/x64/Cyberpunk2077.exe'));cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
functions=sorted((x.struct.BeginAddress,x.struct.EndAddress,x.struct.UnwindData) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
starts=[f[0] for f in functions]
def fn(addr):
 i=bisect.bisect_right(starts,addr)-1
 return functions[i] if i>=0 and functions[i][0]<=addr<functions[i][1] else None
lines=[];candidates=[];seen=set()
for delta in range(0,8192,8):
 b=d.read(r['rsp']+delta,8)
 if not b:break
 a=struct.unpack('<Q',b)[0];label=d.module(a)
 if label and label.startswith('Cyberpunk2077.exe'):
  f=fn(a-base)
  if f:
   candidates.append({'stack_offset':hex(delta),'rva':hex(a-base),'function':hex(f[0])})
   if f[0] not in seen:
    seen.add(f[0]);lines.append('\nFUNCTION '+hex(f[0])+' stack+'+hex(delta)+' return '+hex(a-base))
    code=pe.get_data(f[0],min(f[1]-f[0],1700))
    lines.extend(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in cs.disasm(code,f[0]))
f=fn(r['rip']-base);lines.append('\nFAULT '+str(f));lines.extend(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in cs.disasm(pe.get_data(f[0],f[1]-f[0]),f[0]))
(O/'stack_code_candidates.json').write_text(json.dumps(candidates,indent=2));(O/'code_01.asm').write_text('\n'.join(lines))
print(json.dumps({'stack_candidates_not_unwound':candidates[:45],'functions_disassembled':len(seen),'fault_function':f},indent=2))
