"""Independent exact EXE guard review using Windows unwind function boundaries."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
H=Path(__file__).resolve().parent
W=H.parents[2]
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_64

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path);args=ap.parse_args()
 p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe')
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest().upper()=='D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4','Changed game binary: investigate before reusing addresses'
 pe=struct.unpack_from('<I',b,60)[0]; op=pe+24; base=struct.unpack_from('<Q',b,op+24)[0]
 sh=op+struct.unpack_from('<H',b,pe+20)[0]; sec={}
 for i in range(struct.unpack_from('<H',b,pe+6)[0]):
  at=sh+i*40; name=b[at:at+8].rstrip(b'\0').decode(); vs,rva,size,raw=struct.unpack_from('<IIII',b,at+8); sec[name]=(rva,size,raw)
 def off(addr):return next(o+addr-base-r for r,z,o in sec.values() if base+r<=addr<base+r+z)
 md=Cs(CS_ARCH_X86,CS_MODE_64)
 pd,ps,po=sec['.pdata']; func=None; guard=0x140255e94
 for i in range(po,po+ps-11,12):
  a,c,u=struct.unpack_from('<III',b,i)
  if base+a<=guard<base+c:func=(base+a,base+c);break
 assert func is not None
 a,c=func; instr=[(hex(i.address),i.mnemonic,i.op_str)for i in md.disasm(b[off(a):off(a)+c-a],a)]
 mapping={int(addr,16):(mn,ops)for addr,mn,ops in instr}
 assert mapping[guard]==('test','byte ptr [rax + 0x70], 4')
 assert mapping[0x140255e98]==('jne','0x140255ea6')
 assert mapping[0x140255e9a][0]=='lea'
 i=next(md.disasm(b[off(0x140255e9a):off(0x140255e9a)+7],0x140255e9a))
 dest=i.address+i.size+struct.unpack('<i',i.bytes[-4:])[0]
 literal=b[off(dest):b.index(b'\0',off(dest))].decode()
 assert 'called with non-scripted object' in literal
 assert mapping[0x140255ea1]==('jmp','0x14025607b')
 result={'path':str(p),'sha256':hashlib.sha256(b).hexdigest().upper(),
 'method':'Independent PE .pdata boundaries and Capstone decode; native binaries read only, not loaded',
 'function_begin':hex(a),'function_end':hex(c),'guard_raw':b[off(guard):off(guard)+18].hex(),
 'literal_va':hex(dest),'literal':literal,'instructions':instr,
 'asserted_static_properties':['class flags bit2 at offset0x70 required','unset bit routes to non-scripted error','error branch skips normal continuation'],
 'not_observed':['historic returned IDs','live runtime class flags','actual callback delivery']}
 dest=args.out or H/'installed_game_guard.json'; assert not dest.exists(); dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print({k:v for k,v in result.items()if k!='instructions'})

if __name__=='__main__':main()
