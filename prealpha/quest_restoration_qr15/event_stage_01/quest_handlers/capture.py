"""Static PE evidence for saved quest-handler/event state; never accesses a save/process."""
from pathlib import Path
import argparse,json,struct,sys
HERE=Path(__file__).resolve().parent;WORKSPACE=HERE.parents[3]
sys.path.insert(0,str(WORKSPACE/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image
def main():
    ap=argparse.ArgumentParser()
    for name in ('rva','callers','pointer','refs','qwords'):ap.add_argument('--'+name,action='append',default=[],type=lambda x:int(x,0))
    ap.add_argument('--strings',action='append',default=[]);ap.add_argument('--span',action='append',default=[]);ap.add_argument('--out',required=True)
    a=ap.parse_args();out=HERE/a.out;assert out.parent==HERE and not out.exists();im=Image()
    v={'exe_sha256':im.sha,'functions':[im.disasm(x) for x in a.rva],
       'direct_call_candidates':{hex(x):im.calls_to(x) for x in a.callers},'pointer_references':{hex(x):im.pointers_to(x) for x in a.pointer},
       'rip_reference_candidates':{hex(x):im.refs_to(x) for x in a.refs},'qwords':{hex(x):[(hex(x+8*n),hex(struct.unpack_from('<Q',im.data,im.off(x)+8*n)[0])) for n in range(96)] for x in a.qwords},
       'strings':{},'explicit_spans':[],'original_save_reads':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0}
    for val in a.span:
        lo,hi=(int(x,0) for x in val.split(':'));assert 0<hi-lo<=16384
        v['explicit_spans'].append({'begin_rva':hex(lo),'end_rva':hex(hi),'extent':'Explicit bounded byte span, not a complete-function assertion',
            'instructions':[{'rva':hex(i.address-im.base),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in im.md.disasm(im.data[im.off(lo):im.off(lo)+hi-lo],im.base+lo)]})
    for val in a.strings:
        off=0;hits=[]
        while True:
            off=im.data.find(val.encode('ascii'),off)
            if off<0:break
            try:rva=im.rva(off);hits.append({'rva':hex(rva),'rip_refs':im.refs_to(rva)})
            except StopIteration:pass
            off+=1
        v['strings'][val]=hits
    out.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
    for f in v['functions']+v['explicit_spans']:print(f['begin_rva'],f['end_rva'],len(f['instructions']))
    for key in ('strings','direct_call_candidates','rip_reference_candidates','pointer_references'):
        if v[key]:print(key,json.dumps(v[key]))
if __name__=='__main__':main()
