"""Bounded read-only R9 crash diagnosis; no heap strings or save data exported."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

from inspect_native_crash import Dump

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/finalboards_dismissal/tooling/python'))
import pefile

GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
REPORT = 'Cyberpunk2077-20261006-142725-20216-18236'
DUMP = Path(r'C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue') / REPORT / 'Cyberpunk2077.dmp'
AUDIT = GAME / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit/afterlife_behavior_20261006T182639Z.jsonl'


def fnv(value):
    h = 0xcbf29ce484222325
    for byte in value.encode():
        h = ((h ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return h


def main():
    d = Dump(DUMP)
    report = d.report()
    assert report['fault'] == 'Cyberpunk2077.exe+0x1d9779'
    assert report['exception_parameters'] == ['0x0', '0xffffffffffffffff']
    r = {k: int(v, 16) for k, v in report['registers'].items()}
    base = next(b for b, _, name in d.modules if name == 'Cyberpunk2077.exe')
    u64 = lambda p: struct.unpack('<Q', d.read(p, 8))[0]
    pe = pefile.PE(str(GAME / 'bin/x64/Cyberpunk2077.exe'), fast_load=True)
    assert pe.get_data(0x1d9779, 6) == bytes.fromhex('ff90d8000000')
    # 18ef7e0 and 18ef8c0 are the RTTI getters for the two native tables.
    hard_type = u64(base + 0x342df18)
    anim_type = u64(base + 0x342df98)
    assert u64(hard_type + 0x18) == fnv('entHardAttachment')
    assert u64(anim_type + 0x18) == fnv('entAnimatedComponent')
    assert r['rax'] == u64(r['rcx']) == base + 0x307ea9c
    # A neighboring allocation has the normal constructor-written table.
    assert u64(r['rcx'] + 0x58) == base + 0x307ea98
    assert u64(r['rdx']) == base + 0x2ae68b0
    assert u64(r['rdx'] + 0x40) == fnv('root')
    # Native hard-attachment method 1d92a0 copies WorldTransform from e0/f0.
    position = [v / 131072 for v in struct.unpack('<iii', d.read(r['rdx'] + 0xe0, 12))]
    orientation = list(struct.unpack('<ffff', d.read(r['rdx'] + 0xf0, 16)))
    bounds = list(struct.unpack('<ffffffff', d.read(r['rdx'] + 0x100, 32)))
    assert all(abs(bounds[i] - (position[i] - 10)) < 1e-4 for i in range(3))
    assert all(abs(bounds[i + 4] - (position[i] + 10)) < 1e-4 for i in range(3))
    matches = []
    for line in AUDIT.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        for actor in row.get('actors', []):
            p = actor.get('position', {})
            if all(abs(p.get(k, 0) - position[i]) < 1e-6 for i, k in enumerate(('x', 'y', 'z'))):
                matches.append(dict(utc=row['utc'], id=actor['id'], record=actor['record'],
                                    in_workspot=actor.get('in_workspot'), in_scene=actor.get('in_scene')))
    assert len(matches) == 4 and {a['id'] for a in matches} == {'10029921ULL'}
    # Both attachment sides share their owner pointer, but that owner's memory
    # is absent from the bounded minidump: do not claim a directly read ID.
    child = u64(r['rdi'])
    assert u64(child + 0x50) == u64(r['rdx'] + 0x50)
    child_name_hash = u64(child + 0x40)
    source_name_matches = []
    for path in (ROOT / 'research/afterlife_world').rglob('*.app.json'):
        strings = set(re.findall(r'"([^"\r\n]{1,160})"', path.read_text(encoding='utf-8-sig')))
        for value in strings:
            if fnv(value) == child_name_hash:
                source_name_matches.append({'file': str(path.relative_to(ROOT)), 'component_name': value})
    result = dict(
        status='MATCHED_CORRUPTED_HARD_ATTACHMENT_NOT_OLD_ACTOR_INDEX_FAULT',
        report=REPORT,
        dump_sha256=hashlib.sha256(d.data).hexdigest().upper(),
        build='Cyberpunk 2.31 / P4CL9778208',
        fault='Cyberpunk2077.exe+0x1d9779',
        fault_instruction='call qword ptr [rax+0xd8]',
        object_type='entHardAttachment', expected_vtable_rva='0x307ea98',
        actual_vtable_rva='0x307ea9c', vtable_difference=4,
        target_type='entAnimatedComponent', target_component_name='root',
        position=position, orientation=orientation,
        live_transform_matches=matches,
        same_owner_pointer_on_attachment_child_and_parent=True,
        child_component_name_source_matches=source_name_matches,
        instructions=[
            '1d976e: read hard attachment vtable',
            '1d9775: load target component argument',
            '1d9779: virtual call at table+0xd8',
            '1d92a0: expected method copies target WorldTransform at e0/e8/f0',
            '1c772d..1c773e: constructor writes valid table307ea98'],
        limits=[
            'Transform match is strong actor association, not a directly read entity ID.',
            'Writer that corrupted attachment vtable is not known; +4 is compatible with a misdirected counter increment, not proof of one.',
            'User reports approach to Rogue, but root target matches an ordinary crowd female near entrance, not Rogue booth.',
            'No basis to blame R5, Rogue scene, an external mod, or the new distance gate conclusively.',
            'Disabling Rogue scene admission is safety containment only, not proof this crash is fixed.'])
    out = ROOT / 'research/afterlife_world/interactions_r10/crash/evidence.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
