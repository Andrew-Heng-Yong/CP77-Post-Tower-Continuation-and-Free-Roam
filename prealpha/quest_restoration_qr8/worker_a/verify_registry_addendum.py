"""Narrow native registry missing-node branch; runtime availability is not inferred."""
from inspect_archivexl import *
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
 out=HERE/'trigger_registry_addendum_01';out.mkdir(exist_ok=False);x=Binary(Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe'));checks=[]
 def op(r,m,s):
  a=next(x.md.disasm(x.b[x.off(r):x.off(r)+15],x.base+r,count=1));assert a.mnemonic==m and a.op_str==s,(hex(r),a.mnemonic,a.op_str);checks.append({'rva':hex(r),'instruction':m+' '+s,'pass':True})
 M=load(HERE/'world_registry_01/manifest.json');c=M['hits'][0]['candidates'][0];assert struct.unpack_from('<Q',x.b,x.off(c['instance_vtable'])+0x190)[0]-x.base==0x2fc61c
 op(0x3c7e17,'mov','rax, qword ptr [rdi + 0x78]');op(0x3c7e1b,'mov','rcx, qword ptr [rax + 0x230]');op(0x3c7e22,'mov','qword ptr [rbx + 0x1e0], rcx')
 op(0x2fc638,'xor','r15d, r15d');op(0x2fc644,'test','r8, r8');op(0x2fc649,'mov','qword ptr [rdx], r15');op(0x2fc64c,'mov','qword ptr [rdx + 8], r15')
 op(0x2fc652,'lea','r14, [rcx + 0x48]');op(0x2fc659,'call',hex(x.base+0x22ca420));op(0x2fc65e,'movzx','r13d, bx');op(0x2fc671,'mov','eax, dword ptr [r13]');op(0x2fc678,'je',hex(x.base+0x2fc699));op(0x2fc687,'cmp','qword ptr [rsi], rbx');op(0x2fc69c,'call',hex(x.base+0x1ffad90));op(0x2fc6a1,'mov','qword ptr [rdi], r15');op(0x2fc6a4,'mov','qword ptr [rdi + 8], r15')
 op(0x2fc6cf,'test','rax, rax');op(0x2fc6d2,'je',hex(x.base+0x2fc742));op(0x2fc6e1,'lock cmpxchg','dword ptr [rdx], ecx');op(0x2fc76c,'mov','qword ptr [rsi], r14');op(0x2fc78c,'mov','qword ptr [rdi], r14');op(0x2fc78f,'mov','qword ptr [rdi + 8], r14')
 helpers=[]
 for r in [0x22ca420,0x1ffad90]:
  (s,e),ins=x.dis(r);p=out/f'helper_{s:08x}.asm';p.write_text('\n'.join(f'{a.address-x.base:08X}: {a.bytes.hex():<30} {a.mnemonic} {a.op_str}' for a in ins)+'\n',encoding='utf8');helpers.append({'rva':s,'end':e,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()})
 result={'status':'PROVEN_EXPECTED_NATIVE_REGISTRY_MISSING_ENTRY_RETURNS_NULL_WITHOUT_RECONSTRUCTION','input':x.freshness(),'checks':checks,'class':'worldNodeInstanceRegistry','instance_vtable':hex(c['instance_vtable']),'FindNode_vslot':'0x190','FindNode_rva':'0x2FC61C','helpers':helpers,'conclusion':'Exact current registry FindNode searches existing ID buckets/weak handles. Empty/missing entry yields null. An expired weak entry is removed and yields null, rather than constructing a new node. Local expected-registry path supplies no implicit bar-geometry acquisition.','source_corroboration':str(ROOT/'research/framework_pr63_01/archivexl/src/Red/WorldNode.hpp'),'remaining':['Quest context+0x1E0 is traced from GameInstance+0x78→internal systems+0x230, but that field’s concrete startup object/type registration is not independently bound by this addendum. Source WorldNode.hpp and matching slot semantics corroborate the expected registry; no universal dynamic-instance assertion is made.','Whether original trigger nodes are registered under another owner, warm cache, saved world state or external mod in a particular save remains UNKNOWN. Neither workspot presence nor omitted explicit lease answers that.','This does not approve an unfiltered bar owner or prove actor absence. B0 source omission and runtime availability remain separate dispositions.'],'candidate_or_runtime_writes':0}
 (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print({'checks':len(checks),'helpers':helpers,'status':result['status']})
if __name__=='__main__':main()
