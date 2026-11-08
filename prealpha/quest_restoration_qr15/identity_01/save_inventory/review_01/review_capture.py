"""Review retained capture03 metadata only; never reopen or parse an original save."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
IDENTITY=HERE.parents[1]
sys.path.insert(0,str(IDENTITY/'native_pid'))
from inspect_pid import Image,WORKSPACE
OUT=HERE/'verification_01.json';LOOKUPS=HERE/'key_lookups_01.json';MANIFEST=HERE/'manifest_01.json'
assert all(not p.exists() for p in (OUT,LOOKUPS,MANIFEST))
capture=HERE.parent/'capture_03';prior=HERE.parent/'capture_02'
paths=[HERE.parent/'capture_03.ps1',*sorted(capture.glob('*.json')),HERE/'capture_ast_01.json',
       IDENTITY/'vehicle_data_native/evidence_01.json',IDENTITY/'vehicle_data_native/verification_01.json',
       IDENTITY/'native_pid/verification_01.json',IDENTITY/'native_pid/zero_entries_01/verification_01.json',
       IDENTITY.parent/'lifecycle_01/save_community/capture_01/capture.json']
snapshots={p:p.read_bytes() for p in paths}
def load(p):return json.loads(snapshots[p] if p in snapshots else p.read_bytes())
def sha(data):return hashlib.sha256(data).hexdigest().upper()
meta=load(capture/'manifest.json');ids=load(capture/'ps2_ids.json');vehicles=load(capture/'vehicle_ps_metadata.json')
dynamic=load(capture/'dynamic_ids.json');ast=load(HERE/'capture_ast_01.json')
source=snapshots[HERE.parent/'capture_03.ps1'].decode('utf-8-sig')
checks=[]
def check(name,condition,evidence):
    assert condition,name
    checks.append({'name':name,'result':'PASS','evidence':evidence})
check('Capture03 parses as PowerShell source without invocation',ast['parse_errors']==0 and ast['capture_invocations']==ast['save_reads']==0,'Static AST capture only')
check('All four exact candidates are in the source query',ast['candidate_keys']==[
      '10229047','6695448052237678836','15311582179580628726','17113219195054135786'],
      'capture_ast_01 candidate assignment')
check('Global membership query is outside the vehicle-class filter',ast['candidate_if_direct_child_of_full_entry_loop'] and
      ast['entry_loop']=='$ps.Entries' and ast['candidate_condition']=='$row.id_u64 -in $candidateKeys' and
      ast['candidate_body']=='{$candidateMatches.Add($row)}','Direct AST parent is the complete entry loop body')
check('Candidate list avoids the automatic Matches variable collision',ast['candidate_list_constructor']=='[Collections.Generic.List[object]]::new()' and
      ast['automatic_matches_variable_references']==0,'PowerShell names are case insensitive; candidateMatches is distinct from Matches')
check('Metadata query source uses raw decimal entry.Id before filtering',
      '$row=@{id_u64=$entry.Id.ToString();parsed_class=$class}' in source and
      source.index('$row=@{id_u64=')<source.index("$class -match 'VehicleComponentPS$|vehicleControllerPS$|vehiclePersistentDataPS$'"),
      'capture_03.ps1 plain Id getter -> ToString; parser field identity already source-bound')
check('Snapshot source guards cover pre-read, captured bytes and post-read',len(ast['recorded_source_hash_guards'])==3 and
      'Historical body changed' in ast['recorded_source_hash_guards'][0] and
      'HashData($bytes)' in ast['recorded_source_hash_guards'][1] and
      'Input changed during capture' in ast['recorded_source_hash_guards'][2],
      'Static source guards, not a new source-save hash read')
check('Successful manifest output follows post-read guard',
      source.index("throw 'Input changed during capture'")<source.index('New-Item -ItemType Directory -Path $output')<source.index("status='READ_ONLY_IDENTITY_METADATA'"),
      'Captured success fields occur after all hash guards')
origin=load(IDENTITY.parent/'lifecycle_01/save_community/capture_01/capture.json')
expected_source='AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E'
expected_metadata='BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E'
expected_reader='EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987'
check('Capture03 records the same pinned historical source and metadata',meta['source_sha256']==origin['source_sha256']==expected_source and
      meta['metadata_sha256']==origin['metadata_sha256']==expected_metadata and meta['source']==origin['source'] and meta['source_unchanged'],
      'Retained manifests and three source-code hash guards; original save not reopened')
dll=WORKSPACE/'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/WolvenKit.RED4.dll'
check('Captured reader hash matches exact current local parser artifact',meta['reader_sha256']==sha(dll.read_bytes())==expected_reader,'Managed DLL file bytes only')
pid_verify=load(IDENTITY/'native_pid/verification_01.json')
zero_verify=load(IDENTITY/'native_pid/zero_entries_01/verification_01.json')
check('Sealed native PID and PS2 key contract remains unchanged',sha(snapshots[IDENTITY/'native_pid/verification_01.json'])==
      'AD7783C30200663AE8B896F9E9EABA8A884732FEA501CC318A59413688DD89AA' and
      pid_verify['check_count']==32 and all(c['result']=='PASS' for c in pid_verify['checks']),
      'Native hash409010 -> system+48 record key0 -> saved entry.Id; class follows separately')
check('Sealed zero/filter and key-preserving parser contract remains unchanged',sha(snapshots[IDENTITY/'native_pid/zero_entries_01/verification_01.json'])==
      'A4852BFC52FCF49C944489ED2A08197A2B09BEBC462F85D54840EDC459D1FFE0' and
      zero_verify['check_count']==26 and all(c['result']=='PASS' for c in zero_verify['checks']),
      'Present records can save zero; nonzero Id survives body fallback; null Data iff zero in successful parse')
im=Image();peer=load(IDENTITY/'vehicle_data_native/evidence_01.json');peer_checks=load(IDENTITY/'vehicle_data_native/verification_01.json')
check('Peer vehicle-data key proof is exact and all14 controls pass',sha(snapshots[IDENTITY/'vehicle_data_native/evidence_01.json'])==
      '9ED5801CD1DDD4BDCBD650FEBBF977AC212FBCABB3FA100D8C14F68DAB43EBDD' and peer_checks['evidence_sha256']==
      '9ED5801CD1DDD4BDCBD650FEBBF977AC212FBCABB3FA100D8C14F68DAB43EBDD' and peer['exe_sha256']==im.sha and
      len(peer_checks['checks'])==14 and all(c['pass'] for c in peer_checks['checks']),'Separate sealed source-bound factory/owner evidence')
native_rows={};native_count=0
for name in ('vehicle_base_initialize','vehicle_data_class_name','vehicle_data_lookup'):
    for r in peer['functions'][name]['instructions']:
        a=int(r['rva'],16);b=bytes.fromhex(r['bytes']);assert im.data[im.off(a):im.off(a)+len(b)]==b
        native_rows[a]=r;native_count+=1
def op(a,m,s):return native_rows[a]['mnemonic']==m and native_rows[a]['operands']==s
check('Native initializer constructs entity0 and exact component8 before lookup',
      op(0x593215,'call','0x1409a2498') and op(0x59321A,'mov','rdx, qword ptr [rsi + 0x48]') and
      op(0x593225,'mov','qword ptr [rbp - 0x48], rcx') and op(0x59322C,'mov','qword ptr [rbp - 0x50], rdx') and
      op(0x593234,'call','0x1409a2514'),'Independent exact native byte readback; PID16 passed at rbp-50')
check('Native CName literal is exact and class is a separate lookup argument',
      op(0x9A24AC,'movabs','rdi, 0xf8b5d41e08e5736f') and
      op(0x9A252E,'mov','r9, qword ptr [rip + 0x3225c2b]') and op(0x9A254B,'call','qword ptr [rax + 0x1b0]'),
      'Independent byte readback of name helper and lookup argument construction')
MASK=(1<<64)-1;M=0xC6A4A7935BD1E995
def cname(name):
    h=0xCBF29CE484222325
    for b in name.encode('utf-8'):h=((h^b)*0x100000001B3)&MASK
    return 0 if name in ('','None') else h
def pid(e,c):
    if c==0:return e
    t=(M*c)&MASK;t=(M*(t^(t>>47)))&MASK
    return (M*(e^t))&MASK
def inverse_pid(k,c):
    if c==0:return k
    t=(M*c)&MASK;t=(M*(t^(t>>47)))&MASK
    return ((k*pow(M,-1,1<<64))&MASK)^t
inputs=[('raw EntityID probe',0,10229047),('controller',cname('controller'),6695448052237678836),
        ('VehicleController',cname('VehicleController'),15311582179580628726),
        ('vehiclePersistentDataPS',cname('vehiclePersistentDataPS'),17113219195054135786)]
check('CName hashes reproduce prior probes and exact native vehicle-data literal',cname('controller')==0x18B8DE5B56F6D021 and
      cname('VehicleController')==0x149307BBD7B0A813 and cname('vehiclePersistentDataPS')==0xF8B5D41E08E5736F,
      'Independent Python FNV1a64; exact spelling/case; SDK CName.hpp')
check('All four candidate key values reproduce and invert to10229047',all(pid(10229047,c)==k and inverse_pid(k,c)==10229047 for _,c,k in inputs),
      'Wrapping UInt64 native/SDK formula; raw probe has no inferred component owner')
rows=vehicles['entries'];counts=Counter(r['parsed_class'] for r in rows);row_ids=[int(r['id_u64']) for r in rows]
check('Retained rows exactly cover the three selected class counts',len(rows)==meta['vehicle_metadata_rows']==966 and
      counts=={'VehicleComponentPS':382,'vehicleControllerPS':384,'vehiclePersistentDataPS':200} and
      all(meta['class_counts'][k]==v for k,v in counts.items()),'capture03 vehicle metadata and complete manifest aggregates')
check('All retained IDs are unique canonical nonzero UInt64 decimal strings',len(set(row_ids))==966 and
      all(0<e<=MASK and str(e)==r['id_u64'] for e,r in zip(row_ids,rows)),
      'No float conversion, signed truncation, default ID or duplicate in retained selected rows')
vehicle_data_rows=[r for r in rows if r['parsed_class']=='vehiclePersistentDataPS']
check('All200 vehicle-data rows retain parseable payloads and pre-export property-name inventories',
      len(vehicle_data_rows)==200 and all(json.loads(r['native_parsed_data_json'])['$type']=='vehiclePersistentDataPS' and
      isinstance(r['property_names_before_native_export'],list) for r in vehicle_data_rows),
      'Payload container completeness only; no property values/defaults or serialized presence certified')
lookups=[]
for name,c,k in inputs:
    hits=[{'id_u64':r['id_u64'],'parsed_class':r['parsed_class']} for r in rows if int(r['id_u64'])==k]
    lookups.append({'input':name,'entity_candidate_u64':'10229047','component_cname_u64':str(c),
                    'key_u64':str(k),'key_hex':f'0x{k:016X}','inverse_control_entity_u64':str(inverse_pid(k,c)),
                    'retained_966_row_hits':hits,'recorded_global_candidate_hits':meta['candidate_matches']})
check('All four candidates independently miss the retained966 row IDs',all(not r['retained_966_row_hits'] for r in lookups),
      'Python exact integer membership over retained rows; covers all200 vehicle-data rows')
check('Recorded global scan has no candidate match across full116594 entries',meta['candidate_matches']==[] and
      meta['ps2_entry_count']==116594 and sum(meta['class_counts'].values())==116594,
      'Completed coordinator manifest plus reviewed unconditional full-entry query; global IDs not all retained')
check('Zero-placeholder and duplicate aggregates agree with sealed native/parser contract',meta['class_counts']['NULL']==27923 and
      meta['ps2_entry_duplicate_keys']==27922 and meta['ps2_entry_low24_keys']==29725,
      '27,923 anonymous zero rows; all duplicate count explained by zero;1,802 remaining low24 nonzero keys')
check('First Ids list is UInt32 metadata and excludes target',len(ids['ids_u64'])==meta['ps2_header_ids_count']==2165 and
      not meta['ps2_header_ids_contain_raw_target'] and '10229047' not in ids['ids_u64'] and
      all(str(int(v))==v and 0<=int(v)<=0xFFFFFFFF for v in ids['ids_u64']),
      'Separate dynamic-ID enabled subset, not component PersistentID key census')
old=load(prior/'manifest.json');oldrows=load(prior/'vehicle_ps_metadata.json')['entries']
check('Unchanged aggregates and prior766 wrapper IDs/classes agree with capture02',meta['class_counts']==old['class_counts'] and
      [(r['id_u64'],r['parsed_class']) for r in oldrows]==[(r['id_u64'],r['parsed_class']) for r in rows if r['parsed_class']!='vehiclePersistentDataPS'],
      'Retained metadata comparison only; capture02 not rerun')
check('Dynamic metadata and first Ids sequence are unchanged from capture02',dynamic==load(prior/'dynamic_ids.json') and
      ids==load(prior/'ps2_ids.json'),'No runtime status meaning assigned to dynamic maps')
check('Capture03 records no save writes or game calls',meta['save_writes']==meta['game_calls']==0 and
      meta['status']=='READ_ONLY_IDENTITY_METADATA','Capture receipt only; review itself also performs none')
check('AST source pin matches exact reviewed capture03 script',ast['source_sha256']==sha(snapshots[HERE.parent/'capture_03.ps1']),
      'No original script invocation')
for p,b in snapshots.items():assert p.read_bytes()==b
LOOKUPS.write_text(json.dumps({'exe_sha256':im.sha,'magic':hex(M),'lookups':lookups,
    'scope':'Three component inputs for this candidate only; vehiclePersistentDataPS is source-bound in inspected factory routes. Raw and prior component probes are not additional owner proof.',
    'global_membership_evidence':'Coordinator candidate_matches over all entries; independent retained-subset checks recorded separately',
    'save_reads':0,'parser_invocations':0,'game_calls':0},indent=2)+'\n',encoding='utf-8')
result={'status':'CAPTURE03_FOUR_KEY_MEMBERSHIP_REVIEW_PASS_WITH_ZERO_FILTER_AND_STAGE_LIMITS',
        'checks':checks,'check_count':len(checks),'independently_verified_native_instruction_spans':native_count,
        'capture03_source_sha256':expected_source,'capture03_reader_sha256':expected_reader,
        'recorded_total_rows':116594,'retained_selected_rows':966,'retained_native_vehicle_data_rows':200,
        'recorded_zero_rows_source_derived':27923,'four_candidate_matches':[],
        'documentation_note':'capture03 limits prose still says raw and two component-hash candidates; actual source query contains raw plus three component keys.',
        'limitations':['Global full-entry membership relies on completed coordinator extraction receipt and reviewed source; only966 retained selected IDs independently searched here.',
                       'Missing nonzero serialized key does not distinguish no record from a native-filtered zero placeholder.',
                       'Vehicle-data payload defaults, exact live actor/body identity, stage/cleanup/queued-event completion and safe replay remain unproved.'],
        'original_save_reads':0,'parser_invocations':0,'capture_invocations':0,'game_calls':0,'runtime_changes':0,'builds':0}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
sources=[*paths,*sorted(prior.glob('*.json')),IDENTITY/'native_pid/REPORT.md',IDENTITY/'native_pid/zero_entries_01/REPORT.md',
         IDENTITY/'vehicle_data_native/REPORT.md',
         WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/CName.hpp',
         WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/gamePersistentID.hpp']
pins=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sources]
files=[{'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(HERE.iterdir()) if p.is_file()]
MANIFEST.write_text(json.dumps({'exe_sha256':im.sha,'source_pins':pins,'files':files,'original_save_reads':0,
                               'capture_invocations':0,'parser_invocations':0,'game_calls':0,'runtime_changes':0},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','limitations')},indent=2))
