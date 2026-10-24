-- Save-bound JSON sidecars. No quest/fact setters and no cross-save/global import.
local api, work, counter, retry, time = {}, nil, 0, 0, 0
local prefix = "snapshot_hs1_"
local function system()
  if not Game or type(Game.GetScriptableSystemsContainer) ~= "function" then return nil end
  local c = Game.GetScriptableSystemsContainer()
  return c and c:Get("PTFR.HistorySnapshotHS1.SnapshotStateHS1") or nil
end
local function tokenOK(s)
  return type(s) == "string" and #s >= 1 and #s <= 96 and s:match("^[A-Za-z0-9_-]+$") ~= nil
end
local function read(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local data = f:read(8388609)
  local ok = f:close()
  if not ok or not data or #data > 8388608 then error("Snapshot read failed or exceeded size limit") end
  return data
end
local function same(s, w)
  return s and s:CanExport() and s:Epoch() == w.epoch and s:Revision() == w.revision
end
local function finish(s, w)
  local data = table.concat(w.parts) .. "]}\n"
  if #data > 8388608 then error("Snapshot size limit") end
  local parsed = json.decode(data)
  if parsed.schema ~= 1 or #parsed.rows ~= w.count or parsed.revision ~= w.revision or
     (parsed.origin ~= "pre_ending" and parsed.origin ~= "post_ending_fallback") then error("Invalid snapshot document") end
  if not same(s,w) then return end
  local token = s:FileToken()
  if tokenOK(token) and read(prefix .. token .. ".json") == data then
    assert(s:AckFile(w.epoch,w.revision,token), "Snapshot changed before acknowledgement")
    return
  end
  -- Never overwrite a differing file: it may belong to another branch/version.
  local found = false
  for _ = 1, 1000 do
    counter = counter + 1
    token = os.date("!%Y%m%dT%H%M%SZ") .. "_" .. tostring(w.revision) .. "_" .. tostring(counter)
    if read(prefix .. token .. ".json") == nil and read(prefix .. token .. ".tmp") == nil then found = true;break end
  end
  assert(found and tokenOK(token), "No unused snapshot filename")
  local path, temp = prefix .. token .. ".json", prefix .. token .. ".tmp"
  local f = assert(io.open(temp,"wb"), "Cannot create snapshot temporary file")
  local wrote, flushed, closed
  local ok, err = pcall(function()
    wrote = f:write(data);flushed = f:flush()
  end)
  closed = f:close()
  assert(ok and wrote and flushed and closed, tostring(err or "Snapshot write/flush/close failed"))
  assert(read(temp) == data, "Snapshot temporary readback mismatch")
  if not same(s,w) then return end
  assert(read(path) == nil, "Snapshot destination appeared")
  assert(os.rename(temp,path), "Snapshot rename failed")
  assert(read(path) == data, "Snapshot committed readback mismatch")
  if not same(s,w) then return end
  assert(s:AckFile(w.epoch,w.revision,token), "Snapshot changed before acknowledgement")
  print("[PTFR] " .. parsed.origin .. " snapshot verified: " .. path)
end
function api.Status()
  local ok,result = pcall(function() local s=system();return s and s:Status() or "Load a save first." end)
  return ok and result or tostring(result)
end
registerForEvent("onUpdate",function(dt)
  if type(dt)~="number" or dt~=dt or dt<0 or dt==math.huge then return end
  time=time+dt
  if time<retry then return end
  local s
  local ok,err=pcall(function()
    s=system()
    if not s or not s:CanExport() then work=nil;return end
    if s:Exported() then work=nil;return end
    if work and not same(s,work) then work=nil end
    if not work then
      work={epoch=s:Epoch(),revision=s:Revision(),count=s:Count(),index=0,parts={s:HeaderJSON()}}
      assert(work.count==158 and work.parts[1]~="","Unexpected snapshot catalogue")
    end
    local n=0
    while n<16 and work.index<work.count do
      local row=s:RowJSON(work.index);assert(type(row)=="string" and row~="","Snapshot row unavailable")
      if work.index>0 then work.parts[#work.parts+1]="," end
      work.parts[#work.parts+1]=row;work.index=work.index+1;n=n+1
    end
    if work.index==work.count then finish(s,work);work=nil end
  end)
  if not ok then
    if s and work then pcall(function() s:ReportIOFailure(work.epoch,work.revision) end) end
    work=nil;retry=time+5
    print("[PTFR] Snapshot export waiting: "..tostring(err))
  end
end)
registerForEvent("onShutdown",function() work=nil end)
return api
