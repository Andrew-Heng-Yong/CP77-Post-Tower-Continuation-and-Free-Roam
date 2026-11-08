"""Bounded current-executable RTTI xrefs, without executing the game.

Only RIP-relative LEA candidates are decoded and validated. Absence of a match
does not prove absence of an engine implementation or alternate reference.
"""
import sys,re,struct,bisect
from prepare import ROOT,HERE,read,write,sha
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone

def main():
    out=HERE/'native_xrefs_01';assert not out.exists();out.mkdir()
    p=__import__('pathlib').Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe')
    before=sha(p);b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True)
    text=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
    pdata=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata')
    bounds=[struct.unpack_from('<III',b,pdata.PointerToRawData+i)[:2] for i in range(0,pdata.SizeOfRawData-11,12)]
    bounds=[x for x in bounds if x[0] and x[1]>x[0]];bounds.sort();starts=[x[0] for x in bounds]
    target_names=['ChangeEntryState','ChangeEntryStateByHash','questInjectLoot_NodeType','gsmGameDefinition','mainQuests','questLogicalHubNodeDefinition']
    target_map={};strings=[]
    for name in target_names:
        token=name.encode()+b'\0';at=0
        while True:
            at=b.find(token,at)
            if at<0:break
            # Require string start, excluding substrings of longer RTTI names.
            if at==0 or b[at-1]==0:
                rva=pe.get_rva_from_offset(at);target_map[rva]=name;strings.append({'name':name,'rva':rva,'file_offset':at})
            at+=len(token)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
    code=b[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
    hits=[];functions={}
    for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]',code):
        offset=m.start();rva=text.VirtualAddress+offset
        if offset+7>len(code):continue
        target=rva+7+struct.unpack_from('<i',code,offset+3)[0]
        if target not in target_map:continue
        ins=list(md.disasm(code[offset:offset+7],pe.OPTIONAL_HEADER.ImageBase+rva,count=1))
        if len(ins)!=1 or ins[0].mnemonic!='lea' or ins[0].size!=7:continue
        index=bisect.bisect_right(starts,rva)-1
        bound=bounds[index] if index>=0 and bounds[index][0]<=rva<bounds[index][1] else None
        hits.append({'target':target_map[target],'target_rva':target,'xref_rva':rva,'instruction':ins[0].mnemonic+' '+ins[0].op_str,'function_bounds':bound})
        if bound and bound[1]-bound[0]<=50000: functions[bound]=None
    for bound in functions:
        start,end=bound;fo=pe.get_offset_from_rva(start)
        lines=[f'{i.address-pe.OPTIONAL_HEADER.ImageBase:08X}: {i.mnemonic} {i.op_str}' for i in md.disasm(b[fo:fo+end-start],pe.OPTIONAL_HEADER.ImageBase+start)]
        (out/f'function_{start:08x}.asm').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert sha(p)==before
    write(out/'result.json',{'status':'BOUNDED_NATIVE_RTTI_XREFS_NOT_ENGINE_SEMANTICS','input':str(p),'input_sha256':before,
        'strings':strings,'lea_rip_xrefs':hits,'function_files':[{'path':str(out/f'function_{s:08x}.asm'),'sha256':sha(out/f'function_{s:08x}.asm')} for s,e in functions],
        'source_pins':[{'path':str(__import__('pathlib').Path(pefile.__file__)),'sha256':sha(pefile.__file__)},
                       {'path':str(__import__('pathlib').Path(capstone.__file__)),'sha256':sha(capstone.__file__)}],
        'code_sha256':sha(__file__),'input_unchanged':True,'limits':['Only validated RIP-relative LEA xrefs; other reference forms not inventoried.',
        'RTTI name or registration wrapper does not establish implementation semantics or a saved history.']})
    print({'strings':len(strings),'xrefs':len(hits),'functions':len(functions)})

if __name__=='__main__':main()
