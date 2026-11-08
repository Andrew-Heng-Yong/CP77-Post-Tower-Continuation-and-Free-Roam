"""Bounded read-only disassembly of exact pinned-current executable RVAs."""
from pathlib import Path
import sys,struct,bisect,argparse
from prepare import ROOT,HERE,write,sha
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone

def main(out,rvas):
    out=out.resolve();assert out.is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
    p=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe');before=sha(p)
    assert before=='D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    pd=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata')
    bs=sorted(x for i in range(0,pd.SizeOfRawData-11,12) if (x:=struct.unpack_from('<III',b,pd.PointerToRawData+i)[:2])[0] and x[1]>x[0]);starts=[x[0] for x in bs]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);rows=[]
    for rva in rvas:
        ix=bisect.bisect_right(starts,rva)-1;s,e=bs[ix];pdata=s<=rva<e
        if not pdata:s=rva;e=rva+96
        assert e-s<=50000,'Function capture size bound'
        fo=pe.get_offset_from_rva(s);ins=[]
        for x in md.disasm(b[fo:fo+e-s],base+s):
            ins.append(x)
            if not pdata and x.mnemonic in ['ret','jmp']:break
        if not pdata:assert ins[-1].mnemonic in ['ret','jmp'];e=ins[-1].address+ins[-1].size-base
        fp=out/f'function_{s:08x}.asm';fp.write_text('\n'.join(f'{x.address-base:08X}: {x.mnemonic} {x.op_str}' for x in ins)+'\n',encoding='utf-8')
        rows.append({'requested_rva':rva,'bounds':[s,e],'bounds_source':'pdata' if pdata else 'bounded_leaf_thunk_to_first_terminal',
            'path':str(fp),'sha256':sha(fp),'bytes_sha256':__import__('hashlib').sha256(b[fo:fo+e-s]).hexdigest().upper()})
    assert sha(p)==before
    write(out/'manifest.json',{'status':'READ_ONLY_PINNED_NATIVE_FUNCTION_CAPTURE','input':str(p),'input_sha256':before,'functions':rows,'code_sha256':sha(__file__),
        'limits':['Disassembly and function boundaries alone are not gameplay-semantic or saved-state proof.','Cold branch targets must be captured separately when outside this pdata function.']})
    print({'functions':len(rows),'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--rva',type=lambda x:int(x,0),action='append',required=True);a=ap.parse_args();main(a.output,a.rva)
