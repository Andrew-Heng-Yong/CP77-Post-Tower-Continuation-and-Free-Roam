"""Fresh bounded static native quest-spawner action evidence, no execution."""
from pathlib import Path
import argparse, json, struct, sys
HERE=Path(__file__).resolve().parent
WORKSPACE=HERE.parents[3]
sys.path.insert(0,str(WORKSPACE/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
    ap=argparse.ArgumentParser()
    for key in ('rva','qwords','refs','callers','pointer'):
        ap.add_argument('--'+key,action='append',default=[],type=lambda v:int(v,0))
    ap.add_argument('--span',action='append',default=[])
    ap.add_argument('--strings',action='append',default=[])
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--quiet',action='store_true')
    args=ap.parse_args();assert args.out.resolve().parent==HERE and not args.out.exists()
    im=Image()
    result={'exe_sha256':im.sha,'method':'Pinned file-byte disassembly only; no process, game, framework, save, compiler or installer access',
        'functions':[im.disasm(v) for v in args.rva],
        'qwords':{hex(v):[(hex(v+8*n),hex(struct.unpack_from('<Q',im.data,im.off(v)+8*n)[0])) for n in range(80)] for v in args.qwords},
        'rip_ref_candidates':{hex(v):im.refs_to(v) for v in args.refs},
        'direct_call_candidates':{hex(v):im.calls_to(v) for v in args.callers},
        'pointer_refs':{hex(v):im.pointers_to(v) for v in args.pointer},'explicit_spans':[],'strings':{},'game_api_calls':0,'runtime_changes':0,'save_reads':0}
    for value in args.span:
        a,end=(int(v,0) for v in value.split(':'));assert 0<end-a<=8192
        result['explicit_spans'].append({'begin_rva':hex(a),'end_rva':hex(end),'extent':'Explicit bounded span; no function extent claim',
            'instructions':[{'rva':hex(i.address-im.base),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in im.md.disasm(im.data[im.off(a):im.off(a)+end-a],im.base+a)]})
    for value in args.strings:
        off=0;rows=[]
        while True:
            off=im.data.find(value.encode(),off)
            if off<0:break
            try:
                a=im.rva(off);rows.append({'rva':hex(a),'refs':im.refs_to(a)})
            except StopIteration:pass
            off+=1
        result['strings'][value]=rows
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('functions','explicit_spans')},indent=2))
    for f in result['functions']+result['explicit_spans']:
        print(f['begin_rva'],f['end_rva'],len(f['instructions']))
        if not args.quiet:
            for i in f['instructions']:print(i['rva'],i['mnemonic'],i['operands'])

if __name__=='__main__':main()
