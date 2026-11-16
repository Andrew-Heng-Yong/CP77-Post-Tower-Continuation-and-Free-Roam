"""Verify the bounded native-freezer counterexample without executing game code.

Reads the pinned executable, captured disassembly, HP1 controls and installed
files. Writes only a fresh assessment directory beside this script.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HP1 = ROOT / 'prealpha/handler_preservation_hp1_20261112_01'
sys.path.insert(0, str(ROOT / 'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = HERE / args.out
    assert out.parent == HERE and not out.exists(), 'Use a fresh direct child directory'
    image = Image()
    checks, pins, functions = [], {}, {}

    def check(name, passed):
        assert passed, name
        checks.append(name)

    byte_count = 0
    for index in range(1, 25):
        path = HERE / f'native_{index:02d}/readback.json'
        capture = read(path)
        pins[str(path.relative_to(ROOT))] = sha(path)
        check(f'native_{index:02d} engine identity', capture['engine_sha256'] == image.sha)
        for function in capture['functions']:
            functions[int(function['requested_rva'], 16)] = function
            for row in function['instructions']:
                rva, expected = int(row['rva'], 16), bytes.fromhex(row['bytes'])
                actual = image.data[image.off(rva):image.off(rva) + len(expected)]
                assert actual == expected, (path, row)
                decoded = list(image.md.disasm(actual, image.base + rva))
                assert len(decoded) == 1
                assert (decoded[0].mnemonic, decoded[0].op_str) == (row['mnemonic'], row['operands'])
                byte_count += len(expected)
        for table, rows in capture['tables'].items():
            for row in rows:
                pointer = struct.unpack_from('<Q', image.data, image.off(int(table, 16) + int(row['slot'], 16)))[0]
                assert pointer - image.base == int(row['rva'], 16)
        check(f'native_{index:02d} instruction bytes, decoded operands and table pointers', True)

    def instruction(function, rva, mnemonic, operands):
        rows = {int(r['rva'], 16): r for r in functions[function]['instructions']}
        row = rows[rva]
        check(f'{rva:#x}: {mnemonic} {operands}', (row['mnemonic'], row['operands']) == (mnemonic, operands))

    # Actual area-freezer path: eligibility -> collect -> mode-5 recursive stop.
    instruction(0xBEB194, 0xBEB405, 'call', 'qword ptr [rax + 0x220]')
    instruction(0xBEB194, 0xBEB419, 'call', 'qword ptr [rax + 0x228]')
    instruction(0xBEC238, 0xBEC2E5, 'mov', 'r8b, 5')
    instruction(0xBEC238, 0xBEC32F, 'call', 'qword ptr [rax + 0xf8]')
    instruction(0xBEC478, 0xBEC6BB, 'call', '0x140bec6d4')
    instruction(0xBEC6D4, 0xBEC75A, 'call', '0x1402b1d30')
    instruction(0x2B1D30, 0x2B1E53, 'call', '0x142cc3684')
    instruction(0x2CC3684, 0x2CC3687, 'jmp', 'qword ptr [rax + 0x178]')
    instruction(0x2FDA9C, 0x2FDADD, 'call', 'qword ptr [rax + 0x68]')
    instruction(0x2FCF0C, 0x2FCF77, 'call', 'qword ptr [rax + 0x20]')
    # Timer uninitialization removes the node->timer mapping and cancels callback.
    instruction(0x194828, 0x194868, 'call', 'qword ptr [rax + 0x2c0]')
    instruction(0x194828, 0x194889, 'mov', 'rdi, qword ptr [rax + 0x1d0]')
    instruction(0x194828, 0x1948A2, 'call', 'rdi')
    instruction(0x1934AC, 0x1934EF, 'call', 'qword ptr [rax + 0x2c0]')
    instruction(0x1934AC, 0x193502, 'call', 'qword ptr [rax + 0x250]')
    instruction(0x7C7278, 0x7C72C0, 'mov', 'qword ptr [r8 + r10*8 + 0x49988], rdx')
    instruction(0x193674, 0x193688, 'call', '0x142179420')
    instruction(0x2179420, 0x21794E0, 'mov', 'dword ptr [rcx + r8*4 + 8], eax')
    # Absent record branch takes the duration supplied from the authored definition.
    instruction(0xE7111C, 0xE71183, 'movss', 'dword ptr [rsi + 0x48], xmm6')
    instruction(0x1948BC, 0x1948FB, 'call', 'qword ptr [rax + 0x2c8]')
    instruction(0x1948BC, 0x194907, 'jne', '0x1401949a8')
    instruction(0x1948BC, 0x194920, 'movss', 'xmm3, dword ptr [rsi + 0x48]')
    instruction(0x124214C, 0x12421C4, 'mov', 'dword ptr [r15 + 0x44], edi')
    instruction(0x193C74, 0x193CC4, 'je', '0x140193d68')
    instruction(0x193C74, 0x193DAB, 'mov', 'r8d, dword ptr [rsi + 0x44]')

    # This is a targeted engine counterexample, not a fabricated live timer fixture.
    qualification_path = HP1 / 'analysis_03/qualification.json'
    qualification = read(qualification_path)
    pins[str(qualification_path.relative_to(ROOT))] = sha(qualification_path)
    active = qualification['resolved_handlers']
    check('23 original saved registrations in the three controls', sum(map(len, active.values())) == 23)
    check('No active timer in those saved controls', all('questTimeCondition' not in json.dumps(r['parameters']) for rows in active.values() for r in rows))
    timer_examples = {}
    for quest, rows in qualification['native_timer_definitions'].items():
        timer_examples[quest] = [r for r in rows if r['graph'] != 'scene' and r['conditions']][:2]

    inputs = read(HP1 / 'evidence_01/inputs.json')
    unchanged = []
    for path, expected in inputs['pins'].items():
        # The registry is a large unrelated generated database; HP1's exact record
        # is retained. Verify runtime/core/dependency/manifest/snapshot inputs here.
        if path == inputs['registry']:
            continue
        check(f'unchanged input: {path}', sha(Path(path)) == expected)
        unchanged.append(path)
    for save in inputs['saves']:
        check(f'unchanged save body: {save["slot"]}', sha(Path(save['source'])) == save['source_sha256'])

    result = {
        'status': 'NATIVE_AREA_FREEZER_REJECTED_AS_GENERAL_EXACT_PAUSE',
        'engine_sha256': image.sha,
        'checks': checks,
        'check_count': len(checks),
        'verified_instruction_bytes_including_repeated_captures': byte_count,
        'evidence_sha256': pins,
        'native_delay_handlers': {
            'real_time': {'definition_vtable': '0x302c5a8', 'handler_vtable': '0x31267a0', 'initialize': '0x1948bc', 'uninitialize': '0x194828'},
            'game_time': {'definition_vtable': '0x31033b0', 'handler_vtable': '0x31c2388', 'initialize': '0x193c74', 'uninitialize': '0x1934ac'},
        },
        'static_finding': 'The traced freeze-stop removes pause handlers. Both native delay handlers remove their timer mapping and request cancellation through their respective timer-ID queues; their initialization without that record uses the authored duration. No remaining-time transfer is established by this path.',
        'scope_limit': 'Static instruction and source analysis, not execution. Cancellation enqueue is not an observed drained-queue acknowledgement. Does not prove every handler is freezable, every timer restarts on every route, or every callback can be suspended. Leaf disassembly after an unconditional tail jump is not treated as part of that function.',
        'selected_live_timer_fixture': 'NONE: all 23 selected saved registrations are non-timer controls',
        'timer_definition_examples_not_active_instances': timer_examples,
        'runtime_preservation_candidate': 'NOT_BUILT: shared exact-suspension prerequisite failed qualification',
        'live_preservation_test': 'NOT_RUN',
        'unchanged_inputs': unchanged,
        'unchanged_save_bodies': [s['slot'] for s in inputs['saves']],
        'game_writes': 0, 'save_writes': 0, 'game_launches': 0,
        'next_design': 'Keep native preservation unavailable; use the shared dispatcher with reviewed earned-stage adapters. Exact arbitrary-moment preservation would need a separate timer/callback and ownership implementation.',
    }
    out.mkdir()
    (out / 'assessment.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'check_count', 'live_preservation_test', 'game_writes', 'save_writes')}))


if __name__ == '__main__':
    main()
