"""Verify native serializer/registration contracts and retained child framing only."""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent;STAGE=HERE.parent;QR15=STAGE.parent;WORKSPACE=QR15.parents[1]
sys.path.insert(0,str(QR15/'saved_graph_state_01'))
from inspect_native import Image
OUT=HERE/'verification_01.json';SCHEMA=HERE/'schema_01.json';MANIFEST=HERE/'manifest_01.json'
assert all(not p.exists() for p in (OUT,SCHEMA,MANIFEST))
im=Image();rows={};decoded=0;qcount=0
old=[QR15/'saved_graph_state_01/native_01.json',QR15/'saved_graph_state_01/native_16.json',
     QR15/'saved_graph_state_01/inspector_review_01/native_04.json',QR15/'saved_graph_state_01/inspector_review_01/native_05.json']
captures=sorted(HERE.glob('native_*.json'))
for p in [*captures,*old]:
    j=json.loads(p.read_text());assert j['exe_sha256']==im.sha
    for f in j.get('functions',[])+j.get('explicit_spans',[]):
        for r in f.get('instructions',[]):
            a=int(r['rva'],16);b=bytes.fromhex(r['bytes']);assert im.data[im.off(a):im.off(a)+len(b)]==b
            rows[a]=r;decoded+=1
    for words in j.get('qwords',{}).values():
        for a,b in words:
            assert struct.unpack_from('<Q',im.data,im.off(int(a,16)))[0]==int(b,16);qcount+=1
def op(a,m,s):return rows[a]['mnemonic']==m and rows[a]['operands']==s
def ptr(a,b):return struct.unpack_from('<Q',im.data,im.off(a))[0]==im.base+b
def rip(a):
    b=bytes.fromhex(rows[a]['bytes']);return a+len(b)+struct.unpack('<i',b[-4:])[0]
def literal_from_lea(a):
    at=rip(a);return im.data[im.off(at):].split(b'\0',1)[0].decode('ascii')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks=[]
def check(name,condition,evidence):
    assert condition,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
check('Actual QuestsSystem save preparation/save/load slots',ptr(0x30BCE78+0x130,0x2C9F5A0) and
      ptr(0x30BCE78+0x138,0x2C9F364) and ptr(0x30BCE78+0x148,0x739578),'native_01 vtable; earlier RTTI binding reused')
check('Custom path registry header is one UInt16 in actual constructor',rip(0xB26642)==0x30BCE78 and
      op(0xB266AB,'mov','dword ptr [rbx + 0xc8], 1'),'native_23 exact constructor')
check('QuestContext20 binds actual QuestsSystemB8 registry',op(0x2B30D4,'lea','rbx, [rcx + 0xb8]') and
      op(0x2B310C,'mov','qword ptr [rsp + 0x38], rbx') and op(0x2B3195,'mov','qword ptr [rcx + 0x20], rax'),
      'native_12/10 exact caller/callee stack arguments')
check('Phase initialization interns full path length and data after missing-path lookup',
      op(0x2B2046,'mov','rbx, qword ptr [r14 + 0x20]') and op(0x2B2055,'call','0x1408f86a0') and
      op(0x2B205D,'jne','0x1402b20bf') and op(0x2B207E,'mov','word ptr [rax + rdi*2], si') and
      op(0x2B209C,'lea','rcx, [rax + rcx*2]') and op(0x2B20A0,'call','0x14196a250'),
      'Previously sealed phase initializer bytes; no active-tree inference')
check('CustomArray save is fixed U32 total-word count and raw UInt16 payload',
      op(0x2C9F3F9,'mov','eax, dword ptr [r14 + 0xc4]') and op(0x2C9F411,'call','qword ptr [rax + 0x10]') and
      op(0x2C9F41D,'mov','rdx, qword ptr [r14 + 0xb8]') and op(0x2C9F424,'lea','r8d, [rax + rax]'),
      'Outer native writer, header size4 and word size2')
check('CustomArray load restores words and marks index dirty',op(0x73A133,'mov','rcx, rsi') and
      op(0x73A136,'call','0x1404e83a4') and op(0x73A148,'lea','r8d, [rax + rax]') and
      op(0x73A150,'mov','byte ptr [rsi + 0x14], 1'),'native_02 loader')
