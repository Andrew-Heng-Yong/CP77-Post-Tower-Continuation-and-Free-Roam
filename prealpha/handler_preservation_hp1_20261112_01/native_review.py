"""Read exact engine file bytes for freeze/wake and retirement boundaries."""
import struct,sys
from prepare import HERE,ROOT,write,sha

sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
    out=HERE/'native_01';assert not out.exists();out.mkdir();im=Image()
    bindings={0x306F9B0:{0x18:0xBEB194,0x88:0x2CD98E0,0x90:0x2CD9978,0x98:0x7398A0},0x30BCE78:{0x240:0xBEA6CC},0x30470A8:{0x178:0xBEC7A0}}
    for table,slots in bindings.items():
        for slot,rva in slots.items():assert struct.unpack_from('<Q',im.data,im.off(table+slot))[0]==im.base+rva
    functions=[im.disasm(rva) for rva in (0xBEB194,0xBEA6CC,0x2CD9978,0x2CD9A24,0x7398A0,0x438888,0xBEC7A0,0xBEC890,0x2B1D30,0x2FCEAC,0x2FCFD0,0x2FCF0C)]
    path=ROOT/'research/framework_pr63_01/codeware/src/App/Quest/QuestsSystemEx.hpp';source=path.read_text()
    assert 'CreateContext(this, &context, 1, 0, -1, -1)' in source and 'context.phaseStack.PushBack(rootPhaseInstance)' in source
    write(out/'readback.json',{'engine_sha256':im.sha,'bindings':{hex(k):{hex(s):hex(r) for s,r in v.items()} for k,v in bindings.items()},'functions':functions,
        'codeware_executor_source':{'path':str(path),'sha256':sha(path)},'scope':'Static file readback only. Existing exact-engine freeze/wake/stop evidence remains applicable. No native calls, plugin, process access or simulation of timer suspension.',
        'limits':['Saved freezer records coordinate phase/node deferred inputs; this does not establish preserving remaining time of every condition/callback.','ExecuteNode uses root context mode 1; it is not a selective suspension or saved-owner restoration API.','Normal phase stop recursively removes handlers and releases tickets; external release acknowledgements are separate.']})
    print('Verified freeze/wake and phase-stop vtable bindings against the installed engine; retained 12 native function readbacks.')

if __name__=='__main__':main()
