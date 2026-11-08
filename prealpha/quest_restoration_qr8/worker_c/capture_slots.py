"""Capture actual virtual targets from a pinned concrete native registration."""
import argparse,struct,sys
from pathlib import Path
from prepare import ROOT,HERE,read,sha,write
from capture_native_functions import main as capture
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile

def main(mf,out,slots):
    assert out.resolve().is_relative_to(HERE) and not out.exists()
    m=read(mf);p=Path(m['input']);assert sha(p)==m['input_sha256']
    assert len(m['constructor_candidates'])==1
    vt=m['constructor_candidates'][0]['instance_vtable'];b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    rows=[{'slot':s,'slot_hex':hex(s),'target_rva':struct.unpack_from('<Q',b,pe.get_offset_from_rva(vt)+s)[0]-base} for s in slots]
    write(out/'slots.json',{'registration':str(mf.resolve()),'registration_sha256':sha(mf),'type':m['rtti_name'],'input_sha256':sha(p),'instance_vtable_rva':vt,'slots':rows,'code_sha256':sha(__file__)})
    capture(out/'functions',[r['target_rva'] for r in rows]);print(rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--slot',action='append',type=lambda v:int(v,0),required=True);a=p.parse_args();main(a.manifest,a.output,a.slot)
