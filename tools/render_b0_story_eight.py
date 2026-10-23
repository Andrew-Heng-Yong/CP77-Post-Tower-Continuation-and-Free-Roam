"""Render the pending-enable coordinator and read-only S4 trace."""
import json
from plan_b0_story_eight import ROOT,OUT,read

def main():
    c=read(OUT/'cohort.json');sites=c['sites']
    src=(ROOT/'redscript/PTFR_B0_StoryServices/StoryServiceDriver.reds').read_text()
    src=src.replace('PTFR.B0StoryServices','PTFR.B0StoryEight').replace('StoryServiceDriver','StoryEightDriver').replace('StoryServiceTick','StoryEightTick').replace('PTFRB0ST_Suspended','PTFRB0S4_Suspended')
    a=src.index('    pending = this.Site(');b=src.index('    return pending;',a)
    lines=[]
    for s in sites:
        p=s['prefix'];extra=' && '.join([f'q.GetFact(n"{p}QuestOwns") == 0']+[f'q.GetFact(n"{f}") {"=="if op=="Equal"else">"} {v}'for f,op,v in s['guards'][1:]])
        lines.append(f'    pending = this.Site(q, n"{p}Enabled", n"{p}Ready", n"{p}OwnerActive", n"{p}Excluded", n"{s["gate"]}", {extra}, commit) || pending;\n')
    src=src[:a]+''.join(lines)+src[b:]
    dest=ROOT/'redscript/PTFR_B0_StoryEight';dest.mkdir(exist_ok=True);(dest/'StoryEightDriver.reds').write_text(src)
    names=list(c['common_guards'])+['PTFRBASE_Suspended','PTFRB0S4_Suspended']
    for s in sites:names += [f for f,_,_ in s['guards']]+[s['prefix']+x for x in ['Ready','Enabled','Excluded','QuestOwns','OwnerActive','OwnerStarts','SceneRequests','Departures']]
    # Append/close each record. A process crash does not leave a buffered session log.
    lua=r'''-- S4 diagnostics only: never enable, disable, teleport, or write facts.
local M={}
local names=__NAMES__
local sites=__SITES__
local filename=nil
local elapsed,interval,heartbeat=0,0,0
local last,reported=nil,false
local function snapshot(label)
 local q,p=Game.GetQuestsSystem(),Game.GetPlayer()
 if not q or not p or not IsDefined(p) then return 'loaded=false','loaded=false' end
 local values={};for _,n in ipairs(names) do values[#values+1]=n..'='..tostring(q:GetFactStr(n)) end
 local signature=table.concat(values,'\t')
 local pos=p:GetWorldPosition()
 return 'elapsed='..elapsed..'\tlabel='..tostring(label)..'\tx='..pos.x..'\ty='..pos.y..'\tz='..pos.z..'\t'..signature,signature
end
local function append(line)
 if not filename then return end
 local ok,err=pcall(function()
  local f,reason=io.open(filename,'a');assert(f,reason)
  local wrote,why=f:write(line..'\n');local closed,closeError=f:close()
  assert(wrote,why);assert(closed,closeError)
 end)
 if not ok and not reported then print('[PTFR S4] LOG ERROR '..tostring(err));reported=true end
end
local function record(label,force)
 local ok,line,signature=pcall(snapshot,label)
 if not ok then line='sample_error='..tostring(line);signature=line end
 if force or signature~=last or heartbeat>=15 then append(line);last=signature;heartbeat=0 end
 return line
end
function M.Observe(label)
 local line=record(label or 'manual',true)
 local q=Game.GetQuestsSystem()
 print('[PTFR S4] '..tostring(filename))
 if q then for _,s in ipairs(sites) do
  local p=s.prefix
  print('[PTFR S4] '..s.key..' gate='..q:GetFactStr(s.gate)..' E='..q:GetFactStr(p..'Enabled')..' owner='..q:GetFactStr(p..'OwnerActive')..' requests='..q:GetFactStr(p..'SceneRequests')..' departures='..q:GetFactStr(p..'Departures'))
 end end
 return line
end
function M.Finish()record('finish',true);filename=nil;print('[PTFR S4] Logging stopped; services unchanged')end
registerForEvent('onInit',function()
 filename='story_eight_'..os.date('%Y%m%d_%H%M%S')..'.tsv'
 reported=false;last=nil;record('init',true)
end)
registerForEvent('onUpdate',function(dt)
 elapsed=elapsed+dt;interval=interval+dt;heartbeat=heartbeat+dt
 if interval>=2 then interval=0;record('sample',false) end
end)
registerForEvent('onShutdown',function()record('shutdown',true);filename=nil end)
return M
'''
    def table(v):
        if isinstance(v,list):return '{'+','.join(table(x)for x in v)+'}'
        if isinstance(v,dict):return '{'+','.join(k+'='+table(x)for k,x in v.items())+'}'
        return json.dumps(v)
    lua=lua.replace('__NAMES__',table(list(dict.fromkeys(names)))).replace('__SITES__',table([{k:s[k]for k in ['key','prefix','gate']}for s in sites]))
    dest=ROOT/'diagnostics/PTFR_B0_StoryEight';dest.mkdir(exist_ok=True);(dest/'init.lua').write_text(lua)
    print('Rendered automatic S4 enabling and read-only append/close logging')

if __name__=='__main__':main()
