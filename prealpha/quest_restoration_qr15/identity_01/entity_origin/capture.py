"""Trace exact saved associated-ID producers/consumers in pinned native bytes.

No original save, executable loading, process access, game calls or mutations.
"""
from pathlib import Path
import hashlib,json,struct,sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
sys.path.insert(0,str(WORK/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

FUNCTIONS={
    'save_row_from_spawner':0x2BCED84,
    'u64_array_append':0x2F9DF0,
    'spawner_active_ids':0x36E5E0,
    'pending_stub_list':0x46960C,
    'restore_registration':0x3840E0,
    'restore_array20_to_reserved98':0x2606570,
    'restore_u64_array_copy':0x467DEC,
    'activation_virtual_first_block':0x9CEFD8,
    'activation_virtual_taken_branch':0x9CEFE2,
    'activate_create_or_restore':0x9CF5A0,
    'create_request_from_associated_id':0x9CF6EC,
    'create_stub_forwarder':0x2F9E74,
    'create_stub_queue':0x2FA044,
    'create_stub_token':0x2FA378,
    'restore_previous_active_ids':0x9CEFE8,
    'restore_stub_prepare':0x9CF088,
    'restore_stub_forwarder':0x9CF25C,
    'restore_stub_queue':0x9CF378,
    'stub_system_binding':0x384960,
    'stub_system_registration':0x173C1C8,
    'stub_system_construct':0xDB3B7C,
    'stub_system_ctor':0xDB3B84,
    'persistency_interface_registration':0x163D24C,
    'persistency_registration':0x17341D0,
    'persistency_construct':0x5A14B0,
    'persistency_ctor':0x5A02C8,
    'entity_persistence_classification':0x4CB220,
    'dynamic_id_interface_registration':0x162FCD4,
    'dynamic_id_registration':0x16E6E38,
    'dynamic_id_construct':0x13EFF30,
    'dynamic_id_ctor':0x13EFF38,
    'allocate_high_interval':0x4FAC20,
    'allocate_high_interval_wrap':0x4FAC3F,
    'allocate_low_interval':0x12EC1A8,
    'allocate_low_interval_wrap':0x12EC1C7,
    'allocator_select':0x4FABB8,
    'dynamic_id_v1D8_filter':0x2FAB90,
    'dynamic_id_v1E0_filter':0x2B338D8,
    'record_id_lookup':0x4FAB74,
    'record_map_lookup':0x382BE0,
}

def main():
    out=HERE/'evidence_01.json'
    assert not out.exists()
    im=Image()
    def capture(a):
        f=im.disasm(a)
        if f['end_rva'] is None:
            rows=[]
            for i in f['instructions']:
                rows.append(i)
                if i['mnemonic'] in ('jmp','ret'):break
            f['instructions']=rows
            f['boundary_limit']='No unwind boundary; first JMP or RET only. Separately named taken/wrap branches are captured explicitly.'
        return f
    def q(v,o):return hex(struct.unpack_from('<Q',im.data,im.off(v+o))[0]-im.base)
    files=[WORK/'prealpha/quest_restoration_qr15/lifecycle_01/save_community/decode_02/result.json',
           WORK/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/gameIEntityStubSystem.hpp',
           WORK/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/entEntityID.hpp']
    result={'status':'BOUNDED_NATIVE_ENTITY_ID_DATAFLOW','exe_sha256':im.sha,
            'functions':{k:capture(v)for k,v in FUNCTIONS.items()},
            'bindings':{
                'stub_metadata_D8':q(0x3330838,0xD8),
                'stub_instance_slots':{hex(o):q(0x31083C0,o)for o in(0x1B0,0x1B8)},
                'persistency_metadata_D8':q(0x332B058,0xD8),
                'persistency_instance_v1F0':q(0x36343D8,0x1F0),
                'dynamic_metadata_D8':q(0x32F1268,0xD8),
                'dynamic_instance_slots':{hex(o):q(0x3213628,o)for o in(0x1B0,0x1B8,0x1D8,0x1E0,0x200)},
            },
            'pins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest().upper()for p in files},
            'source_trace':[
                'savedrow+0x20 merges object+0x98 and active IDs whose IPersistencySystem.v1F0 result!=2',
                'restore_registration→2606570→467DEC copies row+0x20 unchanged to object+0x98',
                '9CF5A0 pops exactU64 from object+0x98→9CF6EC→create-requestfirstU64→2F9E74→2FA044',
                'same requestfield fallback is populated by exact DynamicEntityIDSystem allocators4FAC20/12EC1A8',
                'EntityStubToken native2FA378 copies requestfirstU64 to token+0x08 unchanged',
            ],
            'conclusion':'Associated values use the EntityID namespace on this native path, not a distinct opaque StubID needing a numeric conversion. Specific row20 origin(reserved vsfiltered active) is not recoverable from this merged row alone.',
            'limits':['No current-loaded-body or actorPS identity proof.',
                      'No claim the target ID is currently spawned, saved asPS, or absent.',
                      'High allocator interval[10000000,16777215) is source-confirmed; persistence maps/exceptions and eligibility can still affect treatment.',
                      'No global proof that all engine restore/remap paths preserve every ID; only this concrete copied/reserved request route.'],
            'original_save_reads':0,'game_calls':0,'save_writes':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest().upper(),'functions':len(FUNCTIONS)}))

if __name__=='__main__':main()
