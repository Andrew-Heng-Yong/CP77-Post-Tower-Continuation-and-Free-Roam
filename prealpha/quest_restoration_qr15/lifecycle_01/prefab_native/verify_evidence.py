"""Verify static evidence against pinned bytes; never loads game code or saves."""
from pathlib import Path
import hashlib, json, struct, sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from inspect_prefabs import Image, WORKSPACE

out = HERE / 'verification_01.json'
manifest = HERE / 'manifest_01.json'
assert not out.exists() and not manifest.exists()
im = Image()
rows = {}
verified_instructions = 0
verified_qwords = 0
for path in sorted(HERE.glob('native_*.json')) + [HERE / 'queue_candidates_03.json']:
    value = json.loads(path.read_text(encoding='utf-8'))
    assert value['exe_sha256'] == im.sha
    assert value.get('game_api_calls') == 0 and value.get('runtime_changes') == 0
    for f in value.get('functions', []) + value.get('explicit_spans', []):
        for row in f['instructions']:
            a = int(row['rva'], 16)
            b = bytes.fromhex(row['bytes'])
            assert im.data[im.off(a):im.off(a)+len(b)] == b, (path, row)
            if a in rows: assert rows[a]['bytes'] == row['bytes']
            rows[a] = row
            verified_instructions += 1
    for base, words in value.get('qwords', {}).items():
        for address, target in words:
            assert struct.unpack_from('<Q', im.data, im.off(int(address, 16)))[0] == int(target, 16)
            verified_qwords += 1
    for target, addresses in value.get('pointer_refs', {}).items():
        for address in addresses:
            assert struct.unpack_from('<Q', im.data, im.off(int(address, 16)))[0] == im.base+int(target, 16)

checks = []
def check(name, condition, evidence):
    assert condition, name
    checks.append({'name': name, 'result': 'PASS', 'evidence': evidence})
def op(address, mnemonic, operands):
    row = rows[int(address, 16)]
    return row['mnemonic'] == mnemonic and row['operands'] == operands
def pointer(address, target):
    return struct.unpack_from('<Q', im.data, im.off(address))[0] == im.base+target
def call(address, target):
    return op(address, 'call', hex(im.base+target))

sdk = WORKSPACE / 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated'
source_paths = [WORKSPACE / 'research/framework_pr63_01/codeware/src/Red/QuestsSystem.hpp'] + [sdk / p for p in (
    'quest/QuestPhaseResource.hpp', 'quest/PhaseNodeDefinition.hpp', 'quest/QuestPrefabEntry.hpp',
    'quest/QuestPrefabsHandler.hpp', 'quest/QuestPrefabsEntry.hpp', 'world/QuestPrefabLoadingMode.hpp',
    'world/IQuestPrefabStateListener.hpp', 'world/RuntimeSystemWorldStreaming.hpp')]
sources = {str(p.relative_to(WORKSPACE)): hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in source_paths}
check('SDK resource and instance prefab arrays are distinct',
      'phasePrefabs; // 50' in source_paths[1].read_text() and
      'inplacePhases; // 60' in source_paths[1].read_text() and
      'phaseInstancePrefabs; // 70' in source_paths[2].read_text(), sources)
check('SDK entry is one NodeRef and mode values are zero/one',
      'RED4EXT_ASSERT_SIZE(QuestPrefabEntry, 0x8)' in source_paths[3].read_text() and
      'Disable = 0' in source_paths[6].read_text() and 'ForceLoad = 1' in source_paths[6].read_text(),
      ['quest/QuestPrefabEntry.hpp', 'world/QuestPrefabLoadingMode.hpp'])
check('Shared loader reflection ConstructCls binds native constructor',
      pointer(0x32B7858, 0x2CA3338) and op('0x2ca333b', 'jmp', '0x140697cd4'), 'native_06/07/08/09')
check('Shared loader listener virtual slot binds state callback', pointer(0x306F998, 0x69A0D8), 'native_10/27')
check('Resource cache constructor and acquire/release vtable slots agree',
      pointer(0x306F788, 0x21F99D0) and pointer(0x306F790, 0x34F7C4) and
      op('0x6976ba', 'mov', 'qword ptr [rsi + 0x198], rcx'), 'native_12/13/14')
check('Phase handler virtual initialization/uninitialization/readiness',
      pointer(0x3046758, 0x88AFCC) and pointer(0x3046768, 0x34F1C0) and pointer(0x3046790, 0x3515D8), 'native_03/04')
check('PhaseNode factory and execute bind exact native methods',
      pointer(0x3047230, 0x3519F8) and pointer(0x3047200, 0x34F37C), 'native_32')
check('Resource callback copies resource phasePrefabs',
      op('0xdd542f', 'mov', 'rdx, qword ptr [rdx]') and op('0xdd5436', 'add', 'rdx, 0x50') and
      call('0xdd543a', 0x4CEF9C), 'native_18')
check('Actual child ticket selector chooses resource plus50 else definition plus70',
      op('0xdae8fc', 'mov', 'rax, qword ptr [rcx + 0x48]') and
      op('0xdae905', 'add', 'rax, 0x50') and op('0xdae90a', 'lea', 'rax, [rcx + 0x70]'), 'native_35 explicit leaf span')