check('Reload reindexes catalog records and rebuilds native path hashes',
      op(0xCC57FD,'call','0x1404e7ebc') and op(0x4E7F2D,'call','0x1404e8014') and
      op(0x4E7F3C,'call','0x1404e7d4c') and op(0x4E7F53,'call','0x1404e7dac'),
      'native_15/16 catalog rebuild')
check('Whole-system destruction frees catalog separately from phase cleanup',
      op(0xB265E4,'lea','rcx, [rbx + 0xb8]') and op(0xB265EB,'call','0x140b26390'),
      'native_22; ordinary Cut chain separately sealed, no universal never-reset claim')
check('EventManager object is stored at systemE8 with back-pointer28',
      rip(0x69758E)==0x306F9A0 and op(0x6975A8,'mov','qword ptr [rax + 0x28], rsi') and
      op(0x6975B3,'mov','qword ptr [rsi + 0xe8], rax'),'native_01 actual construction')
check('Context10 and handler factory refer to this EventManager endpoint',
      op(0x2B30E7,'mov','rax, qword ptr [rcx + 0xe8]') and op(0x2B311C,'mov','qword ptr [rsp + 0x28], rax') and
      ptr(0x3040630+0x50,0x351870) and op(0x351877,'mov','rax, qword ptr [rax + 0x10]'),
      'native_12/18/19 derived context50, not base interface')
check('Definition factory supplies handler and definition type CName to context registration',
      op(0x2B056C,'call','qword ptr [rax + 0x188]') and op(0x2B0580,'call','qword ptr [r8 + 0x180]') and
      op(0x2B0594,'mov','r8, qword ptr [rax]') and op(0x2B0597,'call','qword ptr [r10 + 0x60]') and
      op(0x35188B,'mov','rcx, qword ptr [rax + 0x18]'),'native_09/10 type/name metadata flow')
check('In-memory serialized node key is phaseHash32 then nodeID32',
      op(0x2B2237,'mov','dword ptr [r9 + 4], r8d') and op(0x2B223B,'mov','ecx, dword ptr [rax + 0x80]') and
      op(0x2B2244,'mov','dword ptr [r9], ecx'),'native_16 exact GetKey, distinct FactID codec')
check('EventManager inserts typeCName64 followed by key64 into a reused or appended slot',
      op(0xEB6B49,'mov','qword ptr [rsp + 0x20], rdx') and op(0xEB6B5D,'mov','rcx, qword ptr [r8]') and
      op(0xEB6B62,'mov','qword ptr [rsp + 0x28], rcx') and op(0xEB6B73,'movdqu','xmmword ptr [rcx + rdx*8], xmm0') and
      op(0xEB6B8F,'call','0x1401cc5ac'),'native_09 complete insertion')
check('Assigned saved slot index is retained in handler28 and phase handler map98',
      op(0x2B085E,'mov','dword ptr [rax + 0x28], edx') and op(0x2B0872,'lea','rcx, [rax + 0x98]') and
      op(0x2B08A4,'jmp','qword ptr [rax + 0x10]'),'Earlier source plus exact captured registration')
check('EventManager serialization preserves every high-water slot including blanks',
      op(0x2C9F441,'mov','rbx, qword ptr [r14 + 0xe8]') and op(0x2C9F468,'mov','eax, dword ptr [rbx + 0x14]') and
      op(0x2C9F489,'mov','rdx, qword ptr [rbx + 8]') and op(0x2C9F48D,'shl','r8d, 4'),
      'Outer writer native preserved bytes')
check('EventManager loader restores the same U32 count and16-byte row array',
      op(0x73A07F,'call','qword ptr [rax + 0x10]') and op(0x73A086,'lea','rcx, [rsi + 8]') and
      op(0x73A09A,'mov','rdx, qword ptr [rsi + 8]') and op(0x73A09E,'shl','r8d, 4'),'native_14 loader')
