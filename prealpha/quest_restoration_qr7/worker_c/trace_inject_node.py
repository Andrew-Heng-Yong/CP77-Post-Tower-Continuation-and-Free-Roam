"""Current native InjectLoot node RTTI/constructor/vtable source capture, read-only."""
from pathlib import Path
import sys,struct,bisect,re
from prepare import ROOT,HERE,write,sha
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone

def main():
    out=HERE/'inject_node_02';assert not out.exists();out.mkdir()
    p=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe')
    before=sha(p);b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    text=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text');pd=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata')
    bounds=sorted(x for i in range(0,pd.SizeOfRawData-11,12) if (x:=struct.unpack_from('<III',b,pd.PointerToRawData+i)[:2])[0] and x[1]>x[0]);starts=[x[0] for x in bounds]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
    def dis(rva):
        ix=bisect.bisect_right(starts,rva)-1;s,e=bounds[ix]
        if not s<=rva<e:
            s=rva;of=pe.get_offset_from_rva(s);ins=[]
            for x in md.disasm(b[of:of+96],base+s):
                ins.append(x)
                if x.mnemonic in ['ret','jmp']:break
            assert ins and ins[-1].mnemonic in ['ret','jmp'],rva
            e=ins[-1].address+ins[-1].size-base
            return (s,e),ins
        of=pe.get_offset_from_rva(s);ins=list(md.disasm(b[of:of+e-s],base+s))
        return (s,e),ins
    saved={}
    def save(rva):
        bound,ins=dis(rva);s,e=bound
        if s not in saved:
            fp=out/f'function_{s:08x}.asm'
            fp.write_text('\n'.join(f'{x.address-base:08X}: {x.mnemonic} {x.op_str}' for x in ins)+'\n',encoding='utf-8')
            saved[s]={'path':str(fp),'sha256':sha(fp),'function_bounds':[s,e]}
        return ins
    def lea_target(ins):
        if ins.mnemonic=='lea' and len(ins.operands)==2 and ins.operands[1].type==capstone.x86.X86_OP_MEM and ins.operands[1].mem.base==capstone.x86.X86_REG_RIP:
            return ins.address+ins.size+ins.operands[1].mem.disp-base
    name='questInjectLoot_NodeType';at=b.find(name.encode()+b'\0');assert at>=0;target=pe.get_rva_from_offset(at)
    code=b[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData];xrefs=[]
    for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]',code):
        off=m.start();rva=text.VirtualAddress+off
        if rva+7+struct.unpack_from('<i',code,off+3)[0]==target:xrefs.append(rva)
    candidates=[]
    for xref in xrefs:
        ins=save(xref)
        for i,x in enumerate(ins[:-1]):
            vt=lea_target(x)
            if vt is None or x.operands[0].reg!=capstone.x86.X86_REG_RAX:continue
            nearby=ins[i+1:i+4]
            if not any(y.mnemonic=='mov' and y.op_str.endswith(', rax') and y.operands[0].type==capstone.x86.X86_OP_MEM and y.operands[0].mem.base==capstone.x86.X86_REG_RIP for y in nearby):continue
            ctor=struct.unpack_from('<Q',b,pe.get_offset_from_rva(vt)+0xD8)[0]-base
            cin=save(ctor)
            targets=[ctor]+[y.operands[0].imm-base for y in cin if y.mnemonic in ['jmp','call'] and y.operands[0].type==capstone.x86.X86_OP_IMM]
            for c in targets:
                try:actual=save(c)
                except (AssertionError,pefile.PEFormatError):continue
                ivtables=[]
                for j,y in enumerate(actual[:-1]):
                    iv=lea_target(y)
                    if iv is not None and any(z.mnemonic=='mov' and z.operands[0].type==capstone.x86.X86_OP_MEM and z.operands[0].mem.disp==0 and z.operands[1].type==capstone.x86.X86_OP_REG and z.operands[1].reg==y.operands[0].reg for z in actual[j+1:j+3]):ivtables.append(iv)
                for iv in ivtables:
                    methods=[]
                    for slot in range(0,0x180,8):
                        f=struct.unpack_from('<Q',b,pe.get_offset_from_rva(iv)+slot)[0]-base
                        if not text.VirtualAddress<=f<text.VirtualAddress+text.SizeOfRawData:break
                        save(f);methods.append({'slot':slot,'rva':f})
                    candidates.append({'registration_xref':xref,'class_vtable':vt,'constructCls':ctor,'native_constructor':c,'instance_vtable':iv,'methods':methods})
    assert sha(p)==before
    write(out/'manifest.json',{'input':str(p),'input_sha256':before,'rtti_name':name,'rtti_string_rva':target,'registration_xrefs':xrefs,
        'constructor_candidates':candidates,'function_files':list(saved.values()),'code_sha256':sha(__file__),
        'limits':['CClass ConstructCls slotD8 comes from captured RED4ext SDK ABI; actual constructors and stores are independently decoded.',
        'Candidates require review; this capture alone asserts no gameplay semantics.']})
    print({'xrefs':len(xrefs),'candidates':len(candidates),'function_files':len(saved),'out':str(out)})

if __name__=='__main__':main()
