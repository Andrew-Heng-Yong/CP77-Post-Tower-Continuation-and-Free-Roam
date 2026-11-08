"""Offline syntax, reader-only API and fault controls for two manual CET commands."""
from pathlib import Path
import hashlib,json,re,sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
sys.path.insert(0,str(WORK/'prealpha/quest_restoration_qr9/worker_b/tooling'))
from lupa.luajit21 import LuaRuntime

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

MOCK=r'''
lines={}; calls={writes=0,facts=0,world=0,entries=0}; print=function(s) lines[#lines+1]=tostring(s) end
local function deny(_,k) if tostring(k):match("^Set") or tostring(k):match("^Activate") or tostring(k):match("^Deactivate") or tostring(k):match("^Reset") then calls.writes=calls.writes+1 end error("UNEXPECTED_API:"..tostring(k)) end
local function ro(t) return setmetatable(t,{__index=deny}) end
local p=ro({IsAttached=function()return not cfg.detached end})
local q=ro({GetFactStr=function(_,n) calls.facts=calls.facts+1;if cfg.facterror then error("READ_FAILED")end;if n=="sa_ep1_114_toggledoff_force" then return cfg.force or 0 end;return 1 end})
local c=ro({GetEntries=function() local es={};for i=1,(cfg.entrycount or 2) do es[i]=ro({IsActive=function()calls.entries=calls.entries+1;return i==1 end})end;return es end})
local s=ro({IsInitialized=function()return true end,IsActive=function()return false end})
local w=ro({IsReady=function()return not cfg.notready end,GetCommunity=function(_,r) calls.world=calls.world+1;if cfg.worlderror then error("WORLD_GETTER_FAILED")end;if cfg.unresolved then return nil end;return c end,GetPopulationSpawner=function()calls.world=calls.world+1;if cfg.unresolved then return nil end;return s end})
Game=ro({GetPlayer=function()if cfg.noplayer then return nil end;return p end,GetQuestsSystem=function()return q end,GetWorldStateSystem=function()if cfg.noapi then error("NO_WORLD_API")end;return w end,CreateNodeRef=function(r)if cfg.referror then error("REF_ERROR")end;return r end})
'''
def run(text,cfg):
    lua=LuaRuntime(unpack_returned_tuples=True);lua.globals().cfg=lua.table_from(cfg);lua.execute(MOCK);lua.execute(text)
    lines=list(lua.globals().lines.values());calls=dict(lua.globals().calls.items())
    return lines,calls