check('Context removal clears saved slot before uninitialize/map erase',
      op(0x2FCEE0,'mov','edx, dword ptr [rax + 0x28]') and op(0x2FCEE3,'mov','rcx, qword ptr [rcx + 0x10]') and
      op(0x2FCEE7,'call','0x1402fcfd0') and op(0x2FCF07,'jmp','0x1402fcf0c') and
      op(0x2FCF77,'call','qword ptr [rax + 0x20]'),'native_13 plus earlier exact inner removal')
check('Slot removal erases both identities and adds index to free list',
      op(0x2FCFE6,'and','qword ptr [rax], 0') and op(0x2FCFEA,'and','dword ptr [rax + 8], 0') and
      op(0x2FCFEE,'mov','dword ptr [rax + 0xc], 0xffff') and op(0x2FD002,'lea','rcx, [rbx + 0x18]') and
      op(0x2FD00B,'call','0x1401e07bc'),'native_14 exact free-slot writer')
check('Reload rebuilds free slots using phaseHash0 or nodeID32FFFF',
      op(0xCC5869,'cmp','dword ptr [rax], 0') and op(0xCC586E,'cmp','dword ptr [rax + 4], 0xffff') and
      op(0xCC58EB,'call','0x1401e07bc'),'native_16 actual free-list reconstruction')
check('Restore preparation skips blank keys and constructs full catalog path plus nodeID',
      op(0x2B2757,'test','ecx, ecx') and op(0x2B2766,'cmp','eax, 0xffff') and
      op(0x2B2778,'call','0x1402b1bc4') and op(0x2B27AB,'movzx','eax, word ptr [rbp - 0x3d]') and
      op(0x2B27BC,'call','0x1403bbeec'),'native_16 occupied-slot restore preparation')
check('Source-bound restoration callback dispatches paths in mode2',
      op(0x14D4624,'call','0x1414d4640') and rip(0x14D4661)==0x156EFD0 and
      op(0x156F001,'call','0x1402b32b0') and op(0x2B3328,'mov','r8b, 2') and
      op(0x2B3343,'call','0x1402b30a0') and op(0x2B3365,'call','qword ptr [rax + 0x130]'),
      'native_17/18/19/20 exact callback chain, no callback invoked')
check('Mode2 handler registration reuses a saved key slot',
      op(0x2B0835,'cmp','byte ptr [rdx + 1], 2') and op(0x2B084B,'call','0x14079cf00') and
      op(0x2B0852,'cmp','eax, -1'),'Captured exact registration; no completion label')
check('QueuedData writes VLQ/U64 request array followed by fixed U32/U32 notifications',
      op(0x2CA05DF,'mov','rcx, qword ptr [rax + 0x30]') and op(0x2CA060E,'call','0x14104170c') and
      op(0x2CA0621,'shl','r8d, 3') and op(0x2CA0642,'mov','eax, dword ptr [rsi + 0x164]') and
      op(0x2CA064F,'mov','r8d, 4') and op(0x2CA0673,'shl','r8d, 2'),'native_01 exact queue serializer')
check('Queued request keys are re-fed to actual resource-cache acquisition',
      op(0x7394AF,'call','qword ptr [rax + 0x1f0]') and ptr(0x30BCE78+0x1F0,0x2CA04E4) and
      op(0x2CA0513,'mov','rsi, qword ptr [rcx + 0x198]') and op(0x2CA0531,'mov','rdi, qword ptr [rax + 0x30]') and
      op(0x2CA053F,'mov','rdx, rbx') and op(0x2CA0545,'call','rdi'),'native_01/15 exact queue restoration')
check('Common handler notification routes assigned slot index into system158 queue',
      op(0x88BB80,'mov','rcx, qword ptr [rdx + 0x18]') and op(0x88BB84,'mov','edx, dword ptr [rdx + 0x28]') and
      ptr(0x306F9A0+8,0x88BC48) and op(0x88BC4F,'jmp','qword ptr [rax + 0x200]') and
      ptr(0x30BCE78+0x200,0x88BC58) and op(0x88BC75,'lea','rcx, [rbx + 0x158]'),
      'native_16/20 plus exact system queue function')
