"""Bounded fresh disassembly of exact integration paths and address resolver."""
from inspect_archivexl import *

def main():
 out=HERE/'integration_capture_02';out.mkdir(exist_ok=False);x=Binary(DLL);saved={};warnings=['integration_capture_01 preserved: RED4ext leaf resolver exceeded initial128byte leaf bound; no complete manifest claimed']
 def save(r,rawlen=None,binary=x,prefix='axl'):
  if rawlen is None:(s,e),ins=binary.dis(r)
  else:
   s=r;e=r+rawlen;ins=list(binary.md.disasm(binary.b[binary.off(s):binary.off(e)],binary.base+s))
  p=out/f'{prefix}_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-binary.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8');saved[p.name]={'rva':s,'end_rva':e,'path':str(p),'sha256':hashlib.sha256(binary.b[binary.off(s):binary.off(e)]).hexdigest().upper(),'capture':'explicit span includes split exception-table fragments' if rawlen else 'exception-table bounds'}
  return ins
 for r,l in [(0xf6470,None),(0xf42b0,None),(0xf4a90,None),(0x130a00,0xc0),(0x122630,None),(0x122680,None),(0x115680,None),(0xf4de0,None),(0xf4ea0,None),(0xf5a10,None),(0xf6160,None),(0xf4e80,None),(0xf4e40,None),(0xf4e00,None),(0x120bb0,None),(0xf6dd0,None)]:save(r,l)
 red=Binary(DLL.parents[2]/'RED4ext.dll');exports=[]
 for s in red.pe.DIRECTORY_ENTRY_EXPORT.symbols:
  if s.name and s.name.decode()=='RED4ext_ResolveAddress':
   ins=save(s.address,binary=red,prefix='red4ext');exports.append({'name':s.name.decode(),'rva':s.address,'direct_calls':[i.operands[0].imm-red.base for i in ins if i.mnemonic in ['call','jmp'] and i.operands[0].type==capstone.x86.X86_OP_IMM]})
 for e in exports:
  for t in e['direct_calls']:save(t,0x200,binary=red,prefix='red4ext')
 report={'inputs':[x.freshness(),red.freshness()],'exports':exports,'files':saved,'warnings':warnings,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()}
 (out/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'exports':exports,'files':list(saved),'inputs':report['inputs']},indent=2))

if __name__=='__main__':main()
