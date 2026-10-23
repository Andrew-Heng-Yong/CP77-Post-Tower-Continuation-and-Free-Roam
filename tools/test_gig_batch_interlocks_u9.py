"""Actual LuaJIT mocked U9 admission-hook tests; no engine/gameplay proof."""
import json, re, sys
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, sha
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

OUT=ROOT/'research/gig_restoration/gig_batch_u9'
LUA=ROOT/'diagnostics/PTFR_GigBatchU9/init.lua'
HELPER=ROOT/'redscript/PTFR_GigBatchU9/EntryInterlocks.reds'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
TARGETS=[
 ('PTFR.ActivityStateR3.NativeSupportU7','Start',['String']),
 ('PTFR.ActivityStateR3.NativePadreU6','Start',['String']),
 ('PTFR.ActivityStateR3.NativeReuseU1','Start',['String']),
 ('PTFR.ActivityStateR3.NativeJeopardyU4','Start',['String']),
 ('PTFR.ActivityStateR3.NativeHeywoodU8','Start',['String','String']),
 ('PTFR.ActivityStateR3.GigFamilyB7','Restore',['String','Bool']),
 ('PTFR.ActivityStateR3.FreshGigsB5','RestoreFresh',['String']),
 ('PTFR.ActivityStateR3.FreshGigsB6','RestoreFresh',[]),
 ('PTFR.GigPilotR1.GigPilotR1','Restore',[]),
 ('PTFR.RiteG2.RiteG2','Restore',[]),
 ('PTFR.MinefieldG3.MinefieldG3','Restore',[])]

