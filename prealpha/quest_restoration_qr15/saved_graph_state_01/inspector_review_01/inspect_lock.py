"""Fresh read-only static review for a proposed quest traversal inspector."""
from pathlib import Path
import argparse, json, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from inspect_native import Image

def main():
    ap=argparse.ArgumentParser()
    for name in ['rva','pointer','callers','refs','qwords']:
        ap.add_argument('--'+name,action='append',default=[],type=lambda s:int(s,0))
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--quiet',action='store_true')
    ap.add_argument('--strings',action='append',default=[])
    ap.add_argument('--span',action='append',default=[])
    args=ap.parse_args()
    assert args.out.resolve().parent==HERE and not args.out.exists()
    im=Image()
    result={'exe_sha256':im.sha,'method':'Static PE .pdata/Capstone exact bytes only; never loads binary or attaches to process',
            'functions':[im.disasm(v) for v in args.rva],
            'pointer_refs':{hex(v):im.pointers_to(v) for v in args.pointer},
            'direct_call_candidates':{hex(v):im.calls_to(v) for v in args.callers},
            'rip_ref_candidates':{hex(v):im.refs_to(v) for v in args.refs},
            'game_api_calls':0,'runtime_changes':0}
    import struct
    result['qwords']={hex(v):[(hex(v+i*8),hex(struct.unpack_from('<Q',im.data,im.off(v)+i*8)[0])) for i in range(80)] for v in args.qwords}
    result['strings']={}
    result['explicit_spans']=[]
    for spec in args.span:
        a,c=(int(x,0) for x in spec.split(':'))
        assert 0<c-a<=4096
        result['explicit_spans'].append({'begin_rva':hex(a),'end_rva':hex(c),
            'boundary_limit':'Explicit reviewed span; no .pdata function boundary claimed',
            'instructions':[{'rva':hex(i.address-im.base),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}
                for i in im.md.disasm(im.data[im.off(a):im.off(a)+c-a],im.base+a)]})
    for text in args.strings:
        rows=[];off=0
        while True:
            off=im.data.find(text.encode(),off)
            if off<0:break
            try:
                rva=im.rva(off)
                rows.append({'rva':hex(rva),'refs':im.refs_to(rva)})
            except StopIteration:pass
            off+=1
        result['strings'][text]=rows
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({k:v for k,v in result.items() if k!='functions'})
    for f in result['functions']:
        print('Function',f.get('begin_rva'),f.get('end_rva'),len(f.get('instructions',[])))
        if not args.quiet:
            for r in f.get('instructions',[]):print(r['rva'],r['mnemonic'],r['operands'])

if __name__=='__main__':main()
