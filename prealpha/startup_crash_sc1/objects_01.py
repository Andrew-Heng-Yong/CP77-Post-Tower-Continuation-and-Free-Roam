from pathlib import Path
import sys,struct,json,re
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
sys.path.insert(0,str(W/'tools'));from inspect_native_crash import Dump
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile,capstone
d=Dump(O/'report/Cyberpunk2077.dmp');base=next(b for b,_,n in d.modules if n=='Cyberpunk2077.exe')
pe=pefile.PE(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe',fast_load=True);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
def read(a,n):
 b=d.read(a,n)
 if b is not None:return b
 if base<=a<base+pe.OPTIONAL_HEADER.SizeOfImage:return pe.get_data(a-base,n)
 return None
def q(a):
 b=read(a,8);return struct.unpack('<Q',b)[0] if b is not None and len(b)==8 else 0
def fnv(s):
 h=0xcbf29ce484222325
 for b in s.encode():h=((h^b)*0x100000001b3)&0xffffffffffffffff
 return h
script=(W/'prealpha/loading_cover_lc2/candidate_01/compile_02/compiled.script').read_text(encoding='utf-8-sig')
names={fnv(n):n for n in re.findall(r'\bclass ([\w.]+)',script)}
for f in (W/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext').rglob('*.hpp'):
 for n in re.findall(r'NAME = "([^"]+)"',f.read_text(errors='replace')):names[fnv(n)]=n
def obj(a):
 vt=q(a);result={'address':hex(a),'vtable':d.module(vt) or hex(vt)}
 locator=q(vt-8);b=read(locator,24)
 if b and struct.unpack_from('<I',b)[0]==1:
  u=struct.unpack('<6I',b);x=read(base+u[3]+16,180)
  if x:result['cpp_type']=x.split(b'\0')[0].decode(errors='replace')
 getter=q(vt+8)
 if base<=getter<base+pe.OPTIONAL_HEADER.SizeOfImage:
  code=read(getter,30);result['getter']=[f'{i.address-base:x} {i.mnemonic} {i.op_str}' for i in cs.disasm(code,getter)]
  if code[:3]==b'\x48\x8b\x05':
   gp=getter+7+struct.unpack_from('<i',code,3)[0];typeptr=q(gp);name=q(typeptr+0x18)
   result['red_type']=names.get(name,hex(name))
 result['words']={hex(i):d.module(q(a+i)) or hex(q(a+i)) for i in range(0,0xb0,8)}
 return result
frames=json.loads((O/'unwind_01.json').read_text());out={}
for ix,reg in [(2,'rbx'),(2,'r15'),(6,'rbx'),(7,'r15'),(8,'rsi'),(9,'r15'),(10,'r12')]:
 a=int(frames[ix]['registers'][reg],16);out[str(ix)+':'+reg]=obj(a)
 if ix==8:
  for off in [0x150,0x718,0x868]:out['spawn+'+hex(off)]=obj(q(a+off) if off==0x150 else a+off)
(O/'objects_01.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
