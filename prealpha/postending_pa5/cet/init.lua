-- PA5 diagnostics are read-only except explicitly named one-shot RepairCamera.
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
-- Read-only, bounded transition trace in PTFR_PreAlpha.log. No gameplay writes.
local clock, sample, traceStart, rows, previous = 0, 0, nil, 0, nil
registerForEvent("onUpdate", function(dt)
  clock = clock + dt
  if clock - sample < 1 then return end
  sample = clock
  local ok, active = pcall(function()
    local q = Game.GetQuestsSystem()
    return q and q:GetFactStr("PTFRPA2_Started") == 1
  end)
  if not ok or not active then
    traceStart, rows, previous = nil, 0, nil
    return
  end
  if not traceStart then traceStart = clock end
  if rows >= 180 or clock - traceStart > 180 then return end
  local state = api.Camera() .. " | " .. api.Status()
  if state ~= previous or rows % 5 == 0 then
    print("[PA5 transition] " .. state)
  end
  if rows % 5 == 0 then print("[PA5 restoration] " .. api.H10() .. " | " .. api.GigSummary()) end
  if rows % 30 == 0 then print("[PA5 map details] " .. api.GigVisibility()) end
  previous, rows = state, rows + 1
end)
return api
