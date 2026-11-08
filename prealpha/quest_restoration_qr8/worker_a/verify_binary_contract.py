"""Source-bounded semantic checks against installed ArchiveXL instructions.

No DLL loading or execution. Negative controls mutate captured bytes in memory;
the same disassembly checks must reject changed integration behavior.
"""
from inspect_archivexl import *

def fnv64(text):
 n=0xcbf29ce484222325
 for v in text.encode():n=((n^v)*0x100000001b3)&0xffffffffffffffff
 return n
def verify(data,x):
 checks=[]
 def ck(name,b,rv=None):
  assert b,name
  checks.append({'name':name,'rva':rv,'pass':True})
 def at(r):
  off=x.off(r);return next(x.md.disasm(data[off:off+15],x.base+r,count=1))
 def op(r,m,s):
  i=at(r);ck(m+' '+s,i.mnemonic==m and i.op_str==s,hex(r));return i
 def rip(r):
  i=at(r);v=[o for o in i.operands if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP];assert len(v)==1,hex(r)
  return i.address+i.size+v[0].mem.disp-x.base
 def target(r):
  i=at(r);assert i.operands[-1].type==capstone.x86.X86_OP_IMM
  return i.operands[-1].imm-x.base
 # A source function is identified by independent method/name/vtable/hook anchors.
 ck('QuestPhase GetName exact literal',data[x.off(rip(0xf4de0)):x.off(rip(0xf4de0))+11]==b'QuestPhase\0',hex(0xf4de0))
 namep=struct.pack('<Q',x.base+0xf4de0);refs=[m.start() for m in re.finditer(re.escape(namep),data)]
 ck('unique QuestPhase GetName virtual table and adjacent Load',len(refs)==1 and struct.unpack_from('<Q',data,refs[0]+8)[0]==x.base+0xf4ea0,hex(x.rva(refs[0])))
 for label,aid,loadid,callbacklea,store,wrapper,wrapcall,wraporiginal,originlea,cb in [
  ('preload',0x2f1f26cc,0xf4f1e,0xf4ecb,0xf4ed2,0xf4e00,0xf4e18,0xf4e36,0xf4f5b,0xf5f40),
  ('restore',0x7a20106e,0xf5025,0xf4fd2,0xf4fd9,0xf4e80,0xf4e89,0xf4e97,0xf5062,0xf5a10),
  ('root start',0x2f8e2179,0xf512c,0xf50d9,0xf50e0,0xf4e40,0xf4e58,0xf4e76,0xf5169,0xf6160)]:
  op(loadid,'mov',f'edx, {hex(aid)}')
  ck(label+' callback address installed by Load',rip(callbacklea)==cb and at(store).mnemonic=='mov',hex(callbacklea))
  ck(label+' wrapper calls exact callback slot before native original',rip(store)==rip(wrapcall) and rip(originlea)==rip(wraporiginal) and at(wrapcall).mnemonic=='call' and at(wraporiginal).mnemonic=='jmp',hex(wrapcall))
  # r8 passed to actual hook provider must be this wrapper, with r9 native trampoline slot.
  lea={'preload':0xf4eed,'restore':0xf4ff4,'root start':0xf50fb}[label]
  ck(label+' wrapper is actual hook-provider argument r8',at(lea).op_str.startswith('r8, ') and rip(lea)==wrapper,hex(lea))
 op(0xf5a3e,'lea','rsi, [rcx + 0x78]')
 op(0xf5ac5,'mov','ecx, dword ptr [r9 + 0xb4]')
 op(0xf5ad0,'mov','rdx, qword ptr [r9 + 0xa8]')
 op(0xf5ae3,'cmp','qword ptr [rdx + rax*8], r8')
 op(0xf5af8,'jae',hex(x.base+0xf5eaf))
 op(0xf5b1f,'mov','r9d, 0x811c9dc5')
 op(0xf5b48,'imul','r9d, eax, 0x1000193')
 op(0xf5b5f,'cmp','dword ptr [rsi + 8], 0')
 op(0xf5bb3,'call',hex(x.base+0xef9c0))
 op(0xf5c0d,'mov','dword ptr [rbp - 0x69], r9d')
 op(0xf5c11,'movzx','eax, word ptr [rax]')
 op(0xf5c14,'mov','dword ptr [rbp - 0x65], eax')
 op(0xf5c1a,'shl','r8, 0x20')
 op(0xf5cab,'imul','edx, eax, 0x1000193')
 op(0xf5cb4,'mov','rcx, qword ptr [r13 + 0xf8]')
 op(0xf5cc1,'mov','edx, 1')
 op(0xf5cc6,'call','qword ptr [rax + 0x10]')
 op(0xf5cc9,'test','eax, eax')
 op(0xf5ccb,'jne',hex(x.base+0xf5e1b))
 literal=rip(0xf5cd1);ck('zero-receipt route constructs literal In1 socket only',data[x.off(literal):x.off(literal)+4]==b'In1\0',hex(literal))
 op(0xf5d94,'mov','dword ptr [rbp - 0x7d], 1')
 op(0xf5da2,'mov','r9, qword ptr [rax + 0x240]')
 op(0xf5da9,'lea','r8, [rsp + 0x30]')
 op(0xf5dae,'lea','rdx, [rbp - 0x69]')
 op(0xf5db2,'mov','rcx, r13')
 op(0xf5db5,'call','r9')
 op(0xf5db8,'mov','rcx, qword ptr [r13 + 0xf8]')
 op(0xf5dc2,'mov','r9d, 1')
 op(0xf5dc8,'mov','r8d, dword ptr [rbp + 0x6f]')
 op(0xf5dcc,'mov','edx, r9d')
 op(0xf5dcf,'call','qword ptr [rax + 0x18]')
 # Normal-root callback computes same context-bound hash and records the receipt.
 op(0xf618a,'mov','rax, qword ptr [rdx + 0x128]')
 op(0xf61f8,'mov','ecx, dword ptr [rax + 0xb4]')
 op(0xf6202,'mov','rdx, qword ptr [rax + 0xa8]')
 op(0xf6253,'mov','r12d, 0x811c9dc5')
 op(0xf6278,'imul','r12d, ecx, 0x1000193')
 op(0xf62d3,'shl','r8, 0x20')
 op(0xf62d7,'movzx','eax, word ptr [rax]')
 op(0xf635f,'imul','r8d, eax, 0x1000193')
 op(0xf6366,'mov','rcx, qword ptr [rbp + 0xf8]')
 op(0xf6370,'mov','edx, 1')
 op(0xf6375,'mov','r9d, edx')
 op(0xf6378,'call','qword ptr [rax + 0x18]')
 (s,e),_=x.dis(0xf6160);allins=list(x.md.disasm(data[x.off(s):x.off(s)+e-s],x.base+s))
 ck('ordinary-root callback contains no virtual ForceStartNode dispatch',not any(i.mnemonic=='call' and '0x240' in i.op_str for i in allins),hex(s))
 # Actual CRC pipeline and collision refusal, copied-node persistent identities.
 op(0xf44b1,'mov','r14d, 0xffff');op(0xf44c4,'shr','cx, 8');op(0xf44c8,'xor','cl, byte ptr [rdx]');op(0xf44d1,'shr','al, 4')
 op(0xf44e4,'shl','r14w, 3');op(0xf44ed,'shl','r14w, 5');op(0xf463b,'cmp','word ptr [rcx + 0x40], r14w');op(0xf4640,'je',hex(x.base+0xf4725))
 # Streaming config postconfigure calls path-registry RegisterPatch for main world.
 op(0x130a1e,'movabs','rbx, '+hex(fnv64(r'base\worlds\03_night_city\_compiled\default\03_night_city.streamingworld')))
 op(0x130a2d,'lea','rsi, [rbp + 0x50]');op(0x130a5d,'mov','rcx, rbx');op(0x130a60,'call',hex(x.base+0x122630))
 op(0x122692,'call',hex(x.base+0x134ee0));op(0x12269d,'call',hex(x.base+0x122440))
 op(0x122581,'call',hex(x.base+0x57870));op(0x122591,'call',hex(x.base+0x112b90));op(0x1225bb,'mov','qword ptr [rdx], rax');op(0x1225be,'mov','qword ptr [rdx + 8], rbx');op(0x1225c2,'add','qword ptr [rcx + 0x10], 0x10')
 # Resource-ready dispatch only enters world merge for matching RTTI name/hash.
 op(0x1204eb,'movabs','rax, '+hex(fnv64('worldStreamingWorld')))
 op(0x1204f5,'cmp','rcx, rax');op(0x1204f8,'jne',hex(x.base+0x1206dc));op(0x1205b5,'call',hex(x.base+0x120bb0))
 op(0x120c68,'call',hex(x.base+0x10a570));op(0x120c73,'test','rbx, rbx');op(0x120c76,'jne',hex(x.base+0x120d0e))
 op(0x120d1d,'lea','rdx, [rsp + 0x70]');op(0x120d22,'lea','rcx, [rdi + 0x70]');op(0x120d26,'call',hex(x.base+0x106ec0))
 op(0x120d41,'mov','rcx, qword ptr [rax + 0x48]');op(0x120d45,'mov','qword ptr [r8], rcx')
 op(0x120d71,'mov','qword ptr [r8 + 8], rax');op(0x120d7e,'mov','qword ptr [r8 + 0x10], rdx')
 return checks

