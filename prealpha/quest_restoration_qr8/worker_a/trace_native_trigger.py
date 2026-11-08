"""Read-only exact questTriggerCondition native RTTI/construction capture."""
from inspect_archivexl import *
def main():
 out=HERE/'trigger_native_01';out.mkdir(exist_ok=False)
 x=Binary(Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe'));saved={}
 def save(r):
  (s,e),ins=x.dis(r)
  if s not in saved:
   p=out/f'function_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8');saved[s]={'rva':s,'end_rva':e,'path':str(p),'sha256':hashlib.sha256(x.b[x.off(s):x.off(s)+e-s]).hexdigest().upper()}
  return ins
 def lea(i):
  if i.mnemonic!='lea':return None
  os=[o for o in i.operands if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP]
  return i.address+i.size+os[0].mem.disp-x.base if len(os)==1 else None
 name='questTriggerCondition';hits=[]
 for m in re.finditer(re.escape(name.encode()+b'\0'),x.b):
  target=x.rva(m.start());refs=x.refs(target);candidates=[]
  for r in refs:
   ins=save(r)
   for i,a in enumerate(ins[:-1]):
    vt=lea(a)
    if vt is None or a.operands[0].reg!=capstone.x86.X86_REG_RAX:continue
    if not any(b.mnemonic=='mov' and b.op_str.endswith(', rax') and b.operands[0].type==capstone.x86.X86_OP_MEM and b.operands[0].mem.base==capstone.x86.X86_REG_RIP for b in ins[i+1:i+4]):continue
    try:
     ctor=struct.unpack_from('<Q',x.b,x.off(vt)+0xd8)[0]-x.base
     cin=save(ctor)
    except (pefile.PEFormatError,AssertionError,StopIteration):continue
    for b in cin:
     if b.mnemonic not in ['call','jmp'] or b.operands[0].type!=capstone.x86.X86_OP_IMM:continue
     c=b.operands[0].imm-x.base
     try:actual=save(c)
     except (pefile.PEFormatError,AssertionError,StopIteration):continue
     for j,v in enumerate(actual[:-1]):
      iv=lea(v)
      if iv is None:continue
      if not any(z.mnemonic=='mov' and z.operands[0].type==capstone.x86.X86_OP_MEM and z.operands[0].mem.disp==0 and z.operands[1].type==capstone.x86.X86_OP_REG and z.operands[1].reg==v.operands[0].reg for z in actual[j+1:j+3]):continue
      methods=[]
      for slot in range(0,0x180,8):
       f=struct.unpack_from('<Q',x.b,x.off(iv)+slot)[0]-x.base
       if not x.text.VirtualAddress<=f<x.text.VirtualAddress+x.text.SizeOfRawData:break
       try:save(f)
       except (pefile.PEFormatError,AssertionError,StopIteration):break
       methods.append({'slot':slot,'rva':f})
      candidates.append({'registration_rva':ins[0].address-x.base,'registration_xref':r,'class_vtable':vt,'ConstructCls':ctor,'constructor':c,'instance_vtable':iv,'methods':methods})
  hits.append({'rtti_name':name,'string_rva':target,'xrefs':refs,'candidates':candidates})
 result={'status':'RAW_NATIVE_TRIGGER_CAPTURE_REQUIRES_ADJUDICATION','input':x.freshness(),'image_base':x.base,'hits':hits,'functions':list(saved.values()),'scope':'Exact serialized questTriggerCondition class only; constructor/vtable candidates, not automatic ownership semantics','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()}
 (out/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({'input':result['input'],'hits':hits,'functions':len(saved)},indent=2))
if __name__=='__main__':main()
