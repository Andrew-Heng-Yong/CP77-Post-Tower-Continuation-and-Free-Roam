"""QR8 five-UNKNOWN targeted verification. Static bytecode only; no native execution.

Independent known-answer fixtures exercise actual decoded branch instructions.
The small scalar interpreter does not emulate the engine, inventory, or a save.
"""
import argparse,copy,re,struct,sys,collections,hashlib
from pathlib import Path
from prepare import ROOT,HERE,Q7,GAME,read,sha,write
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
from common import walk,value
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone

class Scalar:
    """Only scalar branch/compare operations used in three bounded native prefixes."""
    aliases={'eax':('rax',32),'al':('rax',8),'ecx':('rcx',32),'cl':('rcx',8),'edx':('rdx',32),'dl':('rdx',8),'r8d':('r8',32)}
    def __init__(self,code,start,regs=None,mem=None):
        md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
        self.ins={x.address:x for x in md.disasm(code,start)};self.r=dict(regs or {});self.mem=dict(mem or {});self.z=self.c=False
    def reg(self,n):
        root,bits=self.aliases.get(n,(n,64));return self.r.get(root,0)&((1<<bits)-1)
    def put(self,n,v):
        root,bits=self.aliases.get(n,(n,64));mask=(1<<bits)-1
        self.r[root]=(v&mask) if bits>=32 else ((self.r.get(root,0)&~mask)|(v&mask))
    def get(self,x,o):
        if o.type==capstone.x86.X86_OP_REG:return self.reg(x.reg_name(o.reg))
        if o.type==capstone.x86.X86_OP_IMM:return o.imm
        assert o.type==capstone.x86.X86_OP_MEM and not o.mem.index
        a=self.reg(x.reg_name(o.mem.base))+o.mem.disp
        return sum(self.mem.get(a+i,0)<<(8*i) for i in range(o.size))
    def run(self,start,stops=None):
        pc=start;trace=[]
        for _ in range(60):
            if stops and pc in stops:return stops[pc],trace
            x=self.ins[pc];m=x.mnemonic;o=x.operands;trace.append(pc);n=pc+x.size
            if m=='ret':return self.reg('al'),trace
            if m in ('mov','xor','sub'):
                assert o[0].type==capstone.x86.X86_OP_REG
                v=self.get(x,o[1])
                if m=='xor':v=self.get(x,o[0])^v
                elif m=='sub':
                    old=self.get(x,o[0]);self.c=old<v;v=old-v
                self.put(x.reg_name(o[0].reg),v)
                if m!='mov':self.z=self.get(x,o[0])==0
            elif m in ('cmp','test'):
                a,b=self.get(x,o[0]),self.get(x,o[1]);self.z=(a==b) if m=='cmp' else (a&b)==0;self.c=(a<b) if m=='cmp' else False
            elif m in ('je','jne','jmp'):
                if m=='jmp' or (m=='je' and self.z) or (m=='jne' and not self.z):n=o[0].imm
            elif m in ('seta','setae','sete','setb','setbe'):
                v={'seta':not self.c and not self.z,'setae':not self.c,'sete':self.z,'setb':self.c,'setbe':self.c or self.z}[m]
                self.put(x.reg_name(o[0].reg),int(v))
            else:raise AssertionError(('unimplemented bounded instruction',m,x.op_str,hex(pc)))
            pc=n
        raise AssertionError('bounded interpreter did not terminate')

def memory(*rows):
    return {a+i:(v>>(8*i))&255 for a,v,size in rows for i in range(size)}