def main():
 out=HERE/'binary_verification_01';out.mkdir(exist_ok=False);x=Binary(DLL)
 assert x.sha=='C07DA66DF4E4D57401FA3DF0F6288F3B780F01102A98807B6ADAABAEF45F69BF'
 checks=verify(x.b,x);controls=[]
 mutations=[('bypass_existing_receipt',0xf5ccb,b'\x90'*6),('wrong_callback',0xf4fd2,b'\x48\x8d\x05'+struct.pack('<i',0xf6160-(0xf4fd2+7))),('wrong_force_start_vslot',0xf5da2,bytes.fromhex('4c8b8848020000')),('zero_receipt_write',0xf5dc2,bytes.fromhex('41b900000000')),('wrong_socket',0x17d87c,b'In2\0'),('wrong_main_world',0x130a1e,bytes.fromhex('48bb9d5e2abbb4011161'))]
 for name,r,rep in mutations:
  m=bytearray(x.b);before=bytes(m[x.off(r):x.off(r)+len(rep)]);m[x.off(r):x.off(r)+len(rep)]=rep
  try:verify(bytes(m),x)
  except AssertionError as err:controls.append({'name':name,'rva':hex(r),'before':before.hex(),'after':rep.hex(),'caught_by':str(err),'pass':True})
  else:raise AssertionError('missed mutant '+name)
 pins=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted((HERE/'source_v1_28_0').glob('*'))]
 evidence={'status':'PASS_BOUNDED_INSTALLED_BINARY_SOURCE_MECHANISM_CORRESPONDENCE_PENDING_PEER','checks':len(checks),'negative_controls':len(controls),'input':x.freshness(),'source_pins':pins,'source_url_prefix':'https://raw.githubusercontent.com/psiberx/cp2077-archive-xl/v1.28.0/src/','bound_methods':{'QuestPhase GetName':'0xF4DE0','QuestPhase Load':'0xF4EA0','OnPhasePreload':'0xF5F40','PatchPhase':'0xF6470','CreatePhaseNode/CRC':'0xF42B0','OnGameRestored':'0xF5A10','OnQuestStart':'0xF6160','restore_hook_wrapper':'0xF4E80','WorldStreaming PostConfigure':'0x130A00','ResourcePatch RegisterPatch(char*)':'0x122630','ResourcePatch RegisterPatch(ResourcePath)':'0x122440','ResourcePatch OnResourceReady':'0x120430','ResourcePatch OnStreamingWorldLoad':'0x120BB0'},'conclusions':['The installed DLL actually installs the relevant exact-address-ID callback and preserves callback-before-native ordering. It searches the saved quest list for the registered parent path rather than assuming a fixed quest index.','Actual code derives private engine receipt from root quest-index hash and generated phase ID; existing nonzero receipt skips startup. The zero route starts literal In1 through QuestsSystem virtual slot0x240 then writes receipt store1/value1. Normal-root start records same derived receipt without ForceStart dispatch.','Current DLL explicitly registers streaming.blocks through the ResourcePatch main-world target, and the resource-ready world type dispatch appends path/token refs to native blockRefs. This is not an unfiltered sector/prefab owner.'],'limits':['No matching developer PDB or reproducible full-DLL build is claimed: methods are bound by actual instructions, unique GetName/vtable adjacency, callback-slot dataflow, source address IDs, ABI offsets and typed merge dispatch.','This proves the bounded DLL mechanism, not successful runtime address resolution, hook installation/scheduling, native QuestsSystem virtual implementation, fact serialization or marker acquisition/release in a particular save. Those need controlled live diagnostics.','No full binary equivalence to upstream1.28.0 is asserted; unrelated extension code is outside this analysis.','No native/external named-fact hash collision census or full world-global collision census is claimed. Generated phase ID namespace is independently checked.'],'runtime_load_or_execution':False,'runtime_writes':0,'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()}
 for n,d in [('evidence.json',evidence),('checks.json',checks),('controls.json',controls)]: (out/n).write_text(json.dumps(d,indent=2),encoding='utf8')
 print(json.dumps({'status':evidence['status'],'checks':len(checks),'controls':len(controls),'output':str(out)},indent=2))
if __name__=='__main__':main()
