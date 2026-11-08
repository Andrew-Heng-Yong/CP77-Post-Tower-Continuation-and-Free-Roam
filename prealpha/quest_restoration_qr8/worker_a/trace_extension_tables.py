"""Capture class virtual tables anchored to GetName and adjacent native functions."""
from inspect_archivexl import *

def main():
 out=HERE/'extension_tables_01';out.mkdir(exist_ok=False);x=Binary(DLL);rows=[];saved={}
 def save(r):
  (s,e),ins=x.dis(r)
  if s not in saved:
   p=out/f'function_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8')
   saved[s]={'rva':s,'end_rva':e,'path':str(p),'sha256':hashlib.sha256(x.b[x.off(s):x.off(s)+e-s]).hexdigest().upper()}
  return s
 for name,r in [('QuestPhase',0xf4de0),('ResourcePatch',0x115660),('WorldStreaming',0x12dd80)]:
  refs=[]
  for m in re.finditer(re.escape(struct.pack('<Q',x.base+r)),x.b):
   a=x.rva(m.start());entries=[]
   for off in range(-32,112,8):
    v=struct.unpack_from('<Q',x.b,m.start()+off)[0]-x.base
    code=x.text.VirtualAddress<=v<x.text.VirtualAddress+x.text.SizeOfRawData
    entries.append({'relative_slot':off,'rva':v,'function':save(v) if code else None})
   refs.append({'name_pointer_rva':a,'table_entries':entries,'vtable_lea_xrefs':x.refs(a-16)})
  rows.append({'name':name,'getname_rva':r,'tables':refs})
 # Capture all exception-table functions in bounded quest-specific code span.
 for s,e in x.bounds:
  if 0xf4c00<=s<0xf6470:save(s)
 (out/'manifest.json').write_text(json.dumps({'input':x.freshness(),'tables':rows,'functions':list(saved.values())},indent=2),encoding='utf8')
 print(json.dumps({'tables':rows,'functions':len(saved)},indent=2))

if __name__=='__main__':main()
