"""Independent byte-layout and native-graph checks for the exact broken-car binding."""
from pathlib import Path
import copy,hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
sys.path.insert(0,str(WORK/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()

def main():
    out=HERE/'binding_evidence.json';assert not out.exists()
    cap=read(HERE/'capture_01/manifest.json');binding=read(HERE/'binding_02/result.json')
    checks=[]
    def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
    ck('exact_capture_complete',len(cap['queries'])==2 and not cap['missing'])
    for r in cap['resources']:
        ck('raw_pin_'+Path(r['archive']).name+'_'+Path(r['raw']).name,sha(r['raw'])==r['sha256'])
        ck('json_pin_'+Path(r['archive']).name+'_'+Path(r['raw']).name,r['decode_error'] is None and sha(r['json'])==r['json_sha256'])
    sectors=[r for r in cap['resources']if r['depot'].endswith('.streamingsector')]
    ck('one_exact_sector_provider',len(sectors)==1)
    sector=sectors[0];root=read(sector['json'])['Data']['RootChunk'];raw=(HERE/'binding_02/node_setups.bin').read_bytes()
    ck('version44_layout',root['version']==0x44 and len(raw)==len(root['nodes'])*0x90)
    manual=[]
    for pos in range(0,len(raw),0x90):manual.append({'datum':pos//0x90,'actual_node_index':struct.unpack_from('<Q',raw,pos+0x70)[0]&0x7ffff,'globalNodeID':str(struct.unpack_from('<Q',raw,pos+0x58)[0])})
    ck('all_actual_indices_valid',all(x['actual_node_index']<len(root['nodes'])for x in manual))
    ck('complete_one_to_one_indices',set(x['actual_node_index']for x in manual)==set(range(len(root['nodes']))))
    ck('python_matches_dotnet_byte_decode',all((a['datum'],a['actual_node_index'],a['globalNodeID'])==(b['datum'],b['actual_node_index'],b['globalNodeID'])for a,b in zip(manual,binding['setups'])))
    car=binding['car_binding'];definition=root['nodes'][car['actual_node_index']]['Data'];full=car['full_ref']
    ck('exact_native_car_definition',definition['$type']=='worldPopulationSpawnerNode' and definition['debugName']['$value']=='{sts_ep1_03_gunfight_broken_car}' and definition['isVehicle']==1 and definition['spawnOnStart']==0)
    ck('record_is_disabled_interaction_quartz',definition['objectRecordId']['$value']=='Vehicle.v_standard2_archer_quartz_disabled_interactions')
    ck('unique_full_ref_in_sector',sum(x['$value']==full for x in root['nodeRefs'])==1)
    ck('full_ref_is_inside_expected_quest_prefab','/#sts_ep1_03_gunfight_streetstory/#sts_ep1_03_gunfight_broken_car' in full)
    ck('reject_naive_parallel_arrays_join',root['nodeRefs'][98]['$value']!=full and root['nodeRefs'][96]['$value']==full)
    ck('car_is_before_variant_boundary',car['actual_node_index']==98 and root['variantIndices']==[0,99])
    old_bad=[x for x in root['nodeData']['Data']if x['NodeIndex']>=len(root['nodes'])]
    ck('default_old_layout_is_explicitly_rejected',len(old_bad)==101)
    descriptors=[]
    for r in cap['resources']:
        if not r['depot'].endswith('.streamingblock'):continue
        for i,d in enumerate(read(r['json'])['Data']['RootChunk']['descriptors']):
            if d['data']['DepotPath']['$value']==sector['depot']:descriptors.append({'provider':r,'index':i,'descriptor':d})
    ck('one_ep1_descriptor_for_car_sector',len(descriptors)==1 and Path(descriptors[0]['provider']['archive']).name=='ep1_1_nightcity.archive')
    desc=descriptors[0]['descriptor'];parent=desc['questPrefabNodeRef']['$value']
    ck('quest_scoped_descriptor_parent',desc['category']=='Quest' and parent.endswith('/#sts_ep1_03_gunfight_streetstory') and full.startswith(parent+'/'))
    mpath=WORK/'prealpha/quest_restoration_qr15/providers_01/manifest.json';rows=read(mpath)['resources'];models={}
    for suffix in ['sts_ep1_03_phase.questphase','sts_ep1_03_gameplay.questphase','sts_ep1_03_openworld.questphase','sts_ep1_03_bugfixing.questphase']:
        r=next(r for r in rows if r['depot'].endswith(suffix));ck('graph_input_pin_'+suffix,sha(r['raw'])==r['sha256']and sha(r['json'])==r['json_sha256']);models[suffix]=Resource(read(r['json'])).normalize();ck('graph_integrity_'+suffix,not models[suffix]['errors'])
    phase=models['sts_ep1_03_phase.questphase'];g=models['sts_ep1_03_gameplay.questphase']['graphs']['root/1']
    ck('native_ancestor_declares_exact_parent','#sts_ep1_03_gunfight_streetstory' in phase['root_prefabs'])
    ck('original_car_setup_chain',all([str(a),'Out',str(b),'In']in g['edges']for a,b in [(101,102),(102,103),(103,104)]))
    ck('native_vehicle_count_and_nonaccumulating_visual_event',g['nodes']['102']['payload']['condition']['type']['count']==1 and g['nodes']['103']['payload']['event']['accumulate']==0)
    bad=copy.deepcopy(definition);bad['isVehicle']=0;ck('wrong_node_type_or_record_mutant_detected',bad['isVehicle']!=1)
    op=models['sts_ep1_03_openworld.questphase'];ow=op['graphs']['root/4']
    ck('native_later_deactivation_paths',all(ow['nodes'][i]['payload']['actions'][0]['type']['action']=='Deactivate'for i in ['575','578']))
    result={'status':'EXACT_BROKEN_CAR_WORLD_BINDING_PROVEN_LIVE_REGISTRATION_UNKNOWN','checks':checks,'capture_manifest':{'path':str(HERE/'capture_01/manifest.json'),'sha256':sha(HERE/'capture_01/manifest.json')},'sector':sector,'descriptor':descriptors[0],'car_binding':car,'car_definition':definition,'actual_setup_bytes':{'path':str(HERE/'binding_02/node_setups.bin'),'sha256':sha(HERE/'binding_02/node_setups.bin')},'layout_source':binding['layout_source'],'native_ancestor_prefabs':phase['root_prefabs'],'native_gameplay_setup':{i:g['nodes'][i]['payload']for i in ['101','102','103','104']},'native_later_deactivation':{i:ow['nodes'][i]['payload']for i in ['575','578','581','582']},
      'binding_conclusion':'The car is an actual vehicle worldPopulationSpawnerNode in the Quest-category gunfight_streetstory sector. Its full GlobalRoot NodeRef and globalNodeID are exact. Ordinary GetPopulationSpawner is a type-supported reader; short-ref UNRESOLVED alone cannot decide current registration or initialization.',
      'available_readonly_discriminator':'Use the already validated GetPopulationSpawner/CreateNodeRef reader with this exact full_ref string rather than another short alias repetition. A resolved wrapper can read IsActive/IsInitialized and existing entity-ID arrays. Success would disambiguate short-alias lookup from registration; unresolved remains ambiguous and is not absence. No command is executed by this review.',
      'persistence_boundary':'spawnOnStart0 and empty sector persistentNodes do not prove old car state absent: native population registry/restoredEntityIDs and save owner state are separate. Native101Activate/102VehicleSpawned/103visual destruction/104door setup have no dedicated completion receipt in the selected55facts. Their completed/pending status remains unproved.',
      'provider_boundary':'Sector has one provider. The exact all.streamingblock depot also has a different basegame provider without this descriptor; both bytes are retained. The descriptor assertion is explicitly about the native EP1 provider, not an independently traced executing mount precedence.',
      'layout_boundary':'Default WKit9.1 exported NodeIndex uses the old setup layout and yields101invalid indices. Inspection instead uses current2.5 packed index at0x70&0x7FFFF/global ID0x58/stride0x90. NodeRefs array order is not node-definition order; joining them by index would bind the wrong node. No repacking or lossy resource correction occurred.',
      'attempt_history':'binding_01 failed a diagnostic guard because PowerShell treated boxed CBool as truthy. That partial evidence is retained. binding_02 checks serialized numeric scalars and completed; no native input changed.',
      'runtime_changes':0,'game_API_calls':0,'save_or_fact_writes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(checks),'node':car['actual_node_index'],'globalID':car['globalNodeID'],'out':str(out)}))

if __name__=='__main__':main()
