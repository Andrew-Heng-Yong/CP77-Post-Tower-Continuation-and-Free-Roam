"""Bounded AMD64 PE unwind from copied dump, without running the game."""
from pathlib import Path
import sys,struct,bisect,json
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
sys.path.insert(0,str(W/'tools'));from inspect_native_crash import Dump
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
d=Dump(O/'report/Cyberpunk2077.dmp');regs={k:int(v,16) for k,v in d.report()['registers'].items()}
base=next(b for b,_,n in d.modules if n=='Cyberpunk2077.exe');pe=pefile.PE(str(G/'bin/x64/Cyberpunk2077.exe'),fast_load=True);pe.parse_data_directories(directories=[3])
functions=sorted((x.struct.BeginAddress,x.struct.EndAddress,x.struct.UnwindData) for x in pe.DIRECTORY_ENTRY_EXCEPTION);starts=[f[0] for f in functions]
names='rax rcx rdx rbx rsp rbp rsi rdi r8 r9 r10 r11 r12 r13 r14 r15'.split()
def q(a):
 b=d.read(a,8);assert b is not None,hex(a);return struct.unpack('<Q',b)[0]
def apply(f,control):
 begin,end,unwind=f;head=pe.get_data(unwind,4);vf,prolog,count,fr=head;version=vf&7;flags=vf>>3;assert version==1,(f,version)
 data=pe.get_data(unwind+4,2*((count+1)&~1)+12);i=0
 while i<count:
  off,op=data[i*2:i*2+2];info=op>>4;op&=15;i+=1
  arg=None
  if op in [1,4,5,8,9]:
   n=2 if op in [5,9] or op==1 and info==1 else 1
   arg=int.from_bytes(data[i*2:(i+n)*2],'little');i+=n
  if control-begin<off:continue
  if op==0:regs[names[info]]=q(regs['rsp']);regs['rsp']+=8
  elif op==1:regs['rsp']+=arg*8 if info==0 else arg
  elif op==2:regs['rsp']+=info*8+8
  elif op==3:regs['rsp']=regs[names[fr&15]]-(fr>>4)*16
  elif op==4:regs[names[info]]=q(regs['rsp']+arg*8)
  elif op==5:regs[names[info]]=q(regs['rsp']+arg)
  elif op in [8,9]:pass
  else:raise AssertionError(('unsupported unwind opcode',op,info))
 if flags&4:
  f2=struct.unpack_from('<III',data,2*((count+1)&~1));apply(f2,2**32)
frames=[]
for _ in range(40):
 rip=regs['rip'];label=d.module(rip)
 if not label or not label.startswith('Cyberpunk2077.exe'):break
 rva=rip-base;i=bisect.bisect_right(starts,rva)-1;f=functions[i] if i>=0 and functions[i][0]<=rva<functions[i][1] else None
 frames.append({'rva':hex(rva),'function':hex(f[0]) if f else None,'registers':{k:hex(v) for k,v in regs.items()}})
 if f:apply(f,rva)
 regs['rip']=q(regs['rsp']);regs['rsp']+=8
(O/'unwind_01.json').write_text(json.dumps(frames,indent=2))
print(json.dumps([{'rva':f['rva'],'function':f['function'],'rsp':f['registers']['rsp']} for f in frames],indent=2))
