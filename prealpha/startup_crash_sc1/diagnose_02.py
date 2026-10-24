from pathlib import Path
import struct,sys,json,hashlib
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
sys.path.insert(0,str(W/'tools'));from inspect_native_crash import Dump
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile,capstone
d=Dump(O/'report/Cyberpunk2077.dmp');base=next(b for b,_,n in d.modules if n=='Cyberpunk2077.exe')
pe=pefile.PE(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe',fast_load=True);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
def q(a):return struct.unpack('<Q',d.read(a,8))[0]
def u(a):return struct.unpack('<I',d.read(a,4))[0]
def fnv(s):
 h=0xcbf29ce484222325
 for b in s.encode():h=((h^b)*0x100000001b3)&0xffffffffffffffff
 return h
frames=json.loads((O/'unwind_01.json').read_text());scene=int(frames[8]['registers']['rsi'],16);resource=q(scene+0x150);players=q(resource+0x90);count=u(resource+0x9c);actors=u(resource+0x8c)
entry=int(frames[7]['registers']['r15'],16);table=q(scene+0x730);size=u(scene+0x73c)
out={'resource_hash':hex(q(resource+0x30)),'resource_depot':'towercontinued\\housing_h1\\native\\corpo_purchase.scene','resource_hash_verified':q(resource+0x30)==fnv('towercontinued\\housing_h1\\native\\corpo_purchase.scene'),'rtti_hashes':{n:hex(fnv(n)) for n in ['scnSceneResource','scnSceneSystem','scnSceneSystemData','scnPerformerSymbol']},'resource_actor_count':actors,'resource_player_count':count,'player_definitions':[{'id':u(players+i*0x100),'address':hex(players+i*0x100),'facial_array_pointer':hex(q(players+i*0x100+0x38)),'facial_count':u(players+i*0x100+0x44)} for i in range(count)],'runtime_player_table':hex(table),'runtime_player_count':size,'failing_runtime_entry':hex(entry),'failing_runtime_index':(entry-table)//0xb0,'wrong_definition_pointer':hex(q(entry+8)),'correct_definition_pointer':(hex(q(table+8)) if d.read(table+8,8) else None),'overflow_elements':u(q(entry+8)+0x44)}
assert out['resource_hash_verified'] and actors==0 and count==size==1
assert out['player_definitions'][0]['id']==out['failing_runtime_index']==3
assert q(entry+8)!=players and out['overflow_elements']==410592809
(O/'cause_02.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
lines=[]
for a,n in [(0x2c9490,900),(0x2c99d4,145),(0x2c9f51,70)]:
 lines+=['\nRVA '+hex(a)]+[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in cs.disasm(pe.get_data(a,n),a)]
(O/'cause_02.asm').write_text('\n'.join(lines))
summary=[]
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
for p in sorted((W/'prealpha/housing_h1/native/build/native_06/readback').glob('*.scene.json')):
 x=json.loads(p.read_text());r=x['Data']['RootChunk'];ids=[a['actorId']['id'] for a in r['actors']+r['playerActors']];refs=sorted({v['id'] for v in walk(r) if v.get('$type')=='scnActorId'});perf=sorted({v['id'] for v in walk(r) if v.get('$type')=='scnPerformerId' and v['id']&255==1});summary.append({'scene':p.name,'actors':[a['actorId']['id'] for a in r['actors']],'players':[a['actorId']['id'] for a in r['playerActors']],'valid_dense':ids==list(range(len(ids))),'actor_refs':refs,'actor_performers':perf})
(O/'housing_scope_01.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

