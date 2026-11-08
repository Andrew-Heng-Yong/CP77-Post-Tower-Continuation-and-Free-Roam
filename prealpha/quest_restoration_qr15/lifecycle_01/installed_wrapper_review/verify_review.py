"""Independent byte/registration checks for the disputed installed flag layout."""
from pathlib import Path
import hashlib, json, struct, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from inspect_installed import Image, WORKSPACE, DLL
out=HERE/'verification_01.json'; manifest=HERE/'manifest_01.json'
assert not out.exists() and not manifest.exists()
im=Image(); rows={}; count=0; qcount=0
for p in sorted(HERE.glob('installed_*.json')):
    v=json.loads(p.read_text()); assert v['dll_sha256']==im.sha
    for f in v['functions']+v['explicit_spans']:
        for row in f['instructions']:
            a=int(row['rva'],16); b=bytes.fromhex(row['bytes'])
            assert im.data[im.off(a):im.off(a)+len(b)]==b
            if a in rows: assert rows[a]['bytes']==row['bytes']
            rows[a]=row;count+=1
    for words in v['qwords'].values():
        for a,b in words:
            assert struct.unpack_from('<Q',im.data,im.off(int(a,16)))[0]==int(b,16);qcount+=1
def op(a,m,s): return rows[int(a,16)]['mnemonic']==m and rows[int(a,16)]['operands']==s
def rip(a):
    a=int(a,16);b=bytes.fromhex(rows[a]['bytes']);return a+len(b)+struct.unpack('<i',b[-4:])[0]
def text(a): return im.data[im.off(a):].split(b'\0',1)[0].decode()
def fnv(value):
    v=0xCBF29CE484222325
    for b in value.encode():v=((v^b)*0x100000001B3)&0xFFFFFFFFFFFFFFFF
    return v
checks=[]
def check(name,value,evidence):
    assert value,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
