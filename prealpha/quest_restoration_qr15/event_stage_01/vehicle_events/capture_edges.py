"""Exact ToggleDoor cold/type branches, separate fresh evidence."""
from pathlib import Path
import json, struct, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
 out=HERE/'native_03.json';assert not out.exists()
 im=Image();funcs={}
 for name,addr in {'toggle_door_cold':0x25F98AE,'toggle_wrapper_registration':0x16DC0C0,'toggle_wrapper_type_getter':0x193A610}.items():
  funcs[name]=im.disasm(addr)
 constants={}
 for name,addr,size in [('out_literal',0x305C994,4),('toggle_wrapper_name',0x32E9308,len('vehicleToggleDoorWrapperEvent')+1)]:
  data=im.data[im.off(addr):im.off(addr)+size]
  constants[name]={'rva':hex(addr),'bytes':data.hex(),'ascii':data.rstrip(b'\0').decode('ascii')}
 out.write_text(json.dumps({'exe_sha256':im.sha,'functions':funcs,'constants':constants,'toggle_wrapper_vtable':{'rva':'0x33f4cd8','get_type':hex(struct.unpack_from('<Q',im.data,im.off(0x33F4CD8))[0]-im.base)},'method':'File bytes only. No original save/process/game/API access.'},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(out),'functions':len(funcs)}))
if __name__=='__main__':main()
