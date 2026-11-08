"""Target the named remaining Cuckoo/Voodoo evidence gaps, read-only.

The checks preserve unknown engine/object-history behavior rather than infer
that absence of a journal entry means unused loot entitlement.
"""
from pathlib import Path
import sys,struct,copy,re,argparse
from prepare import ROOT,HERE,read,write,sha
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from common import walk,value
from model import Resource
sys.path.insert(0,str(ROOT/'research/redscript_2_5/binary_reader_01'))
import diagnose_01 as diag

CUCKOO=r'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\phases\sts_std_rcr_02_phase.questphase'
DIXON=r'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\scenes\sts_std_rcr_02_dixon.scene'
STASH=r'ep1\quest\main_quests\q304\phases\q304_slider_stash.questphase'
BOOT=r'towercontinued\sidejobs_s23\ep1\voodoo_boot.questphase'

def method(text,klass,name):
    start=re.search(r'^public .*class '+re.escape(klass)+r'\b[^\n]*\{',text,re.M).end()
    tail=text[start:];nxt=re.search(r'^public .*class \w+',tail,re.M)
    body=tail[:nxt.start()] if nxt else tail
    m=re.search(r'^  [^\n]*func '+re.escape(name)+r'\([^\n]*\{',body,re.M)
    assert m,(klass,name)
    at=m.end();depth=1
    while depth:
        depth+=(body[at]=='{')-(body[at]=='}');at+=1
    return body[m.start():at]