def main(out):
    assert out.resolve().is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
    checks=[];mutants=[];pins=[]
    def ck(name,ok,evidence=None):
        checks.append({'check':name,'pass':bool(ok),'evidence':evidence});assert ok,name
    def pin(p,expected=None):
        p=Path(p);h=sha(p);ck('Pinned input '+str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p),expected is None or h==expected)
        pins.append({'path':str(p),'sha256':h});return p
    base=read(pin(HERE/'baseline_01/baseline.json'));original=read(pin(HERE/'baseline_01/original_five_contracts.json'))
    ck('Exactly five original UNKNOWN rows',len(original)==5 and all(x['status']=='UNKNOWN' for x in original))
    for r in base['targeted_sources']:pin(r['path'],r['sha256'])
    for r in base['native_inputs']:pin(r['path'],r['sha256'])
    cap=read(pin(HERE/'capture_01/manifest.json'));rows={r['depot']:r for r in cap['resources']};models={};objs={}
    for d,r in rows.items():
        pin(r['raw'],r['raw_sha256']);pin(r['json'],r['json_sha256']);objs[d]=read(r['json'])
        if d.endswith(('.questphase','.scene')):models[d]=Resource(objs[d]).normalize()
    ck('Eight unique fresh provider targets, zero ambiguous providers',len(rows)==8 and len(cap['resources'])==8 and all(r['status']=='EXPORTED' for r in cap['resources']))
    ck('No whole large archive SHA operation',cap['large_archive_sha_operations']==0)
    ex=read(pin(HERE/'exterior_capture_01/manifest.json'))
    opaque=[]
    for r in ex['resources']:
        pin(r['raw'],r['raw_sha256']);opaque.append({'depot':r['depot'],'raw_sha256':r['raw_sha256'],'error':r.get('error'),'provider':r['provider'],'provider_metadata':r['provider_metadata']})
    ck('Three bounded nearest exterior candidates stop at exact unsupported worldNode format',len(opaque)==3 and all(r['status']=='OPAQUE' and 'DynamicBaseClass' in r['error'] and 'worldNode' in r['error'] for r in ex['resources']))
    # Each new capture is checked against its exact current executable byte ranges.
    exe=GAME/'bin/x64/Cyberpunk2077.exe';binary=exe.read_bytes();pe=pefile.PE(data=binary,fast_load=True)
    def raw(rva,n):return binary[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(rva)+n]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
    manifests=['inventory_native_02','device_native_01','hub_native_01','native_followup_01','native_followup_02','context_native_01','context_native_02','context_binding_01','context_systems_01','container_native_01','container_slots_01/functions','transaction_slots_01/functions','inventory_lookup_01','inventory_lookup_02','inventory_lookup_03','container_inject_01','container_inject_02']
    for rel in manifests:
        m=read(pin(HERE/rel/'manifest.json'));ck('Exact current executable for '+rel,m['input_sha256']==sha(exe))
        for f in m.get('function_files',m.get('functions',[])):
            p=pin(f['path'],f['sha256']);s,e=f.get('function_bounds',f.get('bounds'))
            got='\n'.join(f'{x.address:08X}: {x.mnemonic} {x.op_str}' for x in md.disasm(raw(s,e-s),s))+'\n'
            # Historical captures print ImageBase-adjusted branch targets; regenerate the same address convention.
            old='\n'.join(f'{x.address-pe.OPTIONAL_HEADER.ImageBase:08X}: {x.mnemonic} {x.op_str}' for x in md.disasm(raw(s,e-s),pe.OPTIONAL_HEADER.ImageBase+s))+'\n'
            ck('Disassembly regenerated from exact current bytes '+p.name,p.read_text(encoding='utf-8')==old)
            if 'bytes_sha256' in f:ck('Function byte pin '+p.name,hashlib.sha256(raw(s,e-s)).hexdigest().upper()==f['bytes_sha256'])
    systems=read(HERE/'context_systems_01/manifest.json')['systems']
    names={r['context_field']:[s['value'] for f in r['registration_stores'] for s in f['strings']] for r in systems}
    ck('Inventory/Inject/device context slots request exact distinct interfaces',names=={'inventory_context_C0':['gameITransactionSystem'],'inject_context_170':['gameIContainerManager'],'device_context_58':['gameIPersistencySystem']},names)
    ck('Actual container slot258 target',read(pin(HERE/'container_slots_01/slots.json'))['slots'][0]['target_rva']==0x1527428)
    ck('Actual transaction quantity slot2F0 target',read(pin(HERE/'transaction_slots_01/slots.json'))['slots'][0]['target_rva']==0x63E400)
    # Independent known-answer branch fixtures, from actual current native bytes.
    idcode=raw(0x1FB2B4,0x13);idtests=[]
    for tdb,seed,want in [(114327022403,1,1),(0,1,0),(114327022403,0,0),(26<<32,1,1),(1,1,1)]:
        got,trace=Scalar(idcode,0x1FB2B4,{'rcx':0x10000},memory((0x10000,tdb,8),(0x10008,seed,4))).run(0x1FB2B4)
        idtests.append({'raw_tdbid':tdb,'seed':seed,'expected':want,'actual':got,'trace_rvas':trace});ck('Native ItemID validity fixture '+str((tdb,seed)),got==want)
    mutant=bytearray(idcode);off=0x1FB2B8-0x1FB2B4;ck('Actual validity JNE opcode',mutant[off]==0x75);mutant[off]=0x74
    got,_=Scalar(mutant,0x1FB2B4,{'rcx':0x10000},memory((0x10000,0,8),(0x10008,1,4))).run(0x1FB2B4)
    ck('Flipped actual native validity branch detected',got!=0);mp=out/'mutant_itemid_jne.bin';mp.write_bytes(mutant);mutants.append({'name':'actual ItemID JNE→JE','path':str(mp),'sha256':sha(mp),'violated_fixture':'zero TDBID with seed1 must be invalid'})
    cmpcode=raw(0x88CD20,0x13);qtytests=[]
    for n,want in [(0,0),(1,1),(2,1),(0xffffffff,1)]:
        got,trace=Scalar(cmpcode,0x88CD20,{'rcx':0x10000,'rdx':0x10010,'r8':1},memory((0x10000,n,4),(0x10010,1,4))).run(0x88CD20)
        ck('Actual GreaterOrEqual unsigned quantity fixture '+str(n),got==want);qtytests.append({'quantity':n,'required':1,'comparison_enum':1,'expected':want,'actual':got,'trace_rvas':trace})
    mutant=bytearray(cmpcode);off=0x88CD2F-0x88CD20;ck('Actual quantity SETAE opcode',mutant[off:off+2]==bytes.fromhex('0f93'));mutant[off+1]=0x97
    got,_=Scalar(mutant,0x88CD20,{'rcx':0x10000,'rdx':0x10010,'r8':1},memory((0x10000,1,4),(0x10010,1,4))).run(0x88CD20)
    ck('Changed actual >= to > detected on equality',got==0);mp=out/'mutant_quantity_seta.bin';mp.write_bytes(mutant);mutants.append({'name':'actual SETAE→SETA','path':str(mp),'sha256':sha(mp),'violated_fixture':'quantity1 must satisfy >=1'})
    gate=raw(0x21F5E22,0x12);gatetests=[]
    for tdb,want in [(114327022403,'raw_item_id'),(0,'tag_or_all_items'),(26<<32,'tag_or_all_items'),(1,'tag_or_all_items')]:
        got,trace=Scalar(gate,0x21F5E22,{'rbx':0x10000},memory((0x100A0,tdb,8))).run(0x21F5E22,{0x21F5E34:'raw_item_id',0x21F5E68:'tag_or_all_items'})
        ck('Actual inventory evaluator branch '+str(tdb),got==want);gatetests.append({'raw_tdbid':tdb,'expected':want,'actual':got,'trace_rvas':trace})
    mutant=bytearray(gate);off=0x21F5E29-0x21F5E22;ck('Actual raw-ID gate JE opcode',mutant[off]==0x74);mutant[off]=0x75
    got,_=Scalar(mutant,0x21F5E22,{'rbx':0x10000},memory((0x100A0,114327022403,8))).run(0x21F5E22,{0x21F5E34:'raw_item_id',0x21F5E68:'tag_or_all_items'})
    ck('Flipped actual inventory ID gate detected',got!='raw_item_id');mp=out/'mutant_inventory_je.bin';mp.write_bytes(mutant);mutants.append({'name':'actual raw-ID JE→JNE','path':str(mp),'sha256':sha(mp),'violated_fixture':'actual nonzero CRC/length Dixon ID takes raw-ID quantity path'})
    validity={'id_validity':idtests,'quantity_comparison':qtytests,'raw_id_dispatch':gatetests,'limits':['Fixtures are abstract native scalar-state inputs, not saved histories.','No stock-definition lookup occurs in these bounded predicates. They do not prove the target exists in any player inventory or identify an unknown historical item name.','Downstream inventory lookup603430→2190010 is captured as a boundary; arbitrary installed runtime providers are not fully enumerated.']}
    write(out/'native_scalar_controls.json',validity)
    # Container dispatch boundary, without inferring grant idempotence or an admitted history.
    inject=(HERE/'container_slots_01/functions/function_01527428.asm').read_text();manager=(HERE/'container_inject_01/function_007af278.asm').read_text();append=(HERE/'container_inject_02/function_02b3a064.asm').read_text()
    ck('Concrete Inject target calls descriptor builder and actual manager',all(x in inject for x in ['call 0x1407af998','call 0x1407af90c','call 0x1407af278']))
    ck('Manager exact loaded/pending append destinations',all(x in manager for x in ['call 0x142b3a064','call 0x1407af3ac','call 0x1407af4b4','[rcx + 0x30], rbx']))
    ck('Actual loaded descriptor append increments count and writes it before copy',all(x in append for x in ['mov ebx, dword ptr [rcx + 0xc]','inc ebx','mov dword ptr [rdi + 0xc], ebx','call 0x1407af90c']))
    # Career bounded new carrier evidence. Absence is explicitly not retirement proof.
    career=r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase';needles=['mws_wat_08','shooter_appeared_on_leaderboard','activate_trauma_drama_section'];search=[]
    for d in [r'base\quest\minor_quests\minorquests.questphase',r'base\quest\bugfixing\additional_content_bugfixing.questphase',r'base\quest\additional_game_elements.questphase']:
        text=Path(rows[d]['json']).read_text(encoding='utf-8');hits=[s for s in needles if s in text];search.append({'depot':d,'hits':hits,'raw_sha256':rows[d]['raw_sha256'],'json':rows[d]['json']})
        ck('Bounded carrier lacks exact Career literals '+d,not hits)
    script=pin(Q7/'worker_c/native_scripts_02/all.script');st=script.read_text(encoding='utf-8');script_hits=[n for n in needles if n in st]
    ck('Exact current native-script derivative has no Career owner literal',not script_hits)
    career_search={'carrier_candidates':search,'native_script':str(script),'native_script_sha256':sha(script),'script_hits':script_hits,
        'result':'No executing Career owner/retirement chain established. Search stops here; these bounded absences are not universal ownership or saved retirement proof.',
        'next_evidence':'Original minigame/streamed-world owner registration and exact saved-phase retirement transition before first-place8; a personal save is not fabricated or inspected.'}
    write(out/'career_owner_bound.json',career_search)
    # Preserve literal native null endpoints and inspect the actual numeric condition.
    cuckoo=next(d for d in rows if d.endswith('sts_std_rcr_02_phase.questphase'));dixon=next(d for d in rows if d.endswith('sts_std_rcr_02_dixon.scene'))
    cr=Resource(objs[cuckoo]);graph=cr.d(cr.root['graph']);nulls=[];seen=set()
    for nh in graph['nodes']:
        n=cr.d(nh)
        for sh in n.get('sockets',[]):
            sock=cr.d(sh)
            for ch in (sock or {}).get('connections',[]):
                c=cr.d(ch);hid=cr.hid(ch)
                if c and c.get('source') is None and hid not in seen:
                    nulls.append({'node':str(n['id']),'socket':value(sock['name']),'handle':hid,'source':None,'destination_handle':cr.hid(c['destination'])});seen.add(hid)
    ck('Four literal native null endpoints unchanged',len(nulls)==4 and {x['node'] for x in nulls}=={'11','13','15','2'},nulls)
    inv=[x for x in walk(models[dixon]['graphs']['scene']['nodes']['86']['payload']) if x.get('$type')=='questInventory_ConditionType']
    ck('Fresh numeric predicate source matches tested native branch',len(inv)==1 and value(inv[0]['itemID'])=='114327022403' and inv[0]['quantity']==1 and inv[0]['comparisonType']=='GreaterOrEqual')
    write(out/'cuckoo_numeric_and_nulls.json',{'predicate':inv,'native_nulls':nulls,'numeric_semantics':'Actual raw ID takes quantity lookup; validity is numeric structure, not current stock-definition existence. Quantity comparison is unsigned >=1. No alias or grant is invented.','remaining':'Exact original source provenance/intended implicit activation for the four retained null entries is unavailable. Native data equality proves preservation, not their missing authored intent.'})
    # Exact quest prefab is only an area trigger. Nearby sectors are opaque candidates.
    sd=next(d for d in rows if d.endswith('quest_02032d862a5c14c8.streamingsector'));sector=objs[sd]['Data']['RootChunk'];nodes=[n['Data'] for n in sector['nodes']]
    ck('Exact registered Voodoo quest sector contains only its native area trigger',len(nodes)==1 and nodes[0]['$type']=='worldTriggerAreaNode')
    ck('Voodoo quest sector has no persistent entity records',sector['persistentNodes']==[] and sector['persistentNodeIndex']==0)
    target=read(HERE/'baseline_01/new_targets.json')['voodoo_descriptor'];node=nodes[0]
    ck('Trigger ref is exact descriptor subtree',str(value(node['nodeRef'])).endswith('/#q304_mp_slider_stash_area'))
    spatial={'descriptor':target,'sector':{'depot':sd,'raw_sha256':rows[sd]['raw_sha256'],'json':rows[sd]['json']},'nodes':nodes,'packed_node_buffer':rows[sd].get('node_buffer'),'packed_node_buffer_sha256':rows[sd].get('node_buffer_sha256'),
        'opaque_nearest_exterior_candidates':opaque,'selection_scope':'Three nearest XY streaming-box centers overlapping the trigger position; this is a spatial candidate heuristic, not proof that the actual door/container is in those sectors.',
        'result':'Quest prefab lease owns the trigger, not an observed door/container in this sector. Exact door/container entities, persistent IDs and controller components remain unobserved. Stop equivalent sector decoding at the identical unsupported worldNode error.'}
    write(out/'voodoo_spatial_and_native.json',spatial)
    # Final per-contract dispositions remain honest; new proof narrows each blocker.
    updates=[]
    for old in original:
        r=copy.deepcopy(old);r['previous_status']='UNKNOWN';r['status']='UNKNOWN';r['effective_source_epoch']='QR8:00 exact QR7:04 source';r['source_epoch_investigated']='QR8:00';r['runtime_changes']=[]
        r['evidence']=list(dict.fromkeys(r['evidence']+[str(out/'evidence.json'),str(out/'source_pins.json')]))
        if r['quest_id']=='mws_wat_08_trauma_drama':
            r['proven']+=['QR8 freshly captured three additional native registered-root carrier candidates and checked the exact current native script derivative. None exposes the Career phase/fact owner literal; this bounded negative search is not retirement proof.']
            r['remaining']=['Original early minigame/streamed-world owner registration, ancestry, queued/concurrent state and retirement across genuine Tower for6→68→7→57→56→8 remain unavailable. Stop repeated equivalent static searches without that owner input.','LIVE_ONLY: exact retained-session transition fixture for the early pre-first-place owner; equal-state journal suppression is already proven and is not re-counted as new work.']
            r['evidence']+=[str(out/'career_owner_bound.json')]
        elif r['quest_id']=='sts_std_rcr_02':
            r['proven']+=['Current native RTTI/constructor dispatch ties Inventory_ConditionType F0 toD9631C→88D7E8→21F5DF0. Phase contextC0 binds gameITransactionSystem; concrete quantity slot2F0 is63E400.','Exact numeric114327022403 takes raw ItemID quantity dispatch. Native ItemID validity tests numeric CRC/length/seed, not current record-definition existence. Actual GreaterOrEqual1 branch accepts quantity1 and2, rejects0; three actual-byte mutants are detected. Stock record absence alone does not establish a permanently false mandatory route.']
            r['remaining']=['Four native source:null endpoints11/13/15/2 retain no authored source or provenance in the captured original. Their historical intent and any implicit engine activation are not established. No authored edge is invented.','The historical name/provider and actual player inventory for numeric record114327022403 remain unobserved. Scalar predicate semantics are now proven at the stated boundaries; arbitrary runtime providers/downstream inventory state are not claimed.']
            r['evidence']+=[str(out/'native_scalar_controls.json'),str(out/'cuckoo_numeric_and_nulls.json')]
        else:
            r['proven']+=['Fresh current EP1 block descriptor1809 resolves the native quest-prefab sector to one area trigger only, with no door/container or persistent entity list. Three nearest exterior candidate sectors are pinned but unsupported by WK9.1 DynamicBaseClass→worldNode decoding; candidate selection is not ownership proof.','Actual native context170 requests gameIContainerManager, not TransactionSystem. Concrete ContainerManager2581527428→7AF278 appends a descriptor to the loaded container or pending entity queue. This dispatch has no one-time quest receipt; downstream consumption and historical admission are separate.','DeviceManager1081073750 passes the requested controller class to107389C, which resolves its RTTI class through gameIPersistencySystem. Native cleanup21 TerminalControllerPS vs query3 DoorControllerPS therefore cannot be discarded as an unused string. Exact entity applicability remains unavailable.']
            if r['stage']=='eligibility':r['remaining']=['Actual #q304_dvc_slider_stash_door entity/controller components and persistent ID are unobserved beyond an area-only prefab. The three exterior candidates are opaque, not absent.','Whether a genuine manually claimed history later leaves that exact door closed and all late90 conditions true remains a saved-history/engine transition gap. No abstract zero/default fixture proves that history.']
            elif r['stage']=='completion_rewards_cleanup':r['remaining']=['Native generic hub12 runtime dispatch remains unproven; its RTTI socket-configuration methods do not establish once/fan-in execution semantics.','Actual injection dispatch appends descriptors, but downstream container consumer, merge/idempotence and persistent injection history are unobserved. A duplicate grant is not asserted.','Exact cleanup21 TerminalControllerPS applicability to the native door entity remains unproven.']
            elif r['stage']=='persistence':r['remaining']=['Exact door/container entity and persistent IDs and original-versus-restored saved owner transition remain unobserved; the registered quest prefab sector proves only an area trigger lease.','Per-container injection/claim history and generic hub12 dispatch remain unavailable. Numeric descriptor append behavior and generic persistent field flags do not establish an admitted previously claimed save.']
            r['evidence']+=[str(out/'voodoo_spatial_and_native.json'),str(HERE/'context_systems_01/manifest.json'),str(HERE/'container_slots_01/slots.json')]
        r['remaining_unknowns']=[x for x in r['remaining'] if not x.startswith('LIVE_ONLY:')]
        r['newly_resolved_subproperties']=r['proven'][len(old['proven']):];r['independent_review']='Pending QR8 worker peer review; no runtime repair proposed.'
        updates.append(r)
    ck('Five exact rows retained without UNKNOWN count relabeling',len(updates)==5 and all(r['status']=='UNKNOWN' for r in updates))
    write(out/'contract_updates.json',updates);write(out/'source_pins.json',pins)
    write(out/'evidence.json',{'status':'QR8_TARGETED_STATIC_PROGRESS_FIVE_UNKNOWN_ROWS_RETAINED','checks':checks,'checks_passed':len(checks),'actual_byte_mutants':mutants,'contracts':5,'remaining_unknown_rows':5,'confirmed_runtime_defects':[],'runtime_changes':[],
        'newly_proven':['Native inventory numeric predicate dispatch/validity/comparison boundaries.','Actual Inject→ContainerManager loaded/pending append dispatch.','Device class-name input participates in PersistencySystem lookup.','Exact native Voodoo quest-prefab sector is an area trigger only.','Three additional current Career carrier absences are bounded and do not establish owner retirement.'],
        'stopping_rule':'Saved owner/claim histories and opaque entity sources cannot be manufactured by further equivalent static searches. No speculative repair or state reset is justified.',
        'limits':['Scalar controls interpret decoded current native bytes without executing the game; synthetic inputs are not real saved histories.','No game/candidate/runtime/save/fact/deploy/release/package writes.','No whole large archive hash operation. Current provider payloads are pinned with metadata stable during capture.','Hub socket-builder and generic field semantics do not prove the requested engine-history contracts.'], 'code_sha256':sha(__file__)})
    print({'checks':len(checks),'mutants':len(mutants),'contracts':len(updates),'remaining_UNKNOWN':5,'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
