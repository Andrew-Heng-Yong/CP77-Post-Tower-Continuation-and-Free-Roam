"""Bounded B0 support versus actual native trigger-resolution boundary."""
from inspect_archivexl import *
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
def main():
 out=HERE/'trigger_boundary_01';out.mkdir(exist_ok=False);x=Binary(Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe'));checks=[]
 def ck(n,b,r=None):checks.append({'name':n,'pass':bool(b),'rva':r});assert b,n
 def op(r,m,s):
  ins=next(x.md.disasm(x.b[x.off(r):x.off(r)+15],x.base+r,count=1));ck(m+' '+s,ins.mnemonic==m and ins.op_str==s,hex(r));return ins
 op(0x1c21fd,'mov','qword ptr [rcx], rax');ck('actual final class vtable is TriggerCondition',0x1c21ef+7+struct.unpack_from('<i',x.b,x.off(0x1c21ef)+3)[0]==0x302bc80)
 ck('final native virtual evaluate slotF0 targets actual handler',struct.unpack_from('<Q',x.b,x.off(0x302bc80)+0xf0)[0]-x.base==0x7c2390)
 op(0x7c23b3,'cmp','byte ptr [rcx + 0x38], 3');op(0x7c23de,'mov','r8, qword ptr [rax]');op(0x7c23e1,'call',hex(x.base+0x2ac524));op(0x7c23e6,'mov','r8, qword ptr [r14 + 0x1e0]');op(0x7c2404,'call',hex(x.base+0x2fc8b8))
 op(0x7c240d,'cmp','qword ptr [rbp - 0x39], rbx');op(0x7c2411,'je',hex(x.base+0x7c2632));op(0x7c2632,'xor','edx, edx');op(0x7c2638,'call',hex(x.base+0x7c2668))
 op(0x7c266b,'mov','cl, byte ptr [rax + 0x38]');op(0x7c266e,'lea','eax, [rcx - 3]');op(0x7c2675,'mov','al, dl')
 op(0x2fc8ca,'cmp','qword ptr [rcx], 0');op(0x2fc8f6,'mov','rax, qword ptr [r9]');op(0x2fc903,'call','qword ptr [rax + 0x190]');op(0x2fc925,'call',hex(x.base+0x18a5a4))
 # Preserve complete selector span beyond split .pdata bounds for peer inspection.
 ins=list(x.md.disasm(x.b[x.off(0x7c2668):x.off(0x7c2668)+40],x.base+0x7c2668));(out/'selector.asm').write_text('\n'.join(f'{i.address-x.base:08X}: {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf8')
 B=ROOT/'prealpha/quest_restoration_qr8/worker_b';rows=load(B/'readback_01/manifest.json');b0=next(r for r in rows if r['depot']==r'towercontinued\b0_story_eight\ronald.questphase');native=next(r for r in rows if r['depot'].endswith('q302_ronald_tree.questphase'))
 for r in [b0,native]:ck('typed source pin '+r['depot'],hashlib.sha256(Path(r['json']).read_bytes()).hexdigest().upper()==r['json_sha256'])
 bm=Resource(load(b0['json'])).normalize();nm=Resource(load(native['json'])).normalize()
 ck('B0 literally omits root and child5 support prefabs',not bm['root_prefabs'] and not bm['graphs']['root']['nodes']['5']['prefabs'])
 ck('native literal bar lease retained in original source',any('#q302_pr_bar' in v for v in nm['root_prefabs']))
 inside=[v for v in walk(load(b0['json'])) if v.get('$type')=='questTriggerCondition' and v.get('type')=='IsInside'];ck('B0 requests literal original area02',any(v['triggerAreaRef'].get('$value')=='#q302_tr_ronald_area_02' for v in inside))
 spot=load(B/'tree_persistent_workspot_01.json');s=spot['hits'][0][1];ck('actual persistent workspot remains enabled under exact native tree global',spot['hits'][0][0]==47255 and s['$type']=='AISpotPersistentData' and s['globalNodeId']['hash']=='7106761085964620863' and s['isEnabled']==1)
 limits=['The resolver makes an actual dynamic service call at virtual0x190 through context+0x1E0. Its exact current implementation/side effects have not been bound here. Implicit world-support acquisition or cached reconstruction is NOT proved absent.','The local evaluator has a proved missing-reference→false path for IsInside3. A particular supported save reaching that null result is not observed.','AISpotPersistentData proves retained workspot identity/enabled position/yaw. It does not prove actor presence or absence, nor native area volume acquisition.','The explicit missing B0 bar lease is a literal source difference/ownership-support omission. Runtime trigger availability is UNKNOWN; no unconditional missing-actor/trigger claim or repair is approved.','QR7 private two-trigger lease has distinct full refs/globals; it is not evidence that B0 original short NodeRef resolves through that private support.']
 result={'status':'SOURCE_SUPPORT_OMISSION_PROVEN_RUNTIME_IMPLICIT_ACQUISITION_UNKNOWN','input':x.freshness(),'checks':checks,'native_resolution_boundary':{'evaluation':'0x7C2390','missing_reference_branch':'0x7C240D→0x7C2632','selector':'0x7C2668','resolver':'0x2FC8B8','unbound_service_vslot':'0x190','service_context_offset':'0x1E0'},'source_rows':[b0,native],'persistent_workspot_evidence':str(B/'tree_persistent_workspot_01.json'),'persistent_workspot_evidence_sha256':hashlib.sha256((B/'tree_persistent_workspot_01.json').read_bytes()).hexdigest().upper(),'limits':limits,'candidate_or_runtime_writes':0}
 (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print({'status':result['status'],'checks':len(checks),'unbound':'service0x190 acquisition effects','output':str(out)})
if __name__=='__main__':main()
