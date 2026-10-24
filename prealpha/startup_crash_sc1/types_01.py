from pathlib import Path
import struct,sys,json
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
sys.path.insert(0,str(W/'tools'));from inspect_native_crash import Dump
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile,capstone
d=Dump(O/'report/Cyberpunk2077.dmp');base=next(b for b,_,n in d.modules if n=='Cyberpunk2077.exe')
pe=pefile.PE(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe',fast_load=True);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
def q(a):
 b=d.read(a,8)
 if b is not None:return struct.unpack('<Q',b)[0]
 if base<=a<base+pe.OPTIONAL_HEADER.SizeOfImage:
  v=struct.unpack('<Q',pe.get_data(a-base,8))[0]
  if pe.OPTIONAL_HEADER.ImageBase<=v<pe.OPTIONAL_HEADER.ImageBase+pe.OPTIONAL_HEADER.SizeOfImage:v+=base-pe.OPTIONAL_HEADER.ImageBase
  return v
 return 0
out={}
for vt in [0x3041098,0x30bce78,0x3059c88,0x3041e50,0x3057c68]:
 rows=[]
 for slot in range(10):
  p=q(base+vt+8*slot);r={'slot':slot,'p':hex(p),'code':[]}
  if base<=p<base+pe.OPTIONAL_HEADER.SizeOfImage:
   code=pe.get_data(p-base,28);r['code']=[f'{i.address:x} {i.mnemonic} {i.op_str}' for i in cs.disasm(code,p-base)]
   if code[:3]==b'\x48\x8b\x05':
    ptr=q(p+7+struct.unpack_from('<i',code,3)[0]);r['type']=hex(ptr);r['name']=hex(q(ptr+0x18))
  rows.append(r)
 out[hex(vt)]=rows
(O/'types_01.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
