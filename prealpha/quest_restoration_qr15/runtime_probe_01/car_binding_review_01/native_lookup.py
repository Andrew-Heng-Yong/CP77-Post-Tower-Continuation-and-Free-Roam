"""One exact class-registration lookup for native spawner semantics; file reads only."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
HELPER=WORK/'prealpha/quest_restoration_qr15/saved_graph_state_01/inspect_native.py'
sys.path.insert(0,str(HELPER.parent))
from inspect_native import Image,EXE

def main():
    out=HERE/'native_semantics_01';assert not out.exists();out.mkdir()
    im=Image();needle=b'gameCommunitySystem\0';hits=[];at=0
    while True:
        at=im.data.find(needle,at)
        if at<0:break
        hits.append(im.rva(at));at+=len(needle)
    assert len(hits)<=4,'Ambiguous exact registration name; preserve output boundary'
    matches=[];functions={}
    for rva in hits:
        refs=im.refs_to(rva);pointers=im.pointers_to(rva)
        for ref in refs:
            addr=ref['container_rva']
            if addr and addr not in functions:functions[addr]=im.disasm(int(addr,16))
        matches.append({'string_rva':hex(rva),'rip_ref_candidates':refs,'pointer_candidates':pointers})
    result={'status':'EXACT_CLASS_NAME_LOOKUP_PENDING_REGISTRATION_MAPPING','class':'gameCommunitySystem','exe_path':str(EXE),'exe_sha256':im.sha,'helper_path':str(HELPER),'helper_sha256':hashlib.sha256(HELPER.read_bytes()).hexdigest().upper(),'matches':matches,'functions':functions,'known_virtual_slots':{'ActivateCommunity':'0x1B0','ActivateSpawner':'0x1D8','DeactivateSpawner':'0x1E0','ResetSpawner':'0x1E8','GetSpawner':'0x260'},'limit':'One exact class registration lookup; string RIP refs are candidates until decoded and mapped to the concrete native instance vtable. No broad function brute force.','game_API_calls':0,'writes_to_exe':0}
    (out/'lookup.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'matches':matches,'functions':[(k,len(v['instructions']))for k,v in functions.items()],'out':str(out/'lookup.json')}))

if __name__=='__main__':main()
