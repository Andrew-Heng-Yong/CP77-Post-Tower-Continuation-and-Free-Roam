"""Verify exact static dispatch premises and pinned action objects; no game APIs."""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from inspect_spawn import Image,WORKSPACE
out=HERE/'verification_01.json';binding_out=HERE/'bindings_01.json';manifest=HERE/'manifest_01.json'
assert all(not p.exists() for p in (out,binding_out,manifest))
im=Image();rows={};count=0;qcount=0
def retain(f):
    global count
    for row in f['instructions']:
        a=int(row['rva'],16);b=bytes.fromhex(row['bytes'])
        assert im.data[im.off(a):im.off(a)+len(b)]==b
        if a in rows:assert rows[a]['bytes']==row['bytes']
        rows[a]=row;count+=1
for p in sorted(HERE.glob('native_*.json')):
    v=json.loads(p.read_text());assert v['exe_sha256']==im.sha
    for f in v['functions']+v['explicit_spans']:retain(f)
    for words in v['qwords'].values():
        for a,b in words:
            assert struct.unpack_from('<Q',im.data,im.off(int(a,16)))[0]==int(b,16);qcount+=1
capture=HERE.parent/'community_native/capture_01.json'
capture_sha=hashlib.sha256(capture.read_bytes()).hexdigest().upper()
assert capture_sha=='A2805CC1E047115D2D2D7188E5001E6713392D82B54CB017E4B5600E6C15E343'
captured=json.loads(capture.read_text())
selected=('spawn_manager_class_registration','spawn_manager_ctor_thunk','spawn_manager_ctor','spawn_manager_handler_factory',
    'spawn_manager_handler_init','spawner_action_registration','spawner_action_ctor','spawner_action_execute','spawner_action_live','spawner_action_reset',
    'community_class_registration','community_construct_cls_thunk','community_instance_ctor','spawner_weak_lookup','action_dispatcher','ordinary_activate','activate_facade','deactivate_facade','reset_facade')
for name in selected:retain(captured['functions'][name])
def op(a,m,s):return rows[a]['mnemonic']==m and rows[a]['operands']==s
def ptr(a,b):return struct.unpack_from('<Q',im.data,im.off(a))[0]==im.base+b
def string(a):return im.data[im.off(a):].split(b'\0',1)[0].decode()
def rip(a):
    b=bytes.fromhex(rows[a]['bytes']);return a+len(b)+struct.unpack('<i',b[-4:])[0]
checks=[]
def check(name,value,evidence):
    assert value,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
bindings=[
 {'class':'questSpawnManagerNodeDefinition','name_rva':0x32BDB68,'registration_rva':0x16A248C,'metadata_rva':0x32BDB88,'construct_rva':0x35230C,'ctor_rva':0x352314,'instance_vtable_rva':0x30473D0,'methods':{'0x158':0xFA404C,'0x188':0x36CBB0}},
 {'class':'questSpawner_NodeType','name_rva':0x32BE1C0,'registration_rva':0x16A2D14,'metadata_rva':0x32BE1D8,'construct_rva':0xD6EF04,'ctor_rva':0xD6EF04,'instance_vtable_rva':0x30FCB68,'methods':{'0x110':0x36DFD0}},
 {'class':'questCommunityTemplate_NodeType','name_rva':0x32BE0B0,'registration_rva':0x16A2BA8,'metadata_rva':0x32BE0D0,'construct_rva':0xCA8F08,'ctor_rva':0xCA8F08,'instance_vtable_rva':0x30E0230,'methods':{'0x110':0x36D1B4}}]
for b in bindings:
    check(b['class']+' exact RTTI name and ConstructCls',string(b['name_rva'])==b['class'] and ptr(b['metadata_rva']+0xD8,b['construct_rva']),'Pinned EXE strings and metadataD8')
    check(b['class']+' instance vtable method binding',all(ptr(b['instance_vtable_rva']+int(s,16),v) for s,v in b['methods'].items()),'Constructor disassembly plus exact table')
