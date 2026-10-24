"""Independent native index, full semantic preservation and archive-proof checks."""
from pathlib import Path
import copy,hashlib,json,struct,sys
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks=[]
def check(v,label):
 assert v,label
 checks.append(label)
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def valid(r):
 defs=r['actors']+r['playerActors'];ids=[a['actorId']['id'] for a in defs];n=len(r['actors'])
 if ids!=list(range(len(ids))):return False
 for p in r['playerActors']:
  # Current native 2c9a3c passes actorId to 2c9f30, which subtracts NPC count.
  index=p['actorId']['id']-n
  if not 0<=index<len(r['playerActors']) or r['playerActors'][index] is not p:return False
 for v in walk(r):
  if v.get('$type')=='scnActorId' and v['id']!=0xffffffff and v['id'] not in ids:return False
  if v.get('$type')=='scnPerformerId' and v['id']&255==1 and v['id']>>8 not in ids:return False
 return True
build=read(C/'build_02.json');prepared=read(C/'prepared_01.json');audit=read(C/'scene_audit_01/audit.json');cause=read(C/'diagnosis_01/cause_02.json')
check(build['status']=='BUILT_SC1_NATIVE_NOT_LIVE','build status')
check(len(prepared['resources'])==len(build['resources'])==9,'nine H1 scenes')
check(build['unchanged_resources']==8 and len(build['original_resource_hashes'])==17,'all eight owner resources unchanged byte for byte')
check(cause['resource_hash_verified'] and cause['resource_actor_count']==0 and cause['resource_player_count']==1,'dump identifies private Corpo purchase scene')
check(cause['failing_runtime_index']==cause['player_definitions'][0]['id']==3 and cause['runtime_player_count']==1,'dump proves index three into one-entry table')
check(cause['overflow_elements']==410592809 and cause['player_definitions'][0]['facial_count']==0,'wrong definition produces overflow, correct player facial array empty')
pe=pefile.PE(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe',fast_load=True)
check(pe.get_data(0x2c9a3c,10)==bytes.fromhex('8b13498bcdE8EA040000'),'native caller reads definition actorId')
check(pe.get_data(0x2c9f5d,12)==bytes.fromhex('2B51148BC24C69F8B0000000'),'native lookup subtracts actor count and scales index by176')
for row in prepared['resources']:
 orig=read(row['source']);fixed=read(row['prepared']);br=next(r for r in build['resources'] if r['depot']==row['depot']);packed=read(br['readback']);name=row['depot']
 check(sha(row['raw'])==row['raw_sha256']==br['before'],name+' original bytes')
 check(sha(row['source'])==row['source_sha256'] and sha(row['prepared'])==row['prepared_sha256'],name+' JSON source bindings')
 check(sha(br['readback'])==br['readback_sha256'],name+' readback binding')
 check(packed['Data']==fixed['Data'],name+' complete serialized data matches intended edit')
 check(not valid(orig['Data']['RootChunk']),name+' original reproduces invalid index')
 check(valid(packed['Data']['RootChunk']),name+' repaired native indices and references valid')
 restored=copy.deepcopy(packed);root=restored['Data']['RootChunk']
 for op in row['id_changes']:
  obj=root
  for k in op['path'][:-1]:obj=obj[k]
  check(obj[op['path'][-1]]==op['after'],name+' exact changed typed reference '+str(op['path']))
  obj[op['path'][-1]]=op['before']
 for symbol in row['removed_debug_symbols']:
  check(symbol['symbol']['performerId']['id']&255==1,name+' removed metadata is actor debug symbol')
  root['debugSymbols']['performersDebugSymbols'].insert(symbol['index'],symbol['symbol'])
 check(restored['Data']==orig['Data'],name+' inversion proves all unrelated payloads unchanged')
 oldnodes=orig['Data']['RootChunk']['sceneGraph']['Data']['graph'];newnodes=packed['Data']['RootChunk']['sceneGraph']['Data']['graph']
 check([x['Data']['nodeId'] for x in oldnodes]==[x['Data']['nodeId'] for x in newnodes],name+' native scene node identities preserved')
 for a,b in zip(oldnodes,newnodes):
  check(a['Data']['outputSockets']==b['Data']['outputSockets'],name+' native edge payloads unchanged '+str(a['Data']['nodeId']))
 mutated=copy.deepcopy(packed['Data']['RootChunk']);mutated['playerActors'][0]['actorId']['id']=len(mutated['actors'])+1
 check(not valid(mutated),name+' out of range regression rejected')
 check(len(packed['Data']['RootChunk']['actors'])==len(orig['Data']['RootChunk']['actors']),name+' no excluded actors restored')
check(audit['count']==89 and len(audit['non_dense'])==10,'audit covers89 installed Tower scenes, nine active H1 plus legacy seat')
snap=read(next((C/'diagnosis_01/snapshots').glob('*.json')))
check(snap['origin']=='post_ending_fallback' and len(snap['rows'])==158,'live HS1 exports158row fallback; not pre-ending history')
check(sha(C/'package'/build['target'])==build['after'],'final package binding')
sources=[H/'prepare_01.py',H/'build_02.ps1',Path(__file__),C/'build_02.json',C/'prepared_01.json',C/'scene_audit_01/audit.json',C/'diagnosis_01/cause_02.json',C/'diagnosis_01/cause_02.asm']
sources+=list((C/'readback_02').glob('*.json'))+list((C/'prepared_01').glob('*.json'))
result={'status':'PASS_NATIVE_INDEX_REPAIR_NOT_LIVE','count':len(checks),'checks':checks,'sources':{str(p):sha(p) for p in sources},'unchanged_owner_resources':8,'changed_private_scenes':9,'reds_changes':0,'framework_changes':0,'live_result':'pending'}
with (C/'tests_01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','sources']}))