MOCK=r'''
state={events={},hooks={},overrides=0,facts={},originalCalls=0,dumps=0,reads=0}
local function sealed(t) return setmetatable(t,{__index=function(_,k) error('Unapproved API '..tostring(k)) end}) end
registerForEvent=function(name,fn) assert(name=='onInit' or name=='onShutdown');state.events[name]=fn end
DumpType=function(name,detailed)
  assert(detailed==false);state.dumps=state.dumps+1
  if state.badDump==name then error('bad RTTI') end
  local text=descriptors[name] or '{\n\tname: Unknown,\n\tfunctions: {\n\t},\n\tstaticFunctions: {\n\t}\n}'
  return setmetatable({},{__tostring=function() return text end})
end
Override=function(class,method,fn)
  state.overrides=state.overrides+1
  if state.throwHook==state.overrides then error('registration failure') end
  if state.dropHook==state.overrides then return end
  state.hooks[class..'.'..method]=fn
end
GetSingleton=function(name)
  assert(name=='GigBatchLockU9')
  if state.noBridge then return nil end
  return sealed({Ready=function()
    if state.readyError then error('bridge failure') end
    local hook=state.hooks['GigBatchLockU9.Probe;']
    if not hook then return false end
    return hook(function() return false end)
  end})
end
Game=sealed({GetQuestsSystem=function()
  if state.noQuests then error('quests unavailable') end
  return sealed({GetFactStr=function(_,name)
    state.reads=state.reads+1
    if state.badFact==name then error('fact unavailable') end
    if state.nilFact==name then return nil end
    return state.facts[name] or 0
  end})
end})
function invoke(key,...)
  local arguments={...};local n=select('#',...)
  arguments[n+1]=function(...)
    state.originalCalls=state.originalCalls+1;state.lastArgs={n=select('#',...),...}
    return 'ORIGINAL',false
  end
  return state.hooks[key]('SELF',unpack(arguments,1,n+1))
end
'''

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    source=LUA.read_text();helper=HELPER.read_text();pins={str(LUA.relative_to(ROOT)):sha(LUA),str(HELPER.relative_to(ROOT)):sha(HELPER)}
    actual=[]
    for cls,method,args in re.findall(r'\{"(PTFR\.[^"]+)", "(\w+)", \{([^}]*)\}\}',source):
        actual.append((cls,method,re.findall(r'"([^"]+)"',args)))
    assert actual==TARGETS
    assert helper.count('public static func')==2 and 'return false;' in helper
    for bad in ('let ','.SetFact','@wrapMethod','persistent'):assert bad not in helper
    for bad in ('SetFact','SetEntryState','ExecuteNode','io.','os.','Start(',':Restore','NewObject','registerHotkey'):
        assert bad not in source,bad
    # Independently verify exact signatures against the actually installed old
    # implementations, not the new runtime's target declarations.
    descriptors={}
    for cls,method,types in TARGETS:
        name=cls.rsplit('.',1)[1];path=GAME/f'r6/scripts/PTFR_{name}/{name}.reds'
        text=path.read_text(encoding='utf-8-sig');pins[str(path)]=sha(path)
        module=re.search(r'^module (\S+)',text).group(1);assert module+'.'+name==cls
        params=re.findall(r'public func '+method+r'\(([^)]*)\) -> String',text);assert len(params)==1
        assert re.findall(r':\s*(\w+)',params[0])==types
        descriptors[cls]='{\n\tname: '+cls+',\n\tfunctions: {\n\t\t'+method+'('+params[0]+') => (String),\n\t},\n\tstaticFunctions: {\n\t}\n}'
    descriptors['GigBatchLockU9']='{\n\tname: GigBatchLockU9,\n\tfunctions: {\n\t},\n\tstaticFunctions: {\n\t\tReady() => (Bool),\n\t\tProbe() => (Bool),\n\t}\n}'
    cases=0
    def fixture(setup=None):
        nonlocal cases
        lua=LuaRuntime(unpack_returned_tuples=True);lua.globals().descriptors=lua.table_from(descriptors)
        lua.execute(MOCK)
        if setup:lua.execute(setup)
        api=lua.execute(source);lua.globals().api=api;lua.execute("state.events.onInit()")
        cases+=1;return lua
    lua=fixture();assert lua.eval('api.Status()').startswith('U9 interlocks: registered=true preflight=11/11 probeCalls=1')
    assert lua.eval('state.originalCalls')==lua.eval('state.reads')==0
    assert lua.eval('state.overrides')==12
    lua.execute('state.events.onInit()');assert lua.eval('state.overrides')==12
    # Exact argument count/value preservation, including the false Bool and
    # method SELF omission from wrapped(), for every target.
    for index,(cls,method,types) in enumerate(TARGETS):
        key=cls+'.'+method;args=['id' if x=='String' else False for x in types]
        assert lua.globals().invoke(key,*args)==('ORIGINAL',False)
        got=lua.eval('state.lastArgs');assert got.n==len(args)
        for i,value in enumerate(args,1):assert got[i]==value
        cases+=1
    lua.execute('state.events.onShutdown()');assert lua.eval('GetSingleton("GigBatchLockU9"):Ready()') is False
    for fact in ['Request','Permit','Issued']:
        for value in (-1,1,2):
            lua=fixture(f'state.facts.PTFRU9_Support_{fact}={value}')
            for cls,method,types in TARGETS:
                args=['id' if x=='String' else False for x in types]
                assert 'Older gig/phone entry refused' in lua.globals().invoke(cls+'.'+method,*args)
            assert lua.eval('state.originalCalls')==0;cases+=11
    for bad in ('state.noQuests=true', 'state.badFact="PTFRU9_Support_Request"','state.nilFact="PTFRU9_Support_Request"','state.facts.PTFRU9_Support_Request=0/0','state.facts.PTFRU9_Support_Request=0.5'):
        lua=fixture(bad);assert 'unavailable' in lua.globals().invoke(TARGETS[0][0]+'.Start','id');assert lua.eval('state.originalCalls')==0
    # Every missing/wrong/overloaded class signature refuses before any hooks.
    for cls,method,_ in TARGETS:
        for mutation in ('missing','return','overload'):
            lua=LuaRuntime(unpack_returned_tuples=True);broken=dict(descriptors)
            if mutation=='missing':broken.pop(cls)
            elif mutation=='return':broken[cls]=broken[cls].replace('=> (String)','=> (Bool)')
            else:broken[cls]=broken[cls].replace('\n\t},','\n\t\t'+method+'(other: Int32) => (String),\n\t},',1)
            lua.globals().descriptors=lua.table_from(broken);lua.execute(MOCK);api=lua.execute(source);lua.execute('state.events.onInit()')
            assert 'registered=false' in api.Status();assert lua.eval('state.overrides')==0;cases+=1
    for n in range(1,13):
        lua=fixture(f'state.throwHook={n}');assert 'registered=false' in lua.eval('api.Status()')
    for bad in ('state.dropHook=12','state.readyError=true','state.noBridge=true'):
        lua=fixture(bad);assert 'registered=false' in lua.eval('api.Status()')
    # The C++ void registration API cannot reveal a silently lost legacy hook.
    # Keep this limitation explicit; never call old mutators just to "prove" it.
    lua=fixture('state.dropHook=1');assert 'registered=true' in lua.eval('api.Status()')
    assert lua.eval('state.hooks["PTFR.ActivityStateR3.NativeSupportU7.Start"]') is None
    assert lua.eval('state.originalCalls')==0
    for path,hash in pins.items():assert sha(ROOT/path)==hash
    OUT.mkdir(parents=True,exist_ok=True)
    result=dict(status='PASS_U9_INTERLOCK_LUAJIT_MOCKS_LIVE_PENDING',test_sha256=sha(__file__),source_pins=pins,cases=cases,target_count=11,hook_count=12,actual_luajit=True,no_mutator_probes=True,no_gameplay_writes=True,exact_installed_signatures=True,default_false_helper=True,all_target_delivery_proven=False,void_registration_silent_failure_explicit=True,primary_sources=[
      'https://raw.githubusercontent.com/maximegmd/CyberEngineTweaks/v1.37.1/src/scripting/FunctionOverride.cpp',
      'https://raw.githubusercontent.com/maximegmd/CyberEngineTweaks/v1.37.1/src/scripting/Scripting.cpp',
      'https://raw.githubusercontent.com/maximegmd/CyberEngineTweaks/v1.37.1/src/reverse/Type.cpp',
      'https://wiki.redmodding.org/cyber-engine-tweaks/patch-notes',
      'https://raw.githubusercontent.com/maximegmd/CyberEngineTweaks/v1.37.1/src/reverse/RTTIHelper.cpp'])
    (OUT/'interlock_tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],cases)

if __name__=='__main__':main()
