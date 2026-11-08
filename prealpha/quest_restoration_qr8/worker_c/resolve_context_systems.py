"""Bounded native CClass global xrefs; no engine execution or CClass-name inference."""
import argparse,bisect,re,struct,sys
from pathlib import Path
from prepare import ROOT,HERE,read,sha,write
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone

def main(out):
    assert out.resolve().is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
    p=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe')
    assert sha(p)=='D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    tx=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text');pd=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata')
    bs=sorted(x for i in range(0,pd.SizeOfRawData-11,12) if (x:=struct.unpack_from('<III',b,pd.PointerToRawData+i)[:2])[0] and x[1]>x[0]);starts=[x[0] for x in bs]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
    targets={'inventory_context_C0':0x90A5AB+0x32B9FFD,'inject_context_170':0xC0C137+0x2FB8801,'device_context_58':0x3C8B93+0x37FA37D}
    code=b[tx.PointerToRawData:tx.PointerToRawData+tx.SizeOfRawData];rows=[]
    for label,target in targets.items():
        xrefs=[]
        for m in re.finditer(rb'[\x48\x4c][\x89\x8b\x8d][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]',code):
            rva=tx.VirtualAddress+m.start()
            if rva+7+struct.unpack_from('<i',code,m.start()+3)[0]!=target:continue
            inst=next(md.disasm(code[m.start():m.start()+7],base+rva))
            if inst.mnemonic!='mov' or inst.operands[0].type!=capstone.x86.X86_OP_MEM:continue
            ix=bisect.bisect_right(starts,rva)-1;s,e=bs[ix];assert s<=rva<e and e-s<2000
            of=pe.get_offset_from_rva(s);ins=list(md.disasm(b[of:of+e-s],base+s));strings=[]
            for x in ins:
                if x.mnemonic!='lea' or x.operands[-1].type!=capstone.x86.X86_OP_MEM or x.operands[-1].mem.base!=capstone.x86.X86_REG_RIP:continue
                dest=x.address+x.size+x.operands[-1].mem.disp-base
                try:fo=pe.get_offset_from_rva(dest)
                except pefile.PEFormatError:continue
                value=b[fo:fo+160].split(b'\0')[0]
                if len(value)>5 and all(32<=c<127 for c in value):strings.append({'rva':dest,'value':value.decode('ascii')})
            fp=out/f'function_{s:08x}.asm';fp.write_text('\n'.join(f'{x.address-base:08X}: {x.mnemonic} {x.op_str}' for x in ins)+'\n',encoding='utf-8')
            xrefs.append({'store_rva':rva,'function':[s,e],'strings':strings,'path':str(fp),'sha256':sha(fp)})
        rows.append({'context_field':label,'class_global_rva':target,'registration_stores':xrefs})
    write(out/'manifest.json',{'input':str(p),'input_sha256':sha(p),'systems':rows,'code_sha256':sha(__file__),
        'limits':['CClass registration strings identify requested interfaces; concrete service implementation and saved state require separate evidence.']})
    print([{'field':r['context_field'],'names':[s['value'] for f in r['registration_stores'] for s in f['strings']]} for r in rows])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
