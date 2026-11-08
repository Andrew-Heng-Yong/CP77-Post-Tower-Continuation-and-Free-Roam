"""Read-only installed ArchiveXL inspection; captures actual bytes, never loads DLL."""
from pathlib import Path
import sys,struct,re,bisect,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone
DLL=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/red4ext/plugins/ArchiveXL/ArchiveXL.dll')

class Binary:
 def __init__(self,path):
  self.path=Path(path);self.stat=self.path.stat();self.b=self.path.read_bytes();self.sha=hashlib.sha256(self.b).hexdigest().upper()
  assert (self.stat.st_size,self.stat.st_mtime_ns)==(self.path.stat().st_size,self.path.stat().st_mtime_ns)
  self.pe=pefile.PE(data=self.b);self.base=self.pe.OPTIONAL_HEADER.ImageBase
  self.text=next(s for s in self.pe.sections if s.Name.rstrip(b'\0')==b'.text')
  pd=next(s for s in self.pe.sections if s.Name.rstrip(b'\0')==b'.pdata')
  self.bounds=sorted(x for i in range(0,pd.SizeOfRawData-11,12) if (x:=struct.unpack_from('<III',self.b,pd.PointerToRawData+i)[:2])[0] and x[1]>x[0]);self.starts=[x[0] for x in self.bounds]
  self.md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);self.md.detail=True
 def rva(self,offset):return self.pe.get_rva_from_offset(offset)
 def off(self,rva):return self.pe.get_offset_from_rva(rva)
 def dis(self,rva):
  ix=bisect.bisect_right(self.starts,rva)-1;s,e=self.bounds[ix]
  if not s<=rva<e:
   s=rva;ins=[]
   for x in self.md.disasm(self.b[self.off(s):self.off(s)+128],self.base+s):
    ins.append(x)
    if x.mnemonic in ['ret','jmp']:break
   assert ins and ins[-1].mnemonic in ['ret','jmp'],hex(rva)
   e=ins[-1].address+ins[-1].size-self.base
  return (s,e),list(self.md.disasm(self.b[self.off(s):self.off(s)+e-s],self.base+s))
 def refs(self,target):
  code=self.b[self.text.PointerToRawData:self.text.PointerToRawData+self.text.SizeOfRawData];out=[]
  for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]',code):
   off=m.start();rva=self.text.VirtualAddress+off
   if rva+7+struct.unpack_from('<i',code,off+3)[0]==target:out.append(rva)
  return out
 def freshness(self):
  now=self.path.stat();assert (now.st_size,now.st_mtime_ns)==(self.stat.st_size,self.stat.st_mtime_ns),'Input changed after hash'
  return {'path':str(self.path),'sha256':self.sha,'size':self.stat.st_size,'mtime_ns':self.stat.st_mtime_ns,'hash_policy':'Read bytes and SHA once, require stable size/mtime before and after all analysis'}

def main():
 out=HERE/'binary_capture_01';out.mkdir(exist_ok=False);x=Binary(DLL);saved={}
 def save(rva):
  (s,e),ins=x.dis(rva)
  if s not in saved:
   p=out/f'function_{s:08x}.asm';p.write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex():<30} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8')
   saved[s]={'rva':s,'end_rva':e,'path':str(p),'bytes_sha256':hashlib.sha256(x.b[x.off(s):x.off(s)+e-s]).hexdigest().upper()}
  return s
 strings=[]
 for m in re.finditer(rb'[\x20-\x7e]{6,}\0',x.b):
  s=m.group()[:-1].decode('ascii')
  if any(q in s for q in ['QuestPhase','WorldStreaming','ResourcePatch','OnGameRestored','ForceStartNode','QuestRootInstance','Patching phase','merge phase','Patching world','streaming block','*.pdb']):
   rva=x.rva(m.start());refs=x.refs(rva)
   strings.append({'text':s,'rva':rva,'lea_xrefs':refs,'xref_functions':sorted(set(save(r) for r in refs))})
 version=[]
 for fi in getattr(x.pe,'FileInfo',[]):
  for entry in fi:
   if hasattr(entry,'StringTable'):
    for st in entry.StringTable:version.append({k.decode():v.decode(errors='replace') for k,v in st.entries.items()})
 debug=[]
 for entry in getattr(x.pe,'DIRECTORY_ENTRY_DEBUG',[]):
  if entry.struct.Type==2:
   data=x.b[entry.struct.PointerToRawData:entry.struct.PointerToRawData+entry.struct.SizeOfData]
   debug.append({'type':2,'bytes_hex':data.hex(),'pdb':data[24:].rstrip(b'\0').decode(errors='replace') if data[:4]==b'RSDS' else None})
 # MSVC COL pointers followed by candidate vtable entries near each RTTI type name.
 rtti=[]
 for s in strings:
  if not s['text'].startswith('.?AV'):continue
  td=s['rva']-16;tdrefs=[]
  for off in range(0,len(x.b)-24,4):
   if x.b[off:off+4]==b'\x01\0\0\0' and struct.unpack_from('<I',x.b,off+12)[0]==td:
    col=x.rva(off);key=struct.pack('<Q',x.base+col)
    for m in re.finditer(re.escape(key),x.b):
     vt=x.rva(m.start()+8);methods=[]
     for slot in range(0,0x100,8):
      a=struct.unpack_from('<Q',x.b,m.start()+8+slot)[0]-x.base
      if not x.text.VirtualAddress<=a<x.text.VirtualAddress+x.text.SizeOfRawData:break
      methods.append({'slot':slot,'rva':save(a)})
     tdrefs.append({'col_rva':col,'vtable_rva':vt,'methods':methods})
  rtti.append({'name':s['text'],'type_descriptor_rva':td,'vtables':tdrefs})
 manifest={'input':x.freshness(),'image_base':x.base,'version':version,'debug':debug,'strings':strings,'rtti':rtti,'functions':list(saved.values()),'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper(),'runtime_load_or_execution':False}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps({'input':manifest['input'],'version':version,'debug':debug,'strings':len(strings),'rtti':rtti,'functions':len(saved)},indent=2))

if __name__=='__main__':main()
