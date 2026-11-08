"""Verify exact flag/data/registration contracts from pinned native bytes; no save access."""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from inspect_pid import Image,WORKSPACE
out=HERE/'verification_01.json';manifest=HERE/'manifest_01.json';findings=HERE/'findings_01.json'
assert all(not p.exists() for p in (out,manifest,findings))
im=Image();rows={};span_count=0;qcount=0
source_files=list(sorted(HERE.glob('native_*.json')))+[HERE.parent/n for n in ('native_03.json','native_04.json','native_05.json','native_06.json','native_07.json','native_08.json','native_09.json')]
for p in source_files:
    j=json.loads(p.read_text());assert j['exe_sha256']==im.sha
    for f in j['functions']+j.get('explicit_spans',[]):
        for r in f['instructions']:
            a=int(r['rva'],16);b=bytes.fromhex(r['bytes']);assert im.data[im.off(a):im.off(a)+len(b)]==b
            if a in rows:assert rows[a]['bytes']==r['bytes']
            rows[a]=r;span_count+=1
    for words in j.get('qwords',{}).values():
        for a,b in words:
            assert struct.unpack_from('<Q',im.data,im.off(int(a,16)))[0]==int(b,16);qcount+=1
def op(a,m,s):return rows[a]['mnemonic']==m and rows[a]['operands']==s
def ptr(a,b):return struct.unpack_from('<Q',im.data,im.off(a))[0]==im.base+b
def rip(a):
    b=bytes.fromhex(rows[a]['bytes']);return a+len(b)+struct.unpack('<i',b[-4:])[0]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks=[]
def check(name,condition,evidence):
    assert condition,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
check('Actual EntityStubSystem initialization virtual resolves exact persistence interface',
      ptr(0x31083C0+0x110,0x1818F68) and rip(0x1818F7C)==0x3BC2F10 and
      op(0x1818F89,'mov','qword ptr [rdi + 0xb0], rax'),
      'native_07/08; global type gameIPersistencySystem from sealed entity-origin proof')
check('Ordinary create chain reaches exact stub allocator and constructor',
      op(0x2FA45C,'call','0x1402fa4f4') and op(0x2FA55C,'call','0x1402fa9a8') and
      op(0x2FAA20,'call','0x1402faa48'),'native_04')
check('Cached persistence pointer becomes stub field0',
      op(0x2FA9C1,'mov','rdi, qword ptr [rcx + 0xb0]') and op(0x2FAA11,'mov','qword ptr [rsp + 0x30], rdi') and
      op(0x2FAA58,'mov','rax, qword ptr [rsp + 0x60]') and op(0x2FAA60,'mov','qword ptr [rcx], rax'),
      'native_04 exact stack argument and constructor store')
check('Requested EntityID is stored unchanged at stub40',op(0x2FAA68,'mov','rdi, r8') and
      op(0x2FAA76,'mov','qword ptr [rcx + 0x40], r8'),'native_04')
check('Ordinary constructor registers requested UInt32 ID with argument0 before component attachment',
      op(0x2FAA84,'mov','rcx, qword ptr [r14]') and op(0x2FAA87,'xor','r8d, r8d') and
      op(0x2FAA8E,'mov','edx, edi') and op(0x2FAA93,'call','qword ptr [rax + 0x1e0]') and
      op(0x2FAAA6,'call','0x1402fbc1c'),'native_04')
check('Concrete registration virtual is2FAAEC',ptr(0x36343D8+0x1E0,0x2FAAEC),
      'Exact PersistencySystem RTTI/instance chain previously sealed')
check('Registration true value requires predicate true and third argument exactly1',
      op(0x2FAB0E,'mov','r14d, r8d') and op(0x2FAB16,'call','qword ptr [rax + 0x1d8]') and
      op(0x2FAB20,'je','0x1402fab2a') and op(0x2FAB22,'lea','edi, [rbx + 1]') and
      op(0x2FAB25,'cmp','r14d, edi') and op(0x2FAB28,'je','0x1402fab2d') and
      op(0x2FAB2A,'mov','dil, bl'),'native_01; ebx explicitly zero')
