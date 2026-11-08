"""Verify the native zero-row branches and managed identity-preserving parser contract."""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from inspect_pid import Image,WORKSPACE
out=HERE/'verification_01.json';manifest=HERE/'manifest_01.json'
assert not out.exists() and not manifest.exists()
im=Image();rows={};count=0
selection=[(HERE.parent/'native_03.json',{0x2A35150}),(HERE.parent/'native_06.json',{0x408C58}),
           (HERE/'native_zero_01.json',{0x1820E8C})]
for p,wanted in selection:
    evidence=json.loads(p.read_text());assert evidence['exe_sha256']==im.sha
    for f in evidence['functions']:
        if int(f['begin_rva'],16) not in wanted:continue
        for r in f['instructions']:
            a=int(r['rva'],16);b=bytes.fromhex(r['bytes'])
            assert im.data[im.off(a):im.off(a)+len(b)]==b
            rows[a]=r;count+=1
def op(a,m,s):return rows[a]['mnemonic']==m and rows[a]['operands']==s
checks=[]
def check(name,value,evidence):
    assert value,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
check('Snapshot helper locks table, iterates keys and releases before returning',
      op(0x1820EA0,'lea','rsi, [rcx + 0x20]') and op(0x1820EAE,'call','0x1422ca300') and
      op(0x1820EF4,'add','rdx, 8') and op(0x1820EFB,'call','0x14019b75c') and
      op(0x1820F0C,'xchg','byte ptr [rsi], bl'),'native_zero_01 complete helper; prior key/table binding')
check('Record count is snapshot count written before row filtering',
      op(0x2A353DC,'lea','r13, [rdi + 0x48]') and op(0x2A353E8,'call','0x141820e8c') and
      op(0x2A353ED,'mov','edx, dword ptr [rsp + 0x4c]') and op(0x2A353F4,'call','0x142a35018'),
      'native_03 full writer')
check('Output zero register is initialized before the row loop',op(0x2A3529A,'xor','r12d, r12d') and
      op(0x2A353FD,'mov','r15d, 8'),'native_03 full writer')
check('Zero snapshot key branches directly to the first zero writer',
      op(0x2A35419,'mov','rsi, qword ptr [rbx]') and op(0x2A3541C,'test','rsi, rsi') and
      op(0x2A3541F,'je','0x142a35453'),'native_03')
check('Missing record branches directly to the first zero writer',
      op(0x2A35427,'call','0x140408c58') and op(0x2A3542F,'test','rax, rax') and
      op(0x2A35432,'je','0x142a35453') and op(0x408C9A,'xor','eax, eax'),
      'native_03 plus exact record lookup native_06')
check('Record is locked and exact key checked before selection flags',
      op(0x2A35434,'lea','r12, [rax + 0x78]') and op(0x2A3543B,'call','0x1422ca300') and
      op(0x2A35440,'mov','rcx, qword ptr [rdi]') and op(0x2A35443,'cmp','rcx, rsi') and
      op(0x2A35446,'je','0x142a35470'),'native_03')
check('Mismatched key unlocks and clears zero register before zero row',
      op(0x2A3544B,'call','0x141ffad80') and op(0x2A35450,'xor','r12d, r12d'),
      'native_03 fall-through into2A35453')
check('Either missing mask04 or missing mask01 branches to filtered zero writer',
      op(0x2A35470,'mov','al, byte ptr [rdi + 0x79]') and op(0x2A35473,'test','al, 4') and
      op(0x2A35475,'je','0x142a355eb') and op(0x2A3547B,'test','al, 1') and
      op(0x2A3547D,'je','0x142a355eb'),'native_03 exact branch polarity')
check('First zero path writes only UInt64 zero then advances one key',
      op(0x2A3545A,'mov','r8, r15') and op(0x2A3545D,'mov','qword ptr [rbp + 0x60], r12') and
      op(0x2A35464,'call','qword ptr [rax + 0x10]') and op(0x2A3546B,'add','rbx, r15') and
      op(0x2A3546E,'jmp','0x142a35410'),'native_03; r15=8')
check('Filtered path explicitly writes UInt64 zero and unlocks without a body',
      op(0x2A355F2,'and','qword ptr [rbp + 0x60], 0') and op(0x2A355F7,'mov','r8, r15') and
      op(0x2A355FD,'call','qword ptr [rax + 0x10]') and op(0x2A35600,'jmp','0x142a355db') and
      op(0x2A355DE,'call','0x141ffad80') and op(0x2A355E3,'xor','r12d, r12d') and
      op(0x2A355E6,'jmp','0x142a35467'),'native_03; original key not written in filtered branch')
