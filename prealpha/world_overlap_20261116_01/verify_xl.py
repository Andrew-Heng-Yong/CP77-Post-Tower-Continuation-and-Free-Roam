"""Validate the new ArchiveXL registration against every installed addition."""
from pathlib import Path
import binascii,re
from prepare import WORK,DEPOT,XL,read,sha,write

def crc_independent(text):
 crc=65535
 for b in text.encode('utf-8'):
  crc^=b<<8
  for _ in range(8):crc=((crc<<1)^0x1021 if crc&0x8000 else crc<<1)&65535
 return crc

def main():
 pins=read(WORK/'inputs.json');game=Path(pins['game'])
 packed=read(WORK/'archive_01/readback.json')
 assert packed['status']=='MEMBERS_VERIFIED' and len(packed['native_parents'])==1
 parent=packed['native_parents'][0];assert sha(parent['path'])==parent['sha256'] and sha(parent['json'])==parent['json_sha256']
 graph=read(parent['json'])['Data']['RootChunk']['graph']['Data']
 # Native root nodes have inline definitions in this exact exported resource.
 native_ids={h['Data']['id'] for h in graph['nodes']}
 files=sorted({p for root in (game/'archive/pc',game/'mods') if root.exists() for p in root.rglob('*.xl')})
 regs=[];inventory=[]
 for path in files:
  before=sha(path);t=(Path(pins['xl']['path']) if path==game/XL else path).read_text(encoding='utf-8-sig')
  inventory.append(dict(path=str(path),sha256=before,candidate_sha256=sha(pins['xl']['path']) if path==game/XL else before))
  match=re.search(r'(?m)^quest:\s*\n',t)
  if not match:continue
  section=t[match.end():];end=re.search(r'(?m)^[A-Za-z_][^\n]*:',section)
  if end:section=section[:end.start()]
  phase=re.search(r'(?m)^  phases:\s*\n',section)
  if not phase:continue
  section=section[phase.end():];end=re.search(r'(?m)^  [A-Za-z_][^\n]*:',section)
  if end:section=section[:end.start()]
  blocks=re.split(r'(?m)^    - path:\s*',section)
  assert not blocks[0].strip() or all(l.strip().startswith('#') for l in blocks[0].splitlines() if l.strip()),f'Unsupported phase shape: {path}'
  for block in blocks[1:]:
   depot=block.splitlines()[0].strip();p=re.search(r'^      parent: (.+)$',block,re.M)
   assert p,f'Missing phase parent: {path}'
   if p[1].strip()!=r'ep1\quest\ep1.quest':continue
   node=re.search(r'^        node: \[(.+)\]',block,re.M)
   assert node and node[1]=='1',f'Unsupported root injection: {path} {depot}'
   socket=re.search(r'^        socket: (.+)$',block,re.M);assert socket and socket[1].strip()=='Out'
   key=depot+':1';i=binascii.crc_hqx(key.encode(),65535);assert i==crc_independent(key)
   regs.append(dict(path=depot,id=i,source=str(path)))
  assert sha(path)==before,'Installed XL changed during inspection'
 ids=[r['id'] for r in regs]
 assert len(ids)==len(set(ids)) and not set(ids)&native_ids,'Generated phase-node ID collision'
 new=[r for r in regs if r['path']==DEPOT];assert len(new)==1
 old=(game/XL).read_bytes();candidate=Path(pins['xl']['path']).read_bytes();entry=pins['xl']['addition'].encode()
 assert candidate.count(entry)==1 and candidate.replace(entry,b'',1)==old
 write(WORK/'xl_assessment.json',dict(status='PASS',native_root_ids=sorted(native_ids),root_registrations=len(regs),
     new_registration=new[0],registrations=regs,input_files=inventory,only_delta=entry.decode(),
     old_order_and_bytes_preserved=True,new_depot_provider_collision=False,provider_scan=packed['scanned_archives']))
 print('PASS:',len(regs),'root registrations; new ID',new[0]['id'],'has no native or installed collision.')
if __name__=='__main__':main()
