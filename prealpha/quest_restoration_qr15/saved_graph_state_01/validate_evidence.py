"""Assert exact native anchors and source inputs; writes only fresh evidence here."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, struct
from inspect_native import Image, HERE, WORKSPACE

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def fnv32(data, seed=0x811c9dc5):
    for byte in data:
        seed=((seed^byte)*0x01000193)&0xffffffff
    return seed

def main():
    out=HERE/'verification_01.json'
    manifest=HERE/'manifest_01.json'
    assert not out.exists() and not manifest.exists()
    im=Image()
    instructions={}
    for p in sorted(HERE.glob('native_*.json')):
        data=json.loads(p.read_text(encoding='utf-8'))
        assert data['exe_sha256']==im.sha
        for f in data.get('functions',[]):
            for r in f.get('instructions',[]):
                address=int(r['rva'],16)
                b=bytes.fromhex(r['bytes'])
                assert im.data[im.off(address):im.off(address)+len(b)]==b
                assert address not in instructions or instructions[address]==r
                instructions[address]=r
    checks=[]
    def instruction(addr, mnemonic, operands):
        r=instructions[addr]
        assert (r['mnemonic'],r['operands'])==(mnemonic,operands),r
    def check(label, anchors):
        for addr,mn,ops in anchors:
            instruction(addr,mn,ops)
        checks.append({'label':label,'result':'PASS','anchor_rvas':[hex(a[0]) for a in anchors]})
    check('GetFact API index uses index-1 and ten-pointer storage',[
        (0x2b227f,'lea','eax, [rdx - 1]'),
        (0x2b2287,'mov','rdi, qword ptr [rcx + rax*8 + 8]')])
    check('SetFact selects the same API index',[
        (0x350e53,'lea','eax, [rdx - 1]'),
        (0x350e56,'mov','rcx, qword ptr [rcx + rax*8 + 8]')])
    check('Save enumerates ten stores in ascending pointer order',[
        (0x2cd956f,'mov','edi, 0xa'),
        (0x2cd957e,'add','rbx, 8'),
        (0x2cd9582,'mov','rcx, qword ptr [rbx]'),
        (0x2cd9588,'call','0x142cd95b4'),
        (0x2cd958d,'lea','rbx, [rbx + 8]')])
    check('Load enumerates at most ten stores in ascending pointer order',[
        (0x7399de,'mov','edi, 1'),
        (0x739a13,'lea','ebp, [rdi + 9]'),
        (0x739a20,'mov','rcx, qword ptr [rsi]'),
        (0x739a26,'call','0x140739a68'),
        (0x739a31,'add','rsi, 8')])
    check('Native context key is current phase path hash then requested node ID',[
        (0x2b2237,'mov','dword ptr [r9 + 4], r8d'),
        (0x2b223b,'mov','ecx, dword ptr [rax + 0x80]'),
        (0x2b2244,'mov','dword ptr [r9], ecx')])
    check('Native graph FactID packs phaseHash high then hashes eight little-endian bytes',[
        (0xc97792,'mov','eax, dword ptr [rbx + 4]'),
        (0xc9779a,'mov','edx, dword ptr [rbx]'),
        (0xc9779c,'mov','r8d, 0x811c9dc5'),
        (0xc977a9,'shl','rdx, 0x20'),
        (0xc977ad,'add','rdx, rax'),
        (0xc977b0,'mov','qword ptr [rsp + 0x48], rdx'),
        (0xc977b5,'mov','edx, 8'),
        (0xc977ba,'call','0x1401efa14')])
    check('Native FNV1a32 byte XOR and prime are exact',[
        (0x1efa19,'movzx','eax, byte ptr [rcx]'),
        (0x1efa1f,'xor','eax, r8d'),
        (0x1efa22,'imul','r8d, eax, 0x1000193')])
    check('Native path hashing uses full UInt16 array and seed selected by first element',[
        (0x4e7d50,'mov','edx, dword ptr [rcx + 0xc]'),
        (0x4e7d63,'add','edx, edx'),
        (0x4e7d65,'movzx','r8d, word ptr [rcx]'),
        (0x4e7d69,'mov','r8d, dword ptr [r9 + r8*4]')])
    assert struct.unpack_from('<I',im.data,im.off(0x37015b8))[0]==0x811c9dc5
    checks.append({'label':'Root0 path hash seed equals Codeware FNV offset basis','result':'PASS','rva':'0x37015b8'})
    check('Store3 load restores disabled-node set',[
        (0x2b2170,'mov','edx, 3'),
        (0x2b2178,'call','r9'),
        (0x2b217b,'test','eax, eax'),
        (0x2b2183,'lea','r12, [r15 + 0xc8]')])
    check('Store3 writer adds disabled node and writes value1 to store3',[
        (0xc97755,'lea','rdi, [rcx + 0xc8]'),
        (0xc9778d,'call','0x140c977e8'),
        (0xc977c2,'mov','r9d, 1'),
        (0xc977ce,'lea','edx, [r9 + 2]'),
        (0xc977e1,'jmp','qword ptr [r10 + 0x18]')])
    check('Disabled-node guard bypasses execution virtual',[
        (0x2b3ae9,'lea','rcx, [rbp + 0xc8]'),
        (0x2b3afa,'call','0x140c97850'),
        (0x2b3b01,'jne','0x1402b3c6f'),
        (0x2b3b1a,'call','qword ptr [rax + 0x150]'),
        (0x2b3c6f,'mov','al, 1')])
    check('AND input mask sets socket bit and clears when all inputs received',[
        (0x9f1428,'lea','r15d, [r14 - 4]'),
        (0x9f1436,'mov','edx, r15d'),
        (0x9f144b,'bts','r9d, r13d'),
        (0x9f1454,'cmp','r9d, eax'),
        (0x9f14bc,'xor','r9d, r9d'),
        (0x9f14c8,'call','qword ptr [r10 + 0x18]')])
    check('XOR latch refuses nonzero and records first socket bit',[
        (0x14c71ed,'mov','edx, 5'),
        (0x14c71fc,'test','eax, eax'),
        (0x14c71fe,'jne','0x1414c7268'),
        (0x14c7247,'shl','r9d, cl'),
        (0x14c724a,'mov','edx, 5'),
        (0x14c7252,'call','qword ptr [r10 + 0x18]')])
    check('Logical mask reset methods explicitly zero their own stores except context mode5',[
        (0x1068994,'cmp','al, 5'),
        (0x10689db,'xor','r9d, r9d'),
        (0x10689e4,'lea','edx, [r9 + 4]'),
        (0x1076b2c,'cmp','al, 5'),
        (0x1076b73,'xor','r9d, r9d'),
        (0x1076b7c,'lea','edx, [r9 + 5]')])
    # Check class registration globals and getter links, using decoded RIP-relative byte displacements.
    def rip_target(addr):
        r=instructions[addr];b=bytes.fromhex(r['bytes'])
        return addr+len(b)+struct.unpack('<i',b[-4:])[0]
    assert rip_target(0x1620ab2)==0x3bcb1d0
    assert rip_target(0x15c8fb8)==rip_target(0x195b770)==0x3bcae28
    assert rip_target(0x1693bfa)==rip_target(0x195b730)==0x3bcae08
    for vtable, offset, target in [(0x306fa58,0x10,0x2b2270),(0x306fa58,0x18,0x350e50),
                                  (0x369d710,8,0x195b770),(0x369d710,0x158,0x9f1288),
                                  (0x369d3d0,8,0x195b730),(0x369d3d0,0x158,0x14c714c)]:
        assert struct.unpack_from('<Q',im.data,im.off(vtable+offset))[0]==im.base+target
    checks.append({'label':'Native class-registration, getter and virtual-method links agree','result':'PASS'})
    assert fnv32(b'')==0x811c9dc5 and fnv32(b'hello')==0x4f9f2cab
    assert fnv32(b'sts_ep1_03_start_community')==379570577
    packed=struct.pack('<Q',(0x12345678<<32)+0x4321)
    assert packed==bytes.fromhex('2143000078563412')
    checks.append({'label':'Independent FNV vectors, named-fact control and explicit NodeKey little-endian packing','result':'PASS',
                   'node_key_control_bytes':packed.hex(),'node_key_control_hash':fnv32(packed)})
    source_paths=[
        WORKSPACE/'AGENTS.md',WORKSPACE/'prealpha/AGENTS.md',
        WORKSPACE/'research/framework_pr63_01/codeware/src/Red/QuestsSystem.hpp',
        WORKSPACE/'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseExecutor.hpp',
        WORKSPACE/'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseRegistry.cpp',
        WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated/quest/LogicalAndNodeDefinition.hpp',
        WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated/quest/LogicalXorNodeDefinition.hpp',
        WORKSPACE/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/Generated/quest/DisableableNodeDefinition.hpp',
        WORKSPACE/'prealpha/quest_restoration_qr12/read_saves.ps1',
        WORKSPACE/'prealpha/quest_restoration_qr12/batch_001.json',
    ]
    result={'created_utc':datetime.now(timezone.utc).isoformat(),'result':'PASS_STATIC_ANCHORS_ONLY',
            'exe_sha256':im.sha,'checks':checks,'checks_count':len(checks),
            'verified_instruction_byte_spans':len(instructions),'source_inputs':[{'path':str(p.relative_to(WORKSPACE)),'sha256':sha(p)} for p in source_paths],
            'decision':'NO_SAVED_OWNER_STAGE_DECODER_JUSTIFIED',
            'not_verified':['Exact saved phase path/root binding','Pending-node/handler/queue absence','Community/prefab/spawner or ancestor lease retirement','Current live loaded save identity'],
            'save_reads':0,'game_api_calls':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    leaves=[p for p in sorted(HERE.iterdir()) if p.is_file() and p!=manifest]
    manifest.write_text(json.dumps({'result':'SEALED_LOCAL_EVIDENCE','files':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in leaves]},indent=2)+'\n',encoding='utf-8')
    print({'result':result['result'],'checks':len(checks),'byte_spans':len(instructions),'decision':result['decision']})

if __name__=='__main__':
    main()
