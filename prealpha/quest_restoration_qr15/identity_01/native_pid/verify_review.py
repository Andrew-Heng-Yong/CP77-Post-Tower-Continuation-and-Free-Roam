"""Verify bounded native identity/serialization premises; no native or save execution."""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from inspect_pid import Image,WORKSPACE
out=HERE/'verification_01.json';contract=HERE/'key_contract_01.json';manifest=HERE/'manifest_01.json'
assert all(not p.exists() for p in (out,contract,manifest))
im=Image();rows={};count=0;qcount=0
for p in sorted(HERE.glob('native_*.json')):
    v=json.loads(p.read_text());assert v['exe_sha256']==im.sha
    for f in v['functions']+v['explicit_spans']:
        for r in f['instructions']:
            a=int(r['rva'],16);b=bytes.fromhex(r['bytes']);assert im.data[im.off(a):im.off(a)+len(b)]==b
            if a in rows:assert rows[a]['bytes']==r['bytes']
            rows[a]=r;count+=1
    for words in v['qwords'].values():
        for a,b in words:
            assert struct.unpack_from('<Q',im.data,im.off(int(a,16)))[0]==int(b,16);qcount+=1
def op(a,m,s):return rows[a]['mnemonic']==m and rows[a]['operands']==s
def ptr(a,b):return struct.unpack_from('<Q',im.data,im.off(a))[0]==im.base+b
def rip(a):
    b=bytes.fromhex(rows[a]['bytes']);return a+len(b)+struct.unpack('<i',b[-4:])[0]
def string(a):return im.data[im.off(a):].split(b'\0',1)[0].decode()
checks=[]
def check(name,value,evidence):
    assert value,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
