"""Seal reviewed exact-byte/static contracts; never touches originals for writing."""
import hashlib,json,struct
from pathlib import Path
from inspect_lock import Image,HERE
W=HERE.parents[3]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
    out=HERE/'verification_01.json';manifest=HERE/'manifest_01.json'
    assert not out.exists() and not manifest.exists()
    im=Image();rows={};functions={}
    def add(f):
        functions[f['begin_rva']]=f
        for r in f.get('instructions',[]):
            a=int(r['rva'],16);b=bytes.fromhex(r['bytes'])
            assert im.data[im.off(a):im.off(a)+len(b)]==b
            assert a not in rows or rows[a]==r
            rows[a]=r
    for p in sorted(HERE.glob('native_*.json')):
        x=json.loads(p.read_text());assert x['exe_sha256']==im.sha
        for f in x.get('functions',[])+x.get('explicit_spans',[]):add(f)
    reused=HERE.parent/'native_22.json'
    x=json.loads(reused.read_text());assert x['exe_sha256']==im.sha
    for f in x['functions']:add(f)
    for f in json.loads((HERE/'save_header_candidates_01.json').read_text())['functions']:add(f)
    phase=json.loads((HERE/'phase_type_01.json').read_text())
    for f in [phase['registration'],phase['getter']]+list(phase['methods'].values()):add(f)
    stream=json.loads((HERE/'stream_version_binding_01.json').read_text())
    for c in stream['candidates']:add(c['instructions'])
    checks=[]
    def ck(label,anchors):
        for a,m,o in anchors:assert (rows[a]['mnemonic'],rows[a]['operands'])==(m,o),rows[a]
        checks.append({'label':label,'result':'PASS','anchors':[hex(a[0]) for a in anchors]})
    ck('Native exclusive byte CAS and release match SDK protocol',[
       (0x22ca321,'lea','esi, [rbp - 1]'),(0x22ca32b,'xor','eax, eax'),
       (0x22ca32d,'lock cmpxchg','byte ptr [rbx], sil'),(0x19417f5,'xchg','byte ptr [rax], dl')])
    ck('Ordinary path wrapper locks QuestsSystem60 before dispatch',[
       (0xbea6ea,'lea','rdx, [rcx + 0x60]'),(0xbea6f8,'call','0x141ffad60'),
       (0xbea79e,'call','qword ptr [rax + 0x120]'),(0xbea85a,'call','0x1419417f0')])
    ck('Root replacement writes handles',[(0x35f48c,'mov','qword ptr [rsi + 0x70], rcx'),
       (0x35f4a0,'mov','qword ptr [rsi + 0x68], rdx')])
    assert not any(r['mnemonic']=='call' and r['operands'] in ['0x141ffad60','0x1422ca300'] for r in functions['0x35f430']['instructions'])
    checks.append({'label':'No local exclusive-lock helper call in reviewed root replacement body; outer lifecycle remains unknown','result':'PASS_BOUNDARY'})
    ck('Teardown releases lock before global NodePathMap clearing',[
       (0x35eb25,'mov','qword ptr [rbx + 0x68], rsi'),(0x35eb35,'xchg','byte ptr [rax], cl'),
       (0x35eb37,'lea','rcx, [rbx + 0x78]'),(0x35eb3b,'call','0x140b263ec')])
    ck('CutControl emits cut command before ordinary Out',[
       (0x975309,'mov','byte ptr [rbp - 8], 2'),(0x97531b,'call','0x1401cc5ac'),
       (0x97532d,'mov','byte ptr [rbp - 8], 0'),(0x97533b,'call','0x1401cc5ac'),
       (0x975360,'mov','byte ptr [rbp - 8], 3')])
    ck('Pending output queue is FIFO and destination commands drain first',[
       (0x352c27,'mov','r8, qword ptr [rcx]'),(0x352c2e,'mov','rax, qword ptr [r8]'),
       (0x352c57,'call','0x140352b00'),(0x352b61,'lea','rsi, [rcx + 0x20]'),
       (0x352bc5,'call','0x14021ca80'),(0x352b27,'dec','dword ptr [rdi + 0xc]'),
       (0x352a01,'cmp','dword ptr [rbp + 0xb], ebx'),(0x352a10,'call','0x1402b393c'),
       (0x352a1d,'cmp','dword ptr [rbp + 0xb], ebx'),(0x352a3b,'call','0x140352bfc')])
    ck('Special cut signals invoke phase stop virtual178',[
       (0x2b3ca9,'mov','r9b, 1'),(0x2b3cac,'xor','r8d, r8d'),
       (0x2b3caf,'call','qword ptr [rax + 0x178]'),(0x2b3cc2,'call','qword ptr [r10 + 0x178]')])
    ck('Phase stop requests child stop/removal before base cleanup',[
       (0xbec7cd,'call','qword ptr [rax + 0x48]'),(0xbec805,'jmp','0x1402fda9c')])
    ck('Child stop recursively cleans before erasing registration',[
       (0xbec8a6,'call','0x1402b1d30'),(0xbec8e0,'lea','rcx, [rbx + 0x88]'),
       (0xbec8e7,'call','0x1401cafc4')])
    ck('Handler removal calls Uninitialize20 then hash-map erase',[
       (0x2fcf77,'call','qword ptr [rax + 0x20]'),(0x2fcf90,'call','0x1402fd024'),
       (0x2fd0b3,'dec','dword ptr [rdi + 8]')])
    ck('Root path first UInt16 directly indexes root.Children',[
       (0xbea3f7,'movzx','r10d, word ptr [rax]'),(0xbea3fb,'shl','r10, 4'),
       (0xbea3ff,'add','r10, qword ptr [rcx + 0x88]')])
    ck('Resource index comes from ordered context array search',[
       (0x1266558,'mov','rax, qword ptr [rdx + 0x18]'),
       (0x1266577,'cmp','qword ptr [rax], r8'),(0x1266582,'sub','rax, rdx'),
       (0x1266585,'sar','rax, 3'),(0x2c9c341,'call','0x141266558'),
       (0x2c9c37e,'mov','word ptr [rsp + 0x28], r14w')])
    ck('Untagged resource array lies after FactsDB and before customArray',[
       (0x2c9f3bf,'call','qword ptr [rax + 0x48]'),(0x2c9f3c2,'lea','rdx, [r14 + 0xa8]'),
       (0x2c9f3d4,'call','0x14073ad98'),(0x2c9f3dd,'call','0x141921b08'),
       (0x739619,'cmp','eax, 0x8b'),(0x739624,'lea','rdx, [rdi + 0xa8]')])
    ck('Native array count uses signed VLQ then UInt64 byte transfer',[
       (0x1041726,'call','0x14027b824'),(0x73adba,'shl','r8d, 3'),
       (0x27b85c,'and','ebx, 0x3f'),(0x27b85f,'and','sil, 0x80'),
       (0x27b863,'test','al, 0x40')])
    ck('Stream version getter reads SaveVersion field298',[
       (0x3e9c70,'mov','rax, qword ptr [rcx + 0xe0]'),
       (0x3e9c77,'mov','eax, dword ptr [rax + 0x298]'),
       (0xfa5607,'lea','rsi, [rcx + 0x298]'),(0xfa5620,'call','qword ptr [rax + 0x10]'),
       (0xfa5626,'lea','rbp, [rdi + 0x29c]'),(0xfa5639,'call','qword ptr [rax + 0x10]'),
       (0xfa563c,'cmp','dword ptr [rsi], 0x115'),(0xfa5648,'cmp','dword ptr [rbp], 0x9c4')])
    assert struct.unpack_from('<Q',im.data,im.off(0x30ad578+0x48))[0]==im.base+0x3e9c70
    assert struct.unpack_from('<Q',im.data,im.off(0x30ad578+0x68))[0]==im.base+0xfa507c
    ck('Same reader class loads header separately from ArchiveVersion',[
       (0xfa50aa,'call','0x140fa5548'),(0xfa557f,'call','0x140fa55f0'),
       (0xfa55cf,'mov','dword ptr [rbx + 0xc], ecx')])
    strict=json.loads((HERE/'root_array_controls_01.json').read_text())
    assert strict['controls_count']==16 and all(c['result']=='PASS' for c in strict['controls'])
    header=strict['header_artifact']['data'];assert header['save_version']==277>=139
    root=json.loads((HERE/'root_binding_decode_01.json').read_text())
    assert root['source_body_sha256']==header['source_sha256']
    assert root['ep1_root_index']==1 and root['startup_path']==[1,0,10,5,2,50,19,5,1]
    assert root['startup_phase_path_hash_u32']=='2698350362'
    checks.append({'label':'Same-body exact root index/path binding and 16 strict count/array controls','result':'PASS'})
    inputs=[W/'research/framework_pr63_01/codeware/src/Red/QuestsSystem.hpp',
       W/'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseExecutor.hpp',
       W/'research/framework_pr63_01/codeware/src/App/Quest/QuestsSystemEx.hpp',
       W/'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseRegistry.cpp',
       W/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/SharedSpinLock.hpp',
       W/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/SharedSpinLock-inl.hpp',
       W/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/ResourcePath.hpp',
       W/'tools/parity_audit/common.py',W/'tools/parity_audit/model.py',reused]
    result={'result':'PASS_STATIC_REVIEW_AND_EXACT_OFFLINE_BINDING','exe_sha256':im.sha,
       'checks_count':len(checks),'checks':checks,'verified_instruction_byte_spans':len(rows),
       'inputs':[{'path':str(p.relative_to(W)),'sha256':sha(p)} for p in inputs],
       'closed':['Ordinary lock protocol and sampled mutation chain','CutControl cut-destination dispatch precedes Out through FIFO queues','Recursive handler Uninitialize/map erase and child registration removal','Exact saved EP1 root index1 and Jason startup path','Native version query maps to SaveVersion277'],
       'unknown':['Manual CET lifecycle/thread transition safety','External prefab/community/spawner lease completion','Exact current live body binding','Prepared pending-handler stage'],
       'live_inspector_readiness':'BLOCKED_NOT_PREPARED','original_save_reads':0,'game_api_calls':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest.write_text(json.dumps({'files':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(HERE.iterdir()) if p.is_file() and p!=manifest]},indent=2)+'\n',encoding='utf-8')
    print({'result':result['result'],'checks':len(checks),'byte_spans':len(rows),'strict_controls':16,'live_inspector':'BLOCKED_NOT_PREPARED'})

if __name__=='__main__':main()