check('Constructor chain really writes each instance vtable',rip(0x352383)==0x30473D0 and rip(0xD6EF33)==0x30FCB68 and rip(0xCA8F37)==0x30E0230,'Exact ctor LEA and following vptr stores')
check('Generic Execute checks existing handler then creates through common factory',op(0xFA407A,'call','qword ptr [rax + 0x80]') and op(0xFA408B,'call','0x1402b054c'),'native_01; common188 factory reused from prior sealed review')
check('Spawn factory walks definition actions and calls action virtual110',op(0x36CBE6,'lea','r8, [rbx + 0x48]') and op(0x36CBF0,'call','0x14036cc40') and op(0x36CCBE,'call','qword ptr [rax + 0x110]'),'Sealed community capture selected bytes')
check('Special action branch is explicitly context byte1 equals2',op(0x88BB64,'mov','rax, qword ptr [rcx + 0x220]') and op(0x88BB6B,'cmp','byte ptr [rax + 1], 2') and op(0x88BB6F,'sete','al'),'native_03; alternate helpers not certified')
check('Population action normal branch reaches36E038',op(0x36E00B,'test','r9b, r9b') and op(0x36E010,'call','0x14036e038'),'Sealed community capture')
check('Population action resolves reference and uses v258 population lookup',op(0x36E091,'call','0x140351030') and op(0x36E0A4,'mov','r9, qword ptr [rcx + 0x258]') and ptr(0x30D3A18+0x258,0x36E160) and op(0x36E170,'call','0x140383660'),'capture plus native_01')
check('Population Activate1 calls1D8 and Reactivate3 calls1E0 before1D8',op(0x36E0E1,'je','0x14036e115') and op(0x36E10F,'call','qword ptr [rax + 0x1e0]') and op(0x36E11E,'call','qword ptr [rax + 0x1d8]'),'Selected full36E038 branch disassembly')
check('Population ResetKillCount4 is separate1E8 branch',op(0x245E43A,'call','qword ptr [rax + 0x1e8]'),'Sealed cold block245E428')
check('Population ordinary activate has init11 and active10 no-op guards',op(0x9CEFBC,'cmp','byte ptr [rcx + 0x11], 0') and op(0x9CEFC2,'cmp','byte ptr [rcx + 0x10], 0') and op(0x9CEFC6,'jne','0x1409cefd2') and op(0x9CEFCB,'mov','byte ptr [rcx + 0x10], 1'),'Selected ordinary_activate full function')
check('Community normal action reaches36D28C and uses v230 community lookup',op(0x36D218,'call','0x14036d28c') and op(0x36D2E5,'call','0x140351030') and op(0x36D2F8,'mov','r9, qword ptr [rcx + 0x230]') and ptr(0x30D3A18+0x230,0x46757C),'native_05/06/07/09')
check('Community Activate optional phase1C0 then1B0',op(0x36D336,'cmp','qword ptr [rsi + 0x18], 0') and op(0x36D34E,'call','qword ptr [rax + 0x1c0]') and op(0x36D361,'call','qword ptr [rax + 0x1b0]'),'native_07')
check('Community Deactivate and Reactivate have extra cancellation1D0',op(0x36D3BF,'call','qword ptr [rax + 0x1d0]') and op(0x36D3D2,'call','qword ptr [rax + 0x1b8]') and op(0x36D3F0,'call','qword ptr [rax + 0x1d0]') and op(0x36D403,'call','qword ptr [rax + 0x1b8]') and op(0x36D409,'jmp','0x14036d336'),'native_07')
check('Exact community action facade bindings',ptr(0x30D3A18+0x1B0,0x36D42C) and ptr(0x30D3A18+0x1B8,0x36C714) and ptr(0x30D3A18+0x1C0,0x36D540) and ptr(0x30D3A18+0x1D0,0x36DF5C),'native_02 and pinned instance vtable')
check('Community facades enqueue operation0/1/2 under lockA0',op(0x36D464,'mov','byte ptr [rsp + 0x68], bl') and op(0x36C74C,'mov','byte ptr [rsp + 0x68], 1') and op(0x36D57C,'mov','byte ptr [rsp + 0x30], 2') and op(0x36D44E,'lea','rdx, [rdi + 0xa0]'),'native_03/08')
check('Queue tail appends32byte rows without state counter increment',op(0x36D4BE,'inc','ebx') and op(0x36D4EE,'shl','rcx, 5') and op(0x36D510,'mov','byte ptr [rax + 0x18], r9b'),'native_04; this increment is queue length, not entry state')
check('Root native tick calls community update4676DC',op(0x71EE1E,'call','0x1404676dc'),'native_05; separate from preceding spawner tick')
check('Community queue consumer reads same queue and clears its source count',op(0x467816,'lea','rdx, [rsi + 0x48]') and op(0x467826,'and','dword ptr [rsi + 0x54], 0') and op(0x4678B4,'add','rbx, 0x20'),'native_06')
check('Consumer maps community Activate to guarded entry helper',op(0x4678AF,'call','0x140fb2680') and op(0xFB2699,'jmp','0x140fb26a0') and op(0xFB26BC,'call','0x140467ecc') and op(0xFB26DF,'call','0x140467ecc'),'native_06/07/08')
check('Community entry Activate is zero-to-one, no increment on nonzero',op(0x467ED0,'mov','eax, dword ptr [rcx + 0x28]') and op(0x467ED5,'jne','0x140467ee5') and op(0x467ED7,'mov','eax, 1') and op(0x467EDC,'xchg','dword ptr [rcx + 0x28], eax') and op(0x467EE2,'call','qword ptr [rdx + 0x18]'),'native_09 entire10-instruction function')
check('Community entry Deactivate has its own zero guard and virtual20',op(0x468641,'test','eax, eax') and op(0x468645,'ret','') and op(0x468646,'xchg','dword ptr [rcx + 0x28], edx') and op(0x46864C,'jmp','qword ptr [rax + 0x20]'),'native_10 explicit leaf span')
check('Extra cancellation zero-name path really removes matching pair rows',op(0x36DF6B,'mov','rsi, qword ptr [rcx + 0xf0]') and op(0x36DFA7,'cmp','qword ptr [rbx], rdi') and op(0x245E417,'call','0x14196a250') and op(0x245E41C,'dec','dword ptr [rsi + 0x94]'),'native_08/12; full semantic identity of pair requests unknown')
payload=json.loads((HERE/'action_payloads_01.json').read_text())
check('Four exact native payloads source hash unchanged',hashlib.sha256(Path(payload['source']['path']).read_bytes()).hexdigest().upper()==payload['source']['sha256'],'action_payloads_01')
by_id={r['id']:r['action_payload'] for r in payload['four_source_objects']}
check('Exact type split and ordinary actions are preserved',by_id[101]['$type']=='questSpawner_NodeType' and all(by_id[n]['$type']=='questCommunityTemplate_NodeType' for n in (86,142,143)) and [by_id[n]['action'] for n in (101,142,143,86)]==['Activate','Activate','Deactivate','Activate'],'action_payloads_01')
check('Exact community payloads use zero entry/phase names',all(by_id[n]['communityEntryName']['$value']=='None' and by_id[n]['communityEntryPhaseName']['$value']=='None' for n in (86,142,143)),'No SetPhase side effect is selected by these3sourceobjects')
sdk=WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated'
enum=sdk/'population/SpawnerObjectCtrlAction.hpp'
enum_text=enum.read_text()
check('SDK action byte meanings agree with branch selectors',all(v in enum_text for v in ('Activate = 1','Deactivate = 2','Reactivate = 3','ResetKillCount = 4')),'Generated SDK enum')
binding_out.write_text(json.dumps({'exe_sha256':im.sha,'bindings':bindings,'shared_community_instance_vtable':hex(0x30D3A18),'reused_capture_sha256':capture_sha,'game_api_calls':0,'runtime_changes':0},indent=2)+'\n',encoding='utf-8')
result={'status':'EXACT_ACTION_DISPATCH_BOUND_ACTIVATE_GUARDS_CLOSED_COMPLETE_PREFIX_REPEAT_NOT_CERTIFIED',
    'exe_sha256':im.sha,'checks':checks,'check_count':len(checks),'verified_instruction_spans':count,'unique_verified_instruction_starts':len(rows),'verified_qwords':qcount,
    'game_api_calls':0,'runtime_changes':0,'save_reads':0,'builds':0,
    'limits':['Context byte1==2 alternate action branches are not certified','Target live identities/stage/actor placement unknown','Community Deactivate143 also removes matching pending pair rows; pair semantic ownership remains unknown','No full startup replay, prepared adapter, world/population retirement or inactive activation callback safety certification']}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
source_paths=[enum,sdk/'quest/SpawnManagerNodeDefinition.hpp',sdk/'quest/SpawnManagerNodeActionEntry.hpp',sdk/'quest/SpawnManagerNodeType.hpp',sdk/'quest/Spawner_NodeType.hpp',sdk/'quest/CommunityTemplate_NodeType.hpp',capture]
pins=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in source_paths]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted(HERE.iterdir()) if p.is_file()]
manifest.write_text(json.dumps({'exe_sha256':im.sha,'source_pins':pins,'files':files,'game_api_calls':0,'runtime_changes':0,'save_reads':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
