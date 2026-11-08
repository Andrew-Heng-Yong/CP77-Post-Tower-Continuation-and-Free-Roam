"""Static bytes only. No game APIs, processes, original saves or imports of builders."""
from pathlib import Path
import hashlib, json, struct, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

FUNCTIONS = {
    'event_node_registration': 0x168EBBC,
    'event_node_construct': 0x352840,
    'event_node_ctor': 0x352770,
    'event_node_execute': 0x565B5C,
    'event_node_ps_class': 0x566160,
    'event_node_pid': 0x1817C7C,
    'out_name': 0x4F1D80,
    'event_node_append_out': 0x5649F4,
    'vehicle_node_registration': 0x16AD920,
    'vehicle_node_construct': 0x352848,
    'vehicle_node_execute': 0x9A1524,
    'vehicle_node_factory': 0x9A170C,
    'toggle_door_registration': 0x16AA1AC,
    'toggle_door_construct': 0xE72B3C,
    'toggle_door_execute': 0x18F3D54,
    'toggle_door_second_stage': 0x664F00,
    'toggle_door_event_constructor': 0x18F3E78,
    'toggle_door_handler_factory': 0x1164DE8,
    'toggle_door_context_factory': 0x1164E40,
    'persistency_ctor': 0x5A02C8,
    'persistency_queue_ctor': 0x5A1588,
    'persistency_queue_append': 0x1A5568,
    'persistency_queue_locked_append': 0x1A548C,
    'persistency_queue_copy': 0x1A5524,
    'persistency_register_updates': 0xDAAE14,
    'persistency_queue_callback': 0xE6EC4C,
    'persistency_queue_drain': 0x1A50EC,
    'persistency_request_dispatch': 0x1A5200,
    'persistency_typed_dispatch': 0x1A536C,
    'persistency_notify_pid_listeners': 0x1A52E0,
    'persistency_forward_original_event': 0xE36684,
    'persistency_forward_changed_event': 0xE365BC,
    'persistency_world_attached': 0x1853728,
    'persistency_before_world_detach': 0x4B4B90,
    'persistency_after_world_detach': 0xAF88C0,
    'persistency_before_save': 0x2A35648,
    'persistency_save': 0x2A35150,
    'persistency_load': 0x59FB28,
    'presave_job_constructor': 0x2A8230,
    'presave_job_queue1': 0x21648C0,
    'presave_job_queue2': 0x2164910,
    'presave_job_queue3': 0x21647F0,
    'entity_queue_event': 0x1A67B0,
    'entity_queue_event_locked': 0x1A67D4,
}
TABLES = {
    'EventManagerNodeDefinition': (0x3047DB8, [0x158, 0x188]),
    'VehicleNodeDefinition': (0x3047F38, [0x158, 0x188]),
    'ToggleDoorNodeType': (0x3126D18, [0x108, 0x110, 0x118]),
    'PersistencySystem': (0x36343D8, [0x108, 0x110, 0x118, 0x128, 0x130, 0x138, 0x140, 0x148, 0x1C8]),
    'PersistencyQueueCallback': (0x394E1E0, [0]),
}

def main():
    target = HERE / 'native_01.json'
    assert not target.exists(), 'Fresh output required'
    im = Image()
    funcs = {}
    for name, addr in FUNCTIONS.items():
        f = im.disasm(addr)
        if f.get('end_rva') is None:
            rows = []
            for row in f['instructions']:
                rows.append(row)
                if row['mnemonic'] in ('ret', 'jmp'):
                    break
            f['instructions'] = rows
            f['boundary_limit'] = 'No unwind boundary; bounded at first unconditional JMP/RET, at most256 bytes'
        funcs[name] = f
    tables = {name: {'rva': hex(vt), 'slots': {hex(s): hex(struct.unpack_from('<Q', im.data, im.off(vt)+s)[0]-im.base) for s in slots}} for name, (vt, slots) in TABLES.items()}
    pinned = []
    for path in [ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source/event_contract_01.json', ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/manifest.json', ROOT/'prealpha/quest_restoration_qr15/identity_01/native_pid/flags_lifecycle_01/REPORT.md']:
        data=path.read_bytes()
        pinned.append({'path': str(path), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest().upper()})
    result={'exe_sha256': im.sha, 'method': 'Read-only pinned executable file bytes and retained source evidence. No game/save/process/API access.', 'functions': funcs, 'tables': tables, 'source_pins': pinned}
    target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'output':str(target), 'functions':len(funcs), 'tables':len(tables), 'exe_sha256':im.sha}))

if __name__=='__main__': main()