check('Existing registration rows are retained while absent rows receive computed value',
      op(0x2FAB49,'call','0x1402fabf0') and op(0x2FAB4E,'test','byte ptr [rsp + 0x28], 2') and
      op(0x2FAB53,'je','0x1402fab5e') and op(0x2FAB5E,'lea','rcx, [rsi + 0x1e8]') and
      op(0x2FAB6A,'call','0x1405a4fb0') and op(0x2FAB74,'mov','byte ptr [rax], dil'),
      'native_01 exact registration branches')
check('Low-ID false registration is eligible for PS creation while absent row is not',
      op(0x2FACA8,'and','al, 1') and op(0x2FACAF,'shl','al, 2') and op(0x2FACB2,'or','al, 3') and
      op(0x2FACDE,'mov','byte ptr [rsp + 0x28], 1') and op(0x408DF2,'test','sil, 2') and
      op(0x408DF6,'je','0x140408f86'),'Sealed native_04/06 actual lookup and descriptor code')
check('Fresh allocation requests and zero-fill initialization cover0x40000-byte block',
      op(0x216594D,'mov','edx, 0x40000') and op(0x2165962,'xor','edx, edx') and
      op(0x216597D,'call','0x141969f30') and op(0x4091FA,'xor','edx, edx') and
      op(0x4091FC,'mov','r8d, 0x40000') and op(0x409208,'call','0x141969f30'),
      'native_01/02 exact allocator/zero-fill arguments; fresh block only')
check('Record pool uses0x80-byte stride; incoming key assigned separately',
      op(0x409239,'lea','r12, [rdi + 0x80]') and op(0x409246,'sub','r12, -0x80') and
      op(0x40927C,'mov','qword ptr [rdi], rax'),'native_01; reused slot state not universally asserted')
check('Inline and heap buffer choice uses length63 threshold',
      op(0x2165912,'cmp','eax, 0x3f') and op(0x2165915,'ja','0x14216592a') and
      op(0x2165917,'call','0x1404b5e58') and op(0x216592A,'call','0x1404b46c4'),
      'native_04 complete installer')
check('Inline installation sets mask01 even when span is empty',
      op(0x4B5ECD,'cmp','rdx, qword ptr [rdi + 8]') and op(0x4B5ED1,'je','0x1404b5edf') and
      op(0x4B5EDF,'or','byte ptr [rbx + 0x79], 1'),'native_05 exact empty-span path')
check('Heap installation unconditionally sets mask01 after copy',
      op(0x4B4768,'call','0x14196a250') and op(0x4B476D,'or','byte ptr [rdi + 0x79], 1'),
      'native_05')
check('Mask02 selects buffer representation rather than quest stage',
      op(0x4B5E9B,'and','byte ptr [rbx + 0x79], 0xfd') and op(0x4B46E8,'or','al, 2') and
      op(0x2164E87,'test','byte ptr [r8 + 0x79], 2'),'native_01/05')
check('Clear installs empty buffer then explicitly clears mask01',
      op(0x4B5E32,'xorps','xmm0, xmm0') and op(0x4B5E43,'call','0x1404b5e58') and
      op(0x4B5E48,'and','dword ptr [rbx + 8], 0') and op(0x4B5E4C,'and','byte ptr [rbx + 0x79], 0xfe'),
      'native_06 explicit4B5E2C..4B5E58 span, caller-bound')
check('Actual Reset virtual clears the serialized-buffer bit',ptr(0x36343D8+0x1D0,0xABF470) and
      op(0xABF4F7,'call','0x1404b5e2c'),'native_06 exact Reset body; not invoked')
check('Actual dynamic removal drops map row and clears matching known component records',
      ptr(0x36343D8+0x1E8,0x408A50) and op(0x408A74,'lea','rcx, [rbp + 0x1e8]') and
      op(0x408A85,'call','0x1403bb530') and op(0x408ABD,'call','0x140408adc') and
      op(0x408BC2,'call','0x1404b5e2c'),'native_02/06; association enumeration only')
check('Generic object serialization installs a buffer and is not a unique node receipt',
      op(0x4B5FF4,'call','0x140279248') and op(0x4B604D,'call','0x1421658f0') and
      op(0x21650E9,'test','dword ptr [rax + 0x70], 0x400') and op(0x216511C,'call','0x1404b5f70'),
      'native_05/07 generic serializer and actual class mask gate')