check('Selected row writes key then distinct class hash and body size',
      op(0x2A3548A,'mov','qword ptr [rbp + 0x60], rcx') and op(0x2A35494,'call','qword ptr [rax + 0x10]') and
      op(0x2A35497,'mov','rax, qword ptr [rdi + 0x18]') and op(0x2A354AC,'call','qword ptr [rax + 0x10]') and
      op(0x2A3552B,'call','0x142a35018'),'native_03; key and class size8 previously bound')
managed=json.loads((HERE/'parser_il_02.json').read_text())
dll=Path(managed['assembly']);dll_bytes=dll.read_bytes();dll_hash=hashlib.sha256(dll_bytes).hexdigest().upper()
check('Exact managed reader matches completed capture02 pin',dll_hash==managed['assembly_sha256']==
      'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987','Managed DLL file bytes only')
methods=managed['methods']
for method in methods:
    raw=bytes.fromhex(method['il_hex']);assert raw in dll_bytes
    assert len(raw)==method['decoded_bytes'] and method['instructions'][-1]['offset']<len(raw)
parser=next(m for m in methods if m['type']=='WolvenKit.RED4.Save.PersistencySystem2Parser' and m['method'].startswith('Void Read('))
il={r['offset']:r for r in parser['instructions']};raw=bytes.fromhex(parser['il_hex'])
def ilop(a,opcode,operand,member=None):
    r=il[a];return r['opcode']==opcode and r['operand']==operand and (member is None or r['member_type']==member)
check('Parser creates one fresh entry per iteration and reads UInt64 Id first',
      ilop(69,'newobj','Void .ctor()','WolvenKit.RED4.Save.PS2Entry') and
      ilop(79,'callvirt','UInt64 ReadUInt64()','System.IO.BinaryReader') and
      ilop(84,'callvirt','Void set_Id(UInt64)','WolvenKit.RED4.Save.PS2Entry'),'parser_il_02 Read')
check('Id0 branch directly reaches list addition before any class or body read',
      ilop(96,'brfalse',315) and raw[96]==0x39 and 101+struct.unpack_from('<i',raw,97)[0]==315 and
      ilop(102,'callvirt','UInt64 ReadUInt64()') and ilop(110,'callvirt','UInt32 ReadUInt32()') and
      ilop(323,'callvirt','Void Add(WolvenKit.RED4.Save.PS2Entry)'),
      'parser_il_02 Read; independent encoded branch target control')
entry_methods={m['method']:m for m in methods if m['type']=='WolvenKit.RED4.Save.PS2Entry'}
check('Entry constructor has no Data initialization and Id/Data accessors are plain backing fields',
      [r['opcode'] for r in entry_methods['Void .ctor()']['instructions']]==['ldarg.0','call','ret'] and
      entry_methods['Void .ctor()']['instructions'][1]['member_type']=='System.Object' and
      entry_methods['Void set_Id(UInt64)']['instructions'][2]['operand']=='UInt64 <Id>k__BackingField' and
      entry_methods['WolvenKit.RED4.Types.RedBaseClass get_Data()']['instructions'][1]['operand']=='WolvenKit.RED4.Types.RedBaseClass <Data>k__BackingField',
      'parser_il_02 PS2Entry metadata/IL and CLR reference default')
factory=next(m for m in methods if m['type']=='WolvenKit.RED4.Types.RedTypeManager')
check('Known class factory cannot successfully return null',
      [(r['offset'],r['opcode']) for r in factory['instructions']]==[(0,'ldarg.0'),(1,'call'),(6,'isinst'),(11,'dup'),(12,'brtrue.s'),(14,'newobj'),(19,'throw'),(20,'ret')] and
      factory['instructions'][4]['operand']==20,'parser_il_02 Create(Type), null path throws')
check('Known class branch assigns factory object then adds entry and skips fallback addition',
      ilop(158,'call','WolvenKit.RED4.Types.RedBaseClass Create(System.Type)','WolvenKit.RED4.Types.RedTypeManager') and
      ilop(236,'callvirt','Void set_Data(WolvenKit.RED4.Types.RedBaseClass)') and
      ilop(249,'callvirt','Void Add(WolvenKit.RED4.Save.PS2Entry)') and ilop(254,'leave.s',328),
      'parser_il_02 Read')
check('Unknown class and caught decode error select a nonnull UnknownRedClass fallback',
      ilop(154,'brfalse.s',259) and ilop(257,'leave.s',259) and
      ilop(272,'newobj','Void .ctor()','WolvenKit.RED4.Save.UnknownRedClass') and
      ilop(280,'callvirt','Void set_Hash(UInt64)') and ilop(310,'callvirt','Void set_Data(WolvenKit.RED4.Types.RedBaseClass)') and
      any(c['handler_offset']==256 and c['flags']=='Clause' for c in parser['exception_clauses']),
      'parser_il_02 exact fallback and exception table')