check('NodeInstanceDataManager framing is separately bound to F0 and count*16',
      op(0x2C9F49E,'mov','rcx, qword ptr [r14 + 0xf0]') and op(0x2C9F4A8,'call','0x142cd3208') and
      op(0x2CD324C,'mov','eax, dword ptr [rbx + 0x14]') and op(0x2CD326D,'shl','ebp, 4') and
      op(0x2CD32A2,'mov','rdx, qword ptr [rbx + 8]'),'native_01 exact F0 writer; internal field meanings remain opaque')
check('Debug and scene-helper owner labels are distinct and corrected',
      literal_from_lea(0x738A6C)=='questDebugLogManager' and literal_from_lea(0x739218)=='questSceneDataHelper' and
      op(0x2C9F4CF,'mov','rbx, qword ptr [r14 + 0x2c8]') and op(0x2C9F4FD,'call','0x14027cab4') and
      op(0x2C9F50B,'mov','rcx, qword ptr [r14 + 0x190]'),'native_24 names and outer serializer ownership')
check('Node103 event definition is bound through actual constructor to direct execute',
      ptr(0x32AED58+0xD8,0x352840) and op(0x352843,'jmp','0x140352770') and rip(0x3527CA)==0x3047DB8 and
      ptr(0x3047DB8+0x158,0x565B5C),'native_02/03/04/05/06 exact type chain')
check('Node103 execute emits Out and returns0 without a handler wait in this body',
      op(0x565C05,'call','0x1404f1d80') and op(0x565C13,'call','0x1405649f4') and
      op(0x565C1D,'xor','al, al') and op(0x565B8B,'je','0x140565c01'),
      'native_07 exact body; outer/listener state is not globally excluded')
components=STAGE/'components_01';m=json.loads((components/'manifest.json').read_text())
node_table={r['name']:r for r in m['nodes']};raw={}
for name,r in node_table.items():
    p=Path(r['path']);b=p.read_bytes();assert len(b)==r['size']==r['data_size'] and sha(p)==r['sha256']
    assert struct.unpack_from('<I',b)[0]==r['id'];raw[name]=b
check('Retained components have pinned IDs/bytes and completed source guard receipt',m['source_unchanged'] and
      m['source_sha256']=='AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E' and
      len(raw)==9 and m['save_writes']==m['game_calls']==0 and all(c['pass'] for c in m['checks']),
      'Coordinator component extraction receipt only; original source save never reopened')
def framed(name,stride):
    b=raw[name];n=struct.unpack_from('<I',b,4)[0];assert len(b)==8+n*stride
    return n,b[8:]
n,body=framed('customArray',2);words=struct.unpack('<'+'H'*n,body);paths=[];at=0
while at<len(words):
    count=words[at];at+=1;assert 0<count<=1024 and at+count<=len(words)
    paths.append(tuple(words[at:at+count]));at+=count
event_count,eb=framed('eventManager',16);events=[struct.unpack_from('<QII',eb,i*16) for i in range(event_count)]
instance_count,_=framed('nodeInstanceDataManager',16)
check('Raw current child framing fully consumes native-confirmed arrays',n==112318 and len(paths)==13112 and
      event_count==8924 and instance_count==8,'Bounded retained-byte unpack only, not a save parser')
check('All event nodeID32 high halves are0 and blank rows match native erased pattern',
      all(node<=0xFFFF for _,phase,node in events) and sum(r==(0,0,0xFFFF) for r in events)==5148,
      'Actual struct QII, not a separately meaningful tail flag')
q=raw['QueuedData'];check('Both retained QueuedData counts are exactly empty',len(q)==9 and q[4]==0 and
      struct.unpack_from('<I',q,5)[0]==0,'Only this observed empty signed-VLQ case decoded here')
analysis=json.loads((STAGE/'analysis_01.json').read_text());anc=json.loads((STAGE/'ancestor_membership_01.json').read_text())
prefix=(1,0,10,5,2,50,19);selected=[p for p in paths if p[:len(prefix)]==prefix]
check('Retained Jason catalog has exact five source-bound paths',set(selected)=={prefix,prefix+(5,),prefix+(5,1),prefix+(6,),prefix+(6,2)} and
      len(selected)==5,'Catalog interning observation only')
