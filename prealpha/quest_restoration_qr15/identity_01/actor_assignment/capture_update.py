"""Fresh successor: follow exact PopulationSystem registered callbacks/consumer."""
from pathlib import Path
import hashlib,json,struct
from capture import HERE, Image

FUNCTIONS={
    'population_register_updates':0xDAB09C,
    'callback_early_thunk':0xEEB5DC,
    'callback_early_body':0x9B6664,
    'callback_main_builder':0x21D6A80,
    'callback_main_thunk':0xC6C6EC,
    'callback_main_body':0xC6C6F4,
    'callback_main_job_builder':0xC6C7B0,
    'callback_main_job_creator':0xC6C858,
    'callback_main_job':0xD32E84,
    'population_main_tick':0x4F6B5C,
    'population_descriptor_consumer':0x4F5C18,
    'population_record_insert':0x4F6440,
    'population_record_insert_body':0x4F6458,
    'population_pending_selection':0x4F6324,
    'population_pending_refresh':0x4F6064,
    'callback_second_builder':0x21D68F0,
    'callback_second_body':0xDD6654,
    'callback_late_builder':0x21D6970,
    'callback_late_body':0xE9A784,
    'callback_late_job_builder':0x21DA980,
    'callback_late_job':0x21DAD10,
    'population_manager_update':0x298B68,
    'stub_component_attach':0x2FBC1C,
    'stub_component_initialize':0x2FAF14,
}

def main():
    out=HERE/'evidence_02.json'
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
            f['boundary_limit']='No unwind boundary; first JMP/RET only. Explicit nextbody captured separately.'
        return f
    def qword(a):return struct.unpack_from('<Q',im.data,im.off(a))[0]-im.base
    checks=[]
    def ck(n,v,e):checks.append({'name':n,'pass':bool(v),'evidence':e})
    ck('actual_population_RegisterUpdates_slot',qword(0x3677070+0x108)==0xDAB09C,'constructedinstancevtable')
    for v,a in [(0x3956A48,0xEEB5DC),(0x39569C8,0xC6C6EC),(0x39569E8,0xDD6654),(0x3956A08,0xE9A784)]:
        ck('registered_callback_'+hex(v),qword(v)==a,hex(a))
    rows=capture(0x4F5C18)['instructions']
    ck('consumer_loads_exact_queue60',any(x['rva']=='0x4f5d69' and x['operands']=='rdx, [rdi + 0x60]'for x in rows),'afterlock+58')
    ck('consumer_uses_descriptor_ID28',any(x['rva']=='0x4f5da0' and x['operands']=='r14, [rsi + 0x28]'for x in rows),'sameIDusedfortable/stublookup')
    ck('consumer_steps_exact_descriptor_stride38',any(x['rva']=='0x4f5eca' and x['operands']=='rsi, 0x38'for x in rows),'structuredqueueiteration')
    result={'status':'REGISTERED_CALLBACK_AND_DESCRIPTOR_CONSUMER_BOUND_ACTOR_ASSIGNMENT_UNRESOLVED',
        'exe_sha256':im.sha,'predecessor_sha256':hashlib.sha256((HERE/'evidence_01.json').read_bytes()).hexdigest().upper(),
        'functions':{k:capture(v)for k,v in FUNCTIONS.items()},'checks':checks,
        'controls_status':'PASS'if all(x['pass']for x in checks)else'FAIL',
        'registered_queue_path':'PopulationSystemv108DAB09C→21D6A80→39569C8/C6C6EC→C6C6F4→C6C7B0→C6C858→D32E84→4F6B5C→4F5C18',
        'source_confirmed':'4F5C18drainsqueue+60underlock+58,usesdescriptorID32+28toFindStubandinsertrecordinmap+F8;pendingselectionmap+128receivessameID.',
        'remaining_boundary':{
            'proven_source':'Per-IDPopulationSystemrecordmap+0xF8 and pendingselection+0x128, createdfromdescriptor+0x28 and stubpointer.',
            'proven_destination':'EntityInitializeRequest+0x20→entEntity+0x48 in71BEF0;71BD9C passesrequestfromjobcontext+0x10.',
            'missing':'Thepopulationmaterialization/spawn-jobproducerthatconstructsthisEntityInitializeRequestwasnotboundtothisper-IDrecord. Registeredqueueconsumptiondoesnotfilltheidentitygap.',
            'excluded_inference':'No guarantee of unchanged actual actorID, no positive remapfinding, no inference from direct-caller miss alone.'},
        'decision':'Still insufficient for an actor-specific setup guard or car-state absence certificate. No game command or runtime repair follows.',
        'game_calls':0,'original_save_reads':0,'save_writes':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'controls':result['controls_status'],
       'checks':len(checks),'failures':[x['name']for x in checks if not x['pass']],
       'sha256':hashlib.sha256(out.read_bytes()).hexdigest().upper()}))

if __name__=='__main__':main()
