"""Exercise durable observer with Lua 5.1 and no permitted game writes."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
events={}; prints={}; rows={}; reads=0; flushed=0; closed=0
function registerForEvent(n,f) events[n]=f end
function print(s) table.insert(prints,s) end
function IsDefined(p) return p~=nil end
json={encode=function(v) table.insert(rows,v); return "{}" end}
io={open=function(name,mode) if mode=="r" then return nil end
  return {write=function(self,s) return self end,
    flush=function(self) flushed=flushed+1; return true end,
    close=function() closed=closed+1 end} end}
q={GetFactStr=function(self,f) reads=reads+1; return 1 end,
  SetFactStr=function() error("ILLEGAL gameplay write") end}
player={GetWorldPosition=function() return {x=0,y=0,z=0} end,
  IsInCombat=function() return false end,GetEntityID=function() return {hash=1} end}
Game={GetQuestsSystem=function() return q end,GetPlayer=function() return player end,
  GetSceneSystem=function() return {GetScriptInterface=function() return {IsEntityInScene=function() return false end} end} end,
  GetWorkspotSystem=function() return {IsActorInWorkspot=function() return false end} end}
''')
source=(ROOT/'archive/b0_club_dancing/cet/init.lua').read_text()
assert 'SetFactStr' not in source and 'Teleport' not in source and 'SetFact' not in source
m=lua.execute(source);m.Start();m.Start()
lua.execute('events.onUpdate(0.5);events.onUpdate(0.5)')
m.Mark('first-return');m.Stop()
assert lua.eval('#rows')==4 and lua.eval('flushed')==4 and lua.eval('closed')==1
count=lua.eval('reads');lua.execute('events.onUpdate(10)');assert lua.eval('reads')==count
lua.execute('Game.GetPlayer=function() return nil end');m.Start();lua.execute('events.onShutdown()')
assert lua.eval('closed')==2
print('PASS: Lua51 observer start/idempotence/mark/tick/flush/stop/shutdown and absent-player handling; no gameplay writer')