def main():
    out=HERE/'validation_01.json';assert not out.exists()
    checks=[]
    def ck(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    chunks={n:(HERE/(n+'.command.txt')).read_text().strip() for n in ['facts','world']}
    permitted={'GetPlayer','IsAttached','GetQuestsSystem','GetFactStr','GetWorldStateSystem','IsReady','GetCommunity','CreateNodeRef','GetEntries','IsActive','GetPopulationSpawner','IsInitialized'}
    for n,chunk in chunks.items():
        calls=set(re.findall(r'(?:Game\.|:)([A-Za-z_][A-Za-z_0-9]*)\s*\(',chunk))
        ck(n+'_strict_reader_call_allowlist',calls<=permitted)
        ck(n+'_no_event_hook_timer_or_file_io',not re.search(r'\b(register|Observe|Override|io\.|os\.|dofile|loadfile|loadstring|SetFact|ExecuteNode)',chunk))
        ck(n+'_single_line',len(chunk.splitlines())==1)
        a,counts=run(chunk,{})
        b,_=run((HERE/(n+'.lua')).read_text(),{})
        ck(n+'_one_line_matches_multiline_execution',a==b and counts['writes']==0)
        for key in ['noplayer','detached']:
            lines,calls=run(chunk,{key:True});ck(n+'_'+key+'_no_world_or_fact_reads',calls['facts']==0 and calls['world']==0 and 'LOAD_SAVE_FIRST' in ' '.join(lines))
    lines,calls=run(chunks['facts'],{'force':3})
    ck('existing_nonzero_shared_value_preserved_in_output',any('sa_ep1_114_toggledoff_force=3' in l for l in lines) and calls['writes']==0)
    lines,_=run(chunks['facts'],{'facterror':True});ck('read_failure_not_default_zero',sum('ERROR:' in l for l in lines)==8 and not any(l.endswith('=0') for l in lines))
    lines,calls=run(chunks['world'],{})
    ck('world_snapshot_reports_counts_and_spawner_readings',sum('entries=2 active=1' in l for l in lines)==2 and any('initialized=true active=false' in l for l in lines) and calls['writes']==0)
    lines,calls=run(chunks['world'],{'notready':True});ck('world_not_ready_no_queries',calls['world']==0 and any('WORLD_NOT_READY' in l for l in lines))
    lines,_=run(chunks['world'],{'unresolved':True});ck('unresolved_is_not_reported_inactive_or_absent',sum('UNRESOLVED' in l for l in lines)==3 and not any('active=false' in l or 'entries=0' in l for l in lines))
    for key in ['worlderror','referror','noapi']:
        lines,calls=run(chunks['world'],{key:True});ck('guarded_'+key,any('ERROR:' in l for l in lines) and calls['writes']==0)
    lines,calls=run(chunks['world'],{'entrycount':65});ck('entry_loop_bounded',sum('TRUNCATED' in l for l in lines)==2 and calls['entries']==128)
    _,calls=run(chunks['world'].replace('w:GetCommunity(','w:ActivateCommunity('),{})
    ck('deliberate_writer_mutant_rejected_by_tripwire',calls['writes']==2)
    manifest=WORK/'prealpha/quest_restoration_qr14/deployment_01/installed_manifest_01.json';m=read(manifest);game=Path(m['game_root'])
    api=game/'red4ext/plugins/Codeware/Scripts/Codeware.Global.reds';text=api.read_text()
    required=['public native func GetCommunity(community: NodeRef)','public native func GetPopulationSpawner(spawner: NodeRef)','public native func GetEntries()','public native func IsInitialized()','public native func CreateNodeRef(value: script_ref<String>)','public static native func GetWorldStateSystem()']
    ck('exact_installed_API_declarations_present',all(x in text for x in required))
    protected=[]
    for r in m['core_files']+m['required_files']:
        p=game/r['path'];actual=sha(p);ck('installed_pin_'+r['path'],actual==r['sha256']);protected.append({'path':str(p),'sha256':actual})
    source=WORK/'research/framework_pr63_01/codeware/src/App/World'
    pins=[{'path':str(p),'sha256':sha(p)}for p in [api,game/'red4ext/plugins/Codeware/Codeware.dll',source/'WorldStateSystem.cpp',source/'CommunityWrapper.cpp',source/'PopulationSpawnerWrapper.cpp',WORK/'research/framework_pr63_01/codeware/src/Red/NodeRef.hpp',Path(__file__),manifest]]
    result={'status':'PASS_OFFLINE_READ_ONLY_COMMAND_CONTROLS_AWAITING_HUMAN_OUTPUT','checks':checks,'command_pins':{n:{'path':str(HERE/(n+'.command.txt')),'sha256':sha(HERE/(n+'.command.txt')),'characters':len(chunk)}for n,chunk in chunks.items()},'source_pins':pins,'protected_installed_inputs':protected,'real_game_API_calls':0,'native_owner_query':False,'limits':['Offline mocks prove syntax/control/error behavior, not real Lua binding delivery or native state.','Installed API and compiled project use support the getters; local C++ source is corroboration, not full binary-body equivalence.','Short native NodeRefs are preserved exactly; unresolved may mean context/streaming/lookup limitation, never owner absence.','World readings and facts do not enumerate the executing quest-owner tree.']}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'installed_pins':len(protected),'commands':[len(x)for x in chunks.values()],'result':str(out)}))

if __name__=='__main__':main()