check('Parent phase-hash and exact owner-address queries agree with raw slots',
      len(analysis['target_contexts'])==5 and all(not x['event_manager_phase_rows'] and not x['registered_path_hash_collisions'] for x in analysis['target_contexts']) and
      all(not [r for r in events if r[1]==int(x['phase_hash_u32'])] for x in analysis['target_contexts']) and
      len(anc['route'])==8 and len(anc['route'][0]['serialized_handler_rows'])==1 and
      all(not x['serialized_handler_rows'] for x in anc['route'][1:]) and
      all([r for r in events if r[1]==int(x['phase_hash_u32']) and r[2]==x['phase_node']]==
          [(int(r['type_token_u64']),int(r['phase_hash_u32']),r['node_u16']) for r in x['serialized_handler_rows']] for x in anc['route']),
      'No new root guessing; parent source ancestry binding and raw integer membership')
check('All nine child sizes are retained without excluding opaque components',sum(len(v) for v in raw.values())==374629 and
      len(raw['nodeInstanceDataManager'])==136 and len(raw['questPhaseFreezer'])==1104 and len(raw['questSceneDataHelper'])==328,
      'No complete-event-stage-absence conclusion is made')
schema={'exe_sha256':im.sha,'source_body_sha256':m['source_sha256'],
 'customArray':{'parent_field':'QuestsSystem+B8','format':'U32 total words; repeated U16 length + U16 path[length]','header_words':1,
                'producer':'PhaseInstance.Initialize2B2046..20BA','meaning':'Interned initialized-phase paths; not active-owner/completion list','retention':'Exact Cut removal does not erase catalog; whole-owner destruction separate'},
 'eventManager':{'parent_field':'QuestsSystem+E8','format':'U32 high-water slot count; count*{U64 definitionTypeCName,U32 phaseHash,U32 nodeID}',
                 'clear':'2FCEAC->2FCFD0 writes0,0,FFFF and queues free index before handler uninit/erase','restore':'73A024 raw read;CC5844 free-list rebuild;2B26A4 full paths;2B32B0 mode2 dispatch',
                 'meaning':'Saved/restorable handler registrations; no completed/cancelled history retained by clear'},
 'QueuedData':{'format':'signedVLQ resource-request count + U64 keys; U32 handler-notification count + U32 slot indices',
               'observed_case':'Both counts0, exact9-byte child including NodeID','not_kind':'Persistency/actor event queue or acknowledgement log'},
 'opaque_for_stage':['nodeInstanceDataManager key/data semantics and lifecycle','questPrefabsHandler saved data as event receipt','questPhaseFreezer','questSceneDataHelper','playerObjectListenerMapper','debug-log completeness'],
 'node103':'Exact direct execute565B5C attempts dispatch, emits Out, returns0; no actor-application receipt from this handler projection',
 'scope':'No current-session binding, full-save equivalence, complete event-state absence, replay/skip authorization or universal owner proof',
 'original_save_reads':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0}
SCHEMA.write_text(json.dumps(schema,indent=2)+'\n',encoding='utf-8')
result={'status':'EXACT_HANDLER_REGISTRY_AND_QUEUE_SCHEMA_NO_STARTUP_COMPLETION_RECEIPT','exe_sha256':im.sha,
        'checks':checks,'check_count':len(checks),'captured_decoded_byte_spans_verified':decoded,'unique_captured_decoded_starts':len(rows),'qwords_verified':qcount,
        'retained_raw_bytes_read':sum(len(v) for v in raw.values()),'original_save_reads':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0,'builds':0}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
sources=[*old,QR15/'saved_graph_state_01/inspector_review_01/REPORT.md',QR15/'lifecycle_01/prefab_native/REPORT.md',
         STAGE/'analysis_01.json',STAGE/'analyze_components.py',STAGE/'ancestor_membership_01.json',STAGE/'analyze_ancestors.py',
         components/'manifest.json',*[Path(r['path']) for r in m['nodes']],
         WORKSPACE/'research/framework_pr63_01/codeware/src/Red/QuestsSystem.hpp',
         WORKSPACE/'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseExecutor.hpp']
pins=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sources]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(HERE.iterdir()) if p.is_file()]
MANIFEST.write_text(json.dumps({'exe_sha256':im.sha,'source_pins':pins,'files':files,'original_save_reads':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
