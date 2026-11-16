"""Read remaining delay values where the saved node and timer identities agree."""
import math
import struct
import sys

from read_handlers import HERE, PREALPHA, RD10, framed, phase_hash, pin, read, sha, write

sys.path.insert(0, str(PREALPHA / 'quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image


GAME_DELAY = 'questGameTimeDelay_ConditionType'
REAL_DELAY = 'questRealtimeDelay_ConditionType'
GAME_RECORD = struct.Struct('<BIII11sI')
REAL_RECORD = struct.Struct('<BIIf')


def evidence():
    engine = Image()
    # Both delay initializers submit their saved node/value pair to the same table.
    vtable = 0x30BCE78
    for slot, entry in ((0x2B8, 0x194718), (0x2C8, 0x194AC4)):
        assert struct.unpack_from('<Q', engine.data, engine.off(vtable + slot))[0] == engine.base + entry
    expected = {
        0x194718: (0x194727, 'mov', 'rsi, qword ptr [rcx + 0xf0]'),
        0x194AC4: (0x194AD1, 'mov', 'rdi, qword ptr [rcx + 0xf0]'),
        0x1948BC: (0x19498B, 'call', 'qword ptr [rax + 0x2b8]'),
        0x193C74: (0x193E06, 'call', 'qword ptr [rax + 0x2b8]'),
        0x2CD3208: (0x2CD326D, 'shl', 'ebp, 4'),
        0x2AAC3D4: (0x2AAC465, 'addss', 'xmm0, dword ptr [rax + 0x38]'),
        0x2AAC958: (0x2AACB19, 'movss', 'xmm0, dword ptr [rdi + 4]'),
        0x1133B2C: (0x1133D33, 'mov', 'dword ptr [rax + 0x38], ecx'),
        0x2B0F614: (0x2B0F64C, 'lea', 'rdx, [rbx + 0x40]'),
        0x2AA8D00: (0x2AA8D88, 'call', 'qword ptr [rax + 0xf8]'),
    }
    for start, wanted in expected.items():
        assert any((int(row['rva'], 16), row['mnemonic'], row['operands']) == wanted
                   for row in engine.disasm(start)['instructions']), hex(start)
    return engine.sha, list(expected.values())


def component(row):
    raw = bytes.fromhex(row['hex'])
    if len(raw) != row['size'] or len(raw) < 4 or struct.unpack_from('<I', raw)[0] != row['id']:
        raise ValueError('Mismatched captured component frame')
    return raw


def game_records(raw):
    records = {}
    count, = struct.unpack_from('<I', raw)
    if len(raw) != 4 + count * GAME_RECORD.size:
        raise ValueError('Unsupported game timer layout')
    for timer_type, timer_id, deadline, flags, context, duration in GAME_RECORD.iter_unpack(raw[4:]):
        # This fixture contains one native timer record variant with empty named fields.
        if timer_type != 1 or flags != 1 or context != b'\x84None\x84None\x00' or not timer_id or timer_id in records:
            raise ValueError('Unsupported or duplicate game timer')
        records[timer_id] = (deadline, duration)
    return records


def real_records(raw):
    (group_count,) = struct.unpack_from('<I', raw)
    offset = 4
    records = {}
    for _ in range(group_count):
        (count,) = struct.unpack_from('<I', raw, offset)
        offset += 4
        end = offset + count * REAL_RECORD.size
        if end > len(raw):
            raise ValueError('Truncated real-time timer group')
        for timer_type, serial, group, remaining in REAL_RECORD.iter_unpack(raw[offset:end]):
            timer_id = (serial << 32) | group
            if timer_type != 1 or not serial or timer_id in records or not math.isfinite(remaining) or remaining < 0:
                raise ValueError('Unsupported or duplicate real-time timer')
            records[timer_id] = remaining
        offset = end
    if offset != len(raw):
        raise ValueError('Unparsed real-time timer bytes')
    return records


def main():
    selected = HERE / 'evidence_02/assessment.json'
    capture = HERE / 'evidence_04/timers.json'
    pin(selected, '5A3A48EFF64B82B2EAEBE69ED15BB65A44109CAF638E4A4DA0E294329CD1968D')
    pin(capture, '305FD3544FD009F91E90CB2F911130C3B09CC83EAC2C8D5F74E661F389F528FA')
    assessment = read(selected)
    saved = read(capture)
    sample = assessment['fixtures']['ManualSave-26']
    assert sample['save_sha256'] == saved['source_sha256'] and saved['save_version'] == 277
    engine_sha, instructions = evidence()
    assert engine_sha == assessment['engine_sha256']

    parts = saved['components']
    rows = list(struct.iter_unpack('<QQ', framed(component(parts['instances']), parts['instances']['id'], 16)))
    instance_data = dict(rows)
    assert len(instance_data) == len(rows)
    time_core = component(parts['time_core'])
    assert len(time_core) == 24
    game_clock, = struct.unpack_from('<I', time_core, 8)
    game = game_records(component(parts['time_timers'])[4:])
    real = real_records(component(parts['delay_structs'])[4:])
    bound = []
    for handler in sample['delay_handlers']:
        kind = handler['registration_type']
        if kind not in (GAME_DELAY, REAL_DELAY):
            continue
        key = phase_hash(handler['address']) << 32 | handler['node']
        timer_id = instance_data.get(key)
        if kind == GAME_DELAY and timer_id in game:
            deadline, duration = game[timer_id]
            remaining = deadline - game_clock
            assert 0 < remaining <= duration
            result = {'remaining_game_seconds': remaining, 'scheduled_game_seconds': duration}
        elif kind == REAL_DELAY and timer_id in real:
            result = {'remaining_real_seconds': real[timer_id]}
        else:
            continue
        bound.append(dict(handler, node_key=f'{key:016X}', timer_id=f'{timer_id:016X}', **result))

    real_count = sum('remaining_real_seconds' in row for row in bound)
    game_count = len(bound) - real_count
    assert real_count == 9 and game_count == 13
    assert len({row['timer_id'] for row in bound}) == len(bound)
    output = HERE / 'evidence_04/timer_binding.json'
    write(output, {'status': 'OFFLINE_SAVED_REMAINING_DELAY', 'save_sha256': saved['source_sha256'],
                   'registration_assessment_sha256': sha(selected), 'timer_capture_sha256': sha(capture),
                   'engine_sha256': engine_sha, 'native_instruction_checks': instructions,
                   'game_timer_rows': len(game), 'real_timer_rows': len(real), 'direct_delay_bindings': bound,
                   'runtime_admission': 0, 'game_writes': 0, 'save_writes': 0})
    print(f'Bound remaining duration for {real_count} real-time and {game_count} game-time quest delays.')


if __name__ == '__main__':
    main()
