"""Bounded native-file capture for record flags and dynamic persistence lifecycle."""
from pathlib import Path
import argparse,json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from inspect_pid import Image
def main():
    ap=argparse.ArgumentParser()
    for name in ('rva','callers','refs','pointer','qwords'):ap.add_argument('--'+name,action='append',default=[],type=lambda x:int(x,0))
    ap.add_argument('--span',action='append',default=[]);ap.add_argument('--out',required=True)
    args=ap.parse_args();out=HERE/args.out;assert out.parent==HERE and not out.exists()
    im=Image();v={'exe_sha256':im.sha,'functions':[im.disasm(a) for a in args.rva],
        'direct_call_candidates':{hex(a):im.calls_to(a) for a in args.callers},
        'rip_reference_candidates':{hex(a):im.refs_to(a) for a in args.refs},
        'pointer_references':{hex(a):im.pointers_to(a) for a in args.pointer},
        'qwords':{hex(a):[(hex(a+8*n),hex(struct.unpack_from('<Q',im.data,im.off(a)+8*n)[0])) for n in range(80)] for a in args.qwords},
        'explicit_spans':[],'original_save_reads':0,'game_calls':0,'runtime_changes':0}
    for value in args.span:
        a,b=(int(x,0) for x in value.split(':'));assert 0<b-a<=8192
        v['explicit_spans'].append({'begin_rva':hex(a),'end_rva':hex(b),'extent':'Explicit bounded span, not function-boundary claim',
            'instructions':[{'rva':hex(i.address-im.base),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in im.md.disasm(im.data[im.off(a):im.off(a)+b-a],im.base+a)]})
    out.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
    for f in v['functions']+v['explicit_spans']:print(f['begin_rva'],f['end_rva'],len(f['instructions']))
    for key in ('direct_call_candidates','rip_reference_candidates','pointer_references'):print(key,json.dumps(v[key]))
if __name__=='__main__':main()