def main(out):
    assert not out.exists();out.mkdir()
    checks=[];controls=[]
    def check(name,yes,evidence=None):
        checks.append({'check':name,'pass':bool(yes),'evidence':evidence});assert yes,name
    export=read(HERE/'resource_exports_01/manifest.json');rows={r['depot']:r for r in export['resources']};models={};objs={}
    for d,r in rows.items():
        check('Actual raw/JSON still pinned '+d,sha(r['raw'])==r['raw_sha256'] and sha(r['json'])==r['json_sha256'])
        if d in [CUCKOO,DIXON,STASH,BOOT]:objs[d]=read(r['json']);models[d]=Resource(objs[d]).normalize()
    providers=read(HERE/'quest_providers_01/manifest.json')
    for r in providers['resources']:
        d=r['depot'];check('Unique current provider agrees with old exact native target '+d,len([x for x in providers['resources'] if x['depot']==d])==1 and r['raw_sha256']==rows[d]['raw_sha256'])
    stock=read(HERE/'stock_01/records.json')
    for r in stock['databases']:check('Stock database unchanged '+r['path'],sha(r['path'])==r['sha256'])
    missing=[x for x in stock['records'] if x['id']=='114327022403']
    check('Direct exact Cuckoo record lookup absent in both stock databases',len(missing)==2 and all(not x['exists'] for x in missing),missing)
    # This is an inventory condition; never call it a missing reward grant.
    dg=models[DIXON]['graphs']['scene'];inv=[x for x in walk(dg['nodes']['86']['payload']) if x.get('$type')=='questInventory_ConditionType']
    check('Dixon86 is player item114327022403 quantity>=1',len(inv)==1 and value(inv[0]['itemID'])=='114327022403' and inv[0]['isPlayer']==1 and inv[0]['quantity']==1 and inv[0]['comparisonType']=='GreaterOrEqual',inv)
    check('Dixon true/false socket bindings are exact',dg['nodes']['86']['payload']['osockMappings']==[{'$type':'CName','$storage':'string','$value':'True'},{'$type':'CName','$storage':'string','$value':'False'}] and ['86','0:0','158','0:0'] in dg['edges'] and ['86','0:1','152','0:1'] in dg['edges'])
    true_route=['158','6'];false_route=['152','88','244','192','249','6']
    for label,route in [('true',true_route),('false',false_route)]:
        check('Dixon '+label+' route still reaches native choice6',all(any(e[0]==a and e[2]==z for e in dg['edges']) for a,z in zip(route,route[1:])),route)
    cr=Resource(objs[CUCKOO]);graph=cr.d(cr.root['graph']);nulls=[];seen=set()
    for nh in graph['nodes']:
        n=cr.d(nh)
        for sh in n.get('sockets',[]):
            sock=cr.d(sh)
            for ch in (sock or {}).get('connections',[]):
                conn=cr.d(ch);key=cr.hid(ch)
                if conn and conn.get('source') is None and key not in seen:
                    nulls.append({'destination_node':str(n['id']),'destination_socket':value(sock['name']),'connection_handle':key,'serialized_source':None,'destination_handle':cr.hid(conn['destination'])});seen.add(key)
    check('Four inherited dangling sources are literal serialized nulls, not omitted model names',len(nulls)==4 and {x['destination_node'] for x in nulls}=={'11','13','15','2'},nulls)
    cg=models[CUCKOO]['graphs']['root']
    check('Four null-source recipient nodes have no input-root reachability',all(x['destination_node'] not in cg['reachable'] for x in nulls))
    controls.append({'mutation':'Attach one inherited null source in copied Cuckoo raw connection evidence','detected':len([x for x in [dict(nulls[0],serialized_source={'HandleRefId':'synthetic_control'})]+nulls[1:] if x['serialized_source'] is None])!=4})
    changed=copy.deepcopy(inv[0]);changed['quantity']=2
    controls.append({'mutation':'Change Dixon86 inventory quantity1→2 in copied real predicate','detected':changed!=inv[0]})
    # Actual original phase is referenced from the private wrapper, with original IDs.
    bg=models[BOOT]['graphs']['root'];sg=models[STASH]['graphs']['root'];sn=sg['nodes']
    check('Private root100/4 invokes exact original stash resource',models[BOOT]['graphs']['root/100']['nodes']['4']['refs']==[STASH])
    check('Private wrapper has no new Inject operation',not any(x.get('$type')=='questInjectLoot_NodeType' for x in walk(models[BOOT])))
    gate=bg['nodes']['90']['payload']['condition']
    device=[x for x in walk(gate) if x.get('$type')=='questDevice_ConditionType'];native_device=[x for x in walk(sn['3']['payload']) if x.get('$type')=='questDevice_ConditionType']
    check('Late guard and native3 query exact same loaded DoorControllerPS IsOpen identity',len(device)==1 and device==native_device and value(device[0]['deviceControllerClass'])=='DoorControllerPS' and value(device[0]['objectRef'])=='#q304_dvc_slider_stash_door')
    nor=[x for x in walk(gate) if x.get('$type')=='questLogicalCondition' and x.get('operation')=='NOR' and any(y.get('$type')=='questDevice_ConditionType' for y in walk(x))]
    check('Late guard is AND with NOR(IsOpen), not merely four Inactive journals',gate['operation']=='AND' and len(nor)==1 and len(nor[0]['conditions'])==1)
    check('Native earned-info prerequisite remains exact',sn['14']['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'q304_05_slider_stash_info_downloaded','value':1}])
    ops=[x for x in walk(sn['22']['payload']) if x.get('$type')=='questInjectLoot_NodeTypeParams_OperationData']
    check('Native22 exact three Inject operations and amounts',[(value(x['itemTDBID']),x['quantity'],x['operationType']) for x in ops]==[('51369838828',8000,'Inject'),('127255451537',1,'Inject'),('118124605694',1,'Inject')],ops)
    check('Native hub12 remains generic logical hub',sn['12']['type']=='questLogicalHubNodeDefinition' and sn['12']['payload']['inputSocketCount']==2 and sn['12']['payload']['outputSocketCount']==1)
    check('Native22→5→13→6→1 cleanup path remains actual graph',all(any(e[0]==a and e[2]==z for e in sg['edges']) for a,z in [('12','22'),('22','5'),('5','13'),('13','6'),('6','1')]))
    cleanup=[x for x in walk(sn['21']['payload']) if x.get('$type')=='questDeviceManager_NodeTypeParams']
    check('Native21 cleanup uses TerminalControllerPS for the same door NodeRef',len(cleanup)==1 and value(cleanup[0]['deviceControllerClass'])=='TerminalControllerPS' and value(cleanup[0]['objectRef'])==value(device[0]['objectRef']) and value(cleanup[0]['deviceAction'])=='ForceDisabled',cleanup)
    native_data,cache,pools,defs=diag.parse(diag.CURRENT)
    check('Native script bytecode has exact pinned current cache',cache['sha256']=='B78043064AE90FB80861B0D885D1C8DBCD22070F1DB71F20664D19F2D83C4AAC')
    classes={x['name']:x['index'] for x in defs if x['type']==1}
    fields=[]
    for klass,name in [('DoorControllerPS','m_isOpened'),('SharedGameplayPS','m_deviceState')]:
        d=next(x for x in defs if x['type']==8 and x['parent']==classes[klass] and x['name']==name)
        flags=struct.unpack_from('<H',native_data,d['offset']+5)[0]
        check('Actual native field is persistent: '+klass+'.'+name,bool(flags&0x100))
        fields.append(dict(d,class_name=klass,field_flags=flags,persistent=bool(flags&0x100),raw_payload_hex=native_data[d['offset']:d['offset']+d['size']].hex()))
    decomp=HERE/'native_scripts_02/all.script';script_result=read(HERE/'native_scripts_02/result.json')
    check('Derived decompiled source remains tied to byte-identical current definition payloads',sha(decomp)==script_result['output_sha256'] and script_result['definition_payloads_byte_equal']==len(defs))
    text=decomp.read_text(encoding='utf-8');methods={}
    for klass,name in [('DoorControllerPS','IsOpen'),('DoorControllerPS','SetIsOpened'),('DoorControllerPS','OnToggleOpen'),('DoorControllerPS','OnSetClosed'),('DoorControllerPS','OnQuestForceClose'),('ScriptableDeviceComponentPS','OnQuestForceDisabled'),('ScriptableDeviceComponentPS','DisableDevice')]:
        methods[klass+'.'+name]=method(text,klass,name)
    check('Actual DoorControllerPS.IsOpen returns persistent m_isOpened', 'return this.m_isOpened;' in methods['DoorControllerPS.IsOpen'])
    check('Normal toggle/close paths reject disabled doors',all('this.IsDisabled()' in methods['DoorControllerPS.'+n] and 'SendActionFailedEvent' in methods['DoorControllerPS.'+n] for n in ['OnToggleOpen','OnSetClosed']))
    check('QuestForceDisabled calls DisableDevice without writing m_isOpened','this.DisableDevice();' in methods['ScriptableDeviceComponentPS.OnQuestForceDisabled'] and 'SetIsOpened' not in methods['ScriptableDeviceComponentPS.OnQuestForceDisabled']+methods['ScriptableDeviceComponentPS.DisableDevice'])
    check('A separate native quest-force-close can still close a door','this.SetIsOpened(false);' in methods['DoorControllerPS.OnQuestForceClose'])
    changed_nor=copy.deepcopy(nor[0]);changed_nor['operation']='OR'
    controls.append({'mutation':'Change actual private NOR(IsOpen) to OR','detected':changed_nor!=nor[0]})
    changed_op=copy.deepcopy(ops[0]);changed_op['quantity']=8001
    controls.append({'mutation':'Change native money injection8000→8001','detected':changed_op!=ops[0]})
    controls.append({'mutation':'Clear persistent bit in actual m_isOpened field flags','detected':not bool((fields[0]['field_flags']&~0x100)&0x100)})
    check('Five resource/native-field negative controls detected',len(controls)==5 and all(x['detected'] for x in controls))
    inject=read(HERE/'inject_node_02/manifest.json');actual_inject=inject['constructor_candidates'][-1]
    check('Native InjectLoot processing function captured from its actual current vtable',actual_inject['instance_vtable']==0x3165410 and next(x['rva'] for x in actual_inject['methods'] if x['slot']==0x108)==0x152726C)
    findings={
      'sts_std_rcr_02':{'status':'UNKNOWN','new_proven':['All four current targeted native providers are unique across134 archive indexes. Dixon exact numeric inventory record remains absent from both direct stock databases; this is a condition, not a reward operation.',
        'The four graph diagnostics are actual serialized source:null entries, with exact destination handles/nodes recorded. Their recipients11/13/15/2 are unreachable from the native root input. This resolves decoder-vs-native ambiguity but supplies no missing original source.',
        'Both inventory branches still have the exact native route to choice6.'],
        'remaining':['Record114327022403 has no identified current stock definition or verified native invalid-record inventory semantics. Runtime/computed providers are not ruled out.',
          'No native source exists for four null connection endpoints; they are retained original data. Their intended historical behavior and any engine-origin implicit activation require exact native provenance/engine evidence.'],
        'repair':'None: no restoration-specific route loss or missing grant has been proven.'},
      'q304_splinter_stash':{'status':'UNKNOWN','new_proven':['Current late90 guard checks exact original door IsOpen through DoorControllerPS and requires NOR(IsOpen). Four inactive journals alone are not its whole admission guard.',
        'm_isOpened and inherited m_deviceState are genuinely persistent fields in the exact current script cache. Generic disabled-door handlers preserve open state and block ordinary close, but this does not establish applicability to native cleanup21.',
        'Native3 uses DoorControllerPS; native21 sends ForceDisabled to the same door NodeRef using TerminalControllerPS. The native binding mismatch is exact evidence, not an inferred fix.',
        'Private root100/4 refers to original native stash phase; it does not clone/replace its Inject. Original22 operations, generichub12 and container-empty6 termination are pinned.',
        'Native InjectLoot vtable108 processing152726C and actual TransactionSystem258/250 implementations are captured. No per-quest saved receipt is exposed by that top-level call; downstream inventory behavior remains unproven.'],
        'remaining':['Exact door entity/controller binding for native21, including whether TerminalControllerPS resolves on that NodeRef, and resulting persisted close/disabled behavior.',
          'Native generic-hub12 dispatch, downstream currency/container injection idempotence/merge behavior, and whether a source-realizable manually claimed history can later satisfy late90 after Tower.',
          'Saved container and door identity/serialization across original owner retirement and restored private owner; source fields alone are not an old-save transition fixture.'],
        'repair':'None: a source-only abstract gate witness is not a proven duplicate-grant route. Do not force a door, create a receipt or fabricate pre-Tower entitlement.'}}
    write(out/'result.json',{'status':'TARGETED_NATIVE_PROPERTIES_PROVEN_RESIDUAL_UNKNOWNS_RETAINED','checks':checks,'controls':controls,'cuckoo_null_sources':nulls,
        'dixon_condition':inv[0],'voodoo_late_guard':gate,'voodoo_native_cleanup21':sn['21']['payload'],'native_persistent_fields':fields,'native_methods':methods,
        'findings':findings,'source_pins':[rows[d] for d in [CUCKOO,DIXON,STASH,BOOT]],
        'other_evidence_pins':[{'path':str(p),'sha256':sha(p)} for p in [HERE/'quest_providers_01/manifest.json',HERE/'stock_01/records.json',HERE/'native_scripts_02/result.json',HERE/'inject_node_02/manifest.json',HERE/'transaction_01/manifest.json',HERE/'inject_followup_01/manifest.json']],
        'code_sha256':sha(__file__),'runtime_changes':[]})
    print({'checks':len(checks),'controls':len(controls),'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
