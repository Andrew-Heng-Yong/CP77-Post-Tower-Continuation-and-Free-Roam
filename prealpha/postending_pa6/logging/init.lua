-- PA6 diagnostics are read-only except explicitly named one-shot RepairCamera.
local api = {}
local function call(name, method, ...)
  local args, count = {...}, select("#", ...)
  local ok, result = pcall(function()
    if not Game or type(Game.GetScriptableSystemsContainer) ~= "function" then
      return "Load a save first; game systems unavailable."
    end
    local c = Game.GetScriptableSystemsContainer()
    local s = c and c:Get(name)
    if not s then return "Load a save first; PA2 system unavailable: " .. name end
    local fn = s[method]
    if type(fn) ~= "function" then return "PA2 diagnostic method unavailable: " .. name .. "." .. method end
    return fn(s, unpack(args, 1, count))
  end)
  if not ok then return "PA2 diagnostic unavailable: " .. tostring(result) end
  return result
end
function api.Status()
  return call("PTFR.ActivityStateR3.PreAlphaEntry", "Status")
end
function api.Arrival()
  return call("PTFR.ActivityStateR3.PreAlphaArrivalPA1", "Status")
end
function api.Gigs()
  return call("PTFR.ActivityStateR3.NativeGigsU9", "InspectAll")
end
function api.Gig(id)
  if type(id) ~= "string" or id == "" then return "Pass a gig ID, for example Gig(\"sts_hey_rey_06\")." end
  return call("PTFR.ActivityStateR3.NativeGigsU9", "Inspect", id)
end
function api.Entry()
  return call("PTFR.ActivityStateR3.PreAlphaEntry", "InspectAll")
end
function api.Phone()
  return call("PTFR.ActivityStateR3.GigPhoneU9", "Inspect")
end
function api.Profile()
  return call("PTFR.RestrictionsR3.ProfilePolicy", "GetStatus")
end
function api.Optics()
  return call("PTFR.ActivityStateR3.CameraOpticsPA5", "Inspect")
end
function api.RepairCamera()
  return call("PTFR.ActivityStateR3.CameraOpticsPA5", "Repair")
end
function api.H10()
  return call("PTFR.RestorationBaseline.RestorationBaseline", "H10Status")
end
function api.GigSummary()
  return call("PTFR.ActivityStateR3.GigDiagnosticsPA5", "Summary")
end
function api.GigVisibility(id)
  if id == nil then return call("PTFR.ActivityStateR3.GigDiagnosticsPA5", "InspectOwned") end
  if type(id) ~= "string" or id == "" then return "Pass a whitelisted gig ID or omit it for owned gigs." end
  return call("PTFR.ActivityStateR3.GigDiagnosticsPA5", "Inspect", id)
end
-- Optional read-only compatibility evidence; never disable another mod or its input.
function api.Camera()
  local ok, result = pcall(function()
    if type(GetMod) ~= "function" then return "IFP=unavailable" end
    local mod = GetMod("ImmersiveFirstPerson")
    if not mod or not mod.api or type(mod.api.GetCameraState) ~= "function" then
      return "IFP=unavailable"
    end
    local state = mod.api.GetCameraState()
    if type(state) ~= "table" then return "IFP=unavailable" end
    return "IFP mode=" .. tostring(state.mode) .. " ownsCamera=" .. tostring(state.ownsCamera) ..
      " inputLocked=" .. tostring(state.inputLocked)
  end)
  return api.Arrival() .. " | " .. api.Optics() .. " | " .. (ok and result or "IFP=unavailable")
end
-- PA6: verbose diagnostics are OFF by default. Use Trace(seconds) explicitly.
-- Manual getters remain available; this monitor only reports each owned fault once.
local clock, sample = 0, 0
local traceUntil, traceRows, previous = nil, 0, nil
local reportedFaults = {}
local function stopTrace()
  traceUntil, traceRows, previous = nil, 0, nil
end
function api.Trace(seconds)
  if seconds == nil then seconds = 60 end
  if type(seconds) ~= "number" or seconds ~= seconds or seconds < 1 or seconds > 180 then
    return "Pass a duration from 1 to 180 real-time seconds."
  end
  traceUntil, traceRows, previous = clock + seconds, 0, nil
  return "PA6 read-only trace enabled for " .. tostring(seconds) .. " seconds. TraceStop() stops it."
end
function api.TraceStop()
  stopTrace()
  return "PA6 trace stopped. Automatic verbose output remains off."
end
function api.TraceStatus()
  return traceUntil and ("PA6 trace active; samples=" .. tostring(traceRows)) or "PA6 trace off."
end
registerForEvent("onUpdate", function(dt)
  if type(dt) ~= "number" or dt ~= dt or dt < 0 or dt == math.huge then return end
  clock = clock + dt
  if clock - sample < 1 then return end
  sample = clock
  local ok, q = pcall(function()
    return Game and type(Game.GetQuestsSystem) == "function" and Game.GetQuestsSystem()
  end)
  if not ok or not q then
    -- A trace never silently resumes in a different loaded game.
    stopTrace()
    reportedFaults = {}
    return
  end
  local faults = { "PTFRPA2_Fault", "PTFRPA5O_Fault" }
  for _, name in ipairs(faults) do
    local readOK, value = pcall(function() return q:GetFactStr(name) end)
    if readOK and type(value) == "number" and value > 0 and not reportedFaults[name] then
      reportedFaults[name] = true
      print("[PTFR] Restoration fault: " .. name .. ". Use Status(), Arrival(), Optics() and H10() to inspect.")
    end
  end
  if not traceUntil then return end
  if clock > traceUntil or traceRows >= 180 then stopTrace(); return end
  local state = api.Camera() .. " | " .. api.Status()
  if state ~= previous or traceRows % 5 == 0 then print("[PA6 trace] " .. state) end
  if traceRows % 5 == 0 then print("[PA6 restoration] " .. api.H10() .. " | " .. api.GigSummary()) end
  if traceRows % 30 == 0 then print("[PA6 map details] " .. api.GigVisibility()) end
  previous, traceRows = state, traceRows + 1
end)
return api

