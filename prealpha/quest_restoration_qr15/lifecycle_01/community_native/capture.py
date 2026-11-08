"""Bounded static byte inspection of the pinned game; no executable loading.

Fresh outputs only. The finite functions below were reached through exact RTTI
constructors, instance vtables, and their direct control/data-flow dependencies.
"""
from pathlib import Path
import hashlib, json, struct, sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[3]
sys.path.insert(0, str(WORKSPACE / 'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image, EXE

FUNCTIONS = {
    'community_class_registration': 0x16CDD44,
    'community_construct_cls_thunk': 0xC2DC74,
    'community_instance_ctor': 0xC2DF6C,
    'spawner_subsystem_ctor': 0xC2E460,
    'spawner_weak_getter': 0x38360C,
    'spawner_weak_lookup': 0x383660,
    'spawner_raw_lookup': 0x382DA8,
    'activate_facade': 0x36E344,
    'deactivate_facade': 0x36E388,
    'reset_facade': 0x2BCD5F8,
    'registry_membership': 0x38430C,
    'queue_push': 0x38438C,
    'register_updates': 0xDABF78,
    'update_callback': 0x4CE6C8,
    'queue_job_builder': 0x4CEA80,
    'queue_job_creator': 0x4CEB20,
    'queue_job_body': 0x71F058,
    'system_tick': 0x71EDD0,
    'queue_drain': 0x71EE6C,
    'action_dispatcher': 0x382CF0,
    'ordinary_activate': 0x9CEFB8,
    'unregister_dispatch': 0x382D84,
    'reset_dispatch': 0x24600AE,
    'population_instance_registration': 0x16CF404,
    'population_construct_cls': 0xFA6858,
    'population_instance_init': 0x383F0C,
    'population_instance_uninit': 0x38426C,
    'population_instance_other_cleanup': 0xEE6FE8,
    'spawner_register_facade': 0x3840D4,
    'spawner_register': 0x3840E0,
    'spawner_allocate_shared': 0x383EAC,
    'spawner_ctor': 0x384470,
    'shared_pair_create': 0x1F5544,
    'registry_insert': 0x3847B4,
    'registry_value_insert': 0x38484C,
    'shared_pair_move': 0x18F068,
    'shared_pointer_swap': 0x26117FC,
    'spawner_initialize': 0x384944,
    'spawner_unregister_facade': 0x3842C8,
    'spawner_other_cleanup_facade': 0xEE7044,
    'take_saved_row': 0x3848BC,
    'restore_count_42': 0x384C74,
    'restore_array_10_to_spawned_88': 0x260657C,
    'restore_array_20_to_reserved_98': 0x2606570,
    'restore_array_30_to_nested': 0x21DA3F0,
    'restore_count_40': 0x11725C0,
    'restore_count_44': 0x11725B4,
    'restore_array_00_to_restored_78': 0x2BCEFC0,
    'array_u64_copy': 0x467DEC,
    'spawn_manager_class_registration': 0x16A248C,
    'spawn_manager_ctor_thunk': 0x35230C,
    'spawn_manager_ctor': 0x352314,
    'spawn_manager_handler_factory': 0x36CBB0,
    'spawn_manager_handler_init': 0x36CC40,
    'spawner_action_registration': 0x16A2D14,
    'spawner_action_ctor': 0xD6EF04,
    'spawner_action_execute': 0x36DFD0,
    'spawner_action_live': 0x36E038,
    'spawner_action_reset': 0x245E428,
    'community_save': 0x2BD3A48,
    'community_load': 0xA5C5BC,
    'community_map_load': 0x31C6C8,
    'community_entry_map_load': 0x31CA34,
    'spawner_map_load': 0xC2D078,
    'community_map_row_save': 0x2BD3F90,
    'spawner_row_save': 0x2BD3E84,
    'spawner_row_load': 0x3E9ADC,
    'fixed_u32_transfer': 0x3EAA6C,
    'name_transfer': 0x27A7C4,
    'name_write_without_dictionary': 0x2444600,
    'signed_vlq_write': 0x2F60040,
    'name_read_without_dictionary': 0xB9E560,
    'save_tail_three_lists': 0x2BD693C,
    'save_tail_list_a_row': 0x2BD6898,
}

def capture(im, rva):
    result = im.disasm(rva)
    if result['end_rva'] is None:
        rows = []
        for row in result['instructions']:
            rows.append(row)
            if row['mnemonic'] in ('ret', 'jmp'):
                break
        result['instructions'] = rows
        result['boundary_limit'] = 'No .pdata boundary; stop at first unconditional JMP or RET; maximum256 bytes'
    return result

def main():
    output = HERE / 'capture_01.json'
    assert not output.exists(), 'Refuse replacing evidence'
    im = Image()
    qword = lambda at: struct.unpack_from('<Q', im.data, im.off(at))[0] - im.base
    source = WORKSPACE / 'research/framework_pr63_01/codeware/src/Red/CommunitySystem.hpp'
    result = {
        'status': 'STATIC_PINNED_NATIVE_CAPTURE', 'exe': str(EXE), 'sha256': im.sha,
        'method': 'Read file bytes, PE .pdata and static Capstone decoding; no LoadLibrary/process/game calls',
        'game_calls': 0, 'save_writes': 0, 'runtime_writes': 0,
        'functions': {name: capture(im, rva) for name, rva in FUNCTIONS.items()},
        'metadata': {
            'class': 'gameCommunitySystem', 'registration': '0x16cdd44',
            'metadata_object': '0x4f2b5d8', 'metadata_vtable': '0x32deb60',
            'construct_cls_slot': '0xd8', 'construct_cls': hex(qword(0x32DEB60 + 0xD8)),
            'instance_vtable': '0x30d3a18',
            'instance_slots': {hex(o): hex(qword(0x30D3A18 + o)) for o in
                (0x108, 0x138, 0x148, 0x1D8, 0x1E0, 0x1E8, 0x258, 0x260, 0x2C8, 0x2E0, 0x2E8)},
            'population_metadata_vtable': '0x32dfb88',
            'population_construct_cls': hex(qword(0x32DFB88 + 0xD8)),
            'population_instance_vtable': '0x36773c0',
            'population_instance_slots': {hex(o): hex(qword(0x36773C0 + o)) for o in (0x160, 0x168, 0x170)},
        },
        'source': {'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest().upper()},
    }
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest().upper(),
                      'functions': len(FUNCTIONS), 'status': result['status']}))

if __name__ == '__main__':
    main()
