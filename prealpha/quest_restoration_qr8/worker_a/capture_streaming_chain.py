from inspect_archivexl import *
def main():
 out=HERE/'streaming_chain_01';out.mkdir(exist_ok=False);x=Binary(DLL);saved={};refs=[]
 def save(r):
  (s,e),ins=x.dis(r)
  if s not in saved:
   p=out/f'function_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8');saved[s]={'rva':s,'end_rva':e,'path':str(p),'sha256':hashlib.sha256(x.b[x.off(s):x.off(s)+e-s]).hexdigest().upper()}
  return ins
 code=x.b[x.text.PointerToRawData:x.text.PointerToRawData+x.text.SizeOfRawData]
 for m in re.finditer(b'\xe8',code):
  k=m.start()
  if k+5>len(code):continue
  r=x.text.VirtualAddress+k;target=r+5+struct.unpack_from('<i',code,k+1)[0]
  if target==0x120bb0:
   ins=save(r)
   if any(i.address-x.base==r and i.mnemonic=='call' for i in ins):refs.append({'rva':r,'function':ins[0].address-x.base})
 for r in [0x122440,0x10a570,0x122630]:save(r)
 (out/'manifest.json').write_text(json.dumps({'input':x.freshness(),'streaming_world_load_callers':refs,'functions':list(saved.values())},indent=2),encoding='utf8');print(json.dumps({'callers':refs,'functions':list(saved)},indent=2))
if __name__=='__main__':main()
