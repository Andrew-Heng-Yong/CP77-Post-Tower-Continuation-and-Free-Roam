"""Bounded static stub/actor identity investigation; no runtime or save access."""
from pathlib import Path
import hashlib,json,struct,sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
sys.path.insert(0,str(WORK/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

FUNCTIONS={
    'create_queue':0x2FA044,
    'restore_queue':0x9CF378,
    'stub_update_registration':0xDAAC0C,
    'stub_update_callback':0x2F91D4,
    'stub_completed_dispatch':0x2F94EC,
    'stub_create_queue_consumer':0x2FA3EC,
    'stub_create_or_restore_worker':0x2FA4F4,
    'stub_create_alloc':0x2FA9A8,
    'stub_create_ctor':0x2FAA48,
    'stub_restore_alloc':0xDCD34C,
    'stub_restore_ctor':0xDCD3E4,
    'population_stub_callback_ctor':0x9CF818,
    'population_stub_callback_thunk':0x4D2648,
    'population_stub_callback':0x4D227C,
    'population_system_getter':0x4D1AD8,
    'population_interface_registration':0x1633964,
    'population_class_registration':0x16CF570,
    'population_construct_cls':0x86FDC0,
    'population_ctor':0x86FF40,
    'population_register_thunk':0x465F48,
    'population_register':0x465F50,
    'population_descriptor_append':0x466408,
    'population_descriptor_move':0x4664D0,
    'entity_initialize_request_consumer':0x71BD9C,
    'entity_initialize':0x71BEF0,
    'entity_initialize_wrapper':0x29A5954,
    'generic_entity_spawn_request':0x5C1508,
    'generic_entity_spawn_context':0x719F40,
}

def main():
    out=HERE/'evidence_01.json'
    assert not out.exists()
    im=Image()
    def capture(a):
        f=im.disasm(a)
        if f['end_rva']is None:
            rows=[]
            for i in f['instructions']:
                rows.append(i)
                if i['mnemonic']in('jmp','ret'):break
            f['instructions']=rows
            f['boundary_limit']='No unwind boundary; first JMP/RET only. Targetbody captured separately where required.'
        return f
    def slot(v,o):return hex(struct.unpack_from('<Q',im.data,im.off(v+o))[0]-im.base)
    def bytes_at(a,h):
        b=bytes.fromhex(h)
        return im.data[im.off(a):im.off(a)+len(b)]==b
    checks=[]
    def ck(n,v,e):checks.append({'name':n,'pass':bool(v),'evidence':e})
    ck('create_stub_keeps_requested_id',bytes_at(0x2FAA76,'4c894140'),'R8→EntityStub+40')
    ck('restore_stub_keeps_requested_id',bytes_at(0xDCD416,'4c894140'),'R8→EntityStub+40')
    ck('callback_reads_token_id',bytes_at(0x4D229B,'488b5a08'),'Token+8→RBX')
    ck('callback_requires_created_status',bytes_at(0x4D22AB,'44386a10'),'Tokenstatus+10==1')
    ck('callback_population_request_id',bytes_at(0x4D233C,'48895dd0'),'sameRBX→requestfirstU64')
    ck('population_register_current_virtual',slot(0x3677070,0x1F0)=='0x465f48','exactconstructedinstance')
    ck('population_register_looks_up_stub_by_input_id',bytes_at(0x465F7A,'488b12') and bytes_at(0x465F80,'ff90d0010000'),
       'request[0]→FindStubv1D0')
    ck('queued_descriptor_keeps_dynamic_id32',bytes_at(0x4661F9,'458b7500') and bytes_at(0x46626D,'4489742470'),
       'requestIDlow32→descriptor+28')
    ck('target_fits_exact_dynamic_id_width',10229047<0x1000000,'No truncationfortarget')
    ck('entity_initialize_terminal_id_copy',bytes_at(0x71BF47,'498b4020') and bytes_at(0x71BF4B,'48894148'),
       'EntityInitializeRequest+20→entEntity+48')
    ck('initialize_consumer_passes_job_request',bytes_at(0x71BE84,'4c8b4710'),'jobcontext+10→R8')
    result={'status':'PARTIAL_NATIVE_IDENTITY_CONTRACT_POPULATION_QUEUE_BRIDGE_UNRESOLVED',
        'exe_sha256':im.sha,'functions':{k:capture(v)for k,v in FUNCTIONS.items()},
        'bindings':{'stub_update_callback_vtable':'0x394dd00','population_stub_callback_vtable':'0x3956dc8',
            'population_metadata_vtable':'0x32dfc90','population_construct':slot(0x32DFC90,0xD8),
            'population_instance_vtable':'0x3677070','population_register_v1F0':slot(0x3677070,0x1F0)},
        'source_confirmed':['SuccessfulCreateStubandRestoreStubstoretheoriginalrequestedIDunchangedinEntityStub+40.',
            'ThecompletedpopulationcallbackkeepsToken+8asthepopulationregisterrequestID.',
            'Theexactpopulationregistrationroutequeuesa0x38bytedescriptoratsystem+60withinputdynamicID32at+28.',
            'TheknownnativeEntityInitializeterminalcopiesrequest+20totheactualentity+48withoutconversion.'],
        'missing_link':{'source':'gamePopulationSystem+0x60 queueddescriptor, dynamicID32atdescriptor+0x28',
            'destination':'EntityInitializeRequest.entityID+0x20 passedby71BD9Cviajobcontext+0x10to71BEF0',
            'unresolved':'Theexactpopulationdescriptorconsumer/jobproducerthatconnectsthesetwositeswasnotbound. Itcouldperformadditionalselectionorassignment; absenceofremapisnotproved.'},
        'bounded_search':{'direct_calls_to_entity_initialize':im.calls_to(0x71BEF0),
            'direct_calls_to_initialize_consumer':im.calls_to(0x71BD9C),
            'absolute_pointers_to_initialize_consumer':im.pointers_to(0x71BD9C),
            'RIP_refs_to_initialize_consumer':im.refs_to(0x71BD9C)},
        'checks':checks,'controls_status':'PASS'if all(x['pass']for x in checks)else'FAIL',
        'conclusion':'NoCreateStub/RestoreStubremapwasfoundintheboundworker. Thecompleteactorassignmentcontractisnotclosed;10229047cannotyetbecertifiedastheactualspawnedvehicle+48fromthissourcealone.',
        'limits':['No claim that an actor was ever instantiated or is currently loaded.',
            'No actoridentity,PSabsence,visualgrid,doorcompletion,graphownerorrepaircertificate.',
            'GenericEntitySpawnerrequest code is terminal/context evidence only; notsubstitutedfortheunboundpopulationconsumer.'],
        'game_calls':0,'original_save_reads':0,'save_writes':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'controls':result['controls_status'],'checks':len(checks),
        'failures':[x['name']for x in checks if not x['pass']],
        'sha256':hashlib.sha256(out.read_bytes()).hexdigest().upper()}))

if __name__=='__main__':main()
