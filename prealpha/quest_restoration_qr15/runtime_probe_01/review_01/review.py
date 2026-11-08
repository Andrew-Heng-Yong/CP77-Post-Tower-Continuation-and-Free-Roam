"""Independent source/syntax review; no Game or CET APIs are executed."""
from pathlib import Path
import argparse, hashlib, json, re, sys

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
PROBE=HERE.parent
sys.path.insert(0,str(WORK/'prealpha/quest_restoration_qr9/worker_b/tooling'))
from lupa.luajit21 import LuaRuntime

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    out=HERE/args.out;assert out.parent==HERE and not out.exists()
    game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
    api=game/'red4ext/plugins/Codeware/Scripts/Codeware.Global.reds'
    src=WORK/'research/framework_pr63_01/codeware/src/App/World'
    text=api.read_text();checks=[]
    def ck(n,b):checks.append({'name':n,'pass':bool(b)});assert b,n
    chunks={n:(PROBE/(n+'.command.txt')).read_text().strip() for n in ['facts','world']}
    allowed={'GetPlayer','IsAttached','GetQuestsSystem','GetFactStr','GetWorldStateSystem','IsReady','GetCommunity','CreateNodeRef','GetEntries','IsActive','GetPopulationSpawner','IsInitialized'}
    lua=LuaRuntime(unpack_returned_tuples=True)
    for name,chunk in chunks.items():
        # Compile only; never evaluate the returned chunk against live interfaces.
        loaded=lua.eval('function(s) return loadstring(s) end')(chunk)
        ck(name+'_independent_luajit_syntax',callable(loaded))
        methods=set(re.findall(r'(?:Game\.|:)(\w+)\s*\(',chunk))
        ck(name+'_all_engine_methods_are_readers',methods<=allowed)
        ck(name+'_no_install_io_events_timers_setters',not re.search(r'\b(?:SetFact|Activate|Deactivate|Reset|Observe|Override|registerForEvent|io|os|require|dofile|loadfile|ExecuteNode)\b',chunk))
    ck('community_signature_in_exact_class','public native func GetCommunity(community: NodeRef) -> ref<CommunityWrapper>' in text.split('public native class WorldStateSystem',1)[1].split('@addMethod',1)[0])
    ck('spawner_signature_in_exact_class','public native func GetPopulationSpawner(spawner: NodeRef) -> ref<PopulationSpawnerWrapper>' in text.split('public native class WorldStateSystem',1)[1].split('@addMethod',1)[0])
    ck('community_entries_signature_in_exact_class','GetEntries() -> array<ref<CommunityEntryWrapper>>' in text.split('public native class CommunityWrapper',1)[1].split('\n}',1)[0])
    ck('spawner_readers_in_exact_class',all(s in text.split('public native class PopulationSpawnerWrapper',1)[1].split('\n}',1)[0] for s in ['IsActive() -> Bool','IsInitialized() -> Bool']))
    ck('node_ref_script_ref_string_signature','public native func CreateNodeRef(value: script_ref<String>) -> NodeRef' in text)
    ck('gameinstance_static_world_api','@addMethod(GameInstance)\npublic static native func GetWorldStateSystem() -> ref<WorldStateSystem>' in text.replace('\r\n','\n'))
    cxx=(src/'WorldStateSystem.cpp').read_text()
    community=cxx.split('WorldStateSystem::GetCommunity(',1)[1].split('WorldStateSystem::ActivateCommunity(',1)[0]
    spawner=cxx.split('WorldStateSystem::GetPopulationSpawner(',1)[1].split('WorldStateSystem::ActivatePopulationSpawner(',1)[0]
    ck('corroborating_getters_only_resolve_existing_objects',all('ResolveNodeRef' in s and '.Lock()' in s and 'MakeHandle<' in s for s in [community,spawner]) and not any(x in community+spawner for x in ['ActivateCommunity(','ActivatePopulationSpawner(','CommunitySystem::Update','ResetCommunity(','ResetPopulationSpawner(']))
    ck('facts_fixed_eight_reads',len(re.findall(r'"(?:sts_ep1_03_start_community|sa_ep1_\w+|PTFRU9_sts_ep1_03_\w+|q307_ep1_killed)"',chunks['facts']))==8)
    ck('world_fixed_two_community_one_spawner_queries',chunks['world'].count('w:GetCommunity(')==1 and chunks['world'].count('w:GetPopulationSpawner(')==1 and chunks['world'].count('#sts_ep1_03_')==3 and 'if i > 64 then return "TRUNCATED" end' in chunks['world'])
    ck('unknown_and_error_paths_explicit','"UNRESOLVED"' in chunks['world'] and '"ERROR:"' in chunks['world'] and '"ERROR:"' in chunks['facts'])
    pins=[{'path':str(p),'sha256':sha(p)}for p in [api,game/'red4ext/plugins/Codeware/Codeware.dll',src/'WorldStateSystem.cpp',src/'CommunityWrapper.cpp',src/'PopulationSpawnerWrapper.cpp',PROBE/'facts.command.txt',PROBE/'world.command.txt',PROBE/'facts.lua',PROBE/'world.lua',PROBE/'validation_01.json',Path(__file__)]]
    result={'status':'APPROVED_BOUNDED_READ_ONLY_DIAGNOSTIC_WITH_EXPLICIT_LIMITS','checks':checks,'source_pins':pins,'blocking_findings':[],
      'source_confirmed':['Exact installed declarations match receiver/argument/result shapes.','Corroborating local C++ getter bodies resolve existing objects and read wrapper state; no activate/reset/update path is used.','Fixed fact list, two communities, one spawner, limited Lua entry traversal and short logging.'],
      'not_proven':['Actual live CET binding of Game.CreateNodeRef/script_ref<String> and wrapper arrays; a real read-only command observation is still needed.','Binary-body equivalence of local C++ source with installed Codeware.dll.','Executing quest-owner tree, native/private listener retirement, exact saved pending node, acquired prefab lease or safe restoration adapter.'],
      'interpretation':['Facts add missing shared-courier state; preserve values/errors literally, never infer missing zero.','Resolved active/initialized wrapper readings narrow current community/spawner state and may rule out a fresh-state assumption.','All zero/inactive values still do not prove saved-owner retirement or permit a repair.','UNRESOLVED may reflect native-short-reference context, streaming or lookup limits; it does not prove absent/inactive ownership.','TRUNCATED/ERROR/WORLD_NOT_READY are incomplete evidence, not defects or successful negative observations.'],
      'boundedness_limit':'Lua processes at most64entries per queried community and prints about5world lines. Native GetEntries() first materializes that community array; the Lua cap is not a hard native-allocation cap. Two fixed quest-specific communities keep this a bounded target query, not a world census.',
      'workflow':'A single pair of read-only snapshots on the current working save is useful. No quest replay, travel prerequisite, save/fact mutation, installation or repeated successful route is required. Do not promise these two outputs alone will authorize a gameplay fix.',
      'real_game_API_calls':0,'runtime_changes':0,'save_or_fact_writes':0}
    out.mkdir();(out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'blocking_findings':0,'result':str(out/'review.json')}))

if __name__=='__main__':main()
