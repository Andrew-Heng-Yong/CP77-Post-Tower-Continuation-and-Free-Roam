"""Exact native vehiclePersistentDataPS component key; static files only."""
from pathlib import Path
import hashlib,json,struct,sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
sys.path.insert(0,str(WORK/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

FUNCTIONS={
    'vehicle_base_class_registration':0xEC3E8C,
    'vehicle_base_construct_cls':0x10A63DC,
    'vehicle_base_normal_ctor':0x23591C,
    'vehicle_base_initialize':0x593118,
    'vehicle_data_class_registration':0x16DDA58,
    'vehicle_data_construct_cls':0xDD73C8,
    'vehicle_data_ctor':0xDD73D0,
    'vehicle_data_class_name':0x9A2498,
    'vehicle_data_lookup':0x9A2514,
    'vehicle_data_lookup_from_stub':0x9A24E4,
    'vehicle_data_other_consumer':0x9A2428,
    'vehicle_data_cleanup_consumer':0x2B9ED90,
    'vehicle_persistency_system_getter':0x256F2C,
}

def main():
    out=HERE/'evidence_01.json'
    verify=HERE/'verification_01.json'
    assert not out.exists() and not verify.exists()
    im=Image()
    def capture(a):
        f=im.disasm(a)
        if f['end_rva']is None:
            rows=[]
            for i in f['instructions']:
                rows.append(i)
                if i['mnemonic']in('jmp','ret'):break
            f['instructions']=rows
            f['boundary_limit']='No unwind boundary; first unconditional JMP or RET only'
        return f
    def slot(v,o):return struct.unpack_from('<Q',im.data,im.off(v+o))[0]-im.base
    def rip(a):
        p=im.off(a)
        return a+7+struct.unpack_from('<i',im.data,p+3)[0]
    def raw(a,h):
        b=bytes.fromhex(h)
        return im.data[im.off(a):im.off(a)+len(b)]==b
    component=0xF8B5D41E08E5736F
    calculated=0xCBF29CE484222325
    for b in b'vehiclePersistentDataPS':
        calculated=((calculated^b)*0x100000001B3)&0xFFFFFFFFFFFFFFFF
    m,mask=0xC6A4A7935BD1E995,0xFFFFFFFFFFFFFFFF
    entity=10229047
    t=(m*component)&mask
    t=(m*(t^(t>>47)))&mask
    key=(m*(entity^t))&mask
    pins=[WORK/'prealpha/quest_restoration_qr15/identity_01/native_pid/REPORT.md',
          WORK/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated/vehicle/PersistentDataPS.hpp',
          WORK/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated/vehicle/DestructionPSData.hpp']
    result={'status':'EXACT_NATIVE_VEHICLE_DATA_COMPONENT_KEY','exe_sha256':im.sha,
            'functions':{k:capture(v)for k,v in FUNCTIONS.items()},
            'vehicle_base':{'class':'vehicleBaseObject','metadata_vtable':'0x3670030',
                'ConstructCls':hex(slot(0x3670030,0xD8)),'instance_vtable':'0x317bb80',
                'initialize_slot_160':hex(slot(0x317BB80,0x160))},
            'vehicle_data':{'class':'vehiclePersistentDataPS','metadata_vtable':'0x32ea648',
                'ConstructCls':hex(slot(0x32EA648,0xD8)),'class_global':'0x3bc8160',
                'component_name':'vehiclePersistentDataPS','component_cname_u64':str(component),
                'component_cname_hex':hex(component),'owner_pid_entity_field':'vehicle+0x48',
                'owner_state_handle_field':'vehicle+0x538'},
            'target':{'associated_entity_candidate_u64':str(entity),'component_cname_u64':str(component),
                      'persistent_id_key_u64':str(key),'persistent_id_key_hex':hex(key)},
            'pins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest().upper()for p in pins},
            'limits':['This is the ordinary native initialization key; no guarantee this associatedhistoricalEntityID is the presently loadedbody.',
                      'The lookup can create/hydrate/init state; it is not authorized as a passive game query.',
                      'No saved-row hit, visual-grid content, door state, setup completion or safe replay is established here.',
                      'SDK destruction-field layout is corroborating type evidence, not a substitute for decoding the exact saved property content.'],
            'game_calls':0,'original_save_reads':0,'save_writes':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    checks=[]
    def ck(n,v,e):checks.append({'name':n,'pass':bool(v),'evidence':e})
    ck('base_name_rip',rip(0xEC3EDB)==0x3132048,'vehicleBaseObjectliteral')
    ck('base_construct_bound',slot(0x3670030,0xD8)==0x10A63DC,'CClassvirtualD8')
    ck('base_construct_installs_vtable',rip(0x10A63ED)==0x317BB80,'leaactualinstancevtable')
    ck('base_initializer_bound',slot(0x317BB80,0x160)==0x593118,'actualinstancevirtual160')
    ck('data_class_name_literal',rip(0x16DDAA7)==0x30A0A98,'vehiclePersistentDataPSliteral')
    ck('data_construct_bound',slot(0x32EA648,0xD8)==0xDD73C8,'nativeclassconstructor')
    ck('data_class_pointer_registration_and_lookup_agree',rip(0x16DDAF8)==rip(0x9A252E)==0x3BC8160,
       'separatePSclassargumentR9')
    ck('cname_literal_matches_independent_fnv',calculated==component and raw(0x9A24AC,'48bf6f73e5081ed4b5f8'),
       'literalvehiclePersistentDataPS→F8B5D41E08E5736F')
    ck('initializer_entity_id_is_object48',raw(0x59321A,'488b5648') and raw(0x59322C,'488955b0'),
       'object+48→PersistentID+0')
    ck('initializer_component_name_is_class_cname',raw(0x593222,'488b08') and raw(0x593225,'48894db8'),
       'class-namehelperout→PersistentID+8')
    ck('initializer_state_handle_field538',raw(0x5931E0,'488dbe38050000'),
       'nativevehicledatahandle+538')
    ck('lookup_passes_PID_unchanged_and_create_true',raw(0x9A2546,'c644242001') and raw(0x9A254B,'ff90b0010000'),
       'R8retainedPID;stackcreate1;PersistencySystemvirtual1B0')
    ck('system_getter_is_exact_persistency_interface',rip(0x256F33)==0x3BC2F10,'reusedexactgameIPersistencySystembinding')
    ck('candidate_key_uses_verified_native_formula',key==17113219195054135786,
       'native_pid/REPORT.md arithmetic reused withoutPSlookup')
    verification={'status':'PASS'if all(x['pass']for x in checks)else'FAIL','checks':checks,
                  'evidence_sha256':hashlib.sha256(out.read_bytes()).hexdigest().upper(),
                  'game_calls':0,'original_save_reads':0,'save_writes':0,'runtime_changes':0}
    verify.write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':verification['status'],'checks':len(checks),
                      'failures':[x['name']for x in checks if not x['pass']], 'target':result['target'],
                      'evidence_sha256':verification['evidence_sha256']}))

if __name__=='__main__':main()