check('Create-enabled synchronization distinguishes descriptor bit0 from record mask01',
      op(0x409304,'mov','al, byte ptr [rcx + 8]') and op(0x409307,'not','al') and op(0x409309,'and','al, 1') and
      op(0x408E2F,'call','0x140409304') and op(0x408E36,'je','0x140408e44') and
      op(0x408E38,'and','byte ptr [rbx + 0x79], 0xfb') and op(0x408E41,'or','byte ptr [rbx + 0x79], al'),
      'native_01 plus sealed native_04; descriptor flags are a different byte')
check('Persistence value changes update table separately then refresh associated records',
      op(0x2FD712,'lea','rcx, [rbx + 0x1e8]') and op(0x2FD728,'mov','byte ptr [rax], dil') and
      op(0x2FD738,'call','0x140716e3c'),'Sealed native_09 exact map update')
check('Associated-record change handler replaces only mask04 under matching record lock',
      op(0x716F27,'cmp','qword ptr [rsi], r15') and op(0x716F2A,'je','0x140716f33') and
      op(0x716F45,'and','dl, 0xfb') and op(0x716F48,'shl','al, 2') and op(0x716F4B,'or','dl, al') and
      op(0x716F4D,'mov','byte ptr [rsi + 0x79], dl'),'native_01 full change handler')
check('Enable and disable share value-change helper, with native predicate gate for enable',
      ptr(0x36343D8+0x1F8,0xF78440) and ptr(0x36343D8+0x200,0x2FD61C) and
      op(0xF7845B,'call','qword ptr [rax + 0x1d8]') and op(0xF78470,'mov','r8b, 1') and
      op(0xF78478,'call','0x1402fd6bc') and op(0x2FD61C,'xor','r8d, r8d') and
      op(0x2FD61F,'jmp','0x1402fd6bc'),'Sealed native_08/09, no API call')
check('Current DynamicID predicate includes high-range membership lookup, not blanket allocator label',
      ptr(0x3213628+0x1D8,0x2FAB90) and op(0x2FABA7,'lea','eax, [rdx - 0x989680]') and
      op(0x2FABB1,'cmp','eax, 0x67697e') and op(0x2FABC9,'lea','rcx, [rbx + 0xf0]') and
      op(0x2FABD5,'call','0x1402fbf04') and op(0x2FABE8,'mov','al, 1'),
      'native_02/08 exact predicate; target membership/history not established')
check('Bounded refresh body writes eligibility mask04 and skips serialization when it is clear',
      op(0x2164CCC,'call','0x140408fac') and op(0x2164CDD,'and','byte ptr [rbx + 0x79], 0xfb') and
      op(0x2164CE1,'or','byte ptr [rbx + 0x79], al') and op(0x2164CE4,'test','byte ptr [rsp + 0x38], 4') and
      op(0x2164CE9,'je','0x142164cfd') and op(0x2164CF1,'call','0x1421650d0'),
      'native_08 explicit continuation span; dispatch not needed for projection argument')
check('Modern load rebuilds true-valued IDs after clearing registration table',
      op(0x59FECC,'lea','rdi, [r15 + 0x1e8]') and op(0x59FED6,'call','0x1401dea48') and
      op(0x59FF23,'call','0x142608060') and op(0x59FF2C,'mov','byte ptr [rax], 1'),
      'native_03 exact modern loader; first-list serializer selection previously sealed')
check('Admitted nonzero load installs buffer then sets mask04',
      op(0x5A0075,'call','0x1421658f0') and op(0x5A007D,'call','0x1405a02a4') and
      op(0x5A02A4,'or','byte ptr [rcx + 0x79], 4'),'native_03/04; subject to preceding class/body admission')
check('Zero-key load branch skips identity/class/body restoration',
      op(0x59FFC2,'mov','rbx, rax') and op(0x59FFC5,'test','rax, rax') and
      op(0x59FFC8,'je','0x1405a0232') and op(0x5A0232,'sub','r13, 1'),
      'native_03 exact row loop')