check('Separate handler and child ticket acquisitions use same shared loader',
      call('0xdd52fb', 0x699F78) and op('0xdd5304', 'mov', 'dword ptr [rsi + 0x54], eax') and
      call('0x2b1568', 0x699F78) and op('0x2b1571', 'mov', 'dword ptr [rcx + 0x84], eax'), 'native_05/33')
check('Shared count acquire only emits enable on zero',
      op('0x699731', 'test', 'eax, eax') and op('0x699733', 'jne', '0x140699746') and
      call('0x69973e', 0x699498) and op('0x69974b', 'inc', 'eax'), 'native_02/35')
check('Shared count release only emits disable at zero',
      op('0x698f93', 'add', 'dword ptr [rax + rdx*4], -1') and
      op('0x698f97', 'jne', '0x140698fb7') and call('0x698fb2', 0x699498), 'native_02/35')
check('Cancel releases ticket references and erases ticket record',
      call('0x698ea4', 0x698F24) and call('0x698ec2', 0x698D84), 'native_01/35')
check('Child cleanup cancels its prefab ticket',
      op('0x2b1ebf', 'mov', 'edx, dword ptr [rdi + 0x84]') and call('0x2b1f36', 0x698E24), 'native_35')
check('Owning phase handler cancellation clears its ticket',
      call('0x34f2a6', 0x698E24) and op('0x34f2ab', 'and', 'dword ptr [rbx + 0x54], 0'), 'native_32')
check('Handler Uninitialize cancels and disables late responses',
      call('0x34f1e1', 0x34F28C) and op('0x34f1ee', 'xchg', 'dword ptr [rbx + 0x30], esi') and
      op('0xdd5422', 'mov', 'eax, dword ptr [rcx + 0x30]') and op('0x6989b9', 'mov', 'eax, dword ptr [r10 + 0x30]'), 'native_04/18/35')
check('Resource-cache release decrements count or erases resource handle',
      op('0x34f80b', 'cmp', 'eax, 1') and op('0x34f810', 'dec', 'eax') and
      call('0x34f825', 0x34F680) and call('0x34f744', 0x195798), 'native_15/16')
check('World reflection ConstructCls binds constructor and two vtables',
      pointer(0x338DEF8, 0x8B8800) and op('0x8b8803', 'jmp', '0x1408b8244') and
      pointer(0x308F3D0, 0x69B1FC), 'native_20/21/22/28')
check('World producer appends request under separate queue lock',
      op('0x699534', 'lea', 'rdi, [rcx + 0x2e8]') and
      op('0x69954d', 'lea', 'rcx, [rsi + 0x2d8]') and call('0x699563', 0x1CC5AC), 'native_04')
check('World consumer takes same queue and source count is cleared by move',
      op('0x69b477', 'lea', 'rbx, [rcx + 0x2e8]') and
      op('0x69b499', 'lea', 'rdx, [rsi + 0x2d8]') and call('0x69b4a4', 0x547ACC) and
      op('0x547af7', 'and', 'dword ptr [rdx + 0xc], 0'), 'native_25/26')
check('World callback/update order evaluates previous state before consuming requests',
      call('0x69b269', 0x69B738) and call('0x69b271', 0x69B450), 'native_26')
check('World consumer reads retained NodeRef index and edits separate desired map',
      op('0x69b4f0', 'lea', 'rcx, [rsi + 0x128]') and
      op('0x69b5ba', 'lea', 'rcx, [rsi + 0x2a8]') and
      op('0x69b65d', 'lea', 'rcx, [rsi + 0x2a8]'), 'native_25; full reviewed consumer')
check('Streaming state invokes shared listener at correct virtual slot',
      op('0x69b93e', 'call', 'qword ptr [rax + 0xd8]') and
      op('0x69b9b8', 'call', 'qword ptr [rax + 0xd8]') and pointer(0x306F998, 0x69A0D8), 'native_27')
check('Quest update separately drains ready-ticket callbacks',
      call('0x4ad65b', 0x698FC8) and call('0x699037', 0x699064) and
      op('0x69907d', 'call', 'qword ptr [rax + 0x10]'), 'native_13/30/31')
candidate_value = json.loads((HERE / 'queue_candidates_03.json').read_text())
check('Queue search positive producer control and independently bound consumer',
      {f['begin_rva'] for f in candidate_value['functions']} == {'0x699520', '0x69b450'}, 'queue_candidates_03; earlier empty filtered outputs are not proof')

result = {'scope': 'Static native prefab lifecycle premises only; no live owner, physical detach, population, spawner, persistent-state, callback-thread, gameplay or save-compatibility certification',
          'exe_sha256': im.sha, 'verified_instruction_spans_with_duplicates': verified_instructions,
          'unique_verified_instruction_starts': len(rows), 'verified_qwords_with_duplicates': verified_qwords,
          'checks': checks, 'check_count': len(checks), 'game_api_calls': 0, 'runtime_changes': 0, 'save_reads': 0}
out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
files = [{'path': str(p.relative_to(WORKSPACE)), 'bytes': p.stat().st_size,
          'sha256': hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted(HERE.iterdir()) if p.is_file()]
manifest.write_text(json.dumps({'exe_sha256': im.sha, 'source_sha256': sources, 'files': files,
    'game_api_calls': 0, 'runtime_changes': 0, 'save_reads': 0}, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
