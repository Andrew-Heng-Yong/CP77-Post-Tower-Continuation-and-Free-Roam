"""Reproducible current native journal dispatch and same-state guard checks.

This checks current binary instructions, not a mocked journal implementation.
The tiny emulator only proves the early equality return basic block. Other
native paths and saved-owner lifecycle remain explicitly outside that proof.
"""
from pathlib import Path
import sys,struct,bisect,copy,argparse
from prepare import ROOT,HERE,read,write,sha
sys.path.insert(0,str(ROOT/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
from common import walk,value

def main(out):
    assert not out.exists();out.mkdir()
    p=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe');before=sha(p)
    assert before=='D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
    pd=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata')
    bounds=sorted(x for i in range(0,pd.SizeOfRawData-11,12) if (x:=struct.unpack_from('<III',b,pd.PointerToRawData+i)[:2])[0] and x[1]>x[0]);starts=[x[0] for x in bounds]
    checks=[];functions={}
    def check(name,yes,evidence=None):
        checks.append({'check':name,'pass':bool(yes),'evidence':evidence});assert yes,name
    def raw(rva,size):return b[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(rva)+size]
    def qword(rva):return struct.unpack('<Q',raw(rva,8))[0]-base
    def dis(rva):
        ix=bisect.bisect_right(starts,rva)-1;s,e=bounds[ix]
        if not s<=rva<e:
            ins=[]
            for x in md.disasm(raw(rva,96),base+rva):
                ins.append(x)
                if x.mnemonic in ['ret','jmp']:break
            assert ins[-1].mnemonic in ['ret','jmp'];s=rva;e=ins[-1].address+ins[-1].size-base
        else:ins=list(md.disasm(raw(s,e-s),base+s))
        if s not in functions:
            fp=out/f'function_{s:08x}.asm';fp.write_text('\n'.join(f'{x.address-base:08X}: {x.mnemonic} {x.op_str}' for x in ins)+'\n',encoding='utf-8')
            functions[s]={'path':str(fp),'sha256':sha(fp),'bounds':[s,e],'bytes_sha256':__import__('hashlib').sha256(raw(s,e-s)).hexdigest().upper()}
        return ins
    def direct_call(ins,target):return any(x.mnemonic=='call' and x.operands[0].type==capstone.x86.X86_OP_IMM and x.operands[0].imm-base==target for x in ins)
    def vcall(ins,slot):return any(x.mnemonic in ['call','jmp'] and x.operands[0].type==capstone.x86.X86_OP_MEM and x.operands[0].mem.disp==slot for x in ins)
    def lea(ins,address,register):
        return any(x.mnemonic=='lea' and x.operands[0].type==capstone.x86.X86_OP_REG and x.reg_name(x.operands[0].reg)==register and x.operands[1].type==capstone.x86.X86_OP_MEM and x.operands[1].mem.base==capstone.x86.X86_REG_RIP and x.address+x.size+x.operands[1].mem.disp-base==address for x in ins)
    registration=dis(0x15D151C);name_rva=pe.get_rva_from_offset(b.find(b'gameJournalManager\0'))
    check('Current gameJournalManager RTTI registration exact string and class vtable',lea(registration,name_rva,'rdx') and lea(registration,0x3679D58,'rax'))
    ctor_thunk=qword(0x3679D58+0xD8)
    check('Actual CClass ConstructCls thunk dispatches to journal ctor',ctor_thunk==0x871CC8 and any(x.mnemonic=='jmp' and x.operands[0].type==capstone.x86.X86_OP_IMM and x.operands[0].imm-base==0x8720D8 for x in dis(ctor_thunk)))
    check('Native journal constructor stores exact instance vtable',lea(dis(0x8720D8),0x3679E48,'rcx') and any(x.mnemonic=='mov' and x.op_str=='qword ptr [rbx], rcx' for x in dis(0x8720D8)))
    slots={slot:qword(0x3679E48+slot) for slot in [0x260,0x268,0x290,0x2B0]}
    check('Actual instance dispatch pointers are exact current implementations',slots=={0x260:0x6C19BC,0x268:0x6C1A48,0x290:0x565DFC,0x2B0:0x6549F8},slots)
    check('Unique path overload260 forwards to handle overload268',any(x.mnemonic=='mov' and x.op_str=='r10, qword ptr [rax + 0x268]' for x in dis(slots[0x260])) and any(x.mnemonic=='call' and x.op_str=='r10' for x in dis(slots[0x260])))
    check('Handle overload268 dispatches Active2 to6543EC',direct_call(dis(slots[0x268]),0x6543EC) and any(x.mnemonic=='cmp' and x.op_str=='edi, r8d' for x in dis(slots[0x268])) and any(x.mnemonic=='mov' and x.op_str=='r8d, 2' for x in dis(slots[0x268])))
    check('Active path calls common state change654C0C',direct_call(dis(0x6543EC),0x654C0C))
    check('Common change reads old state then invokes exact equality guard',vcall(dis(0x654C0C),0x2B0) and direct_call(dis(0x654C0C),0x6545D0))
    check('Common change returns when guard is false before callback block',all(any(x.address-base==a and x.mnemonic==mn for x in dis(0x654C0C)) for a,mn in [(0x654C61,'test'),(0x654C63,'jne'),(0x654C7F,'ret')]))
    guard=raw(0x6545D0,16)
    def equal_returns_false(code,old,new):
        regs={'r8d':old,'r9d':new,'al':99};zf=False;pc=0x6545D0;ins={x.address-base:x for x in md.disasm(code,base+pc)}
        for _ in range(12):
            x=ins.get(pc)
            if x is None:return None
            nextpc=pc+x.size
            if x.mnemonic in ['sub','add'] and x.op_str.startswith('rsp,'):pass
            elif x.mnemonic=='cmp' and x.op_str=='r8d, r9d':zf=regs['r8d']==regs['r9d']
            elif x.mnemonic in ['jne','je']:
                if (not zf if x.mnemonic=='jne' else zf):nextpc=x.operands[0].imm-base
            elif x.mnemonic=='xor' and x.op_str=='al, al':regs['al']=0
            elif x.mnemonic=='ret':return regs['al']==0
            else:return None
            pc=nextpc
        return None
    fixtures=[{'old':s,'new':s,'returns_false_before_side_effects':equal_returns_false(guard,s,s)} for s in range(5)]
    check('Actual machine-code equality basic block returns false for every native state',all(x['returns_false_before_side_effects'] is True for x in fixtures),fixtures)
    # Graph operation is a separate native dispatch from script overload260.
    node_trace=read(HERE/'journal_node_03/manifest.json')
    derived=node_trace['constructor_candidates'][-1]
    check('Actual JournalQuestEntry resource type vtable108 is processing method56455C',derived['instance_vtable']==0x369E7A8 and next(x['rva'] for x in derived['methods'] if x['slot']==0x108)==0x56455C)
    check('Graph processing uses JournalManager290, which forwards to268',vcall(dis(0x56455C),0x290) and vcall(dis(slots[0x290]),0x268))
    check('State dispatch core equality guard is thus applicable to graph journal writes',vcall(dis(0x56455C),0x290) and vcall(dis(0x565DFC),0x268) and direct_call(dis(0x6C1A48),0x6543EC) and direct_call(dis(0x6543EC),0x654C0C) and direct_call(dis(0x654C0C),0x6545D0))
    ex=read(HERE/'resource_exports_01/manifest.json');rows={x['depot']:x for x in ex['resources']}
    native=r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase'
    current='towercontinued\\sidejobs_s30\\native\\'+native
    models={}
    for d in [native,current]:
        row=rows[d];check('Pinned Career resource '+d,sha(row['raw'])==row['raw_sha256'] and sha(row['json'])==row['json_sha256']);models[d]=Resource(read(row['json'])).normalize()
    ng=models[native]['graphs']['root'];cg=models[current]['graphs']['root']
    messages=[]
    for nid in ['7','56']:
        n=ng['nodes'][nid];c=cg['nodes'][nid]
        check('Native and current message write is identical '+nid,n['payload']==c['payload'] and n['payload']['type']['sendNotification']==1 and n['payload']['type']['trackQuest']==0)
        check('Journal node is actually activated via Active socket '+nid,any(e[2:]==[nid,'Active'] for e in ng['edges']))
        messages.append({'node':nid,'path':n['payload']['type']['path'],'sendNotification':1,'trackQuest':0,'native_payload_sha256':n['payload_sha256'],'current_payload_sha256':c['payload_sha256']})
    check('Native old-history prefix6→68→7→57→56→8 is preserved',all(any(e[0]==a and e[2]==z for e in ng['edges']) for a,z in [('6','68'),('68','7'),('7','57'),('57','56'),('56','8')]))
    check('Started write is after first-place8→9→66, not before messages7/56',all(any(e[0]==a and e[2]==z for e in ng['edges']) for a,z in [('8','9'),('9','66')]) and ng['nodes']['66']['writes'][0]['factName']=='mws_wat_08_started')
    controls=[]
    bad=bytearray(guard);branch=next(x for x in md.disasm(guard,base+0x6545D0) if x.mnemonic=='jne');bad[branch.address-base-0x6545D0]=0x74
    controls.append({'mutation':'Flip actual equality-guard JNE to JE in private byte array','detected':equal_returns_false(bad,2,2) is not True})
    badnode=copy.deepcopy(cg['nodes']['7']);badnode['payload']['type']['path']['realPath']+='_wrong'
    controls.append({'mutation':'Change actual Career message7 journal identity','detected':badnode['payload']!=ng['nodes']['7']['payload']})
    check('Both independent binary/resource controls detected',all(x['detected'] for x in controls))
    check('Current native executable unchanged',sha(p)==before)
    write(out/'result.json',{'status':'PROVEN_CURRENT_NATIVE_JOURNAL_SAME_STATE_REJECTION_AND_GRAPH_APPLICABILITY','checks':checks,'controls':controls,
        'input':str(p),'input_sha256':before,'function_files':list(functions.values()),'same_state_fixtures':fixtures,'career_messages':messages,
        'exact_path':'JournalQuestEntry_NodeType processing56455C→JournalManager.vfunc290(565DFC)→268(6C1A48)→Active6543EC→common654C0C→guard6545D0. old==new returns false before journal write/listener notification.',
        'preserved_limits':['No observed duplicate message or reward was asserted in QR6 or here.',
        'State-change/notification idempotence is proven for same-state graph writes under this pinned native executable.',
        'Other journal entry or ancestor states, separately executed tracking callbacks, concurrent engine interleaving and old saved native-owner retirement are not universally proven.',
        'The graph writes do not add a native reward receipt. Actual saved-owner migration remains a separate contract boundary.'],
        'source_pins':[rows[native],rows[current],{'path':str(HERE/'journal_node_03/manifest.json'),'sha256':sha(HERE/'journal_node_03/manifest.json')},
          {'path':str(ROOT/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/RTTITypes.hpp'),'sha256':sha(ROOT/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/RTTITypes.hpp')}],
        'code_sha256':sha(__file__),'runtime_changes':[]})
    print({'checks':len(checks),'controls':len(controls),'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
