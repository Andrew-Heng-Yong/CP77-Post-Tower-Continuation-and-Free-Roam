"""Raw-resource and native-byte controls supplement the targeted assertions."""
from pathlib import Path
import sys,copy,struct,argparse
from prepare import ROOT,HERE,read,write,sha
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from common import walk,value
from model import Resource,digest
from verify_remaining import CUCKOO,DIXON,STASH,BOOT
sys.path.insert(0,str(ROOT/'research/redscript_2_5/binary_reader_01'))
import diagnose_01 as diag

def main(out):
    assert not out.exists();out.mkdir()
    rows={r['depot']:r for r in read(HERE/'resource_exports_01/manifest.json')['resources']}
    controls=[];pins=[]
    def load(d):
        r=rows[d];assert sha(r['raw'])==r['raw_sha256'] and sha(r['json'])==r['json_sha256'];pins.append(r);return read(r['json'])
    actual=load(CUCKOO);mutant=copy.deepcopy(actual);rr=Resource(mutant);gg=rr.d(rr.root['graph'])
    root_input=next(rr.d(x) for x in gg['nodes'] if rr.d(x).get('id')==0)
    output=next(x for x in root_input['sockets'] if value(rr.d(x).get('name'))=='Out')
    conn=next(x for x in walk(mutant) if x.get('$type')=='graphGraphConnectionDefinition' and x.get('source','not-null') is None)
    conn['source']={'HandleRefId':rr.hid(output)}
    original_model=Resource(actual).normalize();mutant_model=Resource(mutant).normalize()
    original_nulls=[x for x in original_model['errors'] if x['kind']=='DANGLING_EDGE']
    changed_nulls=[x for x in mutant_model['errors'] if x['kind']=='DANGLING_EDGE']
    controls.append({'depot':CUCKOO,'mutation':'Bind one actual null-source connection to existing native input0.Out, without adding a synthetic socket.',
        'before_diagnostics':original_nulls,'after_diagnostics':changed_nulls,'baseline_pass':len(original_nulls)==4,
        'mutant_rejected':len(changed_nulls)!=4,'before_model_sha256':digest(original_model),'after_model_sha256':digest(mutant_model)})
    actual=load(DIXON);mutant=copy.deepcopy(actual)
    # Change the actual nested quest condition object before normalization.
    predicates=[x for x in walk(mutant) if x.get('$type')=='questInventory_ConditionType' and value(x.get('itemID'))=='114327022403']
    assert len(predicates)==1;predicates[0]['quantity']=2
    def inventory_valid(obj):
        m=Resource(obj).normalize();ps=[x for x in walk(m['graphs']['scene']['nodes']['86']['payload']) if x.get('$type')=='questInventory_ConditionType']
        return len(ps)==1 and ps[0]['quantity']==1 and ps[0]['comparisonType']=='GreaterOrEqual'
    controls.append({'depot':DIXON,'mutation':'Actual scene86 nested quantity1→2','baseline_pass':inventory_valid(actual),'mutant_rejected':not inventory_valid(mutant),'before_json_semantic_sha256':digest(actual),'after_json_semantic_sha256':digest(mutant)})
    actual=load(BOOT);mutant=copy.deepcopy(actual);mr=Resource(mutant)
    late=next(x for x in walk(mutant) if x.get('$type')=='questConditionNodeDefinition' and x.get('id')==90)
    logical=next(x for x in walk(mr.d(late['condition'])) if x.get('$type')=='questLogicalCondition' and x.get('operation')=='NOR')
    logical['operation']='OR'
    def closed_guard(obj):
        gate=Resource(obj).normalize()['graphs']['root']['nodes']['90']['payload']['condition']
        return any(x.get('$type')=='questLogicalCondition' and x.get('operation')=='NOR' and any(y.get('$type')=='questDevice_ConditionType' for y in walk(x)) for x in walk(gate))
    controls.append({'depot':BOOT,'mutation':'Actual late90 NOR(IsOpen)→OR(IsOpen)','baseline_pass':closed_guard(actual),'mutant_rejected':not closed_guard(mutant),'before_json_semantic_sha256':digest(actual),'after_json_semantic_sha256':digest(mutant)})
    actual=load(STASH);mutant=copy.deepcopy(actual)
    operation=next(x for x in walk(mutant) if x.get('$type')=='questInjectLoot_NodeTypeParams_OperationData' and x.get('quantity')==8000);operation['quantity']=8001
    def amount_valid(obj):
        ops=[x for x in walk(Resource(obj).normalize()['graphs']['root']['nodes']['22']['payload']) if x.get('$type')=='questInjectLoot_NodeTypeParams_OperationData']
        return [(value(x['itemTDBID']),x['quantity'],x['operationType']) for x in ops]==[('51369838828',8000,'Inject'),('127255451537',1,'Inject'),('118124605694',1,'Inject')]
    controls.append({'depot':STASH,'mutation':'Actual native22 money quantity8000→8001','baseline_pass':amount_valid(actual),'mutant_rejected':not amount_valid(mutant),'before_json_semantic_sha256':digest(actual),'after_json_semantic_sha256':digest(mutant)})
    b,info,pools,defs=diag.parse(diag.CURRENT);klass=next(x['index'] for x in defs if x['name']=='DoorControllerPS' and x['type']==1);field=next(x for x in defs if x['parent']==klass and x['name']=='m_isOpened' and x['type']==8)
    pos=field['offset']+5;flags=struct.unpack_from('<H',b,pos)[0];mutant=bytearray(b);struct.pack_into('<H',mutant,pos,flags&~0x100)
    controls.append({'input':str(diag.CURRENT),'input_sha256':info['sha256'],'mutation':'Clear persistent bit at actual DoorControllerPS.m_isOpened FieldFlags offset','offset':pos,
        'before_hex':b[pos:pos+2].hex(),'after_hex':bytes(mutant[pos:pos+2]).hex(),'baseline_pass':bool(struct.unpack_from('<H',b,pos)[0]&0x100),'mutant_rejected':not bool(struct.unpack_from('<H',mutant,pos)[0]&0x100)})
    assert all(x['baseline_pass'] and x['mutant_rejected'] for x in controls)
    write(out/'result.json',{'status':'PASS_FIVE_ACTUAL_RAW_INPUT_MUTATIONS','controls':controls,'source_pins':pins,'code_sha256':sha(__file__),
        'limits':['Mutants exist only in private memory. These controls test source-property detection, not game behavior or validity of an untracked historical claim.'],'runtime_changes':[]})
    print({'raw_resource_controls':4,'raw_native_field_controls':1,'out':str(out)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
