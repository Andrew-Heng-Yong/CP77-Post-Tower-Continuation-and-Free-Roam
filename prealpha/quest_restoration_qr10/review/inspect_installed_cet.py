"""Independent static PE inspection; loads Capstone only, never game/CET DLLs."""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys
H=Path(__file__).resolve().parent
W=H.parents[2]
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'))
import capstone

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path);args=ap.parse_args()
 p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks.asi')
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest().upper()=='ACB12B25CFCF77C3F5A84DF7CD4F4AE5074B8269E7C7389F349E12B237F88D6E','Changed CET binary: investigate before reusing addresses'
 pe=struct.unpack_from('<I',b,60)[0]; op=pe+24; base=struct.unpack_from('<Q',b,op+24)[0]
 sh=op+struct.unpack_from('<H',b,pe+20)[0]; sec={}
 for n in range(struct.unpack_from('<H',b,pe+6)[0]):
  s=sh+n*40; name=b[s:s+8].rstrip(b'\0').decode(); vs,rva,sz,off=struct.unpack_from('<IIII',b,s+8); sec[name]=(rva,sz,off)
 def va(off):
  return next(base+r+off-o for r,z,o in sec.values() if o<=off<o+z)
 def off(addr):
  return next(o+addr-base-r for r,z,o in sec.values() if base+r<=addr<base+r+z)
 pd,ps,po=sec['.pdata']; funcs=[]
 for i in range(po,po+ps-11,12):
  begin,end,unwind=struct.unpack_from('<III',b,i)
  if begin and end>begin:funcs.append((base+begin,base+end,unwind))
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.skipdata=True
 prefix=b.index(b'$LuaProxy$'); target=va(prefix)
 r,z,o=sec['.text']; matches=[]
 pattern=re.compile(r'\[rip ([+-]) (0x[0-9a-f]+)\]')
 for addr,size,mn,ops in md.disasm_lite(b[o:o+z],base+r):
  match=pattern.search(ops)
  if match:
   dest=addr+size+int(match[2],16)*(1 if match[1]=='+' else -1)
   if target-16<=dest<target+16:
    func=next(((a,c)for a,c,u in funcs if a<=addr<c),None)
    row={'address':hex(addr),'instruction':mn+' '+ops,'destination':hex(dest),'function':None}
    if func:
     a,c=func; row['function']={'begin':hex(a),'end':hex(c),'file_offset':hex(off(a)),
      'instructions':[(hex(x),m,p)for x,s,m,p in md.disasm_lite(b[off(a):off(a)+c-a],a)]}
    matches.append(row)
 callee=0x1800bb4c0
 a,c=next((a,c)for a,c,u in funcs if a<=callee<c)
 callee_rows=[(hex(x),m,p)for x,s,m,p in md.disasm_lite(b[off(a):off(a)+c-a],a)]
 assert ('0x1800bb4e1','mov','ebx, r9d')in callee_rows
 assert ('0x1800bb65c','mov','dword ptr [rsi + 0x70], ebx')in callee_rows
 assert any(('0x1800b2e52','mov','r9d, 2')in row['function']['instructions']and ('0x1800b2e5b','call','0x1800bb4c0')in row['function']['instructions']for row in matches if row['function'])
 result={'method':'Independent PE .pdata function boundary parsing + Capstone static disassembly; no binary execution',
  'path':str(p),'sha256':hashlib.sha256(b).hexdigest().upper(),'prefix_offset':hex(prefix),'prefix_va':hex(target),'matches':matches,
  'capstone_version':capstone.__version__,'base_constructor':{'begin':hex(a),'end':hex(c),'instructions':callee_rows}}
 dest=args.out or H/'installed_cet_proxy_02.json'; assert not dest.exists(); dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print({'sha256':result['sha256'],'matches':[(r['address'],r['instruction'],r['function']['begin']if r['function']else None)for r in matches]})

if __name__=='__main__':main()
