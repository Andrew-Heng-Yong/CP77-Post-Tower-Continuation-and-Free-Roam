"""Lua51 diagnostic lifecycle tests; native callback delivery remains a live test."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
SETUP='''
events={};rows={};reads=0;flushed=0;closed=0;registered=0;disabled=0
active=false;hands=0;selfTestOk=true;nativeMode=8192
function registerForEvent(n,f) events[n]=f end
function print(s) end
function IsDefined(p) return p~=nil end
json={encode=function(v) table.insert(rows,v);return "{}" end}
io={open=function(n,m) if m=="r" then return nil end
 return {write=function(self,s)return self end,flush=function()flushed=flushed+1;return true end,close=function()closed=closed+1 end} end}
q={GetFactStr=function(self,f)reads=reads+1;if f=="PTFRWORLD_Coaster_HandsStarted" then return hands end;return 1 end,SetFactStr=function()error("FORBIDDEN")end}
player={GetWorldPosition=function()return{x=0,y=0,z=0}end,IsInCombat=function()return false end,GetEntityID=function()return{}end}
Enum={new=function(t,n)assert(t=="workWorkspotDebugMode" and n=="FunctionalTests");return nativeMode end}
function NewObject(name)
 assert(name=="PTFRCoasterAnimationAudit")
 observer={enabled=false,pending={},received=0,
 SelfTest=function()return selfTestOk end,GetDebugModeValue=function(self,v)return v end,
 SetEnabled=function(self,v)self.enabled=v;if not v then disabled=disabled+1 end end,
 DrainEvents=function(self)local a=self.pending;self.pending={};return a end,
 GetReceivedCount=function(self)return self.received end,GetDroppedCount=function()return 0 end}
 return observer
end
Game={GetQuestsSystem=function()return q end,GetPlayer=function()return player end,
 GetSceneSystem=function()return{GetScriptInterface=function()return{IsEntityInScene=function()return false end}end}end,
 GetWorkspotSystem=function()return{IsActorInWorkspot=function()return active end,
 SendDebugCommandFunctionalTests=function(self,mode,p,o)
 assert(mode==8192 and p==player and o==observer and active);registered=registered+1 end}end}
'''
source=(ROOT/'archive/b0_world_interactions/cet/init.lua').read_text()
assert not any(w in source for w in ('SetFact','Teleport','SetAppearance','Spawn','SendJump','SendPlay'))
def runtime():
    lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(SETUP)
    return lua,lua.execute(source)

lua,m=runtime();m.Start();m.Start()
assert lua.eval('registered')==0
assert lua.eval('rows[1].animation_observer')=='WAITING_FOR_WORKSPOT'
assert lua.eval('rows[1].animation_selftest')=='PASS'
lua.execute('events.onUpdate(1);active=true;events.onUpdate(1)')
assert lua.eval('registered')==1
assert lua.eval('rows[#rows].animation_observer')=='REQUESTED_NO_CALLBACKS'
lua.execute('observer.pending={"played:cheer","skipped:idle","missing:unknown"};observer.received=3;events.onUpdate(1)')
assert lua.eval('#rows[#rows].animation_events')==3
assert lua.eval('rows[#rows].animation_observer')=='CALLBACKS_RECEIVED'
m.Mark('return');assert lua.eval('#rows[#rows].animation_events')==0
m.Stop();assert lua.eval('closed')==1 and lua.eval('disabled')==1
reads=lua.eval('reads');lua.execute('events.onUpdate(10)');assert reads==lua.eval('reads')

lua,m=runtime();lua.execute('active=true');m.Start()
lua.execute('for i=1,30 do events.onUpdate(1) end')
assert lua.eval('registered')==3
lua.execute('for i=1,40 do hands=hands+1;events.onUpdate(1) end')
assert lua.eval('registered')==12
assert lua.eval('rows[#rows].animation_observer')=='REQUESTED_NO_CALLBACKS'
m.Stop()

lua,m=runtime();m.Start();lua.execute('active=true;hands=1');m.Stop()
assert lua.eval('registered')==0  # Stop only drains; never attaches on teardown

for setup,status in [
    ('Game.GetPlayer=function()return nil end','NO_PLAYER'),
    ('NewObject=function()error("missing observer")end','UNAVAILABLE:'),
    ('selfTestOk=false','UNAVAILABLE:'),
    ('nativeMode=11','UNAVAILABLE:'),
]:
    lua,m=runtime();lua.execute(setup);m.Start();m.Stop()
    assert lua.eval('rows[1].animation_observer').startswith(status)
    assert lua.eval('registered')==0
print('PASS: Lua51 active-instance registration, native8192 guard, queue self-test failure, bounded retries, callback acknowledgement, drain/disable; no gameplay writes')
