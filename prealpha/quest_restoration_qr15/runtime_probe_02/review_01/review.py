"""Independent review of the single absolute-car reader. No live Game APIs."""
from pathlib import Path
import hashlib,json,re,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
PROBE=HERE.parent
sys.path.insert(0,str(WORK/'prealpha/quest_restoration_qr9/worker_b/tooling'))
from lupa.luajit21 import LuaRuntime
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def main():
    dest=HERE/'review.json';assert not dest.exists()
    cmd=(PROBE/'car.command.txt').read_text().strip();multiline=(PROBE/'car.lua').read_text()
    binding=HERE.parents[1]/'runtime_probe_01/car_binding_review_01/binding_evidence.json'
    b=read(binding);validation=read(PROBE/'validation_01.json');checks=[]
    def ck(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    lua=LuaRuntime(unpack_returned_tuples=True)
    for name,chunk in [('copy_command',cmd),('multiline',multiline)]:
        ck(name+'_independent_syntax',callable(lua.eval('function(s) return loadstring(s) end')(chunk)))
    methods={'GetPlayer','IsAttached','GetWorldStateSystem','IsReady','CreateNodeRef','GetPopulationSpawner','IsInitialized','IsActive','GetSpawnedEntityIDs','GetRestoredEntityIDs','GetReservedEntityIDs'}
    ck('strict_reader_method_allowlist',set(re.findall(r'(?:Game\.|:)(\w+)\s*\(',cmd))<=methods)
    ck('no_external_io_hooks_timers_or_mutators',not re.search(r'\b(?:Activate|Deactivate|Reset|SetFact|ExecuteNode|Observe|Override|registerForEvent|require|io|os|dofile|loadfile)\b',cmd))
    ck('only_one_spawner_lookup',cmd.count(':GetPopulationSpawner(')==1 and 'for ' not in cmd and 'while ' not in cmd)
    ck('exact_absolute_extracted_native_reference',b['car_binding']['full_ref'] in cmd and b['car_binding']['full_ref'].startswith('$/'))
    ck('target_is_typed_vehicle_spawner',b['car_definition']['$type']=='worldPopulationSpawnerNode' and b['car_definition']['isVehicle']==1)
    ck('no_unsafe_lua_numeric_node_id',b['car_binding']['globalNodeID'] not in cmd)
    ck('unknown_and_errors_not_coerced_to_zero',all(x in cmd for x in ['ABSOLUTE_CAR_UNRESOLVED','WORLD_NOT_READY','ERROR:','LOAD_SAVE_FIRST']))
    game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
    declarations=game/'red4ext/plugins/Codeware/Scripts/Codeware.Global.reds';d=declarations.read_text();klass=d.split('public native class PopulationSpawnerWrapper',1)[1].split('\n}',1)[0]
    getters={'GetSpawnedEntityIDs':'spawnedEntityIDs','GetRestoredEntityIDs':'restoredEntityIDs','GetReservedEntityIDs':'reservedEntityIDs'}
    source=WORK/'research/framework_pr63_01/codeware/src/App/World/PopulationSpawnerWrapper.cpp';cpp=source.read_text();bodies={}
    for getter,field in getters.items():
        ck(getter+'_installed_return_signature','public native func '+getter+'() -> array<EntityID>' in klass)
        body=cpp.split('PopulationSpawnerWrapper::'+getter+'() const',1)[1].split('\n}',1)[0];bodies[getter]=body
        ck(getter+'_corroborating_stored_array_only',('return spawner->'+field+';') in body and not re.search(r'Activate|Deactivate|Reset|Update|Queue|Dispatch|Set\w+|GetActiveEntityIDs',body))
    ck('no_virtual_active_entity_query',':GetActiveEntityIDs(' not in cmd)
    ck('three_list_lengths_no_entity_iteration',sum(cmd.count(':'+g+'(') for g in getters)==3 and all('#s:'+g+'()'in cmd for g in getters))
    ck('primary_fixtures_21_all_pass',len(validation['checks'])==21 and all(x['pass']for x in validation['checks']))
    for p in validation['inputs']:ck('primary_input_pin_'+Path(p['path']).name,sha(p['path'])==p['sha256'])
    inputs=[PROBE/'car.lua',PROBE/'car.command.txt',PROBE/'validation_01.json',binding,declarations,source,game/'red4ext/plugins/Codeware/Codeware.dll',Path(__file__)]
    result={'status':'APPROVED_SINGLE_ABSOLUTE_CAR_READ_ONLY_PROBE','blocking_findings':[],'checks':checks,'source_pins':[{'path':str(p),'sha256':sha(p)}for p in inputs],
      'usefulness':'Genuinely new discriminator: exact source-proven absolute world reference replaces the old short alias. A successful result can establish currently registered wrapper/state/stored lists that JF01 could not read. This is one lookup, not a repeated generic fact or quest test.',
      'native_getter_review':{'mutating_calls_found':False,'const_stored_array_bodies':bodies,'scope':'Current installed method declarations plus corroborating local native source. DLL-body and underlying game ABI equivalence are not established by this review.'},
      'interpretation':['ABSOLUTE_CAR_UNRESOLVED leaves registration/context/prefab state unknown; it is not absent car or safe fresh initialization.','IsInitialized/IsActive are population-spawner flags, not the native quest phase execution or completed car event/door configuration.','spawned/restored/reserved are three stored array lengths; identities may overlap and entries are not guaranteed distinct living/rendered cars. Do not sum into unique population.','A successful reader result does not prove native VehicleSpawned predicate equivalence, visual-destruction completion, door state, old owner retirement or a safe repair.','ERROR/LOAD_SAVE_FIRST/WORLD_NOT_READY report incomplete evidence without substituting zero.'],
      'boundedness':'One fixed-target lookup, five reader calls on a resolved wrapper, one output line, no polling/loops/timers/hooks. Native array getters copy stored arrays before Lua length is taken; no hard array-allocation cap is claimed.',
      'decision':'Safe and useful to ask once on the existing working save. Preserve current state, use no fact changes, quest starts, reload/replay or travel merely to force a positive result. Do not promise this output alone authorizes implementation.',
      'real_Game_calls':0,'runtime_changes':0,'save_or_fact_writes':0}
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(checks),'result':str(dest)}))

if __name__=='__main__':main()
