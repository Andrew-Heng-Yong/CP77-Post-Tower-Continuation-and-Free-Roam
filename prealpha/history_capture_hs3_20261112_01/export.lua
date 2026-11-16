-- Recovery sidecars for save-local histories. No file import or test override.
local api, counter, leaseCounter, time = {}, 0, 0, 0
local channels = {
  {name="PTFR.HistorySnapshotHS1.SnapshotStateHS1", prefix="snapshot_hs1_", schema=1, count=158},
  {name="PTFR.HistorySnapshotHS1.CaptureArchiveHS3", prefix="snapshot_hs3_", schema=3, count=__HS3_COUNT__},
}
local function system(name)
  if not Game or type(Game.GetScriptableSystemsContainer)~="function" then return nil end
  local player=Game.GetPlayer();if not player or not player:IsAttached() then return nil end
  local handler=Game.GetSystemRequestsHandler();if not handler or handler:IsPreGame() then return nil end
  local container=Game.GetScriptableSystemsContainer();return container and container:Get(name) or nil
end
local function tokenOK(s)
  return type(s)=="string" and #s>=1 and #s<=96 and s:match("^[A-Za-z0-9_-]+$")~=nil
end
local function read(path)
  local file=io.open(path,"rb");if not file then return nil end
  local data=file:read(8388609);local closed=file:close()
  assert(closed and data and #data<=8388608,"Snapshot read failed or exceeded size limit")
  return data
end
local function same(s,w)
  return s and s:CanExport() and s:Epoch()==w.epoch and s:Revision()==w.revision and s:LeaseHS3()==w.lease
end
local function finish(c,s,w)
  local data=table.concat(w.parts).."]}\n"
  assert(#data<=8388608,"Snapshot size limit")
  local parsed=json.decode(data)
  assert(parsed.schema==c.schema and #parsed.rows==c.count and parsed.revision==w.revision,"Invalid snapshot document")
  assert((c.schema==1 and (parsed.origin=="pre_ending" or parsed.origin=="post_ending_fallback")) or
    (c.schema==3 and parsed.origin=="pre_native_cleanup" and (parsed.route==1 or parsed.route==2) and parsed.ticket>0),"Invalid snapshot origin")
  if not same(s,w) then return end
  local token=s:FileToken()
  if not (tokenOK(token) and read(c.prefix..token..".json")==data) then
    local unused=false
    for _=1,1000 do
      counter=counter+1;token=os.date("!%Y%m%dT%H%M%SZ").."_"..tostring(w.revision).."_"..tostring(counter)
      if not read(c.prefix..token..".json") and not read(c.prefix..token..".tmp") then unused=true;break end
    end
    assert(unused and tokenOK(token),"No unused snapshot filename")
    local path,temp=c.prefix..token..".json",c.prefix..token..".tmp"
    local file=assert(io.open(temp,"wb"),"Cannot create snapshot temporary file")
    local wrote,flushed
    local ok,err=pcall(function() wrote=file:write(data);flushed=file:flush() end)
    local closed=file:close()
    assert(ok and wrote and flushed and closed,tostring(err or "Snapshot write/flush/close failed"))
    assert(read(temp)==data,"Snapshot temporary readback mismatch")
    if not same(s,w) then return end
    assert(not read(path),"Snapshot destination appeared")
    assert(os.rename(temp,path),"Snapshot rename failed")
    assert(read(path)==data,"Snapshot committed readback mismatch")
  end
  if not same(s,w) then return end
  assert(s:AckFileLeaseHS3(w.epoch,w.revision,token,w.lease),"Save changed before snapshot acknowledgement")
  print("[PTFR] "..parsed.origin.." history verified: "..c.prefix..token..".json")
end
local function update(c)
  if time<(c.retry or 0) then return end
  local s
  local ok,err=pcall(function()
    s=system(c.name)
    if not s or not s:CanExport() or s:Exported() then c.work=nil;return end
    if c.work and not same(s,c.work) then c.work=nil end
    if not c.work then
      leaseCounter=leaseCounter+1
      local w={epoch=s:Epoch(),revision=s:Revision(),index=0,lease="hs3_"..tostring(leaseCounter)}
      assert(s:BeginExportHS3(w.epoch,w.revision,w.lease),"Save changed before export lease")
      w.count=s:Count();w.parts={s:HeaderJSON()}
      assert(same(s,w) and w.count==c.count and w.parts[1]~="","Unexpected snapshot catalogue")
      c.work=w
    end
    local w=c.work;local n=0
    while n<64 and w.index<w.count do
      local row=s:RowJSON(w.index);assert(type(row)=="string" and row~="","Snapshot row unavailable")
      if w.index>0 then w.parts[#w.parts+1]="," end
      w.parts[#w.parts+1]=row;w.index=w.index+1;n=n+1
    end
    if w.index==w.count then finish(c,s,w);c.work=nil end
  end)
  if not ok then
    if s and c.work and same(s,c.work) then pcall(function() s:ReportIOFailure(c.work.epoch,c.work.revision) end) end
    c.work=nil;c.retry=time+5;print("[PTFR] History export waiting: "..tostring(err))
  end
end
registerForEvent("onUpdate",function(dt)
  if type(dt)~="number" or dt~=dt or dt<0 or dt==math.huge then return end
  time=time+dt;for _,c in ipairs(channels) do update(c) end
end)
registerForEvent("onShutdown",function() for _,c in ipairs(channels) do c.work=nil end end)
function api.Status()
  local messages={}
  for _,c in ipairs(channels) do
    local ok,result=pcall(function() local s=system(c.name);return s and s:Status() or "Load a save first." end)
    messages[#messages+1]=ok and result or tostring(result)
  end
  return table.concat(messages,"\n")
end
return api
