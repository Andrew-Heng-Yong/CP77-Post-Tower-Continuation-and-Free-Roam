"""Fresh successor: exact population materializer and request-ID preservation."""
from pathlib import Path
import hashlib,json,struct
from capture import HERE, Image

FUNCTIONS={
    'population_selection':0x3C2E0C,
    'pending_iterator_key':0x3C3A78,
    'population_selected_spawn':0x537D4C,
    'population_materializer':0x4F7D80,
    'entity_id_wrap_u64':0x409320,
    'population_world_attach':0x96DA58,
    'runtime_entity_system_spawner_setup':0x9D5A44,
    'entity_spawner_factory_install':0x11DA620,
    'entity_spawner_factory_install_modes':0x25B32FE,
    'entity_spawner_dispatch':0x5C140C,
    'entity_spawner_request_factory':0x5C1508,
    'entity_spawn_context_factory':0xC82270,
    'entity_spawn_context_ctor':0xC822E4,
    'entity_spawn_context_set_request':0x719F40,
    'entity_spawn_request_heap_copy':0x719FE8,
    'entity_initialize_request_copy':0x719D68,
    'entity_spawn_local_job_start':0x71A170,
    'entity_spawn_local_job_builder':0x71A2B8,
    'entity_spawn_local_job_creator':0x71B480,
    'entity_spawn_local_job':0x71A38C,
    'entity_spawn_local_job_body':0x7191E0,
}

def main():
    out=HERE/'evidence_03.json'
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
            f['boundary_limit']='No unwind boundary; stop at first JMP/RET'
        return f
    def raw(a,h):
        b=bytes.fromhex(h)
        return im.data[im.off(a):im.off(a)+len(b)]==b
    def direct(a,target):
        p=im.off(a)
        return im.data[p]in(0xE8,0xE9)and a+5+struct.unpack_from('<i',im.data,p+1)[0]==target
    checks=[]
    def ck(n,v,e):checks.append({'name':n,'pass':bool(v),'evidence':e})
    ck('selection_uses_pending128',raw(0x3C2EF5,'4c8daf28010000'),'pendingmap')
    ck('selection_reads_actual_uint32_key',raw(0x3C2F45,'8b18'),'iterator3C3A78returnskeyarrayelement')
    ck('selection_encodes_key_above_flag_bits',raw(0x3C3105,'48c1e008'),'IDshift8;flagslow8')
    ck('selected_spawn_decodes_key',raw(0x537D61,'8b5204') and raw(0x537D67,'c1ea08'),
       'ID24frompackedentry;targetlossless')
    ck('selected_materializer_call',direct(0x537E67,0x4F7D80),'sameIDrecordpair')
    ck('materializer_copies_ID',raw(0x4F7ECD,'8b17') and direct(0x4F7EE9,0x409320) and raw(0x4F7EFD,'48894dd0'),
       'inputID32→EntitySpawnerRequest+30')
    ck('materializer_dispatches_actual_spawner',direct(0x4F810B,0x5C140C),'R8requestbaseRBP-60')
    ck('world_attach_selects_runtime_entity_spawner',raw(0x96DAA3,'488b83a0000000') and raw(0x96DAAA,'488b4858'),
       'scene+A0→RuntimeEntitySystem+58')
    ck('factory_virtual8_is_request_factory',struct.unpack_from('<Q',im.data,im.off(0x3617C00+8))[0]==im.base+0x5C1508,
       'factoryvt3617C00')
    ck('spawner_factory_installs_on68',raw(0x11DA679,'48894768'),'dispatch5C140Cuses+68virtual8')
    ck('request_factory_moves_ID_to_initializer20',raw(0x5C1552,'498b4030') and raw(0x5C1556,'4889442460'),
       'source+30→localinitrequestbaseRSP40 +20')
    ck('heap_request_copy_keeps_ID20',raw(0x719DAC,'488b4220') and raw(0x719DB0,'48894120'),
       '719FE8clonesusing719D68')
    ck('spawn_context_stores_copied_request10',raw(0x719F92,'488d5310'),'parametershandleatcontext+10')
    ck('target_pack_unpack_is_lossless',((10229047<<8)&0xFFFFFFFF)>>8==10229047,'target24bit')
    key=17113219195054135786
    result={'status':'CONDITIONAL_STATIC_POPULATION_REQUEST_IDENTITY_PROVED_DISPATCH_LIMIT_VISIBLE',
        'exe_sha256':im.sha,'functions':{k:capture(v)for k,v in FUNCTIONS.items()},'checks':checks,
        'controls_status':'PASS'if all(x['pass']for x in checks)else'FAIL',
        'predecessors':{p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper()for p in(HERE/'evidence_01.json',HERE/'evidence_02.json')},
        'proven_request_path':'per-IDpending128/recordF8→3C2E0C(packID<<8)→537D4C(unpack>>8)→4F7D80→EntitySpawnerRequest+30→5C140C/factoryvirtual8=5C1508→EntityInitializeRequest+20→719F40/719FE8/719D68heapcopy+20→spawncontext+10',
        'conditional_actor_property':'TheboundordinaryEntityInitialize71BEF0copiesrequest+20toentEntity+48unchanged. Ifthisconstructedspawncontextreachesthatconsumer,thereisnoIDsubstitutiononthetracedparameterpath.',
        'dispatch_limit':'Localjobchain71A170→71A2B8→71B480→71A38C→7191E0wasbound;itslaterhandoffto71BD9Cwasnot. Noactualmaterialization,currentbodyorreloadlivenessisinferred.',
        'canonical_stub_key':{'entity_candidate_u64':'10229047','component':'vehiclePersistentDataPS',
            'key_u64':str(key),'requires_actor48_link':False,
            'proof':'Native9A24E4constructsPIDdirectlyfromEntityStub+40andtheexactcomponentCName,then9A2514.'},
        'decision':'Canonicalstub-keyabsenceisvalidasabsenceatthatcapturedaddress;notaproofofactualcarstateabsenceorstage. NoIDremapontheboundparameterpath;no globalclaimaboutallactors or restoredaliases.',
        'game_calls':0,'original_save_reads':0,'save_writes':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'controls':result['controls_status'],'checks':len(checks),
       'failures':[x['name']for x in checks if not x['pass']],
       'sha256':hashlib.sha256(out.read_bytes()).hexdigest().upper()}))

if __name__=='__main__':main()
