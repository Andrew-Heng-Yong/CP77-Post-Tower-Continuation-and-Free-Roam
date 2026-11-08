from inspect_archivexl import *
def main():
 out=HERE/'trigger_helpers_01';out.mkdir(exist_ok=False);x=Binary(Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe'));saved={}
 def save(r):
  (s,e),ins=x.dis(r)
  if s not in saved:
   p=out/f'function_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8');saved[s]={'rva':s,'end_rva':e,'path':str(p),'sha256':hashlib.sha256(x.b[x.off(s):x.off(s)+e-s]).hexdigest().upper()}
  return ins
 for r in [0xedb834,0xedb878,0xdbcf30,0x2c7a650,0x2c7aaa0]:save(r)
 strings=[]
 for m in re.finditer(rb'[\x20-\x7e]*TriggerCondition[\x20-\x7e]*\0',x.b):
  r=x.rva(m.start());refs=x.refs(r);strings.append({'text':m.group()[:-1].decode(),'rva':r,'refs':refs,'functions':sorted({save(rr)[0].address-x.base for rr in refs})})
 (out/'manifest.json').write_text(json.dumps({'input':x.freshness(),'strings':strings,'functions':list(saved.values())},indent=2),encoding='utf8');print(json.dumps({'strings':strings,'functions':len(saved)},indent=2))
if __name__=='__main__':main()