identity=json.loads((HERE/'pdb_identity_01.json').read_text())
check('Exact installed DLL matches current77 dependency pin',identity['dll_sha256']==im.sha and identity['baseline']['installed_pin_count']==77 and identity['baseline']['matched_dll_pin']['sha256']==im.sha,'pdb_identity_01.json')
check('CodeView readback unchanged',identity['codeview']==im.codeview(),'installed PE debug directory RSDS')
check('Both existing local PDB identities mismatch installed GUID/age',len(identity['local_pdb_identities'])==2 and all(not r['matches_installed_codeview'] for r in identity['local_pdb_identities']),'pdb_identity_01.json; no symbol attribution from either file')
check('Existing PDB identity evidence still pins their exact bytes',all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest().upper()==r['sha256'] for r in identity['local_pdb_identities']),'Two preexisting PDB SHA256 readbacks')
check('Class hash binds PopulationSpawnerWrapper independently',fnv('PopulationSpawnerWrapper')==0x9E16D17C1829E805 and op('0xe1cdf','movabs','rbx, 0x9e16d17c1829e805') and op('0xe1d81','call','0x1800e16e0'),'installed_07; CName FNV1a64 codec')
check('IsActive exact RTTI name and callback target',rip('0xe1726')==0xE1360 and text(rip('0xe172d'))=='IsActive' and rip('0xe172d')==rip('0xe1734') and op('0xe173e','call','0x180036080'),'installed_02')
check('IsInitialized exact RTTI name and callback target',rip('0xe1778')==0xE1390 and text(rip('0xe177f'))=='IsInitialized' and rip('0xe177f')==rip('0xe1786') and op('0xe1790','call','0x180036080'),'installed_02')
check('Method-registration helper forwards exact callback unchanged',op('0x36098','mov','r14, r9') and op('0x3614d','mov','qword ptr [rsp + 0x20], r14'),'installed_03')
check('IsActive reads pointer40 then native byte10',op('0xe136c','mov','rax, qword ptr [rcx + 0x40]') and op('0xe1379','movzx','eax, byte ptr [rax + 0x10]'),'installed_04 explicit leaf continuation')
check('IsInitialized reads pointer40 then native byte11',op('0xe139c','mov','rax, qword ptr [rcx + 0x40]') and op('0xe13a9','movzx','eax, byte ptr [rax + 0x11]'),'installed_04 explicit leaf continuation')
check('Null wrapper member returns false through output byte',op('0xe1370','test','rax, rax') and op('0xe1375','mov','byte ptr [r8], al') and op('0xe13a0','test','rax, rax') and op('0xe13a5','mov','byte ptr [r8], al'),'installed_04')
check('GetPopulationSpawner RTTI registration binds callback',rip('0xf1a9e')==0xEF690 and text(rip('0xf1aa5'))=='GetPopulationSpawner' and op('0xf1ab6','call','0x180036080'),'installed_05')
check('Getter return type exactly names PopulationSpawnerWrapper',im.data[im.off(0x177520):im.off(0x177520)+16]+im.data[im.off(0x1774F0):im.off(0x1774F0)+16]==b'handle:PopulationSpawnerWrapper\0' and rip('0xf087c')==0x177520 and rip('0xf088a')==0x1774F0,'installed_06/07 two SSE constant blocks')
check('Getter callback reaches installed implementation',op('0xef6a7','call','0x1800f1290') and op('0xf1333','call','0x1800f27d0'),'installed_06/07')
check('Getter calls native community virtual260',op('0xf2843','mov','rcx, qword ptr [rbx + 0x68]') and op('0xf284a','mov','r9, qword ptr [rax + 0x260]') and op('0xf2855','call','r9'),'installed_08')
check('Getter forwards locked pointer pair to wrapper constructor',op('0xf29eb','movaps','xmm0, xmmword ptr [rbp - 0x50]') and op('0xf29ef','movdqa','xmmword ptr [rbp - 0x30], xmm0') and op('0xf29f4','lea','rdx, [rbp - 0x30]') and op('0xf29fb','call','0x1800e13c0'),'installed_08')
check('Wrapper constructor stores native pointer unadjusted at40',op('0xe13ee','mov','rax, qword ptr [rbx]') and op('0xe13f1','mov','qword ptr [rdi + 0x40], rax') and op('0xe13f5','mov','rax, qword ptr [rbx + 8]') and op('0xe13f9','mov','qword ptr [rdi + 0x48], rax'),'installed_09')
capture=WORKSPACE/'prealpha/quest_restoration_qr15/lifecycle_01/community_native/capture_01.json'
capture_hash=hashlib.sha256(capture.read_bytes()).hexdigest().upper()
check('Separately sealed native pointer evidence matches agreed artifact',capture_hash=='A2805CC1E047115D2D2D7188E5001E6713392D82B54CB017E4B5600E6C15E343','community_native/capture_01.json')
sys.path.insert(0,str(WORKSPACE/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image as NativeImage
native=NativeImage(); cap=json.loads(capture.read_text());nrows={};ncount=0
for name in ('spawner_ctor','spawner_weak_getter','spawner_weak_lookup','shared_pointer_swap','ordinary_activate'):
    f=cap['functions'][name]
    for i in f['instructions']:
        a=int(i['rva'],16);b=bytes.fromhex(i['bytes']);assert native.data[native.off(a):native.off(a)+len(b)]==b
        nrows[a]=i;ncount+=1
def nop(a,m,s): return nrows[a]['mnemonic']==m and nrows[a]['operands']==s
check('Native ctor stores ID08 and flags10 at allocation base',nop(0x384480,'mov','qword ptr [rcx + 8], rdx') and nop(0x38449B,'mov','word ptr [rcx + 0x10], r15w'),'Native selected bytes independently rechecked')
check('Native ordinary activation uses initialized11 and active10',nop(0x9CEFBC,'cmp','byte ptr [rcx + 0x11], 0') and nop(0x9CEFC2,'cmp','byte ptr [rcx + 0x10], 0') and nop(0x9CEFCB,'mov','byte ptr [rcx + 0x10], 1'),'Native selected bytes independently rechecked')
check('Exact native community v260 binds getter38360C',struct.unpack_from('<Q',native.data,native.off(0x30D3A18+0x260))[0]==native.base+0x38360C,'Pinned EXE instance vtable')
local_header=WORKSPACE/'research/framework_pr63_01/codeware/src/Red/CommunitySystem.hpp'
local_text=local_header.read_text();spawner=local_text.split('struct Spawner',1)[1].split('namespace Raw::CommunitySystem',1)[0]
check('Research header mismatch is source-only evidence', 'bool active;' in spawner and '// 08' in spawner and 'bool initialized;' in spawner and '// 09' in spawner,'Current local research Red::Spawner declaration; installed callbacks instead10/11')
report={'status':'INSTALLED_FLAG_ABI_CORRECT_LOCAL_HEADER_STALE_NO_FRAMEWORK_FIX_STAGED',
        'dll_sha256':im.sha,'native_exe_sha256':native.sha,'checks':checks,'check_count':len(checks),
        'installed_instruction_spans_verified':count,'installed_unique_instruction_starts':len(rows),
        'installed_qwords_verified':qcount,'selected_native_instruction_spans_verified':ncount,
        'game_api_calls':0,'runtime_changes':0,'save_reads':0,'framework_source_edits':0,'builds':0,'downloads':0,
        'limits':['No live wrapper flag observation occurred in JF02','No exact live nil-return site identified','No physical prefab/population/spawner retirement or prepared-stage certification','No matching local PDB used; names bound from installed RTTI/thunks']}
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
source_paths=[local_header,WORKSPACE/'research/framework_pr63_01/codeware/src/App/World/PopulationSpawnerWrapper.cpp',WORKSPACE/'research/framework_pr63_01/codeware/src/App/World/PopulationSpawnerWrapper.hpp',WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/CName.hpp',DLL.parent/'Scripts/Codeware.Global.reds',capture]
pins=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in source_paths]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted(HERE.iterdir()) if p.is_file()]
manifest.write_text(json.dumps({'dll_sha256':im.sha,'source_pins':pins,'files':files,'runtime_changes':0,'game_api_calls':0,'save_reads':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