check('Writer mask04 clear always selects single zero output before inspecting mask01 or payload',
      op(0x2A35473,'test','al, 4') and op(0x2A35475,'je','0x142a355eb') and
      op(0x2A3547B,'test','al, 1') and op(0x2A355F2,'and','qword ptr [rbp + 0x60], 0') and
      op(0x2A355FD,'call','qword ptr [rax + 0x10]'),'Sealed native_03 writer; size8 output control')
check('False registration is omitted from first enabled-ID list',
      op(0x2A3533D,'cmp','byte ptr [rbx + 0xc], r12b') and op(0x2A3529A,'xor','r12d, r12d'),
      'Sealed native_03 writer; full first-list binding prior proof')
capture_review=HERE.parents[1]/'save_inventory/review_01/verification_01.json'
v=json.loads(capture_review.read_text())
check('Canonical historical miss remains the exact sealed capture03 result',
      sha(capture_review)=='8189EE560C66A690584EF72C13846C15006EADE7C2FE741772786D991B72791D' and
      v['check_count']==27 and v['four_candidate_matches']==[] and all(c['result']=='PASS' for c in v['checks']),
      'No save or metadata capture rerun; stage limits retained')
finding_data={'status':'PS2_PROJECTION_INFORMATION_LOSS_NO_SAFE_STAGE_DISCRIMINATOR',
    'ordinary_create':{'registration_rva':'0x2FAAEC','caller_rva':'0x2FAA48','argument3':0,'absent_row_value':False,
        'existing_rows':'Preserved','false_row_lookup_eligible':True,'false_row_saved_in_enabled_ids':False},
    'record_masks':{'01':'Generic serialized-buffer installed; empty installation also sets it; explicit clear removes it',
                    '02':'Inline/heap storage representation','04':'Save selection from eligibility/registration/load, independent of node payload'},
    'projection_counterexample':{'conditional':True,'record_key':'Canonical expected vehicle-data key',
        'history_A':'Node103 relevant setup pending; runtime payloadA','history_B':'Node103 relevant setup applied; different runtime payloadB',
        'shared_condition':'Record mask04 clear and false-valued registration','PS2_key_and_record_projection':'Single UInt64 zero in both; original key/body lost',
        'enabled_id_projection':'ID omitted in both','actual_fixture_history_asserted':False,'full_save_equivalence_asserted':False,
        'other_systems':'Graph/event/other saved state may differ and are not collapsed by this argument'},
    'reload':'Zero rows do not restore identity/data; admitted nonzero rows install data and set01/04 generically',
    'safe_skip_or_replay_guard_justified':False,'global_unsavable_claim':False,
    'original_save_reads':0,'parser_or_capture_invocations':0,'game_calls':0,'runtime_changes':0,'builds':0}
findings.write_text(json.dumps(finding_data,indent=2)+'\n',encoding='utf-8')
result={'status':finding_data['status'],'exe_sha256':im.sha,'checks':checks,'check_count':len(checks),
        'captured_decoded_byte_spans_verified':span_count,'unique_captured_decoded_starts':len(rows),'qwords_verified':qcount,
        'limits':'All captured bytes matched; semantic use is limited to identified bodies/explicit spans. Exploratory captures are not exhaustive lifecycle or executed-code coverage.',
        'original_save_reads':0,'parser_or_capture_invocations':0,'game_calls':0,'runtime_changes':0,'builds':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
sdk=WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext'
pins=[HERE.parent/'REPORT.md',HERE.parent/'verification_01.json',HERE.parent/'zero_entries_01/REPORT.md',
      capture_review,HERE.parents[1]/'entity_origin/evidence_01.json',HERE.parents[1]/'actor_assignment/evidence_01.json',
      sdk/'Scripting/Natives/gameIPersistencySystem.hpp',sdk/'Scripting/Natives/gamePersistentID.hpp',
      WORKSPACE/'research/framework_pr63_01/codeware/src/Red/PersistentObject.hpp']
source_pins=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [*source_files,*pins]]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(HERE.iterdir()) if p.is_file()]
manifest.write_text(json.dumps({'exe_sha256':im.sha,'source_pins':source_pins,'files':files,
                               'original_save_reads':0,'parser_or_capture_invocations':0,'game_calls':0,'runtime_changes':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','limits')},indent=2))
