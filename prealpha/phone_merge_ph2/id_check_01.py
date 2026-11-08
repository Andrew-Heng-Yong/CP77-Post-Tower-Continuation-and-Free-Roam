import binascii,hashlib,json,re
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def crc(s):return binascii.crc_hqx(s.encode(),65535)
def bit(s):
 c=65535
 for b in s.encode():
  c^=b<<8
  for _ in range(8):c=((c<<1)^0x1021 if c&32768 else c<<1)&65535
 return c
inventory=[];files=[]
for f in (G/'archive/pc/mod').glob('*.xl'):
 t=f.read_text(encoding='utf-8-sig');files.append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest().upper()})
 if not re.search(r'^quest:',t,re.M):continue
 section=t.split('quest:',1)[1].split('\nstreaming:',1)[0]
 blocks=re.split(r'(?m)^    - path:\s*',section)[1:]
 assert blocks,f
 for block in blocks:
  path=block.splitlines()[0].strip();parent=re.search(r'^      parent: (.+)$',block,re.M)
  assert parent,(f,path)
  if parent[1].strip()!=r'ep1\quest\ep1.quest':continue
  node=re.search(r'^        node: \[(.+)\]',block,re.M);assert node and node[1]=='1',(f,path)
  key=path+':1';assert crc(key)==bit(key)
  inventory.append({'path':path,'id':crc(key),'source':f.name})
old=r'towercontinued\phone_support_ph1\mark_bana.questphase';new=r'towercontinued\phone_merge_ph2\mark_bana_listener.questphase'
native=[0,1,2,12,27]
conflicts=[x for x in inventory if x['id']==crc(old+':1')]
assert len(conflicts)>=2 or crc(old+':1') in native
assert crc(new+':1') not in native+[x['id'] for x in inventory]
out={'status':'PASS_ALIAS_GENERATED_ID_CHECK','old_path':old,'old_id':crc(old+':1'),'new_path':new,'new_id':crc(new+':1'),'conflicts':conflicts,'native_ids':native,'inventory':inventory,'xl_files':files}
(H/'id_proof_01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['inventory','xl_files']}))
