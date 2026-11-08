-- QR9 read-only diagnostics. No engine setters, quest starts, journal writes or save APIs.
local M = {}
local N = "NOT_OBSERVED"
local cfg, output, path, profile, label, quests, subject
local active, attached, stopping, blocked = false, false, false, false
local generation, seq, serial, rows, bytes, nextCheck = 0, 0, 0, 0, 0, 0
local started, deadline, lastState, known = 0, 0, nil, {}
local regs, orphaned, hookState = {}, {}, "NOT_REQUESTED"
local waitReason
local MAX_ROWS, MAX_BYTES, CHECK_SECONDS = 2048, 8388608, 2
local function say(s) print("[PTFR QR9] " .. s) end
local function readConfig()
  local f = assert(io.open("watch.json", "rb"), "watch.json missing")
  local text = f:read(262145); f:close()
  assert(text and #text <= 262144, "watch.json oversized")
  local c = json.decode(text)
  assert(c.schema == 1 and c.module == "PTFR_QR9_Diagnostics" and type(c.profiles) == "table", "config schema")
  return c
end
local function read(fn)
  local ok, value = pcall(fn)
  if not ok or value == nil then return N, ok and "nil/unavailable" or tostring(value) end
  return value
end
local function defined(x)
  if type(IsDefined)~="function" then return false,"IsDefined unavailable" end
  local ok, v = pcall(function() return x ~= nil and IsDefined(x) end)
  return ok and v == true,not ok and tostring(v)or nil
end
local function identity(p)
  local value,err=read(function() local id=p:GetEntityID(); return tostring(id.hash) end)
  if value==N or value=="nil" then return nil,"player.GetEntityID:"..tostring(err or "hash unavailable") end
  return value
end
local function emit(event, data, force)
  if not output then return false end
  if force and rows>=MAX_ROWS then return false end
  if not force and (rows >= MAX_ROWS-4 or bytes >= MAX_BYTES-32768) then M.stop("EVENT_OR_BYTE_LIMIT"); return false end
  local ok, err = pcall(function()
    local row={schema=1, module="PTFR_QR9_Diagnostics", run_id=path, seq=seq+1,
      utc=os.date("!%Y-%m-%dT%H:%M:%SZ"), wall_elapsed_s=os.time()-started,
      profile=profile, user_label=label, event=event, data=data or {}}
    local line=json.encode(row).."\n"
    assert(#line <= 131072 and bytes+#line <= MAX_BYTES, "row/byte limit")
    assert(output:write(line)); assert(output:flush())
    seq,rows,bytes=seq+1,rows+1,bytes+#line
  end)
  if not ok then
    say("LOG_ERROR: "..tostring(err)); M.stop("LOG_ERROR")
    return false
  end
  return true
end
local function endAtLimit()
  if active and os.time() >= deadline then M.stop("DURATION_LIMIT"); return true end
  return not active or stopping
end
local function state()
  local s={journal={}, vehicle_unlock={}, phone_active=N, game_clock=N,
    actual_graph_activation=N, native_owner=N, ArchiveXL_engine_receipt=N,
    saved_clock_remaining=N, phone_queue=N, save_identity=N, errors={}}
  if not attached then return s end
  for _, row in ipairs(cfg.profiles[profile].journals or {}) do
    local value, err=read(function()
      local jm=Game.GetJournalManager()
      local entry=jm:GetEntryByString(row.path, row.class)
      local found,definitionError=defined(entry)
      if definitionError then error(definitionError) end
      if not found then return {entry_found=false, state=N} end
      return {entry_found=true, state=tostring(jm:GetEntryState(entry)), representation="native_enum_text"}
    end)
    s.journal[row.path]=value
    if err then s.errors["journal:"..row.path]=err end
  end
  local value, err=read(function() return Game.GetPhoneManager():IsPhoneCallActive() end)
  s.phone_active=value; if err then s.errors.phone=err end
  for _, record in ipairs(cfg.profiles[profile].vehicles or {}) do
    local v,e=read(function() return Game.GetVehicleSystem():IsVehiclePlayerUnlocked(TweakDBID.new(record)) end)
    s.vehicle_unlock[record]=v
    if e then s.errors["vehicle:"..record]=e end
  end
  -- Game calendar and native pending clock are deliberately not reconstructed from facts.
  return s
end
local function observeState(reason)
  local s=state(); local encoded=json.encode(s)
  if reason or encoded ~= lastState then emit(reason or "BOUNDED_STATE_CHANGE",s); lastState=encoded end
end
local function cleanup()
  local failures={}
  for _, r in ipairs(regs) do
    local ok, err=pcall(function() quests:UnregisterListener(CName.new(r.name),r.id) end)
    if not ok then
      failures[#failures+1]={fact=r.name,id=tostring(r.id),error=tostring(err):sub(1,160)}
      orphaned[#orphaned+1]=r.proxy
    end
  end
  regs={}; quests=nil
  if #failures>0 then blocked=true end
  emit("LISTENER_CLEANUP_CALLS",{failures=#failures,errors=failures, interpretation="successful void API call is not an introspected listener-registry query"},true)
end
function M.stop(reason)
  if not active or stopping then return path end
  stopping=true; generation=generation+1
  emit("STOP",{reason=tostring(reason or "USER_STOP"), attached=attached},true)
  cleanup()
  local result=path
  active,attached=false,false; subject=nil
  if output then pcall(function() output:flush(); output:close() end) end
  output=nil; stopping=false
  say("Stopped: "..tostring(result)..(blocked and "; cleanup failed, further capture blocked in this Lua environment" or ""))
  return result
end
local function session()
  local p, err=read(function() return Game.GetPlayer() end)
  if p == N then return nil,"Game.GetPlayer:"..tostring(err or "player absent") end
  local found,definitionError=defined(p)
  if not found then return nil,definitionError or "player not defined" end
  local ok,attachError=read(function() return p:IsAttached() end)
  if ok ~= true then return nil,"player.IsAttached:"..tostring(attachError or "false") end
  local pre,preError=read(function() return Game.GetSystemRequestsHandler():IsPreGame() end)
  if pre ~= false then return nil,"IsPreGame:"..tostring(preError or "true (main-menu/load guard)") end
  return identity(p)
end
local function attach()
  if endAtLimit() or attached then return end
  local id,reason=session()
  if not id then
    if reason~=waitReason then waitReason=reason;emit("SESSION_WAIT",{reason=reason,actual_save_identity=N}) end
    return
  end
  local q, err=read(function() return Game.GetQuestsSystem() end)
  if q == N or not defined(q) then emit("API_UNAVAILABLE",{api="GetQuestsSystem",error=err}); M.stop("NO_QUEST_SYSTEM"); return end
  quests,subject,attached=q,id,true;waitReason=nil
  local facts={}
  for _, name in ipairs(cfg.profiles[profile].facts) do
    local v,e=read(function() return q:GetFactStr(name) end)
    facts[name]=v; known[name]=v
    if e then emit("FACT_READ_FAILED",{fact=name,error=e}); M.stop("FACT_API_UNAVAILABLE"); return end
  end
  emit("ATTACHED_BASELINE",{player_entity=id, save_identity=N, facts=facts,
    interpretation="initial values, not transitions, actual entry or saved ownership"})
  local gen=generation
  for _, name in ipairs(cfg.profiles[profile].facts) do
    local captured=name
    local ok, err2=pcall(function()
      local proxy=NewProxy({args={"Int32"},callback=function(value)
        if not active or stopping or generation ~= gen or endAtLimit() then return end
        local previous=known[captured]
        local db,e=read(function() return quests:GetFactStr(captured) end)
        known[captured]=value
        emit("FACT_DELIVERY",{fact=captured, previous_observed=previous or N,
          callback_value=value,current_db=db,read_error=e,
          delivery_differs_from_current=value ~= db,
          evidence="native listener delivery; callback time is not native-write time; not graph execution"})
      end})
      local listener=q:RegisterListener(CName.new(captured),proxy:Target(),proxy:Function())
      assert(listener ~= nil,"missing listener ID")
      regs[#regs+1]={name=captured,id=listener,proxy=proxy}
    end)
    if not ok then emit("LISTENER_CALL_FAILED",{fact=captured,error=tostring(err2)}); M.stop("LISTENER_SETUP_FAILED"); return end
  end
  emit("LISTENER_CALLS_COMPLETED",{returned_ids=#regs, expected=#cfg.profiles[profile].facts,
    interpretation="API calls returned IDs; actual deliveries logged separately"})
  observeState("ATTACHED_STATE")
end
local function freshFile()
  local stamp=os.date("!%Y%m%dT%H%M%SZ")
  for _=1,9999 do
    serial=serial+1
    local name=string.format("QR9_capture_%s_%04d.jsonl",stamp,serial)
    local f,err=io.open(name,"a+")
    if not f then return nil,nil,err end
    local n,e=f:seek("end")
    if n==0 then return f,name end
    f:close(); if n==nil then return nil,nil,e end
  end
  return nil,nil,"no unused filename"
end
function M.start(which, userLabel, seconds)
  if active then say("Already recording: "..path); return path end
  if blocked then say("NOT_RUNNING: prior listener cleanup failed; do not start more captures in this Lua environment"); return nil end
  local ok,c=pcall(readConfig)
  if not ok then say("NOT_RUNNING: "..tostring(c)); return nil end
  cfg=c; which=which or "S00"
  if type(which)~="string" or type(cfg.profiles[which])~="table" then say("NOT_RUNNING: unknown profile"); return nil end
  seconds=seconds or 300
  if type(seconds)~="number" or seconds~=seconds or seconds<1 or seconds>900 then say("NOT_RUNNING: duration must be1..900 seconds"); return nil end
  local names=cfg.profiles[which].facts
  if type(names)~="table" or #names<1 or #names>96 then say("NOT_RUNNING: fact budget"); return nil end
  for _,n in ipairs(names) do if type(n)~="string" or #n>128 or not n:match("^[A-Za-z0-9_]+$") then say("NOT_RUNNING: invalid fact"); return nil end end
  local f,p,e=freshFile(); if not f then say("NOT_RUNNING: log open failed: "..tostring(e)); return nil end
  output,path,profile,label=f,p,which,tostring(userLabel or which):sub(1,96)
  generation=generation+1; seq,rows,bytes=0,0,0; known={}; regs={}; attached=false; quests=nil
  started=os.time(); deadline=started+seconds; nextCheck=0; lastState=nil;waitReason=nil; active=true
  if not emit("CAPTURE_START",{version=cfg.version, declared_build=cfg.declared_build,
      declared_build_runtime_hash_verification="NOT_PERFORMED; separate offline installer manifest verifies bytes",
      duration_seconds=seconds,max_rows=MAX_ROWS,max_bytes=MAX_BYTES,
      watch_facts=names, scope=cfg.profiles[which].description, hook=hookState,
      actual_graph_activation=N,native_owner=N,ArchiveXL_engine_receipt=N, save_identity=N,
      actual_installed_core_hashes=N,
      session_guard="observed detach or attached/pregame/entity change only; identical player ID is not save identity; stop before deliberate load",
      startup_before_command=N, native_clock_or_queue=N,
      note="Fact events, bounded journal/phone reads and user labels only; no gameplay test PASS is inferred"}) then return nil end
  attach()
  if not active then say("NOT_RUNNING; failed capture closed: "..path);return nil end
  say((attached and "Recording: " or "Armed; "..tostring(waitReason).."; early restore NOT_OBSERVED: ")..path)
  return path
end
function M.mark(text)
  if not active then say("NOT_RUNNING"); return nil end
  if endAtLimit() then return path end
  emit("USER_MARK",{label=tostring(text or "manual"):sub(1,96), interpretation="user label, not an automatic gameplay observation"})
  observeState("MARK_STATE"); return path
end
function M.status()
  return {state=active and (attached and "RECORDING" or "ARMED_NO_PLAYER") or "NOT_RUNNING",
    path=path,profile=profile,rows=rows,bytes=bytes,seconds_remaining=active and math.max(0,deadline-os.time()) or 0,
    cleanup_failed=blocked,last_wait_reason=waitReason or N,actual_graph_activation=N, ArchiveXL_engine_receipt=N}
end
registerForEvent("onInit",function()
  -- Known local historical hook; success here only requests registration, never certifies delivery.
  local ok,err=pcall(function()
    ObserveBefore("PlayerPuppet","OnDetach",function(self)
      if active and attached and identity(self)==subject then M.stop("PLAYER_DETACH_OBSERVED_SCRIPT_CALLBACK") end
    end)
  end)
  hookState=ok and "ONDETACH_REGISTRATION_REQUESTED_NOT_RUNTIME_VERIFIED" or "UNAVAILABLE:"..tostring(err)
end)
registerForEvent("onUpdate",function(dt)
  if not active or endAtLimit() then return end
  if type(dt)~="number" or dt~=dt or dt<0 or dt==math.huge then return end
  nextCheck=nextCheck+dt
  if nextCheck<CHECK_SECONDS then return end
  nextCheck=0
  if not attached then attach(); return end
  local id=session()
  if not id or id~=subject then M.stop("SESSION_GUARD_CHANGED_NO_AUTO_RESUME"); return end
  observeState()
end)
registerForEvent("onShutdown",function() M.stop("CET_SHUTDOWN") end)
return M