check('GetConstAccessToPSObject exact name and registered handler',string(rip(0x134A151))=='GetConstAccessToPSObject' and rip(0x134A198)==0x802424 and op(0x134A1B1,'mov','qword ptr [rsp + 0x20], rax') and op(0x134A1B6,'call','0x1406bece4'),'native_01/02')
check('PersistencySystem exact RTTI ConstructCls and instance vtable',string(rip(0x173421F))=='gamePersistencySystem' and ptr(0x332B058+0xD8,0x5A14B0) and op(0x5A14B3,'jmp','0x1405a02c8') and rip(0x5A02D6)==0x36343D8,'native_02/03/04/06')
check('Exact lookup, save and load virtuals',ptr(0x36343D8+0x1B0,0x408DB4) and ptr(0x36343D8+0x138,0x2A35150) and ptr(0x36343D8+0x148,0x59FB28),'native_07')
check('Registered ConstAccess passes allocation-enabled path1',op(0x80253F,'mov','byte ptr [rsp + 0x20], 1') and op(0x80254F,'call','0x140408db4'),'native_03')
check('Lookup input zero entity guard precedes native hash',op(0x408DD3,'mov','r8, qword ptr [r8]') and op(0x408DDC,'test','r8, r8') and op(0x408DDF,'je','0x140408f86') and op(0x408DFF,'call','0x140409010'),'native_04')
check('Hash exact field order entity0 component8',op(0x409010,'mov','r8, qword ptr [rcx + 8]') and op(0x409014,'mov','rdx, qword ptr [rcx]'),'native_05; entity eligibility consumes first field')
check('Hash zero component bypass and unsigned arithmetic constant/shift',op(0x40901A,'je','0x14040903f') and op(0x40901C,'movabs','rcx, 0xc6a4a7935bd1e995') and op(0x40902D,'shr','rax, 0x2f') and op(0x40903F,'mov','rax, rdx'),'native_05 full leaf')
check('Hash result is passed unchanged into record table48',op(0x408E08,'lea','rcx, [r15 + 0x48]') and op(0x408E0C,'mov','r8, rax') and op(0x408E13,'call','0x140409044'),'native_04')
check('Zero key cannot allocate a normal record',op(0x409064,'test','r8, r8') and op(0x409067,'jne','0x140409082') and op(0x409078,'mov','rbx, r8'),'native_05 complete zero branch')
check('Record table creation stores exact incoming UInt64 key at record0',op(0x409159,'mov','qword ptr [rsp + 0x10], rdx') and op(0x409275,'mov','rax, qword ptr [rbp + 0x48]') and op(0x40927C,'mov','qword ptr [rdi], rax'),'native_06')
check('Low24 eligibility delegates dynamic status lookup instead of unconditional rejection',op(0x408FB5,'test','r8, -0x1000000') and op(0x408FBC,'je','0x140408ff7') and op(0x408FF7,'call','0x1402fac58'),'native_05')
check('Dynamic eligibility uses UInt32 ID and map1E8',op(0x2FAC6F,'mov','esi, r8d') and op(0x2FAC85,'lea','rcx, [rbx + 0x1e8]') and op(0x2FACA5,'mov','al, byte ptr [rcx + 0xc]') and op(0x2FACB2,'or','al, 3') and op(0x2FACDE,'mov','byte ptr [rsp + 0x28], 1'),'native_06')
check('Lookup requires eligibility mask2 before hash lookup',op(0x408DF2,'test','sil, 2') and op(0x408DF6,'je','0x140408f86'),'native_04')
check('Status2 shares the same dynamic map and nonzero value flag',ptr(0x36343D8+0x1F0,0x4CB220) and op(0x4CB25E,'lea','rcx, [rdi + 0x1e8]') and op(0x4CB27E,'cmp','byte ptr [rax + 0xc], 0') and op(0x4CB242,'mov','eax, 2'),'native_07/08')
check('Changing dynamic persistence flag updates map separately',op(0x2FD712,'lea','rcx, [rbx + 0x1e8]') and op(0x2FD728,'mov','byte ptr [rax], dil') and op(0x2FD738,'call','0x140716e3c'),'native_09; downstream callback policy not expanded')
check('PS2 exact named node used by writer and loader',string(rip(0x19225F4))=='PersistencySystem2' and op(0x2A35295,'call','0x1419225d4') and op(0x59FE86,'call','0x1419225d4'),'native_02/03')
check('First PS2 Ids enumerates map1E8 keys32 with nonzero flagC',op(0x2A3530A,'mov','r8, qword ptr [rdi + 0x1e8]') and op(0x2A35339,'lea','rdx, [rbx + 8]') and op(0x2A3533D,'cmp','byte ptr [rbx + 0xc], r12b') and op(0x2A35348,'call','0x1401e07bc'),'native_03 full writer')
check('First PS2 Ids count and raw keys use UInt32 widths',op(0x2A353A3,'sar','rsi, 2') and op(0x2A353A9,'call','0x142a35018') and op(0x2A353B6,'lea','r8d, [rsi*4]') and op(0x2A35028,'mov','r8d, 4'),'native_03/07')
check('Writer zero field precedes record count and table48 enumeration',op(0x2A353D2,'xor','edx, edx') and op(0x2A353D7,'call','0x142a35018') and op(0x2A353DC,'lea','r13, [rdi + 0x48]') and op(0x2A353F4,'call','0x142a35018'),'native_03')
check('Modern load reads UInt32 Ids and restores same map value1',op(0x59FECC,'lea','rdi, [r15 + 0x1e8]') and op(0x59FEF0,'call','0x1418f0064') and op(0x59FF23,'call','0x142608060') and op(0x59FF2C,'mov','byte ptr [rax], 1') and op(0x18F00B6,'shl','r8, 2'),'native_03/07; modern save-version branch')
check('Modern PS2 loader gate is version205',op(0x59FB67,'call','qword ptr [rax + 0x48]') and op(0x59FB6A,'cmp','eax, 0xcd') and op(0x59FB6F,'jae','0x14059fc97'),'native_03; prior source binding names stream48 SaveVersion')
check('Writer verifies record0 equals table key before saving',op(0x2A35427,'call','0x140408c58') and op(0x2A35440,'mov','rcx, qword ptr [rdi]') and op(0x2A35443,'cmp','rcx, rsi'),'native_03')
check('Writer filters records using masks04 and01',op(0x2A35470,'mov','al, byte ptr [rdi + 0x79]') and op(0x2A35473,'test','al, 4') and op(0x2A3547B,'test','al, 1'),'native_03')
check('First saved entry UInt64 is record key0 and separate next UInt64 is class18',op(0x2A353FD,'mov','r15d, 8') and op(0x2A3548A,'mov','qword ptr [rbp + 0x60], rcx') and op(0x2A35494,'call','qword ptr [rax + 0x10]') and op(0x2A35497,'mov','rax, qword ptr [rdi + 0x18]') and op(0x2A354AC,'call','qword ptr [rax + 0x10]'),'native_03 full save data flow')
check('Load entry key is UInt64 and zero row skips remaining record',op(0x5A028E,'mov','r8d, 8') and op(0x59FFBD,'call','0x1405a027c') and op(0x59FFC2,'mov','rbx, rax') and op(0x59FFC8,'je','0x1405a0232'),'native_03/05')
check('Load inserts key unchanged into same record table',op(0x5A001D,'lea','rcx, [r15 + 0x48]') and op(0x5A0021,'mov','r8, rbx') and op(0x5A0029,'call','0x140408bf8') and op(0x408C1E,'call','0x140409154'),'native_03/09')
check('Lookup really can materialize and attach state',op(0x408F08,'call','0x140bed864') and op(0x408F31,'mov','qword ptr [rax + 0x60], r15') and op(0x408F35,'movups','xmm0, xmmword ptr [r13]') and op(0x408F3A,'movdqu','xmmword ptr [rax + 0x48], xmm0') and op(0x408F4C,'call','0x14018a5a4'),'native_04; API not approved as passive diagnostic')
controls=json.loads((HERE/'hash_controls_01.json').read_text())
check('Twelve arithmetic controls bind SDK formula and native instruction interpretation',controls['control_count']==12 and controls['all_pass'] and all(c['pass'] for c in controls['controls']),'hash_controls_01.json; no native execution')
check('Two prior candidate values reproduced exactly',[c['native_instruction_arithmetic'] for c in controls['controls'][-3:-1]]==['6695448052237678836','15311582179580628726'],'Hash arithmetic only, no PS existence inference')
check('Nonzero identity can mathematically hash to reserved zero key',int(controls['controls'][-1]['entity_u64'])!=0 and int(controls['controls'][-1]['component_cname_u64'])!=0 and controls['controls'][-1]['native_instruction_arithmetic']=='0','Pure arithmetic zero-collision control')
origin=HERE.parent/'entity_origin/evidence_01.json';origin_sha=hashlib.sha256(origin.read_bytes()).hexdigest().upper()
check('EntityID namespace proof reused at exact sealed bytes',origin_sha=='93F9F278B57E98C087B88F4EB44B70AE0EC1D2A43F632E53DAC832984204BE81','entity_origin/REPORT.md and17check verification_02; not re-audited')
meta_path=HERE.parent/'save_inventory/capture_01/ps2_ids.json'
before=meta_path.read_bytes();meta=json.loads(before);ids=[int(v) for v in meta['ids_u64']]
check('Coordinator metadata has2165 enabled-list IDs, excluding target',len(ids)==2165 and 10229047 not in ids and all(0<=v<=0xFFFFFFFF for v in ids),'Retained metadata file only; coordinator owns original save provenance')
assert meta_path.read_bytes()==before
contract_data={'exe_sha256':im.sha,'persistent_id_memory':{'entityID':'UInt64 at0','componentName':'CName UInt64 at8'},
    'hash_helper_rva':'0x409010','magic':'0xC6A4A7935BD1E995','arithmetic':'UInt64 wrapping; component0 returns entity; otherwise M*(entity XOR M*((M*component mod2^64) XOR ((M*component mod2^64)>>47))) mod2^64',
    'ps2_header_ids':{'kind':'UInt32 dynamic-ID keys from table+1E8 where value byte!=0','not_kind':'Component hash or complete population/record table','restored_value':1},
    'ps2_entry_id':{'kind':'UInt64 native PersistentID key, record+0 in table+48','following_class':'Separate UInt64 CName from record+18','zero':'Skipped/missing/filtered record marker, not actor absence'},
    'associated_id_u64':'10229047','associated_hex':'0x9C1537','namespace':'EntityID candidate by separately sealed native population-to-CreateStub trace; no numeric StubID conversion',
    'candidate_keys':{'controller':'6695448052237678836','VehicleController':'15311582179580628726'},
    'metadata':{'path':str(meta_path),'sha256':hashlib.sha256(before).hexdigest().upper(),'count':len(ids),'target_present':False,'source_scope':'Metadata read only; coordinator extraction owns save-body binding'},
    'read_only_api_approved':False,'get_const_access_warning':'Registered handler passes1 and lookup can allocate/hydrate/create/attach/init state; no call approved or made',
    'remaining':['Exact component identity and selected record/body match','Current actor or live session binding','Visual/door/queued-event completion and repair safety'],
    'game_api_calls':0,'runtime_changes':0,'save_reads':0}
contract.write_text(json.dumps(contract_data,indent=2)+'\n',encoding='utf-8')
result={'status':'NATIVE_PID_CODEC_PS2_KEY_AND_DYNAMIC_HEADER_BINDINGS_CLOSED_NO_STATE_ABSENCE_OR_LIVE_API_CLAIM','exe_sha256':im.sha,'checks':checks,'check_count':len(checks),
    'verified_instruction_spans':count,'unique_verified_instruction_starts':len(rows),'verified_qwords':qcount,'pure_arithmetic_controls':12,'game_api_calls':0,'runtime_changes':0,'save_reads':0,'builds':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
sdk=WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext'
sources=[sdk/'Scripting/Natives/gamePersistentID.hpp',sdk/'Scripting/Natives/entEntityID.hpp',sdk/'Scripting/Natives/gameIPersistencySystem.hpp',sdk/'CName.hpp',origin,HERE.parent/'entity_origin/REPORT.md',meta_path,HERE.parent/'save_inventory/capture.ps1']
pins=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sources]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted(HERE.iterdir()) if p.is_file()]
manifest.write_text(json.dumps({'exe_sha256':im.sha,'source_pins':pins,'files':files,'game_api_calls':0,'runtime_changes':0,'save_reads':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