check('Nonzero Id is not rewritten after reading, including fallback',
      [r['offset'] for r in parser['instructions'] if r['operand']=='Void set_Id(UInt64)']==[84],
      'parser_il_02 all Read instructions')
check('Parser loop preserves every declared row without deduplication',
      ilop(55,'callvirt','Int32 ReadInt32()') and ilop(337,'blt',69) and
      [r['offset'] for r in parser['instructions'] if r['operand']=='Void Add(WolvenKit.RED4.Save.PS2Entry)']==[249,323] and
      ilop(254,'leave.s',328),'parser_il_02 exact loop and exclusive Add paths')
capture=HERE.parents[1]/'save_inventory/capture_02'
meta_path=capture/'manifest.json';meta_bytes=meta_path.read_bytes();meta=json.loads(meta_bytes)
ids_path=capture/'ps2_ids.json';ids_bytes=ids_path.read_bytes();ids=json.loads(ids_bytes)
check('Completed capture02 pins exact source and reader with no candidate matches',
      meta['status']=='READ_ONLY_IDENTITY_METADATA' and meta['source_unchanged'] and meta['save_writes']==meta['game_calls']==0 and
      meta['reader_sha256']==dll_hash and meta['source_sha256']=='AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E' and
      meta['candidate_matches']==[],'Coordinator completed capture02 manifest only; no source save read')
nulls=meta['class_counts']['NULL'];dupes=meta['ps2_entry_duplicate_keys']
check('Null/zero aggregate explains all duplicates under exact parser contract',
      nulls==27923 and dupes==nulls-1 and meta['ps2_entry_count']==116594 and
      sum(meta['class_counts'].values())==116594,
      'Source-derived null iff zero in successful parse; remaining nonzero keys unique')
check('Low24 aggregate includes all zero placeholders',meta['ps2_entry_low24_keys']==29725 and
      meta['ps2_entry_low24_keys']-nulls==1802,'Aggregate only, no actor/class assignment')
check('Enabled dynamic list independently excludes target',len(ids['ids_u64'])==meta['ps2_header_ids_count']==2165 and
      '10229047' not in ids['ids_u64'] and not meta['ps2_header_ids_contain_raw_target'],
      'Completed capture02 first list metadata')
check('Vehicle-data class is outside explicitly retained old wrapper filter',
      meta['class_counts']['vehiclePersistentDataPS']==200 and meta['class_counts']['VehicleComponentPS']==382 and
      meta['class_counts']['vehicleControllerPS']==384 and meta['vehicle_metadata_rows']==766,
      'Capture02 manifest counts and capture_02.ps1 explicit regex; no body defaults')
script=HERE.parents[1]/'save_inventory/capture_02.ps1';text=script.read_text()
check('Capture02 checked only the three stated candidates, not later native-bound vehicle-data key',
      "$candidateKeys=@('10229047','6695448052237678836','15311582179580628726')" in text and
      '17113219195054135786' not in text and "$class -match 'VehicleComponentPS$|vehicleControllerPS$'" in text,
      'Capture02 extraction code read only, never rerun')
assert meta_path.read_bytes()==meta_bytes and ids_path.read_bytes()==ids_bytes
result={'status':'ZERO_PLACEHOLDER_AND_NONZERO_KEY_MEMBERSHIP_LIMITS_SOURCE_CONFIRMED',
        'exe_sha256':im.sha,'reader_sha256':dll_hash,'checks':checks,'check_count':len(checks),
        'verified_native_instruction_spans':count,'unique_native_instruction_starts':len(rows),
        'managed_methods_captured':len(methods),'managed_method_bodies_located_in_pinned_dll':len(methods),
        'capture02_null_and_zero_rows':nulls,'capture02_duplicates_explained_by_zero':dupes,
        'capture02_nonzero_low24_keys':1802,'save_reads':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0,'builds':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
sources=[p for p,_ in selection[:2]]+[HERE.parent/'REPORT.md',HERE.parent/'manifest_01.json',
         dll,script,*sorted(capture.glob('*.json')),HERE.parents[1]/'vehicle_data_native/REPORT.md']
pins=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sources]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
       for p in sorted(HERE.iterdir()) if p.is_file()]
manifest.write_text(json.dumps({'exe_sha256':im.sha,'reader_sha256':dll_hash,'source_pins':pins,'files':files,
                               'save_reads':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
