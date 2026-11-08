from inspect_archivexl import *
def main():
 out=HERE/'trigger_resolution_01';out.mkdir(exist_ok=False);x=Binary(Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe'));saved={}
 def save(r):
  (s,e),ins=x.dis(r)
  if s not in saved:
   p=out/f'function_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8');saved[s]={'rva':s,'end_rva':e,'path':str(p),'sha256':hashlib.sha256(x.b[x.off(s):x.off(s)+e-s]).hexdigest().upper()}
  return ins
 targets=[0x2fc8b8,0x2ac524,0x9a018c,0x7c2668,0x88e0b0]
 calls={}
 for r in targets:
  ins=save(r);cs=[i.operands[0].imm-x.base for i in ins if i.mnemonic=='call' and i.operands[0].type==capstone.x86.X86_OP_IMM];calls[hex(r)]=[hex(v) for v in cs]
  if r in [0x2fc8b8,0x2ac524,0x9a018c]:
   for c in cs:save(c)
 (out/'manifest.json').write_text(json.dumps({'input':x.freshness(),'direct_calls':calls,'functions':list(saved.values())},indent=2),encoding='utf8');print(json.dumps({'direct_calls':calls,'functions':len(saved)},indent=2))
if __name__=='__main__':main()
